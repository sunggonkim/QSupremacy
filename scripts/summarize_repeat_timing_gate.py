#!/usr/bin/env python3
"""Summarize warmup-separated repeat timing gate results."""

import argparse
import glob
import json
import math
import os
import re
import statistics
import sys


def parse_tag(path):
    name = os.path.basename(path)
    match = re.search(r"_([a-z]+)_(warmup|trial)(\d*)\.json$", name)
    if not match:
        return None
    family, phase, trial = match.groups()
    return {
        "family": family,
        "phase": phase,
        "trial": int(trial) if trial else -1,
    }


def load_rows(patterns):
    rows = []
    for pattern in patterns:
        for path in sorted(glob.glob(pattern)):
            tag = parse_tag(path)
            if not tag:
                continue
            with open(path) as f:
                data = json.load(f)
            for workload, record in data.get("workloads", {}).items():
                native = record.get("native_path", {})
                quantum = record.get("quantum_path", {})
                projection = record.get("break_even_projection", {})
                rows.append(
                    {
                        "path": path,
                        "file": os.path.basename(path),
                        "family": tag["family"],
                        "phase": tag["phase"],
                        "trial": tag["trial"],
                        "workload": workload,
                        "native_runtime_sec": float(native.get("runtime_sec", 0.0)),
                        "quantum_runtime_sec": float(
                            quantum.get(
                                "runtime_sec",
                                quantum.get("total_runtime_sec", 0.0),
                            )
                        ),
                        "total_runtime_sec": float(
                            data.get("metadata", {}).get("total_runtime_sec", 0.0)
                        ),
                        "speedup_required": float(
                            projection.get("sim_to_native_speedup_required", 0.0)
                        ),
                        "quantum_status": quantum.get("status", ""),
                    }
                )
    return rows


def stats(values):
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "stdev": None,
            "cv": None,
            "min": None,
            "max": None,
        }
    mean = statistics.mean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        "count": len(values),
        "mean": mean,
        "median": statistics.median(values),
        "stdev": stdev,
        "cv": stdev / mean if mean else None,
        "min": min(values),
        "max": max(values),
    }


def summarize(rows):
    measured = [row for row in rows if row["phase"] == "trial"]
    warmups = [row for row in rows if row["phase"] == "warmup"]
    families = sorted({row["family"] for row in rows})
    by_family = {}
    for family in families:
        subset = [row for row in measured if row["family"] == family]
        warmup_subset = [row for row in warmups if row["family"] == family]
        by_family[family] = {
            "measured_trials": len(subset),
            "warmup_trials": len(warmup_subset),
            "quantum_runtime_sec": stats(
                [row["quantum_runtime_sec"] for row in subset]
            ),
            "native_runtime_sec": stats([row["native_runtime_sec"] for row in subset]),
            "total_runtime_sec": stats([row["total_runtime_sec"] for row in subset]),
            "speedup_required": stats([row["speedup_required"] for row in subset]),
            "failed_trials": sum(1 for row in subset if row["quantum_status"] != "ok"),
        }
    required_families = {"ml", "chemistry", "optimization", "simulation"}
    family_set = set(by_family)
    max_quantum_cv = max(
        [
            item["quantum_runtime_sec"]["cv"]
            for item in by_family.values()
            if item["quantum_runtime_sec"]["cv"] is not None
        ]
        or [math.inf]
    )
    passed = (
        required_families.issubset(family_set)
        and all(by_family[f]["warmup_trials"] >= 1 for f in required_families)
        and all(by_family[f]["measured_trials"] >= 3 for f in required_families)
        and all(by_family[f]["failed_trials"] == 0 for f in required_families)
        and max_quantum_cv <= 1.0
    )
    return {
        "passed": passed,
        "cases": len(rows),
        "warmup_cases": len(warmups),
        "measured_cases": len(measured),
        "required_families": sorted(required_families),
        "families": families,
        "max_quantum_runtime_cv": max_quantum_cv,
        "by_family": by_family,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns", nargs="+")
    parser.add_argument("--summary-json", required=True)
    args = parser.parse_args()

    rows = load_rows(args.patterns)
    summary = summarize(rows)
    os.makedirs(os.path.dirname(args.summary_json), exist_ok=True)
    with open(args.summary_json, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
