#!/bin/bash
#SBATCH --job-name=qsup-chem-compile
#SBATCH --account=m1248
#SBATCH --qos=debug
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=00:30:00
#SBATCH --output=logs/qsup-chem-compile-%j.out
#SBATCH --error=logs/qsup-chem-compile-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"

srun .venv-qre/bin/python scripts/compile_chemistry_measurement_records.py
