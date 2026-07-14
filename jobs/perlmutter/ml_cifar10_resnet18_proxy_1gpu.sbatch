#!/bin/bash
#SBATCH -A m5320_g
#SBATCH -C gpu
#SBATCH -q shared
#SBATCH -t 00:30:00
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=32
#SBATCH -J qsup-mlproxy
#SBATCH -o logs/qsup-mlproxy-%j.out
#SBATCH -e logs/qsup-mlproxy-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
mkdir -p logs data/processed/perlmutter data/raw/perlmutter/accounting
source /etc/profile.d/zzz-lmod.sh
module load pytorch/2.11.0

python scripts/run_ml_deployment_proxy.py \
  --data /pscratch/sd/s/sgkim/qsup_datasets/cifar10 \
  --epochs "${QS_ML_EPOCHS:-10}" \
  --batch-size "${QS_ML_BATCH:-512}" \
  --workers "${QS_ML_WORKERS:-16}" \
  --output data/processed/perlmutter/ml_cifar10_resnet18_proxy.json

sacct -j "${SLURM_JOB_ID}" \
  --format=JobID,JobName,State,ExitCode,Elapsed,AllocNodes,AllocTRES,Submit,Start,End \
  -P > "data/raw/perlmutter/accounting/sacct_ml_cifar10_resnet18_proxy_${SLURM_JOB_ID}.txt" || true
