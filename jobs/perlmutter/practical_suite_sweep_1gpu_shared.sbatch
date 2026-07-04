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
JOB_ID="${SLURM_JOB_ID:-manual}"
mkdir -p "${OUTDIR}" "${SUMMARY_DIR}" logs

echo "job_id=${JOB_ID}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
echo "chunk_id=${QS_CHUNK_ID:-0}"
echo "chunk_ids=${QS_CHUNK_IDS:-${QS_CHUNK_ID:-0}}"
echo "chunk_count=${QS_CHUNK_COUNT:-1}"
echo "workload_families=${QS_WORKLOAD_FAMILIES:-all}"
echo "case_timeout=${QS_CASE_TIMEOUT:-120s}"
echo "preflight_only=${QS_PREFLIGHT_ONLY:-0}"
echo "sweep_profile=${QS_SWEEP_PROFILE:-standard}"
echo "repeat_count=${QS_REPEAT_COUNT:-auto}"
nvidia-smi -L || true

family_enabled() {
  local family="$1"
  local enabled="${QS_WORKLOAD_FAMILIES:-all}"
  if [[ "${enabled}" == "all" ]]; then
    return 0
  fi
  local candidate
  IFS=',' read -ra candidates <<< "${enabled}"
  for candidate in "${candidates[@]}"; do
    if [[ "${candidate}" == "${family}" ]]; then
      return 0
    fi
  done
  return 1
}

run_case() {
  local tag="$1"
  shift
  if [[ "${QS_PREFLIGHT_ONLY:-0}" == "1" ]]; then
    echo "case_would_run=${tag}"
    return
  fi
  echo "case_start=${tag} $(date --iso-8601=seconds)"
  if timeout "${QS_CASE_TIMEOUT:-120s}" "${PY}" benchmarks/workloads/run_practical_suite.py \
    "$@" \
    --entangle \
    --output "${OUTDIR}/practical_${JOB_ID}_${tag}.json" >/dev/null; then
    echo "case_end=${tag} $(date --iso-8601=seconds)"
  else
    local rc=$?
    echo "case_failed=${tag} rc=${rc} $(date --iso-8601=seconds)"
  fi
}

maybe_run_case() {
  local case_id="$1"
  shift
  local chunk_id="${QS_CHUNK_ID:-0}"
  local chunk_ids="${QS_CHUNK_IDS:-${chunk_id}}"
  local chunk_count="${QS_CHUNK_COUNT:-1}"
  local slot=$((case_id % chunk_count))
  local candidate
  IFS=',' read -ra candidates <<< "${chunk_ids}"
  for candidate in "${candidates[@]}"; do
    if (( slot == candidate )); then
      run_case "$@"
      return
    fi
  done
}

case_id=0

SWEEP_PROFILE="${QS_SWEEP_PROFILE:-standard}"
if [[ -n "${QS_REPEAT_COUNT:-}" ]]; then
  REPEAT_COUNT="${QS_REPEAT_COUNT}"
elif [[ "${SWEEP_PROFILE}" == "large" ]]; then
  REPEAT_COUNT=4
else
  REPEAT_COUNT=1
fi

if [[ "${SWEEP_PROFILE}" == "large" ]]; then
  SEEDS=(17 23 31 43)
  ML_CLASSES=("0,1,2" "3,5,8" "0,1,2,3" "2,4,6,8")
  ML_SAMPLES=(128 192 256 320)
  ML_FEATURES=(4 6 8 10)
  ML_DEPTHS=(1 2)
  CHEM_H2_GRIDS=(17 21 25 33)
  CHEM_JSON_GRIDS=(9 13 17)
  CHEM_LAYERS=(1 2)
  OPT_NODES=(4 5 6 7)
  OPT_GRAPHS=(ring chordal ladder)
  OPT_GRIDS=(7 9 11 13)
  SIM_MODELS=(tfim heisenberg)
  SIM_QUBITS=(4 5 6 7)
  SIM_STEPS=(4 6 8 10)
elif [[ "${SWEEP_PROFILE}" == "accept" ]]; then
  SEEDS=(17 23)
  ML_CLASSES=("0,1,2" "3,5,8")
  ML_SAMPLES=(128 192)
  ML_FEATURES=(4 6)
  ML_DEPTHS=(1 2)
  CHEM_H2_GRIDS=(17 21)
  CHEM_JSON_GRIDS=(9 13 17)
  CHEM_LAYERS=(1 2)
  OPT_NODES=(4 5)
  OPT_GRAPHS=(ring chordal)
  OPT_GRIDS=(7 9)
  SIM_MODELS=(tfim heisenberg)
  SIM_QUBITS=(4 5 6 7 8)
  SIM_STEPS=(4 6 8)
else
  SEEDS=(17 23)
  ML_CLASSES=("0,1,2" "3,5,8" "0,1,2,3")
  ML_SAMPLES=(128 192 256)
  ML_FEATURES=(4 6 8)
  ML_DEPTHS=(1 2)
  CHEM_H2_GRIDS=(17 21 25)
  CHEM_JSON_GRIDS=(9 13)
  CHEM_LAYERS=(1)
  OPT_NODES=(4 5)
  OPT_GRAPHS=(ring chordal ladder)
  OPT_GRIDS=(7 9 11)
  SIM_MODELS=(tfim heisenberg)
  SIM_QUBITS=(4 5 6)
  SIM_STEPS=(4 6 8)
fi

if [[ -n "${QS_CHEM_HAMILTONIAN_FILES:-}" ]]; then
  IFS=',' read -ra CHEM_JSON_FILES <<< "${QS_CHEM_HAMILTONIAN_FILES}"
elif [[ "${SWEEP_PROFILE}" == "accept" ]]; then
  CHEM_JSON_FILES=(
    benchmarks/workloads/hamiltonians/h2_sto3g_4q.json
    benchmarks/workloads/hamiltonians/lih_sto3g_active_4q.json
    benchmarks/workloads/hamiltonians/h2o_sto3g_active_4q.json
    benchmarks/workloads/hamiltonians/molecular_chain_4q.json
  )
else
  CHEM_JSON_FILES=(benchmarks/workloads/hamiltonians/molecular_chain_4q.json)
fi

repeat_suffix() {
  local repeat="$1"
  if [[ "${SWEEP_PROFILE}" == "standard" && "${REPEAT_COUNT}" == "1" ]]; then
    echo ""
  else
    echo "_r${repeat}"
  fi
}

# Larger multiclass ML over the real sklearn digits dataset. Feature count is
# the PCA/qubit dimension used by the quantum feature circuit.
if family_enabled ml; then
  for repeat in $(seq 0 $((REPEAT_COUNT - 1))); do
  suffix="$(repeat_suffix "${repeat}")"
  for seed in "${SEEDS[@]}"; do
    run_seed=$((seed + repeat * 1000))
    for classes in "${ML_CLASSES[@]}"; do
      class_count=$(awk -F, '{print NF}' <<< "${classes}")
      class_tag="${classes//,/v}"
      for samples in "${ML_SAMPLES[@]}"; do
      for features in "${ML_FEATURES[@]}"; do
        for depth in "${ML_DEPTHS[@]}"; do
          maybe_run_case "${case_id}" \
            "ml_digits_c${class_tag}_${samples}s_${features}q_d${depth}${suffix}_seed${run_seed}" \
            --workloads ml \
            --seed "${run_seed}" \
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
  done
fi

# VQE-style chemistry. Grid size controls optimizer/search work. The built-in
# H2 case is a quality anchor; the 4-qubit fixture checks the generic Pauli
# Hamiltonian path that can receive OpenFermion/PySCF-generated inputs.
if family_enabled chemistry; then
  for repeat in $(seq 0 $((REPEAT_COUNT - 1))); do
  suffix="$(repeat_suffix "${repeat}")"
  for seed in "${SEEDS[@]}"; do
    run_seed=$((seed + repeat * 1000))
    for layer in "${CHEM_LAYERS[@]}"; do
      for grid in "${CHEM_H2_GRIDS[@]}"; do
        maybe_run_case "${case_id}" \
          "chem_h2_l${layer}_grid${grid}${suffix}_seed${run_seed}" \
          --workloads chemistry \
          --seed "${run_seed}" \
          --chem-grid "${grid}" \
          --chem-layers "${layer}"
        case_id=$((case_id + 1))
      done
      for json_file in "${CHEM_JSON_FILES[@]}"; do
      json_base="$(basename "${json_file}" .json)"
      for grid in "${CHEM_JSON_GRIDS[@]}"; do
        maybe_run_case "${case_id}" \
          "chem_${json_base}_l${layer}_grid${grid}${suffix}_seed${run_seed}" \
          --workloads chemistry \
          --seed "${run_seed}" \
          --chem-grid "${grid}" \
          --chem-layers "${layer}" \
          --chem-hamiltonian-json "${json_file}"
        case_id=$((case_id + 1))
      done
      done
    done
  done
  done
fi

# QAOA-style optimization over small MaxCut graph families.
if family_enabled optimization; then
  for repeat in $(seq 0 $((REPEAT_COUNT - 1))); do
  suffix="$(repeat_suffix "${repeat}")"
  for seed in "${SEEDS[@]}"; do
    run_seed=$((seed + repeat * 1000))
    for nodes in "${OPT_NODES[@]}"; do
      for graph in "${OPT_GRAPHS[@]}"; do
      for grid in "${OPT_GRIDS[@]}"; do
        maybe_run_case "${case_id}" \
          "qaoa_${graph}_${nodes}n_grid${grid}${suffix}_seed${run_seed}" \
          --workloads optimization \
          --seed "${run_seed}" \
          --opt-nodes "${nodes}" \
          --opt-graph "${graph}" \
          --opt-grid "${grid}"
        case_id=$((case_id + 1))
      done
      done
    done
  done
  done
fi

# Hamiltonian simulation. Qubit count, physical model, and Trotter steps control
# circuit size.
if family_enabled simulation; then
  for repeat in $(seq 0 $((REPEAT_COUNT - 1))); do
  suffix="$(repeat_suffix "${repeat}")"
  for seed in "${SEEDS[@]}"; do
    run_seed=$((seed + repeat * 1000))
    for model in "${SIM_MODELS[@]}"; do
    for qubits in "${SIM_QUBITS[@]}"; do
      for steps in "${SIM_STEPS[@]}"; do
        maybe_run_case "${case_id}" \
          "sim_${model}_${qubits}q_${steps}steps${suffix}_seed${run_seed}" \
          --workloads simulation \
          --seed "${run_seed}" \
          --sim-model "${model}" \
          --sim-qubits "${qubits}" \
          --sim-steps "${steps}" \
          --sim-time 0.8
        case_id=$((case_id + 1))
      done
    done
    done
  done
  done
fi

echo "total_case_templates=${case_id}"

if [[ "${QS_PREFLIGHT_ONLY:-0}" == "1" ]]; then
  echo "preflight_complete=${JOB_ID}"
  echo "date_end=$(date --iso-8601=seconds)"
  exit 0
fi

"${PY}" benchmarks/workloads/summarize_practical_results.py \
  "${OUTDIR}/practical_${JOB_ID}_*.json" \
  --summary-json "${SUMMARY_DIR}/practical_suite_${JOB_ID}_summary.json" \
  --csv "${SUMMARY_DIR}/practical_suite_${JOB_ID}_summary.csv" || \
  echo "summary_empty_or_failed=${JOB_ID}"

echo "date_end=$(date --iso-8601=seconds)"
