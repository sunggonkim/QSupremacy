#!/usr/bin/env python3
"""Audit workload-valid concurrency bounds and target stability."""

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from hpca_projection_model import projected_components_sec
from strong_accept_common import (
    DEFAULT_INPUT,
    ROOT,
    as_float,
    as_int,
    json_dump,
    median,
    read_rows,
    record_id,
    relative,
)


DEFAULT_OUTPUT = ROOT / "data/processed/perlmutter/dependency_schedule_coverage.json"
MODES = ("aggregate_ready", "group_wave_ready", "serial_evaluation")
LEVERS = ("factory", "shot_fabric", "logical_cycle", "decoder", "host_feedback")


def logical_qubits(row):
    workload = row["workload"]
    if workload == "ml":
        return max(1, as_int(row, "ml_features", 1))
    if workload == "chemistry":
        fixture = Path(row.get("chem_hamiltonian_json", "")).name
        return 4 if fixture == "molecular_chain_4q.json" else 2
    if workload == "optimization":
        return max(1, as_int(row, "opt_nodes", 1))
    return max(1, as_int(row, "sim_qubits", 1))


def chem_key(row):
    fixture = Path(row.get("chem_hamiltonian_json", "")).name
    name = "molecular_chain_4q_surrogate" if fixture else "H2_minimal_2qubit"
    return name, as_int(row, "chem_layers", 1)


def load_chem_schedules(path):
    artifact = json.loads(Path(path).read_text())
    schedules = {}
    for record in artifact["records"]:
        if record.get("evidence_level") != "compiled_executed_ansatz":
            continue
        topology = next(
            item for item in record["topologies"]
            if item["topology"] == "all_to_all"
        )
        schedules[(record["fixture"], int(record["layers"]))] = {
            "groups": int(record["measurement_groups_per_eval"]),
            "shots_by_group": [int(value) for value in record["shots_by_group"]],
            "shot_executions_per_eval": int(record["shot_executions_per_eval"]),
            "critical_path_depth_lower": int(topology["max_group_depth"]),
            "critical_path_depth_upper": int(sum(group["depth"] for group in topology["groups"])),
            "oneq_per_shot_weighted": float(
                topology["per_evaluation_shot_weighted"]["one_qubit_gates"]
            ) / float(record["shot_executions_per_eval"]),
            "twoq_per_shot_weighted": float(
                topology["per_evaluation_shot_weighted"]["two_qubit_gates"]
            ) / float(record["shot_executions_per_eval"]),
            "meas_per_shot_weighted": float(
                topology["per_evaluation_shot_weighted"]["measurement_ops"]
            ) / float(record["shot_executions_per_eval"]),
            "arbitrary_rotations_per_group": float(record["arbitrary_rotations_per_group"]),
            "source": relative(path),
        }
    return schedules


def count_depth_bracket(row):
    evals = max(1, as_int(row, "circuit_evaluations", 1))
    qubits = logical_qubits(row)
    oneq = as_float(row, "one_qubit_gates") / evals
    twoq = as_float(row, "two_qubit_gates") / evals
    meas = as_float(row, "measurement_ops") / evals
    lower = max(
        1.0,
        oneq / qubits,
        twoq / max(1, qubits // 2),
        meas / qubits,
    )
    upper = max(1.0, oneq + twoq + meas)
    return int(math.ceil(lower)), int(math.ceil(upper))


def semantics(row, chem_schedules):
    workload = row["workload"]
    evals = max(1, as_int(row, "circuit_evaluations", 1))
    lower, upper = count_depth_bracket(row)
    schedule = {
        "evaluation_count": evals,
        "independent_circuit_evaluations": evals,
        "measurement_groups_per_eval": 1,
        "shots_by_group": [10000],
        "shot_executions_per_eval": 10000,
        "critical_path_depth_lower": lower,
        "critical_path_depth_upper": upper,
        "host_visible_barriers_per_eval": 1,
        "mid_circuit_feedback_events": 0,
        "compiled_dependency_wave": False,
        "physical_measurement_supported": True,
    }
    if workload == "ml":
        schedule.update({
            "loop_type": "static_feature_circuit_batch",
            "provenance": "source_audited_static_loop",
            "source": "benchmarks/workloads/run_practical_suite.py:quantum_ml_features",
            "adaptive_feedback": False,
            "physical_measurement_supported": False,
            "limitation": (
                "All sample circuits are independent, but real-amplitude feature "
                "extraction is not a directly measured observable."
            ),
        })
    elif workload == "chemistry":
        compiled = chem_schedules.get(chem_key(row))
        schedule.update({
            "loop_type": "static_parameter_candidate_sweep",
            "provenance": "source_audited_static_loop",
            "source": "benchmarks/workloads/run_practical_suite.py:run_chemistry",
            "adaptive_feedback": False,
            "limitation": (
                "The implemented candidate list is generated before execution; "
                "this is not an adaptive VQE optimizer trace."
            ),
        })
        if compiled:
            schedule.update({
                "measurement_groups_per_eval": compiled["groups"],
                "shots_by_group": compiled["shots_by_group"],
                "shot_executions_per_eval": compiled["shot_executions_per_eval"],
                "critical_path_depth_lower": compiled["critical_path_depth_lower"],
                "critical_path_depth_upper": compiled["critical_path_depth_upper"],
                "compiled_dependency_wave": True,
                "compiled_source": compiled["source"],
                "compiled_gate_override": compiled,
            })
    elif workload == "optimization":
        schedule.update({
            "loop_type": "static_parameter_grid",
            "provenance": "source_audited_static_loop",
            "source": "benchmarks/workloads/run_practical_suite.py:run_optimization",
            "adaptive_feedback": False,
            "limitation": (
                "The beta/gamma grid is independent and predeclared; this is not "
                "an adaptive QAOA optimizer trace."
            ),
        })
    elif workload == "simulation":
        schedule.update({
            "loop_type": "single_unitary_evolution",
            "provenance": "source_audited_single_circuit",
            "source": "benchmarks/workloads/run_practical_suite.py:run_simulation",
            "adaptive_feedback": False,
            "limitation": "One Trotter circuit and one terminal Z observable.",
        })
    else:
        raise ValueError("unsupported workload {}".format(workload))

    max_group_shots = max(schedule["shots_by_group"])
    total = schedule["shot_executions_per_eval"] * evals
    schedule["ready_shot_executions"] = {
        "aggregate_ready": total,
        "group_wave_ready": max_group_shots * evals,
        "serial_evaluation": max_group_shots,
    }
    schedule["critical_path_evaluation_waves"] = {
        "aggregate_ready": 1,
        "group_wave_ready": schedule["measurement_groups_per_eval"],
        "serial_evaluation": evals * schedule["measurement_groups_per_eval"],
    }
    return schedule


def projection_row(row, schedule, mode):
    attached = dict(row)
    attached["measurement_groups_per_eval"] = schedule["measurement_groups_per_eval"]
    attached["shot_executions_per_eval"] = schedule["shot_executions_per_eval"]
    attached["ready_shot_executions"] = schedule["ready_shot_executions"][mode]
    compiled = schedule.get("compiled_gate_override")
    if compiled:
        evals = schedule["evaluation_count"]
        attached["one_qubit_gates"] = evals * compiled["oneq_per_shot_weighted"]
        attached["two_qubit_gates"] = evals * compiled["twoq_per_shot_weighted"]
        attached["measurement_ops"] = evals * compiled["meas_per_shot_weighted"]
        rotations = evals * compiled["arbitrary_rotations_per_group"]
    else:
        rotations = as_float(row, "one_qubit_gates")
        if row["workload"] in ("optimization", "simulation"):
            rotations += as_float(row, "two_qubit_gates")
    attached["magic_state_demand"] = 16.0 * rotations
    return attached


def config_for(lever=None):
    distance = 15.0
    cycle = 0.4e-6
    config = {
        "distance": distance,
        "cycle_sec": cycle,
        "shots_per_group": 10000.0,
        "shot_lanes": 10000.0,
        "decoder_sec_per_eval": 5.0e-6,
        "decoder_bandwidth_bits_per_sec": 4.0e12,
        "magic_state_factory_rate_per_sec": 64.0 / (15.0 * distance * cycle),
        "host_io_floor_sec_per_eval": 5.0e-6,
        "host_link_bandwidth_bytes_per_sec": 64.0e9,
        "enable_queue_model": False,
        "enable_controller_scaling": False,
        "enable_host_context": False,
        "critical_path_serialization_fraction": 1.0,
    }
    if lever == "factory":
        config["magic_state_factory_rate_per_sec"] *= 10.0
    elif lever == "shot_fabric":
        config["shot_lanes"] *= 10.0
    elif lever == "logical_cycle":
        config["cycle_sec"] /= 10.0
    elif lever == "decoder":
        config["decoder_sec_per_eval"] /= 10.0
        config["decoder_bandwidth_bits_per_sec"] *= 10.0
    elif lever == "host_feedback":
        config["host_io_floor_sec_per_eval"] /= 10.0
        config["host_link_bandwidth_bytes_per_sec"] *= 10.0
    return config


def evaluate_modes(rows, schedules):
    per_record = []
    summaries = {}
    for mode in MODES:
        mode_records = []
        for row, schedule in zip(rows, schedules):
            attached = projection_row(row, schedule, mode)
            baseline = projected_components_sec(attached, config_for())
            utility = {}
            for lever in LEVERS:
                improved = projected_components_sec(attached, config_for(lever))
                utility[lever] = baseline["total_sec"] / max(improved["total_sec"], 1.0e-30)
            target = max(utility, key=utility.get)
            mode_records.append({
                "record_id": record_id(row),
                "workload": row["workload"],
                "mode": mode,
                "conditional_projected_native_ratio": baseline["total_sec"] / max(as_float(row, "native_runtime_sec"), 1.0e-30),
                "conditional_first_target": target,
                "conditional_first_target_gain": utility[target],
                "marginal_utility": utility,
                "shot_lane_evidence": baseline["shot_lane_evidence"],
                "effective_shot_lanes": baseline["effective_shot_lanes"],
            })
        per_record.extend(mode_records)
        summaries[mode] = {}
        for workload in sorted({row["workload"] for row in rows}):
            subset = [item for item in mode_records if item["workload"] == workload]
            median_utility = {
                lever: median(item["marginal_utility"][lever] for item in subset)
                for lever in LEVERS
            }
            target = max(median_utility, key=median_utility.get)
            summaries[mode][workload] = {
                "records": len(subset),
                "median_conditional_projected_native_ratio": median(
                    item["conditional_projected_native_ratio"] for item in subset
                ),
                "median_marginal_utility": median_utility,
                "conditional_first_target": target,
                "conditional_first_target_gain": median_utility[target],
                "record_target_counts": dict(Counter(item["conditional_first_target"] for item in subset)),
            }
    return per_record, summaries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT))
    parser.add_argument(
        "--chem-compiled",
        default=(
            "data/processed/perlmutter/"
            "chem_controlled_compiled_measurement_records.json"
        ),
    )
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT.with_suffix(".csv")))
    parser.add_argument(
        "--output-projection-csv",
        default=str(DEFAULT_OUTPUT.with_name("dependency_schedule_projection_records.csv")),
    )
    args = parser.parse_args()

    rows = read_rows(args.input_csv)
    chem_schedules = load_chem_schedules(ROOT / args.chem_compiled)
    schedules = [semantics(row, chem_schedules) for row in rows]
    projection_records, projection_summary = evaluate_modes(rows, schedules)

    target_stability = {}
    for workload in sorted({row["workload"] for row in rows}):
        targets = {
            mode: projection_summary[mode][workload]["conditional_first_target"]
            for mode in MODES
        }
        target_stability[workload] = {
            "by_mode": targets,
            "stable": len(set(targets.values())) == 1,
            "scope": "conditional execution only; quality eligibility is audited separately",
        }

    coverage = {
        "records": len(rows),
        "compiled_dependency_wave": sum(item["compiled_dependency_wave"] for item in schedules),
        "source_audited_static_loop": sum(item["provenance"] == "source_audited_static_loop" for item in schedules),
        "source_audited_single_circuit": sum(item["provenance"] == "source_audited_single_circuit" for item in schedules),
        "aggregate_total_demand_fallback": 0,
        "adaptive_optimizer_trace": sum(item["adaptive_feedback"] for item in schedules),
    }
    internal_errors = []
    if len(rows) != 3552:
        internal_errors.append("expected 3552 records")
    if coverage["aggregate_total_demand_fallback"]:
        internal_errors.append("unclassified aggregate fallback remains")
    if not all(item["mid_circuit_feedback_events"] == 0 for item in schedules):
        internal_errors.append("unexpected mid-circuit feedback event")

    schedule_rows = []
    for row, schedule in zip(rows, schedules):
        schedule_rows.append({
            "record_id": record_id(row),
            "workload": row["workload"],
            "loop_type": schedule["loop_type"],
            "provenance": schedule["provenance"],
            "evaluation_count": schedule["evaluation_count"],
            "independent_circuit_evaluations": schedule["independent_circuit_evaluations"],
            "measurement_groups_per_eval": schedule["measurement_groups_per_eval"],
            "shot_executions_per_eval": schedule["shot_executions_per_eval"],
            "aggregate_ready": schedule["ready_shot_executions"]["aggregate_ready"],
            "group_wave_ready": schedule["ready_shot_executions"]["group_wave_ready"],
            "serial_evaluation_ready": schedule["ready_shot_executions"]["serial_evaluation"],
            "critical_path_depth_lower": schedule["critical_path_depth_lower"],
            "critical_path_depth_upper": schedule["critical_path_depth_upper"],
            "compiled_dependency_wave": schedule["compiled_dependency_wave"],
            "adaptive_feedback": schedule["adaptive_feedback"],
            "mid_circuit_feedback_events": schedule["mid_circuit_feedback_events"],
            "physical_measurement_supported": schedule["physical_measurement_supported"],
            "source": schedule["source"],
            "limitation": schedule["limitation"],
        })

    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(schedule_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(schedule_rows)

    projection_csv = Path(args.output_projection_csv)
    projection_csv.parent.mkdir(parents=True, exist_ok=True)
    projection_rows = []
    for record in projection_records:
        projection_rows.append({
            "record_id": record["record_id"],
            "workload": record["workload"],
            "mode": record["mode"],
            "conditional_projected_native_ratio": record[
                "conditional_projected_native_ratio"
            ],
            "conditional_first_target": record["conditional_first_target"],
            "conditional_first_target_gain": record[
                "conditional_first_target_gain"
            ],
            **{
                "{}_utility".format(lever): record["marginal_utility"][lever]
                for lever in LEVERS
            },
            "shot_lane_evidence": record["shot_lane_evidence"],
            "effective_shot_lanes": record["effective_shot_lanes"],
        })
    with projection_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(projection_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(projection_rows)

    payload = {
        "schema": "qarchgauge.dependency-schedule-coverage.v1",
        "input_csv": relative(args.input_csv),
        "audit_status": "FAIL" if internal_errors else "PASS",
        "p0_completion_status": (
            "PASS_FOR_IMPLEMENTED_STATIC_LOOPS"
            if not internal_errors and all(item["stable"] for item in target_stability.values())
            else "BLOCKED"
        ),
        "scope": (
            "Source-audited schedules for the implemented fixed feature, static "
            "candidate/grid, and single-circuit loops. They do not represent an "
            "adaptive VQE/QAOA/QNN optimizer or mid-circuit feedback trace."
        ),
        "schedule_modes": {
            "aggregate_ready": "all predeclared evaluations and groups may issue",
            "group_wave_ready": "one measurement-group wave across independent evaluations",
            "serial_evaluation": "one evaluation and one group wave at a time",
        },
        "coverage": coverage,
        "by_loop_type": dict(Counter(item["loop_type"] for item in schedules)),
        "conditional_projection_by_mode": projection_summary,
        "conditional_target_stability": target_stability,
        "adaptive_claim_gate": {
            "supported": False,
            "reason": (
                "The measured workload loops are static and contain no adaptive "
                "optimizer or mid-circuit branch trace."
            ),
            "allowed_claim": (
                "Target stability across conservative schedules for the implemented "
                "static loops only."
            ),
        },
        "record_csv": relative(args.output_csv),
        "projection_record_csv": relative(args.output_projection_csv),
        "projection_record_count": len(projection_records),
        "internal_errors": internal_errors,
    }
    json_dump(args.output_json, payload)
    print(json.dumps({
        "output_json": relative(args.output_json),
        "output_csv": relative(args.output_csv),
        "output_projection_csv": relative(args.output_projection_csv),
        "audit_status": payload["audit_status"],
        "p0_completion_status": payload["p0_completion_status"],
        "coverage": coverage,
        "targets": {
            workload: item["by_mode"]
            for workload, item in target_stability.items()
        },
    }, indent=2, sort_keys=True))
    if internal_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
