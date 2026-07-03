#!/usr/bin/env python3
"""Digits native ML vs quantum kernel vs QNN/VQC benchmark.

The runner intentionally keeps dependencies small. The digits dataset is
materialized once from scikit-learn into an NPZ file, while this benchmark uses
NumPy plus cuQuantum/cuStateVec.
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


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -40.0, 40.0)))


def accuracy_binary(score, y):
    pred = (score >= 0.5).astype(np.int64)
    return float(np.mean(pred == y))


def bce_loss(score, y):
    score = np.clip(score, 1.0e-8, 1.0 - 1.0e-8)
    return float(-np.mean(y * np.log(score) + (1.0 - y) * np.log(1.0 - score)))


def parse_classes(text):
    classes = [int(x.strip()) for x in text.split(",") if x.strip()]
    if len(classes) != 2:
        raise ValueError("This first benchmark supports exactly two classes.")
    return classes


def load_digits_npz(path, classes, max_samples, seed):
    with np.load(path, allow_pickle=False) as data:
        x_all = data["data"].astype(np.float64) / 16.0
        y_all = data["target"].astype(np.int64)
        metadata = str(data["metadata"]) if "metadata" in data else "{}"

    rng = np.random.default_rng(seed)
    selected = []
    per_class = max_samples // len(classes)
    remainder = max_samples % len(classes)
    for idx, cls in enumerate(classes):
        cls_indices = np.flatnonzero(y_all == cls)
        rng.shuffle(cls_indices)
        take = per_class + (1 if idx < remainder else 0)
        selected.append(cls_indices[:take])

    indices = np.concatenate(selected)
    rng.shuffle(indices)
    x = x_all[indices]
    raw_y = y_all[indices]
    y = (raw_y == classes[1]).astype(np.int64)
    return x, y, raw_y, metadata


def stratified_split(x, y, train_frac, seed):
    rng = np.random.default_rng(seed)
    train_indices = []
    test_indices = []
    for cls in [0, 1]:
        idx = np.flatnonzero(y == cls)
        rng.shuffle(idx)
        n_train = max(1, int(round(idx.size * train_frac)))
        n_train = min(n_train, idx.size - 1)
        train_indices.append(idx[:n_train])
        test_indices.append(idx[n_train:])
    train = np.concatenate(train_indices)
    test = np.concatenate(test_indices)
    rng.shuffle(train)
    rng.shuffle(test)
    return x[train], y[train], x[test], y[test]


def fit_pca_transform(x_train, x_test, pca_dim):
    start = time.perf_counter()
    mean = x_train.mean(axis=0)
    centered = x_train - mean
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    components = vt[:pca_dim]
    train = centered @ components.T
    test = (x_test - mean) @ components.T
    scale = train.std(axis=0) + 1.0e-12
    train = np.clip(train / scale, -3.0, 3.0)
    test = np.clip(test / scale, -3.0, 3.0)
    return train.astype(np.float64), test.astype(np.float64), {
        "runtime_sec": time.perf_counter() - start,
        "input_dim": int(x_train.shape[1]),
        "pca_dim": int(pca_dim),
    }


def train_logistic(x_train, y_train, x_test, y_test, steps, lr):
    start = time.perf_counter()
    x_train_b = np.concatenate([x_train, np.ones((x_train.shape[0], 1))], axis=1)
    x_test_b = np.concatenate([x_test, np.ones((x_test.shape[0], 1))], axis=1)
    w = np.zeros(x_train_b.shape[1], dtype=np.float64)
    losses = []
    for step in range(steps):
        score = sigmoid(x_train_b @ w)
        grad = x_train_b.T @ (score - y_train) / x_train_b.shape[0]
        w -= lr * grad
        if step in (0, steps - 1):
            losses.append(bce_loss(sigmoid(x_train_b @ w), y_train))
    train_score = sigmoid(x_train_b @ w)
    test_score = sigmoid(x_test_b @ w)
    return {
        "model": "logistic_regression_numpy",
        "runtime_sec": time.perf_counter() - start,
        "train_accuracy": accuracy_binary(train_score, y_train),
        "test_accuracy": accuracy_binary(test_score, y_test),
        "loss_trace": losses,
        "parameters": int(w.size),
    }


def train_mlp(x_train, y_train, x_test, y_test, steps, lr, hidden, seed):
    rng = np.random.default_rng(seed)
    start = time.perf_counter()
    d = x_train.shape[1]
    w1 = rng.normal(scale=1.0 / math.sqrt(max(1, d)), size=(d, hidden))
    b1 = np.zeros(hidden, dtype=np.float64)
    w2 = rng.normal(scale=1.0 / math.sqrt(hidden), size=hidden)
    b2 = 0.0
    y_float = y_train.astype(np.float64)
    losses = []

    for step in range(steps):
        h = np.tanh(x_train @ w1 + b1)
        score = sigmoid(h @ w2 + b2)
        dz = (score - y_float) / x_train.shape[0]
        grad_w2 = h.T @ dz
        grad_b2 = float(np.sum(dz))
        dh = dz[:, None] * w2[None, :] * (1.0 - h * h)
        grad_w1 = x_train.T @ dh
        grad_b1 = dh.sum(axis=0)
        w2 -= lr * grad_w2
        b2 -= lr * grad_b2
        w1 -= lr * grad_w1
        b1 -= lr * grad_b1
        if step in (0, steps - 1):
            losses.append(bce_loss(score, y_train))

    train_score = sigmoid(np.tanh(x_train @ w1 + b1) @ w2 + b2)
    test_score = sigmoid(np.tanh(x_test @ w1 + b1) @ w2 + b2)
    return {
        "model": "mlp_numpy",
        "runtime_sec": time.perf_counter() - start,
        "train_accuracy": accuracy_binary(train_score, y_train),
        "test_accuracy": accuracy_binary(test_score, y_test),
        "loss_trace": losses,
        "hidden": int(hidden),
        "parameters": int(w1.size + b1.size + w2.size + 1),
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


class CuStateVecSimulator:
    def __init__(self, n_qubits):
        import cupy as cp
        from cuquantum import ComputeType, cudaDataType
        from cuquantum.bindings import custatevec as cusv

        self.cp = cp
        self.ComputeType = ComputeType
        self.cudaDataType = cudaDataType
        self.cusv = cusv
        self.n_qubits = int(n_qubits)
        self.state_dim = 1 << self.n_qubits
        self.handle = cusv.create()
        self.state = cp.zeros(self.state_dim, dtype=cp.complex128)
        self.sv_type = int(cudaDataType.CUDA_C_64F)
        self.matrix_type = int(cudaDataType.CUDA_C_64F)
        self.layout = int(cusv.MatrixLayout.ROW)
        self.compute_type = int(ComputeType.COMPUTE_64F)
        self.x_gate = np.ascontiguousarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)

    def close(self):
        self.cusv.destroy(self.handle)

    def apply_gate(self, matrix, targets, controls=None, control_values=None):
        controls_local = [] if controls is None else controls
        values_local = [] if control_values is None else control_values
        workspace_size = self.cusv.apply_matrix_get_workspace_size(
            self.handle,
            self.sv_type,
            self.n_qubits,
            matrix.ctypes.data,
            self.matrix_type,
            self.layout,
            0,
            len(targets),
            len(controls_local),
            self.compute_type,
        )
        workspace = self.cp.cuda.alloc(workspace_size) if workspace_size else None
        workspace_ptr = workspace.ptr if workspace is not None else 0
        self.cusv.apply_matrix(
            self.handle,
            self.state.data.ptr,
            self.sv_type,
            self.n_qubits,
            matrix.ctypes.data,
            self.matrix_type,
            self.layout,
            0,
            targets,
            len(targets),
            controls_local,
            values_local,
            len(controls_local),
            self.compute_type,
            workspace_ptr,
            workspace_size,
        )

    def run_circuit(self, sample, feature_depth, entangle, phase, theta=None):
        one_qubit = 0
        two_qubit = 0
        self.state.fill(0.0)
        self.state[0] = 1.0

        for layer in range(feature_depth):
            for q, value in enumerate(sample):
                angle = float(value * math.pi / 3.0)
                self.apply_gate(ry(angle), [q])
                one_qubit += 1
                if phase:
                    self.apply_gate(rz(angle * (layer + 1)), [q])
                    one_qubit += 1
            if entangle:
                for q in range(self.n_qubits - 1):
                    self.apply_gate(self.x_gate, [q + 1], [q], [1])
                    two_qubit += 1

        if theta is not None:
            for layer in range(theta.shape[0]):
                for q in range(self.n_qubits):
                    self.apply_gate(ry(float(theta[layer, q])), [q])
                    one_qubit += 1
                if entangle:
                    for q in range(self.n_qubits - 1):
                        self.apply_gate(self.x_gate, [q + 1], [q], [1])
                        two_qubit += 1

        self.cp.cuda.Stream.null.synchronize()
        return self.cp.asnumpy(self.state), one_qubit, two_qubit


def simulate_states(x, feature_depth, entangle, phase, theta=None):
    start = time.perf_counter()
    n_samples, n_qubits = x.shape
    simulator = CuStateVecSimulator(n_qubits)
    states = np.empty((n_samples, simulator.state_dim), dtype=np.complex128)
    one_qubit = 0
    two_qubit = 0
    try:
        for i, sample in enumerate(x):
            state, g1, g2 = simulator.run_circuit(sample, feature_depth, entangle, phase, theta)
            states[i] = state
            one_qubit += g1
            two_qubit += g2
        simulator.cp.cuda.Stream.null.synchronize()
        return states, {
            "runtime_sec": time.perf_counter() - start,
            "samples": int(n_samples),
            "qubits": int(n_qubits),
            "state_dim": int(simulator.state_dim),
            "one_qubit_gates": int(one_qubit),
            "two_qubit_gates": int(two_qubit),
            "circuit_evaluations": int(n_samples),
            "device": int(simulator.cp.cuda.runtime.getDevice()),
            "cupy_used_bytes": int(simulator.cp.get_default_memory_pool().used_bytes()),
        }
    finally:
        simulator.close()


def z_expectations(states, n_qubits):
    probs = np.abs(states) ** 2
    z = np.empty((states.shape[0], n_qubits), dtype=np.float64)
    basis = np.arange(states.shape[1])
    for q in range(n_qubits):
        sign = np.where((basis & (1 << q)) != 0, -1.0, 1.0)
        z[:, q] = probs @ sign
    return z


def quantum_kernel_classifier(x_train, y_train, x_test, y_test, args):
    start_total = time.perf_counter()
    train_states, train_meta = simulate_states(
        x_train, args.feature_depth, args.entangle, args.phase, theta=None
    )
    test_states, test_meta = simulate_states(
        x_test, args.feature_depth, args.entangle, args.phase, theta=None
    )

    start_kernel = time.perf_counter()
    k_train = np.abs(train_states @ train_states.conj().T) ** 2
    k_test = np.abs(test_states @ train_states.conj().T) ** 2
    y_sign = 2.0 * y_train.astype(np.float64) - 1.0
    alpha = np.linalg.solve(
        k_train + args.kernel_ridge * np.eye(k_train.shape[0], dtype=np.float64),
        y_sign,
    )
    train_score_raw = k_train @ alpha
    test_score_raw = k_test @ alpha
    train_score = sigmoid(train_score_raw)
    test_score = sigmoid(test_score_raw)
    kernel_time = time.perf_counter() - start_kernel

    return {
        "status": "ok",
        "model": "quantum_kernel_ridge_custatevec",
        "total_runtime_sec": time.perf_counter() - start_total,
        "simulation_runtime_sec": train_meta["runtime_sec"] + test_meta["runtime_sec"],
        "kernel_solve_runtime_sec": kernel_time,
        "train_accuracy": accuracy_binary(train_score, y_train),
        "test_accuracy": accuracy_binary(test_score, y_test),
        "train_metadata": train_meta,
        "test_metadata": test_meta,
        "kernel_entries": int(k_train.size + k_test.size),
        "ridge": float(args.kernel_ridge),
    }


def train_head(z, y, steps, lr, w=None, b=0.0):
    if w is None:
        w = np.zeros(z.shape[1], dtype=np.float64)
    for _ in range(steps):
        score = sigmoid(z @ w + b)
        err = score - y
        w -= lr * (z.T @ err) / z.shape[0]
        b -= lr * float(np.mean(err))
    return w, b


def vqc_feature_batch(x, theta, args):
    states, metadata = simulate_states(
        x, args.feature_depth, args.entangle, args.phase, theta=theta
    )
    return z_expectations(states, x.shape[1]), metadata


def qnn_vqc_classifier(x_train, y_train, x_test, y_test, args):
    rng = np.random.default_rng(args.seed + 17)
    start_total = time.perf_counter()
    theta = rng.normal(scale=0.05, size=(args.vqc_layers, x_train.shape[1]))
    w = np.zeros(x_train.shape[1], dtype=np.float64)
    b = 0.0
    iteration_log = []
    total_meta = {
        "runtime_sec": 0.0,
        "one_qubit_gates": 0,
        "two_qubit_gates": 0,
        "circuit_evaluations": 0,
    }

    def add_meta(meta):
        total_meta["runtime_sec"] += meta["runtime_sec"]
        total_meta["one_qubit_gates"] += meta["one_qubit_gates"]
        total_meta["two_qubit_gates"] += meta["two_qubit_gates"]
        total_meta["circuit_evaluations"] += meta["circuit_evaluations"]

    for iteration in range(args.vqc_iterations):
        z_base, meta = vqc_feature_batch(x_train, theta, args)
        add_meta(meta)
        w, b = train_head(z_base, y_train, args.vqc_head_steps, args.vqc_head_lr, w, b)
        base_loss = bce_loss(sigmoid(z_base @ w + b), y_train)

        delta = rng.choice([-1.0, 1.0], size=theta.shape)
        z_plus, meta_plus = vqc_feature_batch(x_train, theta + args.spsa_epsilon * delta, args)
        z_minus, meta_minus = vqc_feature_batch(x_train, theta - args.spsa_epsilon * delta, args)
        add_meta(meta_plus)
        add_meta(meta_minus)
        loss_plus = bce_loss(sigmoid(z_plus @ w + b), y_train)
        loss_minus = bce_loss(sigmoid(z_minus @ w + b), y_train)
        grad_scale = (loss_plus - loss_minus) / (2.0 * args.spsa_epsilon)
        theta -= args.vqc_theta_lr * grad_scale * delta
        iteration_log.append(
            {
                "iteration": int(iteration),
                "base_loss": float(base_loss),
                "loss_plus": float(loss_plus),
                "loss_minus": float(loss_minus),
                "grad_scale": float(grad_scale),
            }
        )

    z_train, train_meta = vqc_feature_batch(x_train, theta, args)
    z_test, test_meta = vqc_feature_batch(x_test, theta, args)
    add_meta(train_meta)
    add_meta(test_meta)
    train_score = sigmoid(z_train @ w + b)
    test_score = sigmoid(z_test @ w + b)
    return {
        "status": "ok",
        "model": "qnn_vqc_spsa_custatevec",
        "total_runtime_sec": time.perf_counter() - start_total,
        "simulation_runtime_sec": total_meta["runtime_sec"],
        "train_accuracy": accuracy_binary(train_score, y_train),
        "test_accuracy": accuracy_binary(test_score, y_test),
        "train_loss": bce_loss(train_score, y_train),
        "test_loss": bce_loss(test_score, y_test),
        "iterations": int(args.vqc_iterations),
        "layers": int(args.vqc_layers),
        "head_steps_per_iteration": int(args.vqc_head_steps),
        "metadata": total_meta,
        "iteration_log": iteration_log,
    }


def build_projection(native_best_sec, path):
    if native_best_sec <= 0.0 or path.get("status") != "ok":
        return {}
    if "train_metadata" in path:
        g1 = path["train_metadata"]["one_qubit_gates"] + path["test_metadata"]["one_qubit_gates"]
        g2 = path["train_metadata"]["two_qubit_gates"] + path["test_metadata"]["two_qubit_gates"]
        evals = path["train_metadata"]["circuit_evaluations"] + path["test_metadata"]["circuit_evaluations"]
        qubits = path["train_metadata"]["qubits"]
    else:
        meta = path["metadata"]
        g1 = meta["one_qubit_gates"]
        g2 = meta["two_qubit_gates"]
        evals = meta["circuit_evaluations"]
        qubits = path.get("qubits", 0)
    measurement_ops = evals * qubits
    total_ops = max(1, g1 + g2 + measurement_ops)
    return {
        "sim_to_native_speedup_required": float(path["total_runtime_sec"] / native_best_sec),
        "required_uniform_op_time_sec_for_native_parity": float(native_best_sec / total_ops),
        "one_qubit_gates": int(g1),
        "two_qubit_gates": int(g2),
        "measurement_ops": int(measurement_ops),
        "circuit_evaluations": int(evals),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="data/datasets/sklearn_digits.npz")
    parser.add_argument("--classes", default="0,1")
    parser.add_argument("--max-samples", type=int, default=96)
    parser.add_argument("--train-frac", type=float, default=0.75)
    parser.add_argument("--pca-dim", type=int, default=4)
    parser.add_argument("--feature-depth", type=int, default=1)
    parser.add_argument("--phase", action="store_true")
    parser.add_argument("--entangle", action="store_true")
    parser.add_argument("--native-steps", type=int, default=400)
    parser.add_argument("--native-lr", type=float, default=0.35)
    parser.add_argument("--mlp-steps", type=int, default=400)
    parser.add_argument("--mlp-hidden", type=int, default=16)
    parser.add_argument("--mlp-lr", type=float, default=0.05)
    parser.add_argument("--kernel-ridge", type=float, default=1.0e-3)
    parser.add_argument("--vqc-layers", type=int, default=1)
    parser.add_argument("--vqc-iterations", type=int, default=3)
    parser.add_argument("--vqc-head-steps", type=int, default=15)
    parser.add_argument("--vqc-head-lr", type=float, default=0.25)
    parser.add_argument("--vqc-theta-lr", type=float, default=0.15)
    parser.add_argument("--spsa-epsilon", type=float, default=0.08)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--login-safe", action="store_true")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    if args.login_safe and (args.max_samples > 80 or args.pca_dim > 8 or args.vqc_iterations > 3):
        raise SystemExit("Refusing a large login-safe run.")

    classes = parse_classes(args.classes)
    start_total = time.perf_counter()
    x, y, raw_y, dataset_metadata = load_digits_npz(args.dataset, classes, args.max_samples, args.seed)
    x_train_raw, y_train, x_test_raw, y_test = stratified_split(
        x, y, args.train_frac, args.seed + 1
    )
    x_train, x_test, pca_meta = fit_pca_transform(x_train_raw, x_test_raw, args.pca_dim)

    native_start = time.perf_counter()
    logistic = train_logistic(
        x_train, y_train, x_test, y_test, args.native_steps, args.native_lr
    )
    mlp = train_mlp(
        x_train, y_train, x_test, y_test, args.mlp_steps, args.mlp_lr, args.mlp_hidden, args.seed
    )
    native_total = time.perf_counter() - native_start
    native = {
        "status": "ok",
        "total_runtime_sec": native_total,
        "logistic_regression": logistic,
        "mlp": mlp,
        "best_runtime_sec": min(logistic["runtime_sec"], mlp["runtime_sec"]),
        "best_test_accuracy": max(logistic["test_accuracy"], mlp["test_accuracy"]),
    }

    qkernel = quantum_kernel_classifier(x_train, y_train, x_test, y_test, args)
    qkernel["qubits"] = int(args.pca_dim)
    vqc = qnn_vqc_classifier(x_train, y_train, x_test, y_test, args)
    vqc["qubits"] = int(args.pca_dim)

    result = {
        "metadata": {
            "hostname": socket.gethostname(),
            "cwd": os.getcwd(),
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""),
            "slurm_job_name": os.environ.get("SLURM_JOB_NAME", ""),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
            "total_runtime_sec": time.perf_counter() - start_total,
        },
        "config": vars(args),
        "dataset": {
            "name": "sklearn_digits_npz",
            "source_metadata": dataset_metadata,
            "classes": classes,
            "samples": int(x.shape[0]),
            "class_counts": {
                str(cls): int(np.sum(raw_y == cls))
                for cls in classes
            },
            "train_samples": int(x_train.shape[0]),
            "test_samples": int(x_test.shape[0]),
            "raw_feature_dim": int(x.shape[1]),
            "pca": pca_meta,
        },
        "native_ml_path": native,
        "quantum_kernel_path": qkernel,
        "qnn_vqc_path": vqc,
        "break_even_projection": {
            "quantum_kernel": build_projection(native["best_runtime_sec"], qkernel),
            "qnn_vqc": build_projection(native["best_runtime_sec"], vqc),
        },
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
