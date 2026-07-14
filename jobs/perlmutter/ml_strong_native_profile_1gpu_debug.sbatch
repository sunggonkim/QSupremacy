#!/bin/bash
#SBATCH -A m5320_g
#SBATCH -C gpu
#SBATCH -q debug
#SBATCH -t 00:30:00
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=16
#SBATCH -J ml_native_profile
#SBATCH -o data/raw/perlmutter/logs/%x_%j.out
#SBATCH -e data/raw/perlmutter/logs/%x_%j.err

set -euo pipefail

cd /pscratch/sd/s/sgkim/Skim-Qsupreme

PY="${PY:-.venv-mlnative/bin/python}"
NSYS="/opt/nvidia/hpc_sdk/Linux_x86_64/25.5/profilers/Nsight_Systems/bin/nsys"
NCU="/opt/nvidia/hpc_sdk/Linux_x86_64/25.5/profilers/Nsight_Compute/ncu"
TAG="ml_strong_native_${SLURM_JOB_ID:-manual}"
RAW_DIR="data/raw/perlmutter/ml_strong_native"
PROC_DIR="data/processed/perlmutter"
PROFILE_DIR="data/raw/perlmutter/profiles"

mkdir -p "${RAW_DIR}" "${PROC_DIR}" "${PROFILE_DIR}" data/raw/perlmutter/logs

"${PY}" benchmarks/workloads/run_ml_strong_native_gate.py \
  --max-cases "${MAX_CASES:-32}" \
  --amp \
  --torch-steps "${TORCH_STEPS:-80}" \
  --output "${RAW_DIR}/${TAG}.json" \
  --csv-output "${PROC_DIR}/${TAG}.csv"

cp "${RAW_DIR}/${TAG}.json" "${PROC_DIR}/ml_strong_native_gate_latest.json"
cp "${PROC_DIR}/${TAG}.csv" "${PROC_DIR}/ml_strong_native_gate_latest.csv"

"${NSYS}" profile \
  --force-overwrite=true \
  --trace=cuda,nvtx,osrt,cudnn,cublas \
  --stats=true \
  --output="${PROFILE_DIR}/${TAG}_nsys" \
  "${PY}" benchmarks/workloads/run_ml_strong_native_gate.py \
    --max-cases 1 \
    --models torch_cnn_amp,torch_mlp_amp \
    --amp \
    --torch-steps "${PROFILE_TORCH_STEPS:-40}" \
    --output "${RAW_DIR}/${TAG}_nsys_gate.json" \
    --csv-output "${PROC_DIR}/${TAG}_nsys_gate.csv" \
  > "${PROFILE_DIR}/${TAG}_nsys.stdout" 2> "${PROFILE_DIR}/${TAG}_nsys.stderr" || true

if [ -f "${PROFILE_DIR}/${TAG}_nsys.sqlite" ]; then
  "${NSYS}" stats --report cuda_gpu_kern_sum --format csv \
    --output "${PROFILE_DIR}/${TAG}_nsys_kernel" \
    "${PROFILE_DIR}/${TAG}_nsys.sqlite" || true
fi

"${NCU}" --set full --target-processes all --nvtx --csv \
  --launch-count "${NCU_LAUNCH_COUNT:-12}" \
  --log-file "${PROFILE_DIR}/${TAG}_ncu.csv" \
  "${PY}" benchmarks/workloads/run_ml_strong_native_gate.py \
    --max-cases 1 \
    --models torch_cnn_amp \
    --amp \
    --torch-steps "${PROFILE_TORCH_STEPS:-40}" \
    --output "${RAW_DIR}/${TAG}_ncu_gate.json" \
    --csv-output "${PROC_DIR}/${TAG}_ncu_gate.csv" \
  > "${PROFILE_DIR}/${TAG}_ncu.stdout" 2> "${PROFILE_DIR}/${TAG}_ncu.stderr" || true

(
  nvidia-smi dmon -s pucvmet -d 1 -c "${DMON_SAMPLES:-30}" \
    > "${PROFILE_DIR}/${TAG}_dmon.csv"
) &
DMON_PID=$!
"${PY}" benchmarks/workloads/run_ml_strong_native_gate.py \
  --max-cases "${DMON_CASES:-8}" \
  --models torch_cnn_amp,torch_mlp_amp,xgboost_gpu_hist \
  --amp \
  --torch-steps "${DMON_TORCH_STEPS:-40}" \
  --xgb-estimators "${DMON_XGB_ESTIMATORS:-32}" \
  --output "${RAW_DIR}/${TAG}_dmon_gate.json" \
  --csv-output "${PROC_DIR}/${TAG}_dmon_gate.csv" || true
wait "${DMON_PID}" || true

KERNEL_CSV="$(ls "${PROFILE_DIR}/${TAG}_nsys_kernel_cuda_gpu_kern_sum"*.csv 2>/dev/null | head -n 1 || true)"
"${PY}" scripts/summarize_ml_native_profiles.py \
  --gate-json "${RAW_DIR}/${TAG}.json" \
  --nsys-gate-json "${RAW_DIR}/${TAG}_nsys_gate.json" \
  --nsys-kernel-csv "${KERNEL_CSV}" \
  --ncu-csv "${PROFILE_DIR}/${TAG}_ncu.csv" \
  --dmon-csv "${PROFILE_DIR}/${TAG}_dmon.csv" \
  --output "${PROC_DIR}/ml_strong_native_profile_latest.json"
