#!/bin/bash
# Embarrassingly parallel scale-out runner for 1-32 Perlmutter GPU nodes.
#
# Override at submit time, for example:
#   sbatch -q debug -t 00:30:00 -N 1 jobs/perlmutter/practical_suite_scale_nodes.sbatch
#   sbatch -q regular -t 01:00:00 -N 16 jobs/perlmutter/practical_suite_scale_nodes.sbatch
#
# Scaling modes:
#   QS_SCALE_MODE=weak    each GPU runs one chunk slot; total work grows with GPUs.
#   QS_SCALE_MODE=strong  all chunk slots are striped over available GPUs.
#
# Reviewer-response scale ladder smoke:
#   QS_SWEEP_PROFILE=scale_ladder_debug QS_SCALE_MODE=weak QS_CHUNK_COUNT=4 \
#     sbatch -q debug -t 00:30:00 -N 1 jobs/perlmutter/practical_suite_scale_nodes.sbatch

#SBATCH -A m5320
#SBATCH -C gpu
#SBATCH -q debug
#SBATCH -t 00:30:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-prac-scale
#SBATCH -o logs/qsup-prac-scale-%j.out
#SBATCH -e logs/qsup-prac-scale-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/practical_suite_sweep
SUMMARY_DIR=data/processed/perlmutter
LOGDIR=logs
mkdir -p "${OUTDIR}" "${SUMMARY_DIR}" "${LOGDIR}"

ALLOC_ID="${SLURM_JOB_ID:-manual}"
NODE_COUNT="${SLURM_JOB_NUM_NODES:-1}"
TASKS_PER_NODE="${SLURM_NTASKS_PER_NODE:-4}"
TASK_COUNT="${QS_TASK_COUNT:-$((NODE_COUNT * 4))}"
CHUNK_COUNT="${QS_CHUNK_COUNT:-${TASK_COUNT}}"
FAMILIES="${QS_WORKLOAD_FAMILIES:-all}"
CASE_TIMEOUT="${QS_CASE_TIMEOUT:-120s}"
CPUS_PER_CHUNK="${QS_CPUS_PER_CHUNK:-${SLURM_CPUS_PER_TASK:-32}}"
RUN_TAG="${QS_RUN_TAG:-${ALLOC_ID}_scale_${NODE_COUNT}n_${TASK_COUNT}g}"
SWEEP_PROFILE="${QS_SWEEP_PROFILE:-standard}"
REPEAT_COUNT="${QS_REPEAT_COUNT:-}"
SCALE_MODE="${QS_SCALE_MODE:-weak}"

if [[ "${SCALE_MODE}" != "weak" && "${SCALE_MODE}" != "strong" ]]; then
  echo "unsupported QS_SCALE_MODE=${SCALE_MODE}; expected weak or strong" >&2
  exit 2
fi

echo "allocation_id=${ALLOC_ID}"
echo "run_tag=${RUN_TAG}"
echo "node_count=${NODE_COUNT}"
echo "tasks_per_node=${TASKS_PER_NODE}"
echo "task_count=${TASK_COUNT}"
echo "chunk_count=${CHUNK_COUNT}"
echo "workload_families=${FAMILIES}"
echo "case_timeout=${CASE_TIMEOUT}"
echo "cpus_per_chunk=${CPUS_PER_CHUNK}"
echo "preflight_only=${QS_PREFLIGHT_ONLY:-0}"
echo "sweep_profile=${SWEEP_PROFILE}"
echo "repeat_count=${REPEAT_COUNT:-auto}"
echo "scale_mode=${SCALE_MODE}"
echo "date_start=$(date --iso-8601=seconds)"
if [[ -n "${SLURM_JOB_NODELIST:-}" ]]; then
  scontrol show hostnames "${SLURM_JOB_NODELIST}"
else
  hostname
fi
nvidia-smi -L || true

export RUN_TAG CHUNK_COUNT TASK_COUNT FAMILIES CASE_TIMEOUT LOGDIR SWEEP_PROFILE REPEAT_COUNT SCALE_MODE
srun -N "${NODE_COUNT}" -n "${TASK_COUNT}" -c "${CPUS_PER_CHUNK}" \
  --gpus-per-task=1 \
  --gpu-bind=single:1 \
  bash -lc '
    set -euo pipefail
    cd /pscratch/sd/s/sgkim/Skim-Qsupreme
    chunk="${SLURM_PROCID}"
    chunk_tag="${RUN_TAG}_c${chunk}"
    if [[ "${SCALE_MODE}" == "strong" ]]; then
      chunk_ids=""
      next_chunk="${chunk}"
      while (( next_chunk < CHUNK_COUNT )); do
        if [[ -n "${chunk_ids}" ]]; then
          chunk_ids="${chunk_ids},"
        fi
        chunk_ids="${chunk_ids}${next_chunk}"
        next_chunk=$((next_chunk + TASK_COUNT))
      done
    else
      chunk_ids="${chunk}"
    fi
    out_log="${LOGDIR}/qsup-prac-scale-${chunk_tag}.out"
    err_log="${LOGDIR}/qsup-prac-scale-${chunk_tag}.err"
    echo "task_start=${chunk} tag=${chunk_tag} chunk_ids=${chunk_ids} host=$(hostname) cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
    env \
      SLURM_JOB_ID="${chunk_tag}" \
      QS_CHUNK_ID="${chunk}" \
      QS_CHUNK_IDS="${chunk_ids}" \
      QS_CHUNK_COUNT="${CHUNK_COUNT}" \
      QS_WORKLOAD_FAMILIES="${FAMILIES}" \
      QS_CASE_TIMEOUT="${CASE_TIMEOUT}" \
      QS_PREFLIGHT_ONLY="${QS_PREFLIGHT_ONLY:-0}" \
      QS_SWEEP_PROFILE="${SWEEP_PROFILE}" \
      QS_REPEAT_COUNT="${REPEAT_COUNT}" \
      bash jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch \
      >"${out_log}" 2>"${err_log}"
    echo "task_end=${chunk} tag=${chunk_tag}"
  '

if [[ "${QS_PREFLIGHT_ONLY:-0}" == "1" ]]; then
  echo "preflight_complete=${RUN_TAG}"
  echo "date_end=$(date --iso-8601=seconds)"
  exit 0
fi

"${PY}" benchmarks/workloads/summarize_practical_results.py \
  "${OUTDIR}/practical_${RUN_TAG}_c*.json" \
  --summary-json "${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.json" \
  --csv "${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.csv"

# The root allocation is still RUNNING here. This snapshot is provisional;
# refresh it from SlurmDBD after completion with refresh_slurm_accounting.py.
sacct -j "${ALLOC_ID}" \
  --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,AllocTRES%80 \
  -P > "data/raw/perlmutter/accounting/sacct_practical_suite_${RUN_TAG}.txt" || true

echo "summary_json=${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.json"
echo "summary_csv=${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.csv"
echo "accounting_provisional=data/raw/perlmutter/accounting/sacct_practical_suite_${RUN_TAG}.txt"
echo "date_end=$(date --iso-8601=seconds)"
