#!/usr/bin/env python3
"""Build an offline roofline-native stress artifact for QArchGauge.

This is not a new measured baseline. It is a reviewer-facing stress gate: for
each same-input practical-suite case, attach an optimistic accelerator roofline
proxy to the native path and report how much the native deadline can shrink.
"""

import csv
import json
import math
import os
import statistics

from hpca_projection_model import DEFAULT_PROJECTION_CONFIG
from hpca_projection_model import native_deadline_sec
from hpca_projection_model import projected_components_sec
from hpca_projection_model import roofline_time_sec


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_CSV = os.path.join(
    ROOT,
    "data",
    "processed",
    "perlmutter",
    "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv",
)
OUT_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "roofline_native_stress.json"
)
OUT_CSV = os.path.join(
    ROOT, "data", "processed", "perlmutter", "roofline_native_stress.csv"
)


WORKLOAD_ORDER = [
    ("ml", "ML"),
    ("chemistry", "Chem."),
    ("optimization", "Opt."),
    ("simulation", "Sim."),
]


def f(row, key, default=0.0):
    value = row.get(key, default)
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def graph_edges(n, kind):
    if kind == "ring":
        return max(1.0, n)
    if kind == "ladder":
        return max(1.0, 2.0 * n - 3.0)
    if kind == "chordal":
        return max(1.0, n * (n - 1.0) / 2.0)
    return max(1.0, n * math.log2(max(2.0, n)))


def choose_faster_roofline(candidates, config):
    best = None
    for name, flops, bytes_moved in candidates:
        time_sec = roofline_time_sec(
            flops,
            bytes_moved,
            config.get(
                "native_tensor_core_peak_flops", config["native_peak_flops"]
            ),
            config.get(
                "native_hbm_bandwidth_bytes_per_sec",
                config["native_peak_bytes_per_sec"],
            ),
            config["native_launch_floor_sec"],
        )
        if best is None or time_sec < best["time_sec"]:
            best = {
                "proxy_model": name,
                "native_roofline_flops": flops,
                "native_roofline_bytes": bytes_moved,
                "time_sec": time_sec,
            }
    return best


def estimate_native_proxy(row, config):
    workload = row["workload"]
    if workload == "ml":
        samples = max(1.0, f(row, "ml_samples", 1.0))
        features = max(1.0, f(row, "ml_features", 1.0))
        classes = max(1.0, f(row, "ml_classes", 1.0))
        flops = (
            2.0 * samples * features * classes
            + 2.0 * samples * features * features
            + 2.0 * samples * classes
        )
        bytes_moved = 8.0 * (
            samples * features
            + features * classes
            + samples * classes
            + features * features
        )
        return {
            "proxy_model": "batched-linear-ml-roofline",
            "native_roofline_flops": flops,
            "native_roofline_bytes": bytes_moved,
            "time_sec": roofline_time_sec(
                flops,
                bytes_moved,
                config.get("native_tensor_core_peak_flops", config["native_peak_flops"]),
                config.get("native_hbm_bandwidth_bytes_per_sec", config["native_peak_bytes_per_sec"]),
                config["native_launch_floor_sec"],
            ),
        }

    if workload == "chemistry":
        qubits = 4.0
        dim = 2.0 ** qubits
        terms = max(1.0, f(row, "measurement_ops", 1.0))
        layers = max(1.0, f(row, "chem_layers", 1.0))
        dense = ("dense-active-space-eigensolver", (10.0 / 3.0) * dim ** 3, 16.0 * dim ** 2)
        sparse = (
            "sparse-lanczos-pauli-proxy",
            16.0 * terms * layers * dim,
            32.0 * terms * dim,
        )
        return choose_faster_roofline([dense, sparse], config)

    if workload == "optimization":
        nodes = max(1.0, f(row, "opt_nodes", 1.0))
        edges = graph_edges(nodes, row.get("opt_graph", "generic"))
        exact_states = 2.0 ** nodes
        exact = (
            "exact-maxcut-enumeration",
            6.0 * edges * exact_states,
            8.0 * exact_states + 16.0 * edges,
        )
        heuristic = (
            "edge-local-search-roofline",
            128.0 * edges * max(1.0, nodes),
            64.0 * edges * max(1.0, nodes),
        )
        return choose_faster_roofline([exact, heuristic], config)

    if workload == "simulation":
        qubits = max(1.0, f(row, "sim_qubits", 1.0))
        steps = max(1.0, f(row, "sim_steps", 1.0))
        dim = 2.0 ** qubits
        dense = (
            "dense-hamiltonian-evolution",
            8.0 * steps * dim ** 2,
            16.0 * steps * dim ** 2,
        )
        sparse = (
            "sparse-krylov-hamiltonian-vector",
            32.0 * steps * qubits * dim,
            24.0 * steps * qubits * dim,
        )
        return choose_faster_roofline([dense, sparse], config)

    return {
        "proxy_model": "unknown",
        "native_roofline_flops": 0.0,
        "native_roofline_bytes": 0.0,
        "time_sec": f(row, "native_runtime_sec", 0.0),
    }


def percentile(values, pct):
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct / 100.0
    lo = int(math.floor(rank))
    hi = int(math.ceil(rank))
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - rank) + ordered[hi] * (rank - lo)


def summarize_case(row, launch_floor_sec):
    config = dict(DEFAULT_PROJECTION_CONFIG)
    config["native_launch_floor_sec"] = launch_floor_sec
    proxy = estimate_native_proxy(row, config)
    augmented = dict(row)
    augmented["native_roofline_flops"] = proxy["native_roofline_flops"]
    augmented["native_roofline_bytes"] = proxy["native_roofline_bytes"]
    measured_native = max(1.0e-12, f(row, "native_runtime_sec", 0.0))
    deadline = native_deadline_sec(augmented, config)
    components = projected_components_sec(augmented, config)
    return {
        "proxy_model": proxy["proxy_model"],
        "native_roofline_flops": proxy["native_roofline_flops"],
        "native_roofline_bytes": proxy["native_roofline_bytes"],
        "roofline_time_sec": proxy["time_sec"],
        "native_deadline_sec": deadline,
        "measured_native_sec": measured_native,
        "deadline_shrink_x": measured_native / max(1.0e-12, deadline),
        "projected_ratio_x": components["total_sec"] / max(1.0e-12, deadline),
    }


def main():
    with open(INPUT_CSV, newline="") as fobj:
        rows = list(csv.DictReader(fobj))

    launch_scenarios = {
        "launch_free": 0.0,
        "a100_launch_floor_10us": 10.0e-6,
    }
    case_summaries = []
    for row in rows:
        measured_components = projected_components_sec(row, DEFAULT_PROJECTION_CONFIG)
        measured_native = max(1.0e-12, f(row, "native_runtime_sec", 0.0))
        entry = {
            "workload": row["workload"],
            "measured_native_sec": measured_native,
            "measured_deadline_projected_ratio_x": measured_components["total_sec"]
            / measured_native,
            "quantum_runtime_sec": max(0.0, f(row, "quantum_runtime_sec", 0.0)),
            "quality_gap": max(0.0, f(row, "quality_gap", 0.0)),
        }
        for scenario, launch_floor_sec in launch_scenarios.items():
            entry[scenario] = summarize_case(row, launch_floor_sec)
        case_summaries.append(entry)

    by_workload = {}
    csv_rows = []
    for workload, label in WORKLOAD_ORDER:
        subset = [row for row in case_summaries if row["workload"] == workload]
        measured = [row["measured_native_sec"] for row in subset]
        measured_ratio = [row["measured_deadline_projected_ratio_x"] for row in subset]
        quality = [row["quality_gap"] for row in subset]
        data = {
            "label": label,
            "cases": len(subset),
            "measured_native_median_us": 1.0e6 * statistics.median(measured),
            "measured_deadline_projected_ratio_median_x": statistics.median(
                measured_ratio
            ),
            "quality_gap_median": statistics.median(quality),
        }
        for scenario in launch_scenarios:
            deadlines = [row[scenario]["native_deadline_sec"] for row in subset]
            shrink = [row[scenario]["deadline_shrink_x"] for row in subset]
            ratios = [row[scenario]["projected_ratio_x"] for row in subset]
            roof = [row[scenario]["roofline_time_sec"] for row in subset]
            data.update(
                {
                    "{}_deadline_median_us".format(scenario): 1.0e6
                    * statistics.median(deadlines),
                    "{}_roofline_time_median_us".format(scenario): 1.0e6
                    * statistics.median(roof),
                    "{}_deadline_shrink_median_x".format(scenario): statistics.median(
                        shrink
                    ),
                    "{}_deadline_shrink_p90_x".format(scenario): percentile(shrink, 90),
                    "{}_projected_ratio_median_x".format(scenario): statistics.median(
                        ratios
                    ),
                }
            )
        by_workload[workload] = data
        csv_rows.append({"workload": workload, **data})

    summary = {
        "generated_by": os.path.relpath(__file__, ROOT),
        "input_csv": os.path.relpath(INPUT_CSV, ROOT),
        "output_csv": os.path.relpath(OUT_CSV, ROOT),
        "cases": len(case_summaries),
        "roofline_config": {
            "native_peak_flops": DEFAULT_PROJECTION_CONFIG["native_peak_flops"],
            "native_peak_bytes_per_sec": DEFAULT_PROJECTION_CONFIG[
                "native_peak_bytes_per_sec"
            ],
            "native_tensor_core_peak_flops": DEFAULT_PROJECTION_CONFIG[
                "native_tensor_core_peak_flops"
            ],
            "native_hbm_bandwidth_bytes_per_sec": DEFAULT_PROJECTION_CONFIG[
                "native_hbm_bandwidth_bytes_per_sec"
            ],
            "launch_scenarios": launch_scenarios,
        },
        "formula_notes": [
            "ML uses a batched linear/feature-classifier roofline proxy; the measured PyTorch/XGBoost production-native gate remains the executable baseline check.",
            "Chemistry chooses the faster roofline lower bound between dense active-space eigensolver work and sparse Lanczos/Pauli-term work for the measured active space.",
            "Optimization chooses the faster lower bound between exact MaxCut enumeration and an edge-local-search roofline proxy.",
            "Simulation chooses the faster lower bound between dense Hamiltonian evolution and sparse Krylov Hamiltonian-vector work.",
            "The artifact is an optimistic native stress test: a smaller deadline makes the quantum projection harder and does not replace measured native timings.",
        ],
        "by_workload": by_workload,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as fobj:
        json.dump(summary, fobj, indent=2, sort_keys=True)
        fobj.write("\n")

    fieldnames = [
        "workload",
        "label",
        "cases",
        "measured_native_median_us",
        "quality_gap_median",
        "measured_deadline_projected_ratio_median_x",
        "launch_free_deadline_median_us",
        "launch_free_roofline_time_median_us",
        "launch_free_deadline_shrink_median_x",
        "launch_free_deadline_shrink_p90_x",
        "launch_free_projected_ratio_median_x",
        "a100_launch_floor_10us_deadline_median_us",
        "a100_launch_floor_10us_roofline_time_median_us",
        "a100_launch_floor_10us_deadline_shrink_median_x",
        "a100_launch_floor_10us_deadline_shrink_p90_x",
        "a100_launch_floor_10us_projected_ratio_median_x",
    ]
    with open(OUT_CSV, "w", newline="") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(csv_rows)

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
