#!/usr/bin/env python3
"""Plot active-space chemistry quality against measurement growth."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "data/processed/perlmutter/chem_active_space_pair_ucc_closure.json"
)
OUTPUT_JSON = ROOT / "data/processed/perlmutter/chem_vqe_quality_cost_proxy.json"
OUTPUT_FIGURE = ROOT / "paper/figures/chem_vqe_quality_cost_proxy.pdf"


def compiled_value(record, topology, key):
    return next(
        item[key] for item in record["compiled"] if item["topology"] == topology
    )


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
    source = json.loads(SOURCE.read_text())
    if source.get("status") != "complete":
        raise RuntimeError("chemistry closure artifact is not complete")

    records = []
    for qubits in sorted({record["qubits"] for record in source["records"]}):
        candidates = [
            record for record in source["records"] if record["qubits"] == qubits
        ]
        selected = min(candidates, key=lambda record: record["vqe_error_ha"])
        one_rep = next(
            record for record in candidates if record["ansatz_reps"] == 1
        )
        two_rep = next(
            record for record in candidates if record["ansatz_reps"] == 2
        )
        records.append(
            {
                "qubits": qubits,
                "active_spatial_orbitals": selected["active_spatial_orbitals"],
                "active_electrons": selected["active_electrons"],
                "hf_error_ha": selected["hf_error_ha"],
                "best_pair_ucc_error_ha": selected["vqe_error_ha"],
                "best_pair_ucc_reps": selected["ansatz_reps"],
                "one_rep_error_ha": one_rep["vqe_error_ha"],
                "two_rep_error_ha": two_rep["vqe_error_ha"],
                "qwc_groups": selected["measurement"]["qwc_groups"],
                "pauli_terms": selected["measurement"]["pauli_terms_measured"],
                "state_independent_shot_bound": selected["measurement"][
                    "state_independent_shot_bound_for_target_error"
                ],
                "best_all_to_all_two_qubit_gates": compiled_value(
                    selected, "all_to_all", "two_qubit_gates"
                ),
                "best_line_routing_multiplier": compiled_value(
                    selected, "line", "routing_multiplier_vs_all_to_all"
                ),
            }
        )

    output = {
        "status": "complete",
        "scope": source["scope"],
        "source": str(SOURCE.relative_to(ROOT)),
        "quality_tolerance_hartree": source["quality_target_ha"],
        "records": records,
    }
    OUTPUT_JSON.write_text(json.dumps(output, indent=2) + "\n")

    qubits = [record["qubits"] for record in records]
    hf_error = [record["hf_error_ha"] for record in records]
    pair_error = [record["best_pair_ucc_error_ha"] for record in records]
    tick_labels = [
        "{}\n({})".format(record["qubits"], record["qwc_groups"])
        for record in records
    ]

    fig, ax = plt.subplots(figsize=(2.24, 2.30))
    ax.plot(
        qubits,
        hf_error,
        color="#666666",
        marker="o",
        markerfacecolor="white",
        markeredgewidth=1.0,
        linestyle="--",
        linewidth=1.25,
        markersize=4.3,
        label="HF",
    )
    ax.plot(
        qubits,
        pair_error,
        color="#287b76",
        marker="s",
        linestyle="-",
        linewidth=1.5,
        markersize=4.3,
        label="Pair-UCC",
    )
    ax.axhline(
        output["quality_tolerance_hartree"],
        color="#9b2f2a",
        linestyle=":",
        linewidth=1.1,
        label="0.01 Ha",
    )
    ax.set_xlim(3.4, 16.6)
    ax.set_ylim(-0.006, 0.295)
    ax.set_xticks(qubits)
    ax.set_xticklabels(tick_labels)
    ax.set_xlabel("Qubits (measurement groups)")
    ax.set_ylabel("Energy error vs. exact (Hartree)")
    ax.grid(True, axis="y", linestyle=":", linewidth=0.6, color="#b8b8b8")
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=3,
        frameon=False,
        fontsize=8.3,
        handlelength=1.25,
        handletextpad=0.3,
        columnspacing=0.7,
    )
    ax.tick_params(labelsize=8.3)
    fig.subplots_adjust(left=0.27, right=0.98, bottom=0.26, top=0.80)
    OUTPUT_FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FIGURE)
    plt.close(fig)
    print(OUTPUT_JSON)
    print(OUTPUT_FIGURE)


if __name__ == "__main__":
    main()
