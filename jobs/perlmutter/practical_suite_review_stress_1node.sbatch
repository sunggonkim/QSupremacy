#!/bin/bash
# Reviewer-response stress gate: one larger/deeper case per workload family.
# This is not the main scaling suite. It checks that the same-input record path
# remains executable when the workload is pushed beyond the main exact sweep.

#SBATCH -A m1248
#SBATCH -C gpu
#SBATCH -q debug
#SBATCH -t 00:30:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-review-stress
#SBATCH -o logs/qsup-review-stress-%j.out
#SBATCH -e logs/qsup-review-stress-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-32}"

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/practical_suite_sweep
SUMMARY_DIR=data/processed/perlmutter
LOGDIR=logs
JOB_ID="${SLURM_JOB_ID:-manual}"
RUN_TAG="${QS_RUN_TAG:-${JOB_ID}_review_stress_1n_4g}"

mkdir -p "${OUTDIR}" "${SUMMARY_DIR}" "${LOGDIR}" data/raw/perlmutter/accounting

echo "job_id=${JOB_ID}"
echo "run_tag=${RUN_TAG}"
echo "date_start=$(date --iso-8601=seconds)"
hostname
nvidia-smi -L || true

run_case() {
  local gpu="$1"
  local tag="$2"
  shift 2
  echo "case_start=${tag} gpu=${gpu} $(date --iso-8601=seconds)"
  CUDA_VISIBLE_DEVICES="${gpu}" timeout "${QS_CASE_TIMEOUT:-1200s}" \
    "${PY}" benchmarks/workloads/run_practical_suite.py \
      "$@" \
      --entangle \
      --output "${OUTDIR}/practical_${RUN_TAG}_${tag}.json" \
      >"${LOGDIR}/qsup-review-stress-${RUN_TAG}-${tag}.out" \
      2>"${LOGDIR}/qsup-review-stress-${RUN_TAG}-${tag}.err" &
}

run_case 0 "ml_digits_512s_12q_d3_seed17" \
  --workloads ml \
  --seed 17 \
  --ml-dataset digits \
  --digits-path data/datasets/sklearn_digits.npz \
  --digits-classes "0,1,2,3" \
  --ml-samples 512 \
  --ml-features 12 \
  --ml-classes 4 \
  --ml-depth 3 \
  --ml-steps 300 \
  --mlp-steps 300 \
  --mlp-hidden 32

run_case 1 "chem_h2o_8q_l3_grid65_seed17" \
  --workloads chemistry \
  --seed 17 \
  --chem-hamiltonian-json benchmarks/workloads/hamiltonians/h2o_sto3g_active_8q.json \
  --chem-layers 3 \
  --chem-grid 65

run_case 2 "qaoa_chordal_20n_grid5_seed17" \
  --workloads optimization \
  --seed 17 \
  --opt-nodes 20 \
  --opt-graph chordal \
  --opt-grid 5 \
  --opt-local-restarts 128 \
  --opt-anneal-steps 2000

run_case 3 "sim_heisenberg_12q_16steps_seed17" \
  --workloads simulation \
  --seed 17 \
  --sim-model heisenberg \
  --sim-qubits 12 \
  --sim-steps 16 \
  --sim-time 0.8 \
  --sim-native-baselines sparse_krylov \
  --sim-krylov-dim 96

wait

"${PY}" benchmarks/workloads/summarize_practical_results.py \
  "${OUTDIR}/practical_${RUN_TAG}_*.json" \
  --summary-json "${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.json" \
  --csv "${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.csv"

sacct -j "${JOB_ID}" \
  --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,AllocTRES%80 \
  -P > "data/raw/perlmutter/accounting/sacct_practical_suite_${RUN_TAG}.txt" || true

echo "summary_json=${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.json"
echo "summary_csv=${SUMMARY_DIR}/practical_suite_${RUN_TAG}_summary.csv"
echo "accounting=data/raw/perlmutter/accounting/sacct_practical_suite_${RUN_TAG}.txt"
echo "date_end=$(date --iso-8601=seconds)"
