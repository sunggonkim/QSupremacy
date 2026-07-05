#!/usr/bin/env python3
"""Summarize chemistry coverage evidence by molecule/problem and qubit count."""

import argparse
import csv
import json
import os
from collections import Counter, defaultdict


def read_rows(path):
    with open(path) as f:
        return [row for row in csv.DictReader(f) if row.get("workload") == "chemistry"]


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


def median(values):
    ordered = sorted(values)
    count = len(ordered)
    if count == 0:
        return 0.0
    midpoint = count // 2
    if count % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def problem_label(row):
    if row.get("problem_name"):
        return row["problem_name"]
    if row.get("chem_hamiltonian_json"):
        return os.path.splitext(os.path.basename(row["chem_hamiltonian_json"]))[0]
    return "h2_builtin"


def summarize(rows):
    by_problem = defaultdict(list)
    for row in rows:
        by_problem[problem_label(row)].append(row)

    problems = {}
    for problem, problem_rows in sorted(by_problem.items()):
        qubits = sorted({as_int(row, "problem_qubits") for row in problem_rows})
        selected = Counter(
            row.get("native_selected_model", "") or "unknown" for row in problem_rows
        )
        best_quality = Counter(
            row.get("native_best_quality_model", "") or "unknown"
            for row in problem_rows
        )
        grids = sorted({as_int(row, "chem_grid") for row in problem_rows})
        layers = sorted({as_int(row, "chem_layers") for row in problem_rows})
        problems[problem] = {
            "cases": len(problem_rows),
            "qubits": qubits,
            "chem_grids": grids,
            "chem_layers": layers,
            "median_required_speedup": median(
                as_float(row, "speedup_required") for row in problem_rows
            ),
            "median_quality_gap": median(
                as_float(row, "quality_gap") for row in problem_rows
            ),
            "median_native_runtime_sec": median(
                as_float(row, "native_runtime_sec") for row in problem_rows
            ),
            "median_quantum_runtime_sec": median(
                as_float(row, "quantum_runtime_sec") for row in problem_rows
            ),
            "selected_native_models": dict(sorted(selected.items())),
            "best_quality_native_models": dict(sorted(best_quality.items())),
        }

    all_selected = Counter(
        row.get("native_selected_model", "") or "unknown" for row in rows
    )
    all_best = Counter(row.get("native_best_quality_model", "") or "unknown" for row in rows)
    qubits = sorted({as_int(row, "problem_qubits") for row in rows})

    return {
        "cases": len(rows),
        "problem_count": len(problems),
        "qubits": qubits,
        "median_required_speedup": median(
            as_float(row, "speedup_required") for row in rows
        ) if rows else 0.0,
        "median_quality_gap": median(as_float(row, "quality_gap") for row in rows)
        if rows else 0.0,
        "selected_native_models": dict(sorted(all_selected.items())),
        "best_quality_native_models": dict(sorted(all_best.items())),
        "by_problem": problems,
    }


def format_counter(counter):
    return "; ".join("{}: {}".format(key, value) for key, value in counter.items())


def write_markdown(path, summary):
    lines = [
        "| Problem | Cases | Qubits | Grids | Layers | Median required speedup | Median quality gap | Selected native | Best-quality native |",
        "| --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- |",
    ]
    for problem, item in summary["by_problem"].items():
        lines.append(
            "| {} | {} | {} | {} | {} | {:.1f}x | {:.4f} | {} | {} |".format(
                problem,
                item["cases"],
                ",".join(str(q) for q in item["qubits"]),
                ",".join(str(g) for g in item["chem_grids"]),
                ",".join(str(layer) for layer in item["chem_layers"]),
                item["median_required_speedup"],
                item["median_quality_gap"],
                format_counter(item["selected_native_models"]),
                format_counter(item["best_quality_native_models"]),
            )
        )
    out_dir = os.path.dirname(path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
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
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with open(args.output_json, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    if args.output_md:
        write_markdown(args.output_md, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
