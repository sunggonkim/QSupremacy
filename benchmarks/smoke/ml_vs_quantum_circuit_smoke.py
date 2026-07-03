#!/usr/bin/env python3
"""Login-node-safe native ML vs quantum-circuit ML smoke test.

This is an application-level smoke test, not a simulator-vs-simulator result.

Native path:
  synthetic classification data -> NumPy logistic regression

Quantum circuit ML path:
  same data -> angle-encoded quantum feature map -> cuStateVec simulation
  -> NumPy logistic regression head on quantum features

Keep the defaults tiny on purpose. Use Slurm jobs for real experiments.
"""

import argparse
import json
import math
import os
import platform
import socket
import sys
import time

import numpy as np


def make_dataset(n_samples, n_features, seed, nonlinear):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n_samples, n_features)).astype(np.float64)
    score = 1.2 * x[:, 0] - 0.8 * x[:, 1]
    if nonlinear:
        score += 0.35 * x[:, 0] * x[:, 1]
    score += 0.15 * rng.normal(size=n_samples)
    y = (score > np.median(score)).astype(np.float64)

    x = (x - x.mean(axis=0)) / (x.std(axis=0) + 1e-12)
    x = np.clip(x, -3.0, 3.0)
    return x, y


def split_dataset(x, y, train_frac):
    n_train = int(round(x.shape[0] * train_frac))
    return x[:n_train], y[:n_train], x[n_train:], y[n_train:]


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -40.0, 40.0)))


def train_logistic(x_train, y_train, x_test, y_test, steps, lr):
    start = time.perf_counter()
    x_train_b = np.concatenate([x_train, np.ones((x_train.shape[0], 1))], axis=1)
    x_test_b = np.concatenate([x_test, np.ones((x_test.shape[0], 1))], axis=1)
    w = np.zeros(x_train_b.shape[1], dtype=np.float64)

    for _ in range(steps):
        pred = sigmoid(x_train_b @ w)
        grad = x_train_b.T @ (pred - y_train) / x_train_b.shape[0]
        w -= lr * grad

    train_pred = sigmoid(x_train_b @ w) >= 0.5
    test_pred = sigmoid(x_test_b @ w) >= 0.5
    elapsed = time.perf_counter() - start
    return {
        "runtime_sec": elapsed,
        "train_accuracy": float(np.mean(train_pred == y_train)),
        "test_accuracy": float(np.mean(test_pred == y_test)),
        "parameters": int(w.size),
    }


def ry(theta):
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return np.ascontiguousarray([[c, -s], [s, c]], dtype=np.complex128)


def rz(theta):
    return np.ascontiguousarray(
        [[np.exp(-0.5j * theta), 0.0], [0.0, np.exp(0.5j * theta)]],
        dtype=np.complex128,
    )


def extract_quantum_features(x, depth, entangle, phase):
    import cupy as cp
    from cuquantum import ComputeType, cudaDataType
    from cuquantum.bindings import custatevec as cusv

    n_samples, n_qubits = x.shape
    if n_qubits > 12:
        raise ValueError("Refusing to run >12 qubits in login-node smoke mode.")

    sv_type = int(cudaDataType.CUDA_C_64F)
    matrix_type = int(cudaDataType.CUDA_C_64F)
    layout = int(cusv.MatrixLayout.ROW)
    compute_type = int(ComputeType.COMPUTE_64F)
    state_dim = 1 << n_qubits
    handle = cusv.create()
    features = np.empty((n_samples, n_qubits * 2), dtype=np.float64)
    gate_count = 0
    start = time.perf_counter()

    try:
        state = cp.zeros(state_dim, dtype=cp.complex128)
        probs_host = np.empty(state_dim, dtype=np.float64)
        amps_host = np.empty(state_dim, dtype=np.complex128)

        def apply_gate(matrix, targets, controls=None, control_values=None):
            controls_local = [] if controls is None else controls
            values_local = [] if control_values is None else control_values
            workspace_size = cusv.apply_matrix_get_workspace_size(
                handle,
                sv_type,
                n_qubits,
                matrix.ctypes.data,
                matrix_type,
                layout,
                0,
                len(targets),
                len(controls_local),
                compute_type,
            )
            workspace = cp.cuda.alloc(workspace_size) if workspace_size else None
            workspace_ptr = workspace.ptr if workspace is not None else 0
            cusv.apply_matrix(
                handle,
                state.data.ptr,
                sv_type,
                n_qubits,
                matrix.ctypes.data,
                matrix_type,
                layout,
                0,
                targets,
                len(targets),
                controls_local,
                values_local,
                len(controls_local),
                compute_type,
                workspace_ptr,
                workspace_size,
            )

        x_gate = np.ascontiguousarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)

        for sample_id, sample in enumerate(x):
            state.fill(0.0)
            state[0] = 1.0
            for layer in range(depth):
                for q, value in enumerate(sample):
                    angle = float(value * math.pi / 3.0)
                    apply_gate(ry(angle), [q])
                    gate_count += 1
                    if phase:
                        apply_gate(rz(angle * (layer + 1)), [q])
                        gate_count += 1
                if entangle:
                    for q in range(n_qubits - 1):
                        apply_gate(x_gate, [q + 1], [q], [1])
                        gate_count += 1

            cp.cuda.Stream.null.synchronize()
            amps_host[:] = cp.asnumpy(state)
            probs_host[:] = np.abs(amps_host) ** 2
            for q in range(n_qubits):
                mask = 1 << q
                z = 0.0
                x_exp = 0.0
                for basis, prob in enumerate(probs_host):
                    if basis & mask:
                        z -= prob
                    else:
                        z += prob
                        flipped = basis | mask
                        x_exp += 2.0 * np.real(
                            np.conjugate(amps_host[basis]) * amps_host[flipped]
                        )
                features[sample_id, q] = z
                features[sample_id, n_qubits + q] = x_exp

        cp.cuda.Stream.null.synchronize()
        elapsed = time.perf_counter() - start
        return {
            "features": features,
            "metadata": {
                "runtime_sec": elapsed,
                "gate_count": gate_count,
                "state_dim": state_dim,
                "feature_dim": int(features.shape[1]),
                "device": int(cp.cuda.runtime.getDevice()),
                "cupy_used_bytes": int(cp.get_default_memory_pool().used_bytes()),
            },
        }
    finally:
        cusv.destroy(handle)


def run_quantum_path(x_train, y_train, x_test, y_test, depth, steps, lr, entangle, phase):
    start_total = time.perf_counter()
    start = time.perf_counter()
    q_train = extract_quantum_features(x_train, depth, entangle, phase)
    q_test = extract_quantum_features(x_test, depth, entangle, phase)
    feature_time = time.perf_counter() - start
    head = train_logistic(q_train["features"], y_train, q_test["features"], y_test, steps, lr)
    return {
        "status": "ok",
        "total_runtime_sec": time.perf_counter() - start_total,
        "feature_extraction_sec": feature_time,
        "head_training_sec": head["runtime_sec"],
        "train_accuracy": head["train_accuracy"],
        "test_accuracy": head["test_accuracy"],
        "train_feature_metadata": q_train["metadata"],
        "test_feature_metadata": q_test["metadata"],
        "head_parameters": head["parameters"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--features", type=int, default=4)
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--entangle", action="store_true")
    parser.add_argument("--phase", action="store_true")
    parser.add_argument("--nonlinear", action="store_true")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--lr", type=float, default=0.4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    if args.samples > 256 or args.features > 12:
        raise SystemExit("Refusing large login-node smoke test.")

    x, y = make_dataset(args.samples, args.features, args.seed, args.nonlinear)
    x_train, y_train, x_test, y_test = split_dataset(x, y, 0.75)

    native = train_logistic(x_train, y_train, x_test, y_test, args.steps, args.lr)
    try:
        quantum = run_quantum_path(
            x_train,
            y_train,
            x_test,
            y_test,
            args.depth,
            args.steps,
            args.lr,
            args.entangle,
            args.phase,
        )
    except Exception as exc:
        quantum = {
            "status": "error",
            "error": "{}: {}".format(type(exc).__name__, str(exc)),
        }

    result = {
        "metadata": {
            "hostname": socket.gethostname(),
            "cwd": os.getcwd(),
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
        },
        "config": vars(args),
        "dataset": {
            "train_samples": int(x_train.shape[0]),
            "test_samples": int(x_test.shape[0]),
            "native_feature_dim": int(x.shape[1]),
        },
        "native_ml_path": native,
        "quantum_circuit_ml_path": quantum,
    }

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(text)
            f.write("\n")


if __name__ == "__main__":
    main()
