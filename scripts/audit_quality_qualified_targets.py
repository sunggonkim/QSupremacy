#!/usr/bin/env python3
"""Audit quality eligibility before any application-level hardware target."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from strong_accept_common import (
    DEFAULT_INPUT,
    LADDER_FIELDS,
    ROOT,
    TOLERANCES,
    as_float,
    base_seed,
    independent_instance_id,
    json_dump,
    ladder_group_id,
    read_rows,
    record_id,
    relative,
    repeat_round,
    structural_config_id,
)


DEFAULT_OUTPUT = (
    ROOT / "data/processed/perlmutter/quality_qualified_target_map.json"
)


def load_json(path):
    path = ROOT / path
    if not path.exists():
        return None
    return json.loads(path.read_text())


def finite_shot_inventory(closure=None):
    inventory = []

    if closure:
        inventory.append({
            "workload": "all",
            "artifact": "data/processed/perlmutter/finite_shot_quality_sensitivity.json",
            "scope": closure["scope"],
            "shots": closure["shot_grid"],
            "quality_coupled": True,
            "same_record_as_main_corpus": "workload dependent; see record evidence_scope",
            "selected_source_records": closure["selected_source_records"],
        })

    qaoa = load_json("data/processed/perlmutter/qaoa_scale_depth_closure.json")
    if qaoa:
        shots = sorted({
            int(point["shots"])
            for case in qaoa.get("case_results", [])
            for record in case.get("records", [])
            for point in record.get("finite_shot_resampling", [])
        })
        inventory.append({
            "workload": "optimization",
            "artifact": "data/processed/perlmutter/qaoa_scale_depth_closure.json",
            "scope": "separate 10--20-qubit weighted-MaxCut depth ladder",
            "shots": shots,
            "quality_coupled": True,
            "same_record_as_main_corpus": False,
        })

    noisy = load_json("data/processed/perlmutter/qaoa_noisy_closed_loop.json")
    if noisy:
        inventory.append({
            "workload": "optimization",
            "artifact": "data/processed/perlmutter/qaoa_noisy_closed_loop.json",
            "scope": "separate 4/6/8-qubit synthetic depolarizing sweep",
            "shots": sorted({int(row["shots_per_evaluation"]) for row in noisy["records"]}),
            "quality_coupled": True,
            "same_record_as_main_corpus": False,
        })

    chem = load_json(
        "data/processed/perlmutter/chem_active_space_pair_ucc_closure.json"
    )
    if chem:
        inventory.append({
            "workload": "chemistry",
            "artifact": (
                "data/processed/perlmutter/"
                "chem_active_space_pair_ucc_closure.json"
            ),
            "scope": (
                "separate H8 active-space ladder; fixed shot allocation and "
                "state-independent error bound, not sampled energy quality"
            ),
            "shots": sorted({
                int(row["measurement"]["fixed_shots_allocated"])
                for row in chem.get("records", [])
            }),
            "quality_coupled": False,
            "same_record_as_main_corpus": False,
        })
    return inventory


def measurement_contract(workload):
    if workload == "ml":
        return (
            "unsupported_amplitude_feature_readout",
            "The controlled QFeature path uses Z expectations and real state "
            "amplitudes; the latter lack a physical measurement contract.",
        )
    if workload == "chemistry":
        return (
            "compiled_subset_only",
            "QWC schedules exist for controlled H2/chain attachments, not every "
            "record as a sampled quality trace.",
        )
    if workload == "optimization":
        return (
            "computational_basis_sampling_defined",
            "MaxCut quality can be sampled from computational-basis outcomes.",
        )
    if workload == "simulation":
        return (
            "z_observable_sampling_defined",
            "The reported Z0 observable has a direct Bernoulli measurement contract.",
        )
    return "unknown", "No measurement contract is defined."


def ladder_values(row):
    return tuple(row.get(field, "") for field in LADDER_FIELDS[row["workload"]])


def build_ladder_index(rows):
    index = defaultdict(set)
    for row in rows:
        key = (row["workload"], ladder_group_id(row), base_seed(row))
        index[key].add(ladder_values(row))
    return index


def summarize(records, multiplier):
    selected = [record for record in records if record["tolerance_multiplier"] == multiplier]
    by_workload = {}
    for workload in sorted({record["workload"] for record in selected}):
        subset = [record for record in selected if record["workload"] == workload]
        pass_count = sum(record["noiseless_quality_pass"] for record in subset)
        eligible = sum(record["hardware_target_eligible"] for record in subset)
        by_workload[workload] = {
            "records": len(subset),
            "structural_configurations": len({record["structural_config_id"] for record in subset}),
            "independent_instances": len({record["independent_instance_id"] for record in subset}),
            "noiseless_quality_pass_count": pass_count,
            "noiseless_quality_pass_fraction": pass_count / len(subset),
            "hardware_target_eligible_count": eligible,
            "hardware_target_eligible_fraction": eligible / len(subset),
            "quality_status_counts": dict(Counter(record["quality_status"] for record in subset)),
            "measurement_contract_counts": dict(Counter(record["measurement_contract"] for record in subset)),
        }
    return by_workload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--output-csv",
        default=str(DEFAULT_OUTPUT.with_suffix(".csv")),
    )
    parser.add_argument(
        "--finite-shot",
        default="data/processed/perlmutter/finite_shot_quality_sensitivity.json",
    )
    parser.add_argument("--eligibility-shots", type=int, default=10000)
    args = parser.parse_args()

    rows = read_rows(args.input_csv)
    finite_closure = load_json(args.finite_shot)
    finite_map = {}
    if finite_closure:
        finite_map = {
            record["source_record_id"]: record
            for record in finite_closure.get("records", [])
            if int(record["shots"]) == args.eligibility_shots
        }
    ladder_index = build_ladder_index(rows)
    records = []
    for row in rows:
        workload = row["workload"]
        gap = max(0.0, as_float(row, "quality_gap"))
        default_tolerance = TOLERANCES[workload]
        key = (workload, ladder_group_id(row), base_seed(row))
        ladder_points = len(ladder_index[key])
        contract, contract_note = measurement_contract(workload)
        finite = finite_map.get(record_id(row))
        for multiplier in (0.5, 1.0, 2.0):
            tolerance = default_tolerance * multiplier
            passes = gap <= tolerance
            if passes:
                status = "quality_pass"
            elif ladder_points >= 2:
                status = "quality_fail_with_measured_ladder"
            else:
                status = "quality_fail_without_recovery_evidence"

            finite_pass_probability = None
            quality_ci = ["", ""]
            if finite is None:
                finite_shot_status = "missing_same_record_quality_shot_trace"
                same_record = False
                full_loop = False
            else:
                finite_pass_probability = sum(
                    value <= tolerance
                    for value in finite["replicate_quality_gap"]
                ) / len(finite["replicate_quality_gap"])
                quality_ci = finite["sampled_quality_ci_95"]
                same_record = bool(finite["same_record_quality_shot_trace"])
                full_loop = bool(finite["full_algorithm_loop_covered"])
                if not same_record:
                    finite_shot_status = "physically_measurable_variant_not_same_record"
                elif not full_loop:
                    finite_shot_status = "same_record_fixed_parameter_output_only"
                else:
                    finite_shot_status = "same_record_full_loop_quality_trace"

            eligible = bool(
                passes
                and same_record
                and full_loop
                and finite_pass_probability is not None
                and finite_pass_probability >= 0.9
                and not contract.startswith("unsupported")
            )
            if not passes:
                exclusion = "noiseless_application_quality_gate_failed"
            elif finite is not None and not same_record:
                exclusion = "finite_shot_variant_is_not_the_same_circuit_path"
            elif finite is not None and not full_loop:
                exclusion = "finite_shot_outer_loop_not_covered"
            elif finite_pass_probability is not None and finite_pass_probability < 0.9:
                exclusion = "finite_shot_quality_pass_probability_below_0p9"
            elif contract.startswith("unsupported"):
                exclusion = "physical_measurement_contract_missing"
            elif contract == "compiled_subset_only":
                exclusion = "finite_shot_quality_and_full_compiled_coverage_missing"
            else:
                exclusion = "finite_shot_quality_trace_missing"

            records.append({
                "record_id": record_id(row),
                "workload": workload,
                "family": row.get("family", ""),
                "structural_config_id": structural_config_id(row),
                "ladder_group_id": ladder_group_id(row),
                "independent_instance_id": independent_instance_id(row),
                "seed": int(float(row["seed"])),
                "base_seed": base_seed(row),
                "repeat_round": repeat_round(row),
                "quality_metric": row.get("quality_metric", ""),
                "native_quality": as_float(row, "native_quality"),
                "quantum_quality": as_float(row, "quantum_quality"),
                "quality_gap": gap,
                "default_tolerance": default_tolerance,
                "tolerance_multiplier": multiplier,
                "tolerance": tolerance,
                "noiseless_quality_pass": passes,
                "quality_status": status,
                "measured_ladder_points": ladder_points,
                "measured_ladder_fields": ",".join(LADDER_FIELDS[workload]),
                "finite_shot_status": finite_shot_status,
                "finite_shot_pass_probability": (
                    "" if finite_pass_probability is None else finite_pass_probability
                ),
                "quality_ci_low": quality_ci[0],
                "quality_ci_high": quality_ci[1],
                "measurement_contract": contract,
                "measurement_contract_note": contract_note,
                "hardware_target_eligible": eligible,
                "exclusion_reason": exclusion,
            })

    default_records = [record for record in records if record["tolerance_multiplier"] == 1.0]
    internal_errors = []
    if len(rows) != 3552:
        internal_errors.append("expected 3552 main-corpus records, found {}".format(len(rows)))
    if len({record["record_id"] for record in default_records}) != len(rows):
        internal_errors.append("record IDs are not unique")
    if any(record["hardware_target_eligible"] and not record["noiseless_quality_pass"] for record in records):
        internal_errors.append("quality-failing record marked hardware-target eligible")

    inventory = finite_shot_inventory(finite_closure)
    closure_complete = bool(
        finite_closure
        and finite_closure.get("audit_status") == "PASS"
        and set(finite_closure.get("shot_grid", [])) == {1000, 10000, 100000}
        and set(finite_closure.get("selected_by_workload", {})) == set(TOLERANCES)
    )
    gaps = {
        workload: {
            "same_record_finite_shot_quality": any(
                record["workload"] == workload
                and record["finite_shot_status"].startswith("same_record")
                for record in default_records
            ),
            "required_shot_points": [1000, 10000, 100000],
            "measurement_contract": measurement_contract(workload)[0],
            "action": (
                "build a physically measurable feature path and sample it"
                if workload == "ml"
                else "generate representative matched finite-shot quality traces"
            ),
        }
        for workload in TOLERANCES
    }
    payload = {
        "schema": "qarchgauge.quality-qualified-target-map.v1",
        "input_csv": relative(args.input_csv),
        "audit_status": "FAIL" if internal_errors else "PASS",
        "p0_completion_status": (
            "PASS_WITH_RESTRICTED_ELIGIBLE_SUBSET"
            if closure_complete and not internal_errors
            else "BLOCKED_MEASUREMENT_GAPS"
        ),
        "scope": (
            "Stage-1 quality eligibility audit. Noiseless quality pass is not "
            "sufficient for an application-level hardware target; same-record "
            "finite-shot quality and a physical measurement contract are required."
        ),
        "records": len(rows),
        "structural_configurations": len({structural_config_id(row) for row in rows}),
        "independent_instances": len({independent_instance_id(row) for row in rows}),
        "tolerances": TOLERANCES,
        "by_tolerance_multiplier": {
            str(multiplier): summarize(records, multiplier)
            for multiplier in (0.5, 1.0, 2.0)
        },
        "finite_shot_evidence_inventory": inventory,
        "eligibility_shots": args.eligibility_shots,
        "measurement_gaps": gaps,
        "internal_errors": internal_errors,
        "record_csv": relative(args.output_csv),
    }

    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    json_dump(args.output_json, payload)

    print(json.dumps({
        "output_json": relative(args.output_json),
        "output_csv": relative(args.output_csv),
        "audit_status": payload["audit_status"],
        "p0_completion_status": payload["p0_completion_status"],
        "default_quality_pass": {
            workload: summary["noiseless_quality_pass_count"]
            for workload, summary in payload["by_tolerance_multiplier"]["1.0"].items()
        },
        "hardware_target_eligible": {
            workload: summary["hardware_target_eligible_count"]
            for workload, summary in payload["by_tolerance_multiplier"]["1.0"].items()
        },
    }, indent=2, sort_keys=True))
    if internal_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
