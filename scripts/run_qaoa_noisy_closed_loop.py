#!/usr/bin/env python3
"""Run finite-shot noisy QAOA parameter searches on controlled MaxCut cases."""

import argparse
import importlib.metadata
import json
import math
import time
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from run_opt_native_proxy import make_graph, score
from run_opt_qaoa_metadata_proxy import expected_cut


QUBITS = (4, 6, 8)
SEEDS = (17, 31, 43)
SHOTS = (1024, 8192)
TWO_QUBIT_ERRORS = (0.0, 1.0e-3, 1.0e-2)
GRID_POINTS = 9


def exact_best(n, edges):
    best = 0.0
    for state in range(1 << n):
        bits = [(state >> qubit) & 1 for qubit in range(n)]
        best = max(best, score(bits, edges))
    return best


def circuit(n, edges, beta, gamma, measure=True):
    qc = QuantumCircuit(n, n)
    qc.h(range(n))
    for left, right, weight in edges:
        # exp(-i gamma C_uv), C_uv=w(1-ZZ)/2, is RZZ(-gamma*w)
        # up to a global phase.
        qc.rzz(-gamma * weight, left, right)
    for qubit in range(n):
        qc.rx(2.0 * beta, qubit)
    if measure:
        qc.measure(range(n), range(n))
    return qc


def circuit_expected_cut(n, edges, beta, gamma):
    state = Statevector.from_instruction(circuit(n, edges, beta, gamma, False))
    value = 0.0
    for basis, probability in enumerate(state.probabilities()):
        bits = [(basis >> qubit) & 1 for qubit in range(n)]
        value += probability * score(bits, edges)
    return value


def sampled_cut(counts, n, edges):
    total = sum(counts.values())
    value = 0.0
    for bitstring, count in counts.items():
        state = int(bitstring.replace(" ", ""), 2)
        bits = [(state >> qubit) & 1 for qubit in range(n)]
        value += count * score(bits, edges)
    return value / total


def backend_for_error(two_qubit_error):
    if two_qubit_error <= 0.0:
        return AerSimulator()
    model = NoiseModel()
    model.add_all_qubit_quantum_error(
        depolarizing_error(two_qubit_error / 10.0, 1), ["sx", "x"]
    )
    model.add_all_qubit_quantum_error(
        depolarizing_error(two_qubit_error, 2), ["cx"]
    )
    return AerSimulator(noise_model=model)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="data/processed/perlmutter/qaoa_noisy_closed_loop.json",
    )
    args = parser.parse_args()

    output = {
        "schema": "qsup.qaoa-noisy-closed-loop.v2",
        "scope": (
            "controlled 4/6/8-qubit sampled QAOA parameter-grid search under a "
            "synthetic Qiskit Aer depolarizing model; noise-backed, not hardware-backed, "
            "and not a large-graph QAOA claim"
        ),
        "software": {
            "qiskit": importlib.metadata.version("qiskit"),
            "qiskit_aer": importlib.metadata.version("qiskit-aer"),
        },
        "grid_points_per_axis": GRID_POINTS,
        "parameter_evaluations_per_search": GRID_POINTS * GRID_POINTS,
        "shots": list(SHOTS),
        "two_qubit_depolarizing_errors": list(TWO_QUBIT_ERRORS),
        "one_qubit_error_ratio": 0.1,
        "circuit_formula_validation": {},
        "records": [],
    }

    validation_errors = []
    validation_edges = make_graph(4, 0.5, 17)
    for beta, gamma in ((-0.4, 0.2), (0.3, 1.1), (0.7, 2.2)):
        analytical = expected_cut(4, validation_edges, beta, gamma)
        executable = circuit_expected_cut(4, validation_edges, beta, gamma)
        validation_errors.append(abs(analytical - executable))
    max_error = max(validation_errors)
    if max_error > 1.0e-10:
        raise RuntimeError("QAOA circuit/formula mismatch: %.3e" % max_error)
    output["circuit_formula_validation"] = {
        "cases": len(validation_errors),
        "max_abs_error": max_error,
    }

    for n in QUBITS:
        density = {4: 0.5, 6: 0.4, 8: 0.3}[n]
        for seed in SEEDS:
            edges = make_graph(n, density, seed)
            optimum = exact_best(n, edges)
            beta_grid = np.linspace(-math.pi / 2.0, math.pi / 2.0, GRID_POINTS)
            gamma_limit = 2.0 * math.pi / max(weight for _, _, weight in edges)
            gamma_grid = np.linspace(0.0, gamma_limit, GRID_POINTS)
            parameters = [
                (float(beta), float(gamma))
                for gamma in gamma_grid
                for beta in beta_grid
            ]
            base_circuits = [
                circuit(n, edges, beta, gamma) for beta, gamma in parameters
            ]
            for two_qubit_error in TWO_QUBIT_ERRORS:
                backend = backend_for_error(two_qubit_error)
                compiled = transpile(
                    base_circuits,
                    backend,
                    optimization_level=1,
                    seed_transpiler=17,
                )
                for shots in SHOTS:
                    started = time.perf_counter()
                    result = backend.run(
                        compiled,
                        shots=shots,
                        seed_simulator=seed + shots,
                    ).result()
                    wall = time.perf_counter() - started
                    sampled = [
                        sampled_cut(result.get_counts(index), n, edges)
                        for index in range(len(parameters))
                    ]
                    best_index = int(np.argmax(sampled))
                    beta, gamma = parameters[best_index]
                    selected_ideal = expected_cut(n, edges, beta, gamma)
                    output["records"].append({
                        "qubits": n,
                        "density": density,
                        "seed": seed,
                        "edges": len(edges),
                        "two_qubit_depolarizing_error": two_qubit_error,
                        "one_qubit_depolarizing_error": two_qubit_error / 10.0,
                        "shots_per_evaluation": shots,
                        "parameter_evaluations": len(parameters),
                        "total_shots": shots * len(parameters),
                        "search_wall_sec": wall,
                        "selected_beta": beta,
                        "selected_gamma": gamma,
                        "sampled_objective": sampled[best_index],
                        "selected_ideal_objective": selected_ideal,
                        "exact_native_objective": optimum,
                        "sampled_approximation_ratio": sampled[best_index] / optimum,
                        "selected_ideal_approximation_ratio": selected_ideal / optimum,
                        "compiled_depth": int(compiled[best_index].depth()),
                        "compiled_gate_counts": {
                            str(name): int(count)
                            for name, count in compiled[best_index].count_ops().items()
                        },
                    })

    path = Path(args.output)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"output": str(path), "records": len(output["records"])}, indent=2))


if __name__ == "__main__":
    main()
