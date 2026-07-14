#!/usr/bin/env python3
"""Build an auditable reliability and physical-space contract for QArchGauge.

The audit deliberately separates two contracts.  ``strict_all_shots`` requires
the union-bound probability of any logical, distillation, or synthesis failure
across the full estimator to fit the application budget.  The
``estimator_tolerant`` contract is emitted only for records with matched
finite-shot quality: it permits a bounded fraction of corrupted shots while
keeping the probability of exceeding measured quality headroom below the same
application budget.

This is a conservative resource envelope, not a cycle-accurate FT compiler.
Every place where the measured corpus lacks an event trace is recorded as an
unsupported-scope flag instead of being silently filled by a favorable value.
"""

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from strong_accept_common import (
    DEFAULT_INPUT,
    ROOT,
    TOLERANCES,
    as_float,
    as_int,
    json_dump,
    median,
    quantile,
    read_rows,
    record_id,
    relative,
    structural_config_id,
)


DEFAULT_OUTPUT = ROOT / "data/processed/perlmutter/ft_reliability_and_space_budget.json"
DEFAULT_QUALITY = ROOT / "data/processed/perlmutter/quality_qualified_target_map.csv"
DEFAULT_FINITE_SHOT = ROOT / "data/processed/perlmutter/finite_shot_quality_sensitivity.json"
DEFAULT_SCHEDULE = ROOT / "data/processed/perlmutter/dependency_schedule_coverage.csv"
DEFAULT_CHEM = ROOT / "data/processed/perlmutter/chem_controlled_compiled_measurement_records.json"
DEFAULT_QDK = ROOT / "data/processed/perlmutter/qdk_resource_estimator_qaoa_depth_crosscheck.json"

APPLICATION_FAILURE_BUDGETS = (0.01, 0.001)
PHYSICAL_ERROR_RATES = (1.0e-3, 1.0e-4)
T_STATES_PER_ROTATION_SWEEP = (4, 8, 16, 32)

# Current QDK GenericQEC defaults and the gate-based e3/e4 model used by the
# repository's QAOA cross-check.
QEC_CROSSING_PREFACTOR = 0.03
QEC_THRESHOLD = 0.01
PHYSICAL_QUBITS_PER_LOGICAL_COEFFICIENT = 2
SYNDROME_ROUND_SEC = 0.4e-6

# LSQCA reports a 176-logical-cell factory producing one magic state every 15
# code beats.  A code beat is distance syndrome rounds.
FACTORY_LOGICAL_CELLS = 176
FACTORY_CODE_BEATS_PER_STATE = 15
BASELINE_FACTORY_COUNT = 64
USEFUL_SHOT_LANES = 10000

# Khalid et al. decompose an end-to-end communication path into 0.15, 2, 0.5,
# 1, 4, and 0.15 us stages.  Decoder service is swept separately; no queue tail
# is fabricated.
COMMUNICATION_FLOOR_SEC = 7.8e-6
DECODER_SERVICE_ENVELOPES_SEC = (1.0e-6, 5.0e-6, 63.0e-6)
HOST_FEEDBACK_SEC_PER_EVALUATION = 5.0e-6

# Current QDK documentation reproduces these Litinski19 factory entries.  Space
# already includes factory QEC overhead and is therefore kept separate from the
# LSQCA 176-logical-cell throughput envelope.
QDK_LITINSKI_FACTORY_TABLE = (
    {"output_error": 4.4e-8, "physical_qubits": 810, "syndrome_rounds": 18.1},
    {"output_error": 1.5e-9, "physical_qubits": 762, "syndrome_rounds": 36.2},
    {"output_error": 9.3e-10, "physical_qubits": 1150, "syndrome_rounds": 18.1},
    {"output_error": 1.9e-11, "physical_qubits": 2070, "syndrome_rounds": 30.0},
    {"output_error": 2.4e-15, "physical_qubits": 16400, "syndrome_rounds": 90.3},
    {"output_error": 6.3e-25, "physical_qubits": 18600, "syndrome_rounds": 67.8},
)


def load_json(path):
    return json.loads(Path(path).read_text())


def read_csv_index(path, key):
    with Path(path).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {row[key]: row for row in rows}, rows


def logical_qubits(row):
    workload = row["workload"]
    if workload == "ml":
        return max(1, as_int(row, "ml_features", 1))
    if workload == "chemistry":
        return 4 if Path(row.get("chem_hamiltonian_json", "")).name else 2
    if workload == "optimization":
        return max(1, as_int(row, "opt_nodes", 1))
    return max(1, as_int(row, "sim_qubits", 1))


def chem_key(row):
    fixture = Path(row.get("chem_hamiltonian_json", "")).name
    name = "molecular_chain_4q_surrogate" if fixture else "H2_minimal_2qubit"
    return name, as_int(row, "chem_layers", 1)


def load_chem_records(path):
    artifact = load_json(path)
    records = {}
    for record in artifact["records"]:
        if record.get("evidence_level") != "compiled_executed_ansatz":
            continue
        topology = next(
            item for item in record["topologies"]
            if item["topology"] == "all_to_all"
        )
        shots = float(record["shot_executions_per_eval"])
        weighted = topology["per_evaluation_shot_weighted"]
        records[(record["fixture"], int(record["layers"]))] = {
            "shot_executions_per_eval": int(shots),
            "measurement_groups_per_eval": int(record["measurement_groups_per_eval"]),
            "oneq_per_shot": float(weighted["one_qubit_gates"]) / shots,
            "twoq_per_shot": float(weighted["two_qubit_gates"]) / shots,
            "measurement_per_shot": float(weighted["measurement_ops"]) / shots,
            "rotations_per_shot": float(record["arbitrary_rotations_per_group"]),
            "source": relative(path),
        }
    return records


def quality_index(path):
    with Path(path).open(newline="") as handle:
        rows = [
            row for row in csv.DictReader(handle)
            if abs(float(row["tolerance_multiplier"]) - 1.0) < 1.0e-12
        ]
    return {row["record_id"]: row for row in rows}, rows


def finite_shot_index(path, shots=10000):
    artifact = load_json(path)
    return {
        record["source_record_id"]: record
        for record in artifact["records"]
        if int(record["shots"]) == int(shots)
    }, artifact


def raw_workload(row):
    path = ROOT / row["path"]
    payload = load_json(path)
    return payload["workloads"][row["workload"]], payload.get("config", {})


def arbitrary_rotations_without_shots(row, raw):
    """Count rotation positions across the implemented static application loop."""
    workload = row["workload"]
    evals = max(1, as_int(row, "circuit_evaluations", 1))
    if workload == "ml":
        # Every recorded one-qubit gate in the feature path is an Ry or Rz.
        return as_float(row, "one_qubit_gates"), "source-derived ML Ry/Rz count"
    if workload == "chemistry":
        theta = raw["quantum_path"].get("best_theta", [])
        return float(len(theta) * evals), "best-ansatz parameter count times static candidates"
    if workload == "optimization":
        edges = len(raw["problem"]["edges"])
        nodes = int(raw["problem"]["nodes"])
        return float((edges + nodes) * evals), "one Rz per cost edge plus one Rx per node"
    qubits = int(raw["problem"]["qubits"])
    steps = int(raw["problem"]["steps"])
    if raw["problem"]["name"] == "tfim":
        per_step = (qubits - 1) + qubits
    else:
        per_step = 3 * (qubits - 1) + qubits
    return float(per_step * steps), "source-derived Trotter rotation count"


def extracted_angles(row, raw, config):
    workload = row["workload"]
    if workload == "chemistry":
        return [float(value) for value in raw["quantum_path"].get("best_theta", [])], "selected VQE parameters"
    if workload == "optimization":
        quantum = raw["quantum_path"]
        return [float(quantum["best_gamma"]), 2.0 * float(quantum["best_beta"])], "selected QAOA cost/mixer angles"
    if workload == "simulation":
        problem = raw["problem"]
        dt = float(problem["time"]) / int(problem["steps"])
        coupling = abs(2.0 * float(problem["coupling"]) * dt)
        field = abs(2.0 * float(problem["field"]) * dt)
        return [coupling, field], "Trotter angles reconstructed from recorded physical parameters"
    return [], "ML sample values were not retained in the raw result"


def angle_classification(values):
    wrapped = []
    for value in values:
        angle = abs(float(value)) % (2.0 * math.pi)
        wrapped.append(min(angle, 2.0 * math.pi - angle))

    def on_grid(value, step, tolerance=1.0e-10):
        return abs(value / step - round(value / step)) <= tolerance

    count = len(wrapped)
    return {
        "angles": count,
        "absolute_angle_median_rad": median(wrapped),
        "absolute_angle_p90_rad": quantile(wrapped, 0.9),
        "zero_fraction": sum(value <= 1.0e-12 for value in wrapped) / max(1, count),
        "clifford_grid_fraction": sum(on_grid(value, math.pi / 2.0) for value in wrapped) / max(1, count),
        "clifford_t_grid_fraction": sum(on_grid(value, math.pi / 4.0) for value in wrapped) / max(1, count),
        "small_pi_over_16_fraction": sum(value <= math.pi / 16.0 for value in wrapped) / max(1, count),
    }


def logical_error_rate(distance, physical_error_rate):
    exponent = (int(distance) + 1) // 2
    return QEC_CROSSING_PREFACTOR * (
        float(physical_error_rate) / QEC_THRESHOLD
    ) ** exponent


def select_distance(logical_locations, logical_budget, physical_error_rate):
    volume = max(1.0, float(logical_locations))
    budget = max(1.0e-30, float(logical_budget))
    for distance in range(3, 100, 2):
        rate = logical_error_rate(distance, physical_error_rate)
        if volume * rate <= budget:
            return {
                "distance": distance,
                "logical_error_per_location": rate,
                "union_bound_failure_probability": volume * rate,
                "distance_search_exhausted": False,
            }
    distance = 99
    rate = logical_error_rate(distance, physical_error_rate)
    return {
        "distance": distance,
        "logical_error_per_location": rate,
        "union_bound_failure_probability": volume * rate,
        "distance_search_exhausted": True,
    }


def binomial_cdf(k, n, probability):
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    p = min(1.0 - 1.0e-15, max(0.0, float(probability)))
    if p == 0.0:
        return 1.0
    term = math.exp(n * math.log1p(-p))
    total = term
    ratio = p / (1.0 - p)
    for index in range(1, k + 1):
        term *= (n - index + 1) / index * ratio
        total += term
    return min(1.0, max(0.0, total))


def maximum_binomial_rate(shots, tolerated_bad_shots, tail_budget):
    n = int(shots)
    k = min(n, max(0, int(tolerated_bad_shots)))
    if k >= n:
        return 1.0
    target = float(tail_budget)
    low, high = 0.0, min(0.5, max(1.0e-9, 4.0 * (k + 1) / n))
    while 1.0 - binomial_cdf(k, n, high) < target and high < 1.0:
        high = min(1.0, 2.0 * high)
    for _ in range(90):
        middle = 0.5 * (low + high)
        tail = 1.0 - binomial_cdf(k, n, middle)
        if tail <= target:
            low = middle
        else:
            high = middle
    return low


def leading_t_count(synthesis_error_budget):
    epsilon = min(1.0, max(1.0e-30, float(synthesis_error_budget)))
    return max(0, int(math.ceil(3.0 * math.log2(1.0 / epsilon))))


def select_factory_protocol(required_output_error):
    candidates = [
        dict(record) for record in QDK_LITINSKI_FACTORY_TABLE
        if record["output_error"] <= required_output_error
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda record: (record["physical_qubits"], record["syndrome_rounds"]))


def circuit_contract(row, schedule, chem_records, raw):
    workload = row["workload"]
    evals = max(1, as_int(row, "circuit_evaluations", 1))
    compiled = chem_records.get(chem_key(row)) if workload == "chemistry" else None
    if compiled:
        shot_executions_per_eval = compiled["shot_executions_per_eval"]
        oneq_without_shots = evals * compiled["oneq_per_shot"]
        twoq_without_shots = evals * compiled["twoq_per_shot"]
        measurement_without_shots = evals * compiled["measurement_per_shot"]
        rotations_without_shots = evals * compiled["rotations_per_shot"]
        attachment = compiled["source"]
    else:
        shot_executions_per_eval = int(float(schedule["shot_executions_per_eval"]))
        oneq_without_shots = as_float(row, "one_qubit_gates")
        twoq_without_shots = as_float(row, "two_qubit_gates")
        measurement_without_shots = as_float(row, "measurement_ops")
        rotations_without_shots, attachment = arbitrary_rotations_without_shots(row, raw)

    total_shot_executions = evals * shot_executions_per_eval
    logical_locations = shot_executions_per_eval * (
        oneq_without_shots + 2.0 * twoq_without_shots + measurement_without_shots
    )
    weighted_gate_cycles = shot_executions_per_eval * (
        oneq_without_shots + 4.0 * twoq_without_shots + measurement_without_shots
    )
    total_rotations = shot_executions_per_eval * rotations_without_shots
    ready = min(
        USEFUL_SHOT_LANES,
        max(1.0, float(schedule["serial_evaluation_ready"])),
    )
    return {
        "evaluations": evals,
        "shot_executions_per_evaluation": shot_executions_per_eval,
        "total_shot_executions": total_shot_executions,
        "oneq_without_shots": oneq_without_shots,
        "twoq_without_shots": twoq_without_shots,
        "measurement_without_shots": measurement_without_shots,
        "rotations_without_shots": rotations_without_shots,
        "logical_locations": logical_locations,
        "logical_locations_per_shot": logical_locations / total_shot_executions,
        "weighted_gate_cycles": weighted_gate_cycles,
        "total_rotations": total_rotations,
        "rotations_per_shot": total_rotations / total_shot_executions,
        "effective_shot_lanes": ready,
        "schedule_provenance": schedule["provenance"],
        "gate_attachment": attachment,
    }


def strict_budget(contract, application_failure_budget):
    source_budget = application_failure_budget / 3.0
    return {
        "contract": "strict_all_shots",
        "application_failure_budget": application_failure_budget,
        "logical_fault_budget": source_budget,
        "distillation_fault_budget": source_budget,
        "synthesis_fault_budget": source_budget,
        "logical_location_basis": contract["logical_locations"],
        "rotation_basis": contract["total_rotations"],
        "shot_basis": contract["total_shot_executions"],
        "quality_headroom": None,
        "tolerated_bad_shots": 0,
        "scope": "full estimator union bound; every source receives one third of the application budget",
    }


def estimator_tolerant_budget(contract, finite_record, application_failure_budget):
    tolerance = float(finite_record["quality_tolerance"])
    p90_gap = quantile(finite_record["replicate_quality_gap"], 0.9)
    headroom = max(0.0, tolerance - p90_gap)
    # The Sim observable lies in [-1, 1], so an adversarial corrupted shot can
    # move its estimator by at most two.  No such contract is inferred for the
    # other workloads.
    observable_range = 2.0
    shots = int(finite_record["shots"])
    tolerated = int(math.floor(shots * headroom / observable_range))
    total_bad_shot_rate = maximum_binomial_rate(
        shots, tolerated, application_failure_budget
    )
    source_rate = total_bad_shot_rate / 3.0
    return {
        "contract": "estimator_tolerant",
        "application_failure_budget": application_failure_budget,
        "logical_fault_budget": source_rate,
        "distillation_fault_budget": source_rate,
        "synthesis_fault_budget": source_rate,
        "logical_location_basis": contract["logical_locations_per_shot"],
        "rotation_basis": contract["rotations_per_shot"],
        "shot_basis": 1,
        "quality_headroom": headroom,
        "finite_shot_gap_p90": p90_gap,
        "observable_range": observable_range,
        "tolerated_bad_shots": tolerated,
        "maximum_total_bad_shot_rate": total_bad_shot_rate,
        "scope": "matched Sim output; binomial corruption tail plus worst-case bounded-observable bias",
    }


def runtime_and_space(row, contract, reliability, distance, t_per_rotation, factory_protocol):
    d = int(distance)
    logical_cycle_sec = d * SYNDROME_ROUND_SEC
    lanes = contract["effective_shot_lanes"]
    shot_waves = contract["total_shot_executions"] / lanes
    logical_sec = contract["weighted_gate_cycles"] * logical_cycle_sec / lanes
    decoder_service = 5.0e-6
    decoder_reaction_sec = decoder_service + COMMUNICATION_FLOOR_SEC
    decoder_sec = shot_waves * decoder_reaction_sec
    host_sec = contract["evaluations"] * HOST_FEEDBACK_SEC_PER_EVALUATION
    nonfactory_floor_sec = logical_sec + decoder_sec + host_sec

    total_t_states = contract["total_rotations"] * t_per_rotation
    factory_numerator = (
        total_t_states * FACTORY_CODE_BEATS_PER_STATE * logical_cycle_sec
    )
    crossover_factories = max(1, int(math.ceil(
        factory_numerator / max(nonfactory_floor_sec, 1.0e-30)
    )))
    native_deadline = max(1.0e-30, as_float(row, "native_runtime_sec"))
    if nonfactory_floor_sec >= native_deadline:
        parity_factories = None
        parity_status = "blocked_by_nonfactory_floor"
    else:
        parity_factories = max(1, int(math.ceil(
            factory_numerator / (native_deadline - nonfactory_floor_sec)
        )))
        parity_status = "finite_factory_count"

    qubits = logical_qubits(row)
    physical_per_logical_cell = PHYSICAL_QUBITS_PER_LOGICAL_COEFFICIENT * d * d
    data_physical_qubits = qubits * physical_per_logical_cell
    conventional_core_cells = int(math.ceil(qubits / 0.5))
    point_sam_core_cells = qubits + 1 + 6
    point_sam_density = qubits / point_sam_core_cells
    access_distance = max(1, int(math.ceil(math.sqrt(qubits))))
    # LSQCA derives a 7*sqrt(n)-beat worst-case point-SAM load.  Charging the
    # reverse store as well yields the conservative 14*sqrt(n) envelope.
    load_store_beats_per_operand = 14 * access_distance
    operand_accesses = contract["logical_locations"]
    point_sam_serial_upper_sec = (
        operand_accesses * load_store_beats_per_operand * logical_cycle_sec / lanes
    )

    lsqca_factory_qubits = (
        crossover_factories * FACTORY_LOGICAL_CELLS * physical_per_logical_cell
    )
    qdk_factory_qubits = None
    if factory_protocol is not None:
        qdk_factory_qubits = (
            crossover_factories * int(factory_protocol["physical_qubits"])
        )

    syndrome_bits_per_round_data = qubits * d * d
    syndrome_bandwidth_data = syndrome_bits_per_round_data / SYNDROME_ROUND_SEC
    decoder_envelopes = []
    for service in DECODER_SERVICE_ENVELOPES_SEC:
        reaction = service + COMMUNICATION_FLOOR_SEC
        correction_patches_per_factory = int(math.ceil(reaction / logical_cycle_sec))
        decoder_envelopes.append({
            "decoder_service_sec": service,
            "communication_sec": COMMUNICATION_FLOOR_SEC,
            "reaction_sec": reaction,
            "correction_storage_patches_per_factory": correction_patches_per_factory,
            "correction_storage_physical_qubits_at_crossover": (
                correction_patches_per_factory
                * crossover_factories
                * physical_per_logical_cell
            ),
        })

    return {
        "logical_cycle_sec": logical_cycle_sec,
        "logical_pipeline_sec": logical_sec,
        "decoder_reaction_floor_sec": decoder_sec,
        "host_feedback_floor_sec": host_sec,
        "nonfactory_floor_sec": nonfactory_floor_sec,
        "native_deadline_sec": native_deadline,
        "nonfactory_native_ratio": nonfactory_floor_sec / native_deadline,
        "total_t_states": total_t_states,
        "factory_count_to_nonfactory_crossover": crossover_factories,
        "factory_supply_multiplier_to_crossover": crossover_factories / BASELINE_FACTORY_COUNT,
        "factory_count_to_native_parity": parity_factories,
        "native_parity_status": parity_status,
        "data_physical_qubits": data_physical_qubits,
        "floorplan": {
            "conventional_core_cells_at_50_percent_density": conventional_core_cells,
            "point_sam_core_cells_including_six_cell_cr": point_sam_core_cells,
            "point_sam_memory_density": point_sam_density,
            "point_sam_load_store_serial_upper_sec": point_sam_serial_upper_sec,
            "point_sam_access_code_beats_per_operand_upper": load_store_beats_per_operand,
            "factory_cells_excluded_from_memory_density": True,
            "scope": "matched operand-count upper bound; no locality-aware-store benefit is assumed",
        },
        "factory_space": {
            "lsqca_176_cell_envelope_physical_qubits_at_crossover": lsqca_factory_qubits,
            "qdk_protocol_physical_qubits_at_crossover": qdk_factory_qubits,
            "models_are_reported_separately": True,
        },
        "decoder": {
            "syndrome_bits_per_round_data": syndrome_bits_per_round_data,
            "syndrome_bandwidth_bits_per_sec_data": syndrome_bandwidth_data,
            "reaction_envelopes": decoder_envelopes,
            "factory_internal_syndrome_bandwidth_not_composed": True,
        },
    }


def qdk_distance_crosscheck(path):
    artifact = load_json(path)
    records = []
    mismatches = []
    for case in artifact["records"]:
        for model_name, estimate in case["estimates"].items():
            qubits = float(estimate["algorithmic_logical_qubits_after_layout"])
            depth = float(estimate["algorithmic_logical_depth"])
            volume = qubits * depth
            budget = float(estimate["error_budget"]["logical"])
            physical_error = float(estimate["qubit_params"]["twoQubitGateErrorRate"])
            selected = select_distance(volume, budget, physical_error)
            expected = int(estimate["code_distance"])
            record = {
                "qubits": case["qubits"],
                "depth_p": case["depth_p"],
                "model": model_name,
                "logical_volume": volume,
                "logical_budget": budget,
                "selected_distance": selected["distance"],
                "qdk_distance": expected,
                "match": selected["distance"] == expected,
            }
            records.append(record)
            if not record["match"]:
                mismatches.append(record)
    return {
        "source": relative(path),
        "records": len(records),
        "matches": len(records) - len(mismatches),
        "mismatches": mismatches,
        "status": "PASS" if not mismatches else "FAIL",
    }


def summarize_rows(rows, selector):
    subset = [row for row in rows if selector(row)]
    if not subset:
        return {"records": 0}
    distances = [row["distance"] for row in subset]
    crossovers = [row["factory_supply_multiplier_to_crossover"] for row in subset]
    factory_counts = [row["factory_count_to_nonfactory_crossover"] for row in subset]
    nonfactory = [row["nonfactory_native_ratio"] for row in subset]
    data_qubits = [row["data_physical_qubits"] for row in subset]
    lsqca_factory_qubits = [
        row["factory_space"][
            "lsqca_176_cell_envelope_physical_qubits_at_crossover"
        ]
        for row in subset
    ]
    decoder_storage = [
        row["decoder"]["reaction_envelopes"][1][
            "correction_storage_physical_qubits_at_crossover"
        ]
        for row in subset
    ]
    syndrome_bandwidth = [
        row["decoder"]["syndrome_bandwidth_bits_per_sec_data"]
        for row in subset
    ]
    t_counts = [row["t_states_per_rotation"] for row in subset]
    return {
        "records": len(subset),
        "distance_values": sorted(set(distances)),
        "distance_median": median(distances),
        "factory_crossover_multiplier_median": median(crossovers),
        "factory_crossover_multiplier_range": [min(crossovers), max(crossovers)],
        "factory_count_to_crossover_median": median(factory_counts),
        "factory_count_to_crossover_range": [min(factory_counts), max(factory_counts)],
        "nonfactory_native_ratio_median": median(nonfactory),
        "required_t_states_per_rotation_values": sorted(set(t_counts)),
        "data_physical_qubits_median": median(data_qubits),
        "data_physical_qubits_range": [min(data_qubits), max(data_qubits)],
        "lsqca_factory_physical_qubits_at_crossover_median": median(
            lsqca_factory_qubits
        ),
        "decoder_correction_storage_qubits_at_5us_service_median": median(
            decoder_storage
        ),
        "data_syndrome_bandwidth_bits_per_sec_median": median(
            syndrome_bandwidth
        ),
        "selected_factory_protocol_counts": dict(Counter(
            "none" if row["selected_qdk_factory_protocol"] is None
            else "error={}:qubits={}".format(
                row["selected_qdk_factory_protocol"]["output_error"],
                row["selected_qdk_factory_protocol"]["physical_qubits"],
            )
            for row in subset
        )),
        "native_parity_feasible_fraction": sum(
            row["native_parity_status"] == "finite_factory_count" for row in subset
        ) / len(subset),
        "synthesis_proxy_feasible_fraction": sum(
            row["synthesis_proxy_feasible"] for row in subset
        ) / len(subset),
    }


def subtype_summaries(record_rows, main_rows):
    metadata = {}
    for row in main_rows:
        config = structural_config_id(row)
        metadata.setdefault(config, {
            "structural_config_id": config,
            "workload": row["workload"],
            "family": row["family"],
            "main_records": 0,
        })
        metadata[config]["main_records"] += 1
    grouped = defaultdict(list)
    for row in record_rows:
        grouped[row["structural_config_id"]].append(row)
    output = []
    for config in sorted(metadata):
        rows = grouped[config]
        item = dict(metadata[config])
        item["contracts"] = {}
        keys = sorted({
            (row["contract"], row["application_failure_budget"], row["physical_error_rate"])
            for row in rows
            if row["t_count_mode"] == "reliability_leading_term"
        })
        for contract, budget, physical_error in keys:
            selected = [
                row for row in rows
                if row["contract"] == contract
                and row["application_failure_budget"] == budget
                and row["physical_error_rate"] == physical_error
                and row["t_count_mode"] == "reliability_leading_term"
            ]
            name = "{}:failure={}:physical={}".format(contract, budget, physical_error)
            item["contracts"][name] = summarize_rows(selected, lambda _: True)
        item["unsupported_scope_flags"] = sorted({
            flag for row in rows for flag in row["unsupported_scope_flags"]
        })
        output.append(item)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT))
    parser.add_argument("--quality-csv", default=str(DEFAULT_QUALITY))
    parser.add_argument("--finite-shot", default=str(DEFAULT_FINITE_SHOT))
    parser.add_argument("--schedule-csv", default=str(DEFAULT_SCHEDULE))
    parser.add_argument("--chem-compiled", default=str(DEFAULT_CHEM))
    parser.add_argument("--qdk-crosscheck", default=str(DEFAULT_QDK))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT.with_suffix(".csv")))
    args = parser.parse_args()

    rows = read_rows(args.input_csv)
    quality, quality_rows = quality_index(args.quality_csv)
    finite, finite_artifact = finite_shot_index(args.finite_shot)
    schedules, schedule_rows = read_csv_index(args.schedule_csv, "record_id")
    chem_records = load_chem_records(args.chem_compiled)
    qdk_crosscheck = qdk_distance_crosscheck(args.qdk_crosscheck)

    angle_values = defaultdict(list)
    angle_sources = defaultdict(Counter)
    record_rows = []
    full_records = []
    for row in rows:
        rid = record_id(row)
        raw, raw_config = raw_workload(row)
        contract = circuit_contract(row, schedules[rid], chem_records, raw)
        angles, angle_source = extracted_angles(row, raw, raw_config)
        angle_values[row["workload"]].extend(angles)
        angle_sources[row["workload"]][angle_source] += 1
        quality_record = quality[rid]
        eligible = quality_record["hardware_target_eligible"] == "True"

        budgets = []
        for failure_budget in APPLICATION_FAILURE_BUDGETS:
            budgets.append(strict_budget(contract, failure_budget))
            if eligible and rid in finite and row["workload"] == "simulation":
                budgets.append(estimator_tolerant_budget(
                    contract, finite[rid], failure_budget
                ))

        compact_contracts = []
        for reliability in budgets:
            for physical_error in PHYSICAL_ERROR_RATES:
                distance_result = select_distance(
                    reliability["logical_location_basis"],
                    reliability["logical_fault_budget"],
                    physical_error,
                )
                rotation_basis = max(1.0, reliability["rotation_basis"])
                per_rotation_budget = reliability["synthesis_fault_budget"] / rotation_basis
                required_t = leading_t_count(per_rotation_budget)
                t_modes = [
                    ("sweep", value) for value in T_STATES_PER_ROTATION_SWEEP
                ] + [("reliability_leading_term", required_t)]
                contract_entries = []
                for t_mode, t_per_rotation in t_modes:
                    t_basis = rotation_basis * max(1, t_per_rotation)
                    required_t_error = reliability["distillation_fault_budget"] / t_basis
                    protocol = select_factory_protocol(required_t_error)
                    physical = runtime_and_space(
                        row,
                        contract,
                        reliability,
                        distance_result["distance"],
                        max(1, t_per_rotation),
                        protocol,
                    )
                    synthesis_error_proxy = 2.0 ** (-max(0, t_per_rotation) / 3.0)
                    synthesis_feasible = synthesis_error_proxy <= per_rotation_budget
                    flags = []
                    if not eligible:
                        flags.append("not_quality_qualified_for_application_level_hardware_target")
                    if row["workload"] == "chemistry":
                        flags.append("finite_shot_outer_optimizer_not_measured")
                    if row["workload"] == "optimization":
                        flags.append("finite_shot_parameter_search_not_measured")
                    if row["workload"] == "ml":
                        flags.append("physical_amplitude_feature_measurement_not_defined")
                    if not synthesis_feasible:
                        flags.append("selected_t_count_below_leading_term_synthesis_budget")
                    if protocol is None:
                        flags.append("qdk_factory_table_has_no_protocol_below_required_t_error")
                    flags.extend((
                        "no_factory_internal_syndrome_trace",
                        "no_rotation_anticommutation_depth_trace",
                        "no_locality_aware_lsqca_reference_trace",
                        "rotation_synthesis_uses_leading_term_not_emitted_compiler_trace",
                    ))
                    output = {
                        "record_id": rid,
                        "structural_config_id": structural_config_id(row),
                        "workload": row["workload"],
                        "family": row["family"],
                        "hardware_target_eligible": eligible,
                        "contract": reliability["contract"],
                        "application_failure_budget": reliability[
                            "application_failure_budget"
                        ],
                        "physical_error_rate": physical_error,
                        "logical_location_basis": reliability["logical_location_basis"],
                        "logical_fault_budget": reliability["logical_fault_budget"],
                        "distance": distance_result["distance"],
                        "logical_error_per_location": distance_result["logical_error_per_location"],
                        "logical_failure_union_bound": distance_result["union_bound_failure_probability"],
                        "t_count_mode": t_mode,
                        "t_states_per_rotation": max(1, t_per_rotation),
                        "required_t_states_per_rotation_leading_term": required_t,
                        "per_rotation_synthesis_error_budget": per_rotation_budget,
                        "synthesis_error_leading_proxy": synthesis_error_proxy,
                        "synthesis_proxy_feasible": synthesis_feasible,
                        "required_t_state_output_error": required_t_error,
                        "selected_qdk_factory_protocol": protocol,
                        "unsupported_scope_flags": sorted(set(flags)),
                        **physical,
                    }
                    record_rows.append(output)
                    contract_entries.append(output)
                reliable = next(
                    item for item in contract_entries
                    if item["t_count_mode"] == "reliability_leading_term"
                )
                compact_contracts.append({
                    "contract": reliability,
                    "physical_error_rate": physical_error,
                    "distance": distance_result,
                    "reliability_leading_term": reliable,
                    "sweep": [
                        item for item in contract_entries
                        if item["t_count_mode"] == "sweep"
                    ],
                })
        if eligible:
            full_records.append({
                "record_id": rid,
                "workload": row["workload"],
                "quality_evidence": quality_record,
                "circuit_contract": contract,
                "ft_contracts": compact_contracts,
            })

    subtype_records = subtype_summaries(record_rows, rows)
    default_rows = [
        row for row in record_rows
        if row["contract"] == "strict_all_shots"
        and row["application_failure_budget"] == 0.01
        and row["physical_error_rate"] == 1.0e-3
        and row["t_count_mode"] == "reliability_leading_term"
    ]
    eligible_default = [row for row in default_rows if row["hardware_target_eligible"]]
    by_workload = {
        workload: {
            "all_records_conditional": summarize_rows(
                default_rows, lambda row, w=workload: row["workload"] == w
            ),
            "quality_qualified_records": summarize_rows(
                eligible_default, lambda row, w=workload: row["workload"] == w
            ),
        }
        for workload in sorted({row["workload"] for row in rows})
    }
    eligible_t_sweep = {
        str(t_count): summarize_rows(
            record_rows,
            lambda record, t=t_count: (
                record["hardware_target_eligible"]
                and record["contract"] == "strict_all_shots"
                and record["application_failure_budget"] == 0.01
                and record["physical_error_rate"] == 1.0e-3
                and record["t_count_mode"] == "sweep"
                and record["t_states_per_rotation"] == t
            ),
        )
        for t_count in T_STATES_PER_ROTATION_SWEEP
    }

    internal_errors = []
    if len(rows) != 3552:
        internal_errors.append("expected 3552 main records")
    if len(quality_rows) != len(rows):
        internal_errors.append("default quality map does not cover every main record")
    if len(schedule_rows) != len(rows):
        internal_errors.append("dependency schedule does not cover every main record")
    if qdk_crosscheck["status"] != "PASS":
        internal_errors.append("surface-code distance formula does not match QDK cross-check")
    if len(subtype_records) != 222:
        internal_errors.append("expected 222 structural subtypes")
    if any(row["distance"] % 2 == 0 for row in record_rows):
        internal_errors.append("even code distance emitted")
    if any(
        row["contract"] == "estimator_tolerant"
        and not row["hardware_target_eligible"]
        for row in record_rows
    ):
        internal_errors.append("estimator-tolerant contract escaped quality gate")
    if any(
        eligible_t_sweep[str(t_count)]["records"] != len(full_records)
        for t_count in T_STATES_PER_ROTATION_SWEEP
    ):
        internal_errors.append("T-state sensitivity does not cover every eligible record")
    required_subtype_fields = {
        "factory_count_to_crossover_median",
        "data_physical_qubits_median",
        "lsqca_factory_physical_qubits_at_crossover_median",
        "decoder_correction_storage_qubits_at_5us_service_median",
        "data_syndrome_bandwidth_bits_per_sec_median",
    }
    for subtype in subtype_records:
        for contract_summary in subtype["contracts"].values():
            if not required_subtype_fields.issubset(contract_summary):
                internal_errors.append(
                    "subtype {} lacks physical contract fields".format(
                        subtype["structural_config_id"]
                    )
                )
                break

    prior_low, prior_high = 1.0e4, 1.63e4
    eligible_crossover = [
        row["factory_supply_multiplier_to_crossover"]
        for row in eligible_default
    ]
    if eligible_crossover:
        disposition = {
            "prior_claim_range": [prior_low, prior_high],
            "quality_and_ft_qualified_range": [min(eligible_crossover), max(eligible_crossover)],
            "quality_and_ft_qualified_median": median(eligible_crossover),
            "prior_range_preserved": (
                min(eligible_crossover) >= prior_low
                and max(eligible_crossover) <= prior_high
            ),
            "required_action": (
                "preserve with narrowed scope" if (
                    min(eligible_crossover) >= prior_low
                    and max(eligible_crossover) <= prior_high
                ) else "replace the prior cross-workload headline with this qualified range"
            ),
        }
    else:
        disposition = {
            "prior_claim_range": [prior_low, prior_high],
            "quality_and_ft_qualified_range": None,
            "prior_range_preserved": False,
            "required_action": "delete application-level factory crossover claim",
        }

    angle_summary = {}
    for workload in sorted({row["workload"] for row in rows}):
        angle_summary[workload] = {
            **angle_classification(angle_values[workload]),
            "source_counts": dict(angle_sources[workload]),
            "used_to_reduce_rotation_demand": False,
            "reason": (
                "The artifact preserves selected or reconstructed angles, not a complete emitted rotation trace for every static evaluation."
            ),
        }

    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    csv_fields = [
        "record_id", "structural_config_id", "workload", "family",
        "hardware_target_eligible", "contract", "application_failure_budget",
        "physical_error_rate", "logical_location_basis", "logical_fault_budget",
        "distance", "logical_error_per_location", "logical_failure_union_bound",
        "t_count_mode", "t_states_per_rotation",
        "required_t_states_per_rotation_leading_term",
        "per_rotation_synthesis_error_budget", "synthesis_error_leading_proxy",
        "synthesis_proxy_feasible", "required_t_state_output_error",
        "nonfactory_floor_sec", "native_deadline_sec", "nonfactory_native_ratio",
        "total_t_states", "factory_count_to_nonfactory_crossover",
        "factory_supply_multiplier_to_crossover", "factory_count_to_native_parity",
        "native_parity_status", "data_physical_qubits", "unsupported_scope_flags",
    ]
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields, lineterminator="\n")
        writer.writeheader()
        for row in record_rows:
            serialized = {key: row.get(key) for key in csv_fields}
            serialized["unsupported_scope_flags"] = ";".join(row["unsupported_scope_flags"])
            writer.writerow(serialized)

    payload = {
        "schema": "qarchgauge.ft-reliability-space-budget.v1",
        "audit_status": "FAIL" if internal_errors else "PASS",
        "p0_completion_status": (
            "PASS_WITH_RESTRICTED_APPLICATION_SCOPE"
            if not internal_errors else "BLOCKED"
        ),
        "scope": (
            "Conservative QDK-aligned surface-code reliability, rotation, factory, "
            "floorplan, and decoder envelopes. Only the matched finite-shot Sim "
            "subset is application-level eligible; other rows are conditional "
            "architecture pressure and retain explicit unsupported flags."
        ),
        "input_csv": relative(args.input_csv),
        "record_csv": relative(args.output_csv),
        "main_records": len(rows),
        "structural_subtypes": len(subtype_records),
        "quality_qualified_records": len(full_records),
        "parameter_origins": {
            "qec_formula": {
                "source": "Microsoft QDK GenericQEC documentation",
                "url": "https://learn.microsoft.com/en-us/azure/quantum/qre-build-error-correction-models",
                "crossing_prefactor": QEC_CROSSING_PREFACTOR,
                "threshold": QEC_THRESHOLD,
                "physical_qubits_per_logical": "2*d^2",
            },
            "factory_throughput_and_floorplan": {
                "source": "LSQCA, HPCA 2025",
                "url": "https://arxiv.org/abs/2412.20486",
                "factory_logical_cells": FACTORY_LOGICAL_CELLS,
                "code_beats_per_magic_state": FACTORY_CODE_BEATS_PER_STATE,
                "conventional_memory_density": 0.5,
                "point_sam_model": "M data cells + one scan cell + six-cell CR",
            },
            "decoder_reaction": {
                "source": "Khalid et al., Impacts of Decoder Latency on Utility-Scale Quantum Computer Architectures",
                "url": "https://arxiv.org/abs/2511.10633",
                "communication_floor_sec": COMMUNICATION_FLOOR_SEC,
                "decoder_service_sweep_sec": list(DECODER_SERVICE_ENVELOPES_SEC),
            },
            "rotation_synthesis": {
                "source": "Ross--Selinger leading typical-case term",
                "url": "https://arxiv.org/abs/1403.2975",
                "formula": "ceil(3*log2(1/epsilon)); lower-order O(log log(1/epsilon)) omitted",
                "status": "leading-term estimate, not an exact emitted compiler trace",
            },
            "qdk_factory_protocol_table": {
                "source": "Microsoft QDK custom magic-state factory documentation reproducing Litinski19 entries",
                "url": "https://learn.microsoft.com/en-us/azure/quantum/qre-build-error-correction-models",
                "entries": list(QDK_LITINSKI_FACTORY_TABLE),
            },
        },
        "application_failure_budgets": list(APPLICATION_FAILURE_BUDGETS),
        "physical_error_rates": list(PHYSICAL_ERROR_RATES),
        "t_states_per_rotation_sweep": list(T_STATES_PER_ROTATION_SWEEP),
        "budget_contracts": {
            "strict_all_shots": "one-third union-bound budgets for logical, distillation, and synthesis faults over the full estimator",
            "estimator_tolerant": "matched Sim only; binomial corrupted-shot tail under measured p90 quality headroom",
        },
        "qdk_distance_crosscheck": qdk_crosscheck,
        "angle_distribution": angle_summary,
        "by_workload_default_strict": by_workload,
        "quality_qualified_strict_t_sweep": eligible_t_sweep,
        "factory_headline_disposition": disposition,
        "subtypes": subtype_records,
        "quality_qualified_case_contracts": full_records,
        "internal_errors": internal_errors,
    }
    json_dump(args.output_json, payload)
    print(json.dumps({
        "output_json": relative(args.output_json),
        "output_csv": relative(args.output_csv),
        "audit_status": payload["audit_status"],
        "p0_completion_status": payload["p0_completion_status"],
        "records": len(rows),
        "subtypes": len(subtype_records),
        "quality_qualified_records": len(full_records),
        "qdk_distance_crosscheck": qdk_crosscheck["status"],
        "factory_headline_disposition": disposition,
        "by_workload_default_strict": by_workload,
    }, indent=2, sort_keys=True))
    if internal_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
