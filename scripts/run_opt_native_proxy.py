#!/usr/bin/env python3
"""Measure stronger same-input native MaxCut baselines at proxy scale."""

import argparse
import csv
import json
import math
import random
import statistics
import time
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


def make_graph(n, density, seed):
    rng = np.random.default_rng(seed)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < density:
                edges.append((i, j, float(rng.uniform(0.5, 1.5))))
    if not edges:
        raise RuntimeError("generated graph has no edges")
    return edges


def score(bits, edges):
    return sum(weight for i, j, weight in edges if bits[i] != bits[j])


def greedy(n, edges):
    adjacency = [[] for _ in range(n)]
    for i, j, weight in edges:
        adjacency[i].append((j, weight))
        adjacency[j].append((i, weight))
    bits = np.zeros(n, dtype=np.int8)
    assigned = np.zeros(n, dtype=bool)
    order = sorted(range(n), key=lambda v: -sum(w for _, w in adjacency[v]))
    for v in order:
        gain_zero = sum(w for u, w in adjacency[v] if assigned[u] and bits[u] == 1)
        gain_one = sum(w for u, w in adjacency[v] if assigned[u] and bits[u] == 0)
        bits[v] = int(gain_one > gain_zero)
        assigned[v] = True
    return bits


def local_search(initial, edges, restarts, seed):
    rng = np.random.default_rng(seed)
    n = len(initial)
    best = initial.copy()
    best_score = score(best, edges)
    starts = [initial.copy()]
    starts.extend(rng.integers(0, 2, size=n, dtype=np.int8) for _ in range(restarts - 1))
    for bits in starts:
        current = score(bits, edges)
        while True:
            best_gain = 1e-12
            best_vertex = None
            for v in range(n):
                bits[v] ^= 1
                candidate = score(bits, edges)
                bits[v] ^= 1
                gain = candidate - current
                if gain > best_gain:
                    best_gain = gain
                    best_vertex = v
            if best_vertex is None:
                break
            bits[best_vertex] ^= 1
            current += best_gain
        if current > best_score:
            best = bits.copy()
            best_score = current
    return best


def anneal(initial, edges, steps, seed):
    rng = np.random.default_rng(seed)
    bits = initial.copy()
    current = score(bits, edges)
    best = bits.copy()
    best_score = current
    for step in range(steps):
        temperature = max(1e-3, 2.0 * (1.0 - step / steps))
        vertex = int(rng.integers(0, len(bits)))
        bits[vertex] ^= 1
        candidate = score(bits, edges)
        delta = candidate - current
        if delta >= 0 or rng.random() < math.exp(delta / temperature):
            current = candidate
            if current > best_score:
                best = bits.copy()
                best_score = current
        else:
            bits[vertex] ^= 1
    return best


def solve_milp(n, edges, time_limit):
    m = len(edges)
    rows, cols, data, lower, upper = [], [], [], [], []

    def add_constraint(coefficients, lo, hi):
        row = len(lower)
        for col, value in coefficients:
            rows.append(row)
            cols.append(col)
            data.append(value)
        lower.append(lo)
        upper.append(hi)

    for edge_index, (i, j, _) in enumerate(edges):
        y = n + edge_index
        add_constraint([(y, 1), (i, -1), (j, -1)], -np.inf, 0)
        add_constraint([(y, 1), (i, 1), (j, 1)], -np.inf, 2)
        add_constraint([(y, -1), (i, 1), (j, -1)], -np.inf, 0)
        add_constraint([(y, -1), (i, -1), (j, 1)], -np.inf, 0)

    objective = np.zeros(n + m)
    objective[n:] = [-weight for _, _, weight in edges]
    matrix = coo_matrix((data, (rows, cols)), shape=(len(lower), n + m)).tocsr()
    started = time.perf_counter()
    result = milp(
        c=objective,
        integrality=np.ones(n + m),
        bounds=Bounds(np.zeros(n + m), np.ones(n + m)),
        constraints=LinearConstraint(matrix, np.asarray(lower), np.asarray(upper)),
        options={"time_limit": time_limit, "mip_rel_gap": 1e-4},
    )
    elapsed = time.perf_counter() - started
    value = float(-result.fun) if result.fun is not None else None
    return value, elapsed, int(result.status), str(result.message), getattr(result, "mip_gap", None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="50,75,100")
    parser.add_argument("--densities", default="0.10,0.25")
    parser.add_argument("--seeds", default="17,31,43")
    parser.add_argument("--milp-time-limit", type=float, default=10.0)
    parser.add_argument("--output-prefix", default="data/processed/perlmutter/opt_native_proxy")
    args = parser.parse_args()

    rows = []
    for n in [int(value) for value in args.sizes.split(",")]:
        for density in [float(value) for value in args.densities.split(",")]:
            for seed in [int(value) for value in args.seeds.split(",")]:
                edges = make_graph(n, density, seed)
                methods = []
                started = time.perf_counter()
                greedy_bits = greedy(n, edges)
                methods.append(("greedy", score(greedy_bits, edges), time.perf_counter() - started, None, None))
                started = time.perf_counter()
                local_bits = local_search(greedy_bits, edges, restarts=16, seed=seed + 1000)
                methods.append(("local_search_16x", score(local_bits, edges), time.perf_counter() - started, None, None))
                started = time.perf_counter()
                anneal_bits = anneal(local_bits, edges, steps=200 * n, seed=seed + 2000)
                methods.append(("simulated_annealing", score(anneal_bits, edges), time.perf_counter() - started, None, None))
                value, elapsed, status, message, gap = solve_milp(n, edges, args.milp_time_limit)
                methods.append(("scipy_highs_milp", value, elapsed, status, gap))
                best = max(value for _, value, _, _, _ in methods if value is not None)
                for method, value, elapsed, status, gap in methods:
                    rows.append({
                        "nodes": n,
                        "density": density,
                        "seed": seed,
                        "edges": len(edges),
                        "method": method,
                        "objective": value,
                        "best_observed_ratio": value / best if value is not None else None,
                        "runtime_sec": elapsed,
                        "solver_status": status,
                        "mip_gap": gap,
                        "milp_message": message if method == "scipy_highs_milp" else None,
                    })

    prefix = Path(args.output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    with prefix.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    method_summary = {}
    for method in sorted({row["method"] for row in rows}):
        selected = [row for row in rows if row["method"] == method]
        method_summary[method] = {
            "median_runtime_sec": statistics.median(row["runtime_sec"] for row in selected),
            "median_best_observed_ratio": statistics.median(
                row["best_observed_ratio"] for row in selected
            ),
            "best_observed_count": sum(
                abs(row["best_observed_ratio"] - 1.0) < 1e-9 for row in selected
            ),
            "record_count": len(selected),
        }
    summary = {
        "schema": "qsup.opt-native-proxy.v1",
        "scope": "same-input deployment-facing MaxCut proxy; not a QAOA application-quality run",
        "milp_time_limit_sec": args.milp_time_limit,
        "instance_count": len(rows) // 4,
        "method_summary": method_summary,
        "records": rows,
    }
    with prefix.with_suffix(".json").open("w") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"instances": len(rows) // 4, "records": len(rows), "output": str(prefix)}, indent=2))


if __name__ == "__main__":
    main()
