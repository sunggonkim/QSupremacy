#!/usr/bin/env python3
"""Hierarchical bootstrap audit for QArchGauge headline statistics."""

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from strong_accept_common import (
    DEFAULT_INPUT,
    ROOT,
    TOLERANCES,
    as_float,
    base_seed,
    independent_instance_id,
    json_dump,
    median,
    percentile_interval,
    read_rows,
    record_id,
    relative,
    repeat_round,
    structural_config_id,
)


DEFAULT_OUTPUT = ROOT / "data/processed/perlmutter/statistical_robustness.json"
LEVERS = ("factory", "shot_fabric", "logical_cycle", "decoder", "host_feedback")
MODES = ("group_wave_ready", "serial_evaluation")


def read_projection(path):
    joined = defaultdict(dict)
    with Path(path).open(newline="") as handle:
        for row in csv.DictReader(handle):
            joined[row["record_id"]][row["mode"]] = {
                "ratio": float(row["conditional_projected_native_ratio"]),
                "utility": {
                    lever: float(row["{}_utility".format(lever)])
                    for lever in LEVERS
                },
            }
    return joined


def enrich(rows, projection):
    result = []
    for row in rows:
        item = dict(row)
        item["record_id"] = record_id(row)
        item["config_id"] = structural_config_id(row)
        item["instance_id"] = independent_instance_id(row)
        item["quality_pass"] = (
            max(0.0, as_float(row, "quality_gap")) <= TOLERANCES[row["workload"]]
        )
        item["projection"] = projection[item["record_id"]]
        result.append(item)
    return result


def grouped(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["config_id"]].append(row)
    return groups


def resample(groups, rng):
    keys = list(groups)
    sampled = []
    for key in (rng.choice(keys) for _ in keys):
        values = groups[key]
        sampled.extend(rng.choice(values) for _ in values)
    return sampled


def target_summary(rows, mode):
    utility = {
        lever: median(row["projection"][mode]["utility"][lever] for row in rows)
        for lever in LEVERS
    }
    target = max(utility, key=utility.get)
    return target, utility[target], utility


def metrics(rows):
    output = {
        "quality_pass_fraction": sum(row["quality_pass"] for row in rows) / len(rows),
        "median_measured_simulator_speedup_required": median(
            as_float(row, "speedup_required") for row in rows
        ),
    }
    for mode in MODES:
        target, gain, utility = target_summary(rows, mode)
        output[mode] = {
            "median_conditional_projected_native_ratio": median(
                row["projection"][mode]["ratio"] for row in rows
            ),
            "conditional_first_target": target,
            "conditional_first_target_gain": gain,
            "median_marginal_utility": utility,
        }
    return output


def bootstrap_family(rows, samples, seed):
    groups = grouped(rows)
    observed = metrics(rows)
    rng = random.Random(seed)
    replicates = [metrics(resample(groups, rng)) for _ in range(samples)]
    output = {
        "records": len(rows),
        "structural_configurations": len(groups),
        "independent_instance_seed_pairs": len({row["instance_id"] for row in rows}),
        "seeds_per_configuration": sorted({len(values) for values in groups.values()}),
        "observed": observed,
        "confidence_intervals_95": {
            "quality_pass_fraction": percentile_interval(
                item["quality_pass_fraction"] for item in replicates
            ),
            "median_measured_simulator_speedup_required": percentile_interval(
                item["median_measured_simulator_speedup_required"]
                for item in replicates
            ),
        },
        "conditional_target_bootstrap": {},
    }
    for mode in MODES:
        selected = Counter(item[mode]["conditional_first_target"] for item in replicates)
        output["conditional_target_bootstrap"][mode] = {
            "observed_target": observed[mode]["conditional_first_target"],
            "selection_probability": {
                lever: selected[lever] / samples for lever in LEVERS
            },
            "target_gain_ci_95": percentile_interval(
                item[mode]["conditional_first_target_gain"] for item in replicates
            ),
            "projected_native_ratio_ci_95": percentile_interval(
                item[mode]["median_conditional_projected_native_ratio"]
                for item in replicates
            ),
            "scope": "conditional execution target; not quality-qualified",
        }
    return output, replicates


def timing_repeat_inventory(path):
    path = Path(path)
    if not path.exists():
        return {"available": False, "path": relative(path)}
    data = json.loads(path.read_text())
    return {
        "available": True,
        "path": relative(path),
        "warmup_trials": data.get("warmup_cases"),
        "measured_trials": data.get("measured_cases"),
        "trials_per_workload": {
            workload: item.get("measured_trials")
            for workload, item in data.get("by_family", {}).items()
        },
        "max_quantum_runtime_cv": data.get("max_quantum_runtime_cv"),
        "passed_original_gate": data.get("passed"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT))
    parser.add_argument(
        "--projection-csv",
        default=(
            "data/processed/perlmutter/"
            "dependency_schedule_projection_records.csv"
        ),
    )
    parser.add_argument(
        "--repeat-timing",
        default="data/processed/perlmutter/repeat_timing_gate_latest.json",
    )
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=202707)
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT.with_suffix(".csv")))
    args = parser.parse_args()

    raw_rows = read_rows(args.input_csv)
    projection = read_projection(ROOT / args.projection_csv)
    rows = enrich(raw_rows, projection)
    workloads = sorted({row["workload"] for row in rows})

    internal_errors = []
    if len(rows) != 3552:
        internal_errors.append("expected 3552 records")
    if len({row["instance_id"] for row in rows}) != len(rows):
        internal_errors.append("duplicate structural-config/seed instance")
    if any(len(group) != 16 for group in grouped(rows).values()):
        internal_errors.append("not every structural configuration has 16 seeds")
    if any(set(row["projection"]) != {"aggregate_ready", *MODES} for row in rows):
        internal_errors.append("projection schedule coverage is incomplete")

    by_workload = {}
    replicate_sets = {}
    for index, workload in enumerate(workloads):
        subset = [row for row in rows if row["workload"] == workload]
        summary, replicates = bootstrap_family(
            subset,
            args.bootstrap_samples,
            args.seed + 1009 * index,
        )
        by_workload[workload] = summary
        replicate_sets[workload] = replicates

    balanced_quality = []
    balanced_speedup = []
    for index in range(args.bootstrap_samples):
        quality = [
            replicate_sets[workload][index]["quality_pass_fraction"]
            for workload in workloads
        ]
        speedups = [
            replicate_sets[workload][index][
                "median_measured_simulator_speedup_required"
            ]
            for workload in workloads
        ]
        balanced_quality.append(sum(quality) / len(quality))
        balanced_speedup.append(math.exp(sum(math.log(value) for value in speedups) / len(speedups)))

    observed_quality = [
        by_workload[workload]["observed"]["quality_pass_fraction"]
        for workload in workloads
    ]
    observed_speedup = [
        by_workload[workload]["observed"][
            "median_measured_simulator_speedup_required"
        ]
        for workload in workloads
    ]
    balanced = {
        "definition": (
            "Macro-average across four workload families; no family is weighted "
            "by its raw record count."
        ),
        "observed_macro_quality_pass_fraction": sum(observed_quality) / len(observed_quality),
        "macro_quality_pass_fraction_ci_95": percentile_interval(balanced_quality),
        "observed_geomean_family_median_simulator_speedup_required": math.exp(
            sum(math.log(value) for value in observed_speedup) / len(observed_speedup)
        ),
        "geomean_family_median_simulator_speedup_required_ci_95": percentile_interval(
            balanced_speedup
        ),
    }

    timing = timing_repeat_inventory(ROOT / args.repeat_timing)
    payload = {
        "schema": "qarchgauge.statistical-robustness.v1",
        "input_csv": relative(args.input_csv),
        "projection_csv": relative(ROOT / args.projection_csv),
        "audit_status": "FAIL" if internal_errors else "PASS",
        "p0_completion_status": "PASS" if not internal_errors else "BLOCKED",
        "resampling_contract": {
            "method": "hierarchical nonparametric bootstrap",
            "outer_unit": "structural workload configuration",
            "inner_unit": "distinct seed within selected configuration",
            "bootstrap_samples": args.bootstrap_samples,
            "random_seed": args.seed,
            "confidence_level": 0.95,
            "same-instance_repeat_trials_in_main_corpus": 0,
            "note": (
                "Filename rounds use shifted random seeds and are independent "
                "instance-seed records, not repeated timing trials."
            ),
        },
        "corpus": {
            "records": len(rows),
            "structural_configurations": len({row["config_id"] for row in rows}),
            "independent_instance_seed_pairs": len({row["instance_id"] for row in rows}),
            "seed_values": len({int(float(row["seed"])) for row in rows}),
            "base_seed_values": sorted({base_seed(row) for row in raw_rows}),
            "round_values": sorted({repeat_round(row) for row in raw_rows}),
            "by_workload": dict(Counter(row["workload"] for row in rows)),
        },
        "by_workload": by_workload,
        "workload_balanced": balanced,
        "timing_repeat_inventory": timing,
        "internal_errors": internal_errors,
    }
    json_dump(args.output_json, payload)

    compact_rows = []
    for workload in workloads:
        item = by_workload[workload]
        compact_rows.append({
            "workload": workload,
            "records": item["records"],
            "structural_configurations": item["structural_configurations"],
            "independent_instance_seed_pairs": item["independent_instance_seed_pairs"],
            "quality_pass_fraction": item["observed"]["quality_pass_fraction"],
            "quality_pass_ci_low": item["confidence_intervals_95"]["quality_pass_fraction"][0],
            "quality_pass_ci_high": item["confidence_intervals_95"]["quality_pass_fraction"][1],
            "median_simulator_speedup_required": item["observed"]["median_measured_simulator_speedup_required"],
            "speedup_ci_low": item["confidence_intervals_95"]["median_measured_simulator_speedup_required"][0],
            "speedup_ci_high": item["confidence_intervals_95"]["median_measured_simulator_speedup_required"][1],
            "group_wave_conditional_target": item["observed"]["group_wave_ready"]["conditional_first_target"],
            "group_wave_target_bootstrap_probability": item["conditional_target_bootstrap"]["group_wave_ready"]["selection_probability"][item["observed"]["group_wave_ready"]["conditional_first_target"]],
        })
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(compact_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(compact_rows)

    print(json.dumps({
        "output_json": relative(args.output_json),
        "output_csv": relative(args.output_csv),
        "audit_status": payload["audit_status"],
        "p0_completion_status": payload["p0_completion_status"],
        "corpus": payload["corpus"],
        "quality_pass_ci": {
            workload: item["confidence_intervals_95"]["quality_pass_fraction"]
            for workload, item in by_workload.items()
        },
    }, indent=2, sort_keys=True))
    if internal_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
