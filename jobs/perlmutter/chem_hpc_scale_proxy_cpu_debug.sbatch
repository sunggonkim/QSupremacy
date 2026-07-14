#!/bin/bash
#SBATCH --job-name=qsup-chem-hpc
#SBATCH --account=m1248
#SBATCH --qos=debug
#SBATCH --constraint=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=00:30:00
#SBATCH --output=logs/qsup-chem-hpc-%j.out
#SBATCH --error=logs/qsup-chem-hpc-%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK}"

for case_id in n2_ccpvtz h2o_augccpvtz; do
    srun --nodes=1 --ntasks=1 --cpus-per-task="${SLURM_CPUS_PER_TASK}" \
        .venv-chemproxy/bin/python scripts/run_chem_hpc_scale_proxy.py \
        --case "${case_id}" \
        --threads "${SLURM_CPUS_PER_TASK}" \
        --output "data/processed/perlmutter/chem_hpc_scale_${case_id}_${SLURM_JOB_ID}.json"
done
