#!/usr/bin/env python3
"""Plot the measured Trotter quality-cost proxy."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/perlmutter/chem_sim_native_proxies.json"
OUTPUT = ROOT / "paper/figures/sim_quality_cost_proxy.pdf"


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
    # Simulation uses the paper-wide green family; marker and line style carry width.
    colors = {16: "#2f7d49", 18: "#62a875", 20: "#9ac5a5"}
    markers = {16: "o", 18: "s", 20: "D"}
    linestyles = {16: "-", 18: "--", 20: "-."}
    fig, ax = plt.subplots(figsize=(2.24, 2.30))
    for row in data["simulation"]:
        gates = [point["two_qubit_gates"] for point in row["trotter_quality"]]
        fidelity = [point["fidelity_to_krylov"] for point in row["trotter_quality"]]
        ax.plot(
            gates,
            fidelity,
            marker=markers[row["qubits"]],
            linestyle=linestyles[row["qubits"]],
            linewidth=1.6,
            markersize=4.5,
            color=colors[row["qubits"]],
            label=f'{row["qubits"]}q',
        )
    ax.axhline(0.99, color="#555555", linestyle="--", linewidth=0.9, label="0.99")
    ax.set_xlabel("Two-qubit gates")
    ax.set_ylabel("State fidelity vs. Krylov reference")
    ax.set_ylim(0.74, 1.01)
    ax.grid(True, axis="both", linestyle=":", linewidth=0.6, color="#b8b8b8")
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=4,
        frameon=False,
        fontsize=8.3,
        handlelength=0.9,
        handletextpad=0.2,
        columnspacing=0.35,
        borderaxespad=0.0,
    )
    ax.tick_params(labelsize=8.3)
    fig.subplots_adjust(left=0.25, right=0.98, bottom=0.20, top=0.80)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Preserve a fixed canvas so all three Figure 5 panels have equal height.
    fig.savefig(OUTPUT)
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
