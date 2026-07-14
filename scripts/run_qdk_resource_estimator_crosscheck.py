#!/usr/bin/env python3
"""Run an independent Microsoft QDK resource estimate for matched QAOA records."""

import argparse
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np
from qdk.qiskit import estimate
from qiskit import QuantumCircuit


QUBIT_MODELS = ("qubit_gate_ns_e3", "qubit_gate_ns_e4")


def make_graph(n, density, seed):
    rng = np.random.default_rng(seed)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < density:
                edges.append((i, j, float(rng.uniform(0.5, 1.5))))
    return edges


def build_qaoa(record):
    n = int(record["nodes_qubits"])
    edges = make_graph(n, float(record["density"]), int(record["seed"]))
    if len(edges) != int(record["edges"]):
        raise RuntimeError("regenerated edge count does not match QAOA metadata")
    circuit = QuantumCircuit(n)
    circuit.h(range(n))
    for i, j, weight in edges:
        circuit.rzz(2.0 * float(record["gamma"]) * weight, i, j)
    for qubit in range(n):
        circuit.rx(2.0 * float(record["beta"]), qubit)
    circuit.measure_all()
    return circuit


def compact_result(result):
    physical = result["physicalCounts"]
    breakdown = physical["breakdown"]
    logical = result["logicalCounts"]
    return {
        "physical_qubits": int(physical["physicalQubits"]),
        "runtime_ns": int(physical["runtime"]),
        "runtime_sec": float(physical["runtime"]) * 1e-9,
        "rqops": int(physical["rqops"]),
        "algorithmic_logical_qubits_after_layout": int(
            breakdown["algorithmicLogicalQubits"]
        ),
        "algorithmic_logical_depth": int(breakdown["algorithmicLogicalDepth"]),
        "num_t_states": int(breakdown["numTstates"]),
        "num_t_factories": int(breakdown["numTfactories"]),
        "physical_qubits_for_algorithm": int(
            breakdown["physicalQubitsForAlgorithm"]
        ),
        "physical_qubits_for_t_factories": int(
            breakdown["physicalQubitsForTfactories"]
        ),
        "code_distance": int(result["logicalQubit"]["codeDistance"]),
        "logical_cycle_time_ns": int(result["logicalQubit"]["logicalCycleTime"]),
        "input_logical_counts": {
            "qubits": int(logical["numQubits"]),
            "t_count": int(logical["tCount"]),
            "rotation_count": int(logical["rotationCount"]),
            "rotation_depth": int(logical["rotationDepth"]),
            "measurement_count": int(logical["measurementCount"]),
        },
        "error_budget": result["errorBudget"],
        "qec_scheme": result["jobParams"]["qecScheme"],
        "qubit_params": result["jobParams"]["qubitParams"],
        "estimator_assumptions": result.get("assumptions", []),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--qaoa-metadata",
        default="data/processed/perlmutter/opt_qaoa_metadata_proxy.json",
    )
    parser.add_argument(
        "--output",
        default="data/processed/perlmutter/qdk_resource_estimator_qaoa_crosscheck.json",
    )
    parser.add_argument("--density", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    with open(args.qaoa_metadata) as handle:
        metadata = json.load(handle)
    selected = sorted(
        (
            record
            for record in metadata["records"]
            if abs(float(record["density"]) - args.density) < 1e-12
            and int(record["seed"]) == args.seed
        ),
        key=lambda record: int(record["nodes_qubits"]),
    )
    if [int(record["nodes_qubits"]) for record in selected] != [50, 75, 100]:
        raise RuntimeError("expected matched 50/75/100-qubit QAOA records")

    output = {
        "schema": "qsup.qdk-resource-estimator-crosscheck.v1",
        "scope": (
            "independent circuit-level FT resource-estimator cross-check for one "
            "p=1 QAOA circuit per size; excludes shots, parameter search, host/control "
            "tails, and application-level quality recovery"
        ),
        "source_artifact": args.qaoa_metadata,
        "software": {
            "qdk": importlib.metadata.version("qdk"),
            "qiskit": importlib.metadata.version("qiskit"),
        },
        "records": [],
    }
    for record in selected:
        circuit = build_qaoa(record)
        circuit_record = {
            "nodes_qubits": int(record["nodes_qubits"]),
            "density": float(record["density"]),
            "seed": int(record["seed"]),
            "edges": int(record["edges"]),
            "depth_p": int(record["depth_p"]),
            "beta": float(record["beta"]),
            "gamma": float(record["gamma"]),
            "expected_approximation_ratio": float(
                record["expected_approximation_ratio"]
            ),
            "qiskit_depth_before_estimator": int(circuit.depth()),
            "qiskit_gate_counts_before_estimator": {
                str(name): int(count) for name, count in circuit.count_ops().items()
            },
            "estimates": {},
        }
        for model in QUBIT_MODELS:
            started = time.perf_counter()
            raw = estimate(circuit, params={"qubitParams": {"name": model}}).data()
            estimate_record = compact_result(raw)
            estimate_record["estimator_wall_sec"] = time.perf_counter() - started
            circuit_record["estimates"][model] = estimate_record
        output["records"].append(circuit_record)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")
    print(json.dumps({
        "output": str(output_path),
        "records": len(output["records"]),
        "models": list(QUBIT_MODELS),
    }, indent=2))


if __name__ == "__main__":
    main()
