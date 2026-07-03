#!/bin/bash
#SBATCH -A m1248
#SBATCH -C gpu
#SBATCH -q debug
#SBATCH -t 00:10:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -c 32
#SBATCH --gpus-per-node=4
#SBATCH -J qadv-ml-qc
#SBATCH -o logs/qadv-ml-qc-%j.out
#SBATCH -e logs/qadv-ml-qc-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-32}"

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/gpu_node

echo "job_id=${SLURM_JOB_ID}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L

"${PY}" benchmarks/smoke/ml_vs_quantum_circuit_smoke.py \
  --samples 128 \
  --features 4 \
  --depth 1 \
  --steps 400 \
  --output "${OUTDIR}/ml_vs_qc_${SLURM_JOB_ID}_128s_4f_d1.json"

"${PY}" benchmarks/smoke/ml_vs_quantum_circuit_smoke.py \
  --samples 256 \
  --features 4 \
  --depth 1 \
  --steps 400 \
  --output "${OUTDIR}/ml_vs_qc_${SLURM_JOB_ID}_256s_4f_d1.json"

"${PY}" benchmarks/smoke/ml_vs_quantum_circuit_smoke.py \
  --samples 128 \
  --features 8 \
  --depth 1 \
  --steps 400 \
  --output "${OUTDIR}/ml_vs_qc_${SLURM_JOB_ID}_128s_8f_d1.json"

echo "date_end=$(date --iso-8601=seconds)"
