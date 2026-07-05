#!/usr/bin/env python3
"""Classify measured workload cases into advantage bottleneck classes."""

import argparse
import csv
import json
import os
from collections import Counter, defaultdict


TOLERANCES = {
    "ml": 0.02,
    "chemistry": 0.01,
    "optimization": 0.02,
    "simulation": 0.01,
}


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def as_float(row, key, default=0.0):
    value = row.get(key, "")
    if value in ("", None):
        return default
    return float(value)


def as_int(row, key, default=0):
    value = row.get(key, "")
    if value in ("", None):
        return default
    return int(float(value))


def classify(row):
    workload = row["workload"]
    quality_gap = as_float(row, "quality_gap")
    speedup = as_float(row, "speedup_required")
    oneq = as_int(row, "one_qubit_gates")
    twoq = as_int(row, "two_qubit_gates")
    meas = as_int(row, "measurement_ops")
    evals = as_int(row, "circuit_evaluations")
    native_model_count = as_int(row, "native_model_count")
    total_ops = max(1, oneq + twoq + meas)
    measurement_fraction = meas / float(total_ops)
    tolerance = TOLERANCES.get(workload, 0.02)

    if quality_gap > tolerance:
        label = "quality-limited"
        reason = "quality_gap>{:.3g}".format(tolerance)
    elif speedup >= 100000.0 and native_model_count > 1:
        label = "native-dominated"
        reason = "strong_native_speed_threshold"
    elif measurement_fraction >= 0.50:
        label = "shot-limited"
        reason = "measurement_ops_fraction={:.2f}".format(measurement_fraction)
    elif workload == "ml" and evals >= 128:
        label = "encoding-limited"
        reason = "many_data_encoding_circuits"
    else:
        label = "speed-limited"
        reason = "quality_ok_runtime_dominates"

    out = dict(row)
    out["quality_tolerance"] = tolerance
    out["measurement_fraction"] = measurement_fraction
    out["taxonomy"] = label
    out["taxonomy_reason"] = reason
    return out


def summarize(rows):
    by_workload = defaultdict(Counter)
    cases_by_workload = Counter()
    for row in rows:
        workload = row["workload"]
        cases_by_workload[workload] += 1
        by_workload[workload][row["taxonomy"]] += 1
    summary = {"cases": len(rows), "by_workload": {}}
    for workload in sorted(cases_by_workload):
        cases = cases_by_workload[workload]
        counts = dict(sorted(by_workload[workload].items()))
        summary["by_workload"][workload] = {
            "cases": cases,
            "counts": counts,
            "fractions": {
                label: count / float(cases) for label, count in sorted(counts.items())
            },
        }
    return summary


def write_csv(path, rows):
    if not rows:
        return
    fields = list(rows[0].keys())
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--summary-json", required=True)
    args = parser.parse_args()

    rows = [classify(row) for row in read_rows(args.input_csv)]
    summary = summarize(rows)
    write_csv(args.output_csv, rows)
    out_dir = os.path.dirname(args.summary_json)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.summary_json, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
