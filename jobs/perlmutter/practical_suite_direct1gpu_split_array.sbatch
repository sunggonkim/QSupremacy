#!/bin/bash
# Split one-GPU fixed-work strong-scaling anchor for the full 7,104-case suite.
# Each array task runs a striped subset of the 256 chunks, so every task has
# roughly the same work as one GPU in the completed 32-GPU direct run.

#SBATCH -A m5320
#SBATCH -C gpu
#SBATCH -q shared
#SBATCH -t 02:00:00
#SBATCH -n 1
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-d1split
#SBATCH -o logs/qsup-d1split-%A_%a.out
#SBATCH -e logs/qsup-d1split-%A_%a.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

OUTDIR=data/raw/perlmutter/practical_suite_sweep
LOGDIR=logs
mkdir -p "${OUTDIR}" "${LOGDIR}" data/raw/perlmutter/accounting

ARRAY_JOB_ID="${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-manual}}"
GROUP="${SLURM_ARRAY_TASK_ID:-0}"
GROUP_COUNT="${QS_GROUP_COUNT:-32}"
CHUNK_COUNT="${QS_CHUNK_COUNT:-256}"
RUN_TAG="${QS_RUN_TAG:-${ARRAY_JOB_ID}_direct1_split_1g_7104}"
FAMILIES="${QS_WORKLOAD_FAMILIES:-all}"
CASE_TIMEOUT="${QS_CASE_TIMEOUT:-120s}"
SWEEP_PROFILE="${QS_SWEEP_PROFILE:-large}"
REPEAT_COUNT="${QS_REPEAT_COUNT:-8}"

chunk_ids=""
next_chunk="${GROUP}"
while (( next_chunk < CHUNK_COUNT )); do
  if [[ -n "${chunk_ids}" ]]; then
    chunk_ids="${chunk_ids},"
  fi
  chunk_ids="${chunk_ids}${next_chunk}"
  next_chunk=$((next_chunk + GROUP_COUNT))
done

echo "array_job_id=${ARRAY_JOB_ID}"
echo "array_task_id=${GROUP}"
echo "run_tag=${RUN_TAG}"
echo "group_count=${GROUP_COUNT}"
echo "chunk_count=${CHUNK_COUNT}"
echo "chunk_ids=${chunk_ids}"
echo "workload_families=${FAMILIES}"
echo "case_timeout=${CASE_TIMEOUT}"
echo "sweep_profile=${SWEEP_PROFILE}"
echo "repeat_count=${REPEAT_COUNT}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L || true

env \
  SLURM_JOB_ID="${RUN_TAG}_c${GROUP}" \
  QS_CHUNK_ID="${GROUP}" \
  QS_CHUNK_IDS="${chunk_ids}" \
  QS_CHUNK_COUNT="${CHUNK_COUNT}" \
  QS_WORKLOAD_FAMILIES="${FAMILIES}" \
  QS_CASE_TIMEOUT="${CASE_TIMEOUT}" \
  QS_PREFLIGHT_ONLY="${QS_PREFLIGHT_ONLY:-0}" \
  QS_SWEEP_PROFILE="${SWEEP_PROFILE}" \
  QS_REPEAT_COUNT="${REPEAT_COUNT}" \
  bash jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch \
  >"${LOGDIR}/qsup-d1split-${RUN_TAG}-c${GROUP}.out" \
  2>"${LOGDIR}/qsup-d1split-${RUN_TAG}-c${GROUP}.err"

echo "date_end=$(date --iso-8601=seconds)"
