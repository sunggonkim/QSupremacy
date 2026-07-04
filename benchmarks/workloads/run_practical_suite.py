#!/usr/bin/env python3
"""Practical native-vs-quantum workload suite.

This runner is intentionally small enough for login-node smoke validation, but
each workload mirrors a practical application family:

* multiclass ML: native softmax model vs quantum feature circuit + softmax head
* chemistry: exact molecular Hamiltonian diagonalization vs VQE-style circuit
* optimization: exact/greedy MaxCut vs QAOA-style circuit
* simulation: exact Hamiltonian dynamics vs Trotterized quantum circuit

The output is a JSON file with the same modeling idea used by the digits
benchmark: compare application paths, keep quality metrics, and report the
speedup a projected quantum path would need for native parity.
"""

import argparse
import itertools
import json
import math
import os
import platform
import socket
import sys
import time

import numpy as np


I2 = np.eye(2, dtype=np.complex128)
X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
H_GATE = (1.0 / math.sqrt(2.0)) * np.array(
    [[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128
)


def rx(theta):
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return np.ascontiguousarray([[c, -1.0j * s], [-1.0j * s, c]], dtype=np.complex128)


def ry(theta):
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return np.ascontiguousarray([[c, -s], [s, c]], dtype=np.complex128)


def rz(theta):
    return np.ascontiguousarray(
        [[np.exp(-0.5j * theta), 0.0], [0.0, np.exp(0.5j * theta)]],
        dtype=np.complex128,
    )


def kron_all(mats):
    out = mats[0]
    for mat in mats[1:]:
        out = np.kron(out, mat)
    return out


def pauli_string(n_qubits, terms):
    mats = []
    term_map = dict(terms)
    for q in range(n_qubits):
        mats.append(term_map.get(q, I2))
    return kron_all(mats)


def pauli_word_matrix(word):
    ops = {"I": I2, "X": X, "Y": Y, "Z": Z}
    return kron_all([ops[ch] for ch in word])


def softmax(logits):
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def multiclass_accuracy(probs, y):
    return float(np.mean(np.argmax(probs, axis=1) == y))


def train_softmax(x_train, y_train, x_test, y_test, classes, steps, lr):
    start = time.perf_counter()
    x_train_b = np.concatenate([x_train, np.ones((x_train.shape[0], 1))], axis=1)
    x_test_b = np.concatenate([x_test, np.ones((x_test.shape[0], 1))], axis=1)
    w = np.zeros((x_train_b.shape[1], classes), dtype=np.float64)
    y_onehot = np.eye(classes, dtype=np.float64)[y_train]
    for _ in range(steps):
        probs = softmax(x_train_b @ w)
        grad = x_train_b.T @ (probs - y_onehot) / x_train_b.shape[0]
        w -= lr * grad
    train_probs = softmax(x_train_b @ w)
    test_probs = softmax(x_test_b @ w)
    return {
        "model": "softmax_regression_numpy",
        "runtime_sec": time.perf_counter() - start,
        "train_accuracy": multiclass_accuracy(train_probs, y_train),
        "test_accuracy": multiclass_accuracy(test_probs, y_test),
        "parameters": int(w.size),
    }


def train_mlp_classifier(x_train, y_train, x_test, y_test, classes, steps, lr, hidden, seed):
    rng = np.random.default_rng(seed)
    start = time.perf_counter()
    d = x_train.shape[1]
    w1 = rng.normal(scale=1.0 / math.sqrt(max(1, d)), size=(d, hidden))
    b1 = np.zeros(hidden, dtype=np.float64)
    w2 = rng.normal(scale=1.0 / math.sqrt(max(1, hidden)), size=(hidden, classes))
    b2 = np.zeros(classes, dtype=np.float64)
    y_onehot = np.eye(classes, dtype=np.float64)[y_train]

    for _ in range(steps):
        h = np.tanh(x_train @ w1 + b1)
        probs = softmax(h @ w2 + b2)
        dz = (probs - y_onehot) / x_train.shape[0]
        grad_w2 = h.T @ dz
        grad_b2 = dz.sum(axis=0)
        dh = (dz @ w2.T) * (1.0 - h * h)
        grad_w1 = x_train.T @ dh
        grad_b1 = dh.sum(axis=0)
        w2 -= lr * grad_w2
        b2 -= lr * grad_b2
        w1 -= lr * grad_w1
        b1 -= lr * grad_b1

    train_probs = softmax(np.tanh(x_train @ w1 + b1) @ w2 + b2)
    test_probs = softmax(np.tanh(x_test @ w1 + b1) @ w2 + b2)
    return {
        "model": "one_hidden_layer_mlp_numpy",
        "runtime_sec": time.perf_counter() - start,
        "train_accuracy": multiclass_accuracy(train_probs, y_train),
        "test_accuracy": multiclass_accuracy(test_probs, y_test),
        "hidden": int(hidden),
        "parameters": int(w1.size + b1.size + w2.size + b2.size),
    }


def train_linear_ridge_classifier(x_train, y_train, x_test, y_test, classes, alpha):
    start = time.perf_counter()
    x_train_b = np.concatenate([x_train, np.ones((x_train.shape[0], 1))], axis=1)
    x_test_b = np.concatenate([x_test, np.ones((x_test.shape[0], 1))], axis=1)
    y_onehot = np.eye(classes, dtype=np.float64)[y_train]
    gram = x_train_b.T @ x_train_b
    reg = float(alpha) * np.eye(gram.shape[0], dtype=np.float64)
    reg[-1, -1] = 0.0
    w = np.linalg.solve(gram + reg, x_train_b.T @ y_onehot)
    train_scores = x_train_b @ w
    test_scores = x_test_b @ w
    return {
        "model": "linear_ridge_numpy",
        "runtime_sec": time.perf_counter() - start,
        "train_accuracy": multiclass_accuracy(train_scores, y_train),
        "test_accuracy": multiclass_accuracy(test_scores, y_test),
        "alpha": float(alpha),
        "parameters": int(w.size),
    }


def squared_distances(a, b):
    a2 = np.sum(a * a, axis=1, keepdims=True)
    b2 = np.sum(b * b, axis=1, keepdims=True).T
    return np.maximum(a2 + b2 - 2.0 * (a @ b.T), 0.0)


def train_rbf_kernel_ridge_classifier(
    x_train, y_train, x_test, y_test, classes, alpha, gamma
):
    start = time.perf_counter()
    d2_train = squared_distances(x_train, x_train)
    if gamma <= 0.0:
        positive = d2_train[d2_train > 1.0e-12]
        scale = float(np.median(positive)) if positive.size else 1.0
        gamma_used = 1.0 / max(scale, 1.0e-12)
    else:
        gamma_used = float(gamma)
    k_train = np.exp(-gamma_used * d2_train)
    y_onehot = np.eye(classes, dtype=np.float64)[y_train]
    coeff = np.linalg.solve(
        k_train + float(alpha) * np.eye(k_train.shape[0], dtype=np.float64),
        y_onehot,
    )
    train_scores = k_train @ coeff
    k_test = np.exp(-gamma_used * squared_distances(x_test, x_train))
    test_scores = k_test @ coeff
    return {
        "model": "rbf_kernel_ridge_numpy",
        "runtime_sec": time.perf_counter() - start,
        "train_accuracy": multiclass_accuracy(train_scores, y_train),
        "test_accuracy": multiclass_accuracy(test_scores, y_test),
        "alpha": float(alpha),
        "gamma": float(gamma_used),
        "parameters": int(coeff.size),
    }


def train_knn_classifier(x_train, y_train, x_test, y_test, classes, k):
    start = time.perf_counter()
    k = max(1, min(int(k), x_train.shape[0]))

    def predict(x_query):
        d2 = squared_distances(x_query, x_train)
        neighbors = np.argpartition(d2, kth=k - 1, axis=1)[:, :k]
        preds = np.empty(x_query.shape[0], dtype=np.int64)
        for i, row in enumerate(neighbors):
            votes = np.bincount(y_train[row], minlength=classes)
            preds[i] = int(np.argmax(votes))
        return preds

    train_pred = predict(x_train)
    test_pred = predict(x_test)
    return {
        "model": "knn_numpy",
        "runtime_sec": time.perf_counter() - start,
        "train_accuracy": float(np.mean(train_pred == y_train)),
        "test_accuracy": float(np.mean(test_pred == y_test)),
        "k": int(k),
        "parameters": int(x_train.size),
    }


def train_nearest_centroid_classifier(x_train, y_train, x_test, y_test, classes):
    start = time.perf_counter()
    centroids = np.zeros((classes, x_train.shape[1]), dtype=np.float64)
    for cls in range(classes):
        members = x_train[y_train == cls]
        if members.size:
            centroids[cls] = members.mean(axis=0)

    def predict(x_query):
        d2 = squared_distances(x_query, centroids)
        return np.argmin(d2, axis=1)

    train_pred = predict(x_train)
    test_pred = predict(x_test)
    return {
        "model": "nearest_centroid_numpy",
        "runtime_sec": time.perf_counter() - start,
        "train_accuracy": float(np.mean(train_pred == y_train)),
        "test_accuracy": float(np.mean(test_pred == y_test)),
        "parameters": int(centroids.size),
    }


def requested_baselines(text):
    return [item.strip().lower() for item in text.split(",") if item.strip()]


def select_native_classifier(models, quality_tolerance):
    if not models:
        raise ValueError("No native ML baselines were evaluated.")
    best_quality_model = max(
        models, key=lambda model: (model["test_accuracy"], -model["runtime_sec"])
    )
    best_accuracy = float(best_quality_model["test_accuracy"])
    valid = [
        model
        for model in models
        if float(model["test_accuracy"]) >= best_accuracy - float(quality_tolerance)
    ]
    selected = min(valid, key=lambda model: model["runtime_sec"])
    fastest = min(models, key=lambda model: model["runtime_sec"])
    return selected, best_quality_model, fastest, best_accuracy


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
        self.one_qubit_gates = 0
        self.two_qubit_gates = 0

    def close(self):
        self.cusv.destroy(self.handle)

    def reset(self):
        self.state.fill(0.0)
        self.state[0] = 1.0
        self.one_qubit_gates = 0
        self.two_qubit_gates = 0

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
        if len(targets) == 1 and len(controls_local) == 0:
            self.one_qubit_gates += 1
        else:
            self.two_qubit_gates += 1

    def apply_cnot(self, control, target):
        self.apply_gate(X, [target], [control], [1])

    def apply_zz_rotation(self, q0, q1, theta):
        self.apply_cnot(q0, q1)
        self.apply_gate(rz(theta), [q1])
        self.apply_cnot(q0, q1)

    def apply_xx_rotation(self, q0, q1, theta):
        self.apply_gate(H_GATE, [q0])
        self.apply_gate(H_GATE, [q1])
        self.apply_zz_rotation(q0, q1, theta)
        self.apply_gate(H_GATE, [q0])
        self.apply_gate(H_GATE, [q1])

    def apply_yy_rotation(self, q0, q1, theta):
        self.apply_gate(rx(math.pi / 2.0), [q0])
        self.apply_gate(rx(math.pi / 2.0), [q1])
        self.apply_zz_rotation(q0, q1, theta)
        self.apply_gate(rx(-math.pi / 2.0), [q0])
        self.apply_gate(rx(-math.pi / 2.0), [q1])

    def state_host(self):
        self.cp.cuda.Stream.null.synchronize()
        return self.cp.asnumpy(self.state)

    def metadata(self, evaluations=1):
        return {
            "qubits": int(self.n_qubits),
            "state_dim": int(self.state_dim),
            "one_qubit_gates": int(self.one_qubit_gates),
            "two_qubit_gates": int(self.two_qubit_gates),
            "circuit_evaluations": int(evaluations),
            "device": int(self.cp.cuda.runtime.getDevice()),
            "cupy_used_bytes": int(self.cp.get_default_memory_pool().used_bytes()),
        }


def z_expectations_from_state(state, n_qubits):
    probs = np.abs(state) ** 2
    basis = np.arange(state.size)
    out = np.empty(n_qubits, dtype=np.float64)
    for q in range(n_qubits):
        sign = np.where((basis & (1 << q)) != 0, -1.0, 1.0)
        out[q] = float(probs @ sign)
    return out


def make_multiclass_data(samples, features, classes, seed):
    rng = np.random.default_rng(seed)
    centers = rng.normal(scale=1.4, size=(classes, features))
    labels = np.arange(samples, dtype=np.int64) % classes
    rng.shuffle(labels)
    x = centers[labels] + 0.65 * rng.normal(size=(samples, features))
    x[:, 0] += 0.35 * np.sin(x[:, 1])
    x = (x - x.mean(axis=0)) / (x.std(axis=0) + 1.0e-12)
    return np.clip(x, -3.0, 3.0), labels


def parse_int_list(text):
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def fit_pca_transform(x, features):
    mean = x.mean(axis=0)
    centered = x - mean
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    reduced = centered @ vt[:features].T
    scale = reduced.std(axis=0) + 1.0e-12
    reduced = np.clip(reduced / scale, -3.0, 3.0)
    return reduced.astype(np.float64), {
        "raw_feature_dim": int(x.shape[1]),
        "pca_dim": int(features),
    }


def load_digits_multiclass(path, samples, features, classes_text, seed):
    classes = parse_int_list(classes_text)
    if len(classes) < 2:
        raise ValueError("Digits ML needs at least two classes.")
    with np.load(path, allow_pickle=False) as data:
        x_all = data["data"].astype(np.float64) / 16.0
        y_all = data["target"].astype(np.int64)

    rng = np.random.default_rng(seed)
    selected = []
    per_class = samples // len(classes)
    remainder = samples % len(classes)
    for idx, cls in enumerate(classes):
        cls_indices = np.flatnonzero(y_all == cls)
        rng.shuffle(cls_indices)
        take = per_class + (1 if idx < remainder else 0)
        selected.append(cls_indices[:take])
    indices = np.concatenate(selected)
    rng.shuffle(indices)

    raw_x = x_all[indices]
    raw_y = y_all[indices]
    label_map = {cls: i for i, cls in enumerate(classes)}
    y = np.array([label_map[int(value)] for value in raw_y], dtype=np.int64)
    x, pca = fit_pca_transform(raw_x, features)
    metadata = {
        "name": "sklearn_digits",
        "path": path,
        "classes": classes,
        "samples": int(x.shape[0]),
        "class_counts": {str(cls): int(np.sum(raw_y == cls)) for cls in classes},
        "pca": pca,
    }
    return x, y, metadata


def make_ml_dataset(args):
    if args.ml_dataset == "synthetic":
        x, y = make_multiclass_data(
            args.ml_samples, args.ml_features, args.ml_classes, args.seed
        )
        metadata = {
            "name": "synthetic_multiclass",
            "samples": int(x.shape[0]),
            "features": int(x.shape[1]),
            "classes": int(args.ml_classes),
        }
        return x, y, int(args.ml_classes), metadata
    if args.ml_dataset == "digits":
        x, y, metadata = load_digits_multiclass(
            args.digits_path,
            args.ml_samples,
            args.ml_features,
            args.digits_classes,
            args.seed,
        )
        return x, y, len(metadata["classes"]), metadata
    raise ValueError("Unknown ML dataset: {}".format(args.ml_dataset))


def split(x, y, train_frac):
    n_train = int(round(x.shape[0] * train_frac))
    return x[:n_train], y[:n_train], x[n_train:], y[n_train:]


def quantum_ml_features(x, depth, entangle):
    start = time.perf_counter()
    sim = CuStateVecSimulator(x.shape[1])
    features = np.empty((x.shape[0], x.shape[1] * 2), dtype=np.float64)
    g1 = 0
    g2 = 0
    try:
        for i, sample in enumerate(x):
            sim.reset()
            for layer in range(depth):
                for q, value in enumerate(sample):
                    angle = float(value * math.pi / 3.0)
                    sim.apply_gate(ry(angle), [q])
                    sim.apply_gate(rz(angle * (layer + 1)), [q])
                if entangle:
                    for q in range(x.shape[1] - 1):
                        sim.apply_cnot(q, q + 1)
            state = sim.state_host()
            features[i, : x.shape[1]] = z_expectations_from_state(state, x.shape[1])
            features[i, x.shape[1] :] = np.real(state[: x.shape[1]])
            g1 += sim.one_qubit_gates
            g2 += sim.two_qubit_gates
        return features, {
            "runtime_sec": time.perf_counter() - start,
            "qubits": int(x.shape[1]),
            "state_dim": int(1 << x.shape[1]),
            "one_qubit_gates": int(g1),
            "two_qubit_gates": int(g2),
            "circuit_evaluations": int(x.shape[0]),
        }
    finally:
        sim.close()


def run_multiclass_ml(args):
    x, y, classes, dataset_metadata = make_ml_dataset(args)
    x_train, y_train, x_test, y_test = split(x, y, args.train_frac)
    native_start = time.perf_counter()
    native_models = []
    for baseline in requested_baselines(args.ml_native_baselines):
        if baseline == "softmax":
            native_models.append(
                train_softmax(
                    x_train, y_train, x_test, y_test, classes, args.ml_steps, args.ml_lr
                )
            )
        elif baseline == "mlp":
            native_models.append(
                train_mlp_classifier(
                    x_train,
                    y_train,
                    x_test,
                    y_test,
                    classes,
                    args.mlp_steps,
                    args.mlp_lr,
                    args.mlp_hidden,
                    args.seed + 101,
                )
            )
        elif baseline == "linear_ridge":
            native_models.append(
                train_linear_ridge_classifier(
                    x_train, y_train, x_test, y_test, classes, args.ridge_alpha
                )
            )
        elif baseline == "rbf_kernel_ridge":
            native_models.append(
                train_rbf_kernel_ridge_classifier(
                    x_train,
                    y_train,
                    x_test,
                    y_test,
                    classes,
                    args.ridge_alpha,
                    args.rbf_gamma,
                )
            )
        elif baseline == "knn":
            native_models.append(
                train_knn_classifier(
                    x_train, y_train, x_test, y_test, classes, args.knn_k
                )
            )
        elif baseline == "nearest_centroid":
            native_models.append(
                train_nearest_centroid_classifier(
                    x_train, y_train, x_test, y_test, classes
                )
            )
        else:
            raise ValueError("Unknown ML native baseline: {}".format(baseline))

    selected_model, best_quality_model, fastest_model, best_accuracy = select_native_classifier(
        native_models, args.ml_native_quality_tolerance
    )
    native = {
        "runtime_sec": float(selected_model["runtime_sec"]),
        "total_runtime_sec": time.perf_counter() - native_start,
        "train_accuracy": best_quality_model["train_accuracy"],
        "test_accuracy": best_accuracy,
        "selected_model": selected_model["model"],
        "selected_model_test_accuracy": selected_model["test_accuracy"],
        "selected_model_runtime_sec": selected_model["runtime_sec"],
        "best_quality_model": best_quality_model["model"],
        "fastest_model": fastest_model["model"],
        "fastest_runtime_sec": fastest_model["runtime_sec"],
        "best_runtime_sec": selected_model["runtime_sec"],
        "best_test_accuracy": best_accuracy,
        "quality_tolerance": float(args.ml_native_quality_tolerance),
        "selection_rule": "fastest_model_within_tolerance_of_best_test_accuracy",
        "models": {model["model"]: model for model in native_models},
    }
    q_start = time.perf_counter()
    q_train, train_meta = quantum_ml_features(x_train, args.ml_depth, args.entangle)
    q_test, test_meta = quantum_ml_features(x_test, args.ml_depth, args.entangle)
    head = train_softmax(
        q_train, y_train, q_test, y_test, classes, args.ml_steps, args.ml_lr
    )
    quantum = {
        "status": "ok",
        "runtime_sec": time.perf_counter() - q_start,
        "feature_runtime_sec": train_meta["runtime_sec"] + test_meta["runtime_sec"],
        "head_runtime_sec": head["runtime_sec"],
        "train_accuracy": head["train_accuracy"],
        "test_accuracy": head["test_accuracy"],
        "train_metadata": train_meta,
        "test_metadata": test_meta,
    }
    return {
        "family": "multiclass_ml",
        "quality_metric": "test_accuracy",
        "native_path": native,
        "quantum_path": quantum,
        "dataset": dataset_metadata,
    }


def h2_hamiltonian():
    coeffs = {
        "ii": -1.052373245772859,
        "zi": 0.39793742484318045,
        "iz": -0.39793742484318045,
        "zz": -0.01128010425623538,
        "xx": 0.18093119978423156,
    }
    h = coeffs["ii"] * np.eye(4, dtype=np.complex128)
    h += coeffs["zi"] * pauli_string(2, [(0, Z)])
    h += coeffs["iz"] * pauli_string(2, [(1, Z)])
    h += coeffs["zz"] * pauli_string(2, [(0, Z), (1, Z)])
    h += coeffs["xx"] * pauli_string(2, [(0, X), (1, X)])
    return h, coeffs


def load_pauli_hamiltonian_json(path):
    with open(path) as f:
        data = json.load(f)
    n_qubits = int(data["n_qubits"])
    h = np.zeros((1 << n_qubits, 1 << n_qubits), dtype=np.complex128)
    terms = []
    for term in data["terms"]:
        word = term["pauli"].upper()
        if len(word) != n_qubits:
            raise ValueError("Pauli word {} does not match {} qubits".format(word, n_qubits))
        coeff = float(term["coefficient"])
        h += coeff * pauli_word_matrix(word)
        terms.append({"pauli": word, "coefficient": coeff})
    metadata = {
        "name": data.get("name", os.path.basename(path)),
        "source": path,
        "n_qubits": n_qubits,
        "description": data.get("description", ""),
        "terms": terms,
    }
    return h, metadata


def chemistry_hamiltonian(args):
    if args.chem_hamiltonian_json:
        return load_pauli_hamiltonian_json(args.chem_hamiltonian_json)
    h, coeffs = h2_hamiltonian()
    terms = [
        {"pauli": "II", "coefficient": coeffs["ii"]},
        {"pauli": "ZI", "coefficient": coeffs["zi"]},
        {"pauli": "IZ", "coefficient": coeffs["iz"]},
        {"pauli": "ZZ", "coefficient": coeffs["zz"]},
        {"pauli": "XX", "coefficient": coeffs["xx"]},
    ]
    return h, {
        "name": "H2_minimal_2qubit",
        "n_qubits": 2,
        "description": "Built-in 2-qubit H2 minimal-basis Hamiltonian.",
        "terms": terms,
    }


def run_vqe_ansatz(sim, theta, layers, entangle):
    idx = 0
    for layer in range(layers):
        for q in range(sim.n_qubits):
            sim.apply_gate(ry(float(theta[idx])), [q])
            idx += 1
        if entangle:
            for q in range(sim.n_qubits - 1):
                sim.apply_cnot(q, q + 1)
        for q in range(sim.n_qubits):
            sim.apply_gate(rz(float(theta[idx])), [q])
            idx += 1


def vqe_parameter_candidates(n_qubits, layers, grid, seed):
    rng = np.random.default_rng(seed)
    param_count = max(1, layers * n_qubits * 2)
    candidates = [
        np.zeros(param_count, dtype=np.float64),
        np.full(param_count, math.pi / 2.0, dtype=np.float64),
        np.full(param_count, -math.pi / 2.0, dtype=np.float64),
    ]
    for value in np.linspace(-math.pi, math.pi, grid):
        candidates.append(np.full(param_count, float(value), dtype=np.float64))
    if n_qubits == 2 and layers == 1:
        for theta0, theta1 in itertools.product(
            np.linspace(-math.pi, math.pi, grid),
            np.linspace(-math.pi, math.pi, grid),
        ):
            theta = np.zeros(param_count, dtype=np.float64)
            theta[0] = float(theta0)
            theta[1] = float(theta1)
            candidates.append(theta)
    for _ in range(max(0, grid)):
        candidates.append(rng.uniform(-math.pi, math.pi, size=param_count))
    return candidates


def run_chemistry(args):
    h, problem = chemistry_hamiltonian(args)
    n_qubits = int(problem["n_qubits"])
    start = time.perf_counter()
    evals = np.linalg.eigvalsh(h)
    native = {
        "runtime_sec": time.perf_counter() - start,
        "ground_energy": float(np.min(evals).real),
        "method": "exact_diagonalization_numpy",
    }

    start = time.perf_counter()
    sim = CuStateVecSimulator(n_qubits)
    best = {"energy": float("inf"), "theta": None}
    total_g1 = 0
    total_g2 = 0
    candidates = vqe_parameter_candidates(n_qubits, args.chem_layers, args.chem_grid, args.seed)
    try:
        for theta in candidates:
            sim.reset()
            run_vqe_ansatz(sim, theta, args.chem_layers, args.entangle)
            state = sim.state_host()
            energy = float(np.real(np.vdot(state, h @ state)))
            if energy < best["energy"]:
                best = {"energy": energy, "theta": [float(x) for x in theta]}
            total_g1 += sim.one_qubit_gates
            total_g2 += sim.two_qubit_gates
        meta = sim.metadata(evaluations=len(candidates))
        meta["one_qubit_gates"] = int(total_g1)
        meta["two_qubit_gates"] = int(total_g2)
        quantum = {
            "status": "ok",
            "runtime_sec": time.perf_counter() - start,
            "estimated_ground_energy": best["energy"],
            "best_theta": best["theta"],
            "absolute_energy_error": float(abs(best["energy"] - native["ground_energy"])),
            "metadata": meta,
            "ansatz": "hardware_efficient_ry_rz_linear_entangler",
            "layers": int(args.chem_layers),
        }
    finally:
        sim.close()

    return {
        "family": "chemistry_vqe",
        "quality_metric": "absolute_energy_error",
        "native_path": native,
        "quantum_path": quantum,
        "problem": problem,
    }


def maxcut_value(bits, edges):
    value = 0
    for u, v in edges:
        value += int(bits[u] != bits[v])
    return value


def build_maxcut_edges(n, graph):
    if graph == "ring":
        return [(q, (q + 1) % n) for q in range(n)]
    if graph == "ladder":
        if n < 4:
            return [(q, (q + 1) % n) for q in range(n)]
        split_point = n // 2
        top = list(range(split_point))
        bottom = list(range(split_point, n))
        edges = []
        for row in (top, bottom):
            for idx in range(len(row) - 1):
                edges.append((row[idx], row[idx + 1]))
        for idx in range(min(len(top), len(bottom))):
            edges.append((top[idx], bottom[idx]))
        return edges
    if graph == "chordal":
        edges = [(q, (q + 1) % n) for q in range(n)]
        edges.append((0, n // 2))
        if n > 4:
            edges.append((1, n - 1))
        return sorted(set(tuple(sorted(edge)) for edge in edges))
    raise ValueError("Unknown graph family: {}".format(graph))


def exact_maxcut_baseline(n, edges):
    start = time.perf_counter()
    best_value = -1
    best_bits = None
    for mask in range(1 << n):
        bits = [(mask >> q) & 1 for q in range(n)]
        value = maxcut_value(bits, edges)
        if value > best_value:
            best_value = value
            best_bits = bits
    return {
        "method": "exact_enumeration_numpy",
        "runtime_sec": time.perf_counter() - start,
        "best_cut": int(best_value),
        "best_bits": best_bits,
    }


def greedy_maxcut_baseline(n, edges):
    start = time.perf_counter()
    bits = [0 for _ in range(n)]
    assigned = [False for _ in range(n)]
    for node in range(n):
        best_bit = 0
        best_value = -1
        for bit in (0, 1):
            bits[node] = bit
            assigned[node] = True
            partial_edges = [
                (u, v) for u, v in edges if assigned[u] and assigned[v]
            ]
            value = maxcut_value(bits, partial_edges)
            if value > best_value:
                best_value = value
                best_bit = bit
        bits[node] = best_bit
        assigned[node] = True
    return {
        "method": "greedy_assignment_numpy",
        "runtime_sec": time.perf_counter() - start,
        "best_cut": int(maxcut_value(bits, edges)),
        "best_bits": bits,
    }


def improve_maxcut_by_flips(bits, edges):
    current = maxcut_value(bits, edges)
    improved = True
    while improved:
        improved = False
        for node in range(len(bits)):
            candidate = list(bits)
            candidate[node] = 1 - candidate[node]
            value = maxcut_value(candidate, edges)
            if value > current:
                bits = candidate
                current = value
                improved = True
    return bits, current


def local_search_maxcut_baseline(n, edges, restarts, seed):
    rng = np.random.default_rng(seed)
    start = time.perf_counter()
    starts = []
    starts.append(greedy_maxcut_baseline(n, edges)["best_bits"])
    starts.append([0 for _ in range(n)])
    for _ in range(max(0, int(restarts))):
        starts.append([int(x) for x in rng.integers(0, 2, size=n)])
    best_value = -1
    best_bits = None
    for bits in starts:
        improved_bits, value = improve_maxcut_by_flips(list(bits), edges)
        if value > best_value:
            best_value = value
            best_bits = improved_bits
    return {
        "method": "local_search_numpy",
        "runtime_sec": time.perf_counter() - start,
        "best_cut": int(best_value),
        "best_bits": best_bits,
        "restarts": int(restarts),
    }


def annealing_maxcut_baseline(n, edges, steps, seed):
    rng = np.random.default_rng(seed)
    start = time.perf_counter()
    bits = [int(x) for x in rng.integers(0, 2, size=n)]
    current = maxcut_value(bits, edges)
    best_bits = list(bits)
    best_value = current
    steps = max(1, int(steps))
    for step in range(steps):
        temp = max(0.02, 1.0 - step / steps)
        node = int(rng.integers(0, n))
        candidate = list(bits)
        candidate[node] = 1 - candidate[node]
        value = maxcut_value(candidate, edges)
        delta = value - current
        if delta >= 0 or rng.random() < math.exp(delta / temp):
            bits = candidate
            current = value
            if value > best_value:
                best_value = value
                best_bits = list(candidate)
    return {
        "method": "simulated_annealing_numpy",
        "runtime_sec": time.perf_counter() - start,
        "best_cut": int(best_value),
        "best_bits": best_bits,
        "steps": int(steps),
    }


def select_maxcut_native_baseline(models):
    best_cut = max(int(model["best_cut"]) for model in models)
    valid = [model for model in models if int(model["best_cut"]) == best_cut]
    selected = min(valid, key=lambda model: model["runtime_sec"])
    return selected, best_cut


def run_optimization(args):
    n = args.opt_nodes
    edges = build_maxcut_edges(n, args.opt_graph)
    native_start = time.perf_counter()
    native_models = []
    for baseline in requested_baselines(args.opt_native_baselines):
        if baseline == "exact":
            if n <= args.opt_exact_max_nodes:
                native_models.append(exact_maxcut_baseline(n, edges))
        elif baseline == "greedy":
            native_models.append(greedy_maxcut_baseline(n, edges))
        elif baseline == "local_search":
            native_models.append(
                local_search_maxcut_baseline(
                    n, edges, args.opt_local_restarts, args.seed + 202
                )
            )
        elif baseline == "annealing":
            native_models.append(
                annealing_maxcut_baseline(
                    n, edges, args.opt_anneal_steps, args.seed + 303
                )
            )
        else:
            raise ValueError("Unknown optimization native baseline: {}".format(baseline))
    selected_native, best_value = select_maxcut_native_baseline(native_models)
    native = {
        "runtime_sec": float(selected_native["runtime_sec"]),
        "total_runtime_sec": time.perf_counter() - native_start,
        "best_cut": int(best_value),
        "best_bits": selected_native["best_bits"],
        "method": selected_native["method"],
        "selected_model": selected_native["method"],
        "selection_rule": "fastest_model_matching_best_cut",
        "models": {model["method"]: model for model in native_models},
    }

    start = time.perf_counter()
    sim = CuStateVecSimulator(n)
    best = {"expected_cut": -1.0, "beta": None, "gamma": None}
    total_g1 = 0
    total_g2 = 0
    try:
        for beta in np.linspace(0.0, math.pi / 2.0, args.opt_grid):
            for gamma in np.linspace(0.0, math.pi, args.opt_grid):
                sim.reset()
                for q in range(n):
                    sim.apply_gate(H_GATE, [q])
                for u, v in edges:
                    sim.apply_zz_rotation(u, v, float(-gamma))
                for q in range(n):
                    sim.apply_gate(rx(float(2.0 * beta)), [q])
                state = sim.state_host()
                probs = np.abs(state) ** 2
                expected_cut = 0.0
                for mask, prob in enumerate(probs):
                    bits = [(mask >> q) & 1 for q in range(n)]
                    expected_cut += float(prob) * maxcut_value(bits, edges)
                if expected_cut > best["expected_cut"]:
                    best = {
                        "expected_cut": float(expected_cut),
                        "beta": float(beta),
                        "gamma": float(gamma),
                    }
                total_g1 += sim.one_qubit_gates
                total_g2 += sim.two_qubit_gates
        meta = sim.metadata(evaluations=args.opt_grid * args.opt_grid)
        meta["one_qubit_gates"] = int(total_g1)
        meta["two_qubit_gates"] = int(total_g2)
        quantum = {
            "status": "ok",
            "runtime_sec": time.perf_counter() - start,
            "expected_cut": best["expected_cut"],
            "approximation_ratio": float(best["expected_cut"] / max(1, best_value)),
            "best_beta": best["beta"],
            "best_gamma": best["gamma"],
            "metadata": meta,
            "ansatz": "QAOA_p1_grid",
        }
    finally:
        sim.close()

    return {
        "family": "optimization_qaoa",
        "quality_metric": "approximation_ratio",
        "native_path": native,
        "quantum_path": quantum,
        "problem": {
            "name": "small_maxcut",
            "graph_family": args.opt_graph,
            "nodes": int(n),
            "edges": edges,
        },
    }


def tfim_hamiltonian(n_qubits, coupling, field):
    h = np.zeros((1 << n_qubits, 1 << n_qubits), dtype=np.complex128)
    for q in range(n_qubits - 1):
        h += coupling * pauli_string(n_qubits, [(q, Z), (q + 1, Z)])
    for q in range(n_qubits):
        h += field * pauli_string(n_qubits, [(q, X)])
    return h


def heisenberg_hamiltonian(n_qubits, coupling, field):
    h = np.zeros((1 << n_qubits, 1 << n_qubits), dtype=np.complex128)
    for q in range(n_qubits - 1):
        h += coupling * pauli_string(n_qubits, [(q, X), (q + 1, X)])
        h += coupling * pauli_string(n_qubits, [(q, Y), (q + 1, Y)])
        h += coupling * pauli_string(n_qubits, [(q, Z), (q + 1, Z)])
    for q in range(n_qubits):
        h += field * pauli_string(n_qubits, [(q, Z)])
    return h


def simulation_hamiltonian(args):
    if args.sim_model == "tfim":
        return tfim_hamiltonian(args.sim_qubits, args.sim_coupling, args.sim_field)
    if args.sim_model == "heisenberg":
        return heisenberg_hamiltonian(args.sim_qubits, args.sim_coupling, args.sim_field)
    raise ValueError("Unknown simulation model: {}".format(args.sim_model))


def apply_simulation_trotter_step(sim, args, dt):
    if args.sim_model == "tfim":
        for q in range(args.sim_qubits - 1):
            sim.apply_zz_rotation(q, q + 1, float(2.0 * args.sim_coupling * dt))
        for q in range(args.sim_qubits):
            sim.apply_gate(rx(float(2.0 * args.sim_field * dt)), [q])
        return
    if args.sim_model == "heisenberg":
        for q in range(args.sim_qubits - 1):
            angle = float(2.0 * args.sim_coupling * dt)
            sim.apply_xx_rotation(q, q + 1, angle)
            sim.apply_yy_rotation(q, q + 1, angle)
            sim.apply_zz_rotation(q, q + 1, angle)
        for q in range(args.sim_qubits):
            sim.apply_gate(rz(float(2.0 * args.sim_field * dt)), [q])
        return
    raise ValueError("Unknown simulation model: {}".format(args.sim_model))


def simulation_initial_mask(args):
    if args.sim_initial_state == "zero":
        return 0
    if args.sim_initial_state == "neel":
        mask = 0
        for q in range(args.sim_qubits):
            if q % 2 == 1:
                mask |= 1 << q
        return mask
    if args.sim_initial_state == "auto":
        if args.sim_model == "heisenberg":
            mask = 0
            for q in range(args.sim_qubits):
                if q % 2 == 1:
                    mask |= 1 << q
            return mask
        return 0
    raise ValueError("Unknown simulation initial state: {}".format(args.sim_initial_state))


def prepare_simulation_initial_state(sim, mask):
    for q in range(sim.n_qubits):
        if mask & (1 << q):
            sim.apply_gate(X, [q])


def run_simulation(args):
    n = args.sim_qubits
    h = simulation_hamiltonian(args)
    init = np.zeros(1 << n, dtype=np.complex128)
    init_mask = simulation_initial_mask(args)
    init[init_mask] = 1.0
    start = time.perf_counter()
    evals, evecs = np.linalg.eigh(h)
    evolved = evecs @ (np.exp(-1.0j * evals * args.sim_time) * (evecs.conj().T @ init))
    z0 = pauli_string(n, [(0, Z)])
    native_obs = float(np.real(np.vdot(evolved, z0 @ evolved)))
    native = {
        "runtime_sec": time.perf_counter() - start,
        "z0_expectation": native_obs,
        "method": "exact_dense_eigendecomposition_numpy",
    }

    start = time.perf_counter()
    dt = args.sim_time / args.sim_steps
    sim = CuStateVecSimulator(n)
    try:
        sim.reset()
        prepare_simulation_initial_state(sim, init_mask)
        for _ in range(args.sim_steps):
            apply_simulation_trotter_step(sim, args, dt)
        state = sim.state_host()
        q_obs = float(z_expectations_from_state(state, n)[0])
        meta = sim.metadata(evaluations=1)
        quantum = {
            "status": "ok",
            "runtime_sec": time.perf_counter() - start,
            "z0_expectation": q_obs,
            "absolute_observable_error": float(abs(q_obs - native_obs)),
            "metadata": meta,
            "ansatz": "first_order_trotter_{}".format(args.sim_model),
        }
    finally:
        sim.close()

    return {
        "family": "hamiltonian_simulation",
        "quality_metric": "absolute_observable_error",
        "native_path": native,
        "quantum_path": quantum,
        "problem": {
            "name": args.sim_model,
            "qubits": int(n),
            "steps": int(args.sim_steps),
            "time": float(args.sim_time),
            "coupling": float(args.sim_coupling),
            "field": float(args.sim_field),
            "initial_state": args.sim_initial_state,
            "initial_basis_index": int(init_mask),
        },
    }


def projection_for_workload(workload):
    native_sec = workload["native_path"].get("runtime_sec", 0.0)
    quantum = workload["quantum_path"]
    if native_sec <= 0.0 or quantum.get("status") != "ok":
        return {}
    meta = quantum.get("metadata")
    if meta is None:
        train = quantum.get("train_metadata", {})
        test = quantum.get("test_metadata", {})
        meta = {
            "one_qubit_gates": train.get("one_qubit_gates", 0) + test.get("one_qubit_gates", 0),
            "two_qubit_gates": train.get("two_qubit_gates", 0) + test.get("two_qubit_gates", 0),
            "circuit_evaluations": train.get("circuit_evaluations", 0)
            + test.get("circuit_evaluations", 0),
            "qubits": train.get("qubits", 0) or test.get("qubits", 0),
        }
    measurement_ops = int(meta.get("circuit_evaluations", 1) * max(1, meta.get("qubits", 1)))
    total_ops = max(1, int(meta.get("one_qubit_gates", 0)) + int(meta.get("two_qubit_gates", 0)) + measurement_ops)
    q_sec = quantum.get("runtime_sec", quantum.get("total_runtime_sec", 0.0))
    return {
        "sim_to_native_speedup_required": float(q_sec / native_sec),
        "required_uniform_op_time_sec_for_native_parity": float(native_sec / total_ops),
        "one_qubit_gates": int(meta.get("one_qubit_gates", 0)),
        "two_qubit_gates": int(meta.get("two_qubit_gates", 0)),
        "measurement_ops": int(measurement_ops),
        "circuit_evaluations": int(meta.get("circuit_evaluations", 0)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workloads", default="ml,chemistry,optimization,simulation")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--train-frac", type=float, default=0.75)
    parser.add_argument("--entangle", action="store_true")
    parser.add_argument("--login-safe", action="store_true")
    parser.add_argument("--output", default="")

    parser.add_argument("--ml-dataset", choices=["synthetic", "digits"], default="synthetic")
    parser.add_argument("--digits-path", default="data/datasets/sklearn_digits.npz")
    parser.add_argument("--digits-classes", default="0,1,2")
    parser.add_argument("--ml-samples", type=int, default=72)
    parser.add_argument("--ml-features", type=int, default=4)
    parser.add_argument("--ml-classes", type=int, default=3)
    parser.add_argument("--ml-depth", type=int, default=1)
    parser.add_argument("--ml-steps", type=int, default=250)
    parser.add_argument("--ml-lr", type=float, default=0.25)
    parser.add_argument("--mlp-steps", type=int, default=250)
    parser.add_argument("--mlp-hidden", type=int, default=16)
    parser.add_argument("--mlp-lr", type=float, default=0.05)
    parser.add_argument(
        "--ml-native-baselines",
        default="softmax,mlp,linear_ridge,rbf_kernel_ridge,knn,nearest_centroid",
    )
    parser.add_argument("--ml-native-quality-tolerance", type=float, default=0.01)
    parser.add_argument("--ridge-alpha", type=float, default=1.0e-2)
    parser.add_argument("--rbf-gamma", type=float, default=0.0)
    parser.add_argument("--knn-k", type=int, default=5)

    parser.add_argument("--chem-grid", type=int, default=21)
    parser.add_argument("--chem-layers", type=int, default=1)
    parser.add_argument("--chem-hamiltonian-json", default="")
    parser.add_argument("--opt-nodes", type=int, default=4)
    parser.add_argument("--opt-graph", choices=["chordal", "ring", "ladder"], default="chordal")
    parser.add_argument("--opt-grid", type=int, default=7)
    parser.add_argument(
        "--opt-native-baselines",
        default="exact,greedy,local_search,annealing",
    )
    parser.add_argument("--opt-exact-max-nodes", type=int, default=22)
    parser.add_argument("--opt-local-restarts", type=int, default=8)
    parser.add_argument("--opt-anneal-steps", type=int, default=250)
    parser.add_argument("--sim-model", choices=["tfim", "heisenberg"], default="tfim")
    parser.add_argument("--sim-initial-state", choices=["auto", "zero", "neel"], default="auto")
    parser.add_argument("--sim-qubits", type=int, default=4)
    parser.add_argument("--sim-steps", type=int, default=4)
    parser.add_argument("--sim-time", type=float, default=0.8)
    parser.add_argument("--sim-coupling", type=float, default=0.7)
    parser.add_argument("--sim-field", type=float, default=0.4)
    args = parser.parse_args()

    if args.login_safe:
        if args.ml_samples > 128 or args.ml_features > 8:
            raise SystemExit("Refusing large ML login-safe run.")
        if args.ml_dataset == "digits" and len(parse_int_list(args.digits_classes)) > 4:
            raise SystemExit("Refusing too many digits classes in login-safe run.")
        if args.opt_nodes > 5 or args.sim_qubits > 6:
            raise SystemExit("Refusing large optimization/simulation login-safe run.")
        if args.chem_grid > 41 or args.opt_grid > 11:
            raise SystemExit("Refusing large grid login-safe run.")

    start_total = time.perf_counter()
    requested = [x.strip() for x in args.workloads.split(",") if x.strip()]
    runners = {
        "ml": run_multiclass_ml,
        "chemistry": run_chemistry,
        "optimization": run_optimization,
        "simulation": run_simulation,
    }
    workloads = {}
    for name in requested:
        if name not in runners:
            raise SystemExit("Unknown workload: {}".format(name))
        workload = runners[name](args)
        workload["break_even_projection"] = projection_for_workload(workload)
        workloads[name] = workload

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
        "workloads": workloads,
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
