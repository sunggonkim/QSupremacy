#!/bin/bash
#SBATCH --job-name=qsup-qaoa-noise
#SBATCH --account=m1248
#SBATCH --qos=debug
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=00:30:00
#SBATCH --output=logs/qsup-qaoa-noise-%j.out
#SBATCH --error=logs/qsup-qaoa-noise-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export QISKIT_PARALLEL=true

srun .venv-qre/bin/python scripts/run_qaoa_noisy_closed_loop.py
