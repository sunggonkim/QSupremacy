#!/usr/bin/env python3
"""Evaluate a conservative near-QPU feedback-aggregation mechanism."""

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

from hpca_projection_model import as_float, projected_components_sec


BATCH_SIZES = (1, 4, 16, 64)
WORKLOADS = (
    ("ml", "ML", "#3776ab", "o", "-"),
    ("chemistry", "Chem.", "#4caa88", "s", "--"),
    ("optimization", "Opt.", "#e45756", "D", "-."),
    ("simulation", "Sim.", "#4f9d69", "^", ":"),
)


def mechanism_total(components, evaluations, batch_size):
    rounds = math.ceil(evaluations / float(batch_size))
    round_fraction = rounds / evaluations
    # Component fields are application totals over all evaluations. Scaling the
    # total host term by rounds/evaluations is exactly rounds * per-round cost.
    batched_round_cost = round_fraction * (
        components["host_io_sec"]
        + components["queue_sec"]
        + components["context_sec"]
    )
    preserved_fixed_cost = (
        components["critical_gate_sec"]
        + components["critical_decode_sec"]
        + components["controller_sec"]
    )
    return preserved_fixed_cost + batched_round_cost, rounds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=(
            "data/processed/perlmutter/"
            "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv"
        ),
    )
    parser.add_argument(
        "--output",
        default="data/processed/perlmutter/feedback_aggregator_ablation.json",
    )
    parser.add_argument(
        "--figure", default="paper/figures/feedback_aggregator_ablation.pdf"
    )
    args = parser.parse_args()

    with open(args.input, newline="") as source:
        rows = [row for row in csv.DictReader(source) if row.get("status") == "ok"]

    output = {
        "schema": "qsup.feedback-aggregator-ablation.v1",
        "scope": (
            "analytic mechanism ablation over measured records; batches host-I/O, "
            "p99 queue, and host-context rounds only, while preserving gate, decoder, "
            "controller, native deadline, and quality costs"
        ),
        "independence_assumption": (
            "maximum available-independence envelope: every recorded circuit evaluation "
            "is eligible up to B; sequential dependency width is not measured"
        ),
        "source_artifact": args.input,
        "batch_sizes": list(BATCH_SIZES),
        "cases": len(rows),
        "by_workload": {},
    }

    for workload, _, _, _, _ in WORKLOADS:
        subset = [row for row in rows if row["workload"] == workload]
        records = []
        baseline_totals = []
        prepared = []
        for row in subset:
            components = projected_components_sec(row)
            evaluations = max(1.0, as_float(row, "circuit_evaluations", 1.0))
            baseline, _ = mechanism_total(components, evaluations, 1)
            baseline_totals.append(baseline)
            prepared.append((components, evaluations, baseline))
        for batch_size in BATCH_SIZES:
            totals = []
            ratios = []
            speedups = []
            rounds = []
            for components, evaluations, baseline in prepared:
                total, host_rounds = mechanism_total(
                    components, evaluations, batch_size
                )
                native = max(components["native_deadline_sec"], 1.0e-12)
                totals.append(total)
                ratios.append(total / native)
                speedups.append(baseline / total)
                rounds.append(host_rounds)
            records.append({
                "batch_size": batch_size,
                "median_projected_total_sec": statistics.median(totals),
                "median_projected_to_native": statistics.median(ratios),
                "median_mechanism_speedup": statistics.median(speedups),
                "runtime_pass_fraction": sum(ratio < 1.0 for ratio in ratios) / len(ratios),
                "median_host_rounds": statistics.median(rounds),
            })
        output["by_workload"][workload] = {
            "cases": len(subset),
            "median_circuit_evaluations": statistics.median(
                as_float(row, "circuit_evaluations", 1.0) for row in subset
            ),
            "records": records,
        }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(output, indent=2) + "\n")

    figure, axis = plt.subplots(figsize=(3.35, 1.86))
    for workload, label, color, marker, linestyle in WORKLOADS:
        records = output["by_workload"][workload]["records"]
        axis.plot(
            [record["batch_size"] for record in records],
            [record["median_mechanism_speedup"] for record in records],
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=1.55,
            markersize=4.2,
            label=label,
        )
    axis.set_xscale("log", base=2)
    axis.set_xticks(BATCH_SIZES)
    axis.set_xticklabels([str(value) for value in BATCH_SIZES])
    axis.set_xlabel("Max independent groups per round")
    axis.set_ylabel("Median speedup vs. $B=1$")
    axis.grid(True, which="both", linestyle=":", linewidth=0.6, color="#b8b8b8")
    handles, labels = axis.get_legend_handles_labels()
    figure.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.995),
        ncol=4,
        frameon=False,
        fontsize=6.8,
        columnspacing=0.7,
        handletextpad=0.35,
    )
    axis.tick_params(labelsize=8)
    axis.xaxis.label.set_size(8.5)
    axis.yaxis.label.set_size(8.5)
    figure.subplots_adjust(left=0.19, right=0.985, bottom=0.23, top=0.84)
    figure_path = Path(args.figure)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(figure_path)
    plt.close(figure)
    print(output_path)
    print(figure_path)


if __name__ == "__main__":
    main()
