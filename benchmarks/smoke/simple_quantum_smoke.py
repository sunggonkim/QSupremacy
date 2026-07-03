#!/usr/bin/env python3
"""Tiny login-node-safe quantum simulation smoke test.

This script intentionally keeps the circuit tiny. It is meant to answer:

1. Does a basic Python/NumPy state-vector baseline run?
2. Is cuQuantum importable in the current environment?

It does not claim a meaningful performance comparison on login nodes.
Use Slurm jobs for real GPU benchmarks.
"""

import argparse
import importlib
import json
import math
import os
import platform
import socket
import sys
import time

import numpy as np


def apply_one_qubit_gate(state, gate, target, n_qubits):
    stride = 1 << target
    block = stride << 1
    for base in range(0, state.size, block):
        for offset in range(stride):
            i0 = base + offset
            i1 = i0 + stride
            a0 = state[i0]
            a1 = state[i1]
            state[i0] = gate[0, 0] * a0 + gate[0, 1] * a1
            state[i1] = gate[1, 0] * a0 + gate[1, 1] * a1


def apply_cnot(state, control, target, n_qubits):
    control_mask = 1 << control
    target_mask = 1 << target
    for i in range(state.size):
        if (i & control_mask) and not (i & target_mask):
            j = i | target_mask
            state[i], state[j] = state[j], state[i]


def run_numpy_statevector(n_qubits, depth):
    state = np.zeros(1 << n_qubits, dtype=np.complex128)
    state[0] = 1.0

    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    h_gate = np.array(
        [[inv_sqrt2, inv_sqrt2], [inv_sqrt2, -inv_sqrt2]], dtype=np.complex128
    )
    phase_gate = np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=np.complex128)

    start = time.perf_counter()
    gate_count = 0
    for layer in range(depth):
        for q in range(n_qubits):
            gate = h_gate if (layer + q) % 2 == 0 else phase_gate
            apply_one_qubit_gate(state, gate, q, n_qubits)
            gate_count += 1
        for q in range(n_qubits - 1):
            if (layer + q) % 2 == 0:
                apply_cnot(state, q, q + 1, n_qubits)
                gate_count += 1
    elapsed = time.perf_counter() - start

    norm = float(np.vdot(state, state).real)
    checksum = {
        "real_sum": float(np.real(state).sum()),
        "imag_sum": float(np.imag(state).sum()),
        "norm": norm,
    }
    return {
        "status": "ok",
        "runtime_sec": elapsed,
        "state_dim": int(state.size),
        "gate_count": gate_count,
        "checksum": checksum,
    }


def check_optional_module(name):
    start = time.perf_counter()
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {
            "status": "missing",
            "runtime_sec": time.perf_counter() - start,
            "error": "{}: {}".format(type(exc).__name__, str(exc)),
        }
    version = getattr(module, "__version__", "unknown")
    return {
        "status": "import_ok",
        "runtime_sec": time.perf_counter() - start,
        "version": version,
    }


def run_custatevec_statevector(n_qubits, depth):
    start_total = time.perf_counter()
    try:
        import cupy as cp
        from cuquantum import ComputeType, cudaDataType
        from cuquantum.bindings import custatevec as cusv
    except Exception as exc:
        return {
            "status": "missing",
            "runtime_sec": time.perf_counter() - start_total,
            "error": "{}: {}".format(type(exc).__name__, str(exc)),
        }

    handle = None
    try:
        state = cp.zeros(1 << n_qubits, dtype=cp.complex128)
        state[0] = 1.0

        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        h_gate = np.ascontiguousarray(
            [[inv_sqrt2, inv_sqrt2], [inv_sqrt2, -inv_sqrt2]], dtype=np.complex128
        )
        phase_gate = np.ascontiguousarray(
            [[1.0, 0.0], [0.0, 1.0j]], dtype=np.complex128
        )
        x_gate = np.ascontiguousarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)

        sv_type = int(cudaDataType.CUDA_C_64F)
        matrix_type = int(cudaDataType.CUDA_C_64F)
        layout = int(cusv.MatrixLayout.ROW)
        compute_type = int(ComputeType.COMPUTE_64F)
        handle = cusv.create()

        def apply_gate(matrix, targets, controls=None, control_values=None):
            controls = [] if controls is None else controls
            control_values = [] if control_values is None else control_values
            workspace_size = cusv.apply_matrix_get_workspace_size(
                handle,
                sv_type,
                n_qubits,
                matrix.ctypes.data,
                matrix_type,
                layout,
                0,
                len(targets),
                len(controls),
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
                controls,
                control_values,
                len(controls),
                compute_type,
                workspace_ptr,
                workspace_size,
            )

        cp.cuda.Stream.null.synchronize()
        start = time.perf_counter()
        gate_count = 0
        for layer in range(depth):
            for q in range(n_qubits):
                gate = h_gate if (layer + q) % 2 == 0 else phase_gate
                apply_gate(gate, [q])
                gate_count += 1
            for q in range(n_qubits - 1):
                if (layer + q) % 2 == 0:
                    apply_gate(x_gate, [q + 1], [q], [1])
                    gate_count += 1
        cp.cuda.Stream.null.synchronize()
        elapsed = time.perf_counter() - start

        norm = float(cp.vdot(state, state).real.get())
        checksum = {
            "real_sum": float(cp.real(state).sum().get()),
            "imag_sum": float(cp.imag(state).sum().get()),
            "norm": norm,
        }
        mempool = cp.get_default_memory_pool()
        return {
            "status": "ok",
            "runtime_sec": elapsed,
            "total_runtime_sec": time.perf_counter() - start_total,
            "state_dim": int(state.size),
            "gate_count": gate_count,
            "checksum": checksum,
            "cupy_used_bytes": int(mempool.used_bytes()),
            "device": cp.cuda.runtime.getDevice(),
        }
    except Exception as exc:
        return {
            "status": "error",
            "runtime_sec": time.perf_counter() - start_total,
            "error": "{}: {}".format(type(exc).__name__, str(exc)),
        }
    finally:
        if handle is not None:
            try:
                cusv.destroy(handle)
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qubits", type=int, default=10)
    parser.add_argument("--depth", type=int, default=4)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    if args.qubits > 16:
        raise SystemExit("Refusing to run >16 qubits in smoke mode on a login node.")

    result = {
        "metadata": {
            "hostname": socket.gethostname(),
            "cwd": os.getcwd(),
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
        },
        "config": {
            "qubits": args.qubits,
            "depth": args.depth,
        },
        "numpy_statevector": run_numpy_statevector(args.qubits, args.depth),
        "cupy_import": check_optional_module("cupy"),
        "cuquantum_import": check_optional_module("cuquantum"),
        "cuquantum_custatevec_import": check_optional_module("cuquantum.custatevec"),
        "cuquantum_bindings_custatevec_import": check_optional_module(
            "cuquantum.bindings.custatevec"
        ),
        "cuquantum_bindings_cutensornet_import": check_optional_module(
            "cuquantum.bindings.cutensornet"
        ),
        "custatevec_statevector": run_custatevec_statevector(args.qubits, args.depth),
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
