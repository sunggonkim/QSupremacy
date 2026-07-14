#!/usr/bin/env python3
"""Attach literature-calibrated native-rotation platform timing envelopes."""

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / (
    "data/processed/perlmutter/"
    "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv"
)
DEFAULT_CHEM = ROOT / "data/processed/perlmutter/chem_compiled_measurement_records.json"
DEFAULT_FT = ROOT / "data/processed/perlmutter/ft_reliability_and_space_budget.json"
DEFAULT_OUTPUT = ROOT / "data/processed/perlmutter/native_rotation_platform_envelopes.json"


PLATFORMS = {
    "neutral_atom_zoned": {
        "label": "Neutral atom (zoned)",
        "oneq_sec": 5.0e-6,
        "twoq_sec": 270.0e-9,
        "readout_sec": 4.0e-3,
        "control_sec_per_evaluation": 0.5e-3,
        "initialization_sec": 0.0,
        "cooling_sec_per_routing_equivalent": 0.0,
        "routing_mode": "reconfigurable connectivity; no SWAP charge",
        "evidence": (
            "Nature 649 (2026): about 5-us robust global rotations, 270-ns "
            "entangling gates, zoned arbitrary connectivity, and a 4-ms "
            "optimized readout/reuse cycle; 0.5-ms control is an optimistic "
            "per-evaluation lower-bound attachment"
        ),
    },
    "trapped_ion_qccd": {
        "label": "Trapped ion (QCCD/TILT)",
        "oneq_sec": 10.0e-6,
        "twoq_sec": 48.0e-6,
        "readout_sec": 150.0e-6,
        "control_sec_per_evaluation": 0.0,
        "initialization_sec": 10.0e-3,
        "cooling_sec_per_routing_equivalent": 40.0e-6,
        "routing_mode": (
            "compiled extra-2Q routing equivalents price a 40-us recooling "
            "lower bound; not a full QCCD schedule"
        ),
        "evidence": (
            "BOSS HPCA 2025: optimistic AM nearest-distance gate of about "
            "48 us, about 40-us sympathetic recooling, and >150-us "
            "high-fidelity readout; 10-us 1Q is an explicit optimistic target"
        ),
    },
}


WORKLOAD_LABELS = {
    "ml": "ML",
    "chemistry": "Chem.",
    "optimization": "Opt.",
    "simulation": "Sim.",
}


def as_float(row, key, default=0.0):
    value = row.get(key, default)
    if value in (None, ""):
        return default
    return float(value)


def read_rows(path):
    with Path(path).open(newline="") as handle:
        return [row for row in csv.DictReader(handle) if row.get("status") == "ok"]


def persist(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def chemistry_attachment(path):
    artifact = json.loads(Path(path).read_text())
    selected = [
        record
        for record in artifact["records"]
        if record["evidence_level"] == "compiled_executed_ansatz"
        and record["qubits"] in (6, 8)
    ]
    groups = median(record["measurement_groups_per_eval"] for record in selected)
    shots = median(record["shot_executions_per_eval"] for record in selected)
    routing = median(
        next(
            item["routing_multiplier_vs_all_to_all"]
            for item in record["topologies"]
            if item["topology"] == "grid"
        )
        for record in selected
    )
    qubits = median(record["qubits"] for record in selected)
    return {
        "groups": float(groups),
        "shots": float(shots),
        "routing": float(routing),
        "qubits": float(qubits),
        "record_count": len(selected),
    }


def estimate_qubits(row, chem):
    workload = row["workload"]
    if workload == "chemistry":
        return chem["qubits"]
    if workload == "optimization":
        return max(2.0, as_float(row, "opt_nodes", 2.0))
    if workload == "simulation":
        return max(2.0, as_float(row, "sim_qubits", 2.0))
    return max(
        2.0,
        as_float(row, "ml_features", 0.0),
        as_float(row, "ml_classes", 0.0),
    )


def row_attachment(row, chem):
    if row["workload"] == "chemistry":
        return chem["groups"], chem["shots"], chem["routing"]
    return 1.0, 1.0e4, 1.0


def platform_components(row, platform, chem):
    qubits = estimate_qubits(row, chem)
    evaluations = max(1.0, as_float(row, "circuit_evaluations", 1.0))
    groups, shots_per_evaluation, routing = row_attachment(row, chem)
    oneq = as_float(row, "one_qubit_gates")
    twoq = as_float(row, "two_qubit_gates")
    oneq_parallelism = max(1.0, qubits)
    twoq_parallelism = max(1.0, math.floor(qubits / 2.0))

    oneq_sec = (
        oneq
        * shots_per_evaluation
        * platform["oneq_sec"]
        / oneq_parallelism
    )
    twoq_sec = (
        twoq
        * shots_per_evaluation
        * platform["twoq_sec"]
        / twoq_parallelism
    )
    readout_sec = (
        evaluations * shots_per_evaluation * platform["readout_sec"]
    )
    routing_equivalents = max(0.0, twoq * (routing - 1.0))
    movement_control_sec = (
        platform["initialization_sec"]
        + evaluations * groups * platform["control_sec_per_evaluation"]
        + routing_equivalents
        * shots_per_evaluation
        * platform["cooling_sec_per_routing_equivalent"]
        / twoq_parallelism
    )
    components = {
        "oneq": oneq_sec,
        "twoq": twoq_sec,
        "readout": readout_sec,
        "movement_control": movement_control_sec,
    }
    total = sum(components.values())
    native = max(1.0e-12, as_float(row, "native_runtime_sec", 0.0))
    utilities = {
        name: total / max(1.0e-30, total - 0.9 * value)
        for name, value in components.items()
    }
    return {
        "record_id": Path(row["file"]).stem,
        "workload": row["workload"],
        "qubits": qubits,
        "evaluations": evaluations,
        "measurement_groups": groups,
        "shots_per_evaluation": shots_per_evaluation,
        "routing_multiplier": routing,
        "components_sec": components,
        "component_fraction": {
            name: value / total for name, value in components.items()
        },
        "total_sec": total,
        "native_ratio": total / native,
        "tenfold_utility": utilities,
        "dominant_component": max(components, key=components.get),
    }


def quantile(values, fraction):
    ordered = sorted(values)
    index = int(round(fraction * (len(ordered) - 1)))
    return float(ordered[index])


def summarize(records):
    result = {}
    for workload in WORKLOAD_LABELS:
        selected = [record for record in records if record["workload"] == workload]
        component_names = ("oneq", "twoq", "readout", "movement_control")
        fractions = {
            name: median(record["component_fraction"][name] for record in selected)
            for name in component_names
        }
        fraction_sum = sum(fractions.values())
        fractions = {name: value / fraction_sum for name, value in fractions.items()}
        utilities = {
            name: median(record["tenfold_utility"][name] for record in selected)
            for name in component_names
        }
        dominant = max(utilities, key=utilities.get)
        result[workload] = {
            "label": WORKLOAD_LABELS[workload],
            "cases": len(selected),
            "median_component_fraction": fractions,
            "median_tenfold_utility": utilities,
            "first_target": dominant,
            "first_target_tenfold_speedup": utilities[dominant],
            "median_projected_native_ratio": median(
                record["native_ratio"] for record in selected
            ),
            "p90_projected_native_ratio": quantile(
                [record["native_ratio"] for record in selected], 0.9
            ),
        }
    return result


def summarize_selected(records, label):
    component_names = ("oneq", "twoq", "readout", "movement_control")
    fractions = {
        name: median(record["component_fraction"][name] for record in records)
        for name in component_names
    }
    fraction_sum = sum(fractions.values())
    fractions = {name: value / fraction_sum for name, value in fractions.items()}
    utilities = {
        name: median(record["tenfold_utility"][name] for record in records)
        for name in component_names
    }
    dominant = max(utilities, key=utilities.get)
    return {
        "label": label,
        "cases": len(records),
        "record_ids": sorted(record["record_id"] for record in records),
        "median_component_fraction": fractions,
        "median_tenfold_utility": utilities,
        "first_target": dominant,
        "first_target_tenfold_speedup": utilities[dominant],
        "median_projected_native_ratio": median(
            record["native_ratio"] for record in records
        ),
        "p90_projected_native_ratio": quantile(
            [record["native_ratio"] for record in records], 0.9
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--chem-compiled", type=Path, default=DEFAULT_CHEM)
    parser.add_argument("--ft-contract", type=Path, default=DEFAULT_FT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = read_rows(args.input)
    chem = chemistry_attachment(args.chem_compiled)
    ft_artifact = json.loads(args.ft_contract.read_text())
    eligible_ids = {
        contract["reliability_leading_term"]["record_id"]
        for case in ft_artifact["quality_qualified_case_contracts"]
        for contract in case["ft_contracts"]
        if contract["contract"]["contract"] == "strict_all_shots"
        and abs(float(contract["physical_error_rate"]) - 1.0e-3) <= 1.0e-15
        and abs(
            float(contract["contract"]["application_failure_budget"]) - 0.01
        )
        <= 1.0e-15
    }
    output = {
        "schema": "qsup.native-rotation-platform-envelopes.v2",
        "scope": (
            "execution-only, literature-calibrated native-rotation envelopes "
            "over measured controlled-suite gate/evaluation/shot demand; "
            "count-based intra-circuit parallelism is optimistic, hardware "
            "noise and fault-tolerance overhead are omitted, and QCCD routing "
            "uses a compiled-extra-gate recooling lower bound rather than a "
            "full device schedule"
        ),
        "input": str(args.input.relative_to(ROOT)),
        "cases": len(rows),
        "chem_attachment": chem,
        "platforms": {},
    }
    for platform_id, parameters in PLATFORMS.items():
        records = [
            platform_components(row, parameters, chem) for row in rows
        ]
        eligible_sim = [
            record
            for record in records
            if record["record_id"] in eligible_ids
        ]
        if len(eligible_sim) != len(eligible_ids):
            raise RuntimeError(
                "eligible Sim record mismatch: {} of {}".format(
                    len(eligible_sim), len(eligible_ids)
                )
            )
        output["platforms"][platform_id] = {
            "parameters": parameters,
            "by_workload": summarize(records),
            "quality_qualified_sim": summarize_selected(
                eligible_sim, "Quality-qualified Sim."
            ),
        }
    persist(args.output, output)
    print(json.dumps({"output": str(args.output), "cases": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
