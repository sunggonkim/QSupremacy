#!/usr/bin/env python3
"""Summarize practical workload suite JSON results."""

import argparse
import csv
import glob
import json
import os
import statistics
import sys


def load_results(patterns):
    paths = []
    for pattern in patterns:
        paths.extend(glob.glob(pattern))
    rows = []
    for path in sorted(set(paths)):
        with open(path) as f:
            data = json.load(f)
        config = data.get("config", {})
        metadata = data.get("metadata", {})
        for name, workload in data.get("workloads", {}).items():
            native = workload.get("native_path", {})
            quantum = workload.get("quantum_path", {})
            projection = workload.get("break_even_projection", {})
            dataset = workload.get("dataset", {})
            row = {
                "path": path,
                "file": os.path.basename(path),
                "workload": name,
                "family": workload.get("family", ""),
                "quality_metric": workload.get("quality_metric", ""),
                "native_runtime_sec": native.get("runtime_sec", 0.0),
                "quantum_runtime_sec": quantum.get(
                    "runtime_sec", quantum.get("total_runtime_sec", 0.0)
                ),
                "speedup_required": projection.get(
                    "sim_to_native_speedup_required", 0.0
                ),
                "one_qubit_gates": projection.get("one_qubit_gates", 0),
                "two_qubit_gates": projection.get("two_qubit_gates", 0),
                "measurement_ops": projection.get("measurement_ops", 0),
                "circuit_evaluations": projection.get("circuit_evaluations", 0),
                "slurm_job_id": metadata.get("slurm_job_id", ""),
                "total_runtime_sec": metadata.get("total_runtime_sec", 0.0),
                "seed": config.get("seed", ""),
                "ml_samples": config.get("ml_samples", ""),
                "ml_features": config.get("ml_features", ""),
                "ml_classes": config.get("ml_classes", ""),
                "ml_dataset": config.get("ml_dataset", ""),
                "digits_classes": config.get("digits_classes", ""),
                "dataset_name": dataset.get("name", ""),
                "ml_depth": config.get("ml_depth", ""),
                "chem_grid": config.get("chem_grid", ""),
                "chem_layers": config.get("chem_layers", ""),
                "chem_hamiltonian_json": config.get("chem_hamiltonian_json", ""),
                "opt_nodes": config.get("opt_nodes", ""),
                "opt_graph": config.get("opt_graph", ""),
                "opt_grid": config.get("opt_grid", ""),
                "sim_model": config.get("sim_model", ""),
                "sim_initial_state": config.get("sim_initial_state", ""),
                "sim_qubits": config.get("sim_qubits", ""),
                "sim_steps": config.get("sim_steps", ""),
                "status": quantum.get("status", ""),
            }
            if "test_accuracy" in native:
                row["native_quality"] = native.get("test_accuracy", 0.0)
                row["quantum_quality"] = quantum.get("test_accuracy", 0.0)
                row["quality_gap"] = row["native_quality"] - row["quantum_quality"]
            elif "absolute_energy_error" in quantum:
                row["native_quality"] = native.get("ground_energy", 0.0)
                row["quantum_quality"] = quantum.get("estimated_ground_energy", 0.0)
                row["quality_gap"] = quantum.get("absolute_energy_error", 0.0)
            elif "approximation_ratio" in quantum:
                row["native_quality"] = native.get("best_cut", 0.0)
                row["quantum_quality"] = quantum.get("expected_cut", 0.0)
                row["quality_gap"] = 1.0 - quantum.get("approximation_ratio", 0.0)
            elif "absolute_observable_error" in quantum:
                row["native_quality"] = native.get("z0_expectation", 0.0)
                row["quantum_quality"] = quantum.get("z0_expectation", 0.0)
                row["quality_gap"] = quantum.get("absolute_observable_error", 0.0)
            else:
                row["native_quality"] = 0.0
                row["quantum_quality"] = 0.0
                row["quality_gap"] = 0.0
            rows.append(row)
    return rows


def numeric(values):
    return [float(v) for v in values if v not in ("", None)]


def summarize(rows):
    summary = {"cases": len(rows), "by_workload": {}}
    for workload in sorted({row["workload"] for row in rows}):
        subset = [row for row in rows if row["workload"] == workload]
        speeds = numeric(row["speedup_required"] for row in subset)
        qgaps = numeric(row["quality_gap"] for row in subset)
        qtimes = numeric(row["quantum_runtime_sec"] for row in subset)
        summary["by_workload"][workload] = {
            "cases": len(subset),
            "speedup_required_min": min(speeds) if speeds else None,
            "speedup_required_median": statistics.median(speeds) if speeds else None,
            "speedup_required_max": max(speeds) if speeds else None,
            "quality_gap_median": statistics.median(qgaps) if qgaps else None,
            "quantum_runtime_sec_sum": sum(qtimes),
        }
    return summary


def write_csv(path, rows):
    if not rows:
        return
    fields = [
        "file",
        "workload",
        "family",
        "quality_metric",
        "native_runtime_sec",
        "quantum_runtime_sec",
        "speedup_required",
        "native_quality",
        "quantum_quality",
        "quality_gap",
        "one_qubit_gates",
        "two_qubit_gates",
        "measurement_ops",
        "circuit_evaluations",
        "slurm_job_id",
        "total_runtime_sec",
        "seed",
        "ml_samples",
        "ml_features",
        "ml_classes",
        "ml_dataset",
        "digits_classes",
        "dataset_name",
        "ml_depth",
        "chem_grid",
        "chem_layers",
        "chem_hamiltonian_json",
        "opt_nodes",
        "opt_graph",
        "opt_grid",
        "sim_model",
        "sim_initial_state",
        "sim_qubits",
        "sim_steps",
        "path",
        "status",
    ]
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("patterns", nargs="+")
    parser.add_argument("--summary-json", default="")
    parser.add_argument("--csv", default="")
    args = parser.parse_args()

    rows = load_results(args.patterns)
    summary = summarize(rows)
    text = json.dumps(summary, indent=2, sort_keys=True)
    print(text)

    if args.summary_json:
        out_dir = os.path.dirname(args.summary_json)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.summary_json, "w") as f:
            f.write(text)
            f.write("\n")
    if args.csv:
        write_csv(args.csv, rows)

    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
