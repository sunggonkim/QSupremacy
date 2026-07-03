#!/bin/bash
#SBATCH -A m1248
#SBATCH -C gpu
#SBATCH -q shared
#SBATCH -t 02:00:00
#SBATCH -n 1
#SBATCH -c 32
#SBATCH --gpus-per-task=1
#SBATCH -J qsup-digits-exp
#SBATCH -o logs/qsup-digits-exp-1g-%j.out
#SBATCH -e logs/qsup-digits-exp-1g-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

export SLURM_CPU_BIND="cores"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-32}"

PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
OUTDIR=data/raw/perlmutter/digits_expanded
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
  local classes="$1"
  local samples="$2"
  local pca="$3"
  local depth="$4"
  local iters="$5"
  local seed="$6"
  local cls_tag="${classes/,/v}"
  local tag="c${cls_tag}_${samples}s_${pca}p_d${depth}_i${iters}_seed${seed}"
  echo "case_start=${tag} $(date --iso-8601=seconds)"
  "${PY}" benchmarks/digits/run_digits_supremacy.py \
    --dataset "${DATASET}" \
    --classes "${classes}" \
    --max-samples "${samples}" \
    --pca-dim "${pca}" \
    --feature-depth "${depth}" \
    --entangle \
    --phase \
    --native-steps 800 \
    --mlp-steps 800 \
    --vqc-iterations "${iters}" \
    --vqc-head-steps 25 \
    --seed "${seed}" \
    --output "${OUTDIR}/digits_${SLURM_JOB_ID}_${tag}.json" >/dev/null
  echo "case_end=${tag} $(date --iso-8601=seconds)"
}

# Purposefully mix easy and harder binary digit pairs. 0-vs-1 is a sanity
# anchor; the other pairs are more useful for modeling quality/runtime tradeoffs.
for classes in 0,1 3,8 4,9 5,8; do
  for seed in 11 13; do
    for samples in 128 256; do
      for depth in 1 2 3; do
        run_case "${classes}" "${samples}" 4 "${depth}" 4 "${seed}"
        run_case "${classes}" "${samples}" 8 "${depth}" 4 "${seed}"
      done
      for depth in 1 2; do
        run_case "${classes}" "${samples}" 12 "${depth}" 3 "${seed}"
        run_case "${classes}" "${samples}" 16 "${depth}" 2 "${seed}"
      done
    done
  done
done

"${PY}" benchmarks/digits/summarize_digits_results.py \
  "${OUTDIR}/digits_${SLURM_JOB_ID}_*.json"

echo "date_end=$(date --iso-8601=seconds)"
