#!/usr/bin/env python3
"""Matched CIFAR-10 cuStateVec quantum-feature quality proxy."""

import argparse
import json
import math
import os
import platform
import socket
import time
from pathlib import Path

import numpy as np
from PIL import Image


CLASS_NAMES = (
    "airplane",
    "automobile",
    "bird",
    "cat",
    "deer",
    "dog",
    "frog",
    "horse",
    "ship",
    "truck",
)


def ry(theta):
    cosine = math.cos(theta / 2.0)
    sine = math.sin(theta / 2.0)
    return np.ascontiguousarray(
        [[cosine, -sine], [sine, cosine]], dtype=np.complex128
    )


def rz(theta):
    return np.ascontiguousarray(
        [[np.exp(-0.5j * theta), 0.0], [0.0, np.exp(0.5j * theta)]],
        dtype=np.complex128,
    )


class CuStateVecFeatureCircuit:
    def __init__(self, qubits):
        import cupy as cp
        import cuquantum
        from cuquantum import ComputeType, cudaDataType
        from cuquantum.bindings import custatevec as cusv

        self.cp = cp
        self.cuquantum_version = cuquantum.__version__
        self.cusv = cusv
        self.qubits = int(qubits)
        self.dimension = 1 << self.qubits
        self.handle = cusv.create()
        self.state = cp.zeros(self.dimension, dtype=cp.complex128)
        self.sv_type = int(cudaDataType.CUDA_C_64F)
        self.matrix_type = int(cudaDataType.CUDA_C_64F)
        self.layout = int(cusv.MatrixLayout.ROW)
        self.compute_type = int(ComputeType.COMPUTE_64F)
        self.x_gate = np.ascontiguousarray(
            [[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128
        )
        basis = cp.arange(self.dimension, dtype=cp.uint64)
        z_signs = []
        x_indices = []
        for qubit in range(self.qubits):
            bits = (basis >> cp.uint64(qubit)) & cp.uint64(1)
            z_signs.append(1.0 - 2.0 * bits.astype(cp.float64))
            x_indices.append(basis ^ cp.uint64(1 << qubit))
        self.z_signs = cp.stack(z_signs)
        self.x_indices = cp.stack(x_indices)
        self.zz_signs = cp.stack(
            [
                self.z_signs[qubit] * self.z_signs[(qubit + 1) % self.qubits]
                for qubit in range(self.qubits)
            ]
        )

    def close(self):
        self.cusv.destroy(self.handle)

    def load_state(self, amplitudes):
        self.state.set(np.asarray(amplitudes, dtype=np.complex128))

    def apply_gate(self, matrix, targets, controls=None, control_values=None):
        controls = [] if controls is None else controls
        control_values = [] if control_values is None else control_values
        workspace_size = self.cusv.apply_matrix_get_workspace_size(
            self.handle,
            self.sv_type,
            self.qubits,
            matrix.ctypes.data,
            self.matrix_type,
            self.layout,
            0,
            len(targets),
            len(controls),
            self.compute_type,
        )
        workspace = self.cp.cuda.alloc(workspace_size) if workspace_size else None
        self.cusv.apply_matrix(
            self.handle,
            self.state.data.ptr,
            self.sv_type,
            self.qubits,
            matrix.ctypes.data,
            self.matrix_type,
            self.layout,
            0,
            targets,
            len(targets),
            controls,
            control_values,
            len(controls),
            self.compute_type,
            workspace.ptr if workspace is not None else 0,
            workspace_size,
        )

    def apply_layer(self, ry_angles, rz_angles):
        for qubit in range(self.qubits):
            self.apply_gate(ry(float(ry_angles[qubit])), [qubit])
            self.apply_gate(rz(float(rz_angles[qubit])), [qubit])
        for qubit in range(self.qubits - 1):
            self.apply_gate(self.x_gate, [qubit + 1], [qubit], [1])
        self.apply_gate(self.x_gate, [0], [self.qubits - 1], [1])

    def observable_features(self):
        probabilities = self.cp.abs(self.state) ** 2
        z_values = self.z_signs @ probabilities
        zz_values = self.zz_signs @ probabilities
        x_values = self.cp.sum(
            self.cp.conj(self.state)[None, :] * self.state[self.x_indices], axis=1
        ).real
        return self.cp.asnumpy(self.cp.concatenate([z_values, x_values, zz_values]))


def load_split(root, split, limit):
    images = []
    labels = []
    per_class_limit = None if limit <= 0 else max(1, limit // len(CLASS_NAMES))
    for label, class_name in enumerate(CLASS_NAMES):
        paths = sorted((root / split / class_name).glob("*.png"))
        if per_class_limit is not None:
            paths = paths[:per_class_limit]
        for path in paths:
            with Image.open(path) as image:
                images.append(np.asarray(image.convert("RGB"), dtype=np.float64).reshape(-1))
            labels.append(label)
    x = np.asarray(images, dtype=np.float64) / 255.0
    y = np.asarray(labels, dtype=np.int64)
    return x, y


def amplitude_state(sample, pixel_mean, dimension):
    centered = sample - pixel_mean
    padded = np.zeros(dimension, dtype=np.float64)
    padded[: centered.size] = centered
    norm = np.linalg.norm(padded)
    if norm < 1e-12:
        padded[0] = 1.0
        return padded
    return padded / norm


def extract_features(images, pixel_mean, dimension, layers, seed):
    qubits = int(round(math.log(dimension, 2)))
    rng = np.random.default_rng(seed)
    ry_angles = rng.uniform(-math.pi, math.pi, size=(layers, qubits))
    rz_angles = rng.uniform(-math.pi, math.pi, size=(layers, qubits))
    simulator = CuStateVecFeatureCircuit(qubits)
    features = np.empty((images.shape[0], layers * 3 * qubits), dtype=np.float64)
    started = time.perf_counter()
    try:
        for index, image in enumerate(images):
            simulator.load_state(amplitude_state(image, pixel_mean, dimension))
            for layer in range(layers):
                simulator.apply_layer(ry_angles[layer], rz_angles[layer])
                begin = layer * 3 * qubits
                features[index, begin : begin + 3 * qubits] = (
                    simulator.observable_features()
                )
        simulator.cp.cuda.Stream.null.synchronize()
        metadata = {
            "runtime_sec": time.perf_counter() - started,
            "samples": int(images.shape[0]),
            "qubits": qubits,
            "layers": int(layers),
            "features": int(features.shape[1]),
            "executed_one_qubit_gates": int(images.shape[0] * layers * 2 * qubits),
            "executed_two_qubit_gates": int(images.shape[0] * layers * qubits),
            "circuit_evaluations": int(images.shape[0]),
            "cuquantum_version": simulator.cuquantum_version,
            "cupy_version": simulator.cp.__version__,
            "device": int(simulator.cp.cuda.runtime.getDevice()),
        }
    finally:
        simulator.close()
    return features, metadata


def checkpoint_features(path, expected_samples, compute):
    if path is not None and path.exists():
        with np.load(path, allow_pickle=False) as checkpoint:
            features = checkpoint["features"]
            metadata = json.loads(str(checkpoint["metadata_json"]))
        if features.shape[0] != expected_samples:
            raise RuntimeError("feature checkpoint sample count mismatch: {}".format(path))
        metadata["loaded_from_checkpoint"] = True
        return features, metadata
    features, metadata = compute()
    metadata["loaded_from_checkpoint"] = False
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp.npz")
        np.savez(
            temporary,
            features=features,
            metadata_json=np.asarray(json.dumps(metadata)),
        )
        temporary.replace(path)
    return features, metadata


def ridge_classifier(train_x, train_y, test_x, test_y, regularization):
    mean = train_x.mean(axis=0)
    scale = train_x.std(axis=0) + 1e-8
    train = (train_x - mean) / scale
    test = (test_x - mean) / scale
    train = np.column_stack([train, np.ones(train.shape[0])])
    test = np.column_stack([test, np.ones(test.shape[0])])
    targets = np.eye(len(CLASS_NAMES), dtype=np.float64)[train_y]
    started = time.perf_counter()
    gram = train.T @ train
    gram.flat[:: gram.shape[0] + 1] += regularization
    weights = np.linalg.solve(gram, train.T @ targets)
    runtime = time.perf_counter() - started
    train_prediction = np.argmax(train @ weights, axis=1)
    test_prediction = np.argmax(test @ weights, axis=1)
    return {
        "model": "standardized_ridge_head",
        "regularization": float(regularization),
        "runtime_sec": runtime,
        "train_accuracy": float(np.mean(train_prediction == train_y)),
        "test_accuracy": float(np.mean(test_prediction == test_y)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="/pscratch/sd/s/sgkim/qsup_datasets/cifar10")
    parser.add_argument("--train-limit", type=int, default=0)
    parser.add_argument("--test-limit", type=int, default=0)
    parser.add_argument("--layers", type=int, default=3)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--ridge", type=float, default=1e-2)
    parser.add_argument("--checkpoint-prefix")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    total_start = time.perf_counter()
    root = Path(args.dataset_root)
    train_x, train_y = load_split(root, "train", args.train_limit)
    test_x, test_y = load_split(root, "test", args.test_limit)
    pixel_mean = train_x.mean(axis=0)
    checkpoint_prefix = Path(args.checkpoint_prefix) if args.checkpoint_prefix else None
    train_checkpoint = (
        checkpoint_prefix.with_name(checkpoint_prefix.name + "_train.npz")
        if checkpoint_prefix is not None
        else None
    )
    test_checkpoint = (
        checkpoint_prefix.with_name(checkpoint_prefix.name + "_test.npz")
        if checkpoint_prefix is not None
        else None
    )
    train_features, train_metadata = checkpoint_features(
        train_checkpoint,
        train_x.shape[0],
        lambda: extract_features(train_x, pixel_mean, 4096, args.layers, args.seed),
    )
    test_features, test_metadata = checkpoint_features(
        test_checkpoint,
        test_x.shape[0],
        lambda: extract_features(test_x, pixel_mean, 4096, args.layers, args.seed),
    )
    classifier = ridge_classifier(
        train_features, train_y, test_features, test_y, args.ridge
    )
    output = {
        "schema": "qsup.ml-cifar10-cuquantum-feature-proxy.v1",
        "scope": (
            "same CIFAR-10 split quantum-feature quality gate; direct amplitude "
            "state upload is executed, while generic gate-based state preparation "
            "remains a separate upper contract; this is not end-to-end QNN training"
        ),
        "environment": {
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        },
        "dataset": {
            "root": str(root),
            "train_samples": int(train_x.shape[0]),
            "test_samples": int(test_x.shape[0]),
            "raw_features": int(train_x.shape[1]),
            "classes": list(CLASS_NAMES),
        },
        "encoding": {
            "method": "mean-centered amplitude encoding by direct state upload",
            "qubits": 12,
            "state_dimension": 4096,
            "generic_exact_state_preparation_rotation_upper_per_image": 4095,
            "generic_exact_state_preparation_executed": False,
        },
        "train_circuit": train_metadata,
        "test_circuit": test_metadata,
        "classifier": classifier,
        "resnet18_reference": {
            "artifact": "data/processed/perlmutter/ml_cifar10_resnet18_proxy.json",
            "best_test_accuracy": 0.8185,
        },
        "quality_gap_to_resnet18": float(0.8185 - classifier["test_accuracy"]),
        "total_runtime_sec": time.perf_counter() - total_start,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
