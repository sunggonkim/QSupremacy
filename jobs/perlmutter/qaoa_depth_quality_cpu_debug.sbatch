#!/bin/bash
#SBATCH --job-name=qsup-qaoa-depth
#SBATCH --account=m1248
#SBATCH --qos=debug
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=00:30:00
#SBATCH --output=logs/qsup-qaoa-depth-%j.out
#SBATCH --error=logs/qsup-qaoa-depth-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export QISKIT_PARALLEL=true

srun .venv-qre/bin/python scripts/run_qaoa_depth_quality_closed_loop.py
