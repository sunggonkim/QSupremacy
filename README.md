# QSupremacy

QSupremacy models when quantum-circuit applications can outperform native HPC/ML applications on Perlmutter.

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
benchmarks/smoke/      Login-node-safe correctness and application smoke tests
data/raw/perlmutter/   Small smoke outputs and Perlmutter job outputs
jobs/perlmutter/       Slurm job scripts
logs/                  Small Slurm smoke logs
scripts/               Helper scripts
plan.md                Research and execution plan
```

## Perlmutter Rule

Do not submit full GPU-node jobs unless the workload can use all requested GPUs or the job is explicitly a one-time sanity check.

Use the login smoke gate first, then shared 1-GPU jobs, then full-node or multi-node sweeps only after batching and multi-GPU partitioning are ready.
