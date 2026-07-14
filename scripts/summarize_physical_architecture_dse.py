#!/usr/bin/env python3
"""Build a literature-calibrated QPU marginal-utility design-space artifact."""

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks" / "workloads"))

from run_practical_suite import build_maxcut_edges  # noqa: E402
from hpca_projection_model import as_float, projected_components_sec  # noqa: E402


TOLERANCES = {
    "ml": 0.02,
    "chemistry": 0.01,
    "optimization": 0.02,
    "simulation": 0.01,
}


# A favorable cross-workload synthesis envelope aligned to the matched QDK
# QAOA estimates. Chem compiler artifacts retain their separate epsilon-based
# upper contract, but the physical DSE deliberately does not consume it.
PROJECTION_T_STATES_PER_ROTATION = 16.0


SCENARIOS = (
    {
        "id": "surface_measured_control",
        "label": "Measured-control surface envelope",
        "distance": 25.0,
        "cycle_sec": 1.1e-6,
        "shot_lanes": 1.0e3,
        "decoder_sec_per_eval": 63.0e-6,
        "factory_count": 64.0,
        "host_io_floor_sec_per_eval": 10.0e-6,
        "evidence": (
            "Google 1.1-us correction cycle and 63-us mean distance-5 decoder; "
            "64 factories lies inside the 57--88 QDK QAOA estimates; shot lanes "
            "and d=25 are explicit design assumptions"
        ),
    },
    {
        "id": "surface_estimator_aligned",
        "label": "Estimator-aligned surface envelope",
        "distance": 15.0,
        "cycle_sec": 0.4e-6,
        "shot_lanes": 1.0e4,
        "decoder_sec_per_eval": 5.0e-6,
        "factory_count": 64.0,
        "host_io_floor_sec_per_eval": 5.0e-6,
        "evidence": (
            "d=13--15 and 5.2--6.0-us logical cycles match the QDK QAOA "
            "cross-check; decoder, host, and useful-lane values are targets"
        ),
    },
    {
        "id": "surface_throughput_target",
        "label": "Throughput-target surface envelope",
        "distance": 15.0,
        "cycle_sec": 0.4e-6,
        "shot_lanes": 1.0e5,
        "decoder_sec_per_eval": 1.0e-6,
        "factory_count": 512.0,
        "host_io_floor_sec_per_eval": 1.0e-6,
        "evidence": (
            "forward architecture target; physical cycle/code distance remain "
            "estimator-aligned while lanes, factories, decode, and host scale"
        ),
    },
)


LEVERS = (
    ("shot_fabric", "10x useful shot lanes"),
    ("logical_cycle", "10x logical-cycle speed"),
    ("routing", "remove routing dilation"),
    ("factory", "10x factory supply"),
    ("decoder", "10x decoder latency/bandwidth"),
    ("host_feedback", "10x host/link latency"),
    ("measurement_grouping", "10x fewer shot-group executions"),
    (
        "native_rotation",
        "native arbitrary-rotation path (cross-modality counterfactual)",
    ),
)

MAGIC_SUPPLY_ENVELOPES = (
    {
        "id": "baseline",
        "factory_supply_multiplier": 1.0,
        "scope": "estimator-aligned baseline",
    },
    {
        "id": "pure_magic_reported_upper",
        "factory_supply_multiplier": 4.5,
        "scope": (
            "v4 average magic-state preparation-time reduction; used only as "
            "a favorable supply-equivalent stress (the reported 15x is an "
            "end-to-end scheduler-efficiency upper result, not uniform supply)"
        ),
    },
    {
        "id": "star_magic_reported_upper",
        "factory_supply_multiplier": 100.0,
        "scope": (
            "order-of-magnitude upper envelope for compatible small-angle "
            "rotations; not transferable to every arbitrary rotation"
        ),
    },
    {
        "id": "four_order_target",
        "factory_supply_multiplier": 1.0e4,
        "scope": "diagnostic target, not a published implementation",
    },
)


def read_rows(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def load_chem_attachment(path):
    artifact = json.loads(Path(path).read_text())
    records = {}
    for record in artifact["records"]:
        if record["evidence_level"] != "compiled_executed_ansatz":
            continue
        key = (record["fixture"], int(record["layers"]))
        all_to_all = next(
            item for item in record["topologies"]
            if item["topology"] == "all_to_all"
        )
        grid = next(item for item in record["topologies"] if item["topology"] == "grid")
        shot_executions = max(1.0, float(record["shot_executions_per_eval"]))
        all_weighted = all_to_all["per_evaluation_shot_weighted"]
        grid_weighted = grid["per_evaluation_shot_weighted"]
        all_twoq = max(1.0, float(all_weighted["two_qubit_gates"]))
        records[key] = {
            "measurement_groups_per_eval": record["measurement_groups_per_eval"],
            "shot_executions_per_eval": record["shot_executions_per_eval"],
            "one_qubit_gates_per_shot": (
                float(all_weighted["one_qubit_gates"]) / shot_executions
            ),
            "two_qubit_gates_per_shot": all_twoq / shot_executions,
            "measurement_ops_per_shot": (
                float(all_weighted["measurement_ops"]) / shot_executions
            ),
            "routing_multiplier": (
                float(grid_weighted["two_qubit_gates"]) / all_twoq
            ),
            "arbitrary_rotations_per_shot": float(
                record["arbitrary_rotations_per_group"]
            ),
            "source": "compiled_executed_ansatz",
        }
    return records, artifact


def qaoa_routing_audit(rows):
    keys = sorted(
        {
            (int(float(row["opt_nodes"])), row["opt_graph"])
            for row in rows
            if row.get("workload") == "optimization"
        }
    )
    result = {}
    for qubits, family in keys:
        edges = build_maxcut_edges(qubits, family)
        circuit = QuantumCircuit(qubits)
        circuit.h(range(qubits))
        for left, right in edges:
            circuit.rzz(0.37, left, right)
        circuit.rx(0.41, range(qubits))
        all_to_all = transpile(
            circuit,
            basis_gates=["rz", "sx", "x", "cx"],
            coupling_map=CouplingMap.from_full(qubits, bidirectional=True),
            optimization_level=3,
            seed_transpiler=17,
        )
        columns = int(math.ceil(qubits / 2.0))
        grid = transpile(
            circuit,
            basis_gates=["rz", "sx", "x", "cx"],
            coupling_map=CouplingMap.from_grid(2, columns, bidirectional=True),
            optimization_level=3,
            seed_transpiler=17,
        )
        base_twoq = max(1, int(all_to_all.count_ops().get("cx", 0)))
        grid_twoq = int(grid.count_ops().get("cx", 0))
        result[(qubits, family)] = grid_twoq / base_twoq
    return result


def scenario_config(scenario, levers):
    distance = scenario["distance"]
    cycle = scenario["cycle_sec"]
    factory_rate = scenario["factory_count"] / (15.0 * distance * cycle)
    config = {
        "distance": distance,
        "cycle_sec": cycle,
        "shots_per_group": 1.0e4,
        "shot_lanes": scenario["shot_lanes"],
        "decoder_sec_per_eval": scenario["decoder_sec_per_eval"],
        "decoder_bandwidth_bits_per_sec": 4.0e12,
        "magic_state_factory_rate_per_sec": factory_rate,
        "host_io_floor_sec_per_eval": scenario["host_io_floor_sec_per_eval"],
        "host_link_bandwidth_bytes_per_sec": 64.0e9,
        "enable_queue_model": False,
        "enable_controller_scaling": False,
        "enable_host_context": False,
    }
    if "shot_fabric" in levers:
        config["shot_lanes"] *= 10.0
    if "logical_cycle" in levers:
        config["cycle_sec"] /= 10.0
    if "factory" in levers:
        config["magic_state_factory_rate_per_sec"] *= 10.0
    if "decoder" in levers:
        config["decoder_sec_per_eval"] /= 10.0
        config["decoder_bandwidth_bits_per_sec"] *= 10.0
    if "host_feedback" in levers:
        config["host_io_floor_sec_per_eval"] /= 10.0
        config["host_link_bandwidth_bytes_per_sec"] *= 10.0
    return config


def chemistry_key(row):
    fixture = os.path.basename(row.get("chem_hamiltonian_json", ""))
    layers = int(float(row.get("chem_layers", 1) or 1))
    if fixture == "molecular_chain_4q.json":
        return "molecular_chain_4q_surrogate", layers
    return "H2_minimal_2qubit", layers


def attach_record(row, chem_records, opt_routing, levers):
    attached = dict(row)
    workload = row.get("workload", "unknown")
    routing = 1.0
    groups = 1.0
    shot_executions = 1.0e4
    attachment = "structural_lower_bound"
    if workload == "chemistry":
        key = chemistry_key(row)
        record = chem_records.get(key)
        if record is not None:
            evals = max(1.0, as_float(row, "circuit_evaluations", 1.0))
            groups = float(record["measurement_groups_per_eval"])
            shot_executions = float(record["shot_executions_per_eval"])
            routing = float(record["routing_multiplier"])
            attached["one_qubit_gates"] = (
                evals * record["one_qubit_gates_per_shot"]
            )
            attached["two_qubit_gates"] = (
                evals * record["two_qubit_gates_per_shot"]
            )
            attached["measurement_ops"] = (
                evals * record["measurement_ops_per_shot"]
            )
            attached["compiled_arbitrary_rotations"] = (
                evals * record["arbitrary_rotations_per_shot"]
            )
            attachment = record["source"]
        else:
            groups = 2.0
            shot_executions = 2.0e4
            attachment = "analytical_H2_Z_and_X_measurement_groups"
    elif workload == "optimization":
        key = (int(float(row["opt_nodes"])), row["opt_graph"])
        routing = float(opt_routing[key])
        attachment = "compiled_p1_grid_routing"
    elif workload == "ml":
        attachment = "optimistic_one_group; amplitude-feature readout unresolved"
    elif workload == "simulation":
        attachment = "nearest_neighbor_trotter_and_Z_readout"

    if "routing" in levers:
        routing = 1.0
    if "measurement_grouping" in levers:
        reduced_groups = max(1.0, groups / 10.0)
        grouping_gain = groups / reduced_groups
        shot_executions /= grouping_gain
        groups = reduced_groups

    oneq = as_float(row, "one_qubit_gates", 0.0)
    twoq = as_float(row, "two_qubit_gates", 0.0)
    rotations = oneq
    if workload in ("optimization", "simulation"):
        rotations += twoq
    attached["measurement_groups_per_eval"] = groups
    attached["shot_executions_per_eval"] = shot_executions
    if "native_rotation" in levers:
        attached["magic_state_demand"] = 0.0
    elif workload == "chemistry" and "compiled_arbitrary_rotations" in attached:
        attached["magic_state_demand"] = (
            PROJECTION_T_STATES_PER_ROTATION
            * attached["compiled_arbitrary_rotations"]
        )
    else:
        attached["magic_state_demand"] = (
            PROJECTION_T_STATES_PER_ROTATION * rotations
        )
    return attached, routing, attachment


def dominant_component(components):
    candidates = {
        "logical": components["gate_pipeline_sec"],
        "factory": components["factory_sec"],
        "decoder": components["decode_sec"],
        "host/link": components["host_io_sec"],
    }
    return max(candidates, key=candidates.get)


def evaluate(
    rows,
    scenario,
    chem_records,
    opt_routing,
    levers=(),
    factory_supply_multiplier=1.0,
    serialization_fraction=0.0,
):
    config = scenario_config(scenario, set(levers))
    config["magic_state_factory_rate_per_sec"] *= max(
        1.0, float(factory_supply_multiplier)
    )
    config["critical_path_serialization_fraction"] = min(
        1.0, max(0.0, float(serialization_fraction))
    )
    records = []
    attachment_counts = Counter()
    for row in rows:
        attached, routing, attachment = attach_record(
            row, chem_records, opt_routing, set(levers)
        )
        row_config = dict(config)
        row_config["twoq_routing_multiplier"] = routing
        components = projected_components_sec(attached, row_config)
        native = max(1.0e-12, components["native_deadline_sec"])
        gap = max(0.0, as_float(row, "quality_gap", 0.0))
        tolerance = TOLERANCES.get(row.get("workload"), 0.02)
        runtime_pass = components["total_sec"] < native
        quality_pass = gap <= tolerance
        attachment_counts[attachment] += 1
        records.append({
            "workload": row.get("workload"),
            "ratio": components["total_sec"] / native,
            "runtime_pass": runtime_pass,
            "quality_pass": quality_pass,
            "advantaged": runtime_pass and quality_pass,
            "dominant": dominant_component(components),
            "component_ratio": {
                "logical": components["gate_pipeline_sec"] / native,
                "factory": components["factory_sec"] / native,
                "decoder": components["decode_sec"] / native,
                "host/link": components["host_io_sec"] / native,
            },
        })
    return records, dict(attachment_counts)


def fraction(values):
    values = list(values)
    return sum(bool(value) for value in values) / max(1, len(values))


def summarize_records(records):
    records = list(records)
    ratios = [record["ratio"] for record in records]
    components = {
        name: median([record["component_ratio"][name] for record in records])
        for name in ("logical", "factory", "decoder", "host/link")
    }
    dominant = Counter(record["dominant"] for record in records)
    return {
        "cases": len(records),
        "median_projected_native_ratio": median(ratios),
        "p90_projected_native_ratio": float(sorted(ratios)[int(0.9 * (len(ratios) - 1))]),
        "runtime_pass_fraction": fraction(record["runtime_pass"] for record in records),
        "quality_pass_fraction": fraction(record["quality_pass"] for record in records),
        "advantaged_fraction": fraction(record["advantaged"] for record in records),
        "median_component_native_ratio": components,
        "dominant_component_fraction": {
            name: dominant.get(name, 0) / len(records)
            for name in ("logical", "factory", "decoder", "host/link")
        },
    }


def summarize_qdk_depth(path):
    artifact = json.loads(Path(path).read_text())
    summary = {
        "source_artifact": path,
        "scope": artifact["scope"],
        "records": len(artifact["records"]),
        "by_qubit_model": {},
    }
    for model in artifact["qubit_models"]:
        model_summary = {"by_qubits_and_depth": {}, "distance_transitions": []}
        for qubits in sorted({record["qubits"] for record in artifact["records"]}):
            previous = None
            for depth in sorted(
                {
                    record["depth_p"]
                    for record in artifact["records"]
                    if record["qubits"] == qubits
                }
            ):
                subset = [
                    record
                    for record in artifact["records"]
                    if record["qubits"] == qubits and record["depth_p"] == depth
                ]
                estimates = [record["estimates"][model] for record in subset]
                distances = sorted({item["code_distance"] for item in estimates})
                key = "{}q:p{}".format(qubits, depth)
                model_summary["by_qubits_and_depth"][key] = {
                    "cases": len(subset),
                    "code_distance_values": distances,
                    "median_runtime_sec": median(
                        item["runtime_sec"] for item in estimates
                    ),
                    "median_physical_qubits": median(
                        item["physical_qubits"] for item in estimates
                    ),
                    "median_logical_depth": median(
                        item["algorithmic_logical_depth"] for item in estimates
                    ),
                    "median_factories": median(
                        item["num_t_factories"] for item in estimates
                    ),
                    "median_quality_gap": median(
                        record["quality_gap"] for record in subset
                    ),
                }
                current = max(distances)
                if previous is not None and current > previous:
                    model_summary["distance_transitions"].append(
                        {
                            "qubits": qubits,
                            "from_depth": depth - 1,
                            "to_depth": depth,
                            "from_distance": previous,
                            "to_distance": current,
                        }
                    )
                previous = current
        summary["by_qubit_model"][model] = model_summary
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", required=True)
    parser.add_argument(
        "--chem-compiled",
        default="data/processed/perlmutter/chem_compiled_measurement_records.json",
    )
    parser.add_argument(
        "--chem-controlled-compiled",
        default=(
            "data/processed/perlmutter/"
            "chem_controlled_compiled_measurement_records.json"
        ),
    )
    parser.add_argument(
        "--output",
        default="data/processed/perlmutter/physical_architecture_dse.json",
    )
    parser.add_argument(
        "--qdk-depth",
        default=(
            "data/processed/perlmutter/"
            "qdk_resource_estimator_qaoa_depth_crosscheck.json"
        ),
    )
    args = parser.parse_args()

    rows = read_rows(args.input_csv)
    chem_records, chem_artifact = load_chem_attachment(args.chem_compiled)
    controlled_chem_records, controlled_chem_artifact = load_chem_attachment(
        args.chem_controlled_compiled
    )
    chem_records.update(controlled_chem_records)
    opt_routing = qaoa_routing_audit(rows)
    result = {
        "schema": "qsup.physical-architecture-dse.v3",
        "scope": (
            "technology-calibrated surface-code envelopes and one-factor "
            "marginal utility over paired controlled records; not a vendor "
            "forecast, cycle-accurate QPU model, or present-hardware claim"
        ),
        "input_csv": args.input_csv,
        "cases": len(rows),
        "quality_gate": "measured quality gap only; no free recovery scalar",
        "calibration": {
            "surface_control": "Nature 638 (2025): 1.1-us cycle, 63+/-17-us decoder",
            "factory": "LSQCA: one magic state per 15 code beats per 176-cell factory",
            "rotation_synthesis": (
                "all attached arbitrary rotations are repriced at a favorable "
                "16 T states per rotation, aligned to the matched QDK QAOA "
                "15.0--16.0 range and 57--88 factories; the Chem compiler's "
                "epsilon-based 100-T synthesis upper contract is retained for "
                "provenance but is not consumed by this DSE"
            ),
            "recent_magic_supply": (
                "PureMagic v4 reports 4.5x lower average magic-state preparation "
                "time (its up-to-15x DASCOT result is end-to-end efficiency, not "
                "uniform supply); "
                "STAR-Magic reports up to order-100x only for compatible "
                "small-angle rotations; both are tested as favorable envelopes"
            ),
            "non_ft_context_only": {
                "neutral_atom": (
                    "Nature 626 (2024): 270-ns entangling pulse, 500-us image, "
                    "sub-ms feedforward, reconfigurable connectivity"
                ),
                "trapped_ion": (
                    "BOSS HPCA 2025: circuit-dependent shuttling plus roughly "
                    "40-us recooling and >150-us high-fidelity readout"
                ),
            },
        },
        "scenarios": list(SCENARIOS),
        "projection_t_states_per_arbitrary_rotation": (
            PROJECTION_T_STATES_PER_ROTATION
        ),
        "levers": [{"id": key, "label": label} for key, label in LEVERS],
        "qaoa_grid_routing_multiplier": {
            "{}:{}".format(key[0], key[1]): value
            for key, value in opt_routing.items()
        },
        "chem_compiled_record_count": len(chem_artifact["records"]),
        "chem_controlled_compiled_record_count": len(
            controlled_chem_artifact["records"]
        ),
        "chem_attachment_sources": [
            args.chem_compiled,
            args.chem_controlled_compiled,
        ],
        "qdk_depth_sensitivity": summarize_qdk_depth(args.qdk_depth),
        "by_scenario": {},
    }

    workloads = sorted(set(row["workload"] for row in rows))
    for scenario in SCENARIOS:
        baseline, attachment_counts = evaluate(
            rows, scenario, chem_records, opt_routing
        )
        scenario_result = {
            "attachments": attachment_counts,
            "by_workload": {},
        }
        for workload in workloads:
            base_subset = [item for item in baseline if item["workload"] == workload]
            base_summary = summarize_records(base_subset)
            utility = {}
            improved_cache = {}
            for lever, _ in LEVERS:
                improved, _ = evaluate(
                    rows, scenario, chem_records, opt_routing, (lever,)
                )
                improved_subset = [
                    item for item in improved if item["workload"] == workload
                ]
                improved_cache[lever] = improved_subset
                per_case_speedups = [
                    base["ratio"] / max(1.0e-30, candidate["ratio"])
                    for base, candidate in zip(base_subset, improved_subset)
                ]
                improved_summary = summarize_records(improved_subset)
                utility[lever] = {
                    "median_speedup": median(per_case_speedups),
                    "runtime_pass_gain_percentage_points": 100.0 * (
                        improved_summary["runtime_pass_fraction"]
                        - base_summary["runtime_pass_fraction"]
                    ),
                    "advantage_gain_percentage_points": 100.0 * (
                        improved_summary["advantaged_fraction"]
                        - base_summary["advantaged_fraction"]
                    ),
                }
            resource_levers = [
                lever for lever, _ in LEVERS if lever != "native_rotation"
            ]
            first = max(
                resource_levers,
                key=lambda key: utility[key]["median_speedup"],
            )
            native_subset = improved_cache["native_rotation"]
            post_native_utility = {}
            for lever in resource_levers:
                improved, _ = evaluate(
                    rows,
                    scenario,
                    chem_records,
                    opt_routing,
                    ("native_rotation", lever),
                )
                improved_subset = [
                    item for item in improved if item["workload"] == workload
                ]
                post_native_utility[lever] = median([
                    base["ratio"] / max(1.0e-30, candidate["ratio"])
                    for base, candidate in zip(native_subset, improved_subset)
                ])
            post_native = max(post_native_utility, key=post_native_utility.get)
            component = base_summary["median_component_native_ratio"]
            non_factory_floor = max(
                component["logical"], component["decoder"], component["host/link"]
            )
            scenario_result["by_workload"][workload] = {
                "baseline": base_summary,
                "marginal_utility": utility,
                "first_scalable_resource_target": first,
                "first_scalable_resource_median_speedup": utility[first]["median_speedup"],
                "factory_scale_to_nonfactory_crossover": (
                    component["factory"] / max(non_factory_floor, 1.0e-30)
                ),
                "native_rotation_counterfactual_speedup": utility["native_rotation"][
                    "median_speedup"
                ],
                "post_native_rotation_marginal_utility": post_native_utility,
                "post_native_rotation_target": post_native,
                "post_native_rotation_incremental_speedup": post_native_utility[
                    post_native
                ],
            }
        result["by_scenario"][scenario["id"]] = scenario_result

    aligned = next(
        scenario for scenario in SCENARIOS
        if scenario["id"] == "surface_estimator_aligned"
    )
    result["critical_path_overlap_sensitivity"] = {
        "definition": (
            "rho=0 is ideal overlap; rho=1 serializes logical execution, "
            "factory supply, and decoding; host/control terms remain explicit"
        ),
        "by_rho": {},
    }
    for rho in (0.0, 0.5, 1.0):
        records, _ = evaluate(
            rows,
            aligned,
            chem_records,
            opt_routing,
            serialization_fraction=rho,
        )
        result["critical_path_overlap_sensitivity"]["by_rho"][str(rho)] = {
            workload: summarize_records(
                record for record in records if record["workload"] == workload
            )
            for workload in workloads
        }

    resource_levers = [
        lever for lever, _ in LEVERS if lever != "native_rotation"
    ]
    result["post_native_rotation_overlap_sensitivity"] = {
        "definition": (
            "the native-rotation counterfactual is recomputed at each overlap "
            "endpoint; every one-factor successor uses the same rho"
        ),
        "by_rho": {},
    }
    for rho in (0.0, 0.5, 1.0):
        native_records, _ = evaluate(
            rows,
            aligned,
            chem_records,
            opt_routing,
            levers=("native_rotation",),
            serialization_fraction=rho,
        )
        improved_by_lever = {}
        for lever in resource_levers:
            improved_by_lever[lever], _ = evaluate(
                rows,
                aligned,
                chem_records,
                opt_routing,
                levers=("native_rotation", lever),
                serialization_fraction=rho,
            )
        by_workload = {}
        for workload in workloads:
            base_subset = [
                record
                for record in native_records
                if record["workload"] == workload
            ]
            utility = {}
            for lever in resource_levers:
                improved_subset = [
                    record
                    for record in improved_by_lever[lever]
                    if record["workload"] == workload
                ]
                utility[lever] = median([
                    base["ratio"] / max(1.0e-30, candidate["ratio"])
                    for base, candidate in zip(base_subset, improved_subset)
                ])
            target = max(utility, key=utility.get)
            by_workload[workload] = {
                "baseline": summarize_records(base_subset),
                "marginal_utility": utility,
                "target": target,
                "target_median_speedup": utility[target],
            }
        result["post_native_rotation_overlap_sensitivity"]["by_rho"][
            str(rho)
        ] = by_workload

    result["magic_state_supply_sensitivity"] = {
        "scenario": aligned["id"],
        "envelopes": list(MAGIC_SUPPLY_ENVELOPES),
        "by_envelope": {},
    }
    for envelope in MAGIC_SUPPLY_ENVELOPES:
        records, _ = evaluate(
            rows,
            aligned,
            chem_records,
            opt_routing,
            factory_supply_multiplier=envelope["factory_supply_multiplier"],
        )
        result["magic_state_supply_sensitivity"]["by_envelope"][
            envelope["id"]
        ] = {
            workload: summarize_records(
                record for record in records if record["workload"] == workload
            )
            for workload in workloads
        }

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(path), "cases": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
