#!/bin/bash
#SBATCH --job-name=qsup-review-close
#SBATCH --account=m1248
#SBATCH --qos=debug
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=00:30:00
#SBATCH --output=logs/qsup-review-close-%j.out
#SBATCH --error=logs/qsup-review-close-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export QISKIT_PARALLEL=true

srun .venv-qre/bin/python scripts/compile_chemistry_measurement_records.py
srun .venv-mlnative/bin/python scripts/run_ml_cifar10_compact_control.py
srun .venv-qre/bin/python scripts/run_qaoa_depth_quality_closed_loop.py
