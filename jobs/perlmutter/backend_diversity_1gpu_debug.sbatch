#!/bin/bash
#SBATCH -A m5320
#SBATCH -C gpu
#SBATCH -q debug
#SBATCH -t 00:15:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-backend-sanity
#SBATCH -o logs/qsup-backend-sanity-%j.out
#SBATCH -e logs/qsup-backend-sanity-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-32}"
export PYTHONNOUSERSITE=1

CUDAQ_PY=/pscratch/sd/s/sgkim/zainab-qsims/cudaq-env/bin/python
CUQ_PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/backend_sanity
mkdir -p "${OUTDIR}" logs

echo "job_id=${SLURM_JOB_ID}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L

echo "[1/3] Backend diversity smoke"
"${CUDAQ_PY}" benchmarks/smoke/backend_diversity_smoke.py \
  --cuquantum-python "${CUQ_PY}" \
  --output "${OUTDIR}/backend_diversity_${SLURM_JOB_ID}.json"

echo "[2/3] Application practical-suite smoke"
"${CUQ_PY}" benchmarks/workloads/run_practical_suite.py \
  --login-safe \
  --entangle \
  --output "${OUTDIR}/practical_suite_${SLURM_JOB_ID}.json" >/dev/null

"${CUQ_PY}" benchmarks/smoke/validate_login_smoke.py \
  --practical "${OUTDIR}/practical_suite_${SLURM_JOB_ID}.json"

echo "[3/3] Summary"
"${CUDAQ_PY}" - <<PY
import json
for path in [
    "${OUTDIR}/backend_diversity_${SLURM_JOB_ID}.json",
    "${OUTDIR}/practical_suite_${SLURM_JOB_ID}.json",
]:
    with open(path) as f:
        data = json.load(f)
    print(path)
    if "pass" in data:
        print("  pass={}".format(data["pass"]))
        for name in data["required_backends"]:
            item = data[name]
            print("  {} status={} runtime={:.6f}s".format(
                name, item.get("status"), item.get("runtime_sec", 0.0)
            ))
        print("  qiskit_aer_gpu status={}".format(data["qiskit_aer_gpu"].get("status")))
    else:
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
PY

echo "date_end=$(date --iso-8601=seconds)"
