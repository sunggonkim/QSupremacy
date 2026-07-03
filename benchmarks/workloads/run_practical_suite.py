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
        "runtime_sec": time.perf_counter() - start,
        "train_accuracy": multiclass_accuracy(train_probs, y_train),
        "test_accuracy": multiclass_accuracy(test_probs, y_test),
        "parameters": int(w.size),
    }


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
    x, y = make_multiclass_data(args.ml_samples, args.ml_features, args.ml_classes, args.seed)
    x_train, y_train, x_test, y_test = split(x, y, args.train_frac)
    native = train_softmax(
        x_train, y_train, x_test, y_test, args.ml_classes, args.ml_steps, args.ml_lr
    )
    q_start = time.perf_counter()
    q_train, train_meta = quantum_ml_features(x_train, args.ml_depth, args.entangle)
    q_test, test_meta = quantum_ml_features(x_test, args.ml_depth, args.entangle)
    head = train_softmax(
        q_train, y_train, q_test, y_test, args.ml_classes, args.ml_steps, args.ml_lr
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
        "dataset": {
            "samples": int(x.shape[0]),
            "features": int(x.shape[1]),
            "classes": int(args.ml_classes),
        },
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


def run_chemistry(args):
    h, coeffs = h2_hamiltonian()
    start = time.perf_counter()
    evals = np.linalg.eigvalsh(h)
    native = {
        "runtime_sec": time.perf_counter() - start,
        "ground_energy": float(np.min(evals).real),
        "method": "exact_diagonalization_numpy",
    }

    start = time.perf_counter()
    sim = CuStateVecSimulator(2)
    best = {"energy": float("inf"), "theta0": None, "theta1": None}
    try:
        for theta0 in np.linspace(-math.pi, math.pi, args.chem_grid):
            for theta1 in np.linspace(-math.pi, math.pi, args.chem_grid):
                sim.reset()
                sim.apply_gate(ry(float(theta0)), [0])
                sim.apply_gate(ry(float(theta1)), [1])
                sim.apply_cnot(0, 1)
                state = sim.state_host()
                energy = float(np.real(np.vdot(state, h @ state)))
                if energy < best["energy"]:
                    best = {
                        "energy": energy,
                        "theta0": float(theta0),
                        "theta1": float(theta1),
                    }
        meta = sim.metadata(evaluations=args.chem_grid * args.chem_grid)
        quantum = {
            "status": "ok",
            "runtime_sec": time.perf_counter() - start,
            "estimated_ground_energy": best["energy"],
            "best_theta0": best["theta0"],
            "best_theta1": best["theta1"],
            "absolute_energy_error": float(abs(best["energy"] - native["ground_energy"])),
            "metadata": meta,
            "ansatz": "Ry(theta0)-Ry(theta1)-CNOT",
        }
    finally:
        sim.close()

    return {
        "family": "chemistry_vqe",
        "quality_metric": "absolute_energy_error",
        "native_path": native,
        "quantum_path": quantum,
        "problem": {"molecule": "H2_minimal_2qubit", "hamiltonian_coefficients": coeffs},
    }


def maxcut_value(bits, edges):
    value = 0
    for u, v in edges:
        value += int(bits[u] != bits[v])
    return value


def run_optimization(args):
    n = args.opt_nodes
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
    if n == 5:
        edges.append((3, 4))
        edges.append((1, 4))
    start = time.perf_counter()
    best_value = -1
    best_bits = None
    for mask in range(1 << n):
        bits = [(mask >> q) & 1 for q in range(n)]
        value = maxcut_value(bits, edges)
        if value > best_value:
            best_value = value
            best_bits = bits
    native = {
        "runtime_sec": time.perf_counter() - start,
        "best_cut": int(best_value),
        "best_bits": best_bits,
        "method": "exact_enumeration_numpy",
    }

    start = time.perf_counter()
    sim = CuStateVecSimulator(n)
    best = {"expected_cut": -1.0, "beta": None, "gamma": None}
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
        meta = sim.metadata(evaluations=args.opt_grid * args.opt_grid)
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
        "problem": {"name": "small_maxcut", "nodes": int(n), "edges": edges},
    }


def tfim_hamiltonian(n_qubits, coupling, field):
    h = np.zeros((1 << n_qubits, 1 << n_qubits), dtype=np.complex128)
    for q in range(n_qubits - 1):
        h += coupling * pauli_string(n_qubits, [(q, Z), (q + 1, Z)])
    for q in range(n_qubits):
        h += field * pauli_string(n_qubits, [(q, X)])
    return h


def run_simulation(args):
    n = args.sim_qubits
    h = tfim_hamiltonian(n, args.sim_coupling, args.sim_field)
    init = np.zeros(1 << n, dtype=np.complex128)
    init[0] = 1.0
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
        for _ in range(args.sim_steps):
            for q in range(n - 1):
                sim.apply_zz_rotation(q, q + 1, float(2.0 * args.sim_coupling * dt))
            for q in range(n):
                sim.apply_gate(rx(float(2.0 * args.sim_field * dt)), [q])
        state = sim.state_host()
        q_obs = float(z_expectations_from_state(state, n)[0])
        meta = sim.metadata(evaluations=1)
        quantum = {
            "status": "ok",
            "runtime_sec": time.perf_counter() - start,
            "z0_expectation": q_obs,
            "absolute_observable_error": float(abs(q_obs - native_obs)),
            "metadata": meta,
            "ansatz": "first_order_trotter_tfim",
        }
    finally:
        sim.close()

    return {
        "family": "hamiltonian_simulation",
        "quality_metric": "absolute_observable_error",
        "native_path": native,
        "quantum_path": quantum,
        "problem": {
            "name": "transverse_field_ising",
            "qubits": int(n),
            "steps": int(args.sim_steps),
            "time": float(args.sim_time),
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

    parser.add_argument("--ml-samples", type=int, default=72)
    parser.add_argument("--ml-features", type=int, default=4)
    parser.add_argument("--ml-classes", type=int, default=3)
    parser.add_argument("--ml-depth", type=int, default=1)
    parser.add_argument("--ml-steps", type=int, default=250)
    parser.add_argument("--ml-lr", type=float, default=0.25)

    parser.add_argument("--chem-grid", type=int, default=21)
    parser.add_argument("--opt-nodes", type=int, default=4)
    parser.add_argument("--opt-grid", type=int, default=7)
    parser.add_argument("--sim-qubits", type=int, default=4)
    parser.add_argument("--sim-steps", type=int, default=4)
    parser.add_argument("--sim-time", type=float, default=0.8)
    parser.add_argument("--sim-coupling", type=float, default=0.7)
    parser.add_argument("--sim-field", type=float, default=0.4)
    args = parser.parse_args()

    if args.login_safe:
        if args.ml_samples > 128 or args.ml_features > 8:
            raise SystemExit("Refusing large ML login-safe run.")
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
