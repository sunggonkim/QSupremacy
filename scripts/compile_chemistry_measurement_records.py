#!/usr/bin/env python3
"""Compile representative VQE measurement records with grouping and routing."""

import argparse
import csv
import importlib.metadata
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import CouplingMap


DEFAULT_FIXTURES = (
    "benchmarks/workloads/hamiltonians/lih_sto3g_active_6q.json",
    "benchmarks/workloads/hamiltonians/lih_sto3g_active_8q.json",
    "benchmarks/workloads/hamiltonians/h2o_sto3g_active_6q.json",
    "benchmarks/workloads/hamiltonians/h2o_sto3g_active_8q.json",
)


def load_fixture(path):
    data = json.loads(Path(path).read_text())
    non_identity = [
        item for item in data["terms"] if set(item["pauli"].upper()) != {"I"}
    ]
    operator = SparsePauliOp.from_list(
        [(item["pauli"].upper(), complex(item["coefficient"])) for item in non_identity]
    )
    groups = operator.group_commuting(qubit_wise=True)
    return data, groups


def quality_lookup(path):
    values = defaultdict(list)
    with Path(path).open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("workload") != "chemistry":
                continue
            key = (row.get("problem_name"), int(float(row.get("chem_layers", 0))))
            values[key].append(float(row["quality_gap"]))
    result = {}
    for key, gaps in values.items():
        result[key] = {
            "cases": len(gaps),
            "median_absolute_energy_error_ha": float(np.median(gaps)),
            "best_absolute_energy_error_ha": float(min(gaps)),
        }
    return result


def shot_allocation(groups, total_shots, minimum_shots):
    weights = [float(np.sum(np.abs(group.coeffs))) for group in groups]
    total_weight = max(sum(weights), 1.0e-12)
    allocation = [
        max(minimum_shots, int(round(total_shots * weight / total_weight)))
        for weight in weights
    ]
    return allocation, weights


def ansatz_circuit(qubits, layers, dense_entangler, seed):
    rng = np.random.default_rng(seed + 100 * layers + qubits)
    circuit = QuantumCircuit(qubits, qubits)
    for _ in range(layers):
        for qubit in range(qubits):
            circuit.ry(float(rng.uniform(-math.pi, math.pi)), qubit)
        if dense_entangler:
            for left in range(qubits):
                for right in range(left + 1, qubits):
                    circuit.cx(left, right)
        else:
            for qubit in range(qubits - 1):
                circuit.cx(qubit, qubit + 1)
        for qubit in range(qubits):
            circuit.rz(float(rng.uniform(-math.pi, math.pi)), qubit)
    return circuit


def append_measurement_basis(circuit, group):
    labels = group.paulis.to_labels()
    qubits = circuit.num_qubits
    basis = ["I"] * qubits
    for label in labels:
        for label_index, pauli in enumerate(label):
            if pauli == "I":
                continue
            qubit = qubits - label_index - 1
            if basis[qubit] not in ("I", pauli):
                raise RuntimeError("non-QWC group returned by group_commuting")
            basis[qubit] = pauli
    measured = circuit.copy()
    for qubit, pauli in enumerate(basis):
        if pauli == "X":
            measured.h(qubit)
        elif pauli == "Y":
            measured.sdg(qubit)
            measured.h(qubit)
    measured.measure(range(qubits), range(qubits))
    return measured, "".join(reversed(basis))


def topology_map(name, qubits):
    if name == "all_to_all":
        return CouplingMap.from_full(qubits, bidirectional=True)
    if name == "line":
        return CouplingMap.from_line(qubits, bidirectional=True)
    if name == "grid":
        if qubits % 2:
            raise ValueError("grid topology requires an even qubit count")
        return CouplingMap.from_grid(2, qubits // 2, bidirectional=True)
    raise ValueError("unknown topology: {}".format(name))


def summarize_compilation(circuits, shots_by_group):
    aggregate = defaultdict(int)
    shot_weighted = defaultdict(int)
    max_depth = 0
    max_twoq_depth = 0
    per_group = []
    for index, (circuit, shots) in enumerate(zip(circuits, shots_by_group)):
        counts = {str(name): int(count) for name, count in circuit.count_ops().items()}
        oneq = sum(counts.get(name, 0) for name in ("rz", "sx", "x"))
        twoq = counts.get("cx", 0)
        measurement = counts.get("measure", 0)
        depth = int(circuit.depth())
        twoq_depth = int(
            circuit.depth(
                filter_function=lambda instruction: instruction.operation.name == "cx"
            )
        )
        aggregate["one_qubit_gates"] += oneq
        aggregate["two_qubit_gates"] += twoq
        aggregate["measurement_ops"] += measurement
        shot_weighted["one_qubit_gates"] += oneq * shots
        shot_weighted["two_qubit_gates"] += twoq * shots
        shot_weighted["measurement_ops"] += measurement * shots
        max_depth = max(max_depth, depth)
        max_twoq_depth = max(max_twoq_depth, twoq_depth)
        per_group.append({
            "group": index,
            "shots": shots,
            "depth": depth,
            "two_qubit_depth": twoq_depth,
            "one_qubit_gates": oneq,
            "two_qubit_gates": twoq,
            "measurement_ops": measurement,
        })
    return {
        "per_evaluation_group_sum": dict(aggregate),
        "per_evaluation_shot_weighted": dict(shot_weighted),
        "max_group_depth": max_depth,
        "max_group_two_qubit_depth": max_twoq_depth,
        "groups": per_group,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", nargs="+", default=list(DEFAULT_FIXTURES))
    parser.add_argument("--layers", default="1,2")
    parser.add_argument("--topologies", default="all_to_all,line,grid")
    parser.add_argument("--total-shots-per-eval", type=int, default=100000)
    parser.add_argument("--minimum-shots-per-group", type=int, default=100)
    parser.add_argument("--rotation-synthesis-epsilon", type=float, default=1.0e-10)
    parser.add_argument("--t-states-per-rotation", type=int)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--quality-summary",
        default=(
            "data/processed/perlmutter/"
            "practical_suite_chem_active_6q8q_1node_20260704233824_summary.csv"
        ),
    )
    parser.add_argument(
        "--output",
        default="data/processed/perlmutter/chem_compiled_measurement_records.json",
    )
    args = parser.parse_args()

    layers_values = [int(value) for value in args.layers.split(",")]
    topologies = [value.strip() for value in args.topologies.split(",")]
    measured_quality = quality_lookup(args.quality_summary)
    if args.t_states_per_rotation is None:
        t_states_per_rotation_proxy = int(
            math.ceil(3.0 * math.log2(1.0 / args.rotation_synthesis_epsilon))
        )
    else:
        t_states_per_rotation_proxy = args.t_states_per_rotation
    output = {
        "schema": "qsup.chem-compiled-measurement-records.v1",
        "scope": (
            "compiled QWC measurement and routing attachment for executed "
            "hardware-efficient VQE ansatze; dense entanglers are an explicitly "
            "labeled routing stress and do not inherit the measured quality"
        ),
        "quality_source": args.quality_summary,
        "shot_allocation": {
            "method": "group coefficient L1 weight with a per-group minimum",
            "target_total_shots_per_evaluation": args.total_shots_per_eval,
            "minimum_shots_per_group": args.minimum_shots_per_group,
        },
        "t_state_proxy": {
            "status": "synthesis upper contract, not estimator output",
            "epsilon": args.rotation_synthesis_epsilon,
            "formula": "ceil(3*log2(1/epsilon)) T states per arbitrary rotation",
            "t_states_per_rotation": t_states_per_rotation_proxy,
        },
        "software": {
            "qiskit": importlib.metadata.version("qiskit"),
        },
        "records": [],
    }

    for fixture_path in args.fixtures:
        fixture, groups = load_fixture(fixture_path)
        shots_by_group, group_weights = shot_allocation(
            groups, args.total_shots_per_eval, args.minimum_shots_per_group
        )
        for layers in layers_values:
            for dense_entangler in (False, True):
                evidence = "routing_stress_only" if dense_entangler else "compiled_executed_ansatz"
                variant = "dense_entangler_stress" if dense_entangler else "linear_executed"
                logical = ansatz_circuit(
                    int(fixture["n_qubits"]), layers, dense_entangler, args.seed
                )
                measurement_circuits = []
                bases = []
                for group in groups:
                    measured, basis = append_measurement_basis(logical, group)
                    measurement_circuits.append(measured)
                    bases.append(basis)
                all_to_all_twoq = None
                topology_records = []
                for topology in topologies:
                    compiled = transpile(
                        measurement_circuits,
                        basis_gates=["rz", "sx", "x", "cx"],
                        coupling_map=topology_map(topology, int(fixture["n_qubits"])),
                        optimization_level=3,
                        seed_transpiler=args.seed,
                    )
                    summary = summarize_compilation(compiled, shots_by_group)
                    twoq = summary["per_evaluation_group_sum"]["two_qubit_gates"]
                    if topology == "all_to_all":
                        all_to_all_twoq = max(1, twoq)
                    summary["topology"] = topology
                    summary["routing_multiplier_vs_all_to_all"] = None
                    topology_records.append(summary)
                if all_to_all_twoq is None:
                    raise RuntimeError("all_to_all must be included for routing normalization")
                for summary in topology_records:
                    summary["routing_multiplier_vs_all_to_all"] = (
                        summary["per_evaluation_group_sum"]["two_qubit_gates"]
                        / all_to_all_twoq
                    )
                quality = measured_quality.get((fixture["name"], layers))
                arbitrary_rotations_per_group = 2 * int(fixture["n_qubits"]) * layers
                output["records"].append({
                    "fixture": fixture["name"],
                    "fixture_path": fixture_path,
                    "qubits": int(fixture["n_qubits"]),
                    "pauli_terms_total": len(fixture["terms"]),
                    "pauli_terms_measured": sum(len(group) for group in groups),
                    "measurement_groups_per_eval": len(groups),
                    "group_basis": bases,
                    "group_coefficient_l1_weights": group_weights,
                    "shots_by_group": shots_by_group,
                    "shot_executions_per_eval": int(sum(shots_by_group)),
                    "layers": layers,
                    "ansatz_variant": variant,
                    "evidence_level": evidence,
                    "mid_circuit_measurement": False,
                    "intra_circuit_feedforward": False,
                    "measured_quality": quality if not dense_entangler else None,
                    "arbitrary_rotations_per_group": arbitrary_rotations_per_group,
                    "t_state_demand_proxy_per_eval": (
                        arbitrary_rotations_per_group
                        * len(groups)
                        * t_states_per_rotation_proxy
                    ),
                    "topologies": topology_records,
                })

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"output": str(path), "records": len(output["records"])}, indent=2))


if __name__ == "__main__":
    main()
