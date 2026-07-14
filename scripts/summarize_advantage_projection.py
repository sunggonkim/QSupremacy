#!/usr/bin/env python3
"""Summarize projected advantage fractions from measured practical-suite cases."""

import argparse
import csv
import json
import os
from collections import defaultdict


DEFAULT_TOLERANCES = {
    "ml": 0.02,
    "chemistry": 0.01,
    "optimization": 0.02,
    "simulation": 0.01,
}


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def advantage_fraction(rows, speedup, tolerance):
    if not rows:
        return 0.0
    advantaged = 0
    for row in rows:
        required = float(row["speedup_required"])
        gap = max(0.0, float(row["quality_gap"]))
        if speedup >= required and gap <= tolerance:
            advantaged += 1
    return advantaged / float(len(rows))


def summarize(rows, speedups, tolerances):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["workload"]].append(row)

    summary = {
        "schema": "qsup.advantage-projection.v2",
        "cases": len(rows),
        "speedups": speedups,
        "quality_gate": "measured quality gap <= workload tolerance",
        "tolerances": tolerances,
        "by_workload": {},
    }
    for workload in sorted(grouped):
        workload_rows = grouped[workload]
        tolerance = tolerances.get(workload, 0.02)
        grid = {
            str(speedup): advantage_fraction(
                workload_rows, speedup, tolerance
            )
            for speedup in speedups
        }
        summary["by_workload"][workload] = {
            "cases": len(workload_rows),
            "quality_tolerance": tolerance,
            "grid": grid,
        }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument(
        "--speedups",
        default="1000,10000,100000,1000000",
        help="Comma-separated projected speedup points.",
    )
    args = parser.parse_args()

    speedups = [int(value) for value in args.speedups.split(",")]
    summary = summarize(read_rows(args.input_csv), speedups, DEFAULT_TOLERANCES)

    out_dir = os.path.dirname(args.output_json)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
