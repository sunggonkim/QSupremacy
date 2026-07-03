#!/bin/bash
#SBATCH -A m1248
#SBATCH -C gpu
#SBATCH -q shared
#SBATCH -t 00:30:00
#SBATCH -n 1
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-prac-sweep
#SBATCH -o logs/qsup-prac-sweep-1g-%j.out
#SBATCH -e logs/qsup-prac-sweep-1g-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-32}"

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/practical_suite_sweep
SUMMARY_DIR=data/processed/perlmutter
mkdir -p "${OUTDIR}" "${SUMMARY_DIR}" logs

echo "job_id=${SLURM_JOB_ID}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
echo "chunk_id=${QS_CHUNK_ID:-0}"
echo "chunk_count=${QS_CHUNK_COUNT:-1}"
nvidia-smi -L

run_case() {
  local tag="$1"
  shift
  echo "case_start=${tag} $(date --iso-8601=seconds)"
  "${PY}" benchmarks/workloads/run_practical_suite.py \
    "$@" \
    --entangle \
    --output "${OUTDIR}/practical_${SLURM_JOB_ID}_${tag}.json" >/dev/null
  echo "case_end=${tag} $(date --iso-8601=seconds)"
}

maybe_run_case() {
  local case_id="$1"
  shift
  local chunk_id="${QS_CHUNK_ID:-0}"
  local chunk_count="${QS_CHUNK_COUNT:-1}"
  if (( case_id % chunk_count == chunk_id )); then
    run_case "$@"
  fi
}

case_id=0

# Larger multiclass ML over the real sklearn digits dataset. Feature count is
# the PCA/qubit dimension used by the quantum feature circuit.
for seed in 17 23; do
  for classes in 0,1,2 3,5,8 0,1,2,3; do
    class_count=$(awk -F, '{print NF}' <<< "${classes}")
    class_tag="${classes//,/v}"
    for samples in 128 192 256; do
    for features in 4 6 8; do
      for depth in 1 2; do
        maybe_run_case "${case_id}" \
          "ml_digits_c${class_tag}_${samples}s_${features}q_d${depth}_seed${seed}" \
          --workloads ml \
          --seed "${seed}" \
          --ml-dataset digits \
          --digits-path data/datasets/sklearn_digits.npz \
          --digits-classes "${classes}" \
          --ml-samples "${samples}" \
          --ml-features "${features}" \
          --ml-classes "${class_count}" \
          --ml-depth "${depth}" \
          --ml-steps 300 \
          --mlp-steps 300 \
          --mlp-hidden 24
        case_id=$((case_id + 1))
      done
    done
    done
  done
done

# VQE-style chemistry. Grid size controls optimizer/search work. The built-in
# H2 case is a quality anchor; the 4-qubit fixture checks the generic Pauli
# Hamiltonian path that can receive OpenFermion/PySCF-generated inputs.
for seed in 17 23; do
  for grid in 17 21 25; do
    maybe_run_case "${case_id}" \
      "chem_h2_grid${grid}_seed${seed}" \
      --workloads chemistry \
      --seed "${seed}" \
      --chem-grid "${grid}" \
      --chem-layers 1
    case_id=$((case_id + 1))
  done
  for grid in 9 13; do
    maybe_run_case "${case_id}" \
      "chem_4q_grid${grid}_seed${seed}" \
      --workloads chemistry \
      --seed "${seed}" \
      --chem-grid "${grid}" \
      --chem-layers 1 \
      --chem-hamiltonian-json benchmarks/workloads/hamiltonians/molecular_chain_4q.json
    case_id=$((case_id + 1))
  done
done

# QAOA-style optimization over small MaxCut graph families.
for seed in 17 23; do
  for nodes in 4 5; do
    for graph in ring chordal ladder; do
    for grid in 7 9 11; do
      maybe_run_case "${case_id}" \
        "qaoa_${graph}_${nodes}n_grid${grid}_seed${seed}" \
        --workloads optimization \
        --seed "${seed}" \
        --opt-nodes "${nodes}" \
        --opt-graph "${graph}" \
        --opt-grid "${grid}"
      case_id=$((case_id + 1))
    done
    done
  done
done

# Hamiltonian simulation. Qubit count, physical model, and Trotter steps control
# circuit size.
for seed in 17 23; do
  for model in tfim heisenberg; do
  for qubits in 4 5 6; do
    for steps in 4 6 8; do
      maybe_run_case "${case_id}" \
        "sim_${model}_${qubits}q_${steps}steps_seed${seed}" \
        --workloads simulation \
        --seed "${seed}" \
        --sim-model "${model}" \
        --sim-qubits "${qubits}" \
        --sim-steps "${steps}" \
        --sim-time 0.8
      case_id=$((case_id + 1))
    done
  done
  done
done

echo "total_case_templates=${case_id}"

"${PY}" benchmarks/workloads/summarize_practical_results.py \
  "${OUTDIR}/practical_${SLURM_JOB_ID}_*.json" \
  --summary-json "${SUMMARY_DIR}/practical_suite_${SLURM_JOB_ID}_summary.json" \
  --csv "${SUMMARY_DIR}/practical_suite_${SLURM_JOB_ID}_summary.csv"

echo "date_end=$(date --iso-8601=seconds)"
