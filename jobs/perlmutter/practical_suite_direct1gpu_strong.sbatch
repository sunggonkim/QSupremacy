#!/bin/bash
# One-GPU fixed-work strong-scaling point for the full 7,104-case large suite.

#SBATCH -A m1248
#SBATCH -C gpu
#SBATCH -q shared
#SBATCH -t 36:00:00
#SBATCH -n 1
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-direct1
#SBATCH -o logs/qsup-direct1-%j.out
#SBATCH -e logs/qsup-direct1-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/practical_suite_sweep
SUMMARY_DIR=data/processed/perlmutter
LOGDIR=logs
mkdir -p "${OUTDIR}" "${SUMMARY_DIR}" "${LOGDIR}" data/raw/perlmutter/accounting

ALLOC_ID="${SLURM_JOB_ID:-manual}"
RUN_TAG="${QS_RUN_TAG:-${ALLOC_ID}_direct1_strong_1g_7104}"
CHUNK_COUNT="${QS_CHUNK_COUNT:-256}"
FAMILIES="${QS_WORKLOAD_FAMILIES:-all}"
CASE_TIMEOUT="${QS_CASE_TIMEOUT:-120s}"
SWEEP_PROFILE="${QS_SWEEP_PROFILE:-large}"
REPEAT_COUNT="${QS_REPEAT_COUNT:-8}"
CHUNK_IDS="$(seq -s, 0 $((CHUNK_COUNT - 1)))"

echo "allocation_id=${ALLOC_ID}"
echo "run_tag=${RUN_TAG}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "chunk_count=${CHUNK_COUNT}"
echo "chunk_ids=${CHUNK_IDS}"
echo "workload_families=${FAMILIES}"
echo "case_timeout=${CASE_TIMEOUT}"
echo "sweep_profile=${SWEEP_PROFILE}"
echo "repeat_count=${REPEAT_COUNT}"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L || true

env \
  SLURM_JOB_ID="${RUN_TAG}_c0" \
  QS_CHUNK_ID="0" \
  QS_CHUNK_IDS="${CHUNK_IDS}" \
  QS_CHUNK_COUNT="${CHUNK_COUNT}" \
  QS_WORKLOAD_FAMILIES="${FAMILIES}" \
  QS_CASE_TIMEOUT="${CASE_TIMEOUT}" \
  QS_PREFLIGHT_ONLY="${QS_PREFLIGHT_ONLY:-0}" \
  QS_SWEEP_PROFILE="${SWEEP_PROFILE}" \
  QS_REPEAT_COUNT="${REPEAT_COUNT}" \
  bash jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch \
  >"${LOGDIR}/qsup-direct1-${RUN_TAG}.out" \
  2>"${LOGDIR}/qsup-direct1-${RUN_TAG}.err"

if [[ "${QS_PREFLIGHT_ONLY:-0}" == "1" ]]; then
  echo "preflight_complete=${RUN_TAG}"
  echo "date_end=$(date --iso-8601=seconds)"
  exit 0
fi

"${PY}" benchmarks/workloads/summarize_practical_results.py \
  "${OUTDIR}/practical_${RUN_TAG}_c*.json" \
  --summary-json "${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.json" \
  --csv "${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.csv"

sacct -j "${ALLOC_ID}" \
  --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,AllocTRES%80 \
  -P > "data/raw/perlmutter/accounting/sacct_practical_suite_${RUN_TAG}.txt" || true

echo "summary_json=${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.json"
echo "summary_csv=${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.csv"
echo "accounting=data/raw/perlmutter/accounting/sacct_practical_suite_${RUN_TAG}.txt"
echo "date_end=$(date --iso-8601=seconds)"
