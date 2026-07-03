#!/bin/bash
set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/login_suite
mkdir -p "${OUTDIR}"

echo "[1/6] Environment"
hostname
nvidia-smi -L
"${PY}" - <<'PY'
import cupy, cuquantum
from cuquantum.bindings import custatevec
print("cupy", cupy.__version__)
print("cuquantum", cuquantum.__version__)
print("custatevec", custatevec)
PY

echo "[2/6] State-vector correctness smoke"
"${PY}" benchmarks/smoke/simple_quantum_smoke.py \
  --qubits 10 \
  --depth 4 \
  --output "${OUTDIR}/statevector_10q_d4.json" >/dev/null

"${PY}" benchmarks/smoke/simple_quantum_smoke.py \
  --qubits 12 \
  --depth 4 \
  --output "${OUTDIR}/statevector_12q_d4.json" >/dev/null

echo "[3/6] Application-level ML vs quantum-circuit ML smoke"
"${PY}" benchmarks/smoke/ml_vs_quantum_circuit_smoke.py \
  --samples 64 \
  --features 2 \
  --depth 1 \
  --steps 400 \
  --output "${OUTDIR}/ml_vs_qc_64s_2f_d1.json" >/dev/null

"${PY}" benchmarks/smoke/ml_vs_quantum_circuit_smoke.py \
  --samples 64 \
  --features 4 \
  --depth 1 \
  --steps 400 \
  --output "${OUTDIR}/ml_vs_qc_64s_4f_d1.json" >/dev/null

echo "[4/6] Practical application workload suite"
"${PY}" benchmarks/workloads/run_practical_suite.py \
  --login-safe \
  --entangle \
  --output "${OUTDIR}/practical_suite_smoke.json" >/dev/null

echo "[5/6] Validate outputs"
"${PY}" benchmarks/smoke/validate_login_smoke.py \
  --statevector "${OUTDIR}/statevector_10q_d4.json" \
  --statevector "${OUTDIR}/statevector_12q_d4.json" \
  --ml "${OUTDIR}/ml_vs_qc_64s_2f_d1.json" \
  --ml "${OUTDIR}/ml_vs_qc_64s_4f_d1.json" \
  --practical "${OUTDIR}/practical_suite_smoke.json" \
  --min-native-acc 0.8 \
  --min-quantum-acc 0.75

echo "[6/6] Summary"
"${PY}" - <<'PY'
import glob, json, os
for path in sorted(glob.glob("data/raw/perlmutter/login_suite/*.json")):
    with open(path) as f:
        data = json.load(f)
    print(os.path.basename(path))
    if "workloads" in data:
        for name, workload in sorted(data["workloads"].items()):
            native = workload["native_path"]
            quantum = workload["quantum_path"]
            projection = workload["break_even_projection"]
            print("  {} native={:.6f}s quantum={:.6f}s required={:.2f}x".format(
                name,
                native["runtime_sec"],
                quantum["runtime_sec"],
                projection["sim_to_native_speedup_required"],
            ))
    elif "native_ml_path" in data:
        n = data["native_ml_path"]
        q = data["quantum_circuit_ml_path"]
        print("  native acc={:.4f} runtime={:.6f}s".format(n["test_accuracy"], n["runtime_sec"]))
        print("  quantum acc={:.4f} total={:.6f}s".format(q["test_accuracy"], q["total_runtime_sec"]))
    else:
        n = data["numpy_statevector"]
        q = data.get("custatevec_statevector", {})
        print("  numpy status={} norm={:.12f}".format(n["status"], n["checksum"]["norm"]))
        print("  custatevec status={} norm={:.12f}".format(q.get("status"), q.get("checksum", {}).get("norm", float("nan"))))
PY
