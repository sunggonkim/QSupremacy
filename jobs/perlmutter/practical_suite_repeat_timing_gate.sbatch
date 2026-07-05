#!/bin/bash
# Warmup-separated repeat timing gate for the practical suite.
#
# This is intentionally small: one Perlmutter GPU node, one task per A100,
# one representative case per workload family, one warmup, and three measured
# trials. It is evidence for timing stability, not a replacement for the large
# 3,552-case result.

#SBATCH -A m1248
#SBATCH -C gpu
#SBATCH -q debug
#SBATCH -t 00:20:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-repeat-gate
#SBATCH -o logs/qsup-repeat-gate-%j.out
#SBATCH -e logs/qsup-repeat-gate-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/repeat_timing_gate
SUMMARY_DIR=data/processed/perlmutter
RUN_TAG="${QS_RUN_TAG:-${SLURM_JOB_ID:-manual}_repeat_timing_gate}"
TRIALS="${QS_REPEAT_GATE_TRIALS:-3}"
CASE_TIMEOUT="${QS_CASE_TIMEOUT:-180s}"
mkdir -p "${OUTDIR}" "${SUMMARY_DIR}" logs

echo "run_tag=${RUN_TAG}"
echo "trials=${TRIALS}"
echo "case_timeout=${CASE_TIMEOUT}"
echo "date_start=$(date --iso-8601=seconds)"
nvidia-smi -L || true

export PY OUTDIR RUN_TAG TRIALS CASE_TIMEOUT

srun -N 1 -n 4 -c "${SLURM_CPUS_PER_TASK:-32}" \
  --gpus-per-task=1 \
  --gpu-bind=single:1 \
  bash -lc '
    set -euo pipefail
    cd /pscratch/sd/s/sgkim/Skim-Qsupreme
    source /etc/profile.d/zzz-lmod.sh
    module load cudatoolkit/12.9
    export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-32}"
    task="${SLURM_PROCID}"
    case "${task}" in
      0)
        family="ml"
        args=(--workloads ml --seed 17 --ml-dataset digits --digits-path data/datasets/sklearn_digits.npz --digits-classes 0,1,2 --ml-samples 128 --ml-features 4 --ml-classes 3 --ml-depth 1 --ml-steps 300 --mlp-steps 300 --mlp-hidden 24)
        ;;
      1)
        family="chemistry"
        args=(--workloads chemistry --seed 17 --chem-grid 17 --chem-layers 1 --chem-hamiltonian-json benchmarks/workloads/hamiltonians/h2_sto3g_4q.json)
        ;;
      2)
        family="optimization"
        args=(--workloads optimization --seed 17 --opt-nodes 4 --opt-graph chordal --opt-grid 7)
        ;;
      3)
        family="simulation"
        args=(--workloads simulation --seed 17 --sim-model tfim --sim-qubits 4 --sim-steps 4 --sim-time 0.8)
        ;;
      *)
        echo "unexpected task=${task}" >&2
        exit 2
        ;;
    esac

    echo "family_start=${family} task=${task} host=$(hostname) cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset} ld_library_path=${LD_LIBRARY_PATH:-unset}"

    timeout "${CASE_TIMEOUT}" "${PY}" benchmarks/workloads/run_practical_suite.py \
      "${args[@]}" --entangle \
      --output "${OUTDIR}/repeat_${RUN_TAG}_${family}_warmup.json" >/dev/null

    for trial in $(seq 0 $((TRIALS - 1))); do
      timeout "${CASE_TIMEOUT}" "${PY}" benchmarks/workloads/run_practical_suite.py \
        "${args[@]}" --entangle \
        --output "${OUTDIR}/repeat_${RUN_TAG}_${family}_trial${trial}.json" >/dev/null
    done

    echo "family_end=${family} task=${task}"
  '

"${PY}" scripts/summarize_repeat_timing_gate.py \
  "${OUTDIR}/repeat_${RUN_TAG}_*.json" \
  --summary-json "${SUMMARY_DIR}/repeat_timing_gate_${RUN_TAG}.json" \
  --markdown "${SUMMARY_DIR}/repeat_timing_gate_${RUN_TAG}.md"

cp "${SUMMARY_DIR}/repeat_timing_gate_${RUN_TAG}.json" \
  "${SUMMARY_DIR}/repeat_timing_gate_latest.json"
cp "${SUMMARY_DIR}/repeat_timing_gate_${RUN_TAG}.md" \
  "${SUMMARY_DIR}/repeat_timing_gate_latest.md"

sacct -j "${SLURM_JOB_ID:-}" \
  --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,AllocTRES%80 \
  -P > "data/raw/perlmutter/accounting/sacct_repeat_timing_gate_${RUN_TAG}.txt" || true

echo "summary_json=${SUMMARY_DIR}/repeat_timing_gate_${RUN_TAG}.json"
echo "summary_md=${SUMMARY_DIR}/repeat_timing_gate_${RUN_TAG}.md"
echo "date_end=$(date --iso-8601=seconds)"
