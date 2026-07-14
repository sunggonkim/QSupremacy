#!/bin/bash
#SBATCH --job-name=qsup-cifar-qf
#SBATCH --account=m5320
#SBATCH --qos=shared
#SBATCH --constraint=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gpus-per-task=1
#SBATCH --time=01:30:00
#SBATCH --output=logs/qsup-cifar-qf-%j.out
#SBATCH --error=logs/qsup-cifar-qf-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
source /etc/profile.d/zzz-lmod.sh
module load cudatoolkit/12.9
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export CUPY_CACHE_DIR="${PSCRATCH}/qsup_cupy_cache_${SLURM_JOB_ID}"
PY=/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python
TRAIN_LIMIT=${QS_TRAIN_LIMIT:-0}
TEST_LIMIT=${QS_TEST_LIMIT:-0}
OUTPUT_TAG=${QS_OUTPUT_TAG:-full}

srun "${PY}" scripts/run_ml_cifar10_cuquantum_feature_proxy.py \
    --dataset-root /pscratch/sd/s/sgkim/qsup_datasets/cifar10 \
    --train-limit "${TRAIN_LIMIT}" \
    --test-limit "${TEST_LIMIT}" \
    --layers 3 \
    --seed 17 \
    --checkpoint-prefix "data/raw/perlmutter/ml_cifar10_cuquantum_feature_${OUTPUT_TAG}" \
    --output "data/processed/perlmutter/ml_cifar10_cuquantum_feature_${OUTPUT_TAG}_${SLURM_JOB_ID}.json"
