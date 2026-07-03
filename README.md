# QSupremacy

QSupremacy is a quantum supremacy modeling and analysis project. It models when quantum-circuit applications can outperform native HPC/ML applications on Perlmutter.

The core comparison is not simulator vs simulator. The comparison is:

- native application path: classical ML/HPC model executed directly on CPU/GPU
- quantum application path: the same application converted into a quantum-circuit model, simulated with cuQuantum, then projected to future quantum hardware

## Current Status

- Perlmutter environment identified.
- Existing cuQuantum environment found:
  `/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python`
- cuQuantum version: `26.01.0`
- CuPy version: `13.6.0`
- cuStateVec binding path: `cuquantum.bindings.custatevec`
- Login-node smoke suite passes.
- Perlmutter GPU Slurm smoke jobs completed successfully.
- First `sklearn digits` shared-GPU sweep completed:
  job `55414571`, 18 cases, 221 seconds elapsed, about 0.061 GPU-hours.

## Login Smoke Gate

Run this before spending GPU allocation:

```bash
scripts/run_login_smoke.sh
```

The smoke suite checks:

- cuQuantum/CuPy/cuStateVec import
- small state-vector correctness
- application-level native ML vs quantum-circuit ML pipeline
- JSON output schema
- basic accuracy/runtime validation

Recent pass summary:

```text
PASS: login smoke outputs validated
```

## Digits Supremacy Benchmark

The first non-toy workload uses the bundled `sklearn digits` dataset. The GPU
runner itself uses the existing cuQuantum environment, so materialize the digits
NPZ once before submitting Slurm jobs:

```bash
module load python/3.11-24.1.0
python scripts/materialize_sklearn_digits.py
```

Allocation-safe launch order:

```bash
module load cudatoolkit/12.9
/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/digits/run_digits_supremacy.py \
  --dataset data/datasets/sklearn_digits.npz \
  --classes 0,1 \
  --max-samples 32 \
  --pca-dim 4 \
  --feature-depth 1 \
  --entangle \
  --phase \
  --vqc-iterations 1 \
  --login-safe

sbatch jobs/perlmutter/digits_supremacy_1gpu_shared.sbatch
```

The shared-GPU job runs native ML, quantum kernel, and QNN/VQC paths over a
small sweep. Do not use the full GPU-node script for this workload until the
code can use all requested GPUs.

Recent shared-GPU result:

```text
job_id: 55414571
state: COMPLETED
elapsed: 00:03:41
queue: 00:02:08
results: data/raw/perlmutter/digits_shared/digits_55414571_*.json
summary: data/processed/perlmutter/digits_55414571_summary.json
```

## First Full Workloads

The first real experiment suite should run all three tracks:

1. sklearn digits native ML baseline
   - logistic regression
   - MLP
   - optional SVM/RBF baseline

2. Quantum kernel classifier
   - digits features reduced with PCA
   - quantum feature map simulated with cuQuantum
   - kernel matrix construction and classical classifier head

3. QNN/VQC classifier
   - same train/test split and feature preprocessing
   - parameterized quantum circuit simulated with cuQuantum
   - classical optimizer loop with runtime and accuracy logging

All tracks must report time-to-quality under the same dataset split and target accuracy/loss policy.

## Repository Layout

```text
benchmarks/digits/     sklearn digits native/kernel/QNN benchmark
benchmarks/smoke/      Login-node-safe correctness and application smoke tests
data/raw/perlmutter/   Small smoke outputs and Perlmutter job outputs
jobs/perlmutter/       Slurm job scripts
logs/                  Small Slurm smoke logs
paper/                 ATC-style paper scaffold
scripts/               Helper scripts
plan.md                Research and execution plan
```

## Perlmutter Rule

Do not submit full GPU-node jobs unless the workload can use all requested GPUs or the job is explicitly a one-time sanity check.

Use the login smoke gate first, then shared 1-GPU jobs, then full-node or multi-node sweeps only after batching and multi-GPU partitioning are ready.

## Paper Draft

The ATC-style quantum supremacy modeling and analysis paper scaffold is in `paper/`.

```bash
cd paper
make
```

The current draft is not submission-ready. It contains the thesis, modeling method, workload matrix, analysis plan, and result placeholders. The first full evaluation must complete all three tracks: `sklearn digits` native ML, quantum kernel classification, and QNN/VQC classification.
