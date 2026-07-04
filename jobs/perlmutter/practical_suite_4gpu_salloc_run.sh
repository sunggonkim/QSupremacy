#!/bin/bash
# Run inside an existing one-node, four-GPU allocation.

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/practical_suite_sweep
SUMMARY_DIR=data/processed/perlmutter
LOGDIR=logs
mkdir -p "${OUTDIR}" "${SUMMARY_DIR}" "${LOGDIR}"

ALLOC_ID="${SLURM_JOB_ID:-manual}"
RUN_TAG="${QS_RUN_TAG:-${ALLOC_ID}_4gpu}"
CHUNK_COUNT="${QS_CHUNK_COUNT:-4}"
TASK_COUNT="${QS_TASK_COUNT:-${CHUNK_COUNT}}"
FAMILIES="${QS_WORKLOAD_FAMILIES:-all}"
CASE_TIMEOUT="${QS_CASE_TIMEOUT:-90s}"
CPUS_PER_CHUNK="${QS_CPUS_PER_CHUNK:-32}"
MEM_PER_CHUNK="${QS_MEM_PER_CHUNK:-55G}"
SWEEP_PROFILE="${QS_SWEEP_PROFILE:-standard}"
REPEAT_COUNT="${QS_REPEAT_COUNT:-}"

echo "allocation_id=${ALLOC_ID}"
echo "run_tag=${RUN_TAG}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "chunk_count=${CHUNK_COUNT}"
echo "task_count=${TASK_COUNT}"
echo "workload_families=${FAMILIES}"
echo "case_timeout=${CASE_TIMEOUT}"
echo "cpus_per_chunk=${CPUS_PER_CHUNK}"
echo "mem_per_chunk=${MEM_PER_CHUNK}"
echo "sweep_profile=${SWEEP_PROFILE}"
echo "repeat_count=${REPEAT_COUNT:-auto}"
nvidia-smi -L

export RUN_TAG CHUNK_COUNT TASK_COUNT FAMILIES CASE_TIMEOUT LOGDIR
echo "launch_single_srun_step_tasks=${TASK_COUNT}"
srun -N 1 -n "${TASK_COUNT}" -c "${CPUS_PER_CHUNK}" \
  --gpus-per-task=1 \
  --gpu-bind=single:1 \
  bash -lc '
    set -euo pipefail
    cd /pscratch/sd/s/sgkim/Skim-Qsupreme
    chunk="${SLURM_PROCID}"
    chunk_tag="${RUN_TAG}_c${chunk}"
    out_log="${LOGDIR}/qsup-prac-4gpu-${chunk_tag}.out"
    err_log="${LOGDIR}/qsup-prac-4gpu-${chunk_tag}.err"
    echo "task_start=${chunk} tag=${chunk_tag} host=$(hostname) cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
    env \
      SLURM_JOB_ID="${chunk_tag}" \
      QS_CHUNK_ID="${chunk}" \
      QS_CHUNK_IDS="${chunk}" \
      QS_CHUNK_COUNT="${CHUNK_COUNT}" \
      QS_WORKLOAD_FAMILIES="${FAMILIES}" \
      QS_CASE_TIMEOUT="${CASE_TIMEOUT}" \
      QS_SWEEP_PROFILE="${SWEEP_PROFILE}" \
      QS_REPEAT_COUNT="${REPEAT_COUNT}" \
      bash jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch \
      >"${out_log}" 2>"${err_log}"
    echo "task_end=${chunk} tag=${chunk_tag}"
  '

"${PY}" benchmarks/workloads/summarize_practical_results.py \
  "${OUTDIR}/practical_${RUN_TAG}_c*.json" \
  --summary-json "${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.json" \
  --csv "${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.csv"

echo "summary_json=${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.json"
echo "summary_csv=${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.csv"
echo "date_end=$(date --iso-8601=seconds)"
