#!/usr/bin/env python3
"""Add validated p=1 QAOA quality and circuit metadata to MaxCut proxies.

The analytical correlation follows the implementation used by OpenQAOA and the
single-layer Ising expectation formula of Ozaeta et al. (arXiv:2012.03421).
"""

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

from run_opt_native_proxy import make_graph, score


def adjacency_from_edges(n, edges):
    adjacency = [dict() for _ in range(n)]
    for u, v, weight in edges:
        coupling = -0.5 * weight
        adjacency[u][v] = coupling
        adjacency[v][u] = coupling
    return adjacency


def gamma_coefficients(n, edges, gamma):
    adjacency = adjacency_from_edges(n, edges)
    weighted_a_minus_b = 0.0
    weighted_sine_cd = 0.0
    for u, v, weight in edges:
        coupling = adjacency[u][v]
        neighbors = (set(adjacency[u]) | set(adjacency[v])) - {u, v}
        product_minus = 1.0
        product_plus = 1.0
        product_u = 1.0
        product_v = 1.0
        for node in neighbors:
            j_un = adjacency[u].get(node, 0.0)
            j_vn = adjacency[v].get(node, 0.0)
            product_minus *= math.cos(2.0 * gamma * (j_un - j_vn))
            product_plus *= math.cos(2.0 * gamma * (j_un + j_vn))
            product_u *= math.cos(2.0 * gamma * j_un)
            product_v *= math.cos(2.0 * gamma * j_vn)
        weighted_a_minus_b += weight * (product_minus - product_plus)
        weighted_sine_cd += weight * math.sin(2.0 * gamma * coupling) * (
            product_u + product_v
        )
    return weighted_a_minus_b, weighted_sine_cd


def expected_cut(n, edges, beta, gamma):
    a_minus_b, sine_cd = gamma_coefficients(n, edges, gamma)
    # OpenQAOA's analytical expression uses the opposite mixer sign from the
    # direct exp(-i beta sum X) circuit used in the validation below.
    sine = -math.sin(2.0 * beta)
    cosine = math.cos(2.0 * beta)
    weighted_correlation = 0.5 * sine * sine * a_minus_b - sine * cosine * sine_cd
    return 0.5 * sum(weight for _, _, weight in edges) - 0.5 * weighted_correlation


def optimize_p1(n, edges, gamma_points=257, beta_points=129):
    beta_grid = np.linspace(-math.pi / 2.0, math.pi / 2.0, beta_points)
    gamma_scale = max(weight for _, _, weight in edges)
    gamma_limit = 2.0 * math.pi / gamma_scale
    gamma_grid = np.linspace(0.0, gamma_limit, gamma_points)
    best = (-math.inf, 0.0, 0.0)
    started = time.perf_counter()
    for gamma in gamma_grid:
        a_minus_b, sine_cd = gamma_coefficients(n, edges, float(gamma))
        sine = -np.sin(2.0 * beta_grid)
        cosine = np.cos(2.0 * beta_grid)
        correlation = 0.5 * sine * sine * a_minus_b - sine * cosine * sine_cd
        values = 0.5 * sum(weight for _, _, weight in edges) - 0.5 * correlation
        index = int(np.argmax(values))
        if values[index] > best[0]:
            best = (float(values[index]), float(beta_grid[index]), float(gamma))

    gamma_step = gamma_grid[1] - gamma_grid[0]
    beta_step = beta_grid[1] - beta_grid[0]

    def objective(pair):
        return -expected_cut(n, edges, float(pair[0]), float(pair[1]))

    # Coordinate refinement avoids requiring a two-dimensional optimizer API.
    beta, gamma = best[1], best[2]
    for _ in range(3):
        beta_result = minimize_scalar(
            lambda value: -expected_cut(n, edges, value, gamma),
            bounds=(beta - beta_step, beta + beta_step),
            method="bounded",
        )
        beta = float(beta_result.x)
        gamma_result = minimize_scalar(
            lambda value: -expected_cut(n, edges, beta, value),
            bounds=(max(0.0, gamma - gamma_step), min(gamma_limit, gamma + gamma_step)),
            method="bounded",
        )
        gamma = float(gamma_result.x)
    value = expected_cut(n, edges, beta, gamma)
    return value, beta, gamma, time.perf_counter() - started


def direct_statevector_expectation(n, edges, beta, gamma):
    dimension = 1 << n
    states = np.arange(dimension, dtype=np.uint64)
    costs = np.zeros(dimension, dtype=np.float64)
    for u, v, weight in edges:
        costs += weight * (((states >> np.uint64(u)) ^ (states >> np.uint64(v))) & 1)
    vector = np.exp(-1.0j * gamma * costs) / math.sqrt(dimension)
    cosine = math.cos(beta)
    sine = -1.0j * math.sin(beta)
    for qubit in range(n):
        bit = np.uint64(1 << qubit)
        low = states[(states & bit) == 0]
        high = low ^ bit
        low_values = vector[low].copy()
        high_values = vector[high].copy()
        vector[low] = cosine * low_values + sine * high_values
        vector[high] = sine * low_values + cosine * high_values
    return float(np.sum(np.abs(vector) ** 2 * costs))


def validate_formula():
    errors = []
    for n, density, seed in [(4, 0.5, 17), (6, 0.4, 31), (8, 0.3, 43)]:
        edges = make_graph(n, density, seed)
        for beta, gamma in [(0.17, 0.23), (-0.31, 0.71), (0.44, 1.13)]:
            analytical = expected_cut(n, edges, beta, gamma)
            direct = direct_statevector_expectation(n, edges, beta, gamma)
            errors.append(abs(analytical - direct))
    return {"cases": len(errors), "max_abs_error": max(errors)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--native-proxy", default="data/processed/perlmutter/opt_native_proxy.json"
    )
    parser.add_argument(
        "--output", default="data/processed/perlmutter/opt_qaoa_metadata_proxy.json"
    )
    args = parser.parse_args()

    validation = validate_formula()
    if validation["max_abs_error"] > 1e-9:
        raise RuntimeError(f"analytical formula validation failed: {validation}")

    native = json.loads(Path(args.native_proxy).read_text())
    grouped = {}
    for row in native["records"]:
        key = (row["nodes"], row["density"], row["seed"])
        grouped.setdefault(key, []).append(row)

    records = []
    for (n, density, seed), rows in sorted(grouped.items()):
        edges = make_graph(n, density, seed)
        best_observed = max(row["objective"] for row in rows if row["objective"] is not None)
        expectation, beta, gamma, runtime = optimize_p1(n, edges)
        records.append({
            "nodes_qubits": n,
            "density": density,
            "seed": seed,
            "edges": len(edges),
            "depth_p": 1,
            "optimized_expected_cut": expectation,
            "best_observed_native_cut": best_observed,
            "expected_approximation_ratio": expectation / best_observed,
            "beta": beta,
            "gamma": gamma,
            "analytical_optimization_runtime_sec": runtime,
            "initial_hadamards": n,
            "mixer_rx_gates": n,
            "logical_zz_gates": len(edges),
            "cnot_equivalent_gates": 2 * len(edges),
            "measurement_bits_per_shot": n,
        })

    ratios = sorted(row["expected_approximation_ratio"] for row in records)
    output = {
        "schema": "qsup.opt-qaoa-metadata-proxy.v1",
        "scope": (
            "same-input p=1 analytical QAOA expectation and circuit metadata; "
            "not sampled hardware output and not a p>1 quality claim"
        ),
        "formula": "Ozaeta et al. single-layer Ising expectation as implemented by OpenQAOA",
        "formula_validation": validation,
        "instance_count": len(records),
        "median_expected_approximation_ratio": float(np.median(ratios)),
        "min_expected_approximation_ratio": min(ratios),
        "max_expected_approximation_ratio": max(ratios),
        "records": records,
    }
    path = Path(args.output)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({
        "instances": len(records),
        "validation_max_abs_error": validation["max_abs_error"],
        "median_expected_approximation_ratio": output["median_expected_approximation_ratio"],
        "output": str(path),
    }, indent=2))


if __name__ == "__main__":
    main()
