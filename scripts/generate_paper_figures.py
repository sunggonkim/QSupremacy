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
INTRO_PATH_WIDTH = COLUMN_WIDTH * 0.42
INTRO_THRESHOLD_WIDTH = COLUMN_WIDTH * 0.54
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
ML_STRONG_NATIVE_GATE_JSON = (
    "data/processed/perlmutter/ml_strong_native_gate_latest.json"
)
ML_STRONG_NATIVE_PROFILE_JSON = (
    "data/processed/perlmutter/ml_strong_native_profile_latest.json"
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
    fig, ax = plt.subplots(figsize=(INTRO_PATH_WIDTH, 1.28))
    draw_box(ax, (0.02, 0.39), 0.20, 0.24, "Same\ninput", COLORS["dark"], fontsize=6.3)
    draw_box(ax, (0.31, 0.66), 0.25, 0.20, "Native\nHPC", COLORS["blue"], fontsize=6.0)
    draw_box(ax, (0.31, 0.39), 0.25, 0.20, "Circuit\napp", COLORS["orange"], fontsize=6.0)
    draw_box(ax, (0.31, 0.12), 0.25, 0.20, "Quality\ntarget", COLORS["purple"], fontsize=5.8)
    draw_box(ax, (0.66, 0.58), 0.30, 0.18, "$T_n,Q_n$", COLORS["blue"], fontsize=6.2)
    draw_box(ax, (0.66, 0.30), 0.30, 0.18, "$T_q,Q_q$", COLORS["orange"], fontsize=6.2)
    draw_box(ax, (0.66, 0.06), 0.30, 0.14, "Frontier", COLORS["green"], fontsize=6.1)
    arrow(ax, (0.22, 0.54), (0.31, 0.76), lw=0.95)
    arrow(ax, (0.22, 0.51), (0.31, 0.49), lw=0.95)
    arrow(ax, (0.22, 0.47), (0.31, 0.22), lw=0.95)
    arrow(ax, (0.56, 0.76), (0.66, 0.68), lw=0.95)
    arrow(ax, (0.56, 0.49), (0.66, 0.40), lw=0.95)
    arrow(ax, (0.81, 0.30), (0.81, 0.20), lw=0.95)
    arrow(ax, (0.42, 0.12), (0.66, 0.13), lw=0.95)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    path = os.path.join(FIG_DIR, "intro_comparison_paths.pdf")
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.05, top=0.96)
    fig.savefig(path)
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
    fig, ax = plt.subplots(figsize=(INTRO_THRESHOLD_WIDTH, 1.40))
    ax.axvspan(40, 1e3, color=COLORS["green"], alpha=0.06, linewidth=0)
    ax.axvspan(1e3, 1e5, color=COLORS["orange"], alpha=0.06, linewidth=0)
    ax.axvspan(1e5, 7e5, color=COLORS["red"], alpha=0.055, linewidth=0)
    left = 10.0
    ax.barh(y, np.array(values) - left, left=left, height=0.54, color=colors, alpha=0.20)
    ax.hlines(y, left, values, color=colors, linewidth=2.8, alpha=0.95)
    ax.scatter(values, y, s=34, color=colors, edgecolors="#222222", linewidths=0.45, zorder=3)
    for yi, value in zip(y, values):
        if value > 1e5:
            ax.text(value * 0.94, yi, "{:,.0f}x".format(value), va="center",
                    ha="right", fontsize=5.8)
        else:
            ax.text(value * 1.12, yi, "{:,.0f}x".format(value), va="center", fontsize=5.8)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Req. quantum speedup (x)", labelpad=1.0)
    ax.set_xlim(10, 7e5)
    style_axis(ax, grid="x")
    path = os.path.join(FIG_DIR, "intro_threshold_summary.pdf")
    fig.subplots_adjust(left=0.30, right=0.95, bottom=0.30, top=0.96)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
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


def figure_evaluation_evidence_flow():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.65))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    stages = [
        ("Calibrate", "160\nML cases", COLORS["blue"]),
        ("Main suite", "3,552\ncases", COLORS["green"]),
        ("Stress", "116 + 104\ncoverage", COLORS["teal"]),
        ("Scale", "16-256\nGPUs", COLORS["purple"]),
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
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.72))
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
    fig.subplots_adjust(left=0.28, right=0.98, bottom=0.17, top=0.98)
    path = os.path.join(FIG_DIR, "digits_required_speedup.pdf")
    fig.savefig(path)
    plt.close(fig)
    return path


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
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.72))
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
    fig.subplots_adjust(left=0.25, right=0.98, bottom=0.28, top=0.98)
    path = os.path.join(FIG_DIR, "digits_quality_speedup.pdf")
    fig.savefig(path)
    plt.close(fig)
    return path


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

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.62))
    colors = [COLORS["blue"], COLORS["teal"], COLORS["red"], COLORS["green"]]
    handles = []
    for label, color, initial, strong in zip(labels, colors, official_speed, strong_speed):
        line = ax.plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.9)[0]
        handles.append(line)
        ax.text(1.03, strong, label, fontsize=6.3, color=color, va="center", weight="bold")
    ax.set_yscale("log")
    ax.set_xlim(-0.12, 1.24)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Initial\nbaseline", "Strong\nbaseline"])
    ax.set_ylabel("Median\nspeedup (x)")
    style_axis(ax, grid="y")
    fig.subplots_adjust(top=0.96, bottom=0.31, left=0.38, right=0.88)
    speed_path = os.path.join(FIG_DIR, "strong_native_comparison.pdf")
    fig.savefig(speed_path)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.62))
    for label, color, initial, strong in zip(labels, colors, official_quality, strong_quality):
        ax.plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.9)
        ax.text(1.03, strong, label, fontsize=6.3, color=color, va="center", weight="bold")
    ax.set_xlim(-0.12, 1.24)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Initial\nbaseline", "Strong\nbaseline"])
    ax.set_ylabel("Median\nquality gap")
    style_axis(ax, grid="y")
    fig.subplots_adjust(bottom=0.31, left=0.38, right=0.88, top=0.96)
    quality_path = os.path.join(FIG_DIR, "strong_native_quality_shift.pdf")
    fig.savefig(quality_path)
    plt.close(fig)
    return [speed_path, quality_path]


def figure_ml_strong_native_gate():
    gate = load_summary(ML_STRONG_NATIVE_GATE_JSON)
    if gate is None:
        return None
    gate = gate.get("summary", gate)

    total_cases = int(gate.get("case_count", 32))
    combined = gate.get("combined_selected_counts", {})
    production = gate.get("production_selected_counts", {})
    previous_count = int(combined.get("previous_suite", 0))
    cnn_count = int(combined.get("torch_amp_cnn", 0))
    xgb_count = int(production.get("xgboost_gpu_hist", 0))
    mlp_count = int(production.get("torch_amp_mlp", 0))
    prod_cnn_count = int(production.get("torch_amp_cnn", 0))

    rows = [
        (
            "Combined\nselected",
            [previous_count, cnn_count],
            [COLORS["gray"], COLORS["blue"]],
            ["Previous suite", "AMP CNN"],
            gate["combined_required_speedup_median"],
        ),
        (
            "GPU prod.\nonly",
            [prod_cnn_count, xgb_count, mlp_count],
            [COLORS["blue"], COLORS["orange"], COLORS["purple"]],
            ["AMP CNN", "XGBoost", "AMP MLP"],
            gate["production_required_speedup_median"],
        ),
    ]

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.58))
    handles = {}
    y = np.arange(len(rows))
    for ridx, (row_label, counts, colors, names, speedup) in enumerate(rows):
        left = 0.0
        for count, color, name in zip(counts, colors, names):
            width = 100.0 * count / float(total_cases)
            bar = ax.barh(ridx, width, left=left, height=0.50, color=color)
            handles.setdefault(name, bar[0])
            if width >= 14.0:
                ax.text(
                    left + width / 2.0,
                    ridx,
                    "{:d}/{}".format(count, total_cases),
                    ha="center",
                    va="center",
                    fontsize=6.0,
                    color="white" if color in {COLORS["gray"], COLORS["blue"], COLORS["purple"]} else "black",
                    weight="bold",
                )
            left += width
        ax.text(
            100.0,
            ridx,
            " {:,.0f}x".format(speedup),
            va="center",
            ha="left",
            fontsize=6.1,
            color=COLORS["dark"],
        )
    ax.set_yticks(y)
    ax.set_yticklabels([row[0] for row in rows])
    ax.set_xlim(0, 128)
    ax.set_xlabel("Selected baseline share (%)")
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0", "50", "100"])
    ax.invert_yaxis()
    style_axis(ax, grid="x")
    legend_order = ["Previous suite", "AMP CNN", "XGBoost", "AMP MLP"]
    add_top_legend(fig, [handles[name] for name in legend_order if name in handles],
                   [name for name in legend_order if name in handles], ncol=2, y=1.02, fontsize=5.2)
    fig.subplots_adjust(left=0.36, right=0.83, bottom=0.29, top=0.68)
    path = os.path.join(FIG_DIR, "ml_strong_native_gate.pdf")
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_ml_profile_breakdown():
    profile = load_summary(ML_STRONG_NATIVE_PROFILE_JSON)
    if profile is None:
        return None

    nsys = profile.get("nsys_kernel_summary", {})
    dmon = profile.get("dmon_summary", {})
    gpu_frac = float(nsys.get("gpu_kernel_runtime_fraction") or 0.0)
    host_frac = max(0.0, 1.0 - gpu_frac)
    tensor_frac = float(nsys.get("tensor_kernel_time_fraction") or 0.0)
    other_kernel_frac = max(0.0, 1.0 - tensor_frac)
    rows = [
        ("Gate\nruntime", [host_frac, gpu_frac], [COLORS["gray"], COLORS["green"]], ["Host/orch.", "GPU kernels"]),
        ("GPU\nkernels", [other_kernel_frac, tensor_frac], [COLORS["green"], COLORS["orange"]], ["Other", "Tensor fam."]),
    ]

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.58))
    y = np.arange(len(rows))
    legend_handles = []
    legend_labels = []
    for ridx, (label, values, colors, names) in enumerate(rows):
        left = 0.0
        for value, color, name in zip(values, colors, names):
            bar = ax.barh(ridx, value * 100.0, left=left * 100.0, height=0.52, color=color)
            if name not in legend_labels:
                legend_handles.append(bar[0])
                legend_labels.append(name)
            if value >= 0.06:
                ax.text(
                    (left + value / 2.0) * 100.0,
                    ridx,
                    "{:.0f}%".format(value * 100.0),
                    ha="center",
                    va="center",
                    fontsize=5.8,
                    color="white" if color in {COLORS["gray"], COLORS["green"]} else "black",
                )
            left += value
    if gpu_frac > 0:
        ax.text(
            max(98.0, host_frac * 100.0),
            0,
            "{:.1f}%".format(gpu_frac * 100.0),
            ha="right",
            va="center",
            fontsize=5.5,
            color=COLORS["dark"],
        )
    sm_note = "SM avg {:.1f}%, max {:.0f}%".format(
        float(dmon.get("sm_avg_pct") or 0.0),
        float(dmon.get("sm_max_pct") or 0.0),
    )
    ax.text(0.01, 1.04, sm_note, transform=ax.transAxes, fontsize=5.5, color=COLORS["dark"])
    ax.set_yticks(y)
    ax.set_yticklabels([row[0] for row in rows])
    ax.set_xlim(0, 103)
    ax.set_xlabel("Time fraction (%)")
    style_axis(ax, grid="x")
    add_top_legend(fig, legend_handles, legend_labels, ncol=2, y=1.02, fontsize=5.2)
    fig.subplots_adjust(left=0.36, right=0.95, bottom=0.29, top=0.68)
    path = os.path.join(FIG_DIR, "ml_profile_breakdown.pdf")
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_ml_native_profile_combined():
    gate = load_summary(ML_STRONG_NATIVE_GATE_JSON)
    profile = load_summary(ML_STRONG_NATIVE_PROFILE_JSON)
    if gate is None or profile is None:
        return None
    gate = gate.get("summary", gate)

    total_cases = int(gate.get("case_count", 32))
    combined = gate.get("combined_selected_counts", {})
    production = gate.get("production_selected_counts", {})
    previous_count = int(combined.get("previous_suite", 0))
    cnn_count = int(combined.get("torch_amp_cnn", 0))
    xgb_count = int(production.get("xgboost_gpu_hist", 0))
    mlp_count = int(production.get("torch_amp_mlp", 0))
    prod_cnn_count = int(production.get("torch_amp_cnn", 0))

    nsys = profile.get("nsys_kernel_summary", {})
    dmon = profile.get("dmon_summary", {})
    gpu_frac = float(nsys.get("gpu_kernel_runtime_fraction") or 0.0)
    host_frac = max(0.0, 1.0 - gpu_frac)
    tensor_frac = float(nsys.get("tensor_kernel_time_fraction") or 0.0)
    other_kernel_frac = max(0.0, 1.0 - tensor_frac)

    fig, axes = plt.subplots(1, 2, figsize=(COLUMN_WIDTH, 1.98), gridspec_kw={"wspace": 0.52})
    ax = axes[0]
    rows = [
        (
            "Combined\nselected",
            [previous_count, cnn_count],
            [COLORS["gray"], COLORS["blue"]],
            ["Previous", "AMP CNN"],
            gate["combined_required_speedup_median"],
        ),
        (
            "GPU prod.\nonly",
            [prod_cnn_count, xgb_count, mlp_count],
            [COLORS["blue"], COLORS["orange"], COLORS["purple"]],
            ["AMP CNN", "XGBoost", "AMP MLP"],
            gate["production_required_speedup_median"],
        ),
    ]
    handles = {}
    for ridx, (row_label, counts, colors, names, speedup) in enumerate(rows):
        left = 0.0
        for count, color, name in zip(counts, colors, names):
            width = 100.0 * count / float(total_cases)
            bar = ax.barh(ridx, width, left=left, height=0.52, color=color)
            handles.setdefault(name, bar[0])
            if width >= 18.0:
                ax.text(
                    left + width / 2.0,
                    ridx,
                    "{:d}/{}".format(count, total_cases),
                    ha="center",
                    va="center",
                    fontsize=5.9,
                    color="white" if color in {COLORS["gray"], COLORS["blue"], COLORS["purple"]} else "black",
                    weight="bold",
                )
            left += width
        ax.text(104.0, ridx, "{:,.0f}x".format(speedup), va="center", fontsize=5.7)
    ax.set_yticks(np.arange(len(rows)))
    ax.set_yticklabels([row[0] for row in rows])
    ax.set_xlim(0, 132)
    ax.set_xlabel("Selected baseline share (%)")
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0", "50", "100"])
    ax.invert_yaxis()
    style_axis(ax, grid="x")

    ax = axes[1]
    profile_rows = [
        ("Gate\nruntime", [host_frac, gpu_frac], [COLORS["gray"], COLORS["green"]], ["Host/orch.", "GPU kernels"]),
        ("GPU\nkernels", [other_kernel_frac, tensor_frac], [COLORS["green"], COLORS["orange"]], ["Other", "Tensor fam."]),
    ]
    profile_handles = {}
    for ridx, (label, values, colors, names) in enumerate(profile_rows):
        left = 0.0
        for value, color, name in zip(values, colors, names):
            bar = ax.barh(ridx, value * 100.0, left=left * 100.0, height=0.52, color=color)
            profile_handles.setdefault(name, bar[0])
            if value >= 0.07:
                ax.text(
                    (left + value / 2.0) * 100.0,
                    ridx,
                    "{:.0f}%".format(value * 100.0),
                    ha="center",
                    va="center",
                    fontsize=5.9,
                    color="white" if color in {COLORS["gray"], COLORS["green"]} else "black",
                    weight="bold" if color in {COLORS["gray"], COLORS["green"]} else "normal",
                )
            left += value
    if gpu_frac > 0:
        ax.text(98.5, 0, "{:.1f}%".format(gpu_frac * 100.0), ha="right", va="center",
                fontsize=5.4, color=COLORS["dark"])
    ax.text(
        0.02,
        1.03,
        "SM avg {:.1f}%, max {:.0f}%".format(
            float(dmon.get("sm_avg_pct") or 0.0),
            float(dmon.get("sm_max_pct") or 0.0),
        ),
        transform=ax.transAxes,
        fontsize=5.6,
        color=COLORS["dark"],
    )
    ax.set_yticks(np.arange(len(profile_rows)))
    ax.set_yticklabels([row[0] for row in profile_rows])
    ax.set_xlim(0, 103)
    ax.set_xlabel("Time fraction (%)")
    style_axis(ax, grid="x")

    legend_handles = [
        handles.get("Previous"),
        handles.get("AMP CNN"),
        handles.get("XGBoost"),
        handles.get("AMP MLP"),
        profile_handles.get("Host/orch."),
        profile_handles.get("GPU kernels"),
        profile_handles.get("Tensor fam."),
    ]
    legend_labels = [
        "Prev.",
        "CNN",
        "XGB",
        "MLP",
        "Host",
        "GPU",
        "Tensor",
    ]
    pairs = [(h, l) for h, l in zip(legend_handles, legend_labels) if h is not None]
    fig.legend(
        [h for h, _ in pairs],
        [l for _, l in pairs],
        ncol=7,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.01),
        frameon=False,
        fontsize=4.9,
        handlelength=0.95,
        handletextpad=0.20,
        columnspacing=0.42,
    )
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.23, top=0.76, wspace=0.52)
    path = os.path.join(FIG_DIR, "ml_native_profile_combined.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_workload_growth():
    if not (
        os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_CSV))
        and os.path.exists(os.path.join(ROOT, STRONG_NATIVE_64_SUMMARY_CSV))
    ):
        return None

    points = [
        ("128 GPUs\n3,552 cases", 128, 3552, 257, STRONG_NATIVE_SUMMARY_CSV),
        ("256 GPUs\n7,104 cases", 256, 7104, 514, STRONG_NATIVE_64_SUMMARY_CSV),
    ]

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.78))
    cases = np.array([point[2] for point in points], dtype=float)
    elapsed = np.array([point[3] for point in points], dtype=float)
    x = np.arange(len(points))
    bars = ax.bar(x, cases / 1000.0, color=[COLORS["blue"], COLORS["teal"]], width=0.52, alpha=0.86)
    for xpos, bar, tval in zip(x, bars, elapsed):
        ax.text(
            xpos,
            bar.get_height() + 0.22,
            "{:.1f}K\n{}s".format(bar.get_height(), int(tval)),
            ha="center",
            va="bottom",
            fontsize=5.8,
            linespacing=1.0,
        )
    ax.plot(x, (cases / 1000.0)[0] * (elapsed / elapsed[0]), linestyle="--",
            color=COLORS["gray"], linewidth=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(["128 GPUs", "256 GPUs"])
    ax.set_ylabel("Completed cases (K)")
    ax.set_ylim(0, 8.5)
    style_axis(ax, grid="y")
    fig.subplots_adjust(left=0.27, right=0.98, bottom=0.25, top=0.90)
    time_path = os.path.join(FIG_DIR, "workload_growth_time.pdf")
    fig.savefig(time_path)
    plt.close(fig)

    workloads = [
        ("ml", "ML", COLORS["blue"]),
        ("chemistry", "Chem.", COLORS["teal"]),
        ("optimization", "Opt.", COLORS["red"]),
        ("simulation", "Sim.", COLORS["green"]),
    ]
    rows_by_run = [read_csv(points[0][4]), read_csv(points[1][4])]
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.78))
    handles = []
    legend_labels = []
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
        line = ax.plot(x, medians, marker="o", color=color, linewidth=1.55)[0]
        handles.append(line)
        legend_labels.append(label)
    ax.set_xticks(x)
    ax.set_xticklabels(["128\nGPUs", "256\nGPUs"])
    ax.set_ylabel("Median\nquality gap")
    ax.set_ylim(0.0, 0.34)
    ax.set_yticks([0.0, 0.1, 0.2, 0.3])
    ax.set_xlim(-0.14, 1.14)
    style_axis(ax, grid="y")
    add_top_legend(fig, handles, legend_labels, ncol=4, y=0.99, fontsize=4.9)
    fig.subplots_adjust(left=0.27, right=0.98, bottom=0.31, top=0.74)
    quality_path = os.path.join(FIG_DIR, "workload_growth_quality.pdf")
    fig.savefig(quality_path)
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

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.84))
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
    ax.set_xlabel("Operation share")
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xticklabels(["0", "50%", "100%"])
    style_axis(ax, grid="x")
    add_top_legend(fig, handles, labels, ncol=3, y=1.03, fontsize=5.5)
    fig.subplots_adjust(left=0.25, right=0.98, bottom=0.24, top=0.70)
    path = os.path.join(FIG_DIR, "circuit_operation_mix.pdf")
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_threshold_tail_pressure():
    if not os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_CSV)):
        return None

    rows = read_csv(STRONG_NATIVE_SUMMARY_CSV)
    workloads = [
        ("ml", "ML", COLORS["blue"]),
        ("chemistry", "Chem.", COLORS["teal"]),
        ("optimization", "Opt.", COLORS["red"]),
        ("simulation", "Sim.", COLORS["green"]),
    ]

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.84))
    y = np.arange(len(workloads))
    for ypos, (workload, label, color) in zip(y, workloads):
        subset = [row for row in rows if row["workload"] == workload]
        speed = np.array([float(row["speedup_required"]) for row in subset])
        p50, p90, pmax = np.percentile(speed, [50, 90, 100])
        ax.hlines(ypos, p50, pmax, color=color, linewidth=1.4, alpha=0.55)
        ax.scatter([p50, p90, pmax], [ypos] * 3, s=[18, 24, 30], color=color,
                   edgecolors="#222222", linewidths=0.35, zorder=3)
        ax.text(pmax * 1.04, ypos, label, va="center", fontsize=6.1,
                color=color, weight="bold")
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(["", "", "", ""])
    ax.set_xlabel("Required speedup tail (x)")
    ax.set_xlim(1e3, 6.5e5)
    ax.invert_yaxis()
    style_axis(ax, grid="x")
    ax.text(0.05, 1.05, "dot: median / p90 / max", transform=ax.transAxes,
            fontsize=5.6, color=COLORS["dark"])
    fig.subplots_adjust(left=0.18, right=0.88, bottom=0.24, top=0.86)
    path = os.path.join(FIG_DIR, "threshold_tail_pressure.pdf")
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_tolerance_sensitivity():
    if not os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_CSV)):
        return None

    rows = read_csv(STRONG_NATIVE_SUMMARY_CSV)
    workload_specs = [
        ("ml", "ML $10^5$x", COLORS["blue"], 1.0e5, 0.02),
        ("chemistry", "Chem. $10^5$x", COLORS["teal"], 1.0e5, 0.01),
        ("optimization", "Opt. $10^6$x", COLORS["red"], 1.0e6, 0.02),
        ("simulation", "Sim. $10^4$x", COLORS["green"], 1.0e4, 0.01),
    ]
    multipliers = np.array([0.5, 1.0, 2.0, 5.0], dtype=float)
    recovery = 0.90

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.92))
    handles = []
    labels = []
    for workload, label, color, speedup, base_tol in workload_specs:
        subset = [row for row in rows if row["workload"] == workload]
        required = np.array([float(row["speedup_required"]) for row in subset])
        gaps = np.array([max(0.0, float(row["quality_gap"])) for row in subset])
        values = []
        for multiplier in multipliers:
            tolerance = base_tol * multiplier
            advantaged = (speedup >= required) & (gaps * (1.0 - recovery) <= tolerance)
            values.append(100.0 * float(np.mean(advantaged)) if advantaged.size else 0.0)
        line = ax.plot(
            multipliers,
            values,
            marker="o",
            linewidth=1.6,
            markersize=3.6,
            color=color,
        )[0]
        handles.append(line)
        labels.append(label)

    ax.set_xticks(multipliers)
    ax.set_xticklabels(["0.5x", "1x", "2x", "5x"])
    ax.set_xlim(0.35, 5.15)
    ax.set_ylim(-3, 103)
    ax.set_xlabel("Tolerance multiplier")
    ax.set_ylabel("Cases advantaged\nat 90% recovery (%)")
    style_axis(ax, grid="both")
    add_top_legend(fig, handles, labels, ncol=4, y=1.02, fontsize=5.7)
    fig.subplots_adjust(left=0.20, right=0.98, bottom=0.26, top=0.78)
    path = os.path.join(FIG_DIR, "tolerance_sensitivity.pdf")
    fig.savefig(path)
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

    gpus = np.array([run["gpus"] for run in runs], dtype=float)
    cases = np.array([run["cases"] for run in runs], dtype=float)
    elapsed = np.array([run["elapsed_sec"] for run in runs], dtype=float)
    throughput = cases / elapsed
    ideal = throughput[0] * (gpus / gpus[0])
    per_gpu = cases / (elapsed * gpus)
    efficiency = per_gpu / per_gpu[0]
    gpu_ticks = [1, 4, 16, 64, 256]

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.92))
    line_measured = ax.plot(gpus, throughput, marker="o", color=COLORS["blue"], label="measured")[0]
    line_ideal = ax.plot(gpus, ideal, linestyle="--", color=COLORS["gray"], label="ideal linear")[0]
    ax.set_xscale("log", base=2)
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels([str(tick) for tick in gpu_ticks])
    ax.set_xlabel("GPUs")
    ax.set_ylabel("Throughput\n(cases/s)")
    style_axis(ax, grid="both")
    ax.set_xlim(0.8, 330)
    add_top_legend(fig, [line_measured, line_ideal], ["measured", "ideal"], ncol=2, y=1.00, fontsize=5.2)
    fig.subplots_adjust(top=0.77, bottom=0.28, left=0.29, right=0.98)
    throughput_path = os.path.join(FIG_DIR, "weak_scaling.pdf")
    fig.savefig(throughput_path)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.92))
    line_eff = ax.plot(
        gpus,
        efficiency,
        marker="s",
        color=COLORS["orange"],
        label="per-GPU throughput",
    )[0]
    line_ref = ax.axhline(1.0, linestyle="--", color=COLORS["gray"], linewidth=1.0)
    ax.set_xscale("log", base=2)
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels([str(tick) for tick in gpu_ticks])
    ax.set_xlabel("GPUs")
    ax.set_ylabel("Norm. per-GPU\nthroughput")
    ax.set_ylim(0.82, 1.08)
    style_axis(ax, grid="both")
    ax.set_xlim(0.8, 330)
    add_top_legend(fig, [line_eff, line_ref], ["per-GPU", "reference"], ncol=2, y=1.00, fontsize=5.2)
    fig.subplots_adjust(top=0.77, bottom=0.28, left=0.31, right=0.98)
    efficiency_path = os.path.join(FIG_DIR, "weak_scaling_efficiency.pdf")
    fig.savefig(efficiency_path)
    plt.close(fig)
    return [throughput_path, efficiency_path]


def figure_strong_scaling():
    runs = [run for run in STRONG_SCALING_RUNS if load_summary(run["summary"]) is not None]
    if len(runs) < 2:
        return None

    nodes = np.array([run["nodes"] for run in runs], dtype=float)
    gpus = np.array([run["gpus"] for run in runs], dtype=float)
    elapsed = np.array([run["elapsed_sec"] for run in runs], dtype=float)
    speedup = elapsed[0] / elapsed
    ideal = nodes / nodes[0]
    efficiency = speedup / ideal
    gpu_ticks = [1, 4, 16, 64, 256]

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.94))
    line_time = ax.plot(gpus, elapsed / 60.0, marker="o", color=COLORS["blue"], label="measured")[0]
    line_time_ideal = ax.plot(
        gpus,
        (elapsed[0] / ideal) / 60.0,
        linestyle="--",
        color=COLORS["gray"],
        label="ideal linear",
    )[0]
    ax.set_xscale("log", base=2)
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels([str(tick) for tick in gpu_ticks])
    ax.set_ylabel("Elapsed\n(min)")
    ax.set_xlabel("GPUs")
    style_axis(ax, grid="both")
    ax.set_xlim(0.8, 330)
    add_top_legend(fig, [line_time, line_time_ideal], ["measured", "ideal"], ncol=2, y=1.00, fontsize=5.2)
    fig.subplots_adjust(top=0.77, bottom=0.27, left=0.29, right=0.98)
    elapsed_path = os.path.join(FIG_DIR, "strong_scaling.pdf")
    fig.savefig(elapsed_path)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.94))
    line_speed = ax.plot(gpus, speedup, marker="o", color=COLORS["green"], label="measured")[0]
    line_speed_ideal = ax.plot(gpus, ideal, linestyle="--", color=COLORS["gray"], label="ideal linear")[0]
    ax.set_xscale("log", base=2)
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels([str(tick) for tick in gpu_ticks])
    ax.set_xlabel("GPUs")
    ax.set_ylabel("Speedup\nvs. 16 GPUs")
    style_axis(ax, grid="both")
    ax.set_xlim(0.8, 330)
    add_top_legend(fig, [line_speed, line_speed_ideal], ["measured", "ideal"], ncol=2, y=1.00, fontsize=5.2)
    fig.subplots_adjust(top=0.77, bottom=0.28, left=0.27, right=0.98)
    speedup_path = os.path.join(FIG_DIR, "strong_scaling_speedup.pdf")
    fig.savefig(speedup_path)
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
    time_ticks = [4, 5, 6]
    time_tick_labels = ["0.7 ms", "70 us", "7 us"]

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
        fig, ax = plt.subplots(figsize=(TEXT_WIDTH * 0.48, 2.05))
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
            fontsize=6.6,
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
            top_margin = 0.98
        else:
            ax.tick_params(axis="x", labelbottom=False)
            top = ax.secondary_xaxis("top")
            top_ticks = [tick for tick in time_ticks if tick <= max_power]
            top.set_xticks(top_ticks)
            top.set_xticklabels(time_tick_labels[: len(top_ticks)])
            top.set_xlabel("")
            top.tick_params(axis="x", labelsize=6.0, pad=0.8, width=0.6)
            top_margin = 0.86
        ax.tick_params(axis="both", labelsize=6.5, pad=1.0)
        cbar = fig.colorbar(image, ax=ax, shrink=0.88, pad=0.018)
        cbar.set_ticks([0.0, 0.5, 1.0])
        cbar.ax.tick_params(labelsize=6.3, pad=1.0)
        fig.subplots_adjust(left=0.22, right=0.86, bottom=0.25, top=top_margin)
        suffix = "ml" if workload == "ml" else workload
        filename = (
            "advantage_frontier.pdf"
            if workload == "ml"
            else "advantage_frontier_{}.pdf".format(suffix)
        )
        panel_path = os.path.join(FIG_DIR, filename)
        fig.savefig(panel_path)
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

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.72))
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
        legend_labels.append(
            {
                "quality-limited": "Quality",
                "speed-limited": "Speed",
                "shot-limited": "Shot",
                "encoding-limited": "Encoding",
                "native-dominated": "Native",
            }[label]
        )
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
    add_top_legend(fig, legend_handles, legend_labels, ncol=5, y=1.00, fontsize=5.4)
    fig.subplots_adjust(top=0.70, bottom=0.19, left=0.22, right=0.98)
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
        figure_evaluation_evidence_flow(),
        figure_digits_legend(),
        figure_digits_speedup(),
        figure_digits_quality_runtime(),
        figure_practical_suite_legend(),
        figure_practical_suite(),
        figure_strong_native_comparison(),
        figure_ml_strong_native_gate(),
        figure_ml_profile_breakdown(),
        figure_ml_native_profile_combined(),
        figure_threshold_tail_pressure(),
        figure_circuit_operation_mix(),
        figure_workload_growth(),
        figure_advantage_frontier(),
        figure_tolerance_sensitivity(),
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
