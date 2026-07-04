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
    "practical_suite_strongnative_1node_int_20260704012008_summary.json"
)
STRONG_NATIVE_SUMMARY_CSV = (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_1node_int_20260704012008_summary.csv"
)
STRONG_NATIVE_TAXONOMY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_1node_int_20260704012008_taxonomy.json"
)
SCALE_2NODE_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_2node_large128c0c7_fix_20260704022146_summary.json"
)

SCALE_GATE_RUNS = [
    {
        "label": "1 node",
        "nodes": 1,
        "gpus": 4,
        "cases": 190,
        "elapsed_sec": 419,
        "summary": STRONG_NATIVE_SUMMARY_JSON,
    },
    {
        "label": "2 nodes",
        "nodes": 2,
        "gpus": 8,
        "cases": 224,
        "elapsed_sec": 268,
        "summary": SCALE_2NODE_SUMMARY_JSON,
    },
    {
        "label": "4 nodes",
        "nodes": 4,
        "gpus": 16,
        "cases": 448,
        "elapsed_sec": 283,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongnative_4node_large128c0c15_20260704024223_summary.json"
        ),
    },
]

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
    combined = (
        STRONG_NATIVE_SUMMARY_JSON
        if os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_JSON))
        else OFFICIAL_SUMMARY_JSON
    )
    pilot = "data/processed/perlmutter/practical_suite_55432715_summary.json"
    rel_path = combined if os.path.exists(os.path.join(ROOT, combined)) else pilot
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    workloads = ["ml", "chemistry", "optimization", "simulation"]
    speed = []
    quality = []
    labels = []
    for workload in workloads:
        item = data["by_workload"].get(workload)
        if not item:
            continue
        labels.append(workload)
        speed.append(float(item["speedup_required_median"]))
        quality.append(float(item["quality_gap_median"]))
    x = list(range(len(labels)))
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.35))
    axes[0].bar(x, speed, color="#4C78A8")
    axes[0].set_yscale("log")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    axes[0].set_ylabel("Median required speedup (x)")
    axes[0].grid(axis="y", which="both", linestyle=":", linewidth=0.6)
    axes[0].set_title("Hardware threshold")
    axes[1].bar(x, quality, color="#F58518")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
    axes[1].set_ylabel("Median quality gap")
    axes[1].grid(axis="y", linestyle=":", linewidth=0.6)
    axes[1].set_title("Quality gap")
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


def figure_salloc_pilot_comparison():
    official = load_summary(
        "data/processed/perlmutter/practical_suite_55453128_55453131_summary.json"
    )
    pilot = load_summary(
        "data/processed/perlmutter/practical_suite_55454998_prac2gint_c0c1of4_summary.json"
    )
    if official is None or pilot is None:
        return None

    workloads = ["ml", "chemistry", "optimization", "simulation"]
    labels = ["ML", "Chem.", "Opt.", "Sim."]
    official_speed = [
        float(official["by_workload"][workload]["speedup_required_median"])
        for workload in workloads
    ]
    pilot_speed = [
        float(pilot["by_workload"][workload]["speedup_required_median"])
        for workload in workloads
    ]
    official_quality = [
        float(official["by_workload"][workload]["quality_gap_median"])
        for workload in workloads
    ]
    pilot_quality = [
        float(pilot["by_workload"][workload]["quality_gap_median"])
        for workload in workloads
    ]

    x = list(range(len(workloads)))
    width = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.45))
    axes[0].bar([i - width / 2 for i in x], official_speed, width, label="190-case sweep", color="#4C78A8")
    axes[0].bar([i + width / 2 for i in x], pilot_speed, width, label="2GPU salloc pilot", color="#54A24B")
    axes[0].set_yscale("log")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, fontsize=8)
    axes[0].set_ylabel("Median required speedup (x)")
    axes[0].grid(axis="y", which="both", linestyle=":", linewidth=0.6)
    axes[0].set_title("Threshold")
    axes[0].legend(frameon=False, fontsize=7)

    axes[1].bar([i - width / 2 for i in x], official_quality, width, label="190-case sweep", color="#F58518")
    axes[1].bar([i + width / 2 for i in x], pilot_quality, width, label="2GPU salloc pilot", color="#B279A2")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, fontsize=8)
    axes[1].set_ylabel("Median quality gap")
    axes[1].grid(axis="y", linestyle=":", linewidth=0.6)
    axes[1].set_title("Quality")

    path = os.path.join(FIG_DIR, "salloc_pilot_comparison.pdf")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_strong_native_comparison():
    official = load_summary(OFFICIAL_SUMMARY_JSON)
    strong = load_summary(STRONG_NATIVE_SUMMARY_JSON)
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

    x = list(range(len(workloads)))
    width = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.45))
    axes[0].bar(
        [i - width / 2 for i in x],
        official_speed,
        width,
        label="Initial native",
        color="#4C78A8",
    )
    axes[0].bar(
        [i + width / 2 for i in x],
        strong_speed,
        width,
        label="Strong native",
        color="#E45756",
    )
    axes[0].set_yscale("log")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, fontsize=8)
    axes[0].set_ylabel("Median required speedup (x)")
    axes[0].grid(axis="y", which="both", linestyle=":", linewidth=0.6)
    axes[0].set_title("Baseline stress test")
    axes[0].legend(frameon=False, fontsize=7)

    axes[1].bar(
        [i - width / 2 for i in x],
        official_quality,
        width,
        label="Initial native",
        color="#F58518",
    )
    axes[1].bar(
        [i + width / 2 for i in x],
        strong_quality,
        width,
        label="Strong native",
        color="#72B7B2",
    )
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, fontsize=8)
    axes[1].set_ylabel("Median quality gap")
    axes[1].grid(axis="y", linestyle=":", linewidth=0.6)
    axes[1].set_title("Quality")

    path = os.path.join(FIG_DIR, "strong_native_comparison.pdf")
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


def figure_scale_out_gate():
    runs = []
    for run in SCALE_GATE_RUNS:
        data = load_summary(run["summary"])
        if data is None:
            continue
        item = dict(run)
        item["data"] = data
        runs.append(item)
    if len(runs) < 2:
        return None

    labels = [run["label"] for run in runs]
    throughput = [run["cases"] / run["elapsed_sec"] for run in runs]
    gpu_throughput = [run["cases"] / (run["elapsed_sec"] * run["gpus"]) for run in runs]
    workloads = ["ml", "chemistry", "optimization", "simulation"]
    workload_labels = ["ML", "Chem.", "Opt.", "Sim."]

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.55))
    x = np.arange(len(labels))
    width = 0.36
    axes[0].bar(x - width / 2, throughput, width, label="cases/sec", color="#4C78A8")
    axes[0].bar(x + width / 2, gpu_throughput, width, label="cases/sec/GPU", color="#F58518")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels)
    axes[0].set_ylabel("Throughput")
    axes[0].grid(axis="y", linestyle=":", linewidth=0.6)
    axes[0].legend(frameon=False, fontsize=7)
    axes[0].set_title("Bundled scale gate")

    x2 = np.arange(len(workloads))
    for index, run in enumerate(runs):
        medians = [
            float(run["data"]["by_workload"][workload]["speedup_required_median"])
            for workload in workloads
        ]
        offset = (index - (len(runs) - 1) / 2) * width
        axes[1].bar(x2 + offset, medians, width, label=run["label"])
    axes[1].set_yscale("log")
    axes[1].set_xticks(x2)
    axes[1].set_xticklabels(workload_labels)
    axes[1].set_ylabel("Median required speedup (x)")
    axes[1].grid(axis="y", which="both", linestyle=":", linewidth=0.6)
    axes[1].legend(frameon=False, fontsize=7)
    axes[1].set_title("Threshold stability")

    path = os.path.join(FIG_DIR, "scale_out_gate.pdf")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_scaling_summary():
    weak_runs = [run for run in WEAK_SCALING_RUNS if load_summary(run["summary"]) is not None]
    strong_runs = [run for run in STRONG_SCALING_RUNS if load_summary(run["summary"]) is not None]
    if len(weak_runs) < 2 or len(strong_runs) < 2:
        return None

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.65))

    weak_nodes = np.array([run["nodes"] for run in weak_runs], dtype=float)
    weak_cases_per_sec = np.array(
        [run["cases"] / run["elapsed_sec"] for run in weak_runs], dtype=float
    )
    weak_cases_per_sec_gpu = np.array(
        [run["cases"] / (run["elapsed_sec"] * run["gpus"]) for run in weak_runs],
        dtype=float,
    )
    axes[0].plot(weak_nodes, weak_cases_per_sec, marker="o", color="#4C78A8", label="cases/sec")
    axes[0].plot(
        weak_nodes,
        weak_cases_per_sec_gpu,
        marker="s",
        color="#F58518",
        label="cases/sec/GPU",
    )
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks(weak_nodes)
    axes[0].set_xticklabels([str(int(x)) for x in weak_nodes])
    axes[0].set_xlabel("Nodes")
    axes[0].set_ylabel("Throughput")
    axes[0].grid(True, which="both", linestyle=":", linewidth=0.6)
    axes[0].legend(frameon=False, fontsize=7)
    axes[0].set_title("Weak scaling")

    strong_nodes = np.array([run["nodes"] for run in strong_runs], dtype=float)
    strong_elapsed = np.array([run["elapsed_sec"] for run in strong_runs], dtype=float)
    speedup = strong_elapsed[0] / strong_elapsed
    ideal = strong_nodes / strong_nodes[0]
    axes[1].plot(strong_nodes, speedup, marker="o", color="#54A24B", label="measured")
    axes[1].plot(strong_nodes, ideal, linestyle="--", color="#888888", label="ideal")
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks(strong_nodes)
    axes[1].set_xticklabels([str(int(x)) for x in strong_nodes])
    axes[1].set_xlabel("Nodes")
    axes[1].set_ylabel("Speedup vs. 4 nodes")
    axes[1].grid(True, which="both", linestyle=":", linewidth=0.6)
    axes[1].legend(frameon=False, fontsize=7)
    axes[1].set_title("Strong scaling")

    path = os.path.join(FIG_DIR, "scaling_summary.pdf")
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
        figure_salloc_pilot_comparison(),
        figure_strong_native_comparison(),
        figure_advantage_frontier(),
        figure_workload_taxonomy(),
        figure_scale_out_gate(),
        figure_scaling_summary(),
    ]
    for path in paths:
        if path:
            print(os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
