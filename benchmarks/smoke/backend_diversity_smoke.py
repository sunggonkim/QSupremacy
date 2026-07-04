#!/usr/bin/env python3
"""Backend-diversity smoke test for Perlmutter quantum simulation paths."""

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import time


def timed(fn):
    start = time.perf_counter()
    try:
        payload = fn()
        payload.setdefault("status", "ok")
    except Exception as exc:
        payload = {
            "status": "error",
            "error": "{}: {}".format(type(exc).__name__, str(exc)),
        }
    payload["runtime_sec"] = time.perf_counter() - start
    return payload


def counts_from_cirq_result(result, key):
    counts = {}
    for row in result.measurements[key]:
        bitstring = "".join(str(int(bit)) for bit in row)
        counts[bitstring] = counts.get(bitstring, 0) + 1
    return counts


def run_cuquantum_import(python):
    code = r"""
import json
import cupy
import cuquantum
from cuquantum.bindings import custatevec, cutensornet
print(json.dumps({
    "python_executable": __import__("sys").executable,
    "cupy_version": getattr(cupy, "__version__", "unknown"),
    "cuquantum_version": getattr(cuquantum, "__version__", "unknown"),
    "custatevec_module": str(custatevec),
    "cutensornet_module": str(cutensornet),
    "device_count": int(cupy.cuda.runtime.getDeviceCount()),
    "device": int(cupy.cuda.runtime.getDevice()),
}))
"""
    completed = subprocess.run(
        [python, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "cuQuantum subprocess failed rc={} stdout={} stderr={}".format(
                completed.returncode,
                completed.stdout.strip(),
                completed.stderr.strip(),
            )
        )
    payload = json.loads(completed.stdout)
    if completed.stderr.strip():
        payload["stderr"] = completed.stderr.strip()
    return payload


def run_qsim(qsim_path, use_gpu):
    if qsim_path and qsim_path not in sys.path:
        sys.path.insert(0, qsim_path)

    import cirq
    import qsimcirq

    qubits = cirq.LineQubit.range(4)
    circuit = cirq.Circuit(
        cirq.H.on_each(*qubits),
        cirq.CZ(qubits[0], qubits[1]),
        cirq.CZ(qubits[2], qubits[3]),
        cirq.measure(*qubits, key="m"),
    )
    options = qsimcirq.QSimOptions(
        use_gpu=use_gpu,
        cpu_threads=4,
        max_fused_gate_size=2,
    )
    result = qsimcirq.QSimSimulator(qsim_options=options).run(circuit, repetitions=16)
    return {
        "cirq_version": getattr(cirq, "__version__", "unknown"),
        "qsimcirq_version": getattr(qsimcirq, "__version__", "unknown"),
        "qsimcirq_file": getattr(qsimcirq, "__file__", ""),
        "use_gpu": bool(use_gpu),
        "counts": counts_from_cirq_result(result, "m"),
    }


def run_cudaq():
    import cudaq

    kernel = cudaq.make_kernel()
    qubits = kernel.qalloc(2)
    kernel.h(qubits[0])
    kernel.cx(qubits[0], qubits[1])
    kernel.mz(qubits)
    result = cudaq.sample(kernel, shots_count=16)
    return {
        "cudaq_version": getattr(cudaq, "__version__", "unknown"),
        "target": str(cudaq.get_target()),
        "counts": str(result),
    }


def run_aer(device):
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator

    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    simulator = AerSimulator(device=device)
    result = simulator.run(circuit, shots=16).result()
    return {
        "device": device,
        "available_devices": tuple(AerSimulator().available_devices()),
        "counts": result.get_counts(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--qsim-path",
        default="/pscratch/sd/s/sgkim/ehan/quantum/qsim-main",
    )
    parser.add_argument(
        "--cuquantum-python",
        default="/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python",
    )
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    result = {
        "metadata": {
            "hostname": socket.gethostname(),
            "cwd": os.getcwd(),
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "qsim_path": args.qsim_path,
            "cuquantum_python": args.cuquantum_python,
        },
        "cuquantum_direct": timed(lambda: run_cuquantum_import(args.cuquantum_python)),
        "qsim_cpu": timed(lambda: run_qsim(args.qsim_path, use_gpu=False)),
        "qsim_gpu": timed(lambda: run_qsim(args.qsim_path, use_gpu=True)),
        "cudaq_custatevec": timed(run_cudaq),
        "qiskit_aer_cpu": timed(lambda: run_aer("CPU")),
        "qiskit_aer_gpu": timed(lambda: run_aer("GPU")),
    }

    required = ["cuquantum_direct", "qsim_cpu", "qsim_gpu", "cudaq_custatevec"]
    result["pass"] = all(result[name].get("status") == "ok" for name in required)
    result["required_backends"] = required
    result["optional_backends"] = ["qiskit_aer_cpu", "qiskit_aer_gpu"]

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(text)
            f.write("\n")

    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
