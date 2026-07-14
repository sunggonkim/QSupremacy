#!/bin/bash
#SBATCH -A m5320
#SBATCH -C gpu
#SBATCH -q shared
#SBATCH -t 00:15:00
#SBATCH -n 1
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-digits-1g
#SBATCH -o logs/qsup-digits-1g-%j.out
#SBATCH -e logs/qsup-digits-1g-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-32}"

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/digits_shared
DATASET=data/datasets/sklearn_digits.npz
mkdir -p "${OUTDIR}" logs

echo "job_id=${SLURM_JOB_ID}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L

if [[ ! -f "${DATASET}" ]]; then
  echo "Missing ${DATASET}; materialize it on a login node before submitting."
  exit 2
fi

run_case() {
  local samples="$1"
  local pca="$2"
  local depth="$3"
  local iters="$4"
  local seed="$5"
  local tag="${samples}s_${pca}p_d${depth}_i${iters}_seed${seed}"
  echo "case_start=${tag} $(date --iso-8601=seconds)"
  "${PY}" benchmarks/digits/run_digits_supremacy.py \
    --dataset "${DATASET}" \
    --classes 0,1 \
    --max-samples "${samples}" \
    --pca-dim "${pca}" \
    --feature-depth "${depth}" \
    --entangle \
    --phase \
    --native-steps 600 \
    --mlp-steps 600 \
    --vqc-iterations "${iters}" \
    --vqc-head-steps 20 \
    --seed "${seed}" \
    --output "${OUTDIR}/digits_${SLURM_JOB_ID}_${tag}.json" >/dev/null
  echo "case_end=${tag} $(date --iso-8601=seconds)"
}

for seed in 11 13; do
  run_case 64 4 1 3 "${seed}"
  run_case 96 4 1 3 "${seed}"
  run_case 128 4 1 3 "${seed}"
  run_case 96 4 2 3 "${seed}"
  run_case 128 4 2 3 "${seed}"
  run_case 64 8 1 3 "${seed}"
  run_case 96 8 1 3 "${seed}"
  run_case 128 8 1 2 "${seed}"
done

run_case 64 12 1 2 11
run_case 96 12 1 2 11

"${PY}" benchmarks/digits/summarize_digits_results.py \
  "${OUTDIR}/digits_${SLURM_JOB_ID}_*.json"

echo "date_end=$(date --iso-8601=seconds)"
