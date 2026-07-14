#!/bin/bash
#SBATCH --job-name=qsup-review-rem
#SBATCH --account=m1248
#SBATCH --qos=debug
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=00:30:00
#SBATCH --output=logs/qsup-review-rem-%j.out
#SBATCH --error=logs/qsup-review-rem-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export QISKIT_PARALLEL=true

srun .venv-mlnative/bin/python scripts/run_ml_cifar10_compact_control.py
srun .venv-qre/bin/python scripts/run_qaoa_depth_quality_closed_loop.py
