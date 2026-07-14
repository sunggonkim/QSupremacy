#!/usr/bin/env python3
"""Measure QAOA depth/quality/work growth under finite-shot synthetic noise."""

import argparse
import importlib.metadata
import json
import math
import time
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector

from run_opt_native_proxy import make_graph, score
from run_qaoa_noisy_closed_loop import backend_for_error, exact_best, sampled_cut


DEFAULT_QUBITS = (4, 6, 8)
DEFAULT_SEEDS = (17, 31, 43)
DEFAULT_SHOTS = (1024, 8192)
DEFAULT_TWO_QUBIT_ERRORS = (0.0, 1.0e-3, 1.0e-2)


def parse_values(text, cast):
    return tuple(cast(item.strip()) for item in text.split(",") if item.strip())


def qaoa_circuit(n, edges, betas, gammas, measure=True):
    if len(betas) != len(gammas):
        raise ValueError("beta/gamma depth mismatch")
    qc = QuantumCircuit(n, n if measure else 0)
    qc.h(range(n))
    for beta, gamma in zip(betas, gammas):
        for left, right, weight in edges:
            qc.rzz(-gamma * weight, left, right)
        for qubit in range(n):
            qc.rx(2.0 * beta, qubit)
    if measure:
        qc.measure(range(n), range(n))
    return qc


def ideal_cut(n, edges, betas, gammas):
    state = Statevector.from_instruction(
        qaoa_circuit(n, edges, betas, gammas, measure=False)
    )
    value = 0.0
    for basis, probability in enumerate(state.probabilities()):
        bits = [(basis >> qubit) & 1 for qubit in range(n)]
        value += probability * score(bits, edges)
    return float(value)


def evaluate_candidates(backend, n, edges, candidates, shots, seed):
    circuits = [
        qaoa_circuit(n, edges, item[0], item[1], measure=True)
        for item in candidates
    ]
    compiled = transpile(
        circuits,
        backend,
        optimization_level=1,
        seed_transpiler=17,
    )
    started = time.perf_counter()
    result = backend.run(compiled, shots=shots, seed_simulator=seed).result()
    wall = time.perf_counter() - started
    values = [
        sampled_cut(result.get_counts(index), n, edges)
        for index in range(len(candidates))
    ]
    best_index = int(np.argmax(values))
    return candidates[best_index], float(values[best_index]), compiled[best_index], wall


def search_depth_one(backend, n, edges, shots, seed, grid_points):
    gamma_limit = 2.0 * math.pi / max(weight for _, _, weight in edges)
    candidates = [
        ([float(beta)], [float(gamma)])
        for gamma in np.linspace(0.0, gamma_limit, grid_points)
        for beta in np.linspace(-math.pi / 2.0, math.pi / 2.0, grid_points)
    ]
    selected, objective, compiled, wall = evaluate_candidates(
        backend, n, edges, candidates, shots, seed
    )
    return selected, objective, compiled, wall, len(candidates)


def search_deeper(
    backend,
    n,
    edges,
    shots,
    seed,
    previous,
    depth,
    coordinate_points,
    coordinate_sweeps,
):
    gamma_limit = 2.0 * math.pi / max(weight for _, _, weight in edges)
    betas = list(previous[0]) + [0.0]
    gammas = list(previous[1]) + [0.0]
    if len(betas) != depth:
        raise ValueError("depth warm-start mismatch")
    current = (betas, gammas)
    current_value = -float("inf")
    current_compiled = None
    evaluations = 0
    total_wall = 0.0
    radii = np.linspace(math.pi / 3.0, math.pi / 8.0, coordinate_sweeps)
    for sweep, radius in enumerate(radii):
        for parameter_index in range(2 * depth):
            candidates = []
            for offset in np.linspace(-radius, radius, coordinate_points):
                candidate_betas = list(current[0])
                candidate_gammas = list(current[1])
                if parameter_index < depth:
                    index = parameter_index
                    candidate_betas[index] = float(
                        np.clip(
                            candidate_betas[index] + offset,
                            -math.pi / 2.0,
                            math.pi / 2.0,
                        )
                    )
                else:
                    index = parameter_index - depth
                    candidate_gammas[index] = float(
                        np.clip(candidate_gammas[index] + offset, 0.0, gamma_limit)
                    )
                candidates.append((candidate_betas, candidate_gammas))
            current, current_value, current_compiled, wall = evaluate_candidates(
                backend,
                n,
                edges,
                candidates,
                shots,
                seed + 1000 * depth + 100 * sweep + parameter_index,
            )
            evaluations += len(candidates)
            total_wall += wall
    return current, current_value, current_compiled, total_wall, evaluations


def persist(path, output):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(output, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", default="4,6,8")
    parser.add_argument("--seeds", default="17,31,43")
    parser.add_argument("--shots", default="1024,8192")
    parser.add_argument("--two-qubit-errors", default="0,0.001,0.01")
    parser.add_argument("--depths", default="1,2,3")
    parser.add_argument("--grid-points", type=int, default=9)
    parser.add_argument("--coordinate-points", type=int, default=5)
    parser.add_argument("--coordinate-sweeps", type=int, default=1)
    parser.add_argument(
        "--output",
        default="data/processed/perlmutter/qaoa_depth_quality_closed_loop.json",
    )
    args = parser.parse_args()

    qubits = parse_values(args.qubits, int)
    seeds = parse_values(args.seeds, int)
    shots_values = parse_values(args.shots, int)
    errors = parse_values(args.two_qubit_errors, float)
    depths = parse_values(args.depths, int)
    if depths != tuple(range(1, max(depths) + 1)):
        raise ValueError("depths must be consecutive and start at one")

    output = {
        "schema": "qsup.qaoa-depth-quality-closed-loop.v1",
        "scope": (
            "controlled 4/6/8-qubit finite-shot QAOA depth sweep under a "
            "synthetic Aer depolarizing model; p=1 uses a full grid and p>1 "
            "uses zero-layer warm starts plus sampled coordinate refinement; "
            "noise-backed, not hardware-backed or deployment-scale"
        ),
        "software": {
            "qiskit": importlib.metadata.version("qiskit"),
            "qiskit_aer": importlib.metadata.version("qiskit-aer"),
        },
        "search": {
            "depths": list(depths),
            "grid_points_per_axis_p1": args.grid_points,
            "coordinate_points": args.coordinate_points,
            "coordinate_sweeps": args.coordinate_sweeps,
            "warm_start": "append beta=gamma=0 to preserve the shallower state",
        },
        "shots": list(shots_values),
        "two_qubit_depolarizing_errors": list(errors),
        "one_qubit_error_ratio": 0.1,
        "records": [],
    }
    path = Path(args.output)

    for n in qubits:
        density = {4: 0.5, 6: 0.4, 8: 0.3}.get(n, min(0.5, 2.4 / n))
        for graph_seed in seeds:
            edges = make_graph(n, density, graph_seed)
            optimum = exact_best(n, edges)
            for two_qubit_error in errors:
                backend = backend_for_error(two_qubit_error)
                for shot_count in shots_values:
                    previous = None
                    for depth in depths:
                        search_seed = graph_seed + shot_count + 10000 * depth
                        if depth == 1:
                            selected, sampled, compiled, wall, evaluations = (
                                search_depth_one(
                                    backend,
                                    n,
                                    edges,
                                    shot_count,
                                    search_seed,
                                    args.grid_points,
                                )
                            )
                        else:
                            selected, sampled, compiled, wall, evaluations = search_deeper(
                                backend,
                                n,
                                edges,
                                shot_count,
                                search_seed,
                                previous,
                                depth,
                                args.coordinate_points,
                                args.coordinate_sweeps,
                            )
                        previous = selected
                        ideal = ideal_cut(n, edges, selected[0], selected[1])
                        counts = {
                            str(name): int(count)
                            for name, count in compiled.count_ops().items()
                        }
                        output["records"].append({
                            "qubits": n,
                            "density": density,
                            "seed": graph_seed,
                            "edges": len(edges),
                            "depth_p": depth,
                            "two_qubit_depolarizing_error": two_qubit_error,
                            "one_qubit_depolarizing_error": two_qubit_error / 10.0,
                            "shots_per_evaluation": shot_count,
                            "parameter_evaluations": evaluations,
                            "total_shots": shot_count * evaluations,
                            "search_wall_sec": wall,
                            "selected_betas": selected[0],
                            "selected_gammas": selected[1],
                            "sampled_objective": sampled,
                            "selected_ideal_objective": ideal,
                            "exact_native_objective": optimum,
                            "sampled_approximation_ratio": sampled / optimum,
                            "selected_ideal_approximation_ratio": ideal / optimum,
                            "compiled_depth": int(compiled.depth()),
                            "compiled_two_qubit_depth": int(
                                compiled.depth(
                                    filter_function=lambda instruction: (
                                        instruction.operation.name == "cx"
                                    )
                                )
                            ),
                            "compiled_gate_counts": counts,
                        })
                        persist(path, output)
                        print(
                            json.dumps(
                                {
                                    "qubits": n,
                                    "seed": graph_seed,
                                    "error": two_qubit_error,
                                    "shots": shot_count,
                                    "p": depth,
                                    "ratio": sampled / optimum,
                                    "records": len(output["records"]),
                                }
                            ),
                            flush=True,
                        )

    print(json.dumps({"output": str(path), "records": len(output["records"])}, indent=2))


if __name__ == "__main__":
    main()
