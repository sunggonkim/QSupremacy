#!/bin/bash
#SBATCH -A m1248
#SBATCH -C gpu
#SBATCH -q debug
#SBATCH -t 00:30:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -c 128
#SBATCH --gpus-per-node=4
#SBATCH -J qsup-digits-4g
#SBATCH -o logs/qsup-digits-exp-4g-%j.out
#SBATCH -e logs/qsup-digits-exp-4g-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

module load cudatoolkit/12.9

mkdir -p logs data/raw/perlmutter/digits_expanded

echo "job_id=${SLURM_JOB_ID}"
echo "host=$(hostname)"
echo "date_start=$(date --iso-8601=seconds)"
echo "cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-unset}"
nvidia-smi -L

run_chunk_on_gpu() {
  local gpu="$1"
  shift
  local chunks=("$@")
  for chunk in "${chunks[@]}"; do
    echo "worker_start gpu=${gpu} chunk=${chunk} $(date --iso-8601=seconds)"
    CUDA_VISIBLE_DEVICES="${gpu}" \
    QS_CHUNK_ID="${chunk}" \
    QS_CHUNK_COUNT=8 \
    SLURM_CPUS_PER_TASK=32 \
      bash jobs/perlmutter/digits_supremacy_expanded_1gpu_shared.sbatch \
      > "logs/qsup-digits-exp-4g-${SLURM_JOB_ID}-gpu${gpu}-chunk${chunk}.out" \
      2> "logs/qsup-digits-exp-4g-${SLURM_JOB_ID}-gpu${gpu}-chunk${chunk}.err"
    echo "worker_end gpu=${gpu} chunk=${chunk} $(date --iso-8601=seconds)"
  done
}

# Chunks 0 and 1 already completed in shared-GPU jobs 55421321 and 55421323.
# This debug job runs the remaining 120 cases as six chunks over four GPUs.
run_chunk_on_gpu 0 2 6 &
pid0=$!
run_chunk_on_gpu 1 3 7 &
pid1=$!
run_chunk_on_gpu 2 4 &
pid2=$!
run_chunk_on_gpu 3 5 &
pid3=$!

wait "${pid0}" "${pid1}" "${pid2}" "${pid3}"

/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/digits/summarize_digits_results.py \
  "data/raw/perlmutter/digits_expanded/digits_${SLURM_JOB_ID}_*.json"

echo "date_end=$(date --iso-8601=seconds)"
