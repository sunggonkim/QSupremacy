#!/usr/bin/env python3
"""Generate paper figures from measured Perlmutter results."""

import csv
import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIG_DIR = os.path.join(ROOT, "paper", "figures")
OFFICIAL_SUMMARY_JSON = (
    "data/processed/perlmutter/practical_suite_55453128_55453131_summary.json"
)
OFFICIAL_SUMMARY_CSV = (
    "data/processed/perlmutter/practical_suite_55453128_55453131_summary.csv"
)
STRONG_NATIVE_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json"
)
STRONG_NATIVE_SUMMARY_CSV = (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv"
)
STRONG_NATIVE_TAXONOMY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json"
)
STRONG_NATIVE_1NODE_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_1node_int_20260704012008_summary.json"
)

WEAK_SCALING_RUNS = [
    {
        "label": "8 nodes",
        "nodes": 8,
        "gpus": 32,
        "cases": 896,
        "elapsed_sec": 245,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongnative_8node_large128c0c31_20260704060009_summary.json"
        ),
    },
    {
        "label": "16 nodes",
        "nodes": 16,
        "gpus": 64,
        "cases": 1792,
        "elapsed_sec": 244,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongnative_16node_large128c0c63_20260704060230_summary.json"
        ),
    },
    {
        "label": "32 nodes",
        "nodes": 32,
        "gpus": 128,
        "cases": 3552,
        "elapsed_sec": 257,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json"
        ),
    },
]

STRONG_SCALING_RUNS = [
    {
        "label": "4 nodes",
        "nodes": 4,
        "gpus": 16,
        "cases": 3552,
        "elapsed_sec": 1855,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongscale_4node_large128full_20260704060904_summary.json"
        ),
    },
    {
        "label": "8 nodes",
        "nodes": 8,
        "gpus": 32,
        "cases": 3552,
        "elapsed_sec": 913,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongscale_8node_large128full_20260704060904_summary.json"
        ),
    },
    {
        "label": "16 nodes",
        "nodes": 16,
        "gpus": 64,
        "cases": 3552,
        "elapsed_sec": 665,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongscale_16node_large128full_20260704060904_summary.json"
        ),
    },
    {
        "label": "32 nodes",
        "nodes": 32,
        "gpus": 128,
        "cases": 3552,
        "elapsed_sec": 257,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json"
        ),
    },
]


def ensure_fig_dir():
    os.makedirs(FIG_DIR, exist_ok=True)


def read_csv(path):
    with open(os.path.join(ROOT, path), newline="") as f:
        return list(csv.DictReader(f))


def savefig(name):
    path = os.path.join(FIG_DIR, name)
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def figure_intro_application_gap():
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.6))

    stages = [
        ("Native HPC", 0.14, "#4C78A8"),
        ("Quantum\ncircuit app", 0.50, "#F58518"),
        ("Projected\nQHW path", 0.84, "#54A24B"),
    ]
    for label, x, color in stages:
        axes[0].add_patch(
            plt.Rectangle((x - 0.12, 0.42), 0.24, 0.25, color=color, alpha=0.82)
        )
        axes[0].text(x, 0.545, label, ha="center", va="center", fontsize=8, color="white")
    for x0, x1 in [(0.26, 0.38), (0.62, 0.72)]:
        axes[0].annotate(
            "",
            xy=(x1, 0.545),
            xytext=(x0, 0.545),
            arrowprops={"arrowstyle": "->", "lw": 1.1, "color": "#555555"},
        )
    axes[0].text(0.50, 0.25, "Same input, same quality target", ha="center", fontsize=8)
    axes[0].text(0.50, 0.12, "Question: how fast must quantum hardware be?", ha="center", fontsize=8)
    axes[0].set_xlim(0, 1)
    axes[0].set_ylim(0, 1)
    axes[0].axis("off")
    axes[0].set_title("Application-level comparison")

    labels = ["Digits\nQNN/VQC", "Digits\nQKernel", "ML", "Chem.", "Opt.", "Sim."]
    values = [64.9, 421.9, 3483.4, 39654.6, 378588.2, 9634.5]
    colors = ["#F58518", "#4C78A8", "#4C78A8", "#72B7B2", "#E45756", "#54A24B"]
    axes[1].bar(np.arange(len(labels)), values, color=colors)
    axes[1].set_yscale("log")
    axes[1].set_xticks(np.arange(len(labels)))
    axes[1].set_xticklabels(labels, fontsize=7)
    axes[1].set_ylabel("Median required speedup (x)")
    axes[1].grid(axis="y", which="both", linestyle=":", linewidth=0.6)
    axes[1].set_title("Measured thresholds")

    path = os.path.join(FIG_DIR, "intro_application_gap.pdf")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_design_overview():
    fig, ax = plt.subplots(figsize=(6.8, 2.65))
    boxes = [
        ("Shared\nworkload", 0.08, "#4C78A8"),
        ("Native HPC\npath", 0.30, "#4C78A8"),
        ("Quantum circuit\npath", 0.52, "#F58518"),
        ("Cost and quality\nrecords", 0.74, "#72B7B2"),
        ("Advantage\nfrontier", 0.92, "#54A24B"),
    ]
    for label, x, color in boxes:
        ax.add_patch(
            plt.Rectangle((x - 0.085, 0.47), 0.17, 0.24, color=color, alpha=0.86)
        )
        ax.text(x, 0.59, label, ha="center", va="center", fontsize=8, color="white")
    for x0, x1 in [(0.165, 0.215), (0.385, 0.435), (0.605, 0.655), (0.825, 0.845)]:
        ax.annotate(
            "",
            xy=(x1, 0.59),
            xytext=(x0, 0.59),
            arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#555555"},
        )
    ax.text(0.30, 0.30, "$T_{native}$, quality", ha="center", fontsize=8)
    ax.text(0.52, 0.30, "qubits, gates, shots, $T_{sim}$", ha="center", fontsize=8)
    ax.text(0.83, 0.18, "$T_{qhw} < T_{native}$ under the same target quality", ha="center", fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    path = os.path.join(FIG_DIR, "design_overview.pdf")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_digits_speedup():
    rows = read_csv("data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv")
    kernel = [float(r["quantum_kernel_required_speedup"]) for r in rows]
    vqc = [float(r["qnn_vqc_required_speedup"]) for r in rows]
    plt.figure(figsize=(3.35, 2.35))
    box = plt.boxplot(
        [kernel, vqc],
        tick_labels=["QKernel", "QNN/VQC"],
        patch_artist=True,
        widths=0.55,
        showfliers=False,
    )
    colors = ["#4C78A8", "#F58518"]
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    plt.yscale("log")
    plt.ylabel("Required speedup (x)")
    plt.grid(axis="y", which="both", linestyle=":", linewidth=0.6)
    plt.title("Digits: hardware threshold")
    return savefig("digits_required_speedup.pdf")


def figure_digits_quality_runtime():
    rows = read_csv("data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv")
    plt.figure(figsize=(3.35, 2.35))
    plt.scatter(
        [float(r["quantum_kernel_required_speedup"]) for r in rows],
        [float(r["quantum_kernel_accuracy"]) for r in rows],
        s=14,
        alpha=0.7,
        label="QKernel",
        color="#4C78A8",
    )
    plt.scatter(
        [float(r["qnn_vqc_required_speedup"]) for r in rows],
        [float(r["qnn_vqc_accuracy"]) for r in rows],
        s=14,
        alpha=0.7,
        label="QNN/VQC",
        color="#F58518",
    )
    plt.xscale("log")
    plt.xlabel("Required speedup (x)")
    plt.ylabel("Test accuracy")
    plt.ylim(0.4, 1.03)
    plt.grid(True, which="both", linestyle=":", linewidth=0.6)
    plt.legend(frameon=False, fontsize=8)
    plt.title("Quality vs. threshold")
    return savefig("digits_quality_speedup.pdf")


def figure_practical_suite():
    rel_path = (
        STRONG_NATIVE_SUMMARY_CSV
        if os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_CSV))
        else OFFICIAL_SUMMARY_CSV
    )
    if not os.path.exists(os.path.join(ROOT, rel_path)):
        return None
    rows = read_csv(rel_path)
    workloads = [
        ("ml", "ML", "#4C78A8", 0.02),
        ("chemistry", "Chem.", "#72B7B2", 0.01),
        ("optimization", "Opt.", "#E45756", 0.02),
        ("simulation", "Sim.", "#54A24B", 0.01),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.65))
    for workload, label, color, tolerance in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        speed = np.array([float(row["speedup_required"]) for row in subset])
        quality = np.array([max(0.0, float(row["quality_gap"])) for row in subset])
        axes[0].scatter(
            speed,
            quality,
            s=8,
            alpha=0.22,
            color=color,
            edgecolors="none",
            label=label,
        )
        axes[0].scatter(
            [np.median(speed)],
            [np.median(quality)],
            s=42,
            color=color,
            edgecolors="black",
            linewidths=0.5,
            zorder=4,
        )
        sorted_speed = np.sort(speed)
        cdf = np.arange(1, sorted_speed.size + 1) / float(sorted_speed.size)
        axes[1].plot(sorted_speed, cdf, color=color, linewidth=1.35, label=label)

    axes[0].set_xscale("log")
    axes[0].set_xlabel("Required speedup (x)")
    axes[0].set_ylabel("Quality gap")
    axes[0].grid(True, which="both", linestyle=":", linewidth=0.6)
    axes[0].legend(frameon=False, fontsize=7, ncol=2, loc="upper left")
    axes[0].set_title("Threshold-quality landscape")

    axes[1].set_xscale("log")
    axes[1].set_xlabel("Required speedup (x)")
    axes[1].set_ylabel("Fraction of cases")
    axes[1].grid(True, which="both", linestyle=":", linewidth=0.6)
    axes[1].legend(frameon=False, fontsize=7, loc="lower right")
    axes[1].set_title("Threshold CDF")

    path = os.path.join(FIG_DIR, "practical_suite_summary.pdf")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def load_summary(rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def figure_strong_native_comparison():
    official = load_summary(OFFICIAL_SUMMARY_JSON)
    strong = load_summary(STRONG_NATIVE_1NODE_SUMMARY_JSON)
    if official is None or strong is None:
        return None

    workloads = ["ml", "chemistry", "optimization", "simulation"]
    labels = ["ML", "Chem.", "Opt.", "Sim."]
    official_speed = [
        float(official["by_workload"][workload]["speedup_required_median"])
        for workload in workloads
    ]
    strong_speed = [
        float(strong["by_workload"][workload]["speedup_required_median"])
        for workload in workloads
    ]
    official_quality = [
        float(official["by_workload"][workload]["quality_gap_median"])
        for workload in workloads
    ]
    strong_quality = [
        float(strong["by_workload"][workload]["quality_gap_median"])
        for workload in workloads
    ]

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.45))
    colors = ["#4C78A8", "#72B7B2", "#E45756", "#54A24B"]
    for label, color, initial, strong in zip(labels, colors, official_speed, strong_speed):
        axes[0].plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.35)
        axes[0].text(1.03, strong, label, va="center", fontsize=7)
    axes[0].set_yscale("log")
    axes[0].set_xlim(-0.12, 1.42)
    axes[0].set_xticks([0, 1])
    axes[0].set_xticklabels(["Initial", "Strong"])
    axes[0].set_ylabel("Median required speedup (x)")
    axes[0].grid(axis="y", which="both", linestyle=":", linewidth=0.6)
    axes[0].set_title("Threshold shift")

    for label, color, initial, strong in zip(labels, colors, official_quality, strong_quality):
        axes[1].plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.35)
        axes[1].text(1.03, strong, label, va="center", fontsize=7)
    axes[1].set_xlim(-0.12, 1.42)
    axes[1].set_xticks([0, 1])
    axes[1].set_xticklabels(["Initial", "Strong"])
    axes[1].set_ylabel("Median quality gap")
    axes[1].grid(axis="y", linestyle=":", linewidth=0.6)
    axes[1].set_title("Quality shift")

    path = os.path.join(FIG_DIR, "strong_native_comparison.pdf")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_weak_scaling():
    runs = [run for run in WEAK_SCALING_RUNS if load_summary(run["summary"]) is not None]
    if len(runs) < 2:
        return None

    nodes = np.array([run["nodes"] for run in runs], dtype=float)
    gpus = np.array([run["gpus"] for run in runs], dtype=float)
    cases = np.array([run["cases"] for run in runs], dtype=float)
    elapsed = np.array([run["elapsed_sec"] for run in runs], dtype=float)
    throughput = cases / elapsed
    ideal = throughput[0] * (nodes / nodes[0])
    per_gpu = cases / (elapsed * gpus)
    efficiency = per_gpu / per_gpu[0]

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.45))
    axes[0].plot(nodes, throughput, marker="o", color="#4C78A8", label="measured")
    axes[0].plot(nodes, ideal, linestyle="--", color="#888888", label="ideal")
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks(nodes)
    axes[0].set_xticklabels([str(int(x)) for x in nodes])
    axes[0].set_xlabel("Nodes")
    axes[0].set_ylabel("Cases/sec")
    axes[0].grid(True, which="both", linestyle=":", linewidth=0.6)
    axes[0].legend(frameon=False, fontsize=7)
    axes[0].set_title("Total throughput")

    axes[1].plot(nodes, efficiency, marker="s", color="#F58518", label="per-GPU efficiency")
    axes[1].axhline(1.0, linestyle="--", color="#888888", linewidth=0.9)
    for x, y, seconds, case_count in zip(nodes, efficiency, elapsed, cases):
        axes[1].annotate(
            "{} cases\n{:.1f} min".format(int(case_count), seconds / 60.0),
            xy=(x, y),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=6.5,
        )
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks(nodes)
    axes[1].set_xticklabels([str(int(x)) for x in nodes])
    axes[1].set_xlabel("Nodes")
    axes[1].set_ylabel("Normalized cases/sec/GPU")
    axes[1].set_ylim(0.82, 1.08)
    axes[1].grid(True, which="both", linestyle=":", linewidth=0.6)
    axes[1].set_title("Per-GPU stability")

    path = os.path.join(FIG_DIR, "weak_scaling.pdf")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_strong_scaling():
    runs = [run for run in STRONG_SCALING_RUNS if load_summary(run["summary"]) is not None]
    if len(runs) < 2:
        return None

    nodes = np.array([run["nodes"] for run in runs], dtype=float)
    elapsed = np.array([run["elapsed_sec"] for run in runs], dtype=float)
    speedup = elapsed[0] / elapsed
    ideal = nodes / nodes[0]
    efficiency = speedup / ideal

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.45))
    axes[0].plot(nodes, elapsed / 60.0, marker="o", color="#4C78A8", label="measured")
    axes[0].plot(
        nodes,
        (elapsed[0] / ideal) / 60.0,
        linestyle="--",
        color="#888888",
        label="ideal",
    )
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks(nodes)
    axes[0].set_xticklabels([str(int(x)) for x in nodes])
    axes[0].set_xlabel("Nodes")
    axes[0].set_ylabel("Elapsed time (min)")
    axes[0].grid(True, which="both", linestyle=":", linewidth=0.6)
    axes[0].legend(frameon=False, fontsize=7)
    axes[0].set_title("Fixed 3,552-case time")

    axes[1].plot(nodes, speedup, marker="o", color="#54A24B", label="speedup")
    axes[1].plot(nodes, ideal, linestyle="--", color="#888888", label="ideal")
    axes[1].plot(nodes, efficiency, marker="s", color="#F58518", label="efficiency")
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks(nodes)
    axes[1].set_xticklabels([str(int(x)) for x in nodes])
    axes[1].set_xlabel("Nodes")
    axes[1].set_ylabel("Speedup / efficiency")
    axes[1].grid(True, which="both", linestyle=":", linewidth=0.6)
    axes[1].legend(frameon=False, fontsize=7)
    axes[1].set_title("Speedup vs. 4 nodes")

    path = os.path.join(FIG_DIR, "strong_scaling.pdf")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_advantage_frontier():
    rel_path = (
        STRONG_NATIVE_SUMMARY_CSV
        if os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_CSV))
        else OFFICIAL_SUMMARY_CSV
    )
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    rows = read_csv(rel_path)
    workloads = [
        ("ml", "ML", 0.02),
        ("chemistry", "Chem.", 0.01),
        ("optimization", "Opt.", 0.02),
        ("simulation", "Sim.", 0.01),
    ]
    max_speed = max(float(row["speedup_required"]) for row in rows)
    max_power = max(6, int(math.ceil(math.log10(max_speed * 1.25))))
    speedups = np.logspace(0, max_power, 121)
    recoveries = np.linspace(0.0, 1.0, 101)

    fig, axes = plt.subplots(2, 2, figsize=(6.8, 5.1), sharex=True, sharey=True)
    image = None
    for ax, (workload, label, tolerance) in zip(axes.flat, workloads):
        subset = [row for row in rows if row["workload"] == workload]
        required = np.array([float(row["speedup_required"]) for row in subset])
        gaps = np.array([max(0.0, float(row["quality_gap"])) for row in subset])
        frontier = np.zeros((recoveries.size, speedups.size), dtype=np.float64)
        for yi, recovery in enumerate(recoveries):
            residual_gap = gaps * (1.0 - recovery)
            for xi, speedup in enumerate(speedups):
                advantaged = (speedup >= required) & (residual_gap <= tolerance)
                frontier[yi, xi] = np.mean(advantaged) if advantaged.size else 0.0
        image = ax.imshow(
            frontier,
            origin="lower",
            aspect="auto",
            extent=[0, max_power, 0, 100],
            vmin=0.0,
            vmax=1.0,
            cmap="viridis",
        )
        if np.min(frontier) < 0.5 < np.max(frontier):
            ax.contour(
                np.linspace(0, max_power, speedups.size),
                recoveries * 100.0,
                frontier,
                levels=[0.5],
                colors="white",
                linewidths=1.0,
            )
        ax.set_title("{} frontier".format(label))
        ax.grid(False)
        ax.text(
            0.04,
            0.92,
            "tol={:.2g}".format(tolerance),
            transform=ax.transAxes,
            fontsize=7,
            color="white",
            bbox={"facecolor": "black", "alpha": 0.35, "pad": 2, "edgecolor": "none"},
        )
    for ax in axes[:, 0]:
        ax.set_ylabel("Quality-gap recovery (%)")
    for ax in axes[-1, :]:
        ax.set_xlabel("Projected quantum speedup")
        ticks = list(range(0, max_power + 1, 2))
        ax.set_xticks(ticks)
        ax.set_xticklabels(["$10^{}$".format(tick) for tick in ticks])
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.88, label="Cases in advantage region")
    path = os.path.join(FIG_DIR, "advantage_frontier.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_workload_taxonomy():
    data = load_summary(STRONG_NATIVE_TAXONOMY_JSON)
    if data is None:
        return None

    workloads = ["ml", "chemistry", "optimization", "simulation"]
    labels = ["ML", "Chem.", "Opt.", "Sim."]
    taxonomy_order = [
        "quality-limited",
        "speed-limited",
        "shot-limited",
        "encoding-limited",
        "native-dominated",
    ]
    colors = {
        "quality-limited": "#E45756",
        "speed-limited": "#4C78A8",
        "shot-limited": "#F58518",
        "encoding-limited": "#72B7B2",
        "native-dominated": "#B279A2",
    }

    fig, ax = plt.subplots(figsize=(6.8, 2.45))
    x = np.arange(len(workloads))
    bottom = np.zeros(len(workloads))
    for label in taxonomy_order:
        values = []
        for workload in workloads:
            item = data["by_workload"].get(workload, {})
            values.append(float(item.get("fractions", {}).get(label, 0.0)))
        ax.bar(
            x,
            values,
            bottom=bottom,
            label=label.replace("-", " "),
            color=colors[label],
            width=0.62,
        )
        bottom += np.array(values)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Fraction of cases")
    ax.set_ylim(0.0, 1.0)
    ax.grid(axis="y", linestyle=":", linewidth=0.6)
    ax.legend(ncol=3, frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 1.28))
    ax.set_title("Workload bottleneck taxonomy")
    path = os.path.join(FIG_DIR, "workload_taxonomy.pdf")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    ensure_fig_dir()
    paths = [
        figure_intro_application_gap(),
        figure_design_overview(),
        figure_digits_speedup(),
        figure_digits_quality_runtime(),
        figure_practical_suite(),
        figure_strong_native_comparison(),
        figure_advantage_frontier(),
        figure_workload_taxonomy(),
        figure_weak_scaling(),
        figure_strong_scaling(),
    ]
    for path in paths:
        if path:
            print(os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
