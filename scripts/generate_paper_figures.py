#!/usr/bin/env python3
"""Generate paper figures from measured leadership-system results."""

import csv
import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIG_DIR = os.path.join(ROOT, "paper", "figures")
TEXT_WIDTH = 6.85
COLUMN_WIDTH = 3.35
INTRO_PATH_WIDTH = COLUMN_WIDTH * 0.39
INTRO_THRESHOLD_WIDTH = COLUMN_WIDTH * 0.57
SUBFIGURE_WIDTH = COLUMN_WIDTH * 0.48
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
STRONG_NATIVE_64_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_64node_large256c0c255_20260705024742_summary.json"
)
STRONG_NATIVE_64_SUMMARY_CSV = (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_64node_large256c0c255_20260705024742_summary.csv"
)
STRONG_SCALE_64_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_strongscale_64node_largefull_c0c255_20260705024742_summary.json"
)
STRONG_SCALE_64_SUMMARY_CSV = (
    "data/processed/perlmutter/"
    "practical_suite_strongscale_64node_largefull_c0c255_20260705024742_summary.csv"
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
    {
        "label": "64 nodes",
        "nodes": 64,
        "gpus": 256,
        "cases": 3552,
        "elapsed_sec": 261,
        "summary": STRONG_SCALE_64_SUMMARY_JSON,
    },
]


def ensure_fig_dir():
    os.makedirs(FIG_DIR, exist_ok=True)


def apply_paper_style():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 7.5,
            "axes.labelsize": 7.4,
            "axes.titlesize": 7.4,
            "axes.titleweight": "bold",
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "legend.fontsize": 6.3,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.25,
            "lines.markersize": 3.9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def style_axis(ax, grid="both"):
    ax.tick_params(axis="both", labelsize=6.5, pad=1.2, width=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        axis = "both" if grid == "both" else grid
        ax.grid(axis=axis, which="both", linestyle=":", linewidth=0.45, color="#B9B9B9")


def add_top_legend(fig, handles, labels, ncol, y=1.02, fontsize=None):
    fig.legend(
        handles,
        labels,
        ncol=ncol,
        loc="upper center",
        bbox_to_anchor=(0.5, y),
        frameon=False,
        fontsize=fontsize,
        handlelength=1.35,
        handletextpad=0.35,
        columnspacing=0.75,
    )


def legend_marker(color):
    return Line2D(
        [0],
        [0],
        marker="o",
        color="none",
        markerfacecolor=color,
        markeredgecolor="none",
        markersize=4.5,
    )


def read_csv(path):
    with open(os.path.join(ROOT, path), newline="") as f:
        return list(csv.DictReader(f))


def savefig(name, fig=None, pad=0.18):
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


def figure_intro_paths():
    fig, ax = plt.subplots(figsize=(INTRO_PATH_WIDTH, 1.25))
    draw_box(ax, (0.03, 0.40), 0.24, 0.24, "Input\ninstance", COLORS["dark"], fontsize=6.6)
    draw_box(ax, (0.35, 0.66), 0.32, 0.20, "Native\nHPC", COLORS["blue"], fontsize=6.2)
    draw_box(ax, (0.35, 0.16), 0.32, 0.20, "Quantum\ncircuit", COLORS["orange"], fontsize=6.0)
    draw_box(ax, (0.75, 0.36), 0.22, 0.30, "Time /\nquality", COLORS["green"], fontsize=6.2)
    arrow(ax, (0.27, 0.58), (0.35, 0.76))
    arrow(ax, (0.27, 0.47), (0.35, 0.27))
    arrow(ax, (0.67, 0.76), (0.75, 0.58))
    arrow(ax, (0.67, 0.27), (0.75, 0.44))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    path = os.path.join(FIG_DIR, "intro_comparison_paths.pdf")
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.06, top=0.96)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_intro_threshold_summary():
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
    fig, ax = plt.subplots(figsize=(INTRO_THRESHOLD_WIDTH, 1.42))
    ax.hlines(y, 1, values, color=colors, linewidth=2.1)
    ax.scatter(values, y, s=30, color=colors, edgecolors="#222222", linewidths=0.45, zorder=3)
    for yi, value in zip(y, values):
        ax.text(value * 1.16, yi, "{:,.0f}x".format(value), va="center", fontsize=6.0)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Required quantum speedup (x)", labelpad=1.0)
    ax.set_xlim(10, 2.2e6)
    style_axis(ax, grid="x")
    path = os.path.join(FIG_DIR, "intro_threshold_summary.pdf")
    fig.subplots_adjust(left=0.28, right=0.90, bottom=0.27, top=0.96)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_design_overview():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 3.38))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.04, 0.96, "Measurement plane", fontsize=8.0, weight="bold", color=COLORS["dark"])
    ax.text(0.58, 0.96, "Architecture projection", fontsize=8.0, weight="bold", color=COLORS["dark"])
    ax.plot([0.52, 0.52], [0.17, 0.92], color="#777777", linewidth=0.85, linestyle=":")

    draw_box(ax, (0.06, 0.82), 0.38, 0.10, "Shared task\ninput + quality", COLORS["dark"], fontsize=6.5)
    draw_box(ax, (0.05, 0.65), 0.18, 0.10, "Native\npath", COLORS["blue"], fontsize=6.5)
    draw_box(ax, (0.27, 0.65), 0.18, 0.10, "Circuit\npath", COLORS["orange"], fontsize=6.5)
    draw_box(ax, (0.05, 0.50), 0.18, 0.09, "$T_n, Q_n$", COLORS["blue"], fontsize=6.6)
    draw_box(ax, (0.27, 0.50), 0.18, 0.09, "$T_s, Q_q$", COLORS["orange"], fontsize=6.6)
    draw_box(ax, (0.07, 0.34), 0.36, 0.09, "Case record\nruntime, gates, shots", COLORS["teal"], fontsize=6.0)
    arrow(ax, (0.18, 0.82), (0.14, 0.75))
    arrow(ax, (0.32, 0.82), (0.36, 0.75))
    arrow(ax, (0.14, 0.65), (0.14, 0.59))
    arrow(ax, (0.36, 0.65), (0.36, 0.59))
    arrow(ax, (0.14, 0.50), (0.22, 0.43))
    arrow(ax, (0.36, 0.50), (0.31, 0.43))

    draw_box(ax, (0.60, 0.80), 0.34, 0.09, "Logical op speed\n$t_1,t_2,t_m$", COLORS["green"], fontsize=6.2)
    draw_box(ax, (0.60, 0.66), 0.34, 0.09, "Shot parallelism\n$P_{shots}$", COLORS["purple"], fontsize=6.2)
    draw_box(ax, (0.60, 0.52), 0.34, 0.09, "Error + control\n$T_{error}$, recovery", COLORS["red"], fontsize=6.1)
    draw_box(ax, (0.60, 0.35), 0.34, 0.10, "Break-even search\n$T_{qhw}<T_{native}$", COLORS["dark"], fontsize=6.2)
    arrow(ax, (0.43, 0.39), (0.60, 0.84))
    arrow(ax, (0.43, 0.39), (0.60, 0.70))
    arrow(ax, (0.43, 0.39), (0.60, 0.56))
    arrow(ax, (0.77, 0.52), (0.77, 0.45))

    draw_box(ax, (0.12, 0.14), 0.28, 0.10, "Advantage\nfrontier", "#F3F3F3", text_color=COLORS["dark"], fontsize=6.2)
    draw_box(ax, (0.60, 0.14), 0.34, 0.10, "Design guidance\nspeed / quality / shots", "#F3F3F3", text_color=COLORS["dark"], fontsize=5.9)
    arrow(ax, (0.77, 0.35), (0.77, 0.24))
    arrow(ax, (0.60, 0.19), (0.40, 0.19))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    path = os.path.join(FIG_DIR, "design_overview.pdf")
    fig.subplots_adjust(left=0.03, right=0.98, bottom=0.05, top=0.96)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_design_projection_flow():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.15))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.04, 0.93, "Measured case", fontsize=7.4, weight="bold", color=COLORS["dark"])
    ax.text(0.39, 0.93, "Projection engine", fontsize=7.4, weight="bold", color=COLORS["dark"])
    ax.text(0.72, 0.93, "Design output", fontsize=7.4, weight="bold", color=COLORS["dark"])

    draw_box(ax, (0.04, 0.72), 0.24, 0.11, "Native path\n$T_n, Q_n$", COLORS["blue"], fontsize=6.2)
    draw_box(ax, (0.04, 0.54), 0.24, 0.11, "Circuit path\n$T_s, Q_q$", COLORS["orange"], fontsize=6.2)
    draw_box(ax, (0.04, 0.36), 0.24, 0.11, "Circuit metadata\nqubits, gates, shots", COLORS["teal"], fontsize=5.8)
    draw_box(ax, (0.04, 0.18), 0.24, 0.11, "Quality gap\n$\\Delta Q$", COLORS["purple"], fontsize=6.1)

    draw_box(
        ax,
        (0.38, 0.58),
        0.24,
        0.16,
        "Break-even\n$T_{qhw}<T_n$",
        COLORS["dark"],
        fontsize=6.4,
    )
    draw_box(
        ax,
        (0.38, 0.32),
        0.24,
        0.16,
        "Frontier sweep\n$S, R, P_{shots}$",
        "#F4F4F4",
        text_color=COLORS["dark"],
        fontsize=6.1,
    )
    ax.text(
        0.50,
        0.22,
        "same input\nsame quality target",
        ha="center",
        va="center",
        fontsize=6.1,
        color=COLORS["dark"],
    )

    for y in [0.775, 0.595, 0.415, 0.235]:
        arrow(ax, (0.28, y), (0.38, 0.66 if y > 0.50 else 0.40), lw=0.9)
    arrow(ax, (0.50, 0.58), (0.50, 0.48), lw=0.9)

    outputs = [
        ("Speed-limited", COLORS["green"]),
        ("Quality-limited", COLORS["red"]),
        ("Shot-limited", COLORS["purple"]),
        ("Native-limited", COLORS["gray"]),
    ]
    for idx, (label, color) in enumerate(outputs):
        y = 0.72 - idx * 0.16
        draw_box(ax, (0.72, y), 0.23, 0.09, label, color, fontsize=5.9)
        arrow(ax, (0.62, 0.66 if idx < 2 else 0.40), (0.72, y + 0.045), lw=0.9)

    path = os.path.join(FIG_DIR, "design_projection_flow.pdf")
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.05, top=0.96)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_design_workload_paths():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.25))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.05, 0.94, "Family", fontsize=7.0, weight="bold", color=COLORS["dark"])
    ax.text(0.28, 0.94, "Native path", fontsize=7.0, weight="bold", color=COLORS["dark"])
    ax.text(0.59, 0.94, "Circuit path", fontsize=7.0, weight="bold", color=COLORS["dark"])
    ax.text(0.86, 0.94, "Target", fontsize=7.0, weight="bold", color=COLORS["dark"])

    rows = [
        ("ML", "6 classifiers", "QKernel/QNN", "accuracy", COLORS["blue"]),
        ("Chem.", "dense + sparse", "VQE", "energy", COLORS["teal"]),
        ("Opt.", "exact + heuristic", "QAOA", "objective", COLORS["red"]),
        ("Sim.", "dense + Krylov", "Trotter sim.", "observable", COLORS["green"]),
    ]
    for idx, (family, native, circuit, metric, color) in enumerate(rows):
        y = 0.80 - idx * 0.18
        ax.plot([0.04, 0.96], [y - 0.078, y - 0.078], color="#D6D6D6", linewidth=0.45)
        draw_box(ax, (0.05, y - 0.045), 0.13, 0.09, family, color, fontsize=6.2)
        ax.text(0.30, y, native, ha="center", va="center", fontsize=6.0, color=COLORS["dark"])
        ax.text(0.60, y, circuit, ha="center", va="center", fontsize=6.0, color=COLORS["dark"])
        ax.text(0.86, y, metric, ha="center", va="center", fontsize=6.0, color=COLORS["dark"])
        arrow(ax, (0.39, y), (0.50, y), color="#777777", lw=0.75)
        arrow(ax, (0.69, y), (0.78, y), color="#777777", lw=0.75)

    path = os.path.join(FIG_DIR, "design_workload_paths.pdf")
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.05, top=0.98)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_evaluation_evidence_flow():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.65))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    stages = [
        ("Calibrate", "160\nML cases", COLORS["blue"]),
        ("Main suite", "3,552\ncases", COLORS["green"]),
        ("Stress", "116 + 104\ncoverage", COLORS["teal"]),
        ("Scale", "4-64\nnodes", COLORS["purple"]),
        ("Stability", "12\nrepeat trials", COLORS["orange"]),
    ]
    x_positions = np.linspace(0.08, 0.88, len(stages))
    for idx, ((title, detail, color), x) in enumerate(zip(stages, x_positions)):
        draw_box(ax, (x - 0.07, 0.46), 0.14, 0.22, title, color, fontsize=5.9)
        ax.text(x, 0.30, detail, ha="center", va="center", fontsize=6.0, color=COLORS["dark"])
        if idx < len(stages) - 1:
            arrow(ax, (x + 0.07, 0.57), (x_positions[idx + 1] - 0.07, 0.57), lw=0.85)

    ax.text(
        0.50,
        0.10,
        "correctness gates -> application thresholds -> scaling -> timing evidence",
        ha="center",
        va="center",
        fontsize=6.1,
        color=COLORS["dark"],
    )

    path = os.path.join(FIG_DIR, "evaluation_evidence_flow.pdf")
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.06, top=0.96)
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


def figure_digits_legend():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 0.26))
    handles = [
        legend_marker(COLORS["blue"]),
        legend_marker(COLORS["orange"]),
    ]
    ax.axis("off")
    fig.legend(
        handles,
        ["QKernel", "QNN/VQC"],
        ncol=2,
        loc="center",
        frameon=False,
        fontsize=6.6,
        handletextpad=0.35,
        columnspacing=1.1,
    )
    path = os.path.join(FIG_DIR, "digits_legend.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_practical_suite_legend():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 0.26))
    handles = [
        legend_marker(COLORS["blue"]),
        legend_marker(COLORS["teal"]),
        legend_marker(COLORS["red"]),
        legend_marker(COLORS["green"]),
    ]
    ax.axis("off")
    fig.legend(
        handles,
        ["ML", "Chem.", "Opt.", "Sim."],
        ncol=4,
        loc="center",
        frameon=False,
        fontsize=6.4,
        handletextpad=0.30,
        columnspacing=0.85,
    )
    path = os.path.join(FIG_DIR, "practical_suite_legend.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


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
    legend = ax.get_legend()
    if legend:
        legend.remove()
    fig.subplots_adjust(top=0.98)
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
        ("chemistry", "Chem.", COLORS["teal"], 0.01),
        ("optimization", "Opt.", COLORS["red"], 0.02),
        ("simulation", "Sim.", COLORS["green"], 0.01),
    ]

    series = []
    for workload, label, color, tolerance in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        speed = np.array([float(row["speedup_required"]) for row in subset])
        quality = np.array([max(0.0, float(row["quality_gap"])) for row in subset])
        sorted_speed = np.sort(speed)
        cdf = np.arange(1, sorted_speed.size + 1) / float(sorted_speed.size)
        series.append((label, color, speed, quality, sorted_speed, cdf))

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.74))
    for label, color, speed, quality, sorted_speed, cdf in series:
        ax.scatter(
            speed,
            quality,
            s=9,
            alpha=0.26,
            color=color,
            edgecolors="none",
            label=label,
        )
        ax.scatter(
            [np.median(speed)],
            [np.median(quality)],
            s=42,
            color=color,
            edgecolors="black",
            linewidths=0.65,
            zorder=4,
        )
    ax.set_xscale("log")
    ax.set_xlabel("Required speedup (x)")
    ax.set_ylabel("Quality gap\nto native")
    style_axis(ax, grid="both")
    fig.subplots_adjust(top=0.96, bottom=0.27, left=0.18, right=0.98)
    landscape_path = os.path.join(FIG_DIR, "practical_suite_summary.pdf")
    fig.savefig(landscape_path, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.50))
    for label, color, speed, quality, sorted_speed, cdf in series:
        ax.plot(sorted_speed, cdf, color=color, linewidth=1.8, label=label)
    ax.set_xscale("log")
    ax.set_xlabel("Required speedup (x)")
    ax.set_ylabel("CDF")
    style_axis(ax, grid="both")
    fig.subplots_adjust(bottom=0.32, left=0.22, right=0.98, top=0.98)
    cdf_path = os.path.join(FIG_DIR, "practical_suite_cdf.pdf")
    fig.savefig(cdf_path, bbox_inches="tight")
    plt.close(fig)
    return [landscape_path, cdf_path]


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

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.35))
    colors = [COLORS["blue"], COLORS["teal"], COLORS["red"], COLORS["green"]]
    handles = []
    for label, color, initial, strong in zip(labels, colors, official_speed, strong_speed):
        line = ax.plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.8)[0]
        handles.append(line)
        ax.text(1.06, strong, label, fontsize=6.1, color=color, va="center", weight="bold")
    ax.set_yscale("log")
    ax.set_xlim(-0.12, 1.32)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Initial\nbaseline", "Strong\nbaseline"])
    ax.set_ylabel("Median required\nspeedup (x)")
    style_axis(ax, grid="y")
    fig.subplots_adjust(top=0.98, bottom=0.34, left=0.18, right=0.90)
    speed_path = os.path.join(FIG_DIR, "strong_native_comparison.pdf")
    fig.savefig(speed_path, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.25))
    for label, color, initial, strong in zip(labels, colors, official_quality, strong_quality):
        ax.plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.8)
        ax.text(1.06, strong, label, fontsize=6.1, color=color, va="center", weight="bold")
    ax.set_xlim(-0.12, 1.32)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Initial\nbaseline", "Strong\nbaseline"])
    ax.set_ylabel("Median\nquality gap")
    style_axis(ax, grid="y")
    fig.subplots_adjust(bottom=0.34, left=0.18, right=0.90, top=0.98)
    quality_path = os.path.join(FIG_DIR, "strong_native_quality_shift.pdf")
    fig.savefig(quality_path, bbox_inches="tight")
    plt.close(fig)
    return [speed_path, quality_path]


def figure_workload_growth():
    if not (
        os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_CSV))
        and os.path.exists(os.path.join(ROOT, STRONG_NATIVE_64_SUMMARY_CSV))
    ):
        return None

    points = [
        ("32 nodes\n3,552 cases", 3552, 257, STRONG_NATIVE_SUMMARY_CSV),
        ("64 nodes\n7,104 cases", 7104, 514, STRONG_NATIVE_64_SUMMARY_CSV),
    ]

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.45))
    cases = np.array([point[1] for point in points], dtype=float)
    elapsed = np.array([point[2] for point in points], dtype=float)
    ax.plot(cases, elapsed, marker="o", color=COLORS["blue"], linewidth=1.8)
    ax.plot(
        cases,
        elapsed[0] * cases / cases[0],
        linestyle="--",
        color=COLORS["gray"],
        linewidth=1.1,
    )
    for xval, yval in zip(cases, elapsed):
        ax.text(xval, yval + 16, "{}s".format(int(yval)), ha="center", fontsize=5.9)
    ax.set_xticks(cases)
    ax.set_xticklabels(["3.6K", "7.1K"])
    ax.set_xlabel("Application cases")
    ax.set_ylabel("Elapsed time (s)")
    ax.set_ylim(0, 590)
    style_axis(ax, grid="both")
    fig.subplots_adjust(left=0.23, right=0.98, bottom=0.28, top=0.94)
    time_path = os.path.join(FIG_DIR, "workload_growth_time.pdf")
    fig.savefig(time_path, bbox_inches="tight")
    plt.close(fig)

    workloads = [
        ("ml", "ML", COLORS["blue"]),
        ("chemistry", "Chem.", COLORS["teal"]),
        ("optimization", "Opt.", COLORS["red"]),
        ("simulation", "Sim.", COLORS["green"]),
    ]
    rows_by_run = [read_csv(points[0][3]), read_csv(points[1][3])]
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.45))
    x = np.array([0, 1], dtype=float)
    for workload, label, color in workloads:
        medians = []
        for rows in rows_by_run:
            vals = [
                float(row["quality_gap"])
                for row in rows
                if row["workload"] == workload
            ]
            medians.append(float(np.median(vals)))
        ax.plot(x, medians, marker="o", color=color, linewidth=1.55)
        label_scale = {
            "ml": 1.10,
            "optimization": 0.90,
            "chemistry": 1.16,
            "simulation": 0.84,
        }[workload]
        ax.text(
            1.05,
            medians[-1] * label_scale,
            label,
            va="center",
            fontsize=5.8,
            color=color,
            weight="bold",
        )
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(["32\nnodes", "64\nnodes"])
    ax.set_ylabel("Median\nquality gap")
    ax.set_ylim(0.01, 0.55)
    ax.set_xlim(-0.12, 1.45)
    style_axis(ax, grid="y")
    fig.subplots_adjust(left=0.23, right=0.82, bottom=0.30, top=0.94)
    quality_path = os.path.join(FIG_DIR, "workload_growth_quality.pdf")
    fig.savefig(quality_path, bbox_inches="tight")
    plt.close(fig)
    return [time_path, quality_path]


def figure_circuit_operation_mix():
    if not os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_CSV)):
        return None

    rows = read_csv(STRONG_NATIVE_SUMMARY_CSV)
    workloads = [
        ("ml", "ML", COLORS["blue"]),
        ("chemistry", "Chem.", COLORS["teal"]),
        ("optimization", "Opt.", COLORS["red"]),
        ("simulation", "Sim.", COLORS["green"]),
    ]
    categories = [
        ("one_qubit_gates", "1Q gates", COLORS["blue"]),
        ("two_qubit_gates", "2Q gates", COLORS["orange"]),
        ("measurement_ops", "meas.", COLORS["purple"]),
    ]

    fractions = []
    for workload, label, color in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        med = {
            key: float(np.median([float(row[key]) for row in subset]))
            for key, _, _ in categories
        }
        total_ops = sum(med.values())
        fractions.append([med[key] / total_ops for key, _, _ in categories])

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.60))
    y = np.arange(len(workloads))
    left = np.zeros(len(workloads))
    handles = []
    labels = []
    frac_array = np.array(fractions)
    for idx, (_, label, color) in enumerate(categories):
        values = frac_array[:, idx]
        bars = ax.barh(y, values, left=left, color=color, height=0.58)
        handles.append(bars[0])
        labels.append(label)
        for ypos, value, base in zip(y, values, left):
            if value >= 0.18:
                ax.text(
                    base + value / 2.0,
                    ypos,
                    "{:.0f}%".format(value * 100.0),
                    ha="center",
                    va="center",
                    fontsize=6.1,
                    color="white" if idx != 1 else "black",
                )
        left += values
    ax.set_yticks(y)
    ax.set_yticklabels([label for _, label, _ in workloads])
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Median circuit-operation share")
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xticklabels(["0", "50%", "100%"])
    style_axis(ax, grid="x")
    add_top_legend(fig, handles, labels, ncol=3, y=1.03, fontsize=6.2)
    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.25, top=0.70)
    path = os.path.join(FIG_DIR, "circuit_operation_mix.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_architecture_focus_matrix():
    workloads = ["ML", "Chem.", "Opt.", "Sim."]
    resources = ["Quality\nencoding", "Logical\nspeed", "Shot\nparallel", "Native\nco-design"]
    scores = np.array(
        [
            [3, 1, 1, 2],
            [2, 3, 2, 1],
            [3, 1, 1, 2],
            [2, 3, 3, 2],
        ],
        dtype=float,
    )
    colors = [COLORS["blue"], COLORS["teal"], COLORS["red"], COLORS["green"]]

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.9))
    for yidx, color in enumerate(colors):
        for xidx in range(len(resources)):
            score = scores[yidx, xidx]
            ax.scatter(
                xidx,
                yidx,
                s=42 + 58 * score,
                color=color,
                alpha=0.22 + 0.18 * score,
                edgecolors=COLORS["dark"],
                linewidths=0.45,
            )
            ax.text(
                xidx,
                yidx,
                ["L", "M", "H"][int(score) - 1],
                ha="center",
                va="center",
                fontsize=5.8,
                color=COLORS["dark"],
                weight="bold",
            )
    ax.set_xticks(np.arange(len(resources)))
    ax.set_xticklabels(resources)
    ax.set_yticks(np.arange(len(workloads)))
    ax.set_yticklabels(workloads)
    ax.set_xlim(-0.55, len(resources) - 0.45)
    ax.set_ylim(-0.55, len(workloads) - 0.45)
    ax.invert_yaxis()
    ax.grid(axis="both", linestyle=":", linewidth=0.45, color="#B9B9B9")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="both", length=0, labelsize=6.2, pad=2)
    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.23, top=0.96)
    path = os.path.join(FIG_DIR, "architecture_focus_matrix.pdf")
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

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.34))
    line_measured = ax.plot(nodes, throughput, marker="o", color=COLORS["blue"], label="measured")[0]
    line_ideal = ax.plot(nodes, ideal, linestyle="--", color=COLORS["gray"], label="ideal linear")[0]
    ax.text(nodes[-1] * 1.05, throughput[-1], "measured", color=COLORS["blue"], fontsize=6.0, va="center")
    ax.text(nodes[-1] * 1.05, ideal[-1], "ideal", color=COLORS["gray"], fontsize=6.0, va="center")
    ax.set_xscale("log", base=2)
    ax.set_xticks(nodes)
    ax.set_xticklabels([str(int(x)) for x in nodes])
    ax.set_xlabel("GPU nodes")
    ax.set_ylabel("Throughput\n(cases/s)")
    style_axis(ax, grid="both")
    ax.set_xlim(nodes[0] * 0.88, nodes[-1] * 1.62)
    fig.subplots_adjust(top=0.98, bottom=0.30, left=0.22, right=0.88)
    throughput_path = os.path.join(FIG_DIR, "weak_scaling.pdf")
    fig.savefig(throughput_path, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.34))
    line_eff = ax.plot(
        nodes,
        efficiency,
        marker="s",
        color=COLORS["orange"],
        label="per-GPU throughput",
    )[0]
    ax.axhline(1.0, linestyle="--", color=COLORS["gray"], linewidth=1.0)
    ax.text(nodes[-1] * 1.05, efficiency[-1], "per-GPU", color=COLORS["orange"], fontsize=6.0, va="center")
    ax.set_xscale("log", base=2)
    ax.set_xticks(nodes)
    ax.set_xticklabels([str(int(x)) for x in nodes])
    ax.set_xlabel("GPU nodes")
    ax.set_ylabel("Norm. per-GPU\nthroughput")
    ax.set_ylim(0.82, 1.08)
    style_axis(ax, grid="both")
    ax.set_xlim(nodes[0] * 0.88, nodes[-1] * 1.55)
    fig.subplots_adjust(top=0.98, bottom=0.32, left=0.22, right=0.88)
    efficiency_path = os.path.join(FIG_DIR, "weak_scaling_efficiency.pdf")
    fig.savefig(efficiency_path, bbox_inches="tight")
    plt.close(fig)
    return [throughput_path, efficiency_path]


def figure_strong_scaling():
    runs = [run for run in STRONG_SCALING_RUNS if load_summary(run["summary"]) is not None]
    if len(runs) < 2:
        return None

    nodes = np.array([run["nodes"] for run in runs], dtype=float)
    elapsed = np.array([run["elapsed_sec"] for run in runs], dtype=float)
    speedup = elapsed[0] / elapsed
    ideal = nodes / nodes[0]
    efficiency = speedup / ideal

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.34))
    line_time = ax.plot(nodes, elapsed / 60.0, marker="o", color=COLORS["blue"], label="measured")[0]
    line_time_ideal = ax.plot(
        nodes,
        (elapsed[0] / ideal) / 60.0,
        linestyle="--",
        color=COLORS["gray"],
        label="ideal linear",
    )[0]
    ax.text(nodes[-1] * 1.05, (elapsed / 60.0)[-1], "measured", color=COLORS["blue"], fontsize=6.0, va="center")
    ax.text(nodes[-1] * 1.05, ((elapsed[0] / ideal) / 60.0)[-1], "ideal", color=COLORS["gray"], fontsize=6.0, va="center")
    ax.set_xscale("log", base=2)
    ax.set_xticks(nodes)
    ax.set_xticklabels([str(int(x)) for x in nodes])
    ax.set_ylabel("Elapsed time\n(min)")
    ax.set_xlabel("GPU nodes")
    style_axis(ax, grid="both")
    ax.set_xlim(nodes[0] * 0.88, nodes[-1] * 1.62)
    fig.subplots_adjust(top=0.98, bottom=0.30, left=0.20, right=0.88)
    elapsed_path = os.path.join(FIG_DIR, "strong_scaling.pdf")
    fig.savefig(elapsed_path, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.34))
    line_speed = ax.plot(nodes, speedup, marker="o", color=COLORS["green"], label="measured")[0]
    line_speed_ideal = ax.plot(nodes, ideal, linestyle="--", color=COLORS["gray"], label="ideal linear")[0]
    ax.text(nodes[-1] * 1.05, speedup[-1], "measured", color=COLORS["green"], fontsize=6.0, va="center")
    ax.text(nodes[-1] * 1.05, ideal[-1], "ideal", color=COLORS["gray"], fontsize=6.0, va="center")
    ax.set_xscale("log", base=2)
    ax.set_xticks(nodes)
    ax.set_xticklabels([str(int(x)) for x in nodes])
    ax.set_xlabel("GPU nodes")
    ax.set_ylabel("Speedup vs.\n4 nodes")
    style_axis(ax, grid="both")
    ax.set_xlim(nodes[0] * 0.88, nodes[-1] * 1.62)
    fig.subplots_adjust(top=0.98, bottom=0.32, left=0.18, right=0.88)
    speedup_path = os.path.join(FIG_DIR, "strong_scaling_speedup.pdf")
    fig.savefig(speedup_path, bbox_inches="tight")
    plt.close(fig)
    return [elapsed_path, speedup_path]


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

    panel_paths = []
    for panel_index, (workload, label, tolerance) in enumerate(workloads):
        subset = [row for row in rows if row["workload"] == workload]
        required = np.array([float(row["speedup_required"]) for row in subset])
        gaps = np.array([max(0.0, float(row["quality_gap"])) for row in subset])
        frontier = np.zeros((recoveries.size, speedups.size), dtype=np.float64)
        for yi, recovery in enumerate(recoveries):
            residual_gap = gaps * (1.0 - recovery)
            for xi, speedup in enumerate(speedups):
                advantaged = (speedup >= required) & (residual_gap <= tolerance)
                frontier[yi, xi] = np.mean(advantaged) if advantaged.size else 0.0
        fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.52))
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
        ax.grid(False)
        ax.text(
            0.04,
            0.92,
            "tol={:.2g}".format(tolerance),
            transform=ax.transAxes,
            fontsize=6.0,
            color="white",
            bbox={"facecolor": "black", "alpha": 0.35, "pad": 2, "edgecolor": "none"},
        )
        if panel_index % 2 == 0:
            ax.set_ylabel("Recovery (%)")
        else:
            ax.tick_params(axis="y", labelleft=False)
        ticks = list(range(0, max_power + 1, 3))
        ax.set_xticks(ticks)
        ax.set_xticklabels(["$10^{}$".format(tick) for tick in ticks])
        if panel_index >= 2:
            ax.set_xlabel("Projected speedup (x)")
        else:
            ax.tick_params(axis="x", labelbottom=False)
        ax.tick_params(axis="both", labelsize=6.3, pad=1.0)
        cbar = fig.colorbar(image, ax=ax, shrink=0.88, pad=0.018)
        cbar.set_ticks([0.0, 0.5, 1.0])
        cbar.ax.tick_params(labelsize=6.1, pad=1.0)
        fig.subplots_adjust(left=0.15, right=0.89, bottom=0.27, top=0.98)
        suffix = "ml" if workload == "ml" else workload
        filename = (
            "advantage_frontier.pdf"
            if workload == "ml"
            else "advantage_frontier_{}.pdf".format(suffix)
        )
        panel_path = os.path.join(FIG_DIR, filename)
        fig.savefig(panel_path, bbox_inches="tight")
        plt.close(fig)
        panel_paths.append(panel_path)
    return panel_paths


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

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.55))
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
                    fontsize=5.7,
                    color="white" if label in {"quality-limited", "speed-limited", "native-dominated"} else "black",
                )
        bottom += np.array(values)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Case fraction")
    ax.set_ylim(0.0, 1.0)
    style_axis(ax, grid="y")
    add_top_legend(fig, legend_handles, legend_labels, ncol=3, y=0.995, fontsize=5.8)
    fig.subplots_adjust(top=0.62, bottom=0.20, left=0.22, right=0.98)
    path = os.path.join(FIG_DIR, "workload_taxonomy.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    apply_paper_style()
    ensure_fig_dir()
    paths = [
        figure_intro_paths(),
        figure_intro_threshold_summary(),
        figure_design_overview(),
        figure_design_projection_flow(),
        figure_design_workload_paths(),
        figure_evaluation_evidence_flow(),
        figure_digits_legend(),
        figure_digits_speedup(),
        figure_digits_quality_runtime(),
        figure_practical_suite_legend(),
        figure_practical_suite(),
        figure_strong_native_comparison(),
        figure_circuit_operation_mix(),
        figure_workload_growth(),
        figure_advantage_frontier(),
        figure_architecture_focus_matrix(),
        figure_workload_taxonomy(),
        figure_weak_scaling(),
        figure_strong_scaling(),
    ]
    for generated in paths:
        if not generated:
            continue
        if isinstance(generated, (list, tuple)):
            for path in generated:
                print(os.path.relpath(path, ROOT))
        else:
            print(os.path.relpath(generated, ROOT))


if __name__ == "__main__":
    main()
