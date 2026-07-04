#!/usr/bin/env python3
"""Summarize accept-profile chemistry/simulation baseline evidence.

The paper needs a compact answer to: did the practical-suite run exercise
realistic chemistry instances and stronger native simulation baselines?
This script consumes the per-case summary CSV and emits a small JSON/Markdown
summary for README/paper updates.
"""

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from statistics import median


def read_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def as_float(row, key, default=0.0):
    value = row.get(key, "")
    if value in ("", None):
        return default
    return float(value)


def label_for_row(row):
    workload = row.get("workload", "")
    if workload == "chemistry":
        if row.get("problem_name"):
            return row["problem_name"]
        if row.get("chem_hamiltonian_json"):
            return os.path.splitext(os.path.basename(row["chem_hamiltonian_json"]))[0]
        return "h2_builtin"
    if workload == "simulation":
        model = row.get("sim_model", "model")
        qubits = row.get("sim_qubits", "q")
        return "{}_{}q".format(model, qubits)
    return workload or "unknown"


def summarize(rows):
    by_workload = {}
    for workload in sorted(set(row.get("workload", "unknown") for row in rows)):
        subset = [row for row in rows if row.get("workload", "unknown") == workload]
        selected = Counter(row.get("native_selected_model", "") or "unknown" for row in subset)
        best_quality = Counter(row.get("native_best_quality_model", "") or "unknown" for row in subset)
        baselines = Counter()
        for row in subset:
            key = "chem_native_baselines" if workload == "chemistry" else "sim_native_baselines"
            for baseline in (row.get(key, "") or "").split(","):
                baseline = baseline.strip()
                if baseline:
                    baselines[baseline] += 1
        by_problem = defaultdict(list)
        for row in subset:
            by_problem[label_for_row(row)].append(row)
        problem_summary = {}
        for problem, problem_rows in sorted(by_problem.items()):
            problem_summary[problem] = {
                "cases": len(problem_rows),
                "median_required_speedup": median(
                    as_float(row, "speedup_required") for row in problem_rows
                ),
                "median_quality_gap": median(
                    as_float(row, "quality_gap") for row in problem_rows
                ),
                "selected_native_models": dict(
                    sorted(
                        Counter(
                            row.get("native_selected_model", "") or "unknown"
                            for row in problem_rows
                        ).items()
                    )
                ),
            }
        by_workload[workload] = {
            "cases": len(subset),
            "median_required_speedup": median(
                as_float(row, "speedup_required") for row in subset
            ),
            "median_quality_gap": median(as_float(row, "quality_gap") for row in subset),
            "selected_native_models": dict(sorted(selected.items())),
            "best_quality_native_models": dict(sorted(best_quality.items())),
            "requested_native_baselines": dict(sorted(baselines.items())),
            "by_problem": problem_summary,
        }
    return {"cases": len(rows), "by_workload": by_workload}


def write_markdown(path, summary):
    lines = [
        "| Workload | Cases | Median required speedup | Median quality gap | Selected native models |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for workload, item in summary["by_workload"].items():
        selected = ", ".join(
            "{} {}".format(model, count)
            for model, count in item["selected_native_models"].items()
        )
        lines.append(
            "| {} | {} | {:.1f}x | {:.4f} | {} |".format(
                workload,
                item["cases"],
                item["median_required_speedup"],
                item["median_quality_gap"],
                selected,
            )
        )
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))
        f.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", default="")
    args = parser.parse_args()

    rows = read_rows(args.input_csv)
    summary = summarize(rows)
    out_dir = os.path.dirname(args.output_json)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    if args.output_md:
        write_markdown(args.output_md, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
