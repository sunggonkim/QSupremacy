#!/usr/bin/env python3
"""Summarize and plot the matched CIFAR-10 native/quantum-feature proxy."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def elapsed_seconds(path, job_id):
    with open(path, newline="") as source:
        for row in csv.DictReader(source, delimiter="|"):
            row_id = row.get("JobIDRaw", row.get("JobID", ""))
            if row_id == str(job_id):
                if row.get("ElapsedRaw"):
                    return int(row["ElapsedRaw"])
                hours, minutes, seconds = [int(value) for value in row["Elapsed"].split(":")]
                return hours * 3600 + minutes * 60 + seconds
    raise RuntimeError("missing top-level accounting row for {}".format(job_id))


def main():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Liberation Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.5,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 8.3,
            "ytick.labelsize": 8.3,
            "legend.fontsize": 8.3,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--native", default="data/processed/perlmutter/ml_cifar10_resnet18_proxy.json"
    )
    parser.add_argument(
        "--quantum",
        default="data/processed/perlmutter/ml_cifar10_cuquantum_feature_full_55821879.json",
    )
    parser.add_argument(
        "--compact-control",
        default="data/processed/perlmutter/ml_cifar10_compact_control.json",
    )
    parser.add_argument(
        "--native-accounting",
        default="data/raw/perlmutter/accounting/sacct_ml_cifar10_resnet18_proxy_55820861.txt",
    )
    parser.add_argument(
        "--quantum-accounting",
        default="data/raw/perlmutter/accounting/sacct_ml_cifar10_cuquantum_feature_full_55821879.txt",
    )
    parser.add_argument(
        "--output", default="data/processed/perlmutter/ml_cifar10_matched_comparison.json"
    )
    parser.add_argument(
        "--runtime-figure", default="paper/figures/ml_cifar10_runtime.pdf"
    )
    parser.add_argument(
        "--accuracy-figure", default="paper/figures/ml_cifar10_accuracy.pdf"
    )
    parser.add_argument(
        "--legend-figure", default="paper/figures/ml_cifar10_legend.pdf"
    )
    args = parser.parse_args()

    native = json.loads(Path(args.native).read_text())
    quantum = json.loads(Path(args.quantum).read_text())
    compact_artifact = json.loads(Path(args.compact_control).read_text())
    compact = next(
        item for item in compact_artifact["controls"] if item["name"] == "Pool-108 + ridge"
    )
    native_compute = float(native["total_runtime_sec"])
    quantum_compute = (
        float(quantum["train_circuit"]["runtime_sec"])
        + float(quantum["test_circuit"]["runtime_sec"])
        + float(quantum["classifier"]["runtime_sec"])
    )
    native_accuracy = float(native["best_test_accuracy"])
    quantum_accuracy = float(quantum["classifier"]["test_accuracy"])
    compact_compute = float(compact["total_compute_runtime_sec"])
    compact_accuracy = float(compact["classifier"]["test_accuracy"])
    native_elapsed = elapsed_seconds(args.native_accounting, 55820861)
    quantum_elapsed = elapsed_seconds(args.quantum_accounting, 55821879)
    image_uses = int(quantum["dataset"]["train_samples"] + quantum["dataset"]["test_samples"])
    rotations_per_image = int(
        quantum["encoding"]["generic_exact_state_preparation_rotation_upper_per_image"]
    )

    output = {
        "schema": "qsup.ml-cifar10-matched-comparison.v2",
        "scope": (
            "same CIFAR-10 50k/10k comparison: A100 ResNet-18 is the deployment "
            "frontier, while fixed Pool-108 and the 12-qubit QFeature path use the "
            "same 108-feature budget and standardized ridge head; not matched "
            "end-to-end QNN training"
        ),
        "native_artifact": args.native,
        "quantum_artifact": args.quantum,
        "compact_control_artifact": args.compact_control,
        "native": {
            "model": native["model"],
            "compute_runtime_sec": native_compute,
            "allocation_elapsed_sec": native_elapsed,
            "test_accuracy": native_accuracy,
            "test_error": 1.0 - native_accuracy,
        },
        "quantum_feature": {
            "model": "12-qubit three-layer feature circuit + standardized ridge head",
            "compute_runtime_sec": quantum_compute,
            "allocation_elapsed_sec": quantum_elapsed,
            "test_accuracy": quantum_accuracy,
            "test_error": 1.0 - quantum_accuracy,
            "qubits": int(quantum["encoding"]["qubits"]),
            "features": int(quantum["train_circuit"]["features"]),
            "one_qubit_gates": int(
                quantum["train_circuit"]["executed_one_qubit_gates"]
                + quantum["test_circuit"]["executed_one_qubit_gates"]
            ),
            "two_qubit_gates": int(
                quantum["train_circuit"]["executed_two_qubit_gates"]
                + quantum["test_circuit"]["executed_two_qubit_gates"]
            ),
            "direct_state_uploads": image_uses,
            "generic_state_preparation_executed": False,
            "generic_state_preparation_rotation_upper": image_uses * rotations_per_image,
        },
        "compact_control": {
            "model": compact["name"],
            "compute_runtime_sec": compact_compute,
            "test_accuracy": compact_accuracy,
            "test_error": 1.0 - compact_accuracy,
            "features": int(compact["feature_count"]),
            "ridge_head_parameters": int(compact["ridge_head_parameters"]),
            "trainable_feature_parameters": int(
                compact["transform"]["trainable_feature_parameters"]
            ),
        },
        "ratios": {
            "quantum_to_native_compute_runtime": quantum_compute / native_compute,
            "quantum_to_native_allocation_elapsed": quantum_elapsed / native_elapsed,
            "quantum_to_native_test_error": (1.0 - quantum_accuracy) / (1.0 - native_accuracy),
            "accuracy_gap": native_accuracy - quantum_accuracy,
            "quantum_to_compact_compute_runtime": quantum_compute / compact_compute,
            "compact_minus_quantum_accuracy": compact_accuracy - quantum_accuracy,
        },
    }
    Path(args.output).write_text(json.dumps(output, indent=2) + "\n")

    systems = ("ResNet", "Pool", "Circuit")
    # Native is neutral throughout the paper; blue denotes the ML circuit path.
    colors = ("#6f6f6f", "#4c9a5f", "#3b75af")

    legend_figure, legend_axis = plt.subplots(figsize=(3.35, 0.32))
    legend_axis.axis("off")
    legend_figure.legend(
        [
            Patch(facecolor=color, edgecolor="#303030", linewidth=0.5)
            for color in colors
        ],
        ["ResNet-18 frontier", "Pool-108 control", "QFeature circuit"],
        loc="center",
        ncol=3,
        frameon=False,
        fontsize=8.3,
        handletextpad=0.35,
        columnspacing=0.65,
    )
    legend_path = Path(args.legend_figure)
    legend_path.parent.mkdir(parents=True, exist_ok=True)
    legend_figure.savefig(legend_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(legend_figure)

    def save_metric(values, ylabel, ylim, value_format, path, callouts):
        figure, axis = plt.subplots(figsize=(1.58, 1.72))
        bars = axis.bar(
            range(3),
            values,
            width=0.58,
            color=colors,
            edgecolor="#303030",
            linewidth=0.55,
            zorder=3,
        )
        for index, (bar, value) in enumerate(zip(bars, values)):
            label = value_format.format(value)
            if index in callouts:
                label += "\n({})".format(callouts[index])
            axis.text(
                bar.get_x() + bar.get_width() / 2.0,
                value + 0.025 * ylim[1],
                label,
                ha="center",
                va="bottom",
                fontsize=8.3,
                linespacing=0.95,
            )
        axis.set_xticks(range(3))
        axis.set_xticklabels(systems)
        axis.set_ylabel(ylabel)
        axis.set_ylim(*ylim)
        axis.grid(axis="y", linestyle=":", linewidth=0.48, color="#b8b8b8")
        axis.set_axisbelow(True)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(axis="both", labelsize=8.3, pad=1.0, width=0.65)
        axis.yaxis.label.set_size(8.5)
        figure.subplots_adjust(left=0.31, right=0.98, bottom=0.24, top=0.88)
        figure_path = Path(path)
        figure_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(figure_path)
        plt.close(figure)

    save_metric(
        (native_compute, compact_compute, quantum_compute),
        "Compute time (s)",
        (0.0, 145.0),
        "{:.1f}",
        args.runtime_figure,
        {2: "47.0x"},
    )
    save_metric(
        (100.0 * native_accuracy, 100.0 * compact_accuracy, 100.0 * quantum_accuracy),
        "Test accuracy (%)",
        (0.0, 100.0),
        "{:.1f}",
        args.accuracy_figure,
        {2: "-6.7 pp"},
    )
    print(args.output)
    print(args.runtime_figure)
    print(args.accuracy_figure)
    print(args.legend_figure)


if __name__ == "__main__":
    main()
