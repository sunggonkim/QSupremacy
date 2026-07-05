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
from matplotlib.patches import Rectangle


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIG_DIR = os.path.join(ROOT, "paper", "figures")
TEXT_WIDTH = 6.85
COLUMN_WIDTH = 3.35
COLORS = {
    "blue": "#356CA5",
    "orange": "#E6862B",
    "green": "#4C9A5F",
    "teal": "#4EA6A0",
    "red": "#D94B45",
    "purple": "#8D6AA7",
    "gray": "#6F6F6F",
    "light_gray": "#EDEDED",
    "dark": "#2F2F2F",
}
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


def apply_paper_style():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.8,
            "lines.markersize": 5.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def style_axis(ax, grid="both"):
    ax.tick_params(axis="both", labelsize=9, pad=2, width=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        axis = "both" if grid == "both" else grid
        ax.grid(axis=axis, which="both", linestyle=":", linewidth=0.55, color="#B9B9B9")


def add_top_legend(fig, handles, labels, ncol, y=1.02, fontsize=None):
    fig.legend(
        handles,
        labels,
        ncol=ncol,
        loc="upper center",
        bbox_to_anchor=(0.5, y),
        frameon=False,
        fontsize=fontsize,
        handlelength=1.6,
        handletextpad=0.45,
        columnspacing=1.0,
    )


def read_csv(path):
    with open(os.path.join(ROOT, path), newline="") as f:
        return list(csv.DictReader(f))


def savefig(name, fig=None, pad=0.35):
    if fig is None:
        fig = plt.gcf()
    path = os.path.join(FIG_DIR, name)
    fig.tight_layout(pad=pad)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def draw_box(ax, xy, width, height, label, color, text_color="white", fontsize=9, lw=0.9):
    patch = Rectangle(xy, width, height, facecolor=color, edgecolor="#333333", linewidth=lw)
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2.0,
        xy[1] + height / 2.0,
        label,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=text_color,
        linespacing=1.15,
    )
    return patch


def arrow(ax, start, end, color="#4A4A4A", lw=1.1):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={"arrowstyle": "->", "lw": lw, "color": color, "shrinkA": 3, "shrinkB": 3},
    )


def figure_intro_application_gap():
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(COLUMN_WIDTH, 3.80),
        gridspec_kw={"height_ratios": [1.05, 1.35], "hspace": 0.42},
    )

    ax = axes[0]
    ax.set_title("Same task, two paths", pad=3)
    draw_box(ax, (0.02, 0.61), 0.20, 0.19, "Input\ninstance", COLORS["dark"], fontsize=7.5)
    draw_box(ax, (0.34, 0.67), 0.28, 0.15, "Native HPC\napp", COLORS["blue"], fontsize=7.4)
    draw_box(ax, (0.74, 0.67), 0.22, 0.15, "$T_n, Q_n$", COLORS["blue"], fontsize=7.4)
    draw_box(ax, (0.34, 0.36), 0.28, 0.15, "Quantum\ncircuit app", COLORS["orange"], fontsize=7.4)
    draw_box(ax, (0.74, 0.36), 0.22, 0.15, "$T_q, Q_q$", COLORS["green"], fontsize=7.4)
    arrow(ax, (0.22, 0.70), (0.34, 0.745))
    arrow(ax, (0.62, 0.745), (0.74, 0.745))
    arrow(ax, (0.22, 0.66), (0.34, 0.435))
    arrow(ax, (0.62, 0.435), (0.74, 0.435))
    ax.text(
        0.50,
        0.12,
        "Advantage if projected quantum time < native time\nand residual quality gap <= tolerance",
        ha="center",
        va="center",
        fontsize=7.3,
        color=COLORS["dark"],
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    labels = ["QNN/VQC", "QKernel", "Sim.", "ML", "Chem.", "Opt."]
    values = [64.9, 421.9, 3071.0, 3726.4, 42491.4, 287045.6]
    colors = [
        COLORS["orange"],
        COLORS["blue"],
        COLORS["green"],
        COLORS["blue"],
        COLORS["teal"],
        COLORS["red"],
    ]
    y = np.arange(len(labels))
    axes[1].hlines(y, 1, values, color=colors, linewidth=2.1)
    axes[1].scatter(values, y, s=40, color=colors, edgecolors="#222222", linewidths=0.45, zorder=3)
    for yi, value in zip(y, values):
        axes[1].text(value * 1.18, yi, "{:,.0f}x".format(value), va="center", fontsize=7.4)
    axes[1].set_xscale("log")
    axes[1].set_yticks(y)
    axes[1].set_yticklabels(labels)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Required quantum speedup (x)")
    axes[1].set_title("Measured break-even thresholds", pad=3)
    axes[1].set_xlim(10, 2.2e6)
    style_axis(axes[1], grid="x")

    path = os.path.join(FIG_DIR, "intro_application_gap.pdf")
    fig.subplots_adjust(left=0.20, right=0.98, bottom=0.11, top=0.94, hspace=0.48)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_design_overview():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 3.70))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.06, 0.95, "Measurement", fontsize=9.5, weight="bold", color=COLORS["dark"])
    ax.text(0.62, 0.95, "Analysis", fontsize=9.5, weight="bold", color=COLORS["dark"])
    ax.plot([0.55, 0.55], [0.30, 0.92], color="#777777", linewidth=0.9, linestyle=":")

    draw_box(ax, (0.06, 0.80), 0.42, 0.11, "Shared\nworkload record", COLORS["dark"], fontsize=7.5)
    draw_box(ax, (0.04, 0.62), 0.22, 0.11, "Native\nbaseline", COLORS["blue"], fontsize=7.4)
    draw_box(ax, (0.30, 0.62), 0.22, 0.11, "Quantum\ncircuit", COLORS["orange"], fontsize=7.4)
    draw_box(ax, (0.04, 0.47), 0.22, 0.09, "$T_n, Q_n$", COLORS["blue"], fontsize=7.5)
    draw_box(ax, (0.30, 0.47), 0.22, 0.09, "$T_s, Q_q$", COLORS["orange"], fontsize=7.5)
    arrow(ax, (0.20, 0.80), (0.15, 0.73))
    arrow(ax, (0.34, 0.80), (0.41, 0.73))
    arrow(ax, (0.15, 0.62), (0.15, 0.56))
    arrow(ax, (0.41, 0.62), (0.41, 0.56))

    draw_box(ax, (0.62, 0.75), 0.33, 0.10, "Case record\n$T$, $Q$, gates", COLORS["teal"], fontsize=7.3)
    draw_box(ax, (0.62, 0.55), 0.33, 0.10, "Threshold\nspeedup + recovery", COLORS["green"], fontsize=7.0)
    draw_box(ax, (0.62, 0.35), 0.33, 0.10, "Outputs\nfrontier + taxonomy", COLORS["purple"], fontsize=7.0)
    arrow(ax, (0.26, 0.515), (0.62, 0.80))
    arrow(ax, (0.52, 0.515), (0.62, 0.80))
    arrow(ax, (0.785, 0.75), (0.785, 0.65))
    arrow(ax, (0.785, 0.55), (0.785, 0.45))

    draw_box(
        ax,
        (0.04, 0.14),
        0.20,
        0.10,
        "Control\ninput, seed",
        "#F3F3F3",
        text_color=COLORS["dark"],
        fontsize=7.0,
    )
    draw_box(
        ax,
        (0.28, 0.14),
        0.20,
        0.10,
        "Native\ncandidates",
        "#F3F3F3",
        text_color=COLORS["dark"],
        fontsize=7.0,
    )
    draw_box(
        ax,
        (0.52, 0.14),
        0.20,
        0.10,
        "Quantum\ncandidates",
        "#F3F3F3",
        text_color=COLORS["dark"],
        fontsize=7.0,
    )
    draw_box(
        ax,
        (0.76, 0.14),
        0.20,
        0.10,
        "Audit\nartifacts",
        "#F3F3F3",
        text_color=COLORS["dark"],
        fontsize=7.0,
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    path = os.path.join(FIG_DIR, "design_overview.pdf")
    fig.subplots_adjust(left=0.03, right=0.98, bottom=0.05, top=0.95)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_digits_speedup():
    rows = read_csv("data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv")
    kernel = [float(r["quantum_kernel_required_speedup"]) for r in rows]
    vqc = [float(r["qnn_vqc_required_speedup"]) for r in rows]
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.45))
    box = ax.boxplot(
        [kernel, vqc],
        tick_labels=["QKernel", "QNN/VQC"],
        patch_artist=True,
        widths=0.55,
        showfliers=False,
    )
    colors = [COLORS["blue"], COLORS["orange"]]
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.82)
    for median in box["medians"]:
        median.set_color("black")
        median.set_linewidth(1.2)
    ax.set_yscale("log")
    ax.set_ylabel("Required quantum speedup (x)")
    style_axis(ax, grid="y")
    return savefig("digits_required_speedup.pdf", fig=fig)


def figure_digits_quality_runtime():
    rows = read_csv("data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv")
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.45))
    ax.scatter(
        [float(r["quantum_kernel_required_speedup"]) for r in rows],
        [float(r["quantum_kernel_accuracy"]) for r in rows],
        s=18,
        alpha=0.7,
        label="QKernel",
        color=COLORS["blue"],
        edgecolors="none",
    )
    ax.scatter(
        [float(r["qnn_vqc_required_speedup"]) for r in rows],
        [float(r["qnn_vqc_accuracy"]) for r in rows],
        s=18,
        alpha=0.7,
        label="QNN/VQC",
        color=COLORS["orange"],
        edgecolors="none",
    )
    ax.set_xscale("log")
    ax.set_xlabel("Required quantum speedup (x)")
    ax.set_ylabel("Quantum model accuracy")
    ax.set_ylim(0.4, 1.03)
    style_axis(ax, grid="both")
    handles, labels = ax.get_legend_handles_labels()
    add_top_legend(fig, handles, labels, ncol=2, y=1.03)
    fig.subplots_adjust(top=0.82)
    return savefig("digits_quality_speedup.pdf", fig=fig)


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
        ("ml", "ML", COLORS["blue"], 0.02),
        ("chemistry", "Chemistry", COLORS["teal"], 0.01),
        ("optimization", "Optimization", COLORS["red"], 0.02),
        ("simulation", "Simulation", COLORS["green"], 0.01),
    ]

    fig, axes = plt.subplots(2, 1, figsize=(COLUMN_WIDTH, 3.65), gridspec_kw={"hspace": 0.52})
    legend_handles = []
    legend_labels = []
    for workload, label, color, tolerance in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        speed = np.array([float(row["speedup_required"]) for row in subset])
        quality = np.array([max(0.0, float(row["quality_gap"])) for row in subset])
        points = axes[0].scatter(
            speed,
            quality,
            s=12,
            alpha=0.26,
            color=color,
            edgecolors="none",
            label=label,
        )
        legend_handles.append(points)
        legend_labels.append(label)
        axes[0].scatter(
            [np.median(speed)],
            [np.median(quality)],
            s=58,
            color=color,
            edgecolors="black",
            linewidths=0.65,
            zorder=4,
        )
        sorted_speed = np.sort(speed)
        cdf = np.arange(1, sorted_speed.size + 1) / float(sorted_speed.size)
        axes[1].plot(sorted_speed, cdf, color=color, linewidth=1.8, label=label)

    axes[0].set_xscale("log")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Quality gap\nto native")
    axes[0].set_title("Runtime-quality landscape")
    axes[0].tick_params(labelbottom=False)
    style_axis(axes[0], grid="both")

    axes[1].set_xscale("log")
    axes[1].set_xlabel("Required quantum speedup (x)")
    axes[1].set_ylabel("Cumulative\ncase fraction")
    axes[1].set_title("Full threshold distribution")
    style_axis(axes[1], grid="both")
    add_top_legend(fig, legend_handles, legend_labels, ncol=2, y=0.995, fontsize=8.2)
    fig.subplots_adjust(top=0.84, bottom=0.11, hspace=0.52)

    path = os.path.join(FIG_DIR, "practical_suite_summary.pdf")
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
    labels = ["ML", "Chemistry", "Optimization", "Simulation"]
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

    fig, axes = plt.subplots(2, 1, figsize=(COLUMN_WIDTH, 3.60), gridspec_kw={"hspace": 0.52})
    colors = [COLORS["blue"], COLORS["teal"], COLORS["red"], COLORS["green"]]
    handles = []
    for label, color, initial, strong in zip(labels, colors, official_speed, strong_speed):
        line = axes[0].plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.8)[0]
        handles.append(line)
    axes[0].set_yscale("log")
    axes[0].set_xlim(-0.12, 1.12)
    axes[0].set_xticks([0, 1])
    axes[0].set_xticklabels(["Initial\nbaseline", "Strong\nbaseline"])
    axes[0].set_ylabel("Median required\nspeedup (x)")
    axes[0].set_title("Runtime threshold shift")
    axes[0].tick_params(labelbottom=False)
    style_axis(axes[0], grid="y")

    for label, color, initial, strong in zip(labels, colors, official_quality, strong_quality):
        axes[1].plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.8)
    axes[1].set_xlim(-0.12, 1.12)
    axes[1].set_xticks([0, 1])
    axes[1].set_xticklabels(["Initial\nbaseline", "Strong\nbaseline"])
    axes[1].set_ylabel("Median\nquality gap")
    axes[1].set_title("Quality gap shift")
    style_axis(axes[1], grid="y")
    add_top_legend(fig, handles, labels, ncol=2, y=0.995, fontsize=8.3)
    fig.subplots_adjust(top=0.84, bottom=0.11, hspace=0.52)

    path = os.path.join(FIG_DIR, "strong_native_comparison.pdf")
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

    fig, axes = plt.subplots(2, 1, figsize=(COLUMN_WIDTH, 3.60), gridspec_kw={"hspace": 0.52})
    line_measured = axes[0].plot(nodes, throughput, marker="o", color=COLORS["blue"], label="measured")[0]
    line_ideal = axes[0].plot(nodes, ideal, linestyle="--", color=COLORS["gray"], label="ideal linear")[0]
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks(nodes)
    axes[0].set_xticklabels([str(int(x)) for x in nodes])
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Cases / second")
    axes[0].set_title("Total throughput")
    axes[0].tick_params(labelbottom=False)
    style_axis(axes[0], grid="both")

    line_eff = axes[1].plot(
        nodes,
        efficiency,
        marker="s",
        color=COLORS["orange"],
        label="per-GPU throughput",
    )[0]
    axes[1].axhline(1.0, linestyle="--", color=COLORS["gray"], linewidth=1.0)
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks(nodes)
    axes[1].set_xticklabels([str(int(x)) for x in nodes])
    axes[1].set_xlabel("Perlmutter GPU nodes")
    axes[1].set_ylabel("Per-GPU throughput\n(normalized)")
    axes[1].set_ylim(0.82, 1.08)
    axes[1].set_title("Per-GPU stability")
    style_axis(axes[1], grid="both")
    add_top_legend(
        fig,
        [line_measured, line_ideal, line_eff],
        ["measured", "ideal", "per-GPU normalized"],
        ncol=2,
        y=0.995,
        fontsize=8.3,
    )
    fig.subplots_adjust(top=0.84, bottom=0.11, hspace=0.52)

    path = os.path.join(FIG_DIR, "weak_scaling.pdf")
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

    fig, axes = plt.subplots(2, 1, figsize=(COLUMN_WIDTH, 3.60), gridspec_kw={"hspace": 0.52})
    line_time = axes[0].plot(nodes, elapsed / 60.0, marker="o", color=COLORS["blue"], label="measured")[0]
    line_time_ideal = axes[0].plot(
        nodes,
        (elapsed[0] / ideal) / 60.0,
        linestyle="--",
        color=COLORS["gray"],
        label="ideal linear",
    )[0]
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks(nodes)
    axes[0].set_xticklabels([str(int(x)) for x in nodes])
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Elapsed time\n(min)")
    axes[0].set_title("Fixed-work elapsed time")
    axes[0].tick_params(labelbottom=False)
    style_axis(axes[0], grid="both")

    line_speed = axes[1].plot(nodes, speedup, marker="o", color=COLORS["green"], label="measured speedup")[0]
    line_speed_ideal = axes[1].plot(nodes, ideal, linestyle="--", color=COLORS["gray"], label="ideal linear")[0]
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks(nodes)
    axes[1].set_xticklabels([str(int(x)) for x in nodes])
    axes[1].set_xlabel("Perlmutter GPU nodes")
    axes[1].set_ylabel("Speedup vs.\n4-node run")
    axes[1].set_title("Time-to-solution scaling")
    style_axis(axes[1], grid="both")
    add_top_legend(
        fig,
        [line_time, line_time_ideal, line_speed, line_speed_ideal],
        ["measured time", "ideal time", "measured speedup", "ideal speedup"],
        ncol=2,
        y=0.995,
        fontsize=8.0,
    )
    fig.subplots_adjust(top=0.84, bottom=0.11, hspace=0.52)

    path = os.path.join(FIG_DIR, "strong_scaling.pdf")
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

    fig, axes = plt.subplots(2, 2, figsize=(COLUMN_WIDTH, 3.60), sharex=True, sharey=True)
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
        ax.set_title(label, pad=3, fontsize=8.8)
        ax.grid(False)
        ax.text(
            0.04,
            0.92,
            "tol={:.2g}".format(tolerance),
            transform=ax.transAxes,
            fontsize=7.3,
            color="white",
            bbox={"facecolor": "black", "alpha": 0.35, "pad": 2, "edgecolor": "none"},
        )
        ax.tick_params(axis="both", labelsize=7.5, pad=1.5)
    for ax in axes[:, 0]:
        ax.set_ylabel("Recovery (%)", fontsize=8.0)
    for ax in axes[-1, :]:
        ticks = list(range(0, max_power + 1, 3))
        ax.set_xticks(ticks)
        ax.set_xticklabels(["$10^{}$".format(tick) for tick in ticks])
    fig.text(0.44, 0.045, "Projected speedup (x)", ha="center", fontsize=8.2)
    cbar = fig.colorbar(
        image,
        ax=axes.ravel().tolist(),
        shrink=0.82,
        pad=0.02,
        label="Advantaged fraction",
    )
    cbar.ax.tick_params(labelsize=7.5)
    cbar.set_label("Advantaged fraction", fontsize=8.0)
    fig.subplots_adjust(left=0.14, right=0.82, bottom=0.14, top=0.95, wspace=0.18, hspace=0.33)
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
        "quality-limited": COLORS["red"],
        "speed-limited": COLORS["blue"],
        "shot-limited": COLORS["orange"],
        "encoding-limited": COLORS["teal"],
        "native-dominated": COLORS["purple"],
    }

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.55))
    x = np.arange(len(workloads))
    bottom = np.zeros(len(workloads))
    legend_handles = []
    legend_labels = []
    for label in taxonomy_order:
        values = []
        for workload in workloads:
            item = data["by_workload"].get(workload, {})
            values.append(float(item.get("fractions", {}).get(label, 0.0)))
        bars = ax.bar(
            x,
            values,
            bottom=bottom,
            label=label.replace("-", " "),
            color=colors[label],
            width=0.62,
        )
        legend_handles.append(bars[0])
        legend_labels.append(label.replace("-", " "))
        for xpos, value, base in zip(x, values, bottom):
            if value >= 0.15:
                ax.text(
                    xpos,
                    base + value / 2.0,
                    "{:.0f}%".format(value * 100.0),
                    ha="center",
                    va="center",
                    fontsize=8.8,
                    color="white" if label in {"quality-limited", "speed-limited", "native-dominated"} else "black",
                )
        bottom += np.array(values)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Fraction of workload cases")
    ax.set_ylim(0.0, 1.0)
    style_axis(ax, grid="y")
    add_top_legend(fig, legend_handles, legend_labels, ncol=2, y=0.995)
    fig.subplots_adjust(top=0.70, bottom=0.16)
    path = os.path.join(FIG_DIR, "workload_taxonomy.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    apply_paper_style()
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
