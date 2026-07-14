#!/usr/bin/env python3
"""Estimate the measured QAOA depth ladder with Microsoft QDK QRE."""

import argparse
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np
from qdk.qiskit import estimate
from qiskit import QuantumCircuit


QUBIT_MODELS = ("qubit_gate_ns_e3", "qubit_gate_ns_e4")


def make_graph(qubits, density, seed):
    rng = np.random.default_rng(seed)
    edges = []
    for left in range(qubits):
        for right in range(left + 1, qubits):
            if rng.random() < density:
                edges.append((left, right, float(rng.uniform(0.5, 1.5))))
    return edges


def qaoa_circuit(qubits, edges, betas, gammas):
    circuit = QuantumCircuit(qubits)
    circuit.h(range(qubits))
    for beta, gamma in zip(betas, gammas):
        for left, right, weight in edges:
            circuit.rzz(-float(gamma) * weight, left, right)
        circuit.rx(2.0 * float(beta), range(qubits))
    circuit.measure_all()
    return circuit


def compact_result(result):
    physical = result["physicalCounts"]
    breakdown = physical["breakdown"]
    logical = result["logicalCounts"]
    return {
        "physical_qubits": int(physical["physicalQubits"]),
        "runtime_ns": int(physical["runtime"]),
        "runtime_sec": float(physical["runtime"]) * 1.0e-9,
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


def persist(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/perlmutter/qaoa_scale_depth_closure.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/processed/perlmutter/"
            "qdk_resource_estimator_qaoa_depth_crosscheck.json"
        ),
    )
    args = parser.parse_args()

    source = json.loads(args.input.read_text())
    if source.get("status") != "complete":
        raise RuntimeError("QAOA depth closure is not complete")

    output = {
        "schema": "qsup.qdk-resource-estimator-qaoa-depth-crosscheck.v1",
        "scope": (
            "QDK QRE for each directly optimized 10/14/18/20-qubit p=1--5 "
            "QAOA circuit; estimates one circuit execution and excludes finite "
            "shots, parameter-search repetitions, host/control tails, and any "
            "claim of hardware-backed noise behavior"
        ),
        "source_artifact": str(args.input),
        "software": {
            "qdk": importlib.metadata.version("qdk"),
            "qiskit": importlib.metadata.version("qiskit"),
            "numpy": importlib.metadata.version("numpy"),
        },
        "qubit_models": list(QUBIT_MODELS),
        "records": [],
    }

    for case in sorted(
        source["case_results"], key=lambda item: (item["qubits"], item["seed"])
    ):
        qubits = int(case["qubits"])
        seed = int(case["seed"])
        density = float(case["density"])
        edges = make_graph(qubits, density, seed)
        if len(edges) != int(case["edges"]):
            raise RuntimeError("regenerated graph does not match measured closure")
        for measured in sorted(case["records"], key=lambda item: item["depth_p"]):
            circuit = qaoa_circuit(
                qubits,
                edges,
                measured["optimized_betas"],
                measured["optimized_gammas"],
            )
            record = {
                "qubits": qubits,
                "seed": seed,
                "density": density,
                "edges": len(edges),
                "depth_p": int(measured["depth_p"]),
                "ideal_approximation_ratio": float(
                    measured["ideal_approximation_ratio"]
                ),
                "quality_gap": float(measured["quality_gap"]),
                "qiskit_depth_before_estimator": int(circuit.depth()),
                "qiskit_gate_counts_before_estimator": {
                    str(name): int(count)
                    for name, count in circuit.count_ops().items()
                },
                "estimates": {},
            }
            for model in QUBIT_MODELS:
                started = time.perf_counter()
                raw = estimate(
                    circuit, params={"qubitParams": {"name": model}}
                ).data()
                estimate_record = compact_result(raw)
                estimate_record["estimator_wall_sec"] = (
                    time.perf_counter() - started
                )
                record["estimates"][model] = estimate_record
            output["records"].append(record)
            persist(args.output, output)

    output["record_count"] = len(output["records"])
    output["case_count"] = len(source["case_results"])
    persist(args.output, output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "records": output["record_count"],
                "models": list(QUBIT_MODELS),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
