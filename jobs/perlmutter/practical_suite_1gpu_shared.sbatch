#!/bin/bash
#SBATCH -A m5320
#SBATCH -C gpu
#SBATCH -q shared
#SBATCH -t 00:15:00
#SBATCH -n 1
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-practical
#SBATCH -o logs/qsup-practical-1g-%j.out
#SBATCH -e logs/qsup-practical-1g-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-32}"

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/practical_suite
mkdir -p "${OUTDIR}" logs

echo "job_id=${SLURM_JOB_ID}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L

"${PY}" benchmarks/workloads/run_practical_suite.py \
  --login-safe \
  --entangle \
  --output "${OUTDIR}/practical_suite_${SLURM_JOB_ID}.json" >/dev/null

"${PY}" benchmarks/smoke/validate_login_smoke.py \
  --practical "${OUTDIR}/practical_suite_${SLURM_JOB_ID}.json"

echo "date_end=$(date --iso-8601=seconds)"
