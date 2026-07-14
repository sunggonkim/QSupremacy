#!/usr/bin/env python3
"""Summarize no-srun future-hardware projection scenarios.

This script uses existing practical-suite CSV metadata. It does not consume GPU
allocation time; it changes projection knobs such as effective shot lanes,
pipelined decode, payload-dependent host-I/O, analytical queue-tail pressure, and
logical-operation scale. Quality is never recovered by a scalar: each case keeps
its measured gap and passes only when that gap meets the workload tolerance.
"""

import argparse
import csv
import json
import os
from statistics import median

from hpca_projection_model import as_float, projected_time_sec


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
        "host_io_floor_sec_per_eval": 60.0e-6,
        "queue_service_sec_per_eval": 40.0e-6,
        "queue_utilization": 0.70,
        "queue_tail_percentile": 0.99,
        "evidence_level": "measured cycle/decoder scale plus conservative system assumptions",
        "description": "Small useful shot parallelism with analytical queue-tail pressure and larger decode/host floors.",
    },
    {
        "id": "intermediate_surface",
        "label": "Intermediate surface",
        "distance": 25.0,
        "cycle_sec": 1.0e-6,
        "shot_lanes": 1.0e3,
        "decoder_sec_per_eval": 20.0e-6,
        "host_io_floor_sec_per_eval": 50.0e-6,
        "queue_service_sec_per_eval": 30.0e-6,
        "queue_utilization": 0.55,
        "queue_tail_percentile": 0.99,
        "evidence_level": "interpolation stress point; not a resource-estimator output",
        "description": "Moderate surface-code/control interpolation with constrained shot lanes and queue tails.",
    },
    {
        "id": "default_optimistic",
        "label": "Default optimistic",
        "distance": 25.0,
        "cycle_sec": 1.0e-6,
        "shot_lanes": 1.0e4,
        "decoder_sec_per_eval": 5.0e-6,
        "host_io_floor_sec_per_eval": 20.0e-6,
        "queue_service_sec_per_eval": 30.0e-6,
        "queue_utilization": 0.35,
        "queue_tail_percentile": 0.99,
        "evidence_level": "optimistic architecture target",
        "description": "Paper default optimistic stack with an explicit analytical queue-tail hook.",
    },
    {
        "id": "ldpc_future_like",
        "label": "Low-overhead code/control",
        "distance": 15.0,
        "cycle_sec": 1.0e-6,
        "shot_lanes": 1.0e5,
        "decoder_sec_per_eval": 5.0e-6,
        "host_io_floor_sec_per_eval": 5.0e-6,
        "queue_service_sec_per_eval": 5.0e-6,
        "queue_utilization": 0.20,
        "queue_tail_percentile": 0.99,
        "evidence_level": "generic overhead sensitivity; not a QLDPC implementation or hardware forecast",
        "description": "Future lower-overhead code/control point with larger useful batching and lower queue load; QLDPC is one possible direction, not the modeled implementation.",
    },
    {
        "id": "aggressive_batched",
        "label": "Aggressive batched",
        "distance": 15.0,
        "cycle_sec": 0.5e-6,
        "shot_lanes": 1.0e6,
        "decoder_sec_per_eval": 1.0e-6,
        "host_io_floor_sec_per_eval": 0.5e-6,
        "queue_service_sec_per_eval": 0.5e-6,
        "queue_utilization": 0.08,
        "queue_tail_percentile": 0.99,
        "evidence_level": "aggressive upper-bound sensitivity",
        "description": "Aggressive high-batching point with low queue load for upper-bound sensitivity.",
    },
]


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def projected_time(row, scenario):
    return projected_time_sec(row, scenario)


def summarize(rows):
    workloads = sorted(set(row.get("workload", "unknown") for row in rows))
    result = {
        "schema": "qsup.projection-scenarios.v2",
        "cases": len(rows),
        "quality_gate": "measured quality gap <= workload tolerance",
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
                passes_quality = gap <= tolerance
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
    args = parser.parse_args()

    summary = summarize(read_rows(args.input_csv))
    out_dir = os.path.dirname(args.output_json)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(
        "wrote {} scenarios for {} cases to {}".format(
            len(SCENARIOS), summary["cases"], args.output_json
        )
    )


if __name__ == "__main__":
    main()
