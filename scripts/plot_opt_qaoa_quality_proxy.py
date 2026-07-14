#!/usr/bin/env python3
"""Plot directly optimized QAOA quality against compiled two-qubit work."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import NullFormatter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/perlmutter/qaoa_scale_depth_closure.json"
OUTPUT = ROOT / "paper/figures/opt_qaoa_quality_proxy.pdf"


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
    data = json.loads(SOURCE.read_text())
    records = [
        record
        for case in data["case_results"]
        for record in case["records"]
    ]
    styles = {
        10: ("#8f2925", "o", "-"),
        14: ("#b73733", "s", "--"),
        18: ("#d45b55", "^", "-."),
        20: ("#e9837f", "D", ":"),
    }
    fig, ax = plt.subplots(figsize=(2.24, 2.30))
    for qubits in (10, 14, 18, 20):
        selected = [record for record in records if record["qubits"] == qubits]
        if not selected:
            continue
        x_values = []
        y_values = []
        lower = []
        upper = []
        for depth in range(1, 6):
            depth_records = [
                record for record in selected if record["depth_p"] == depth
            ]
            x_values.append(
                float(np.median([
                    record["compiled"][0]["two_qubit_gates"]
                    for record in depth_records
                ]))
            )
            ratios = [record["ideal_approximation_ratio"] for record in depth_records]
            y_values.append(float(np.median(ratios)))
            lower.append(float(min(ratios)))
            upper.append(float(max(ratios)))
        color, marker, linestyle = styles[qubits]
        ax.plot(
            x_values,
            y_values,
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=1.35,
            markersize=4.2,
            label="{}q".format(qubits),
            zorder=3,
        )
        if qubits != 20:
            ax.fill_between(
                x_values,
                lower,
                upper,
                color=color,
                alpha=0.10,
                linewidth=0,
            )
    ax.text(23, 0.725, "$p=1$", fontsize=8.3, color="#555555")
    ax.text(203, 0.955, "$p=5$", fontsize=8.3, color="#555555")
    ax.set_xscale("log")
    ax.set_xlim(18, 285)
    ax.set_ylim(0.70, 0.985)
    ax.set_xticks((20, 50, 100, 200))
    ax.set_xticklabels(("20", "50", "100", "200"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Two-qubit gates (all-to-all)")
    ax.set_ylabel("Approximation ratio (higher is better)")
    ax.grid(True, axis="both", which="both", linestyle=":", linewidth=0.6, color="#b8b8b8")
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=4,
        frameon=False,
        fontsize=8.3,
        handlelength=1.3,
        handletextpad=0.3,
        columnspacing=0.65,
    )
    ax.tick_params(labelsize=8.3)
    fig.subplots_adjust(left=0.25, right=0.98, bottom=0.20, top=0.80)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT)
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
