#!/bin/bash
#SBATCH --job-name=qsup-chem-pair
#SBATCH --account=m1248
#SBATCH --qos=debug
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=00:30:00
#SBATCH --output=logs/qsup-chem-pair-%j.out
#SBATCH --error=logs/qsup-chem-pair-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export QISKIT_PARALLEL=true

srun --cpu-bind=cores .venv-qre/bin/python \
  scripts/run_chem_active_space_closure.py \
  --output data/processed/perlmutter/chem_active_space_pair_ucc_closure.json
