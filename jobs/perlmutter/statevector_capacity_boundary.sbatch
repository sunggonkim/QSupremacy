#!/bin/bash
# Capacity-boundary probe for high-qubit state-vector footprints.
#
# Examples:
#   QS_CAP_QUBITS=36 sbatch -q regular -t 00:30:00 -N 16 jobs/perlmutter/statevector_capacity_boundary.sbatch
#   QS_CAP_QUBITS=38 sbatch -q regular -t 00:45:00 -N 32 jobs/perlmutter/statevector_capacity_boundary.sbatch
#   QS_CAP_QUBITS=40 sbatch -q regular -t 01:00:00 -N 64 jobs/perlmutter/statevector_capacity_boundary.sbatch

#SBATCH -A m5320
#SBATCH -C gpu
#SBATCH -q regular
#SBATCH -t 01:00:00
#SBATCH -N 16
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-capq
#SBATCH -o logs/qsup-capq-%j.out
#SBATCH -e logs/qsup-capq-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
QUBITS="${QS_CAP_QUBITS:-36}"
DEPTH="${QS_CAP_DEPTH:-4}"
OUTDIR="${QS_CAP_OUTDIR:-data/raw/perlmutter/statevector_capacity}"
SUMMARY_DIR="${QS_CAP_SUMMARY_DIR:-data/processed/perlmutter}"
RUN_TAG="${QS_CAP_RUN_TAG:-${SLURM_JOB_ID}_cap_${QUBITS}q_${SLURM_JOB_NUM_NODES}n_$((SLURM_JOB_NUM_NODES * 4))g}"

mkdir -p "${OUTDIR}" "${SUMMARY_DIR}" logs

echo "run_tag=${RUN_TAG}"
echo "qubits=${QUBITS}"
echo "depth=${DEPTH}"
echo "nodes=${SLURM_JOB_NUM_NODES}"
echo "tasks=${SLURM_NTASKS}"
echo "date_start=$(date --iso-8601=seconds)"
scontrol show hostnames "${SLURM_JOB_NODELIST}"
nvidia-smi -L || true

export CUPY_CACHE_DIR="${OUTDIR}/cupy_cache_${SLURM_JOB_ID}"

srun -N "${SLURM_JOB_NUM_NODES}" -n "${SLURM_NTASKS}" -c "${SLURM_CPUS_PER_TASK}" \
  --gpus-per-task=1 \
  --gpu-bind=single:1 \
  "${PY}" scripts/run_statevector_capacity_boundary.py run \
    --qubits "${QUBITS}" \
    --depth "${DEPTH}" \
    --run-tag "${RUN_TAG}" \
    --out-dir "${OUTDIR}"

"${PY}" scripts/run_statevector_capacity_boundary.py summarize \
  --summary-glob "${OUTDIR}/${RUN_TAG}_${QUBITS}q_rank*.json" \
  --summary-out "${SUMMARY_DIR}/statevector_capacity_${RUN_TAG}_summary.json"

sacct -j "${SLURM_JOB_ID}" \
  --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,AllocTRES%80 \
  -P > "data/raw/perlmutter/accounting/sacct_statevector_capacity_${RUN_TAG}.txt" || true

echo "summary_json=${SUMMARY_DIR}/statevector_capacity_${RUN_TAG}_summary.json"
echo "date_end=$(date --iso-8601=seconds)"
