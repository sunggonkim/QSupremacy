#!/usr/bin/env python3
"""Summarize no-srun future-hardware projection scenarios.

This script uses existing practical-suite CSV metadata. It does not consume GPU
allocation time; it only changes projection knobs such as effective shot lanes,
serial decoder/control floor, and logical-operation scale.
"""

import argparse
import csv
import json
import os
from statistics import median


DEFAULT_TOLERANCES = {
    "ml": 0.02,
    "chemistry": 0.01,
    "optimization": 0.02,
    "simulation": 0.01,
}

SCENARIOS = [
    {
        "id": "conservative_surface",
        "label": "Conservative surface",
        "distance": 31.0,
        "cycle_sec": 1.0e-6,
        "shot_lanes": 1.0e2,
        "decoder_sec_per_eval": 63.0e-6,
        "control_queue_sec_per_eval": 100.0e-6,
        "description": "Small useful shot parallelism and larger real-time decode/control floor.",
    },
    {
        "id": "resource_estimator_like",
        "label": "Resource-estimator-like",
        "distance": 25.0,
        "cycle_sec": 1.0e-6,
        "shot_lanes": 1.0e3,
        "decoder_sec_per_eval": 20.0e-6,
        "control_queue_sec_per_eval": 80.0e-6,
        "description": "Moderate alternate FT resource-estimator point with constrained shot lanes.",
    },
    {
        "id": "default_optimistic",
        "label": "Default optimistic",
        "distance": 25.0,
        "cycle_sec": 1.0e-6,
        "shot_lanes": 1.0e4,
        "decoder_sec_per_eval": 5.0e-6,
        "control_queue_sec_per_eval": 50.0e-6,
        "description": "Paper default lower-bound stack.",
    },
    {
        "id": "ldpc_future_like",
        "label": "LDPC/future-like",
        "distance": 15.0,
        "cycle_sec": 1.0e-6,
        "shot_lanes": 1.0e5,
        "decoder_sec_per_eval": 5.0e-6,
        "control_queue_sec_per_eval": 10.0e-6,
        "description": "Future lower-overhead code/control point with larger useful batching.",
    },
    {
        "id": "aggressive_batched",
        "label": "Aggressive batched",
        "distance": 15.0,
        "cycle_sec": 0.5e-6,
        "shot_lanes": 1.0e6,
        "decoder_sec_per_eval": 1.0e-6,
        "control_queue_sec_per_eval": 1.0e-6,
        "description": "Aggressive high-batching point for upper-bound sensitivity.",
    },
]


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def as_float(row, key, default=0.0):
    value = row.get(key, "")
    if value in ("", None):
        return default
    return float(value)


def projected_time(row, scenario):
    distance = scenario["distance"]
    cycle_sec = scenario["cycle_sec"]
    evals = max(1.0, as_float(row, "circuit_evaluations", 1.0))
    oneq = as_float(row, "one_qubit_gates")
    twoq = as_float(row, "two_qubit_gates")
    meas = as_float(row, "measurement_ops")
    shot_lanes = max(1.0, scenario["shot_lanes"])

    logical_per_eval = (
        oneq * distance * cycle_sec
        + twoq * 4.0 * distance * cycle_sec
        + meas * distance * cycle_sec
    )
    parallel_time = evals * logical_per_eval / shot_lanes
    serial_time = evals * (
        scenario["decoder_sec_per_eval"] + scenario["control_queue_sec_per_eval"]
    )
    return parallel_time + serial_time


def summarize(rows, recovery):
    workloads = sorted(set(row.get("workload", "unknown") for row in rows))
    result = {
        "cases": len(rows),
        "quality_recovery": recovery,
        "tolerances": DEFAULT_TOLERANCES,
        "scenarios": SCENARIOS,
        "by_scenario": {},
    }
    for scenario in SCENARIOS:
        scenario_item = {"by_workload": {}}
        all_advantaged = []
        all_ratios = []
        for workload in workloads:
            subset = [row for row in rows if row.get("workload") == workload]
            tolerance = DEFAULT_TOLERANCES.get(workload, 0.02)
            ratios = []
            advantaged = []
            runtime_pass = []
            quality_pass = []
            for row in subset:
                native = max(as_float(row, "native_runtime_sec"), 1.0e-12)
                gap = max(0.0, as_float(row, "quality_gap"))
                projected = projected_time(row, scenario)
                ratio = projected / native
                passes_runtime = projected < native
                passes_quality = gap * (1.0 - recovery) <= tolerance
                ratios.append(ratio)
                runtime_pass.append(passes_runtime)
                quality_pass.append(passes_quality)
                advantaged.append(passes_runtime and passes_quality)
            scenario_item["by_workload"][workload] = {
                "cases": len(subset),
                "median_projected_native_ratio": median(ratios) if ratios else 0.0,
                "advantaged_fraction": sum(advantaged) / float(len(advantaged)) if advantaged else 0.0,
                "runtime_pass_fraction": sum(runtime_pass) / float(len(runtime_pass)) if runtime_pass else 0.0,
                "quality_pass_fraction": sum(quality_pass) / float(len(quality_pass)) if quality_pass else 0.0,
            }
            all_advantaged.extend(advantaged)
            all_ratios.extend(ratios)
        scenario_item["overall"] = {
            "median_projected_native_ratio": median(all_ratios) if all_ratios else 0.0,
            "advantaged_fraction": sum(all_advantaged) / float(len(all_advantaged)) if all_advantaged else 0.0,
        }
        result["by_scenario"][scenario["id"]] = scenario_item
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--recovery", type=float, default=0.90)
    args = parser.parse_args()

    summary = summarize(read_rows(args.input_csv), args.recovery)
    out_dir = os.path.dirname(args.output_json)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
