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


def advantage_fraction(rows, speedup, recovery, tolerance):
    if not rows:
        return 0.0
    advantaged = 0
    for row in rows:
        required = float(row["speedup_required"])
        gap = max(0.0, float(row["quality_gap"]))
        residual_gap = gap * (1.0 - recovery)
        if speedup >= required and residual_gap <= tolerance:
            advantaged += 1
    return advantaged / float(len(rows))


def summarize(rows, speedups, recoveries, tolerances):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["workload"]].append(row)

    summary = {
        "cases": len(rows),
        "speedups": speedups,
        "recoveries": recoveries,
        "tolerances": tolerances,
        "by_workload": {},
    }
    for workload in sorted(grouped):
        workload_rows = grouped[workload]
        tolerance = tolerances.get(workload, 0.02)
        grid = {}
        for recovery in recoveries:
            key = "{:.2f}".format(recovery)
            grid[key] = {
                str(speedup): advantage_fraction(
                    workload_rows, speedup, recovery, tolerance
                )
                for speedup in speedups
            }
        summary["by_workload"][workload] = {
            "cases": len(workload_rows),
            "quality_tolerance": tolerance,
            "grid": grid,
        }
    return summary


def write_markdown(path, summary):
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    speedups = summary["speedups"]
    with open(path, "w") as f:
        f.write("# Advantage projection summary\n\n")
        f.write(
            "Fractions show measured cases that would enter the advantage region "
            "at a projected quantum speedup and quality-gap recovery.\n\n"
        )
        for recovery in summary["recoveries"]:
            key = "{:.2f}".format(recovery)
            f.write("## Quality-gap recovery {:.0f}%\n\n".format(recovery * 100.0))
            f.write("| Workload | Cases | Tolerance | ")
            f.write(" | ".join("{}x".format(speedup) for speedup in speedups))
            f.write(" |\n")
            f.write("| --- | ---: | ---: | ")
            f.write(" | ".join("---:" for _ in speedups))
            f.write(" |\n")
            for workload in sorted(summary["by_workload"]):
                item = summary["by_workload"][workload]
                cells = [
                    "{:.1f}%".format(item["grid"][key][str(speedup)] * 100.0)
                    for speedup in speedups
                ]
                f.write(
                    "| {} | {} | {:.3f} | {} |\n".format(
                        workload,
                        item["cases"],
                        item["quality_tolerance"],
                        " | ".join(cells),
                    )
                )
            f.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument(
        "--speedups",
        default="1000,10000,100000,1000000",
        help="Comma-separated projected speedup points.",
    )
    parser.add_argument(
        "--recoveries",
        default="0,0.5,0.9,1.0",
        help="Comma-separated quality-gap recovery fractions.",
    )
    args = parser.parse_args()

    speedups = [int(value) for value in args.speedups.split(",")]
    recoveries = [float(value) for value in args.recoveries.split(",")]
    summary = summarize(read_rows(args.input_csv), speedups, recoveries, DEFAULT_TOLERANCES)

    out_dir = os.path.dirname(args.output_json)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    write_markdown(args.output_md, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
