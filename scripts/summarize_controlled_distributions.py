#!/usr/bin/env python3
"""Summarize controlled-suite distributions without hiding workload subtypes."""

import argparse
import csv
import json
import math
import os
from pathlib import Path
from statistics import median


def percentile(values, fraction):
    ordered = sorted(float(value) for value in values)
    return ordered[int(fraction * (len(ordered) - 1))]


def stats(rows):
    speedups = [float(row["speedup_required"]) for row in rows]
    gaps = [float(row["quality_gap"]) for row in rows]
    return {
        "cases": len(rows),
        "required_speedup": {
            "min": min(speedups),
            "p10": percentile(speedups, 0.10),
            "median": median(speedups),
            "geometric_mean": math.exp(
                sum(math.log(max(value, 1.0e-300)) for value in speedups)
                / len(speedups)
            ),
            "p90": percentile(speedups, 0.90),
            "max": max(speedups),
        },
        "quality_gap": {
            "min": min(gaps),
            "p10": percentile(gaps, 0.10),
            "median": median(gaps),
            "p90": percentile(gaps, 0.90),
            "max": max(gaps),
        },
    }


def subtype_key(row):
    workload = row["workload"]
    if workload == "ml":
        return "digits:{}f:d{}".format(row["ml_features"], row["ml_depth"])
    if workload == "chemistry":
        fixture = os.path.basename(row.get("chem_hamiltonian_json") or "H2_minimal")
        return "{}:layers{}".format(fixture, row["chem_layers"])
    if workload == "optimization":
        return "{}q:{}:grid{}".format(
            row["opt_nodes"], row["opt_graph"], row["opt_grid"]
        )
    if workload == "simulation":
        return "{}:{}q:steps{}".format(
            row["sim_model"], row["sim_qubits"], row["sim_steps"]
        )
    raise ValueError("unknown workload {}".format(workload))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True)
    parser.add_argument(
        "--output",
        default="data/processed/perlmutter/controlled_subtype_distributions.json",
    )
    args = parser.parse_args()

    with open(args.input_csv, newline="") as source:
        rows = [row for row in csv.DictReader(source) if row.get("status") == "ok"]

    output = {
        "schema": "qsup.controlled-subtype-distributions.v1",
        "scope": (
            "all successful same-input controlled records; family medians and "
            "p10--p90 summarize heterogeneous target distributions, while the "
            "geometric mean is retained as a secondary conventional speed-ratio "
            "summary rather than replacing the distribution"
        ),
        "input_csv": args.input_csv,
        "cases": len(rows),
        "by_workload": {},
    }
    for workload in sorted({row["workload"] for row in rows}):
        subset = [row for row in rows if row["workload"] == workload]
        keys = sorted({subtype_key(row) for row in subset})
        output["by_workload"][workload] = {
            "overall": stats(subset),
            "subtype_count": len(keys),
            "by_subtype": {
                key: stats([row for row in subset if subtype_key(row) == key])
                for key in keys
            },
        }

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(path), "cases": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
