#!/usr/bin/env python3
"""Generate paper figures from measured leadership-system results."""

import csv
import inspect
import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

from hpca_projection_model import projected_components_sec


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIG_DIR = os.path.join(ROOT, "paper", "figures")
TEXT_WIDTH = 6.85
COLUMN_WIDTH = 3.35
INTRO_PATH_WIDTH = COLUMN_WIDTH * 0.46
INTRO_THRESHOLD_WIDTH = COLUMN_WIDTH * 0.92
SUBFIGURE_WIDTH = COLUMN_WIDTH * 0.48
FIGURE_FONT = 8.5
FIGURE_TICK_FONT = 8.3
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
DEFAULT_FIGURE_PROJECTION = {
    "distance": 25.0,
    "cycle_sec": 1.0e-6,
    "shot_lanes": 1.0e4,
    "decoder_sec_per_eval": 5.0e-6,
    "host_io_floor_sec_per_eval": 20.0e-6,
    "queue_service_sec_per_eval": 30.0e-6,
    "queue_utilization": 0.35,
    "queue_tail_percentile": 0.99,
    "enable_queue_model": False,
    "enable_controller_scaling": False,
    "enable_host_context": False,
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
PHYSICAL_ARCHITECTURE_DSE_JSON = (
    "data/processed/perlmutter/physical_architecture_dse.json"
)
NATIVE_ROTATION_PLATFORMS_JSON = (
    "data/processed/perlmutter/native_rotation_platform_envelopes.json"
)
QUALITY_QUALIFIED_JSON = (
    "data/processed/perlmutter/quality_qualified_target_map.json"
)
FINITE_SHOT_JSON = (
    "data/processed/perlmutter/finite_shot_quality_sensitivity.json"
)
FT_RELIABILITY_JSON = (
    "data/processed/perlmutter/ft_reliability_and_space_budget.json"
)
JOINT_DSE_JSON = (
    "data/processed/perlmutter/joint_bottleneck_phase_map.json"
)
ROOFLINE_NATIVE_STRESS_JSON = (
    "data/processed/perlmutter/roofline_native_stress.json"
)
ROOFLINE_NATIVE_STRESS_CSV = (
    "data/processed/perlmutter/roofline_native_stress.csv"
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
DIRECT_STRONG_8_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_direct32_strong_8n_32g_7104_20260711082639_summary.json"
)
DIRECT1_SPLIT_TAG = "20260711213724"
LOW_GPU_DIRECT_TAG = "20260712091240"
DIRECT_STRONG_1_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_direct1_strong_1g_7104_{}_summary.json".format(DIRECT1_SPLIT_TAG)
)
DIRECT_STRONG_4_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_direct4_strong_1n_4g_7104_{}_summary.json".format(LOW_GPU_DIRECT_TAG)
)
DIRECT_STRONG_8GPU_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_direct8_strong_2n_8g_7104_{}_summary.json".format(LOW_GPU_DIRECT_TAG)
)
DIRECT_STRONG_16GPU_SUMMARY_JSON = (
    "data/processed/perlmutter/"
    "practical_suite_direct16_strong_4n_16g_7104_{}_summary.json".format(LOW_GPU_DIRECT_TAG)
)
WEAK_SCALING_RUNS = [
    {
        "label": "1 GPU context",
        "nodes": 0.25,
        "gpus": 1,
        "cases": 190,
        "elapsed_sec": 1702,
        "summary": ONE_GPU_PILOT_SUMMARY_JSON,
        "kind": "context",
    },
    {
        "label": "1 node context",
        "nodes": 1,
        "gpus": 4,
        "cases": 190,
        "elapsed_sec": 419,
        "summary": STRONG_NATIVE_1NODE_SUMMARY_JSON,
        "kind": "context",
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
        "kind": "context",
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
        "kind": "context",
    },
    {
        "label": "8 nodes",
        "nodes": 8,
        "gpus": 32,
        "cases": 888,
        "elapsed_sec": 765,
        "summary": SCALE_LARGE_8_SUMMARY_JSON,
        "kind": "context",
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
        "label": "1 GPU",
        "nodes": 0.25,
        "gpus": 1,
        "cases": 7104,
        "summary": DIRECT_STRONG_1_SUMMARY_JSON,
        "accounting": (
            "data/raw/perlmutter/accounting/"
            "sacct_practical_suite_direct1_strong_1g_7104_{}.txt".format(DIRECT1_SPLIT_TAG)
        ),
        "elapsed_mode": "sum_array_tasks",
        "kind": "fixed",
    },
    {
        "label": "1 node",
        "nodes": 1,
        "gpus": 4,
        "cases": 7104,
        "summary": DIRECT_STRONG_4_SUMMARY_JSON,
        "accounting": (
            "data/raw/perlmutter/accounting/"
            "sacct_practical_suite_direct4_strong_1n_4g_7104_{}.txt".format(LOW_GPU_DIRECT_TAG)
        ),
        "kind": "fixed",
    },
    {
        "label": "2 nodes",
        "nodes": 2,
        "gpus": 8,
        "cases": 7104,
        "summary": DIRECT_STRONG_8GPU_SUMMARY_JSON,
        "accounting": (
            "data/raw/perlmutter/accounting/"
            "sacct_practical_suite_direct8_strong_2n_8g_7104_{}.txt".format(LOW_GPU_DIRECT_TAG)
        ),
        "kind": "fixed",
    },
    {
        "label": "4 nodes",
        "nodes": 4,
        "gpus": 16,
        "cases": 7104,
        "summary": DIRECT_STRONG_16GPU_SUMMARY_JSON,
        "accounting": (
            "data/raw/perlmutter/accounting/"
            "sacct_practical_suite_direct16_strong_4n_16g_7104_{}.txt".format(LOW_GPU_DIRECT_TAG)
        ),
        "kind": "fixed",
    },
    {
        "label": "8 nodes",
        "nodes": 8,
        "gpus": 32,
        "cases": 7104,
        "elapsed_sec": 2894,
        "summary": DIRECT_STRONG_8_SUMMARY_JSON,
        "accounting": (
            "data/raw/perlmutter/accounting/"
            "sacct_practical_suite_direct32_strong_8n_32g_7104_20260711082639.txt"
        ),
        "kind": "fixed",
    },
    {
        "label": "16 nodes",
        "nodes": 16,
        "gpus": 64,
        "cases": 7104,
        "elapsed_sec": 1713,
        "summary": SCALE_STRONG_16_SUMMARY_JSON,
        "accounting": "data/raw/perlmutter/accounting/sacct_practical_suite_55731032_scale_16n_64g.txt",
        "kind": "fixed",
    },
    {
        "label": "32 nodes",
        "nodes": 32,
        "gpus": 128,
        "cases": 7104,
        "elapsed_sec": 954,
        "summary": SCALE_STRONG_32_SUMMARY_JSON,
        "accounting": "data/raw/perlmutter/accounting/sacct_practical_suite_55731033_scale_32n_128g.txt",
        "kind": "fixed",
    },
    {
        "label": "64 nodes",
        "nodes": 64,
        "gpus": 256,
        "cases": 7104,
        "elapsed_sec": 418,
        "summary": SCALE_STRONG_64_SUMMARY_JSON,
        "accounting": "data/raw/perlmutter/accounting/sacct_practical_suite_55731034_scale_64n_256g.txt",
        "kind": "fixed",
    },
]


def ensure_fig_dir():
    os.makedirs(FIG_DIR, exist_ok=True)


def apply_paper_style():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Liberation Serif"],
            "mathtext.fontset": "stix",
            "font.size": FIGURE_FONT,
            "axes.labelsize": FIGURE_FONT,
            "axes.titlesize": FIGURE_FONT,
            "axes.titleweight": "bold",
            "xtick.labelsize": FIGURE_TICK_FONT,
            "ytick.labelsize": FIGURE_TICK_FONT,
            "legend.fontsize": FIGURE_TICK_FONT,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.25,
            "lines.markersize": 3.9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def style_axis(ax, grid="both"):
    ax.tick_params(axis="both", labelsize=FIGURE_TICK_FONT, pad=1.2, width=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        axis = "both" if grid == "both" else grid
        ax.grid(axis=axis, which="both", linestyle=":", linewidth=0.45, color="#B9B9B9")


def compact_tick(value, _position=None):
    """Keep logarithmic ticks readable without reduced-size exponents."""
    if value >= 1.0e6:
        return "{:g}M".format(value / 1.0e6)
    if value >= 1.0e3:
        return "{:g}k".format(value / 1.0e3)
    if value >= 1.0:
        return "{:g}".format(value)
    return "{:.2g}".format(value)


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


def legend_marker(color, marker="o"):
    return Line2D(
        [0],
        [0],
        marker=marker,
        color="none",
        markerfacecolor=color,
        markeredgecolor="none",
        markersize=4.5,
    )


def read_csv(path):
    with open(os.path.join(ROOT, path), newline="") as f:
        return list(csv.DictReader(f))


def projection_components_ms(row):
    components = projected_components_sec(row, DEFAULT_FIGURE_PROJECTION)
    return {
        "gate_ms": components["gate_sec"] * 1.0e3,
        "decode_ms": components["decode_sec"] * 1.0e3,
        "critical_gate_ms": components["critical_gate_sec"] * 1.0e3,
        "critical_decode_ms": components["critical_decode_sec"] * 1.0e3,
        "host_io_ms": components["host_io_sec"] * 1.0e3,
        "queue_ms": components["queue_sec"] * 1.0e3,
        "controller_ms": components["controller_sec"] * 1.0e3,
        "context_ms": components["context_sec"] * 1.0e3,
        "ctrl_context_ms": (components["controller_sec"] + components["context_sec"]) * 1.0e3,
        "total_ms": components["total_sec"] * 1.0e3,
        "twoq_gate_ms": components["twoq_gate_sec"] * 1.0e3,
        "qpu_energy_j": components["qpu_energy_j"],
        "reference_energy_j": components["reference_energy_j"],
    }


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


def arrow(ax, start, end, color="#4A4A4A", lw=1.1, linestyle="-"):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": "->",
            "lw": lw,
            "linestyle": linestyle,
            "color": color,
            "shrinkA": 3,
            "shrinkB": 3,
        },
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
        COLORS["blue"],
        COLORS["blue"],
        COLORS["green"],
        COLORS["blue"],
        COLORS["teal"],
        COLORS["red"],
    ]
    markers = ["o", "o", "D", "o", "s", "^"]
    y = np.arange(len(labels)) * 1.28
    fig, ax = plt.subplots(figsize=(INTRO_THRESHOLD_WIDTH, 2.42))
    left = 10.0
    ax.hlines(y, left, values, color=colors, linewidth=3.0, alpha=0.90)
    for value, yi, color, marker in zip(values, y, colors, markers):
        ax.scatter(
            value,
            yi,
            s=34,
            marker=marker,
            color=color,
            edgecolors="#222222",
            linewidths=0.55,
            zorder=3,
        )
    for yi, value in zip(y, values):
        if value > 1.0e5:
            text_offset = (-7, 0)
            text_ha = "right"
        else:
            text_offset = (7, 0)
            text_ha = "left"
        ax.annotate(
            "{:,.0f}x".format(value),
            xy=(value, yi),
            xytext=text_offset,
            textcoords="offset points",
            va="center",
            ha=text_ha,
            fontsize=FIGURE_TICK_FONT,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 0.2},
        )
    ax.set_xscale("log")
    ax.set_xticks((10, 100, 1000, 10000, 100000, 1000000))
    ax.set_xticklabels(("10", "100", "1k", "10k", "100k", "1M"))
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.tick_params(axis="y", labelsize=FIGURE_TICK_FONT)
    for tick in ax.get_yticklabels():
        tick.set_linespacing(1.02)
    ax.invert_yaxis()
    ax.set_xlabel("Required circuit speedup vs. native HPC (x)", labelpad=1.0)
    ax.set_xlim(10, 1.05e6)
    style_axis(ax, grid=None)
    ax.grid(axis="x", which="major", linestyle=":", linewidth=0.50, color="#B9B9B9")
    add_top_legend(
        fig,
        [
            legend_marker(COLORS["blue"], marker="o"),
            legend_marker(COLORS["teal"], marker="s"),
            legend_marker(COLORS["red"], marker="^"),
            legend_marker(COLORS["green"], marker="D"),
        ],
        ["ML", "Chem.", "Opt.", "Sim."],
        ncol=4,
        y=0.995,
        fontsize=FIGURE_TICK_FONT,
    )
    path = os.path.join(FIG_DIR, "intro_threshold_summary.pdf")
    fig.subplots_adjust(left=0.31, right=0.98, bottom=0.21, top=0.82)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_design_overview():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 3.28))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def step_badge(x, y, text):
        circle = plt.Circle((x, y), 0.031, facecolor="white", edgecolor=COLORS["dark"], linewidth=0.8, zorder=4)
        ax.add_patch(circle)
        ax.text(x, y - 0.001, text, ha="center", va="center", fontsize=FIGURE_TICK_FONT, weight="bold", color=COLORS["dark"], zorder=5)

    ax.text(0.04, 0.955, "Quality-first critical-path inversion", fontsize=8.7, weight="bold", color=COLORS["dark"])

    draw_box(
        ax,
        (0.07, 0.79),
        0.86,
        0.105,
        "Shared record\ninput, seed, native deadline, quality tolerance",
        COLORS["dark"],
        fontsize=FIGURE_TICK_FONT,
    )
    step_badge(0.085, 0.895, "1")

    draw_box(ax, (0.07, 0.60), 0.36, 0.125, "Native HPC\ntime + output quality", COLORS["blue"], fontsize=FIGURE_TICK_FONT)
    draw_box(ax, (0.57, 0.60), 0.36, 0.125, "Circuit evidence\nquality, gates, shots, loop", COLORS["orange"], fontsize=FIGURE_TICK_FONT)
    step_badge(0.085, 0.725, "2")
    step_badge(0.585, 0.725, "3")
    arrow(ax, (0.30, 0.79), (0.25, 0.725), lw=0.9)
    arrow(ax, (0.70, 0.79), (0.75, 0.725), lw=0.9)

    draw_box(ax, (0.17, 0.395), 0.66, 0.15, "Finite-shot quality gate\nsame-record output + full loop\ntolerance met; pass rate at least 0.9", COLORS["teal"], fontsize=FIGURE_TICK_FONT)
    step_badge(0.185, 0.545, "4")
    arrow(ax, (0.25, 0.60), (0.39, 0.545), lw=0.9)
    arrow(ax, (0.75, 0.60), (0.61, 0.545), lw=0.9)

    draw_box(ax, (0.055, 0.22), 0.39, 0.12, "FAIL: quality\nconditional timing only", COLORS["gray"], fontsize=FIGURE_TICK_FONT)
    draw_box(ax, (0.555, 0.22), 0.39, 0.12, "PASS: quality\nschedule + reliability\nphysical space", COLORS["green"], fontsize=FIGURE_TICK_FONT)
    arrow(ax, (0.40, 0.395), (0.24, 0.34), color=COLORS["gray"], lw=0.8, linestyle="--")
    arrow(ax, (0.60, 0.395), (0.76, 0.34), color=COLORS["green"], lw=0.9)

    draw_box(ax, (0.09, 0.075), 0.36, 0.105, "Conditional\nlower bound", "#F3F3F3", text_color=COLORS["dark"], fontsize=FIGURE_TICK_FONT)
    draw_box(ax, (0.53, 0.055), 0.41, 0.125, "Architecture diagnosis\nnext upgrade + required gain\nfollowing bottleneck", "#F3F3F3", text_color=COLORS["dark"], fontsize=FIGURE_TICK_FONT)
    step_badge(0.105, 0.18, "5")
    arrow(ax, (0.24, 0.22), (0.27, 0.18), color=COLORS["gray"], lw=0.75, linestyle="--")
    arrow(ax, (0.76, 0.22), (0.74, 0.18), color=COLORS["green"], lw=0.85)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    path = os.path.join(FIG_DIR, "design_overview.pdf")
    fig.subplots_adjust(left=0.02, right=0.985, bottom=0.04, top=0.97)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_feedback_aggregator_architecture():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.24))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.035,
        0.94,
        "Dependency-aware near-QPU aggregation",
        fontsize=7.1,
        weight="bold",
        color=COLORS["dark"],
    )
    ax.text(
        0.035,
        0.885,
        "only independent results in the same epoch share a host round",
        fontsize=5.05,
        color=COLORS["dark"],
    )

    draw_box(
        ax,
        (0.035, 0.55),
        0.17,
        0.20,
        "QPU result\nlanes\n$\\langle g,v\\rangle$",
        COLORS["orange"],
        fontsize=5.2,
    )
    draw_box(
        ax,
        (0.255, 0.58),
        0.19,
        0.14,
        "Tag FIFO\n$\\langle epoch,group,v\\rangle$",
        COLORS["teal"],
        fontsize=4.8,
    )
    draw_box(
        ax,
        (0.50, 0.58),
        0.18,
        0.14,
        "Epoch table\nready / serial / $n_{exp}$",
        COLORS["purple"],
        fontsize=5.0,
    )
    draw_box(
        ax,
        (0.735, 0.55),
        0.23,
        0.20,
        "Reduction banks\nhash + RR arbitration\n$B=64$: 2 KiB / bank",
        COLORS["green"],
        fontsize=4.85,
    )
    arrow(ax, (0.205, 0.65), (0.255, 0.65), lw=0.85)
    arrow(ax, (0.445, 0.65), (0.50, 0.65), lw=0.85)
    arrow(ax, (0.68, 0.65), (0.735, 0.65), lw=0.85)

    draw_box(
        ax,
        (0.035, 0.18),
        0.25,
        0.15,
        "Candidate FIFO\npre-staged work",
        COLORS["blue"],
        fontsize=4.9,
    )
    draw_box(
        ax,
        (0.46, 0.18),
        0.22,
        0.15,
        "Compact-result FIFO\n$\\langle epoch,count,sum\\rangle$",
        COLORS["red"],
        fontsize=4.8,
    )
    draw_box(
        ax,
        (0.765, 0.18),
        0.20,
        0.15,
        "Host optimizer\n/ application",
        COLORS["dark"],
        fontsize=5.0,
    )
    arrow(ax, (0.82, 0.55), (0.61, 0.33), lw=0.85)
    arrow(ax, (0.68, 0.255), (0.765, 0.255), lw=0.85)
    arrow(ax, (0.16, 0.33), (0.12, 0.55), lw=0.85)

    ax.annotate(
        "",
        xy=(0.17, 0.18),
        xytext=(0.86, 0.18),
        arrowprops={
            "arrowstyle": "->",
            "lw": 0.75,
            "color": COLORS["dark"],
            "connectionstyle": "arc3,rad=-0.24",
            "shrinkA": 3,
            "shrinkB": 3,
        },
    )

    ax.annotate(
        "",
        xy=(0.18, 0.56),
        xytext=(0.51, 0.34),
        arrowprops={
            "arrowstyle": "->",
            "lw": 0.75,
            "linestyle": "--",
            "color": COLORS["red"],
            "shrinkA": 3,
            "shrinkB": 3,
        },
    )
    ax.text(
        0.30,
        0.40,
        "full / mismatch: backpressure",
        fontsize=4.7,
        color=COLORS["red"],
        ha="center",
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.35},
    )
    ax.text(
        0.57,
        0.025,
        "next epoch; serial dependency forces $B=1$",
        fontsize=4.8,
        color=COLORS["dark"],
        ha="center",
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.35},
    )

    path = os.path.join(FIG_DIR, "feedback_aggregator_architecture.pdf")
    fig.subplots_adjust(left=0.015, right=0.985, bottom=0.035, top=0.98)
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
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.86))
    label_keyword = (
        "tick_labels" if "tick_labels" in inspect.signature(ax.boxplot).parameters else "labels"
    )
    box = ax.boxplot(
        [kernel, vqc],
        patch_artist=True,
        widths=0.55,
        showfliers=False,
        **{label_keyword: ["QKernel", "QNN/VQC"]}
    )
    colors = [COLORS["blue"], COLORS["orange"]]
    for patch, color in zip(box["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.82)
    for median in box["medians"]:
        median.set_color("black")
        median.set_linewidth(1.2)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(compact_tick))
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
        legend_marker(COLORS["blue"], "o"),
        legend_marker(COLORS["teal"], "s"),
        legend_marker(COLORS["red"], "D"),
        legend_marker(COLORS["green"], "^"),
    ]
    ax.axis("off")
    fig.legend(
        handles,
        ["ML", "Chem.", "Opt.", "Sim."],
        ncol=2,
        loc="center",
        frameon=False,
        fontsize=FIGURE_TICK_FONT,
        handletextpad=0.25,
        columnspacing=0.9,
    )
    path = os.path.join(FIG_DIR, "practical_suite_legend.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_digits_quality_runtime():
    rows = read_csv("data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv")
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.70))
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
        ("ml", "ML", COLORS["blue"], "o", 0.02),
        ("chemistry", "Chem.", COLORS["teal"], "s", 0.01),
        ("optimization", "Opt.", COLORS["red"], "D", 0.02),
        ("simulation", "Sim.", COLORS["green"], "^", 0.01),
    ]

    series = []
    for workload, label, color, marker, tolerance in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        speed = np.array([float(row["speedup_required"]) for row in subset])
        quality = np.array([max(0.0, float(row["quality_gap"])) for row in subset])
        sorted_speed = np.sort(speed)
        cdf = np.arange(1, sorted_speed.size + 1) / float(sorted_speed.size)
        series.append((label, color, marker, speed, quality, sorted_speed, cdf))

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.74))
    for label, color, marker, speed, quality, sorted_speed, cdf in series:
        ax.scatter(
            speed,
            quality,
            s=9,
            alpha=0.26,
            color=color,
            marker=marker,
            edgecolors="none",
            label=label,
        )
        ax.scatter(
            [np.median(speed)],
            [np.median(quality)],
            s=42,
            color=color,
            marker=marker,
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
    for label, color, marker, speed, quality, sorted_speed, cdf in series:
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
    ax_gap.set_ylabel("$\\Delta Q$\n(to native)", labelpad=0.5)
    style_axis(ax_gap, grid="y")
    ax_gap.tick_params(axis="x", labelsize=5.8, pad=1.0)
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
    fig.subplots_adjust(top=0.80, bottom=0.23, left=0.34, right=0.98)
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
    ax_tax.set_xlim(0.0, 104.0)
    ax_tax.set_xlabel("Case share (%)")
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
    fig.subplots_adjust(top=0.80, bottom=0.24, left=0.27, right=0.96)
    fraction_path = os.path.join(FIG_DIR, "quality_bottleneck_fraction.pdf")
    save_canvas(fig, fraction_path)

    return [gap_path, fraction_path]


def load_summary(rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def parse_slurm_elapsed(text):
    if not text:
        return None
    value = text.strip()
    if not value or value == "Unknown":
        return None
    days = 0
    if "-" in value:
        day_text, value = value.split("-", 1)
        days = int(day_text)
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    else:
        return None
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def accounting_elapsed_seconds(rel_path):
    if not rel_path:
        return None
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    with open(path, newline="") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            job_id = row.get("JobID", "")
            state = row.get("State", "")
            if "." in job_id:
                continue
            if state != "COMPLETED":
                continue
            return parse_slurm_elapsed(row.get("Elapsed", ""))
    return None


def accounting_sum_array_task_seconds(rel_path):
    if not rel_path:
        return None
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    total = 0
    count = 0
    with open(path, newline="") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            job_id = row.get("JobID", "")
            state = row.get("State", "")
            if "." in job_id or "_" not in job_id:
                continue
            if state != "COMPLETED":
                continue
            elapsed = parse_slurm_elapsed(row.get("Elapsed", ""))
            if elapsed is None:
                continue
            total += elapsed
            count += 1
    return total if count else None


def run_elapsed_seconds(run):
    if run.get("elapsed_mode") == "sum_array_tasks":
        summed = accounting_sum_array_task_seconds(run.get("accounting"))
        if summed is not None:
            return summed
    from_accounting = accounting_elapsed_seconds(run.get("accounting"))
    if from_accounting is not None:
        return from_accounting
    return run.get("elapsed_sec")


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
    ax.yaxis.set_major_formatter(FuncFormatter(compact_tick))
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

    nsys = profile.get("nsys_kernel_summary", {})
    dmon = profile.get("dmon_summary", {})
    gpu_frac = float(nsys.get("gpu_kernel_runtime_fraction") or 0.0)
    host_frac = max(0.0, 1.0 - gpu_frac)
    tensor_frac = float(nsys.get("tensor_kernel_time_fraction") or 0.0)
    other_kernel_frac = max(0.0, 1.0 - tensor_frac)

    fig, axes = plt.subplots(1, 2, figsize=(COLUMN_WIDTH, 1.98), gridspec_kw={"wspace": 0.52})
    ax = axes[0]
    speed_rows = [
        ("Previous\nsuite", float(gate["previous_required_speedup_median"]), COLORS["gray"]),
        ("Combined\nselected", float(gate["combined_required_speedup_median"]), COLORS["blue"]),
        ("GPU prod.\nonly", float(gate["production_required_speedup_median"]), COLORS["orange"]),
    ]
    y_speed = np.arange(len(speed_rows))
    ax.hlines(y_speed, 10.0, [row[1] for row in speed_rows], color="#BDBDBD", linewidth=1.5, zorder=1)
    for ridx, (row_label, speedup, color) in enumerate(speed_rows):
        ax.scatter(speedup, ridx, s=20, color=color, edgecolor=COLORS["dark"], linewidth=0.35, zorder=3)
        ax.text(
            min(speedup * 1.10, 1.55e4),
            ridx,
            "{:,.0f}x".format(speedup),
            va="center",
            ha="left",
            fontsize=5.45,
            color=COLORS["dark"],
        )
    ax.set_yticks(y_speed)
    ax.set_yticklabels([row[0] for row in speed_rows])
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(compact_tick))
    ax.set_xlim(10.0, 2.0e4)
    ax.set_xticks([10, 100, 1000, 10000])
    ax.set_xticklabels(["$10$", "$10^2$", "$10^3$", "$10^4$"])
    ax.set_xlabel("Median required speedup (x)")
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
        profile_handles.get("Host/orch."),
        profile_handles.get("GPU kernels"),
        profile_handles.get("Other"),
        profile_handles.get("Tensor fam."),
    ]
    legend_labels = [
        "Host/orch.",
        "GPU kernels",
        "Other kernels",
        "Tensor fam.",
    ]
    pairs = [(h, l) for h, l in zip(legend_handles, legend_labels) if h is not None]
    fig.legend(
        [h for h, _ in pairs],
        [l for _, l in pairs],
        ncol=4,
        loc="upper center",
        bbox_to_anchor=(0.58, 1.01),
        frameon=False,
        fontsize=5.05,
        handlelength=0.95,
        handletextpad=0.20,
        columnspacing=0.55,
    )
    fig.subplots_adjust(left=0.22, right=0.98, bottom=0.23, top=0.76, wspace=0.46)
    path = os.path.join(FIG_DIR, "ml_native_profile_combined.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def figure_roofline_native_stress():
    data = load_summary(ROOFLINE_NATIVE_STRESS_JSON)
    if data is None:
        return None

    workloads = [
        ("ml", "ML", COLORS["blue"]),
        ("chemistry", "Chem.", COLORS["teal"]),
        ("optimization", "Opt.", COLORS["red"]),
        ("simulation", "Sim.", COLORS["green"]),
    ]
    labels = [label for _workload, label, _color in workloads]
    colors = [color for _workload, _label, color in workloads]
    shrink = np.array(
        [
            data["by_workload"][workload][
                "a100_launch_floor_10us_deadline_shrink_median_x"
            ]
            for workload, _label, _color in workloads
        ]
    )
    measured_ratio = np.array(
        [
            data["by_workload"][workload][
                "measured_deadline_projected_ratio_median_x"
            ]
            for workload, _label, _color in workloads
        ]
    )
    stressed_ratio = np.array(
        [
            data["by_workload"][workload][
                "a100_launch_floor_10us_projected_ratio_median_x"
            ]
            for workload, _label, _color in workloads
        ]
    )

    y = np.arange(len(workloads))
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=COLORS["dark"],
            markeredgecolor="#222222",
            markersize=3.8,
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            color="none",
            markerfacecolor=COLORS["dark"],
            markeredgecolor="#222222",
            markersize=3.8,
        ),
    ]

    legend_fig, legend_ax = plt.subplots(figsize=(COLUMN_WIDTH, 0.22))
    legend_ax.axis("off")
    legend_fig.legend(
        handles,
        ["measured native", "roofline + 10 us"],
        loc="center",
        ncol=2,
        frameon=False,
        fontsize=5.8,
        handletextpad=0.25,
        columnspacing=0.9,
    )
    legend_path = os.path.join(FIG_DIR, "roofline_native_stress_legend.pdf")
    legend_fig.savefig(legend_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(legend_fig)

    fig, ax_shrink = plt.subplots(figsize=(COLUMN_WIDTH, 2.08))
    normalized_floor = 1.0 / shrink
    for ypos, floor, value, color in zip(y, normalized_floor, shrink, colors):
        ax_shrink.hlines(ypos, floor, 1.0, color=color, linewidth=2.1, alpha=0.82, zorder=2)
        ax_shrink.scatter(
            1.0,
            ypos,
            marker="o",
            s=25,
            facecolor="white",
            edgecolor="#303030",
            linewidth=0.7,
            zorder=3,
        )
        ax_shrink.scatter(
            floor,
            ypos,
            marker="s",
            s=28,
            color=color,
            edgecolor="#303030",
            linewidth=0.55,
            zorder=4,
        )
        text = "{:.0f}x".format(value) if value >= 10.0 else "{:.1f}x".format(value)
        ax_shrink.annotate(
            text,
            (floor, ypos),
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=FIGURE_TICK_FONT,
            color=COLORS["dark"],
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 0.25},
        )
    ax_shrink.axvline(1.0, color="#555555", linestyle=":", linewidth=0.7, zorder=1)
    ax_shrink.set_xscale("log")
    ax_shrink.set_xlim(3.0e-3, 1.45)
    ax_shrink.set_xticks([0.005, 0.01, 0.1, 1.0])
    ax_shrink.set_xticklabels(["0.005", "0.01", "0.1", "1"])
    ax_shrink.set_yticks(y)
    ax_shrink.set_yticklabels(labels)
    ax_shrink.invert_yaxis()
    ax_shrink.set_xlabel("Runtime lower bound / measured runtime (x)", labelpad=1.0)
    style_axis(ax_shrink, grid="x")
    ax_shrink.tick_params(axis="both", labelsize=FIGURE_TICK_FONT, pad=1.0)
    add_top_legend(
        fig,
        [
            Line2D([0], [0], marker="o", linestyle="None", markerfacecolor="white", markeredgecolor="#303030", markersize=4.2),
            Line2D([0], [0], marker="s", linestyle="None", markerfacecolor=COLORS["gray"], markeredgecolor="#303030", markersize=4.2),
        ],
        ["Measured runtime", "Roofline lower bound"],
        ncol=2,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(left=0.22, right=0.98, bottom=0.25, top=0.73)
    shrink_path = os.path.join(FIG_DIR, "roofline_deadline_shrink.pdf")
    save_canvas(fig, shrink_path)

    fig, ax_ratio = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.50))
    for ypos, before, after, color in zip(y, measured_ratio, stressed_ratio, colors):
        left = max(1.0e-3, min(before, after))
        right = max(before, after)
        ax_ratio.hlines(ypos, left, right, color=color, linewidth=1.35, alpha=0.68)
        ax_ratio.scatter(
            before,
            ypos,
            marker="o",
            s=25,
            color=color,
            edgecolor="#222222",
            linewidth=0.45,
            zorder=3,
        )
        ax_ratio.scatter(
            after,
            ypos,
            marker="s",
            s=26,
            color=color,
            edgecolor="#222222",
            linewidth=0.45,
            zorder=3,
        )
    ax_ratio.axvspan(1.0e-3, 1.0, color="#EDF6EF", zorder=0)
    ax_ratio.axvline(1.0, color=COLORS["dark"], linestyle="--", linewidth=0.75)
    ax_ratio.set_xscale("log")
    ax_ratio.set_xlim(1.0e-3, 1.0e4)
    ax_ratio.set_xticks([1.0e-2, 1.0, 1.0e2, 1.0e4])
    ax_ratio.set_xticklabels(["0.01", "1", "$10^2$", "$10^4$"])
    ax_ratio.set_yticks(y)
    ax_ratio.set_yticklabels(labels)
    ax_ratio.invert_yaxis()
    ax_ratio.set_xlabel("Projected / native (x)", labelpad=1.0)
    style_axis(ax_ratio, grid="x")
    ax_ratio.tick_params(axis="both", labelsize=5.7, pad=1.0)
    fig.subplots_adjust(left=0.29, right=0.98, bottom=0.27, top=0.97)
    ratio_path = os.path.join(FIG_DIR, "roofline_runtime_shift.pdf")
    save_canvas(fig, ratio_path)
    return [legend_path, shrink_path, ratio_path]


def figure_workload_growth():
    if not (
        os.path.exists(os.path.join(ROOT, SCALE_WEAK_16_SUMMARY_CSV))
        and os.path.exists(os.path.join(ROOT, SCALE_WEAK_32_SUMMARY_CSV))
        and os.path.exists(os.path.join(ROOT, SCALE_WEAK_64_SUMMARY_CSV))
    ):
        return None

    points = [
        ("64 GPUs", 64, 562, SCALE_WEAK_16_SUMMARY_CSV),
        ("128 GPUs", 128, 419, SCALE_WEAK_32_SUMMARY_CSV),
        ("256 GPUs", 256, 576, SCALE_WEAK_64_SUMMARY_CSV),
    ]
    workloads = [
        ("ml", "ML", COLORS["blue"]),
        ("chemistry", "Chem.", COLORS["teal"]),
        ("optimization", "Opt.", COLORS["red"]),
        ("simulation", "Sim.", COLORS["green"]),
    ]
    rows_by_run = [read_csv(point[3]) for point in points]

    def fmt_count(value):
        if value >= 1000:
            return "{:.1f}K".format(value / 1000.0)
        return "{}".format(int(value))

    counts_by_run = []
    for rows in rows_by_run:
        run_counts = []
        for workload, _label, _color in workloads:
            run_counts.append(
                sum(
                    1
                    for row in rows
                    if row["workload"] == workload and row.get("status") == "ok"
                )
            )
        counts_by_run.append(run_counts)

    totals = [sum(counts) for counts in counts_by_run]
    max_total = max(totals)

    payload_rows = rows_by_run[-1]
    payload = []
    for workload, label, color in workloads:
        subset = [
            row
            for row in payload_rows
            if row["workload"] == workload and row.get("status", "ok") == "ok"
        ]
        evals = np.array([float(row["circuit_evaluations"]) for row in subset], dtype=float)
        twoq = np.array([float(row["two_qubit_gates"]) for row in subset], dtype=float)
        payload.append(
            {
                "label": label,
                "color": color,
                "eval_median": float(np.median(evals)),
                "eval_p90": float(np.percentile(evals, 90)),
                "twoq_median": float(np.median(twoq)),
                "twoq_p90": float(np.percentile(twoq, 90)),
            }
        )

    fig, (ax_vol, ax_payload) = plt.subplots(
        1,
        2,
        figsize=(COLUMN_WIDTH, 2.05),
        gridspec_kw={"width_ratios": [1.18, 1.02], "wspace": 0.27},
    )

    y = np.arange(len(points))
    left = np.zeros(len(points))
    handles = []
    for widx, (_workload, label, color) in enumerate(workloads):
        values = np.array([counts[widx] for counts in counts_by_run], dtype=float)
        ax_vol.barh(
            y,
            values,
            left=left,
            height=0.52,
            color=color,
            alpha=0.88,
            edgecolor="white",
            linewidth=0.55,
        )
        handles.append(Rectangle((0, 0), 1, 1, facecolor=color, alpha=0.88))
        for ypos, value, base in zip(y, values, left):
            if value >= max_total * 0.080:
                ax_vol.text(
                    base + value / 2.0,
                    ypos,
                    fmt_count(value),
                    va="center",
                    ha="center",
                    fontsize=5.25,
                    color="white",
                    fontweight="bold",
                )
        left += values

    ax_vol.set_yticks(y)
    ax_vol.set_yticklabels([label.replace(" GPUs", "G") for label, _g, _t, _p in points])
    ax_vol.invert_yaxis()
    ax_vol.set_xlim(0, max_total * 1.16)
    ax_vol.set_xticks([0, max_total / 2.0, max_total])
    ax_vol.set_xticklabels(["0", fmt_count(max_total / 2.0), fmt_count(max_total)])
    ax_vol.set_xlabel("Completed records", labelpad=1.0, fontsize=6.3)
    ax_vol.tick_params(axis="both", labelsize=6.0, pad=1.0)
    for idx, total in enumerate(totals):
        ax_vol.text(
            total + max_total * 0.025,
            idx,
            fmt_count(total),
            va="center",
            ha="left",
            fontsize=5.9,
            color=COLORS["dark"],
        )
    style_axis(ax_vol, grid="x")

    y_payload = np.arange(len(payload))
    ax_payload.set_xscale("log")
    ax_payload.axvspan(0.8, 10.0, facecolor="#EDF6EF", edgecolor="none", zorder=0)
    ax_payload.axvspan(10.0, 1.0e2, facecolor="#F6F1E8", edgecolor="none", zorder=0)
    ax_payload.axvspan(1.0e2, 5.0e3, facecolor="#F8EEEE", edgecolor="none", zorder=0)
    for ypos, item in zip(y_payload, payload):
        ax_payload.hlines(
            ypos - 0.10,
            item["eval_median"],
            item["eval_p90"],
            color=COLORS["purple"],
            linewidth=1.35,
            alpha=0.68,
            zorder=2,
        )
        ax_payload.hlines(
            ypos + 0.10,
            item["twoq_median"],
            item["twoq_p90"],
            color=COLORS["orange"],
            linewidth=1.35,
            alpha=0.68,
            zorder=2,
        )
        ax_payload.scatter(
            item["eval_median"],
            ypos - 0.10,
            marker="s",
            s=18,
            color=COLORS["purple"],
            edgecolor=COLORS["dark"],
            linewidth=0.30,
            zorder=3,
        )
        ax_payload.scatter(
            item["twoq_median"],
            ypos + 0.10,
            marker="o",
            s=18,
            color=COLORS["orange"],
            edgecolor=COLORS["dark"],
            linewidth=0.30,
            zorder=3,
        )
    ax_payload.set_yticks(y_payload)
    ax_payload.set_yticklabels([item["label"] for item in payload])
    ax_payload.invert_yaxis()
    ax_payload.set_xlim(0.8, 5.0e3)
    ax_payload.set_xticks([1, 10, 100, 1000])
    ax_payload.set_xticklabels(["1", "10", "$10^2$", "$10^3$"])
    ax_payload.set_xlabel("Median to p90 count", labelpad=1.0, fontsize=6.3)
    ax_payload.tick_params(axis="both", labelsize=6.0, pad=1.0)
    style_axis(ax_payload, grid="x")

    legend_handles = handles + [
        Line2D(
            [0],
            [0],
            marker="s",
            color=COLORS["purple"],
            markerfacecolor=COLORS["purple"],
            markeredgecolor=COLORS["dark"],
            linewidth=1.0,
            markersize=3.2,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color=COLORS["orange"],
            markerfacecolor=COLORS["orange"],
            markeredgecolor=COLORS["dark"],
            linewidth=1.0,
            markersize=3.2,
        ),
    ]
    legend_labels = [label for _workload, label, _color in workloads] + ["$N_e$", "2Q"]
    fig.legend(
        legend_handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.52, 1.03),
        ncol=6,
        frameon=False,
        fontsize=5.35,
        handlelength=0.82,
        handletextpad=0.22,
        columnspacing=0.42,
    )

    fig.subplots_adjust(left=0.15, right=0.985, bottom=0.20, top=0.82)
    coverage_path = os.path.join(FIG_DIR, "workload_growth_coverage.pdf")
    fig.savefig(coverage_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return coverage_path


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
        ("Gate", "gate_ms", COLORS["blue"], "o"),
        ("Decode", "critical_decode_ms", COLORS["purple"], "s"),
        ("Host I/O", "host_io_ms", COLORS["orange"], "^"),
        ("Ctrl/ctx", "ctrl_context_ms", COLORS["teal"], "v"),
        ("Queue", "queue_ms", COLORS["gray"], "D"),
    ]

    ratios = []
    for workload, _label in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        per_case = []
        for row in subset:
            components = projection_components_ms(row)
            native_ms = max(1.0e-12, 1.0e3 * float(row["native_runtime_sec"]))
            per_case.append(
                [
                    components[key] / native_ms
                    for _label, key, _color, _marker in categories
                ]
            )
        ratios.append(np.median(np.array(per_case), axis=0))

    ratio_array = np.array(ratios)
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.66))
    y = np.arange(len(workloads))
    for ypos, values in zip(y, ratio_array):
        visible = np.maximum(1.0e-4, values)
        ax.hlines(
            ypos,
            float(np.min(visible)),
            float(np.max(visible)),
            color="#B8B8B8",
            linewidth=0.8,
            zorder=1,
        )
    for idx, (label, _key, color, marker) in enumerate(categories):
        values = np.maximum(1.0e-4, ratio_array[:, idx])
        ax.scatter(
            values,
            y,
            s=22,
            marker=marker,
            color=color,
            edgecolor="white",
            linewidth=0.65,
            zorder=3 + idx,
            label=label,
        )
    ax.axvspan(1.0e-4, 1.0, color="#EDF6EF", zorder=0)
    ax.axvline(1.0, color=COLORS["dark"], linestyle="--", linewidth=0.75, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels([label for _, label in workloads])
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlim(1.0e-4, 1.3e4)
    ax.set_xlabel("Component / native runtime (x)", labelpad=0.8)
    ax.set_xticks([1.0e-4, 1.0e-2, 1.0, 1.0e2, 1.0e4])
    ax.set_xticklabels(["$10^{-4}$", "0.01", "1", "$10^2$", "$10^4$"])
    style_axis(ax, grid="x")
    ax.tick_params(axis="both", labelsize=6.1, pad=0.8, width=0.6)
    ax.xaxis.label.set_size(6.5)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.52, 1.20),
        ncol=5,
        frameon=False,
        fontsize=5.35,
        handlelength=0.9,
        handletextpad=0.18,
        columnspacing=0.34,
        borderaxespad=0.0,
    )
    fig.subplots_adjust(left=0.18, right=0.99, bottom=0.24, top=0.79)
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


def projection_scenario_specs():
    return [
        ("conservative_surface", "Cons."),
        ("intermediate_surface", "Mid."),
        ("default_optimistic", "Def."),
        ("ldpc_future_like", "Low-OH"),
        ("aggressive_batched", "Batch"),
    ]


def projection_workload_specs():
    return [
        ("ml", "ML", COLORS["blue"], "o", "-"),
        ("chemistry", "Chem.", COLORS["teal"], "s", "--"),
        ("optimization", "Opt.", COLORS["red"], "D", "-."),
        ("simulation", "Sim.", COLORS["green"], "^", ":"),
    ]


def figure_sensitivity_bottleneck_transition():
    scenario_summary = load_summary(PROJECTION_SCENARIOS_JSON)
    if scenario_summary is None:
        return None

    workload_specs = projection_workload_specs()
    scenario_specs = projection_scenario_specs()
    by_scenario = scenario_summary.get("by_scenario", {})
    compact_scenario_labels = ["Cons.", "Mid.", "Def.", "Low", "Batch"]

    bucket_specs = [
        ("Both fail", "both", "#BDBDBD", ""),
        ("Run fail", "runtime", COLORS["blue"], "////"),
        ("Qual fail", "quality", COLORS["orange"], "\\\\"),
        ("Adv.", "advantaged", COLORS["green"], "xx"),
    ]
    x = np.arange(len(scenario_specs))
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(COLUMN_WIDTH, 1.92),
        sharex=True,
        sharey=True,
    )
    axes = axes.flatten()
    for ax, (workload, label, workload_color, _marker, _linestyle) in zip(axes, workload_specs):
        bucket_values = {key: [] for _label, key, _color, _hatch in bucket_specs}
        for scenario_id, _scenario_label in scenario_specs:
            item = by_scenario.get(scenario_id, {}).get("by_workload", {}).get(workload, {})
            runtime_pass = float(item.get("runtime_pass_fraction", 0.0))
            quality_pass = float(item.get("quality_pass_fraction", 0.0))
            advantaged = float(item.get("advantaged_fraction", 0.0))
            bucket_values["both"].append(100.0 * max(0.0, 1.0 - runtime_pass - quality_pass + advantaged))
            bucket_values["runtime"].append(100.0 * max(0.0, quality_pass - advantaged))
            bucket_values["quality"].append(100.0 * max(0.0, runtime_pass - advantaged))
            bucket_values["advantaged"].append(100.0 * max(0.0, advantaged))

        bottom = np.zeros(len(scenario_specs))
        for _bucket_label, key, color, hatch in bucket_specs:
            values = np.array(bucket_values[key])
            ax.bar(
                x,
                values,
                bottom=bottom,
                color=color,
                width=0.74,
                edgecolor="#555555",
                linewidth=0.32,
                alpha=0.86,
                hatch=hatch,
            )
            bottom += values

        ax.set_title(
            label,
            loc="left",
            fontsize=6.3,
            color=workload_color,
            fontweight="bold",
            pad=0.8,
        )
        ax.set_ylim(0.0, 100.0)
        ax.set_yticks([0, 50, 100])
        ax.set_xlim(-0.55, len(scenario_specs) - 0.45)
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.35, linestyle=":")
        ax.tick_params(axis="both", labelsize=5.8, pad=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    for ax in axes[::2]:
        ax.set_ylabel("Cases (%)", fontsize=6.0, labelpad=0.8)
    for ax in axes[2:]:
        ax.set_xticks(x)
        ax.set_xticklabels(compact_scenario_labels)
    for ax in axes[:2]:
        ax.tick_params(axis="x", labelbottom=False)

    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=color, edgecolor="#555555", hatch=hatch, alpha=0.86)
        for _label, _key, color, hatch in bucket_specs
    ]
    legend_labels = [label for label, _key, _color, _hatch in bucket_specs]
    fig.legend(
        legend_handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.53, 0.965),
        ncol=4,
        frameon=False,
        fontsize=5.8,
        handlelength=0.70,
        handletextpad=0.25,
        columnspacing=0.55,
        borderaxespad=0.0,
    )
    fig.subplots_adjust(left=0.10, right=0.99, bottom=0.15, top=0.75, hspace=0.25, wspace=0.14)
    path = os.path.join(FIG_DIR, "sensitivity_bottleneck_transition.pdf")
    fig.savefig(path)
    plt.close(fig)
    return path


def figure_sensitivity_runtime_parity():
    scenario_summary = load_summary(PROJECTION_SCENARIOS_JSON)
    if scenario_summary is None:
        return None

    workload_specs = projection_workload_specs()
    scenario_specs = projection_scenario_specs()
    by_scenario = scenario_summary.get("by_scenario", {})
    x = np.arange(len(scenario_specs))
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.92))
    ax.axhspan(7.0e-4, 1.0, facecolor="#EDF6EF", edgecolor="none", zorder=0)
    ax.axhline(1.0, color=COLORS["dark"], linestyle="--", linewidth=0.75, zorder=1)
    for workload, label, color, marker, linestyle in workload_specs:
        ratios = []
        for scenario_id, _scenario_label in scenario_specs:
            item = by_scenario.get(scenario_id, {}).get("by_workload", {}).get(workload, {})
            ratios.append(max(1.0e-4, float(item.get("median_projected_native_ratio", 0.0))))
        ax.plot(
            x,
            ratios,
            marker=marker,
            linestyle=linestyle,
            linewidth=1.35,
            markersize=3.8,
            color=color,
            markeredgecolor="#202020",
            markeredgewidth=0.25,
            zorder=3,
            label=label,
        )
    ax.text(
        0.03,
        0.18,
        "runtime-favorable",
        transform=ax.transAxes,
        fontsize=5.8,
        color=COLORS["green"],
    )
    ax.set_yscale("log")
    ax.set_ylim(7.0e-4, 4.0e3)
    ax.set_xlim(-0.25, len(scenario_specs) - 0.75)
    ax.set_ylabel("$T_{qhw}/T_{native}$", fontsize=6.2, labelpad=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([label for _scenario_id, label in scenario_specs])
    ax.tick_params(axis="both", labelsize=5.9, pad=1.0)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.38, linestyle=":")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.53, 0.965),
        ncol=4,
        frameon=False,
        fontsize=5.8,
        handlelength=1.0,
        handletextpad=0.25,
        columnspacing=0.65,
    )
    fig.subplots_adjust(left=0.14, right=0.99, bottom=0.17, top=0.75)
    path = os.path.join(FIG_DIR, "sensitivity_runtime_parity.pdf")
    fig.savefig(path)
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
        host_queue_shares = []
        twoq_shares = []
        recovery_required = []
        for row in subset:
            components = projection_components_ms(row)
            total = max(1.0e-12, components["total_ms"])
            decode_shares.append(100.0 * components["critical_decode_ms"] / total)
            host_queue_shares.append(
                100.0 * (components["host_io_ms"] + components["queue_ms"]) / total
            )
            gate = max(1.0e-12, components["gate_ms"])
            twoq_shares.append(100.0 * components["twoq_gate_ms"] / gate)
            gap = max(0.0, float(row["quality_gap"]))
            tolerance = tolerances[workload]
            if gap <= tolerance:
                recovery_required.append(0.0)
            else:
                recovery_required.append(100.0 * max(0.0, 1.0 - tolerance / gap))
        decode_share = float(np.median(decode_shares))
        host_queue_share = float(np.median(host_queue_shares))
        twoq_share = float(np.median(twoq_shares))
        recovery = float(np.median(recovery_required))
        raw_values.append([recovery, evals, decode_share, host_queue_share, twoq_share])
        cell_text.append(
            [
                "{:.0f}%".format(recovery),
                "{:.0f}".format(evals),
                "{:.0f}%".format(decode_share),
                "{:.0f}%".format(float(np.median(host_queue_shares))),
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
        "Decode\npipe",
        "Host/Q\nserial",
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


def figure_scaling_legend():
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 0.22))
    ax.axis("off")
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="-",
            color=COLORS["blue"],
            markerfacecolor=COLORS["blue"],
            markeredgecolor=COLORS["blue"],
            markeredgewidth=0.9,
            markersize=4.2,
        ),
        Line2D(
            [0],
            [0],
            linestyle="--",
            color=COLORS["gray"],
            linewidth=1.0,
        ),
    ]
    fig.legend(
        handles,
        ["Actual", "Ideal"],
        ncol=2,
        loc="center",
        frameon=False,
        fontsize=FIGURE_TICK_FONT,
        handletextpad=0.35,
        columnspacing=1.0,
    )
    path = os.path.join(FIG_DIR, "evidence_scaling_legend.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_weak_scaling():
    runs = sorted(
        [run for run in WEAK_SCALING_RUNS if load_summary(run["summary"]) is not None],
        key=lambda run: run["gpus"],
    )
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
    regular_median = float(np.median(per_gpu[weak_mask]))
    gpu_ticks = [1, 4, 8, 16, 32, 64, 128, 256]
    gpu_labels = [str(tick) for tick in gpu_ticks]

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.98))
    line_actual = ax.plot(
        gpus,
        throughput,
        marker="o",
        linestyle="-",
        color=COLORS["blue"],
        linewidth=0.9,
        zorder=2,
    )[0]
    ax.plot(
        gpus[~weak_mask],
        throughput[~weak_mask],
        marker="o",
        markerfacecolor="white",
        markeredgecolor=COLORS["blue"],
        linestyle="None",
        color=COLORS["blue"],
        zorder=3,
    )
    line_ideal = ax.plot(
        gpus,
        ideal,
        linestyle="--",
        color=COLORS["gray"],
        linewidth=1.0,
        zorder=1,
    )[0]
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(compact_tick))
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels(gpu_labels)
    ax.set_xlabel("GPU count")
    ax.set_ylabel("Evidence rate\n(records/s)")
    style_axis(ax, grid="both")
    ax.tick_params(axis="x", labelsize=FIGURE_TICK_FONT, pad=1)
    ax.set_xlim(0.78, 330)
    add_top_legend(
        fig,
        [line_actual, line_ideal],
        ["Actual", "Ideal"],
        ncol=2,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(top=0.72, bottom=0.27, left=0.22, right=0.98)
    throughput_path = os.path.join(FIG_DIR, "weak_scaling.pdf")
    save_canvas(fig, throughput_path)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.86))
    ax.plot(gpus, per_gpu, color=COLORS["orange"], linewidth=0.85, alpha=0.45, zorder=1)
    line_rate = ax.plot(
        gpus[weak_mask],
        per_gpu[weak_mask],
        marker="s",
        linestyle="None",
        color=COLORS["orange"],
        zorder=3,
    )[0]
    line_rate_context = ax.plot(
        gpus[~weak_mask],
        per_gpu[~weak_mask],
        marker="s",
        markerfacecolor="white",
        markeredgecolor=COLORS["orange"],
        linestyle="None",
        color=COLORS["orange"],
        zorder=3,
    )[0]
    ax.axhline(regular_median, linestyle="--", color=COLORS["gray"], linewidth=1.0)
    ax.set_xscale("log", base=2)
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels(gpu_labels)
    ax.set_xlabel("GPUs")
    ax.set_ylabel("Per-GPU\nrecords/s")
    ax.set_ylim(
        max(0.0, float(np.min(per_gpu)) * 0.78),
        float(np.max(per_gpu)) * 1.15,
    )
    style_axis(ax, grid="both")
    ax.tick_params(axis="x", labelsize=FIGURE_TICK_FONT, pad=0)
    for label in ax.get_xticklabels():
        label.set_rotation(38)
        label.set_ha("right")
    ax.set_xlim(0.78, 330)
    add_top_legend(
        fig,
        [line_rate_context, line_rate],
        ["context", "regular sweep"],
        ncol=2,
        y=1.00,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(top=0.75, bottom=0.31, left=0.37, right=0.98)
    efficiency_path = os.path.join(FIG_DIR, "weak_scaling_efficiency.pdf")
    fig.savefig(efficiency_path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return [throughput_path, efficiency_path]


def figure_strong_scaling():
    runs = sorted(
        [
            run
            for run in STRONG_SCALING_RUNS
            if load_summary(run["summary"]) is not None and run_elapsed_seconds(run) is not None
        ],
        key=lambda run: run["gpus"],
    )
    if len(runs) < 2:
        return None

    gpus = np.array([run["gpus"] for run in runs], dtype=float)
    cases = np.array([run["cases"] for run in runs], dtype=float)
    elapsed = np.array([run_elapsed_seconds(run) for run in runs], dtype=float)
    fixed_mask = np.array([run.get("kind") == "fixed" for run in runs], dtype=bool)
    anchor_mask = np.array(
        [run.get("elapsed_mode") == "sum_array_tasks" for run in runs], dtype=bool
    )
    direct_mask = fixed_mask & ~anchor_mask
    fixed_cases = float(np.max(cases[fixed_mask])) if np.any(fixed_mask) else float(np.max(cases))
    fixed_elapsed = elapsed * (fixed_cases / cases)
    base_idx = int(np.where(direct_mask)[0][0]) if np.any(direct_mask) else 0
    base_gpu = float(gpus[base_idx])
    base_elapsed = float(fixed_elapsed[base_idx])
    speedup = base_elapsed / fixed_elapsed
    ideal = gpus / base_gpu
    ideal_elapsed = base_elapsed * (base_gpu / gpus)
    gpu_ticks = [1, 4, 8, 16, 32, 64, 128, 256]

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.98))
    line_actual = ax.plot(
        gpus[direct_mask],
        fixed_elapsed[direct_mask] / 60.0,
        marker="o",
        linestyle="-",
        color=COLORS["blue"],
        linewidth=0.9,
        zorder=2,
    )[0]
    ax.plot(
        gpus[anchor_mask],
        fixed_elapsed[anchor_mask] / 60.0,
        marker="o",
        markerfacecolor="white",
        markeredgecolor=COLORS["blue"],
        linestyle="None",
        color=COLORS["blue"],
        zorder=3,
    )
    line_ideal = ax.plot(
        gpus[direct_mask],
        ideal_elapsed[direct_mask] / 60.0,
        linestyle="--",
        color=COLORS["gray"],
        linewidth=1.0,
        zorder=1,
    )[0]
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(compact_tick))
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels([str(tick) for tick in gpu_ticks])
    ax.set_ylabel("Fixed-work time\n(min)")
    ax.set_xlabel("GPU count")
    style_axis(ax, grid="both")
    ax.tick_params(axis="x", labelsize=FIGURE_TICK_FONT, pad=1)
    ax.set_xlim(0.78, 330)
    displayed_minutes = np.concatenate(
        [fixed_elapsed / 60.0, ideal_elapsed[direct_mask] / 60.0]
    )
    ax.set_ylim(
        float(np.min(displayed_minutes)) * 0.70,
        float(np.max(displayed_minutes)) * 1.35,
    )
    add_top_legend(
        fig,
        [line_actual, line_ideal],
        ["Actual", "Ideal"],
        ncol=2,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(top=0.72, bottom=0.27, left=0.22, right=0.98)
    elapsed_path = os.path.join(FIG_DIR, "strong_scaling.pdf")
    save_canvas(fig, elapsed_path)

    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 2.02))
    ax.plot(gpus, speedup, color=COLORS["green"], linewidth=0.85, alpha=0.45, zorder=1)
    line_speed_context = ax.plot(
        gpus[~fixed_mask],
        speedup[~fixed_mask],
        marker="o",
        markerfacecolor="white",
        markeredgecolor=COLORS["green"],
        linestyle="None",
        color=COLORS["green"],
        zorder=3,
    )[0]
    line_speed = ax.plot(
        gpus[fixed_mask],
        speedup[fixed_mask],
        marker="o",
        linestyle="None",
        color=COLORS["green"],
        zorder=3,
    )[0]
    ax.plot(gpus, ideal, linestyle="--", color=COLORS["gray"])
    ax.set_xscale("log", base=2)
    ax.set_xticks(gpu_ticks)
    ax.set_xticklabels([str(tick) for tick in gpu_ticks])
    ax.set_xlabel("GPUs")
    ax.set_ylabel("Build speedup\nvs. {:g} GPUs".format(base_gpu))
    style_axis(ax, grid="both")
    ax.tick_params(axis="x", labelsize=FIGURE_TICK_FONT, pad=0)
    for label in ax.get_xticklabels():
        label.set_rotation(42)
        label.set_ha("right")
    ax.set_xlim(0.78, 330)
    legend_handles = [line_speed]
    legend_labels = ["fixed suite"]
    if np.any(~fixed_mask):
        legend_handles.insert(0, line_speed_context)
        legend_labels.insert(0, "context")
    add_top_legend(fig, legend_handles, legend_labels, ncol=len(legend_handles), y=1.00, fontsize=FIGURE_TICK_FONT)
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

    points = []
    for workload, label, color in workloads:
        subset = [row for row in rows if row["workload"] == workload]
        native_ms = []
        gate_pipe_ms = []
        decode_pipe_ms = []
        host_io_ms = []
        queue_ms = []
        total_ratios = []
        gate_ratios = []
        decode_ratios = []
        host_ratios = []
        queue_ratios = []
        ctrl_context_ratios = []
        energy_ratios = []
        for row in subset:
            components = projection_components_ms(row)
            native = max(1.0e-12, 1.0e3 * float(row["native_runtime_sec"]))
            native_ms.append(native)
            gate_pipe_ms.append(components["critical_gate_ms"])
            decode_pipe_ms.append(components["critical_decode_ms"])
            host_io_ms.append(components["host_io_ms"])
            queue_ms.append(components["queue_ms"])
            total_ratios.append(components["total_ms"] / native)
            gate_ratios.append(components["critical_gate_ms"] / native)
            decode_ratios.append(components["critical_decode_ms"] / native)
            host_ratios.append(components["host_io_ms"] / native)
            queue_ratios.append(components["queue_ms"] / native)
            ctrl_context_ratios.append(components["ctrl_context_ms"] / native)
            energy_ratios.append(
                components["qpu_energy_j"] / max(1.0e-18, components["reference_energy_j"])
            )
        gate_pipe = float(np.median(gate_pipe_ms))
        decode_pipe = float(np.median(decode_pipe_ms))
        host_io = float(np.median(host_io_ms))
        queue = float(np.median(queue_ms))
        total = gate_pipe + decode_pipe + host_io + queue
        native = float(np.median(native_ms))
        component_ratios = {
            "gate_pipe_ratio": float(np.median(gate_ratios)),
            "decode_pipe_ratio": float(np.median(decode_ratios)),
            "host_io_ratio": float(np.median(host_ratios)),
            "queue_ratio": float(np.median(queue_ratios)),
            "ctrl_context_ratio": float(np.median(ctrl_context_ratios)),
            "energy_ratio": float(np.median(energy_ratios)),
        }
        ratio = float(np.median(total_ratios))
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
                "gate_pipe_ratio": component_ratios["gate_pipe_ratio"],
                "decode_pipe_ratio": component_ratios["decode_pipe_ratio"],
                "host_io_ratio": component_ratios["host_io_ratio"],
                "queue_ratio": component_ratios["queue_ratio"],
                "ctrl_context_ratio": component_ratios["ctrl_context_ratio"],
                "energy_ratio": component_ratios["energy_ratio"],
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
        label_inside = total_value > 3.0e3
        ax_total.text(
            total_value / 1.10 if label_inside else max(total_value * 1.13, 0.035),
            center,
            ratio_text,
            ha="right" if label_inside else "left",
            va="center",
            fontsize=5.6,
            color=COLORS["dark"],
        )

    ax_total.set_xscale("log")
    ax_total.set_xlim(eps, 1.3e4)
    ax_total.set_xticks([3e-2, 1e-1, 1, 1e1, 1e2, 1e3, 1e4])
    ax_total.set_xticklabels(["0.03", "0.1", "1", "10", "$10^2$", "$10^3$", "$10^4$"])
    ax_total.axvline(1.0, color=COLORS["dark"], linestyle="--", linewidth=0.8)
    ax_total.text(
        1.04,
        y_centers[0] - 0.30,
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
        evals = float(np.median([float(row["circuit_evaluations"]) for row in subset]))
        recoveries = []
        decode_shares = []
        host_io_shares = []
        feedback_budgets_us = []
        feedback_shrinks = []
        feedback_blocked = []
        twoq_shares = []
        total_ratios = []
        for row in subset:
            components = projection_components_ms(row)
            total = max(1.0e-12, components["total_ms"])
            decode_shares.append(100.0 * components["critical_decode_ms"] / total)
            host_io_shares.append(100.0 * components["host_io_ms"] / total)
            native_ms = max(1.0e-12, 1.0e3 * float(row["native_runtime_sec"]))
            row_evals = max(1.0, float(row["circuit_evaluations"]))
            fixed_ms = (
                components["critical_gate_ms"]
                + components["critical_decode_ms"]
                + components["controller_ms"]
            )
            available_ms = native_ms - fixed_ms
            current_feedback_ms = (
                components["host_io_ms"]
                + components["queue_ms"]
                + components["context_ms"]
            )
            if available_ms <= 0.0:
                feedback_budgets_us.append(0.0)
                feedback_shrinks.append(1.0e6)
                feedback_blocked.append(True)
            else:
                budget_us = 1.0e3 * available_ms / row_evals
                current_us = 1.0e3 * current_feedback_ms / row_evals
                feedback_budgets_us.append(budget_us)
                feedback_shrinks.append(max(1.0, current_us / max(budget_us, 1.0e-12)))
                feedback_blocked.append(False)
            gate = max(1.0e-12, components["gate_ms"])
            twoq_shares.append(100.0 * components["twoq_gate_ms"] / gate)
            gap = max(0.0, float(row["quality_gap"]))
            tol = tolerances[workload]
            recoveries.append(0.0 if gap <= tol else 100.0 * (1.0 - tol / gap))
        matching_point = next(point for point in points if point["label"] == label)
        total_ratios.append(matching_point["ratio"])
        median_budget_us = float(np.median(feedback_budgets_us))
        median_shrink = float(np.median(feedback_shrinks))
        median_blocked = sum(feedback_blocked) >= (len(feedback_blocked) + 1) // 2
        pressure_rows.append(
            [
                float(np.median(recoveries)),
                evals,
                median_budget_us,
                median_shrink,
                float(np.median(twoq_shares)),
                matching_point["energy_ratio"],
                float(np.median(total_ratios)),
            ]
        )
        pressure_text.append(
            [
                "{:.0f}%".format(float(np.median(recoveries))),
                "{:.0f}".format(evals),
                "blocked" if median_blocked else "{:.1f}".format(median_budget_us),
                "--" if median_blocked else "{:.1f}".format(median_shrink),
                "{:.0f}%".format(float(np.median(twoq_shares))),
                "{:,.0f}x".format(matching_point["energy_ratio"])
                if matching_point["energy_ratio"] >= 10.0
                else "{:.1f}x".format(matching_point["energy_ratio"]),
                "{:.1f}x".format(float(np.median(total_ratios)))
                if float(np.median(total_ratios)) >= 1.0
                else "{:.2f}x".format(float(np.median(total_ratios))),
            ]
        )

    raw = np.array([row[:6] for row in pressure_rows], dtype=float)
    matrix = np.zeros_like(raw)
    for col in range(raw.shape[1]):
        values = raw[:, col]
        if col in (2, 3, 5):
            values = np.log10(np.maximum(values, 1.0e-2))
        if col == 1:
            values = np.log10(np.maximum(values, 1.0))
        span = float(np.max(values) - np.min(values))
        matrix[:, col] = 0.0 if span == 0.0 else (values - float(np.min(values))) / span
        if col == 2:
            # A smaller remaining feedback budget is more severe.
            matrix[:, col] = 1.0 - matrix[:, col]

    row_labels = [workloads[idx][1] for idx in range(len(workloads))]
    col_labels = [
        "Quality\nrecov.",
        "Hybrid\n$N_e$",
        "Budget\n($\\mu$s)",
        "Shrink\n($\\times$)",
        "2Q\nshare",
        "Energy /\n400-W ref.",
    ]
    fig_target, ax_target = plt.subplots(figsize=(COLUMN_WIDTH, 1.48))
    image = ax_target.imshow(matrix, cmap="YlOrRd", vmin=0.0, vmax=1.0, aspect="auto")
    ax_target.set_xticks(np.arange(len(col_labels)))
    ax_target.set_xticklabels(col_labels)
    ax_target.set_yticks(np.arange(len(row_labels)))
    ax_target.set_yticklabels(row_labels)
    ax_target.tick_params(
        axis="x",
        top=True,
        bottom=False,
        labeltop=True,
        labelbottom=False,
        labelsize=5.65,
        pad=1.0,
    )
    ax_target.tick_params(axis="y", labelsize=6.0, pad=1.2)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            ax_target.text(
                j,
                i,
                pressure_text[i][j],
                ha="center",
                va="center",
                fontsize=5.55,
                weight="bold" if value >= 0.82 else "normal",
                color="white" if value >= 0.68 else COLORS["dark"],
            )
    ax_target.set_xticks(np.arange(-0.5, len(col_labels), 1), minor=True)
    ax_target.set_yticks(np.arange(-0.5, len(row_labels), 1), minor=True)
    ax_target.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
    ax_target.tick_params(which="minor", bottom=False, left=False)
    for spine in ax_target.spines.values():
        spine.set_linewidth(0.65)
        spine.set_color("#555555")
    # Cell values carry the quantitative contract; a colorbar would imply that
    # unlike units share a common physical scale. Color is only a reading aid.
    fig_target.subplots_adjust(left=0.14, right=0.985, bottom=0.06, top=0.75)
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


def figure_physical_factory_crossover():
    summary = load_summary(PHYSICAL_ARCHITECTURE_DSE_JSON)
    if summary is None:
        return None

    workloads = [
        ("ml", "ML"),
        ("chemistry", "Chem."),
        ("optimization", "Opt."),
        ("simulation", "Sim."),
    ]
    scenarios = [
        ("surface_measured_control", "Measured", COLORS["gray"], "o"),
        ("surface_estimator_aligned", "Estimator", COLORS["blue"], "s"),
        ("surface_throughput_target", "Target", COLORS["orange"], "D"),
    ]
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.50))
    y = np.arange(len(workloads))
    offsets = (-0.16, 0.0, 0.16)
    for offset, (scenario, label, color, marker) in zip(offsets, scenarios):
        values = [
            summary["by_scenario"][scenario]["by_workload"][workload][
                "factory_scale_to_nonfactory_crossover"
            ]
            for workload, _ in workloads
        ]
        ax.scatter(
            values,
            y + offset,
            s=22,
            marker=marker,
            color=color,
            edgecolor="#222222",
            linewidth=0.35,
            label=label,
            zorder=3,
        )
    ax.axvline(4.5, color="#777777", linewidth=0.65, linestyle="--", zorder=1)
    ax.axvline(100.0, color="#777777", linewidth=0.65, linestyle=":", zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(2.0, 5.0e4)
    ax.set_yticks(y)
    ax.set_yticklabels([label for _, label in workloads])
    ax.invert_yaxis()
    ax.set_xlabel("Factory scale to crossover (x)")
    style_axis(ax, grid=None)
    ax.grid(axis="x", which="major", linestyle=":", linewidth=0.5, color="#B9B9B9")
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.52, 0.99),
        ncol=3,
        frameon=False,
        fontsize=6.0,
        handlelength=0.8,
        handletextpad=0.25,
        columnspacing=0.55,
    )
    fig.subplots_adjust(left=0.22, right=0.98, bottom=0.28, top=0.68)
    path = os.path.join(FIG_DIR, "physical_factory_crossover.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_physical_post_rotation_utility():
    summary = load_summary(PHYSICAL_ARCHITECTURE_DSE_JSON)
    if summary is None:
        return None

    workload_specs = [
        ("ml", "ML"),
        ("chemistry", "Chem."),
        ("optimization", "Opt."),
        ("simulation", "Sim."),
    ]
    lever_specs = [
        ("shot_fabric", "Shots"),
        ("logical_cycle", "Cycle"),
        ("routing", "Route"),
        ("decoder", "Dec."),
        ("host_feedback", "Link"),
        ("measurement_grouping", "Group"),
    ]
    scenario = summary["by_scenario"]["surface_estimator_aligned"]["by_workload"]
    values = np.array([
        [
            scenario[workload]["post_native_rotation_marginal_utility"][lever]
            for lever, _ in lever_specs
        ]
        for workload, _ in workload_specs
    ])
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 1.50))
    image = ax.imshow(values, cmap="YlGnBu", vmin=1.0, vmax=10.0, aspect="auto")
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            value = values[row, column]
            color = "white" if value >= 6.2 else COLORS["dark"]
            label = "{:.1f}x".format(value) if value >= 1.05 else "1.0x"
            ax.text(
                column,
                row,
                label,
                ha="center",
                va="center",
                fontsize=5.0,
                color=color,
                fontweight="bold" if value >= 2.0 else "normal",
            )
    ax.set_xticks(np.arange(len(lever_specs)))
    ax.set_xticklabels([label for _, label in lever_specs], rotation=24, ha="right")
    ax.set_yticks(np.arange(len(workload_specs)))
    ax.set_yticklabels([label for _, label in workload_specs])
    ax.tick_params(axis="x", labelsize=5.3, length=0, pad=1.2)
    ax.tick_params(axis="y", labelsize=5.9, length=0, pad=1.2)
    for spine in ax.spines.values():
        spine.set_visible(False)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.025)
    colorbar.set_label("Speedup (x)", fontsize=5.3, labelpad=1.0)
    colorbar.ax.tick_params(labelsize=5.3, length=2, pad=1)
    fig.subplots_adjust(left=0.17, right=0.91, bottom=0.30, top=0.97)
    path = os.path.join(FIG_DIR, "physical_post_rotation_utility.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_native_rotation_platform_legend():
    fig, ax = plt.subplots(figsize=(TEXT_WIDTH * 0.62, 0.22))
    colors = [COLORS["blue"], COLORS["orange"], COLORS["purple"], COLORS["green"]]
    handles = [Rectangle((0, 0), 1, 1, facecolor=color, edgecolor="none") for color in colors]
    ax.axis("off")
    fig.legend(
        handles,
        ["1Q", "2Q", "Readout/reuse", "Movement/control"],
        ncol=4,
        loc="center",
        frameon=False,
        fontsize=5.7,
        handlelength=0.9,
        handletextpad=0.3,
        columnspacing=0.7,
    )
    path = os.path.join(FIG_DIR, "native_rotation_platform_legend.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_native_rotation_platform(platform_id, output_name):
    summary = load_summary(NATIVE_ROTATION_PLATFORMS_JSON)
    if summary is None:
        return None
    workload_specs = [
        ("ml", "ML"),
        ("chemistry", "Chem."),
        ("optimization", "Opt."),
        ("simulation", "Sim."),
    ]
    component_specs = [
        ("oneq", COLORS["blue"]),
        ("twoq", COLORS["orange"]),
        ("readout", COLORS["purple"]),
        ("movement_control", COLORS["green"]),
    ]
    platform = summary["platforms"][platform_id]["by_workload"]
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH * 0.91, 1.38))
    y = np.arange(len(workload_specs))
    left = np.zeros(len(workload_specs))
    for component, color in component_specs:
        values = np.array([
            100.0 * platform[workload]["median_component_fraction"][component]
            for workload, _ in workload_specs
        ])
        ax.barh(y, values, left=left, height=0.58, color=color, edgecolor="white", linewidth=0.35)
        for index, value in enumerate(values):
            if value >= 9.0:
                ax.text(
                    left[index] + value / 2.0,
                    index,
                    "{:.0f}%".format(value),
                    ha="center",
                    va="center",
                    fontsize=5.6,
                    color="white" if component in ("oneq", "twoq", "readout") else COLORS["dark"],
                    fontweight="bold",
                )
        left += values
    ax.set_yticks(y)
    ax.set_yticklabels([label for _, label in workload_specs])
    ax.invert_yaxis()
    ax.set_xlim(0.0, 100.0)
    ax.set_xticks((0, 50, 100))
    ax.set_xticklabels(("0", "50%", "100%"))
    ax.set_xlabel("Projected execution share")
    style_axis(ax, grid="x")
    fig.subplots_adjust(left=0.18, right=0.985, bottom=0.27, top=0.98)
    path = os.path.join(FIG_DIR, output_name)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_quality_eligibility():
    quality = load_summary(QUALITY_QUALIFIED_JSON)
    finite = load_summary(FINITE_SHOT_JSON)
    if quality is None or finite is None:
        return None

    workload_specs = [
        ("ml", "ML"),
        ("chemistry", "Chem."),
        ("optimization", "Opt."),
        ("simulation", "Sim."),
    ]
    y = np.arange(len(workload_specs))
    declared = quality["by_tolerance_multiplier"]["1.0"]
    values = [
        100.0 * declared[workload]["noiseless_quality_pass_fraction"]
        for workload, _ in workload_specs
    ]
    counts = [
        (
            declared[workload]["noiseless_quality_pass_count"],
            declared[workload]["records"],
        )
        for workload, _ in workload_specs
    ]
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 2.08))
    ax.barh(
        y,
        np.full(len(y), 100.0),
        height=0.52,
        color="#E5E5E5",
        edgecolor="white",
        linewidth=0.65,
        label="Fail",
    )
    ax.barh(
        y,
        values,
        height=0.52,
        color=COLORS["green"],
        edgecolor="white",
        linewidth=0.65,
        label="Pass",
    )
    for row, (value, (passed, total)) in enumerate(zip(values, counts)):
        ax.text(
            104.0,
            row,
            "{:,}/{:,}".format(passed, total),
            ha="right",
            va="center",
            fontsize=FIGURE_TICK_FONT,
            color=COLORS["dark"],
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.15},
        )
    ax.set_yticks(y)
    ax.set_yticklabels([label for _, label in workload_specs])
    ax.invert_yaxis()
    ax.set_xlim(0, 108)
    ax.set_xticks((0, 50, 100))
    ax.set_xticklabels(("0", "50%", "100%"))
    ax.set_xlabel("Noiseless records (%)")
    style_axis(ax, grid="x")
    add_top_legend(
        fig,
        [
            Rectangle((0, 0), 1, 1, facecolor=COLORS["green"], edgecolor="#356F43"),
            Rectangle((0, 0), 1, 1, facecolor="#E5E5E5", edgecolor="#888888"),
        ],
        ["Pass", "Fail"],
        ncol=2,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(left=0.31, right=0.99, bottom=0.25, top=0.73)
    noiseless_path = os.path.join(FIG_DIR, "quality_noiseless_gate.pdf")
    save_canvas(fig, noiseless_path)

    direct = {
        workload: finite["summary"][workload]["10000"]
        for workload, _ in workload_specs
    }
    output_pass = [
        100.0
        * direct[workload]["cases_with_pass_probability_ge_0p9"]
        / direct[workload]["cases"]
        for workload, _ in workload_specs
    ]
    full_loop_eligible = [
        100.0
        * declared[workload]["hardware_target_eligible_count"]
        / direct[workload]["cases"]
        for workload, _ in workload_specs
    ]
    fig, ax = plt.subplots(figsize=(SUBFIGURE_WIDTH, 2.08))
    offsets = (-0.16, 0.16)
    ax.barh(
        y + offsets[0],
        output_pass,
        height=0.27,
        color=COLORS["blue"],
        edgecolor="white",
        linewidth=0.65,
    )
    ax.barh(
        y + offsets[1],
        full_loop_eligible,
        height=0.27,
        color=COLORS["green"],
        edgecolor="white",
        linewidth=0.65,
    )
    for row, (workload, _) in enumerate(workload_specs):
        passed = direct[workload]["cases_with_pass_probability_ge_0p9"]
        total = direct[workload]["cases"]
        eligible = declared[workload]["hardware_target_eligible_count"]
        ax.text(
            59.0,
            row + offsets[0],
            "{}/{}".format(passed, total),
            ha="right",
            va="center",
            fontsize=FIGURE_TICK_FONT,
            color=COLORS["dark"],
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.12},
        )
        ax.text(
            59.0,
            row + offsets[1],
            "{}/{}".format(eligible, total),
            ha="right",
            va="center",
            fontsize=FIGURE_TICK_FONT,
            color=COLORS["dark"],
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.12},
        )
    ax.set_yticks(y)
    ax.set_yticklabels([label for _, label in workload_specs])
    ax.invert_yaxis()
    ax.set_xlim(0, 61)
    ax.set_xticks((0, 25, 50))
    ax.set_xticklabels(("0", "25%", "50%"))
    ax.set_xlabel("Pass rate (%)")
    style_axis(ax, grid="x")
    add_top_legend(
        fig,
        [
            Rectangle((0, 0), 1, 1, facecolor=COLORS["blue"], edgecolor="#2D5F91"),
            Rectangle((0, 0), 1, 1, facecolor=COLORS["green"], edgecolor="#356F43"),
        ],
        ["Quality pass", "Complete loop"],
        ncol=2,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(left=0.31, right=0.99, bottom=0.25, top=0.73)
    finite_path = os.path.join(FIG_DIR, "quality_finite_shot_gate.pdf")
    save_canvas(fig, finite_path)
    return [noiseless_path, finite_path]


def figure_trace_aware_lower_bound():
    artifact = load_summary(JOINT_DSE_JSON)
    if artifact is None:
        return None
    detail = artifact["trace_aware_logical_lower_bound"]["detail"]
    eligible = [
        row
        for row in detail
        if row["hardware_target_eligible"]
        and row["mode"] == "serial_evaluation_ready"
    ]
    eligible = sorted(eligible, key=lambda row: row["runtime_ratio"])
    ratios = np.array([row["runtime_ratio"] for row in eligible], dtype=float)
    median_value = float(np.median(ratios))
    offsets = np.array([-0.09, 0.03, -0.03, 0.08, -0.07, 0.01,
                        0.07, -0.01, -0.08, 0.04, -0.04, 0.09])
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.05))
    ax.axvspan(0.1, 1.0, color="#EDF6EF", alpha=0.85, linewidth=0, zorder=0)
    ax.axvspan(1.0, 5.3, color="#F1F1F1", alpha=0.70, linewidth=0, zorder=0)
    beats = ratios < 1.0
    ax.scatter(
        ratios[beats],
        offsets[beats],
        s=22,
        marker="o",
        color=COLORS["green"],
        edgecolors="#333333",
        linewidths=0.35,
        zorder=3,
    )
    ax.scatter(
        ratios[~beats],
        offsets[~beats],
        s=24,
        marker="s",
        facecolors="white",
        edgecolors="#777777",
        linewidths=0.85,
        zorder=3,
    )
    ax.scatter(
        [median_value],
        [0.18],
        marker="D",
        s=28,
        color=COLORS["blue"],
        edgecolors="#222222",
        linewidths=0.45,
        zorder=4,
    )
    ax.axvline(1.0, color="#333333", linewidth=0.75, linestyle="--")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(compact_tick))
    ax.set_xlim(0.1, 5.3)
    ax.set_ylim(-0.16, 0.24)
    ax.set_yticks([])
    ax.set_xlabel("Projected logical runtime / native HPC runtime (x)")
    style_axis(ax, grid="x")
    ax.text(0.16, 0.205, "faster than HPC", fontsize=FIGURE_TICK_FONT, color="#356F43", va="center")
    ax.text(1.18, 0.205, "slower than HPC", fontsize=FIGURE_TICK_FONT, color="#666666", va="center")
    ax.text(
        median_value,
        0.105,
        "{:.2f}x".format(median_value),
        ha="center",
        va="center",
        fontsize=FIGURE_TICK_FONT,
        color=COLORS["blue"],
    )
    add_top_legend(
        fig,
        [
            legend_marker(COLORS["green"]),
            Line2D(
                [0],
                [0],
                marker="s",
                color="none",
                markerfacecolor="white",
                markeredgecolor="#777777",
                markeredgewidth=0.9,
                markersize=4.5,
            ),
            legend_marker(COLORS["blue"], marker="D"),
            Line2D([0], [0], color="#333333", linewidth=0.75, linestyle="--"),
        ],
        ["Faster", "Slower", "Median", "Equal runtime"],
        ncol=4,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.27, top=0.70)
    path = os.path.join(FIG_DIR, "trace_aware_logical_lower_bound.pdf")
    save_canvas(fig, path)
    return path


def figure_ft_reliability_target():
    artifact = load_summary(FT_RELIABILITY_JSON)
    if artifact is None:
        return None
    values_by_contract = {
        "strict_all_shots": [],
        "estimator_tolerant": [],
    }
    for case in artifact["quality_qualified_case_contracts"]:
        for contract in case["ft_contracts"]:
            lead = contract["reliability_leading_term"]
            if (
                abs(float(contract["physical_error_rate"]) - 1.0e-3) > 1.0e-15
                or abs(float(contract["contract"]["application_failure_budget"]) - 0.01) > 1.0e-15
            ):
                continue
            contract_name = contract["contract"]["contract"]
            if contract_name in values_by_contract:
                values_by_contract[contract_name].append(
                    64.0 * lead["factory_supply_multiplier_to_crossover"] / 1.0e6
                )
    rows = [
        ("All shots protected", values_by_contract["strict_all_shots"], COLORS["green"], "o"),
        ("Failed shots allowed", values_by_contract["estimator_tolerant"], COLORS["purple"], "D"),
    ]
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.92))
    for row, (label, values, color, marker) in enumerate(rows):
        low = float(min(values))
        high = float(max(values))
        median_value = float(np.median(values))
        order = np.argsort(values)
        jitter = np.linspace(-0.10, 0.10, len(values))
        point_y = np.empty(len(values))
        point_y[order] = row + jitter
        ax.hlines(row, low, high, color=color, linewidth=2.2, alpha=0.75, zorder=2)
        ax.scatter(
            values,
            point_y,
            color=color,
            marker=marker,
            s=17,
            edgecolors="#222222",
            linewidths=0.35,
            zorder=3,
        )
        ax.scatter(
            [median_value],
            [row],
            color=COLORS["dark"],
            marker="D",
            s=27,
            edgecolors="white",
            linewidths=0.55,
            zorder=4,
        )
    ax.set_xlim(1.4, 2.85)
    ax.set_xticks((1.5, 2.0, 2.5))
    ax.set_yticks(y)
    ax.set_yticklabels([label for label, _, _, _ in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Required T-state factories (millions)")
    style_axis(ax, grid="x")
    add_top_legend(
        fig,
        [
            legend_marker(COLORS["gray"]),
            legend_marker(COLORS["dark"], marker="D"),
        ],
        ["Eligible record", "Median"],
        ncol=2,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    ax.set_ylim(1.34, -0.34)
    fig.subplots_adjust(left=0.40, right=0.98, bottom=0.29, top=0.71)
    path = os.path.join(FIG_DIR, "ft_reliability_target.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_ft_contract_parameters():
    """Show the error-correction settings selected for each eligible record."""
    artifact = load_summary(FT_RELIABILITY_JSON)
    if artifact is None:
        return None

    contracts = {
        "strict_all_shots": {
            "label": "All shots protected",
            "color": COLORS["green"],
            "marker": "o",
            "points": [],
        },
        "estimator_tolerant": {
            "label": "Failed shots allowed",
            "color": COLORS["purple"],
            "marker": "D",
            "points": [],
        },
    }
    for case in artifact["quality_qualified_case_contracts"]:
        for contract in case["ft_contracts"]:
            if (
                abs(float(contract["physical_error_rate"]) - 1.0e-3) > 1.0e-15
                or abs(
                    float(contract["contract"]["application_failure_budget"])
                    - 0.01
                )
                > 1.0e-15
            ):
                continue
            name = contract["contract"]["contract"]
            if name not in contracts:
                continue
            lead = contract["reliability_leading_term"]
            contracts[name]["points"].append(
                (
                    int(lead["distance"]),
                    int(lead["required_t_states_per_rotation_leading_term"]),
                )
            )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(COLUMN_WIDTH, 1.92),
        sharey=True,
        gridspec_kw={"width_ratios": (0.86, 1.14)},
    )
    metric_specs = [
        (axes[0], 0, "Surface-code distance", (6.3, 15.7), (7, 9, 11, 13, 15)),
        (axes[1], 1, "T states per rotation", (46, 89), (50, 60, 70, 80)),
    ]
    for row, spec in enumerate(contracts.values()):
        for ax, metric_index, _xlabel, _xlim, _xticks in metric_specs:
            values = np.asarray(
                [point[metric_index] for point in spec["points"]], dtype=float
            )
            order = np.argsort(values)
            jitter = np.linspace(-0.10, 0.10, len(values))
            point_y = np.empty(len(values))
            point_y[order] = row + jitter
            ax.hlines(
                row,
                float(np.min(values)),
                float(np.max(values)),
                color=spec["color"],
                linewidth=2.2,
                alpha=0.75,
                zorder=2,
            )
            ax.scatter(
                values,
                point_y,
                s=17,
                marker=spec["marker"],
                color=spec["color"],
                edgecolors="#222222",
                linewidths=0.35,
                zorder=3,
            )
            ax.scatter(
                [float(np.median(values))],
                [row],
                s=27,
                marker="D",
                color=COLORS["dark"],
                edgecolors="white",
                linewidths=0.55,
                zorder=4,
            )
    for ax, _metric_index, xlabel, xlim, xticks in metric_specs:
        ax.set_xlim(*xlim)
        ax.set_xticks(xticks)
        ax.set_xlabel(xlabel)
        style_axis(ax, grid="x")
        ax.set_ylim(1.34, -0.34)
    axes[0].set_yticks(np.arange(len(contracts)))
    axes[0].set_yticklabels([spec["label"] for spec in contracts.values()])
    axes[1].tick_params(axis="y", labelleft=False)
    add_top_legend(
        fig,
        [
            legend_marker(COLORS["gray"]),
            legend_marker(COLORS["dark"], marker="D"),
        ],
        ["Eligible record", "Median"],
        ncol=2,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(left=0.40, right=0.99, bottom=0.29, top=0.71, wspace=0.18)
    path = os.path.join(FIG_DIR, "ft_contract_parameters.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_joint_phase_map():
    artifact = load_summary(JOINT_DSE_JSON)
    if artifact is None:
        return None
    cells = artifact["main_phase_map"]["cells"]
    factory_groups = (
        ("64-6.4k factories", 100.0),
        ("640k factories", 10000.0),
        ("3.2M factories", 50000.0),
    )
    lane_groups = (("1k", 1000), ("10k+", 10000))
    targets = ("factory_supply", "shot_parallelism", "logical_cycle", "advantage_reached")
    target_colors = {
        "factory_supply": COLORS["blue"],
        "shot_parallelism": COLORS["orange"],
        "logical_cycle": COLORS["green"],
        "advantage_reached": COLORS["gray"],
    }

    positions = (0.0, 0.72, 1.85, 2.57, 3.70, 4.42)
    cell_data = []
    for _, factory in factory_groups:
        for _, lane in lane_groups:
            cell_data.append(next(
                item for item in cells
                if item["factory_supply_multiplier"] == factory
                and item["useful_lanes"] == lane
            ))

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.48))
    bottoms = np.zeros(len(cell_data))
    for target in targets:
        counts = np.asarray([
            cell["eligible_first_target_counts"].get(target, 0)
            for cell in cell_data
        ], dtype=float)
        shares = counts / 12.0 * 100.0
        bars = ax.bar(
            positions,
            shares,
            bottom=bottoms,
            width=0.59,
            color=target_colors[target],
            edgecolor="white",
            linewidth=0.75,
        )
        for bar, count, share, bottom in zip(bars, counts, shares, bottoms):
            if count <= 0:
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bottom + share / 2.0,
                "{}".format(int(count)),
                ha="center",
                va="center",
                fontsize=FIGURE_TICK_FONT,
                color="white" if target != "shot_parallelism" else "black",
                fontweight="bold",
            )
        bottoms += shares

    pair_centers = tuple((positions[index] + positions[index + 1]) / 2.0 for index in (0, 2, 4))
    for center, (label, _) in zip(pair_centers, factory_groups):
        ax.text(center, 103.5, label, ha="center", va="bottom", fontsize=FIGURE_TICK_FONT)
    ax.set_xticks(positions)
    ax.set_xticklabels(tuple(label for _ in factory_groups for label, _ in lane_groups))
    ax.set_xlabel("Parallel shot lanes")
    ax.set_ylabel("Eligible cases (%)")
    ax.set_ylim(0, 112)
    ax.set_yticks((0, 50, 100))
    style_axis(ax, grid="y")
    legend_targets = (
        "factory_supply",
        "logical_cycle",
        "shot_parallelism",
        "advantage_reached",
    )
    handles = [
        Rectangle(
            (0, 0),
            1,
            1,
            facecolor=target_colors[target],
            edgecolor="#555555",
        )
        for target in legend_targets
    ]
    fig.legend(
        handles,
        ("T-state supply", "Gate speed", "Shot lanes", "Already faster"),
        loc="upper center",
        bbox_to_anchor=(0.53, 0.995),
        ncol=2,
        frameon=False,
        fontsize=FIGURE_TICK_FONT,
        handlelength=0.85,
        handletextpad=0.25,
        columnspacing=0.80,
    )
    fig.subplots_adjust(left=0.22, right=0.99, bottom=0.25, top=0.66)
    path = os.path.join(FIG_DIR, "joint_bottleneck_phase_map.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_resource_removal_ceiling():
    """Plot the maximum end-to-end gain from removing one resource cost."""
    artifact = load_summary(JOINT_DSE_JSON)
    if artifact is None:
        return None
    cells = artifact["main_phase_map"]["cells"]
    scenarios = [
        ("Current", 1.0, 1000, COLORS["dark"], "o"),
        ("640k factories", 10000.0, 1000, COLORS["orange"], "s"),
        ("3.2M factories + 10k lanes", 50000.0, 10000, COLORS["green"], "D"),
    ]
    resources = [
        ("factory_supply", "T-state generation"),
        ("shot_parallelism", "Parallel shots"),
        ("logical_cycle", "Logical-gate latency"),
        ("decoder_reaction", "Decoder latency"),
        ("host_feedback", "Host feedback"),
    ]
    rows = np.arange(len(resources), dtype=float)
    offsets = (-0.16, 0.0, 0.16)
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.58))
    for offset, (label, factory, lanes, color, marker) in zip(offsets, scenarios):
        cell = next(
            item
            for item in cells
            if item["factory_supply_multiplier"] == factory
            and item["useful_lanes"] == lanes
        )
        values = np.array(
            [cell["removal_ceiling"][key]["median"] for key, _ in resources],
            dtype=float,
        )
        ax.scatter(
            values,
            rows + offset,
            s=28,
            marker=marker,
            color=color,
            edgecolors="#222222",
            linewidths=0.45,
            zorder=3,
        )
    ax.axvline(1.0, color="#555555", linewidth=0.7, linestyle="--")
    ax.set_xscale("log")
    ax.set_xlim(0.88, 1.15e4)
    ax.set_xticks((1, 2, 10, 100, 1000, 10000))
    ax.set_xticklabels(("1", "2", "10", "100", "1k", "10k"))
    ax.set_yticks(rows)
    ax.set_yticklabels([label for _, label in resources])
    ax.invert_yaxis()
    ax.set_xlabel("Speedup if one resource were free (x)")
    style_axis(ax, grid="x")
    legend_scenarios = (scenarios[0], scenarios[2], scenarios[1])
    add_top_legend(
        fig,
        [
            legend_marker(color, marker=marker)
            for _label, _factory, _lanes, color, marker in legend_scenarios
        ],
        [label for label, _factory, _lanes, _color, _marker in legend_scenarios],
        ncol=2,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(left=0.39, right=0.98, bottom=0.24, top=0.76)
    path = os.path.join(FIG_DIR, "resource_removal_ceiling.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_sim_hardware_modality_pivot():
    """Show how the first physical bottleneck changes with QPU modality."""
    native = load_summary(NATIVE_ROTATION_PLATFORMS_JSON)
    joint = load_summary(JOINT_DSE_JSON)
    if native is None or joint is None:
        return None

    current = next(
        cell
        for cell in joint["main_phase_map"]["cells"]
        if cell["factory_supply_multiplier"] == 1
        and cell["useful_lanes"] == 1000
    )
    factory_ceiling = float(
        current["removal_ceiling"]["factory_supply"]["median"]
    )
    factory_fraction = 1.0 - 1.0 / factory_ceiling
    surface_ratio = float(current["eligible_runtime_ratio"]["median"])
    neutral = native["platforms"]["neutral_atom_zoned"][
        "quality_qualified_sim"
    ]["median_component_fraction"]
    qccd = native["platforms"]["trapped_ion_qccd"][
        "quality_qualified_sim"
    ]["median_component_fraction"]

    component_specs = [
        ("factory", "T-state generation", COLORS["blue"]),
        ("oneq", "1Q gates", COLORS["teal"]),
        ("twoq", "2Q gates", COLORS["orange"]),
        ("readout", "Readout/reuse", COLORS["purple"]),
        ("movement_control", "Move/control", COLORS["gray"]),
    ]
    rows = [
        (
            "Surface code\n(synthesized rotations)",
            {
                "factory": factory_fraction,
                "oneq": 0.0,
                "twoq": 0.0,
                "readout": 0.0,
                "movement_control": 1.0 - factory_fraction,
            },
        ),
        ("Neutral atom\n(native rotations)", neutral),
        ("Trapped-ion QCCD\n(native rotations)", qccd),
    ]
    runtime_ratios = [
        surface_ratio,
        float(
            native["platforms"]["neutral_atom_zoned"]["quality_qualified_sim"][
                "median_projected_native_ratio"
            ]
        ),
        float(
            native["platforms"]["trapped_ion_qccd"]["quality_qualified_sim"][
                "median_projected_native_ratio"
            ]
        ),
    ]
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.48))
    left = np.zeros(len(rows))
    for key, _label, color in component_specs:
        values = np.array(
            [100.0 * float(components.get(key, 0.0)) for _, components in rows]
        )
        bars = ax.barh(
            y,
            values,
            left=left,
            height=0.52,
            color=color,
            edgecolor="white",
            linewidth=0.75,
        )
        for bar, value, start in zip(bars, values, left):
            if value < 5.0:
                continue
            ax.text(
                start + value / 2.0,
                bar.get_y() + bar.get_height() / 2.0,
                "{:.0f}%".format(value),
                ha="center",
                va="center",
                fontsize=FIGURE_TICK_FONT,
                color="white" if key != "twoq" else "black",
                fontweight="bold",
            )
        left += values

    for ypos, ratio in zip(y, runtime_ratios):
        ax.text(
            103.0,
            ypos,
            "{:,}x slower".format(int(round(ratio))),
            ha="left",
            va="center",
            fontsize=FIGURE_TICK_FONT,
            color=COLORS["dark"],
            fontweight="bold",
        )

    ax.set_xlim(0, 160)
    ax.set_xticks((0, 25, 50, 75, 100))
    ax.set_xticklabels(("0", "25%", "50%", "75%", "100%"))
    ax.set_yticks(y)
    ax.set_yticklabels([label for label, _ in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Share of projected runtime")
    style_axis(ax, grid="x")
    legend_order = (0, 3, 1, 4, 2)
    add_top_legend(
        fig,
        [
            Rectangle(
                (0, 0),
                1,
                1,
                facecolor=color,
                edgecolor="#555555",
            )
            for key, _label, color in [component_specs[index] for index in legend_order]
        ],
        [component_specs[index][1] for index in legend_order],
        ncol=3,
        y=0.995,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(left=0.38, right=0.99, bottom=0.23, top=0.63)
    path = os.path.join(FIG_DIR, "sim_hardware_modality_pivot.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def figure_lsqca_replacement():
    artifact = load_summary(JOINT_DSE_JSON)
    if artifact is None:
        return None
    records = artifact["matched_mechanism_replacement"]["records"]
    values = [
        [record["baseline_runtime_ratio"] for record in records],
        [record["lower_movement_runtime_ratio"] for record in records],
        [record["upper_movement_runtime_ratio"] for record in records],
    ]
    labels = ("Baseline", "LSQCA lower", "LSQCA upper")
    rows = np.arange(len(values))
    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 2.48))
    box = ax.boxplot(
        values,
        positions=rows,
        vert=False,
        widths=0.44,
        whis=(10, 90),
        showfliers=False,
        patch_artist=True,
        manage_ticks=False,
        boxprops={"facecolor": "#D8E4F0", "edgecolor": "#4A4A4A", "linewidth": 0.9},
        whiskerprops={"color": "#4A4A4A", "linewidth": 0.9},
        capprops={"color": "#4A4A4A", "linewidth": 0.9},
        medianprops={"color": "#111111", "linewidth": 1.4},
    )
    del box
    for row, series in zip(rows, values):
        order = np.argsort(series)
        jitter = np.linspace(-0.13, 0.13, len(series))
        point_y = np.empty(len(series))
        point_y[order] = row + jitter
        ax.scatter(
            series,
            point_y,
            s=15,
            color=COLORS["blue"],
            edgecolors="white",
            linewidths=0.35,
            zorder=2,
        )
        parity = sum(value < 1.0 for value in series)
        ax.text(
            1.03,
            row,
            "{}/12".format(parity),
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=FIGURE_TICK_FONT,
            color=COLORS["dark"],
            fontweight="bold",
        )
    ax.axvline(1.0, color="#333333", linewidth=0.75, linestyle="--")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(compact_tick))
    ax.set_yticks(rows)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Projected runtime / native HPC runtime (x)")
    ax.set_xlim(0.08, 55.0)
    style_axis(ax, grid="x")
    add_top_legend(
        fig,
        [
            legend_marker("#777777"),
            Rectangle((0, 0), 1, 1, facecolor="#D8E4F0", edgecolor="#4A4A4A"),
            Line2D([0], [0], color="#111111", linewidth=1.4),
            Line2D([0], [0], color="#333333", linewidth=0.75, linestyle="--"),
        ],
        ["Record", "Q1--Q3", "Median", "Equal runtime"],
        ncol=4,
        y=0.99,
        fontsize=FIGURE_TICK_FONT,
    )
    fig.subplots_adjust(left=0.31, right=0.82, bottom=0.23, top=0.72)
    path = os.path.join(FIG_DIR, "lsqca_matched_replacement.pdf")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
    return path


def main():
    apply_paper_style()
    ensure_fig_dir()
    paths = [
        figure_intro_threshold_summary(),
        figure_design_overview(),
        figure_feedback_aggregator_architecture(),
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
        figure_roofline_native_stress(),
        figure_threshold_tail_pressure(),
        figure_projected_time_decomposition(),
        figure_workload_growth(),
        figure_advantage_frontier(),
        figure_sensitivity_bottleneck_transition(),
        figure_sensitivity_runtime_parity(),
        figure_physical_factory_crossover(),
        figure_physical_post_rotation_utility(),
        figure_native_rotation_platform_legend(),
        figure_native_rotation_platform(
            "neutral_atom_zoned", "native_rotation_neutral_atom.pdf"
        ),
        figure_native_rotation_platform(
            "trapped_ion_qccd", "native_rotation_trapped_ion.pdf"
        ),
        figure_quality_eligibility(),
        figure_trace_aware_lower_bound(),
        figure_ft_contract_parameters(),
        figure_ft_reliability_target(),
        figure_joint_phase_map(),
        figure_resource_removal_ceiling(),
        figure_lsqca_replacement(),
        figure_sim_hardware_modality_pivot(),
        figure_architecture_focus_matrix(),
        figure_workload_taxonomy(),
        figure_scaling_legend(),
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
