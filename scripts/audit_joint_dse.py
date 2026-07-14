#!/usr/bin/env python3
"""Audit the coupled QArchGauge architecture design space.

The audit consumes direct finite-shot quality records, source-audited schedule
bounds, and the case-level FT contract.  It deliberately samples a balanced
set of design points rather than assigning probabilities to technology
scenarios.  Application-level hardware targets are emitted only when the same
record passes measured quality, scope, synthesis, distillation, and logical
reliability gates.
"""

import argparse
import copy
import csv
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import audit_ft_reliability_budget as ft
from strong_accept_common import (
    DEFAULT_INPUT,
    ROOT,
    as_float,
    json_dump,
    median,
    quantile,
    read_rows,
    record_id,
    relative,
)


DEFAULT_OUTPUT = ROOT / "data/processed/perlmutter/joint_bottleneck_phase_map.json"
DEFAULT_FINITE = ROOT / "data/processed/perlmutter/finite_shot_quality_sensitivity.json"
DEFAULT_SCHEDULE = ROOT / "data/processed/perlmutter/dependency_schedule_coverage.csv"
DEFAULT_REPLACEMENT = ROOT / "data/processed/perlmutter/component_replacement_case_studies.json"
DEFAULT_CHEM = ROOT / "data/processed/perlmutter/chem_controlled_compiled_measurement_records.json"

DESIGN_SEED = 27013
DESIGN_POINTS = 384
BASELINE_FACTORIES = 64
FACTORY_CODE_BEATS_PER_STATE = 15
COMMUNICATION_SEC = 7.8e-6
HOST_FEEDBACK_SEC_PER_EVALUATION = 5.0e-6

PARAMETERS = {
    "dependency_mode": ["aggregate_ready", "group_wave_ready", "serial_evaluation_ready"],
    "tolerance_multiplier": [0.5, 1.0, 2.0],
    "shots": [1000, 10000, 100000],
    "useful_lanes": [1000, 10000, 100000],
    "t_mode": ["fixed_16", "fixed_32", "reliability_leading"],
    "application_failure_budget": [0.01, 0.001],
    "physical_error_rate": [1.0e-3, 1.0e-4],
    "factory_supply_multiplier": [1.0, 100.0, 10000.0, 50000.0],
    "syndrome_round_sec": [0.4e-6, 0.1e-6],
    "decoder_service_sec": [1.0e-6, 5.0e-6, 63.0e-6],
    "native_deadline_factor": [0.5, 1.0, 2.0],
    "overlap_rho": [0.0, 0.5, 1.0],
}

PARAMETER_ORIGINS = {
    "dependency_mode": {
        "kind": "measured_bound",
        "source": "data/processed/perlmutter/dependency_schedule_coverage.json",
        "meaning": "source-audited aggregate, group-wave, and serial-evaluation ready widths",
    },
    "tolerance_multiplier": {
        "kind": "measured_sensitivity",
        "source": "declared natural-unit application tolerances",
        "meaning": "0.5x/1x/2x tolerance stress; not free quality recovery",
    },
    "shots": {
        "kind": "direct_measurement",
        "source": "data/processed/perlmutter/finite_shot_quality_sensitivity.json",
        "meaning": "direct replayed sampling with 12 independent replicates per selected case",
    },
    "useful_lanes": {
        "kind": "architecture_target",
        "source": "bounded target sweep",
        "meaning": "hardware lanes capped by dependency-ready repetitions",
    },
    "t_mode": {
        "kind": "bound_and_derived",
        "source": "Ross--Selinger leading term plus explicit 16/32-T stresses",
        "url": "https://arxiv.org/abs/1403.2975",
    },
    "application_failure_budget": {
        "kind": "declared_contract",
        "source": "P0-C strict all-shots application budget",
        "meaning": "split equally across logical, synthesis, and distillation faults",
    },
    "physical_error_rate": {
        "kind": "resource-estimator_envelope",
        "source": "QDK-aligned e3/e4 cross-check",
        "url": "https://learn.microsoft.com/en-us/azure/quantum/qre-build-error-correction-models",
    },
    "factory_supply_multiplier": {
        "kind": "architecture_target",
        "source": "64-factory baseline and P0-C crossover envelope",
        "meaning": "factory count only; no published speedup multiplier is borrowed",
    },
    "syndrome_round_sec": {
        "kind": "literature_and_target",
        "source": "0.4-us P0-C reference and explicit 0.1-us target",
        "meaning": "scenario value, not a vendor forecast",
    },
    "decoder_service_sec": {
        "kind": "literature_envelope",
        "source": "P0-C decoder/reaction contract",
        "url": "https://arxiv.org/abs/2511.10633",
        "meaning": "1/5/63 us service plus a separately retained 7.8-us communication path",
    },
    "native_deadline_factor": {
        "kind": "moving_frontier_stress",
        "source": "measured native deadline scaled by 0.5x/1x/2x",
    },
    "overlap_rho": {
        "kind": "deterministic_bound",
        "source": "max-overlap to full-serialization bracket",
        "meaning": "rho=0 uses max(core terms); rho=1 serializes them",
    },
}

RESOURCE_ORDER = (
    "factory_supply",
    "logical_cycle",
    "shot_parallelism",
    "decoder_reaction",
    "host_feedback",
)


def load_json(path):
    return json.loads(Path(path).read_text())


def read_csv_index(path, key):
    with Path(path).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row[key]: row for row in rows}, rows


def balanced_design(count, seed):
    """Return a deterministic marginally balanced discrete space-filling set."""
    rng = random.Random(seed)
    columns = {}
    for name, levels in PARAMETERS.items():
        values = [levels[index % len(levels)] for index in range(count)]
        rng.shuffle(values)
        columns[name] = values
    scenarios = []
    seen = set()
    for index in range(count):
        params = {name: columns[name][index] for name in PARAMETERS}
        signature = json.dumps(params, sort_keys=True)
        if signature in seen:
            continue
        seen.add(signature)
        scenarios.append({"scenario_id": "dse-{:04d}".format(index), **params})
    return scenarios


def finite_index(artifact):
    return {
        (record["source_record_id"], int(record["shots"])): record
        for record in artifact["records"]
    }


def scale_contract(base, shots):
    """Scale measured per-shot work to the direct finite-shot budget."""
    contract = copy.deepcopy(base)
    evaluations = max(1.0, float(base["evaluations"]))
    target_total = evaluations * int(shots)
    ratio = target_total / max(1.0, float(base["total_shot_executions"]))
    for key in ("logical_locations", "weighted_gate_cycles", "total_rotations"):
        contract[key] = float(base[key]) * ratio
    contract["total_shot_executions"] = target_total
    contract["shot_executions_per_evaluation"] = int(shots)
    contract["logical_locations_per_shot"] = (
        contract["logical_locations"] / target_total
    )
    contract["rotations_per_shot"] = contract["total_rotations"] / target_total
    return contract


def quality_gate(finite_record, tolerance_multiplier):
    tolerance = float(finite_record["quality_tolerance"]) * float(tolerance_multiplier)
    gaps = [float(value) for value in finite_record["replicate_quality_gap"]]
    pass_probability = sum(value <= tolerance for value in gaps) / len(gaps)
    same_record = bool(finite_record["same_record_quality_shot_trace"])
    full_loop = bool(finite_record["full_algorithm_loop_covered"])
    measured_pass = pass_probability >= 0.9
    eligible = measured_pass and same_record and full_loop
    if eligible:
        reason = "quality_pass_with_same_record_full_loop_finite_shot_trace"
    elif not measured_pass:
        reason = "finite_shot_quality_pass_probability_below_0p9"
    elif not same_record:
        reason = "finite_shot_trace_is_not_the_same_record_measurement_contract"
    else:
        reason = "finite_shot_trace_does_not_cover_the_outer_algorithm_loop"
    return {
        "tolerance": tolerance,
        "pass_probability": pass_probability,
        "quality_ci": [quantile(gaps, 0.025), quantile(gaps, 0.975)],
        "measured_quality_pass": measured_pass,
        "same_record": same_record,
        "full_loop": full_loop,
        "hardware_target_eligible": eligible,
        "reason": reason,
    }


def dependency_ready(schedule, mode, base_contract, scaled_contract):
    base_total = max(1.0, float(schedule["aggregate_ready"]))
    selected = max(1.0, float(schedule[mode]))
    fraction = min(1.0, selected / base_total)
    return max(1.0, fraction * float(scaled_contract["total_shot_executions"]))


def reliability_contract(contract, failure_budget, physical_error_rate, t_mode):
    source_budget = float(failure_budget) / 3.0
    distance_result = ft.select_distance(
        contract["logical_locations"], source_budget, physical_error_rate
    )
    rotations = max(1.0, float(contract["total_rotations"]))
    per_rotation_budget = source_budget / rotations
    required_t = ft.leading_t_count(per_rotation_budget)
    if t_mode == "fixed_16":
        t_per_rotation = 16
    elif t_mode == "fixed_32":
        t_per_rotation = 32
    else:
        t_per_rotation = required_t
    synthesis_proxy = 2.0 ** (-t_per_rotation / 3.0)
    synthesis_feasible = synthesis_proxy <= per_rotation_budget
    total_t = rotations * t_per_rotation
    required_output_error = source_budget / max(1.0, total_t)
    protocol = ft.select_factory_protocol(required_output_error)
    return {
        "distance": distance_result["distance"],
        "logical_error_per_location": distance_result["logical_error_per_location"],
        "logical_failure_union_bound": distance_result["union_bound_failure_probability"],
        "logical_fault_budget": source_budget,
        "required_t_per_rotation": required_t,
        "t_per_rotation": t_per_rotation,
        "synthesis_proxy": synthesis_proxy,
        "per_rotation_synthesis_budget": per_rotation_budget,
        "synthesis_feasible": synthesis_feasible,
        "total_t_states": total_t,
        "required_factory_output_error": required_output_error,
        "factory_protocol": protocol,
        "ft_contract_valid": synthesis_feasible and protocol is not None,
    }


def overlap_total(core_terms, rho, host_sec, movement_sec=0.0):
    values = {name: max(0.0, float(value)) for name, value in core_terms.items()}
    largest = max(values.values()) if values else 0.0
    serialized = sum(values.values())
    core = largest + float(rho) * (serialized - largest)
    return core + max(0.0, host_sec) + max(0.0, movement_sec)


def runtime_model(row, schedule, contract, reliability, scenario, overrides=None):
    overrides = overrides or {}
    distance = int(reliability["distance"])
    round_sec = float(scenario["syndrome_round_sec"])
    cycle_sec = distance * round_sec
    ready = dependency_ready(
        schedule, scenario["dependency_mode"], contract, contract
    )
    useful_lanes = float(scenario["useful_lanes"])
    if overrides.get("shot_parallelism") == "10x":
        useful_lanes *= 10.0
    elif overrides.get("shot_parallelism") == "remove":
        useful_lanes = float(contract["total_shot_executions"])
    lanes = min(max(1.0, useful_lanes), ready)

    factories = BASELINE_FACTORIES * float(scenario["factory_supply_multiplier"])
    if overrides.get("factory_supply") == "10x":
        factories *= 10.0
    elif overrides.get("factory_supply") == "remove":
        factories = math.inf

    # A scenario-level syndrome-round change affects both data execution and
    # factory production.  A marginal logical-cycle lever, however, changes
    # only the data-path term while holding the separately named factory-supply
    # term fixed.  This is the component-preserving invariant used to rank
    # first/next targets.
    data_cycle_scale = 1.0
    if overrides.get("logical_cycle") == "10x":
        data_cycle_scale = 0.1
    elif overrides.get("logical_cycle") == "remove":
        data_cycle_scale = 0.0
    data_cycle = cycle_sec * data_cycle_scale

    reaction = float(scenario["decoder_service_sec"]) + COMMUNICATION_SEC
    if overrides.get("decoder_reaction") == "10x":
        reaction *= 0.1
    elif overrides.get("decoder_reaction") == "remove":
        reaction = 0.0

    host = float(contract["evaluations"]) * HOST_FEEDBACK_SEC_PER_EVALUATION
    if overrides.get("host_feedback") == "10x":
        host *= 0.1
    elif overrides.get("host_feedback") == "remove":
        host = 0.0

    logical_sec = float(contract["weighted_gate_cycles"]) * data_cycle / lanes
    decoder_sec = (
        float(contract["total_shot_executions"]) / lanes * reaction
    )
    factory_sec = 0.0 if math.isinf(factories) else (
        float(reliability["total_t_states"])
        * FACTORY_CODE_BEATS_PER_STATE
        * cycle_sec
        / max(1.0, factories)
    )
    movement = float(overrides.get("movement_sec", 0.0))
    core_terms = {
        "factory_supply": factory_sec,
        "logical_cycle": logical_sec,
        "decoder_reaction": decoder_sec,
    }
    total = overlap_total(core_terms, scenario["overlap_rho"], host, movement)
    native = max(
        1.0e-30,
        as_float(row, "native_runtime_sec") * float(scenario["native_deadline_factor"]),
    )
    physical_per_logical = 2 * distance * distance
    protocol = reliability["factory_protocol"]
    factory_physical = None
    if protocol is not None and not math.isinf(factories):
        factory_physical = int(math.ceil(factories)) * int(protocol["physical_qubits"])
    return {
        "total_sec": total,
        "native_deadline_sec": native,
        "runtime_ratio": total / native,
        "runtime_pass": total < native,
        "effective_lanes": lanes,
        "dependency_ready": ready,
        "lane_saturation": lanes / max(1.0, ready),
        "factory_count": None if math.isinf(factories) else int(math.ceil(factories)),
        "data_physical_qubits": ft.logical_qubits(row) * physical_per_logical,
        "factory_physical_qubits": factory_physical,
        "terms_sec": {
            **core_terms,
            "host_feedback": host,
            "matched_movement": movement,
        },
    }


def lever_analysis(row, schedule, contract, reliability, scenario, base):
    gains_10x = {}
    removal_ceilings = {}
    for resource in RESOURCE_ORDER:
        ten = runtime_model(
            row, schedule, contract, reliability, scenario, {resource: "10x"}
        )
        removed = runtime_model(
            row, schedule, contract, reliability, scenario, {resource: "remove"}
        )
        gains_10x[resource] = base["total_sec"] / max(1.0e-30, ten["total_sec"])
        removal_ceilings[resource] = (
            base["total_sec"] / max(1.0e-30, removed["total_sec"])
        )
    first = max(
        RESOURCE_ORDER,
        key=lambda name: (gains_10x[name], removal_ceilings[name], -RESOURCE_ORDER.index(name)),
    )
    after_first = runtime_model(
        row, schedule, contract, reliability, scenario, {first: "remove"}
    )
    next_gains = {}
    for resource in RESOURCE_ORDER:
        if resource == first:
            continue
        both = {first: "remove", resource: "10x"}
        improved = runtime_model(row, schedule, contract, reliability, scenario, both)
        next_gains[resource] = (
            after_first["total_sec"] / max(1.0e-30, improved["total_sec"])
        )
    second = max(
        next_gains,
        key=lambda name: (next_gains[name], -RESOURCE_ORDER.index(name)),
    )
    return {
        "first_target": first,
        "next_target": second,
        "ten_x_gain": gains_10x,
        "removal_ceiling": removal_ceilings,
        "first_removed_runtime_ratio": (
            after_first["total_sec"] / base["native_deadline_sec"]
        ),
        "next_ten_x_gain_after_first_removal": next_gains,
    }


def evaluate_case(row, schedule, base_contract, finite_record, scenario):
    quality = quality_gate(finite_record, scenario["tolerance_multiplier"])
    contract = scale_contract(base_contract, scenario["shots"])
    reliability = reliability_contract(
        contract,
        scenario["application_failure_budget"],
        scenario["physical_error_rate"],
        scenario["t_mode"],
    )
    runtime = runtime_model(row, schedule, contract, reliability, scenario)
    conditional_dominant = max(
        runtime["terms_sec"], key=lambda name: runtime["terms_sec"][name]
    )
    analysis = None
    if not quality["hardware_target_eligible"]:
        first = "algorithm_quality"
        second = None
    elif not reliability["synthesis_feasible"]:
        first = "rotation_synthesis"
        second = "factory_reliability" if reliability["factory_protocol"] is None else None
    elif reliability["factory_protocol"] is None:
        first = "factory_reliability"
        second = None
    elif runtime["runtime_pass"]:
        first = "advantage_reached"
        second = None
    else:
        analysis = lever_analysis(
            row, schedule, contract, reliability, scenario, runtime
        )
        first = analysis["first_target"]
        second = analysis["next_target"]
    advantage = (
        quality["hardware_target_eligible"]
        and reliability["ft_contract_valid"]
        and runtime["runtime_pass"]
    )
    return {
        "record_id": record_id(row),
        "workload": row["workload"],
        "scenario_id": scenario["scenario_id"],
        "quality_pass_probability": quality["pass_probability"],
        "quality_tolerance": quality["tolerance"],
        "hardware_target_eligible": quality["hardware_target_eligible"],
        "quality_exclusion_reason": quality["reason"],
        "distance": reliability["distance"],
        "t_per_rotation": reliability["t_per_rotation"],
        "required_t_per_rotation": reliability["required_t_per_rotation"],
        "synthesis_feasible": reliability["synthesis_feasible"],
        "factory_protocol_available": reliability["factory_protocol"] is not None,
        "ft_contract_valid": reliability["ft_contract_valid"],
        "runtime_sec": runtime["total_sec"],
        "native_deadline_sec": runtime["native_deadline_sec"],
        "runtime_ratio": runtime["runtime_ratio"],
        "runtime_pass": runtime["runtime_pass"],
        "advantage": advantage,
        "effective_lanes": runtime["effective_lanes"],
        "dependency_ready": runtime["dependency_ready"],
        "factory_count": runtime["factory_count"],
        "data_physical_qubits": runtime["data_physical_qubits"],
        "factory_physical_qubits": runtime["factory_physical_qubits"],
        "conditional_execution_dominant": conditional_dominant,
        "first_target": first,
        "next_target": second,
        "ten_x_gain": None if analysis is None else analysis["ten_x_gain"],
        "removal_ceiling": None if analysis is None else analysis["removal_ceiling"],
        "runtime_terms_sec": runtime["terms_sec"],
    }


def mode_and_fraction(values):
    if not values:
        return None, 0.0
    counts = Counter(values)
    value, count = counts.most_common(1)[0]
    return value, count / len(values)


def summarize_case_rows(rows):
    eligible = [row for row in rows if row["hardware_target_eligible"]]
    valid = [row for row in eligible if row["ft_contract_valid"]]
    analyzed = [row for row in valid if row["removal_ceiling"] is not None]
    first_mode, first_stability = mode_and_fraction(
        [row["first_target"] for row in eligible]
    )
    next_mode, next_stability = mode_and_fraction(
        [row["next_target"] for row in analyzed if row["next_target"]]
    )
    ceilings = {}
    for resource in RESOURCE_ORDER:
        values = [row["removal_ceiling"][resource] for row in analyzed]
        if values:
            ceilings[resource] = {
                "median": median(values),
                "p90": quantile(values, 0.9),
            }
    return {
        "records": len(rows),
        "workloads": dict(Counter(row["workload"] for row in rows)),
        "measured_quality_pass_records": sum(
            row["quality_pass_probability"] >= 0.9 for row in rows
        ),
        "hardware_target_eligible_records": len(eligible),
        "ft_valid_eligible_records": len(valid),
        "runtime_pass_eligible_records": sum(row["runtime_pass"] for row in eligible),
        "advantaged_records": sum(row["advantage"] for row in rows),
        "first_target_counts": dict(Counter(row["first_target"] for row in rows)),
        "eligible_first_target_counts": dict(Counter(row["first_target"] for row in eligible)),
        "eligible_first_target_mode": first_mode,
        "eligible_first_target_stability": first_stability,
        "next_target_counts": dict(Counter(
            row["next_target"] for row in analyzed if row["next_target"]
        )),
        "next_target_mode": next_mode,
        "next_target_stability": next_stability,
        "eligible_runtime_ratio": {
            "median": median(row["runtime_ratio"] for row in eligible),
            "p90": quantile((row["runtime_ratio"] for row in eligible), 0.9),
        } if eligible else None,
        "removal_ceiling": ceilings,
    }


def phase_scenarios():
    base = {
        "dependency_mode": "serial_evaluation_ready",
        "tolerance_multiplier": 1.0,
        "shots": 10000,
        "useful_lanes": 10000,
        "t_mode": "reliability_leading",
        "application_failure_budget": 0.01,
        "physical_error_rate": 1.0e-3,
        "factory_supply_multiplier": 1.0,
        "syndrome_round_sec": 0.4e-6,
        "decoder_service_sec": 5.0e-6,
        "native_deadline_factor": 1.0,
        "overlap_rho": 1.0,
    }
    scenarios = []
    for factory in PARAMETERS["factory_supply_multiplier"]:
        for lanes in PARAMETERS["useful_lanes"]:
            scenario = dict(base)
            scenario["scenario_id"] = "phase-f{}-l{}".format(
                "{:g}".format(factory), "{:g}".format(lanes)
            )
            scenario["factory_supply_multiplier"] = factory
            scenario["useful_lanes"] = lanes
            scenarios.append(scenario)
    return base, scenarios


def trace_aware_lower_bound(selected_ids, row_index, schedule_index, base_contracts, finite):
    fixed = {
        "scenario_id": "trace-logical-lower-bound",
        "dependency_mode": "aggregate_ready",
        "tolerance_multiplier": 1.0,
        "shots": 10000,
        "useful_lanes": 10000,
        "t_mode": "reliability_leading",
        "application_failure_budget": 0.01,
        "physical_error_rate": 1.0e-3,
        "factory_supply_multiplier": 1.0,
        "syndrome_round_sec": 0.4e-6,
        "decoder_service_sec": 5.0e-6,
        "native_deadline_factor": 1.0,
        "overlap_rho": 1.0,
    }
    by_mode = {}
    detail = []
    for mode in (
        "aggregate_ready", "group_wave_ready", "serial_evaluation_ready"
    ):
        scenario = dict(fixed)
        scenario["dependency_mode"] = mode
        mode_rows = []
        for rid in selected_ids:
            row = row_index[rid]
            quality = quality_gate(finite[(rid, 10000)], 1.0)
            contract = scale_contract(base_contracts[rid], 10000)
            reliability = reliability_contract(
                contract, 0.01, 1.0e-3, "reliability_leading"
            )
            runtime = runtime_model(
                row,
                schedule_index[rid],
                contract,
                reliability,
                scenario,
                {"factory_supply": "remove"},
            )
            dominant = max(runtime["terms_sec"], key=runtime["terms_sec"].get)
            item = {
                "record_id": rid,
                "workload": row["workload"],
                "mode": mode,
                "hardware_target_eligible": quality["hardware_target_eligible"],
                "runtime_ratio": runtime["runtime_ratio"],
                "runtime_pass": runtime["runtime_pass"],
                "effective_lanes": runtime["effective_lanes"],
                "dependency_ready": runtime["dependency_ready"],
                "dominant_nonfactory_term": dominant,
            }
            mode_rows.append(item)
            detail.append(item)
        workload_summary = {}
        for workload in ("ml", "chemistry", "optimization", "simulation"):
            subset = [row for row in mode_rows if row["workload"] == workload]
            eligible = [row for row in subset if row["hardware_target_eligible"]]
            workload_summary[workload] = {
                "records": len(subset),
                "scope": (
                    "application-level quality-qualified"
                    if len(eligible) == len(subset)
                    else "conditional execution lower bound"
                ),
                "median_runtime_ratio": median(row["runtime_ratio"] for row in subset),
                "p10_runtime_ratio": quantile((row["runtime_ratio"] for row in subset), 0.1),
                "p90_runtime_ratio": quantile((row["runtime_ratio"] for row in subset), 0.9),
                "median_effective_lanes": median(row["effective_lanes"] for row in subset),
                "dominant_term_counts": dict(Counter(
                    row["dominant_nonfactory_term"] for row in subset
                )),
                "eligible_subset": {
                    "records": len(eligible),
                    "median_runtime_ratio": median(
                        row["runtime_ratio"] for row in eligible
                    ),
                    "p10_runtime_ratio": quantile(
                        (row["runtime_ratio"] for row in eligible), 0.1
                    ),
                    "p90_runtime_ratio": quantile(
                        (row["runtime_ratio"] for row in eligible), 0.9
                    ),
                    "runtime_pass_records": sum(row["runtime_pass"] for row in eligible),
                    "dominant_term_counts": dict(Counter(
                        row["dominant_nonfactory_term"] for row in eligible
                    )),
                } if eligible else {"records": 0},
            }
        by_mode[mode] = workload_summary
    return {
        "fixed_assumptions": fixed,
        "factory_term_removed": True,
        "records": len(selected_ids),
        "scope": (
            "Direct finite-shot representative records under strict reliability. "
            "ML/Chem/Opt and nonpassing Sim rows are conditional execution lower bounds."
        ),
        "by_mode": by_mode,
        "detail": detail,
    }


def replacement_reinversion(replacement, row_index, schedule_index, base_contracts):
    scenario = {
        "scenario_id": "lsqca-replacement",
        "dependency_mode": "serial_evaluation_ready",
        "tolerance_multiplier": 1.0,
        "shots": 10000,
        "useful_lanes": 10000,
        "t_mode": "reliability_leading",
        "application_failure_budget": 0.01,
        "physical_error_rate": 1.0e-3,
        "factory_supply_multiplier": 50000.0,
        "syndrome_round_sec": 0.4e-6,
        "decoder_service_sec": 5.0e-6,
        "native_deadline_factor": 1.0,
        "overlap_rho": 1.0,
    }
    records = []
    invariant_errors = []
    for attached in replacement["quality_qualified_records"]:
        rid = attached["record_id"]
        row = row_index[rid]
        contract = scale_contract(base_contracts[rid], 10000)
        reliability = reliability_contract(contract, 0.01, 1.0e-3, "reliability_leading")
        base = runtime_model(row, schedule_index[rid], contract, reliability, scenario)
        integration = attached["lsqca"]["quality_qualified_ft_integration"]
        lower = runtime_model(
            row,
            schedule_index[rid],
            contract,
            reliability,
            scenario,
            {"movement_sec": integration["movement_lower_sec"]},
        )
        upper = runtime_model(
            row,
            schedule_index[rid],
            contract,
            reliability,
            scenario,
            {"movement_sec": integration["movement_upper_sec"]},
        )
        inv = attached["lsqca"]["invariants"]
        if not all((
            inv["logical_error_contract_unchanged"],
            inv["native_deadline_unchanged"],
            inv["quality_unchanged"],
            inv["rotation_and_factory_demand_unchanged"],
        )):
            invariant_errors.append(rid)
        records.append({
            "record_id": rid,
            "point_sam_reduces_core_cells": attached["lsqca"]["point_sam_reduces_core_cells"],
            "changed_terms": inv["changed_terms"],
            "baseline_runtime_ratio": base["runtime_ratio"],
            "lower_movement_runtime_ratio": lower["runtime_ratio"],
            "upper_movement_runtime_ratio": upper["runtime_ratio"],
            "lower_movement_removal_ceiling": lower["total_sec"] / max(1.0e-30, base["total_sec"]),
            "upper_movement_removal_ceiling": upper["total_sec"] / max(1.0e-30, base["total_sec"]),
            "runtime_parity_base": base["runtime_pass"],
            "runtime_parity_lower": lower["runtime_pass"],
            "runtime_parity_upper": upper["runtime_pass"],
            "first_target_after_factory_scaling_lower": (
                "matched_data_movement"
                if integration["movement_lower_sec"] >= max(base["terms_sec"].values())
                else max(base["terms_sec"], key=base["terms_sec"].get)
            ),
            "first_target_after_factory_scaling_upper": (
                "matched_data_movement"
                if integration["movement_upper_sec"] >= max(base["terms_sec"].values())
                else max(base["terms_sec"], key=base["terms_sec"].get)
            ),
        })
    return {
        "mechanism": "LSQCA point-SAM matched-event load/store replacement",
        "source": replacement["parameter_origins"]["lsqca"],
        "scenario": scenario,
        "records": records,
        "summary": {
            "records": len(records),
            "point_sam_area_improvement_records": sum(
                row["point_sam_reduces_core_cells"] for row in records
            ),
            "runtime_parity_base_records": sum(row["runtime_parity_base"] for row in records),
            "runtime_parity_lower_records": sum(row["runtime_parity_lower"] for row in records),
            "runtime_parity_upper_records": sum(row["runtime_parity_upper"] for row in records),
            "lower_first_target_counts": dict(Counter(
                row["first_target_after_factory_scaling_lower"] for row in records
            )),
            "upper_first_target_counts": dict(Counter(
                row["first_target_after_factory_scaling_upper"] for row in records
            )),
            "median_runtime_inflation_lower": median(
                row["lower_movement_removal_ceiling"] for row in records
            ),
            "median_runtime_inflation_upper": median(
                row["upper_movement_removal_ceiling"] for row in records
            ),
        },
        "invariant_errors": invariant_errors,
        "scope": (
            "Only point-SAM core cells and matched load/store movement change. "
            "The study does not borrow LSQCA's published benchmark speedups."
        ),
    }


def flatten_case(case, scenario):
    row = {
        key: value for key, value in case.items()
        if not isinstance(value, (dict, list))
    }
    for key, value in scenario.items():
        if key != "scenario_id":
            row["parameter_{}".format(key)] = value
    if case["removal_ceiling"]:
        for key, value in case["removal_ceiling"].items():
            row["removal_ceiling_{}".format(key)] = value
    if case["ten_x_gain"]:
        for key, value in case["ten_x_gain"].items():
            row["ten_x_gain_{}".format(key)] = value
    for key, value in case["runtime_terms_sec"].items():
        row["runtime_term_{}_sec".format(key)] = value
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT))
    parser.add_argument("--finite-shot", default=str(DEFAULT_FINITE))
    parser.add_argument("--schedule-csv", default=str(DEFAULT_SCHEDULE))
    parser.add_argument("--replacement", default=str(DEFAULT_REPLACEMENT))
    parser.add_argument("--chem-compiled", default=str(DEFAULT_CHEM))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT.with_suffix(".csv")))
    parser.add_argument("--design-points", type=int, default=DESIGN_POINTS)
    args = parser.parse_args()

    rows = read_rows(args.input_csv)
    row_index = {record_id(row): row for row in rows}
    finite_artifact = load_json(args.finite_shot)
    finite = finite_index(finite_artifact)
    selected_ids = sorted({record["source_record_id"] for record in finite_artifact["records"]})
    schedules, _ = read_csv_index(args.schedule_csv, "record_id")
    replacement = load_json(args.replacement)
    chem_records = ft.load_chem_records(args.chem_compiled)

    base_contracts = {}
    for rid in selected_ids:
        row = row_index[rid]
        raw, _ = ft.raw_workload(row)
        base_contracts[rid] = ft.circuit_contract(
            row, schedules[rid], chem_records, raw
        )

    scenarios = balanced_design(args.design_points, DESIGN_SEED)
    detail_rows = []
    scenario_summaries = []
    for scenario in scenarios:
        cases = []
        for rid in selected_ids:
            finite_record = finite[(rid, int(scenario["shots"]))]
            case = evaluate_case(
                row_index[rid], schedules[rid], base_contracts[rid], finite_record, scenario
            )
            cases.append(case)
            detail_rows.append(flatten_case(case, scenario))
        scenario_summaries.append({
            "scenario_id": scenario["scenario_id"],
            "parameters": {key: scenario[key] for key in PARAMETERS},
            "summary": summarize_case_rows(cases),
        })

    phase_base, phase_inputs = phase_scenarios()
    phase_cells = []
    for scenario in phase_inputs:
        cases = [
            evaluate_case(
                row_index[rid], schedules[rid], base_contracts[rid], finite[(rid, 10000)], scenario
            )
            for rid in selected_ids
        ]
        summary = summarize_case_rows(cases)
        phase_cells.append({
            "factory_supply_multiplier": scenario["factory_supply_multiplier"],
            "useful_lanes": scenario["useful_lanes"],
            **summary,
        })

    stable_cells = [
        cell for cell in phase_cells
        if cell["factory_supply_multiplier"] <= 100.0
        and cell["eligible_first_target_stability"] >= 1.0
    ]
    stable_target, stable_fraction = mode_and_fraction(
        [cell["eligible_first_target_mode"] for cell in stable_cells]
    )

    replacement_result = replacement_reinversion(
        replacement, row_index, schedules, base_contracts
    )
    trace_lower_bound = trace_aware_lower_bound(
        selected_ids, row_index, schedules, base_contracts, finite
    )

    coverage = {}
    for name, levels in PARAMETERS.items():
        counts = Counter(str(scenario[name]) for scenario in scenarios)
        coverage[name] = {
            "expected_levels": [str(value) for value in levels],
            "observed_counts": dict(counts),
            "all_levels_covered": all(str(value) in counts for value in levels),
        }

    internal_errors = []
    if finite_artifact["audit_status"] != "PASS":
        internal_errors.append("finite-shot input does not pass")
    if replacement["audit_status"] != "PASS":
        internal_errors.append("component replacement input does not pass")
    if len(selected_ids) != 68:
        internal_errors.append("expected 68 direct finite-shot representative records")
    if set(row_index[rid]["workload"] for rid in selected_ids) != {
        "ml", "chemistry", "optimization", "simulation"
    }:
        internal_errors.append("not every workload is represented")
    if not all(item["all_levels_covered"] for item in coverage.values()):
        internal_errors.append("space-filling design does not cover every parameter level")
    if not stable_cells or stable_target is None:
        internal_errors.append("no stable main recommendation region found")
    if len({cell["eligible_first_target_mode"] for cell in phase_cells}) < 2:
        internal_errors.append("phase map does not expose a target transition")
    if replacement_result["invariant_errors"]:
        internal_errors.append("replacement changed an unnamed contract term")
    if any(
        row["hardware_target_eligible"] is False
        and row["first_target"] != "algorithm_quality"
        for row in detail_rows
    ):
        internal_errors.append("quality-failing case received a hardware first target")
    if any(
        row["hardware_target_eligible"]
        and not row["synthesis_feasible"]
        and row["first_target"] != "rotation_synthesis"
        for row in detail_rows
    ):
        internal_errors.append("invalid fixed-T case was not assigned to rotation synthesis")

    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in detail_rows for key in row})
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(detail_rows)

    csv_sha256 = hashlib.sha256(output_csv.read_bytes()).hexdigest()
    payload = {
        "schema": "qarchgauge.joint-bottleneck-phase-map.v1",
        "audit_status": "FAIL" if internal_errors else "PASS",
        "scope": (
            "Balanced deterministic design coverage over direct finite-shot representative cases. "
            "Scenario frequencies are not probabilities or forecasts."
        ),
        "input_csv": relative(args.input_csv),
        "finite_shot_input": relative(args.finite_shot),
        "schedule_input": relative(args.schedule_csv),
        "replacement_input": relative(args.replacement),
        "detail_csv": relative(args.output_csv),
        "detail_csv_sha256": csv_sha256,
        "parameter_origins": PARAMETER_ORIGINS,
        "parameter_levels": PARAMETERS,
        "design": {
            "method": "deterministic marginally balanced discrete space-filling sample",
            "seed": DESIGN_SEED,
            "requested_points": args.design_points,
            "unique_points": len(scenarios),
            "scenario_probability_assigned": False,
            "representative_records": len(selected_ids),
            "evaluated_case_points": len(detail_rows),
            "coverage": coverage,
        },
        "scenario_summaries": scenario_summaries,
        "main_phase_map": {
            "axes": ["factory_supply_multiplier", "useful_lanes"],
            "fixed_assumptions": phase_base,
            "cells": phase_cells,
            "stable_region": {
                "definition": "factory supply <=100x and 12/12 eligible records agree within each cell",
                "cells": len(stable_cells),
                "target": stable_target,
                "cell_mode_fraction": stable_fraction,
                "interpretation": (
                    "This is a deterministic robustness region, not the probability of a future technology."
                ),
            },
        },
        "trace_aware_logical_lower_bound": trace_lower_bound,
        "matched_mechanism_replacement": replacement_result,
        "boss_qccd_conditional_bounds": replacement["boss_summary"],
        "headline": {
            "quality_first_rule": (
                "Only same-record full-loop finite-shot passes receive application-level hardware targets."
            ),
            "stable_first_target": stable_target,
            "stable_region_cells": len(stable_cells),
            "phase_map_target_types": sorted(set(
                cell["eligible_first_target_mode"] for cell in phase_cells
                if cell["eligible_first_target_mode"] is not None
            )),
            "lsqca_result": replacement_result["summary"],
        },
        "internal_errors": internal_errors,
    }
    json_dump(args.output_json, payload)
    print(json.dumps({
        "output_json": relative(args.output_json),
        "output_csv": relative(args.output_csv),
        "audit_status": payload["audit_status"],
        "design": payload["design"],
        "headline": payload["headline"],
        "internal_errors": internal_errors,
    }, indent=2, sort_keys=True))
    if internal_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
