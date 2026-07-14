#!/bin/bash
#SBATCH --job-name=qsup-qaoa-close
#SBATCH --account=m1248
#SBATCH --qos=debug
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=00:30:00
#SBATCH --output=logs/qsup-qaoa-close-%j.out
#SBATCH --error=logs/qsup-qaoa-close-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

srun --cpu-bind=cores .venv-qre/bin/python \
  scripts/run_qaoa_scale_depth_closure.py --workers 4
