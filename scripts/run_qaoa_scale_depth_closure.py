#!/usr/bin/env python3
"""Measure ideal QAOA size/depth quality with exact native and routing records."""

import argparse
import concurrent.futures
import importlib.metadata
import json
import math
import os
import time
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap
from scipy.optimize import Bounds, minimize

from run_opt_native_proxy import make_graph
from run_opt_qaoa_metadata_proxy import optimize_p1


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data/processed/perlmutter/qaoa_scale_depth_closure.json"


def parse_ints(text):
    return tuple(int(value.strip()) for value in text.split(",") if value.strip())


def persist(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def cut_values(qubits, edges):
    states = np.arange(1 << qubits, dtype=np.uint32)
    values = np.zeros(1 << qubits, dtype=np.float64)
    for left, right, weight in edges:
        values += weight * (((states >> left) ^ (states >> right)) & 1)
    return values


def qaoa_state(costs, qubits, betas, gammas):
    state = np.full(
        len(costs), 1.0 / math.sqrt(len(costs)), dtype=np.complex128
    )
    for beta, gamma in zip(betas, gammas):
        state *= np.exp(-1.0j * gamma * costs)
        cosine = math.cos(beta)
        sine = -1.0j * math.sin(beta)
        for qubit in range(qubits):
            stride = 1 << qubit
            view = state.reshape(-1, 2 * stride)
            low = view[:, :stride].copy()
            high = view[:, stride:].copy()
            view[:, :stride] = cosine * low + sine * high
            view[:, stride:] = sine * low + cosine * high
    return state


def normalize_parameters(values, depth, gamma_limit):
    values = np.asarray(values, dtype=float)
    betas = ((values[:depth] + math.pi / 2.0) % math.pi) - math.pi / 2.0
    gammas = np.clip(values[depth:], 0.0, gamma_limit)
    return betas, gammas


def expectation(costs, qubits, values, depth, gamma_limit):
    betas, gammas = normalize_parameters(values, depth, gamma_limit)
    state = qaoa_state(costs, qubits, betas, gammas)
    return float(np.dot(np.abs(state) ** 2, costs))


def interpolate_parameters(previous_betas, previous_gammas, new_depth):
    old_axis = np.linspace(0.0, 1.0, len(previous_betas))
    new_axis = np.linspace(0.0, 1.0, new_depth)
    return np.concatenate(
        [
            np.interp(new_axis, old_axis, previous_betas),
            np.interp(new_axis, old_axis, previous_gammas),
        ]
    )


def optimize_deeper(
    costs,
    qubits,
    previous_betas,
    previous_gammas,
    depth,
    gamma_limit,
    restarts,
    max_evaluations,
    seed,
):
    append_zero = np.concatenate(
        [previous_betas, [0.0], previous_gammas, [0.0]]
    )
    starts = [append_zero, interpolate_parameters(previous_betas, previous_gammas, depth)]
    rng = np.random.default_rng(seed)
    while len(starts) < restarts:
        starts.append(
            append_zero + rng.normal(0.0, 0.08, size=2 * depth)
        )

    lower = np.concatenate(
        [np.full(depth, -math.pi / 2.0), np.zeros(depth)]
    )
    upper = np.concatenate(
        [np.full(depth, math.pi / 2.0), np.full(depth, gamma_limit)]
    )
    bounds = Bounds(lower, upper)
    baseline_value = expectation(costs, qubits, append_zero, depth, gamma_limit)
    best = {
        "objective": baseline_value,
        "parameters": append_zero,
        "restart": "append_zero_baseline",
        "success": True,
        "message": "exactly preserves the selected p-1 state",
    }
    total_evaluations = 1
    started = time.perf_counter()
    for restart, initial in enumerate(starts[:restarts]):
        evaluations = {"count": 0}

        def objective(values):
            evaluations["count"] += 1
            return -expectation(costs, qubits, values, depth, gamma_limit)

        result = minimize(
            objective,
            np.clip(initial, lower, upper),
            method="COBYLA",
            bounds=bounds,
            options={
                "maxiter": max_evaluations,
                "rhobeg": 0.18,
                "tol": 1.0e-5,
                "catol": 1.0e-8,
            },
        )
        total_evaluations += evaluations["count"]
        value = -float(result.fun)
        if value > best["objective"]:
            best = {
                "objective": value,
                "parameters": np.asarray(result.x, dtype=float),
                "restart": restart,
                "success": bool(result.success),
                "message": str(result.message),
            }
    betas, gammas = normalize_parameters(
        best["parameters"], depth, gamma_limit
    )
    return {
        "expected_cut": float(best["objective"]),
        "betas": [float(value) for value in betas],
        "gammas": [float(value) for value in gammas],
        "selected_restart": best["restart"],
        "optimizer_success": bool(best["success"]),
        "optimizer_message": str(best["message"]),
        "parameter_evaluations_all_restarts": total_evaluations,
        "max_evaluations_per_restart": max_evaluations,
        "optimization_wall_sec": time.perf_counter() - started,
        "append_zero_baseline_cut": baseline_value,
    }


def qaoa_circuit(qubits, edges, betas, gammas):
    circuit = QuantumCircuit(qubits)
    circuit.h(range(qubits))
    for beta, gamma in zip(betas, gammas):
        for left, right, weight in edges:
            circuit.rzz(-gamma * weight, left, right)
        circuit.rx(2.0 * beta, range(qubits))
    circuit.measure_all()
    return circuit


def topology(name, qubits):
    if name == "all_to_all":
        return CouplingMap.from_full(qubits, bidirectional=True)
    if name == "line":
        return CouplingMap.from_line(qubits, bidirectional=True)
    if name == "grid":
        return CouplingMap.from_grid(2, qubits // 2, bidirectional=True)
    raise ValueError(name)


def compile_records(circuit, seed):
    records = []
    for name in ("all_to_all", "grid", "line"):
        compiled = transpile(
            circuit,
            basis_gates=["rz", "sx", "x", "cx"],
            coupling_map=topology(name, circuit.num_qubits),
            optimization_level=3,
            seed_transpiler=seed,
        )
        counts = {
            str(operation): int(count)
            for operation, count in compiled.count_ops().items()
        }
        records.append(
            {
                "topology": name,
                "depth": int(compiled.depth()),
                "two_qubit_depth": int(
                    compiled.depth(
                        filter_function=lambda instruction: (
                            instruction.operation.name == "cx"
                        )
                    )
                ),
                "one_qubit_gates": int(
                    sum(counts.get(gate, 0) for gate in ("rz", "sx", "x"))
                ),
                "two_qubit_gates": int(counts.get("cx", 0)),
                "measurement_ops": int(counts.get("measure", 0)),
                "gate_counts": counts,
            }
        )
    base = max(1, records[0]["two_qubit_gates"])
    for record in records:
        record["routing_multiplier_vs_all_to_all"] = (
            record["two_qubit_gates"] / base
        )
    return records


def finite_shot_records(costs, state, optimum, seed, shot_values):
    probabilities = np.abs(state) ** 2
    rng = np.random.default_rng(seed)
    records = []
    for shots in shot_values:
        counts = rng.multinomial(shots, probabilities)
        sampled = float(np.dot(counts, costs) / shots)
        records.append(
            {
                "shots": shots,
                "sampled_expected_cut": sampled,
                "sampled_approximation_ratio": sampled / optimum,
            }
        )
    return records


def run_case(case):
    qubits = case["qubits"]
    seed = case["seed"]
    depths = case["depths"]
    restarts = case["restarts"]
    max_evaluations_base = case["max_evaluations_base"]
    shots = case["shots"]
    density = min(0.5, 2.4 / qubits)
    edges = make_graph(qubits, density, seed)
    native_started = time.perf_counter()
    costs = cut_values(qubits, edges)
    optimum = float(np.max(costs))
    native_wall = time.perf_counter() - native_started
    gamma_limit = 2.0 * math.pi / max(weight for _, _, weight in edges)
    records = []
    previous_betas = None
    previous_gammas = None

    for depth in depths:
        if depth == 1:
            value, beta, gamma, wall = optimize_p1(qubits, edges)
            optimized = {
                "expected_cut": value,
                "betas": [beta],
                "gammas": [gamma],
                "selected_restart": "global_analytical_grid_plus_refinement",
                "optimizer_success": True,
                "optimizer_message": "validated p=1 analytical optimum search",
                "parameter_evaluations_all_restarts": 257 * 129,
                "max_evaluations_per_restart": None,
                "optimization_wall_sec": wall,
                "append_zero_baseline_cut": None,
            }
        else:
            optimized = optimize_deeper(
                costs,
                qubits,
                np.asarray(previous_betas),
                np.asarray(previous_gammas),
                depth,
                gamma_limit,
                restarts,
                max_evaluations_base + 12 * depth,
                seed + 1000 * depth,
            )
        previous_betas = optimized["betas"]
        previous_gammas = optimized["gammas"]
        state = qaoa_state(
            costs, qubits, previous_betas, previous_gammas
        )
        direct_value = float(np.dot(np.abs(state) ** 2, costs))
        if abs(direct_value - optimized["expected_cut"]) > 1.0e-8:
            raise RuntimeError("QAOA optimizer/direct-state mismatch")
        circuit = qaoa_circuit(
            qubits, edges, previous_betas, previous_gammas
        )
        record = {
            "qubits": qubits,
            "density": density,
            "seed": seed,
            "edges": len(edges),
            "depth_p": depth,
            "exact_native_objective": optimum,
            "exact_native_scan_wall_sec": native_wall,
            "optimized_expected_cut": direct_value,
            "ideal_approximation_ratio": direct_value / optimum,
            "quality_gap": 1.0 - direct_value / optimum,
            "optimized_betas": previous_betas,
            "optimized_gammas": previous_gammas,
            "optimization": {
                key: value
                for key, value in optimized.items()
                if key not in ("expected_cut", "betas", "gammas")
            },
            "finite_shot_resampling": finite_shot_records(
                costs,
                state,
                optimum,
                seed + 10000 * depth,
                shots,
            ),
            "compiled": compile_records(circuit, seed),
        }
        records.append(record)
    return {
        "qubits": qubits,
        "seed": seed,
        "density": density,
        "edges": len(edges),
        "records": records,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="10,14,18")
    parser.add_argument("--seeds", default="17,31,43")
    parser.add_argument("--cap-size", type=int, default=20)
    parser.add_argument("--cap-seed", type=int, default=17)
    parser.add_argument("--depths", default="1,2,3,4,5")
    parser.add_argument("--shots", default="1024,8192")
    parser.add_argument("--restarts", type=int, default=2)
    parser.add_argument("--max-evaluations-base", type=int, default=60)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    sizes = parse_ints(args.sizes)
    seeds = parse_ints(args.seeds)
    depths = parse_ints(args.depths)
    shots = parse_ints(args.shots)
    if depths != tuple(range(1, max(depths) + 1)):
        raise ValueError("depths must be consecutive and begin at one")
    if any(size % 2 for size in sizes + (args.cap_size,)):
        raise ValueError("grid routing attachment requires even qubit sizes")

    cases = [
        {
            "qubits": size,
            "seed": seed,
            "depths": depths,
            "restarts": args.restarts,
            "max_evaluations_base": args.max_evaluations_base,
            "shots": shots,
        }
        for size in sizes
        for seed in seeds
    ]
    if args.cap_size not in sizes or args.cap_seed not in seeds:
        cases.append(
            {
                "qubits": args.cap_size,
                "seed": args.cap_seed,
                "depths": depths,
                "restarts": args.restarts,
                "max_evaluations_base": args.max_evaluations_base,
                "shots": shots,
            }
        )

    output = {
        "schema": "qsup.qaoa-scale-depth-closure.v1",
        "status": "running",
        "scope": (
            "ideal statevector QAOA on exact weighted MaxCut instances through "
            "20 qubits and p=5; p=1 uses a validated analytical global search, "
            "p>1 uses append-zero-preserving multi-start COBYLA; finite-shot "
            "resampling and compiled routing are attached, while the existing "
            "4/6/8-qubit Aer sweep remains the explicitly synthetic noise study"
        ),
        "software": {
            "numpy": importlib.metadata.version("numpy"),
            "scipy": importlib.metadata.version("scipy"),
            "qiskit": importlib.metadata.version("qiskit"),
        },
        "host": os.uname().nodename,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "sizes_three_seeds": list(sizes),
        "seeds": list(seeds),
        "cap_case": {"qubits": args.cap_size, "seed": args.cap_seed},
        "depths": list(depths),
        "shots": list(shots),
        "optimizer": {
            "p1": "257x129 analytical grid plus coordinate refinement",
            "p_gt_1": "append-zero and interpolated starts with bounded COBYLA",
            "restarts": args.restarts,
            "max_evaluations_base": args.max_evaluations_base,
        },
        "case_results": [],
    }
    persist(args.output, output)

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(run_case, case): case for case in cases}
        for future in concurrent.futures.as_completed(futures):
            case = futures[future]
            result = future.result()
            output["case_results"].append(result)
            output["case_results"].sort(key=lambda item: (item["qubits"], item["seed"]))
            persist(args.output, output)
            print(
                json.dumps(
                    {
                        "completed": [result["qubits"], result["seed"]],
                        "cases": len(output["case_results"]),
                        "total_cases": len(cases),
                        "final_depth_ratio": result["records"][-1]["ideal_approximation_ratio"],
                    }
                ),
                flush=True,
            )

    output["status"] = "complete"
    output["record_count"] = sum(
        len(case["records"]) for case in output["case_results"]
    )
    persist(args.output, output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "cases": len(output["case_results"]),
                "records": output["record_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
