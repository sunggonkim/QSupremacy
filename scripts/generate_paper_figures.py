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
INTRO_PATH_WIDTH = COLUMN_WIDTH * 0.46
INTRO_THRESHOLD_WIDTH = COLUMN_WIDTH * 0.92
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
ONE_GPU_PILOT_SUMMARY_JSON = (
    "data/processed/perlmutter/practical_suite_55453128_55453131_summary.json"
)
ML_STRONG_NATIVE_GATE_JSON = (
    "data/processed/perlmutter/ml_strong_native_gate_latest.json"
)
ML_STRONG_NATIVE_PROFILE_JSON = (
    "data/processed/perlmutter/ml_strong_native_profile_latest.json"
)
PROJECTION_SCENARIOS_JSON = (
    "data/processed/perlmutter/practical_suite_projection_scenarios.json"
)
SCALE_LARGE_8_SUMMARY_JSON = (
    "data/processed/perlmutter/practical_suite_55730074_scale_8n_32g_summary.json"
)
SCALE_LARGE_8_SUMMARY_CSV = (
    "data/processed/perlmutter/practical_suite_55730074_scale_8n_32g_summary.csv"
)
SCALE_WEAK_16_SUMMARY_JSON = (
    "data/processed/perlmutter/practical_suite_55731013_scale_16n_64g_summary.json"
)
SCALE_WEAK_16_SUMMARY_CSV = (
    "data/processed/perlmutter/practical_suite_55731013_scale_16n_64g_summary.csv"
)
SCALE_WEAK_32_SUMMARY_JSON = (
    "data/processed/perlmutter/practical_suite_55731014_scale_32n_128g_summary.json"
)
SCALE_WEAK_32_SUMMARY_CSV = (
    "data/processed/perlmutter/practical_suite_55731014_scale_32n_128g_summary.csv"
)
SCALE_WEAK_64_SUMMARY_JSON = (
    "data/processed/perlmutter/practical_suite_55731015_scale_64n_256g_summary.json"
)
SCALE_WEAK_64_SUMMARY_CSV = (
    "data/processed/perlmutter/practical_suite_55731015_scale_64n_256g_summary.csv"
)
SCALE_STRONG_16_SUMMARY_JSON = (
    "data/processed/perlmutter/practical_suite_55731032_scale_16n_64g_summary.json"
)
SCALE_STRONG_32_SUMMARY_JSON = (
    "data/processed/perlmutter/practical_suite_55731033_scale_32n_128g_summary.json"
)
SCALE_STRONG_64_SUMMARY_JSON = (
    "data/processed/perlmutter/practical_suite_55731034_scale_64n_256g_summary.json"
)

WEAK_SCALING_RUNS = [
    {
        "label": "1 GPU pilot",
        "nodes": 0.25,
        "gpus": 1,
        "cases": 190,
        "elapsed_sec": 1702,
        "summary": ONE_GPU_PILOT_SUMMARY_JSON,
        "kind": "pilot",
    },
    {
        "label": "1 node pilot",
        "nodes": 1,
        "gpus": 4,
        "cases": 190,
        "elapsed_sec": 419,
        "summary": STRONG_NATIVE_1NODE_SUMMARY_JSON,
        "kind": "pilot",
    },
    {
        "label": "2 nodes",
        "nodes": 2,
        "gpus": 8,
        "cases": 224,
        "elapsed_sec": 262,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongnative_2node_large128c0c7_fix_20260704022146_summary.json"
        ),
        "kind": "pilot",
    },
    {
        "label": "4 nodes",
        "nodes": 4,
        "gpus": 16,
        "cases": 448,
        "elapsed_sec": 278,
        "summary": (
            "data/processed/perlmutter/"
            "practical_suite_strongnative_4node_large128c0c15_20260704024223_summary.json"
        ),
        "kind": "pilot",
    },
    {
        "label": "8 nodes",
        "nodes": 8,
        "gpus": 32,
        "cases": 888,
        "elapsed_sec": 765,
        "summary": SCALE_LARGE_8_SUMMARY_JSON,
        "kind": "pilot",
    },
    {
        "label": "16 nodes",
        "nodes": 16,
        "gpus": 64,
        "cases": 1776,
        "elapsed_sec": 562,
        "summary": SCALE_WEAK_16_SUMMARY_JSON,
        "kind": "weak",
    },
    {
        "label": "32 nodes",
        "nodes": 32,
        "gpus": 128,
        "cases": 3552,
        "elapsed_sec": 419,
        "summary": SCALE_WEAK_32_SUMMARY_JSON,
        "kind": "weak",
    },
    {
        "label": "64 nodes",
        "nodes": 64,
        "gpus": 256,
        "cases": 7104,
        "elapsed_sec": 576,
        "summary": SCALE_WEAK_64_SUMMARY_JSON,
        "kind": "weak",
    },
]

STRONG_SCALING_RUNS = [
    {
        "label": "1 GPU pilot",
        "nodes": 0.25,
        "gpus": 1,
        "cases": 190,
        "elapsed_sec": 1702,
        "summary": ONE_GPU_PILOT_SUMMARY_JSON,
        "kind": "normalized",
    },
    {
        "label": "1 node pilot",
        "nodes": 1,
        "gpus": 4,
        "cases": 190,
        "elapsed_sec": 419,
        "summary": STRONG_NATIVE_1NODE_SUMMARY_JSON,
        "kind": "normalized",
    },
    {
        "label": "16 nodes",
        "nodes": 16,
        "gpus": 64,
        "cases": 7104,
        "elapsed_sec": 1713,
        "summary": SCALE_STRONG_16_SUMMARY_JSON,
        "kind": "fixed",
    },
    {
        "label": "32 nodes",
        "nodes": 32,
        "gpus": 128,
        "cases": 7104,
        "elapsed_sec": 954,
        "summary": SCALE_STRONG_32_SUMMARY_JSON,
        "kind": "fixed",
    },
    {
        "label": "64 nodes",
        "nodes": 64,
        "gpus": 256,
        "cases": 7104,
        "elapsed_sec": 418,
        "summary": SCALE_STRONG_64_SUMMARY_JSON,
        "kind": "fixed",
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


def save_canvas(fig, path):
    with plt.rc_context({"savefig.bbox": "standard"}):
        fig.savefig(path)
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
    rows = [
        ("ML", "native\nmodels", "QKernel\nQNN/VQC\nfeature", COLORS["blue"], COLORS["orange"]),
        ("Chem.", "exact\nLanczos", "VQE", COLORS["teal"], COLORS["teal"]),
        ("Opt.", "exact\nheur.", "QAOA", COLORS["red"], COLORS["red"]),
        ("Sim.", "dense\nKrylov", "Trotter", COLORS["green"], COLORS["green"]),
    ]
    y_positions = [0.80, 0.60, 0.40, 0.20]
    for (family, native, circuit, native_color, circuit_color), y0 in zip(rows, y_positions):
        draw_box(ax, (0.02, y0 - 0.06), 0.18, 0.12, family, COLORS["dark"], fontsize=6.1)
        draw_box(ax, (0.29, y0 - 0.065), 0.29, 0.13, native, native_color, fontsize=5.6)
        draw_box(ax, (0.68, y0 - 0.065), 0.29, 0.13, circuit, circuit_color, fontsize=5.45)
        arrow(ax, (0.20, y0), (0.29, y0), lw=0.75)
        arrow(ax, (0.58, y0), (0.68, y0), lw=0.75)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    path = os.path.join(FIG_DIR, "intro_comparison_paths.pdf")
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.05, top=0.96)
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_intro_threshold_summary():
    labels = [
        "ML\nscikit/QNN",
        "ML\nscikit/QKernel",
        "Sim.\nKrylov/Trotter",
        "ML\nscikit/QFeature",
        "Chem.\nLanczos/VQE",
        "Opt.\nheuristic/QAOA",
    ]
    values = [64.9, 421.9, 3071.0, 3726.4, 42491.4, 287045.6]
    colors = [
        COLORS["orange"],
        COLORS["blue"],
        COLORS["green"],
        COLORS["blue"],
        COLORS["teal"],
        COLORS["red"],
    ]
    y = np.arange(len(labels)) * 1.28
    fig, ax = plt.subplots(figsize=(INTRO_THRESHOLD_WIDTH, 1.72))
    ax.axvspan(40, 1e3, color=COLORS["green"], alpha=0.06, linewidth=0)
    ax.axvspan(1e3, 1e5, color=COLORS["orange"], alpha=0.06, linewidth=0)
    ax.axvspan(1e5, 7e5, color=COLORS["red"], alpha=0.055, linewidth=0)
    left = 10.0
    ax.barh(y, np.array(values) - left, left=left, height=0.50, color=colors, alpha=0.20)
    ax.hlines(y, left, values, color=colors, linewidth=2.8, alpha=0.95)
    ax.scatter(values, y, s=30, color=colors, edgecolors="#222222", linewidths=0.45, zorder=3)
    for yi, value in zip(y, values):
        ax.annotate(
            "{:,.0f}x".format(value),
            xy=(value, yi),
            xytext=(7, 0),
            textcoords="offset points",
            va="center",
            ha="left",
            fontsize=5.2,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 0.2},
        )
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.tick_params(axis="y", labelsize=5.25)
    for tick in ax.get_yticklabels():
        tick.set_linespacing(1.02)
    ax.invert_yaxis()
    ax.set_xlabel("Req. speedup over native (x)", labelpad=1.0)
    ax.set_xlim(10, 1.05e6)
    style_axis(ax, grid="x")
    path = os.path.join(FIG_DIR, "intro_threshold_summary.pdf")
    fig.subplots_adjust(left=0.32, right=0.94, bottom=0.26, top=0.98)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_design_overview():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 3.25))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def step_badge(x, y, text):
        circle = plt.Circle((x, y), 0.025, facecolor="white", edgecolor=COLORS["dark"], linewidth=0.8, zorder=4)
        ax.add_patch(circle)
        ax.text(x, y - 0.001, text, ha="center", va="center", fontsize=5.5, weight="bold", color=COLORS["dark"], zorder=5)

    ax.text(0.04, 0.955, "QArchGauge procedure", fontsize=7.4, weight="bold", color=COLORS["dark"])
    ax.text(0.04, 0.905, "same input, native deadline, quantum circuit metadata, and projection knobs stay in one case record",
            fontsize=4.9, color=COLORS["dark"])

    draw_box(ax, (0.06, 0.77), 0.88, 0.09, "1. Shared application case: input, seed, quality metric, tolerance", COLORS["dark"], fontsize=5.5)
    step_badge(0.075, 0.86, "1")

    draw_box(ax, (0.07, 0.60), 0.34, 0.105, "2. Native HPC path\n$T_{native}, Q_{native}$\nexact / Krylov / heur.", COLORS["blue"], fontsize=5.0)
    draw_box(ax, (0.59, 0.60), 0.34, 0.105, "3. Quantum-circuit path\n$T_{qsim}, Q_q$\nVQE / QAOA / Trotter", COLORS["orange"], fontsize=5.0)
    step_badge(0.085, 0.705, "2")
    step_badge(0.605, 0.705, "3")
    arrow(ax, (0.28, 0.77), (0.24, 0.705), lw=0.9)
    arrow(ax, (0.72, 0.77), (0.76, 0.705), lw=0.9)

    draw_box(ax, (0.20, 0.43), 0.60, 0.105, "4. Auditable case record\nruntime, quality gap,\ngates, shots, evals", COLORS["teal"], fontsize=5.0)
    step_badge(0.255, 0.535, "4")
    arrow(ax, (0.24, 0.60), (0.38, 0.535), lw=0.9)
    arrow(ax, (0.76, 0.60), (0.62, 0.535), lw=0.9)

    levers = [
        ("Logical ops\n$t_1,t_2,t_m$", COLORS["green"], 0.07),
        ("Shot lanes\n$P_{shots}$", COLORS["purple"], 0.295),
        ("Decode/control\n$T_{err}$", COLORS["red"], 0.52),
        ("Quality recovery\n$R_q$", COLORS["gray"], 0.745),
    ]
    for label, color, x in levers:
        draw_box(ax, (x, 0.25), 0.19, 0.08, label, color, fontsize=4.9)
        arrow(ax, (0.50, 0.43), (x + 0.095, 0.33), lw=0.75)

    draw_box(ax, (0.13, 0.08), 0.31, 0.085, "Runtime gate\n$T_{qhw}<T_{native}$", "#F3F3F3", text_color=COLORS["dark"], fontsize=5.0)
    draw_box(ax, (0.56, 0.08), 0.31, 0.085, "Target map\namount + location", "#F3F3F3", text_color=COLORS["dark"], fontsize=5.0)
    step_badge(0.145, 0.165, "5")
    arrow(ax, (0.25, 0.25), (0.28, 0.165), lw=0.75)
    arrow(ax, (0.74, 0.25), (0.72, 0.165), lw=0.75)
    arrow(ax, (0.44, 0.122), (0.56, 0.122), lw=0.85)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    path = os.path.join(FIG_DIR, "design_overview.pdf")
    fig.subplots_adjust(left=0.02, right=0.985, bottom=0.04, top=0.97)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_design_projection_flow():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.12))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.035, 0.93, "Projection equation", fontsize=7.1, weight="bold", color=COLORS["dark"])
    ax.text(0.035, 0.875, "recorded circuit metadata is priced by explicit hardware terms", fontsize=5.0, color=COLORS["dark"])

    draw_box(ax, (0.045, 0.70), 0.20, 0.10, "case record\n$D_1,D_2,D_m,N_e$", COLORS["teal"], fontsize=5.3)
    draw_box(ax, (0.045, 0.50), 0.20, 0.10, "native deadline\n$T_{native}$", COLORS["blue"], fontsize=5.3)
    draw_box(ax, (0.045, 0.30), 0.20, 0.10, "quality gap\n$\\Delta Q,\\epsilon_w$", COLORS["purple"], fontsize=5.3)

    term_specs = [
        ("logical ops\n$N_e(D_1t_1+D_2t_2+D_mt_m)/P_{shots}$", COLORS["green"], 0.46, 0.66),
        ("serial floor\n$N_e(T_{decode}+T_{ctrl}+T_{io})$", COLORS["red"], 0.46, 0.46),
        ("quality gate\n$(1-R_q)\\Delta Q\\leq\\epsilon_w$", COLORS["gray"], 0.46, 0.26),
    ]
    for label, color, x, y in term_specs:
        draw_box(ax, (x, y), 0.47, 0.105, label, color, fontsize=4.9)
    for y in [0.75, 0.55, 0.35]:
        arrow(ax, (0.245, y), (0.46, y - 0.03), lw=0.85)

    draw_box(ax, (0.31, 0.08), 0.23, 0.095, "frontier\nspeed + $R_q$", "#F4F4F4", text_color=COLORS["dark"], fontsize=5.1)
    draw_box(ax, (0.62, 0.08), 0.32, 0.095, "target map\nspeed / shots /\ncontrol / quality", COLORS["dark"], fontsize=4.7)
    arrow(ax, (0.58, 0.26), (0.45, 0.17), lw=0.8)
    arrow(ax, (0.78, 0.26), (0.80, 0.17), lw=0.8)
    arrow(ax, (0.54, 0.125), (0.62, 0.125), lw=0.8)

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
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.58))
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
    ax.set_ylabel("Req. speedup (x)")
    style_axis(ax, grid="y")
    fig.subplots_adjust(left=0.35, right=0.99, bottom=0.24, top=0.96)
    path = os.path.join(FIG_DIR, "digits_required_speedup.pdf")
    return save_canvas(fig, path)


def figure_digits_legend():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 0.22))
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
        fontsize=5.8,
        handletextpad=0.25,
        columnspacing=0.55,
    )
    path = os.path.join(FIG_DIR, "practical_suite_legend.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_digits_quality_runtime():
    rows = read_csv("data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv")
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.58))
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
    ax.set_xlabel("Req. speedup (x)")
    ax.set_ylabel("Quantum accuracy")
    ax.set_ylim(0.4, 1.03)
    style_axis(ax, grid="both")
    legend = ax.get_legend()
    if legend:
        legend.remove()
    fig.subplots_adjust(left=0.27, right=0.99, bottom=0.32, top=0.96)
    path = os.path.join(FIG_DIR, "digits_quality_speedup.pdf")
    return save_canvas(fig, path)


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


def figure_quality_bottleneck_summary():
    rows = read_csv(STRONG_NATIVE_SUMMARY_CSV)
    taxonomy = load_summary(STRONG_NATIVE_TAXONOMY_JSON)
    if not rows or taxonomy is None:
        return None

    workloads = [
        ("ml", "ML", COLORS["blue"]),
        ("chemistry", "Chem.", COLORS["teal"]),
        ("optimization", "Opt.", COLORS["red"]),
        ("simulation", "Sim.", COLORS["green"]),
    ]
    gap_series = []
    for workload, label, color in workloads:
        gaps = np.array(
            [
                max(0.0, float(row["quality_gap"]))
                for row in rows
                if row["workload"] == workload
            ]
        )
        gap_series.append((label, color, gaps))

    x = np.arange(len(workloads))
    fig, ax_gap = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.52))
    parts = ax_gap.violinplot(
        [gaps for _label, _color, gaps in gap_series],
        positions=x,
        widths=0.72,
        showmeans=False,
        showmedians=False,
        showextrema=False,
    )
    for body, (_label, color, _gaps) in zip(parts["bodies"], gap_series):
        body.set_facecolor(color)
        body.set_edgecolor("black")
        body.set_linewidth(0.45)
        body.set_alpha(0.42)
    for idx, (_label, color, gaps) in enumerate(gap_series):
        p50 = float(np.percentile(gaps, 50))
        p90 = float(np.percentile(gaps, 90))
        ax_gap.scatter(idx, p50, s=23, color=color, edgecolors="black", linewidths=0.5, zorder=3)
        ax_gap.scatter(idx, p90, s=24, color=color, edgecolors="black", linewidths=0.5, marker="s", zorder=3)
    ax_gap.set_xticks(x)
    ax_gap.set_xticklabels([item[1] for item in workloads])
    ax_gap.set_ylim(0.0, 0.9)
    ax_gap.set_ylabel("Quality gap\nto native")
    style_axis(ax_gap, grid="y")
    gap_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS["dark"], markeredgecolor="black", markersize=3.8),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=COLORS["dark"], markeredgecolor="black", markersize=3.8),
    ]
    ax_gap.legend(
        gap_handles,
        ["p50", "p90"],
        ncol=2,
        loc="upper center",
        bbox_to_anchor=(0.52, 1.25),
        frameon=False,
        fontsize=5.3,
        handlelength=0.9,
        handletextpad=0.25,
        columnspacing=0.65,
    )
    fig.subplots_adjust(top=0.80, bottom=0.23, left=0.28, right=0.98)
    gap_path = os.path.join(FIG_DIR, "quality_gap_summary.pdf")
    save_canvas(fig, gap_path)

    y = np.arange(len(workloads))
    quality = []
    speed = []
    for workload, _label, _color in workloads:
        fractions = taxonomy["by_workload"][workload]["fractions"]
        quality.append(100.0 * float(fractions.get("quality-limited", 0.0)))
        speed.append(100.0 * float(fractions.get("speed-limited", 0.0)))
    fig, ax_tax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.52))
    ax_tax.barh(y, quality, color=COLORS["red"], height=0.56, label="Quality")
    ax_tax.barh(y, speed, left=quality, color=COLORS["blue"], height=0.56, label="Speed")
    for ypos, qval, sval in zip(y, quality, speed):
        if qval >= 18:
            ax_tax.text(qval / 2.0, ypos, "{:.0f}%".format(qval), ha="center", va="center", fontsize=5.5, color="white")
        if sval >= 18:
            ax_tax.text(qval + sval / 2.0, ypos, "{:.0f}%".format(sval), ha="center", va="center", fontsize=5.5, color="white")
    ax_tax.set_yticks(y)
    ax_tax.set_yticklabels([item[1] for item in workloads])
    ax_tax.invert_yaxis()
    ax_tax.set_xlim(0.0, 100.0)
    ax_tax.set_xlabel("Within-workload\ncases (%)")
    style_axis(ax_tax, grid="x")
    ax_tax.legend(
        [Rectangle((0, 0), 1, 1, color=COLORS["red"]), Rectangle((0, 0), 1, 1, color=COLORS["blue"])],
        ["Quality", "Speed"],
        ncol=2,
        loc="upper center",
        bbox_to_anchor=(0.52, 1.25),
        frameon=False,
        fontsize=5.3,
        handlelength=0.9,
        handletextpad=0.25,
        columnspacing=0.6,
    )
    fig.subplots_adjust(top=0.80, bottom=0.28, left=0.27, right=0.98)
    fraction_path = os.path.join(FIG_DIR, "quality_bottleneck_fraction.pdf")
    save_canvas(fig, fraction_path)

    return [gap_path, fraction_path]


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

    colors = [COLORS["blue"], COLORS["teal"], COLORS["red"], COLORS["green"]]

    legend_fig, legend_ax = plt.subplots(figsize=(COLUMN_WIDTH * 0.82, 0.24))
    legend_ax.axis("off")
    legend_fig.legend(
        [legend_marker(color) for color in colors],
        labels,
        ncol=4,
        loc="center",
        frameon=False,
        fontsize=5.6,
        handlelength=1.0,
        handletextpad=0.25,
        columnspacing=0.55,
    )
    legend_path = os.path.join(FIG_DIR, "strong_native_legend.pdf")
    legend_fig.savefig(legend_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(legend_fig)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.62))
    for label, color, initial, strong in zip(labels, colors, official_speed, strong_speed):
        ax.plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.9)
    ax.set_yscale("log")
    ax.set_xlim(-0.12, 1.12)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Initial\nbaseline", "Strong\nbaseline"])
    ax.set_ylabel("Median\nspeedup (x)")
    style_axis(ax, grid="y")
    fig.subplots_adjust(top=0.96, bottom=0.31, left=0.38, right=0.98)
    speed_path = os.path.join(FIG_DIR, "strong_native_comparison.pdf")
    fig.savefig(speed_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.62))
    for label, color, initial, strong in zip(labels, colors, official_quality, strong_quality):
        ax.plot([0, 1], [initial, strong], marker="o", color=color, linewidth=1.9)
    ax.set_xlim(-0.12, 1.12)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Initial\nbaseline", "Strong\nbaseline"])
    ax.set_ylabel("Median\nquality gap")
    style_axis(ax, grid="y")
    fig.subplots_adjust(bottom=0.31, left=0.38, right=0.98, top=0.96)
    quality_path = os.path.join(FIG_DIR, "strong_native_quality_shift.pdf")
    fig.savefig(quality_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return [legend_path, speed_path, quality_path]


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
        os.path.exists(os.path.join(ROOT, SCALE_WEAK_32_SUMMARY_CSV))
        and os.path.exists(os.path.join(ROOT, SCALE_WEAK_64_SUMMARY_CSV))
    ):
        return None

    points = [
        ("128 GPUs\n3,552 cases", 128, 3552, 419, SCALE_WEAK_32_SUMMARY_CSV),
        ("256 GPUs\n7,104 cases", 256, 7104, 576, SCALE_WEAK_64_SUMMARY_CSV),
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

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.16))
    y = np.arange(len(workloads))
    left = np.zeros(len(workloads))
    handles = []
    labels = []
    frac_array = np.array(fractions)
    for idx, (_, label, color) in enumerate(categories):
        values = frac_array[:, idx]
        bars = ax.barh(y, values, left=left, color=color, height=0.44)
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
    ax.invert_yaxis()
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Operation share")
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xticklabels(["0", "50%", "100%"])
    style_axis(ax, grid="x")
    add_top_legend(fig, handles, labels, ncol=3, y=1.03, fontsize=5.5)
    fig.subplots_adjust(left=0.40, right=0.98, bottom=0.24, top=0.70)
    path = os.path.join(FIG_DIR, "circuit_operation_mix.pdf")
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_projected_time_decomposition():
    if not os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_CSV)):
        return None

    rows = read_csv(STRONG_NATIVE_SUMMARY_CSV)
    workloads = [
        ("ml", "ML"),
        ("chemistry", "Chem."),
        ("optimization", "Opt."),
        ("simulation", "Sim."),
    ]
    categories = [
        ("1Q", COLORS["blue"]),
        ("2Q", COLORS["orange"]),
        ("Meas.", COLORS["purple"]),
        ("Decode/ctrl.", COLORS["gray"]),
    ]

    shares = []
    for workload, _label in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        per_case = []
        for row in subset:
            oneq = float(row["one_qubit_gates"]) * 1.0
            twoq = float(row["two_qubit_gates"]) * 4.0
            meas = float(row["measurement_ops"]) * 1.0
            serial = float(row["circuit_evaluations"]) * (5.0 + 50.0)
            total = max(1.0, oneq + twoq + meas + serial)
            per_case.append([oneq / total, twoq / total, meas / total, serial / total])
        shares.append(np.median(np.array(per_case), axis=0))

    fig = plt.figure(figsize=(COLUMN_WIDTH, 1.22))
    gs = fig.add_gridspec(2, 1, height_ratios=[0.16, 1.0], hspace=-0.03)
    legend_ax = fig.add_subplot(gs[0])
    ax = fig.add_subplot(gs[1])
    legend_ax.axis("off")
    y = np.arange(len(workloads))
    left = np.zeros(len(workloads))
    handles = []
    labels = []
    share_array = np.array(shares)
    for idx, (label, color) in enumerate(categories):
        values = share_array[:, idx]
        bars = ax.barh(y, values, left=left, color=color, height=0.50)
        handles.append(bars[0])
        labels.append(label)
        for ypos, value, base in zip(y, values, left):
            if value >= 0.16:
                ax.text(
                    base + value / 2.0,
                    ypos,
                    "{:.0f}%".format(value * 100.0),
                    ha="center",
                    va="center",
                    fontsize=6.4,
                    color="white" if idx in {0, 2, 3} else "black",
                )
        left += values
    ax.set_yticks(y)
    ax.set_yticklabels([label for _, label in workloads])
    ax.invert_yaxis()
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Time share", labelpad=0.9)
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xticklabels(["0", "50%", "100%"])
    style_axis(ax, grid="x")
    ax.tick_params(axis="both", labelsize=6.6, pad=0.9, width=0.6)
    ax.xaxis.label.set_size(6.8)
    legend_ax.legend(
        handles,
        labels,
        loc="center",
        bbox_to_anchor=(0.5, 0.36),
        ncol=4,
        frameon=False,
        fontsize=6.4,
        handlelength=0.9,
        handletextpad=0.35,
        columnspacing=0.70,
        borderaxespad=0.0,
    )
    fig.subplots_adjust(left=0.17, right=0.985, bottom=0.25, top=0.99)
    path = os.path.join(FIG_DIR, "projected_time_decomposition.pdf")
    return save_canvas(fig, path)


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
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([label for _, label, _ in workloads])
    ax.set_xlabel("Tail speedup (x)")
    ax.set_xlim(1e3, 8.0e5)
    ax.invert_yaxis()
    style_axis(ax, grid="x")
    fig.subplots_adjust(left=0.30, right=0.98, bottom=0.27, top=0.91)
    path = os.path.join(FIG_DIR, "threshold_tail_pressure.pdf")
    return save_canvas(fig, path)


def figure_tolerance_sensitivity():
    if not os.path.exists(os.path.join(ROOT, STRONG_NATIVE_SUMMARY_CSV)):
        return None

    rows = read_csv(STRONG_NATIVE_SUMMARY_CSV)
    workload_specs = [
        ("ml", "ML", COLORS["blue"], 0.02),
        ("chemistry", "Chem.", COLORS["teal"], 0.01),
        ("optimization", "Opt.", COLORS["red"], 0.02),
        ("simulation", "Sim.", COLORS["green"], 0.01),
    ]
    scenario_specs = [
        ("$10^4$x\n90% R", 1.0e4, 0.90),
        ("$10^5$x\n90% R", 1.0e5, 0.90),
        ("$10^6$x\n90% R", 1.0e6, 0.90),
        ("$10^6$x\n100% R", 1.0e6, 1.00),
    ]

    matrix = np.zeros((len(workload_specs), len(scenario_specs)), dtype=float)
    for row_idx, (workload, label, color, base_tol) in enumerate(workload_specs):
        subset = [row for row in rows if row["workload"] == workload]
        required = np.array([float(row["speedup_required"]) for row in subset])
        gaps = np.array([max(0.0, float(row["quality_gap"])) for row in subset])
        for col_idx, (_scenario_label, speedup, recovery) in enumerate(scenario_specs):
            advantaged = (speedup >= required) & (gaps * (1.0 - recovery) <= base_tol)
            matrix[row_idx, col_idx] = 100.0 * float(np.mean(advantaged)) if advantaged.size else 0.0

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.15))
    cmap = plt.get_cmap("YlGnBu")
    ax.imshow(matrix, vmin=0, vmax=100, cmap=cmap, aspect="auto")
    for row_idx in range(matrix.shape[0]):
        for col_idx in range(matrix.shape[1]):
            value = matrix[row_idx, col_idx]
            text_color = "white" if value >= 56.0 else COLORS["dark"]
            ax.text(
                col_idx,
                row_idx,
                "{:.0f}%".format(value),
                ha="center",
                va="center",
                fontsize=5.1,
                color=text_color,
                fontweight="bold" if value >= 70.0 else "normal",
            )
    ax.set_xticks(np.arange(len(scenario_specs)))
    ax.set_xticklabels([label for label, _speedup, _recovery in scenario_specs])
    ax.tick_params(axis="x", labelsize=5.1, pad=1.0, length=0)
    ax.set_yticks(np.arange(len(workload_specs)))
    ax.set_yticklabels([label for _workload, label, _color, _tol in workload_specs])
    ax.tick_params(axis="y", labelsize=6.1, pad=1.1, length=0)
    for spine in ax.spines.values():
        spine.set_color("#FFFFFF")
        spine.set_linewidth(0.55)
    ax.set_xticks(np.arange(-0.5, len(scenario_specs), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(workload_specs), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.75)
    ax.tick_params(which="minor", bottom=False, left=False)
    fig.subplots_adjust(left=0.16, right=0.99, bottom=0.25, top=0.96)
    path = os.path.join(FIG_DIR, "tolerance_sensitivity.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_ft_shot_sensitivity():
    scenario_summary = load_summary(PROJECTION_SCENARIOS_JSON)
    if scenario_summary is None:
        return None

    workload_specs = [
        ("ml", "ML"),
        ("chemistry", "Chem."),
        ("optimization", "Opt."),
        ("simulation", "Sim."),
    ]
    scenario_specs = [
        ("conservative_surface", "Conserv.\nsurface"),
        ("resource_estimator_like", "Resource\nest."),
        ("default_optimistic", "Default\nopt."),
        ("ldpc_future_like", "LDPC\nfuture"),
        ("aggressive_batched", "Aggressive\nbatch"),
    ]
    matrix = np.zeros((len(workload_specs), len(scenario_specs)), dtype=float)
    ratio_matrix = np.zeros_like(matrix)
    by_scenario = scenario_summary.get("by_scenario", {})
    for row_idx, (workload, _label) in enumerate(workload_specs):
        for col_idx, (scenario_id, _scenario_label) in enumerate(scenario_specs):
            item = by_scenario.get(scenario_id, {}).get("by_workload", {}).get(workload, {})
            matrix[row_idx, col_idx] = 100.0 * float(item.get("advantaged_fraction", 0.0))
            ratio_matrix[row_idx, col_idx] = float(item.get("median_projected_native_ratio", 0.0))

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.35))
    cmap = plt.get_cmap("YlGnBu")
    ax.imshow(matrix, vmin=0, vmax=100, cmap=cmap, aspect="auto")
    for row_idx in range(matrix.shape[0]):
        for col_idx in range(matrix.shape[1]):
            value = matrix[row_idx, col_idx]
            ratio = ratio_matrix[row_idx, col_idx]
            text_color = "white" if value >= 56.0 else COLORS["dark"]
            if ratio >= 100:
                ratio_text = "{:.0f}x".format(ratio)
            elif ratio >= 10:
                ratio_text = "{:.1f}x".format(ratio)
            elif ratio >= 1:
                ratio_text = "{:.1f}x".format(ratio)
            elif ratio >= 0.01:
                ratio_text = "{:.2f}x".format(ratio)
            else:
                ratio_text = "<0.01x"
            ax.text(
                col_idx,
                row_idx,
                "{:.0f}%\n{}".format(value, ratio_text),
                ha="center",
                va="center",
                fontsize=4.65,
                color=text_color,
                linespacing=0.86,
                fontweight="bold" if value >= 70.0 else "normal",
            )
    ax.set_xticks(np.arange(len(scenario_specs)))
    ax.set_xticklabels([label for _scenario_id, label in scenario_specs])
    ax.xaxis.tick_bottom()
    ax.tick_params(axis="x", labelsize=5.4, pad=1.0, length=0)
    ax.set_yticks(np.arange(len(workload_specs)))
    ax.set_yticklabels([label for _workload, label in workload_specs])
    ax.tick_params(axis="y", labelsize=6.1, pad=1.2, length=0)
    for spine in ax.spines.values():
        spine.set_color("#FFFFFF")
        spine.set_linewidth(0.55)
    ax.set_xticks(np.arange(-0.5, len(scenario_specs), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(workload_specs), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=0.75)
    ax.tick_params(which="minor", bottom=False, left=False)
    fig.subplots_adjust(left=0.16, right=0.99, bottom=0.27, top=0.96)
    path = os.path.join(FIG_DIR, "ft_shot_sensitivity.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_architecture_focus_matrix():
    rows = read_csv(STRONG_NATIVE_SUMMARY_CSV)
    taxonomy = load_summary(STRONG_NATIVE_TAXONOMY_JSON)
    if not rows or taxonomy is None:
        return None

    workloads = [
        ("ml", "ML", COLORS["blue"]),
        ("chemistry", "Chem.", COLORS["teal"]),
        ("optimization", "Opt.", COLORS["red"]),
        ("simulation", "Sim.", COLORS["green"]),
    ]

    tolerances = {
        "ml": 0.02,
        "chemistry": 0.01,
        "optimization": 0.02,
        "simulation": 0.01,
    }

    raw_values = []
    cell_text = []
    for workload, label, color in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        fractions = taxonomy["by_workload"][workload]["fractions"]
        quality_fraction = 100.0 * float(fractions.get("quality-limited", 0.0))
        evals = float(np.median([float(row["circuit_evaluations"]) for row in subset]))

        decode_shares = []
        twoq_shares = []
        recovery_required = []
        for row in subset:
            oneq = float(row["one_qubit_gates"]) * 1.0
            twoq = float(row["two_qubit_gates"]) * 4.0
            meas = float(row["measurement_ops"]) * 1.0
            decode = float(row["circuit_evaluations"]) * (5.0 + 50.0)
            total = max(1.0, oneq + twoq + meas + decode)
            decode_shares.append(100.0 * decode / total)
            twoq_shares.append(100.0 * twoq / total)
            gap = max(0.0, float(row["quality_gap"]))
            tolerance = tolerances[workload]
            if gap <= tolerance:
                recovery_required.append(0.0)
            else:
                recovery_required.append(100.0 * max(0.0, 1.0 - tolerance / gap))
        decode_share = float(np.median(decode_shares))
        twoq_share = float(np.median(twoq_shares))
        recovery = float(np.median(recovery_required))
        raw_values.append([recovery, evals, decode_share, twoq_share])
        cell_text.append(
            [
                "{:.0f}%".format(recovery),
                "{:.0f}".format(evals),
                "{:.0f}%".format(decode_share),
                "{:.0f}%".format(twoq_share),
            ]
        )

    raw_values = np.array(raw_values, dtype=float)
    matrix = np.zeros_like(raw_values)
    for col in range(raw_values.shape[1]):
        column = raw_values[:, col]
        span = float(np.max(column) - np.min(column))
        if span > 0.0:
            matrix[:, col] = (column - float(np.min(column))) / span

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.64))
    image = ax.imshow(matrix, cmap="YlOrRd", vmin=0.0, vmax=1.0, aspect="auto")
    row_labels = [label for _, label, _ in workloads]
    col_labels = [
        "Quality\n$R_q$",
        "Hybrid\n$N_e$",
        "Control\nshare",
        "2Q exec.\nshare",
    ]
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    ax.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False, pad=2)
    ax.tick_params(axis="y", pad=2)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            ax.text(
                j,
                i,
                cell_text[i][j],
                ha="center",
                va="center",
                fontsize=6.4,
                weight="bold" if value >= 0.85 else "normal",
                color="white" if value >= 0.68 else COLORS["dark"],
            )
            if value >= 0.85:
                ax.add_patch(
                    Rectangle(
                        (j - 0.48, i - 0.48),
                        0.96,
                        0.96,
                        fill=False,
                        edgecolor=COLORS["dark"],
                        linewidth=1.05,
                    )
                )
    ax.set_xticks(np.arange(-0.5, len(col_labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_linewidth(0.7)
        spine.set_color("#555555")
    cbar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.035)
    cbar.set_ticks([0.0, 0.5, 1.0])
    cbar.set_ticklabels(["low", "mid", "high"])
    cbar.ax.tick_params(labelsize=5.4, width=0.5, pad=1.0)
    cbar.set_label("severity", fontsize=5.8, labelpad=1.5)
    fig.subplots_adjust(left=0.13, right=0.92, bottom=0.08, top=0.78)
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
    weak_mask = np.array([run.get("kind") == "weak" for run in runs], dtype=bool)
    weak_ref_idx = int(np.where(weak_mask)[0][0])
    ideal = throughput[weak_ref_idx] * (gpus / gpus[weak_ref_idx])
    per_gpu = cases / (elapsed * gpus)
    efficiency = per_gpu / per_gpu[weak_ref_idx]
    gpu_ticks = [1, 4, 16, 64, 256]

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 2.02))
    line_weak = ax.plot(
        gpus[weak_mask],
        throughput[weak_mask],
        marker="o",
        color=COLORS["blue"],
        label="weak suite",
    )[0]
    line_pilot = ax.plot(
        gpus[~weak_mask],
        throughput[~weak_mask],
        marker="o",
        markerfacecolor="white",
        markeredgecolor=COLORS["blue"],
        linestyle=":",
        color=COLORS["blue"],
        label="pilot",
    )[0]
    line_ideal = ax.plot(gpus, ideal, linestyle="--", color=COLORS["gray"], label="ideal")[0]
    ax.set_xscale("log", base=2)
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels([str(tick) for tick in gpu_ticks])
    ax.set_xlabel("GPUs")
    ax.set_ylabel("Throughput\n(cases/s)")
    style_axis(ax, grid="both")
    ax.set_xlim(0.8, 330)
    add_top_legend(
        fig,
        [line_pilot, line_weak, line_ideal],
        ["pilot", "weak", "ideal"],
        ncol=3,
        y=1.00,
        fontsize=5.1,
    )
    fig.subplots_adjust(top=0.76, bottom=0.28, left=0.33, right=0.98)
    throughput_path = os.path.join(FIG_DIR, "weak_scaling.pdf")
    fig.savefig(throughput_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 2.02))
    line_eff = ax.plot(gpus[weak_mask], efficiency[weak_mask], marker="s", color=COLORS["orange"])[0]
    line_ref = ax.axhline(1.0, linestyle="--", color=COLORS["gray"], linewidth=1.0)
    ax.set_xscale("log", base=2)
    ax.set_xticks([64, 128, 256])
    ax.set_xticklabels(["64", "128", "256"])
    ax.set_xlabel("GPUs")
    ax.set_ylabel("Norm. per-GPU\nthroughput")
    efficiency_main = efficiency[weak_mask]
    ax.set_ylim(
        max(0.0, float(np.min(efficiency_main)) * 0.90),
        max(1.12, float(np.max(efficiency_main)) * 1.08),
    )
    style_axis(ax, grid="both")
    ax.set_xlim(48, 330)
    add_top_legend(
        fig,
        [line_eff, line_ref],
        ["weak", "ref."],
        ncol=2,
        y=1.00,
        fontsize=5.1,
    )
    fig.subplots_adjust(top=0.76, bottom=0.28, left=0.35, right=0.98)
    efficiency_path = os.path.join(FIG_DIR, "weak_scaling_efficiency.pdf")
    fig.savefig(efficiency_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return [throughput_path, efficiency_path]


def figure_strong_scaling():
    runs = [run for run in STRONG_SCALING_RUNS if load_summary(run["summary"]) is not None]
    if len(runs) < 2:
        return None

    gpus = np.array([run["gpus"] for run in runs], dtype=float)
    cases = np.array([run["cases"] for run in runs], dtype=float)
    elapsed = np.array([run["elapsed_sec"] for run in runs], dtype=float)
    fixed_mask = np.array([run.get("kind") == "fixed" for run in runs], dtype=bool)
    fixed_cases = float(np.max(cases[fixed_mask])) if np.any(fixed_mask) else float(np.max(cases))
    normalized_elapsed = elapsed * (fixed_cases / cases)
    speedup = normalized_elapsed[0] / normalized_elapsed
    ideal = gpus / gpus[0]
    order = np.argsort(gpus)
    gpus = gpus[order]
    normalized_elapsed = normalized_elapsed[order]
    speedup = speedup[order]
    ideal = ideal[order]
    gpu_ticks = [1, 4, 16, 64, 256]

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 2.02))
    line_time = ax.plot(gpus, normalized_elapsed / 60.0, marker="o", color=COLORS["blue"])[0]
    line_time_ideal = ax.plot(
        gpus,
        (normalized_elapsed[0] / ideal) / 60.0,
        linestyle="--",
        color=COLORS["gray"],
    )[0]
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels([str(tick) for tick in gpu_ticks])
    ax.set_ylabel("Actual TTS\n(min)")
    ax.set_xlabel("GPUs")
    style_axis(ax, grid="both")
    ax.set_xlim(0.8, 330)
    ax.set_ylim(max(1.0, float(np.min(normalized_elapsed / 60.0)) * 0.70),
                max(normalized_elapsed / 60.0) * 1.35)
    add_top_legend(
        fig,
        [line_time, line_time_ideal],
        ["actual", "ideal"],
        ncol=2,
        y=1.00,
        fontsize=5.4,
    )
    fig.subplots_adjust(top=0.76, bottom=0.27, left=0.33, right=0.98)
    elapsed_path = os.path.join(FIG_DIR, "strong_scaling.pdf")
    fig.savefig(elapsed_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 2.02))
    line_speed = ax.plot(gpus, speedup, marker="o", color=COLORS["green"])[0]
    line_speed_ideal = ax.plot(gpus, ideal, linestyle="--", color=COLORS["gray"], label="ideal linear")[0]
    ax.set_xscale("log", base=2)
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels([str(tick) for tick in gpu_ticks])
    ax.set_xlabel("GPUs")
    ax.set_ylabel("Speedup\nvs. 1 GPU")
    style_axis(ax, grid="both")
    ax.set_xlim(0.8, 330)
    add_top_legend(
        fig,
        [line_speed, line_speed_ideal],
        ["actual", "ideal"],
        ncol=2,
        y=1.00,
        fontsize=5.4,
    )
    fig.subplots_adjust(top=0.76, bottom=0.28, left=0.31, right=0.98)
    speedup_path = os.path.join(FIG_DIR, "strong_scaling_speedup.pdf")
    fig.savefig(speedup_path, bbox_inches="tight", pad_inches=0.01)
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
        ("ml", "ML", COLORS["blue"]),
        ("chemistry", "Chem.", COLORS["teal"]),
        ("optimization", "Opt.", COLORS["red"]),
        ("simulation", "Sim.", COLORS["green"]),
    ]

    distance = 25.0
    cycle_sec = 1.0e-6
    shot_parallel = 1.0e4
    k1, k2, km = 1.0, 4.0, 1.0
    decoder_sec_per_eval = 5.0e-6
    control_queue_sec_per_eval = 50.0e-6

    points = []
    for workload, label, color in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        native_ms = []
        error_ms = []
        one_meas_ms = []
        twoq_ms = []
        for row in subset:
            evals = max(1.0, float(row["circuit_evaluations"]))
            d1 = float(row["one_qubit_gates"])
            d2 = float(row["two_qubit_gates"])
            dm = float(row["measurement_ops"])
            native_ms.append(1.0e3 * float(row["native_runtime_sec"]))
            error_ms.append(evals * (decoder_sec_per_eval + control_queue_sec_per_eval) * 1.0e3)
            one_meas_ms.append(
                evals * (d1 * k1 * distance * cycle_sec + dm * km * distance * cycle_sec)
                / shot_parallel
                * 1.0e3
            )
            twoq_ms.append(
                evals * d2 * k2 * distance * cycle_sec / shot_parallel * 1.0e3
            )
        error = float(np.median(error_ms))
        one_meas = float(np.median(one_meas_ms))
        twoq = float(np.median(twoq_ms))
        total = error + one_meas + twoq
        native = float(np.median(native_ms))
        component_ratios = {
            "error_ratio": error / max(native, 1.0e-12),
            "one_meas_ratio": one_meas / max(native, 1.0e-12),
            "twoq_ratio": twoq / max(native, 1.0e-12),
        }
        ratio = total / max(native, 1.0e-12)
        single_targets = {}
        for key, value in component_ratios.items():
            if ratio <= 1.0:
                single_targets[key] = 1.0
            else:
                other_terms = ratio - value
                single_targets[key] = None if other_terms >= 1.0 else value / (1.0 - other_terms)
        single_targets["all_terms"] = max(1.0, ratio)
        points.append(
            {
                "label": label,
                "color": color,
                "native": native,
                "error_ratio": component_ratios["error_ratio"],
                "one_meas_ratio": component_ratios["one_meas_ratio"],
                "twoq_ratio": component_ratios["twoq_ratio"],
                "ratio": ratio,
                "single_targets": single_targets,
            }
        )

    def blend_with_white(hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        rgb = np.array([int(hex_color[i:i + 2], 16) for i in (0, 2, 4)], dtype=float) / 255.0
        white = np.ones(3)
        mixed = white * (1.0 - alpha) + rgb * alpha
        return mixed

    fig_total, ax_total = plt.subplots(figsize=(COLUMN_WIDTH, 1.12))
    y_centers = np.arange(len(points)) * 0.92
    eps = 1.5e-2
    for center, point in zip(y_centers, points):
        ratio_text = "{:.1f}x".format(point["ratio"]) if point["ratio"] >= 1.0 else "{:.2f}x".format(point["ratio"])
        total_value = max(eps * 1.08, point["ratio"])
        ax_total.barh(
            center,
            total_value - eps,
            left=eps,
            height=0.34,
            color=blend_with_white(point["color"], 0.68),
            edgecolor=point["color"],
            linewidth=0.45,
        )
        ax_total.text(
            min(370.0, max(total_value * 1.13, 0.035)),
            center,
            ratio_text,
            ha="left",
            va="center",
            fontsize=5.6,
            color=COLORS["dark"],
        )

    ax_total.set_xscale("log")
    ax_total.set_xlim(eps, 520.0)
    ax_total.set_xticks([3e-2, 1e-1, 1, 1e1, 1e2])
    ax_total.set_xticklabels(["0.03", "0.1", "1", "10", "$10^2$"])
    ax_total.axvline(1.0, color=COLORS["dark"], linestyle="--", linewidth=0.8)
    ax_total.text(
        1.04,
        y_centers[0] - 0.43,
        "same-input native runtime",
        ha="left",
        va="bottom",
        fontsize=5.05,
        color=COLORS["dark"],
    )
    ax_total.set_yticks(y_centers)
    ax_total.set_yticklabels([point["label"] for point in points])
    ax_total.invert_yaxis()
    ax_total.set_xlabel("Projected total / native runtime (x)", labelpad=1.5)
    style_axis(ax_total, grid="x")
    ax_total.set_ylim(y_centers[-1] + 0.42, y_centers[0] - 0.42)
    fig_total.subplots_adjust(left=0.19, right=0.96, bottom=0.25, top=0.80)
    path_total = os.path.join(FIG_DIR, "advantage_frontier_total.pdf")
    fig_total.savefig(path_total, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig_total)

    taxonomy = load_summary(STRONG_NATIVE_TAXONOMY_JSON)
    tolerances = {
        "ml": 0.02,
        "chemistry": 0.01,
        "optimization": 0.02,
        "simulation": 0.01,
    }
    pressure_rows = []
    pressure_text = []
    for workload, label, _color in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        quality_fraction = 0.0
        if taxonomy is not None:
            quality_fraction = 100.0 * float(
                taxonomy["by_workload"][workload]["fractions"].get("quality-limited", 0.0)
            )
        evals = float(np.median([float(row["circuit_evaluations"]) for row in subset]))
        recoveries = []
        decode_shares = []
        twoq_shares = []
        total_ratios = []
        for row in subset:
            oneq = float(row["one_qubit_gates"])
            twoq = 4.0 * float(row["two_qubit_gates"])
            meas = float(row["measurement_ops"])
            serial = float(row["circuit_evaluations"]) * 55.0
            total_cycles = max(1.0, oneq + twoq + meas + serial)
            decode_shares.append(100.0 * serial / total_cycles)
            twoq_shares.append(100.0 * twoq / total_cycles)
            gap = max(0.0, float(row["quality_gap"]))
            tol = tolerances[workload]
            recoveries.append(0.0 if gap <= tol else 100.0 * (1.0 - tol / gap))
        matching_point = next(point for point in points if point["label"] == label)
        total_ratios.append(matching_point["ratio"])
        pressure_rows.append(
            [
                float(np.median(recoveries)),
                quality_fraction,
                evals,
                float(np.median(decode_shares)),
                float(np.median(twoq_shares)),
                float(np.median(total_ratios)),
            ]
        )
        pressure_text.append(
            [
                "{:.0f}%".format(float(np.median(recoveries))),
                "{:.0f}%".format(quality_fraction),
                "{:.0f}".format(evals),
                "{:.0f}%".format(float(np.median(decode_shares))),
                "{:.0f}%".format(float(np.median(twoq_shares))),
                "{:.1f}x".format(float(np.median(total_ratios)))
                if float(np.median(total_ratios)) >= 1.0
                else "{:.2f}x".format(float(np.median(total_ratios))),
            ]
        )

    raw = np.array(pressure_rows, dtype=float)
    matrix = np.zeros_like(raw)
    for col in range(raw.shape[1]):
        column = raw[:, col]
        span = float(np.max(column) - np.min(column))
        if span > 0.0:
            matrix[:, col] = (column - float(np.min(column))) / span

    fig_target, ax_target = plt.subplots(figsize=(COLUMN_WIDTH, 1.66))
    image = ax_target.imshow(matrix, cmap="YlOrRd", vmin=0.0, vmax=1.0, aspect="auto")
    col_labels = [
        "Req.\n$R_q$",
        "Qual.\nlimited",
        "Hybrid\n$N_e$",
        "Decode/\nctrl.",
        "2Q\nexec.",
        "Total /\nnative",
    ]
    row_labels = [label for _workload, label, _color in workloads]
    ax_target.set_xticks(np.arange(len(col_labels)))
    ax_target.set_xticklabels(col_labels)
    ax_target.set_yticks(np.arange(len(row_labels)))
    ax_target.set_yticklabels(row_labels)
    ax_target.tick_params(axis="x", top=True, bottom=False, labeltop=True, labelbottom=False, pad=2)
    ax_target.tick_params(axis="y", length=0, pad=2)
    for row_idx in range(matrix.shape[0]):
        for col_idx in range(matrix.shape[1]):
            value = matrix[row_idx, col_idx]
            ax_target.text(
                col_idx,
                row_idx,
                pressure_text[row_idx][col_idx],
                ha="center",
                va="center",
                fontsize=5.55,
                weight="bold" if value >= 0.82 else "normal",
                color="white" if value >= 0.63 else COLORS["dark"],
            )
    ax_target.set_xticks(np.arange(-0.5, len(col_labels), 1), minor=True)
    ax_target.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax_target.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
    ax_target.tick_params(which="minor", bottom=False, left=False)
    for spine in ax_target.spines.values():
        spine.set_linewidth(0.6)
        spine.set_color("#555555")
    cbar = fig_target.colorbar(image, ax=ax_target, fraction=0.036, pad=0.025)
    cbar.set_ticks([0.0, 0.5, 1.0])
    cbar.set_ticklabels(["low", "mid", "high"])
    cbar.ax.tick_params(labelsize=5.0, width=0.5, pad=1.0)
    fig_target.subplots_adjust(left=0.13, right=0.91, bottom=0.08, top=0.79)
    path_target = os.path.join(FIG_DIR, "advantage_component_targets.pdf")
    fig_target.savefig(path_target, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig_target)
    return [path_total, path_target]


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
        figure_intro_threshold_summary(),
        figure_design_overview(),
        figure_design_projection_flow(),
        figure_evaluation_evidence_flow(),
        figure_digits_legend(),
        figure_digits_speedup(),
        figure_digits_quality_runtime(),
        figure_practical_suite_legend(),
        figure_practical_suite(),
        figure_quality_bottleneck_summary(),
        figure_strong_native_comparison(),
        figure_ml_strong_native_gate(),
        figure_ml_profile_breakdown(),
        figure_ml_native_profile_combined(),
        figure_threshold_tail_pressure(),
        figure_projected_time_decomposition(),
        figure_workload_growth(),
        figure_advantage_frontier(),
        figure_tolerance_sensitivity(),
        figure_ft_shot_sensitivity(),
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
