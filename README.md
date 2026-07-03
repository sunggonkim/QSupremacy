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
- Practical workload suite added for multiclass ML, VQE-style chemistry,
  QAOA-style optimization, and Hamiltonian simulation.
- First `sklearn digits` shared-GPU sweep completed:
  job `55414571`, 18 cases, 221 seconds elapsed, about 0.061 GPU-hours.
- Expanded `sklearn digits` sweep completed:
  8 shared-GPU chunks, 160 cases, about 0.409 GPU-hours total.

## Login Smoke Gate

Run this before spending GPU allocation:

```bash
scripts/run_login_smoke.sh
```

The smoke suite checks:

- cuQuantum/CuPy/cuStateVec import
- small state-vector correctness
- application-level native ML vs quantum-circuit ML pipeline
- practical native-vs-quantum workloads for ML, chemistry, optimization, and simulation
- JSON output schema
- basic accuracy/runtime validation

Recent pass summary:

```text
PASS: login smoke outputs validated
```

## Practical Workload Suite

The practical suite is the next step beyond the digits calibration experiment.
It is still login-safe, but each case represents a real application family and
keeps native runtime, quantum-circuit runtime, quality, and break-even
projection together.

```bash
module load cudatoolkit/12.9
/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/workloads/run_practical_suite.py \
  --login-safe \
  --entangle \
  --output data/raw/perlmutter/login_suite/practical_suite_smoke.json
```

Current workload families:

- multiclass ML: native softmax regression vs quantum feature circuit + softmax head
- drug discovery / chemistry: exact H2 Hamiltonian diagonalization vs VQE-style circuit
- optimization: exact small MaxCut vs QAOA-style circuit
- scientific simulation: exact TFIM/Heisenberg dynamics vs Trotterized circuit

Chemistry Hamiltonians can be supplied as Pauli-term JSON:

```json
{
  "name": "my_molecule_active_space",
  "n_qubits": 4,
  "terms": [
    {"pauli": "IIII", "coefficient": -0.81},
    {"pauli": "ZIII", "coefficient": 0.18},
    {"pauli": "XXII", "coefficient": 0.045}
  ]
}
```

Example:

```bash
/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/workloads/run_practical_suite.py \
  --workloads chemistry \
  --chem-hamiltonian-json benchmarks/workloads/hamiltonians/molecular_chain_4q.json \
  --chem-grid 9 \
  --entangle
```

Validate the suite:

```bash
/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/smoke/validate_login_smoke.py \
  --practical data/raw/perlmutter/login_suite/practical_suite_smoke.json
```

Allocation-safe Perlmutter smoke job:

```bash
sbatch jobs/perlmutter/practical_suite_1gpu_shared.sbatch
```

Use this job before any larger practical workload sweep. It requests one shared
GPU for 15 minutes and verifies all four application families.

Chunked practical sweep:

```bash
for chunk in 0 1 2 3 4 5 6 7; do
  QS_CHUNK_ID=${chunk} QS_CHUNK_COUNT=8 \
    sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
done
```

The sweep currently expands to 190 case templates:

- ML: real `sklearn_digits` multiclass sets 0/1/2, 3/5/8, and 0/1/2/3;
  samples 128/192/256, PCA/qubits 4/6/8, depths 1/2, two seeds, native
  softmax and MLP baselines
- chemistry: H2 VQE grid sizes 17/21/25 plus a 4-qubit Pauli Hamiltonian
  fixture with grid sizes 9/13, two seeds. The runner also accepts external
  Pauli Hamiltonian JSON through `--chem-hamiltonian-json`.
- optimization: QAOA MaxCut with ring/chordal/ladder graph families, 4/5 nodes,
  grid sizes 7/9/11, two seeds
- simulation: TFIM and Heisenberg chains with 4/5/6 qubits and 4/6/8 Trotter
  steps, two seeds. The default `auto` initial state uses `|0...0>` for TFIM
  and a Neel-like basis state for Heisenberg.

Each chunk writes raw JSON to `data/raw/perlmutter/practical_suite_sweep/` and
summary JSON/CSV files to `data/processed/perlmutter/`. Combine any finished
chunks with:

```bash
/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/workloads/summarize_practical_results.py \
  'data/raw/perlmutter/practical_suite_sweep/practical_*.json' \
  --summary-json data/processed/perlmutter/practical_suite_combined_summary.json \
  --csv data/processed/perlmutter/practical_suite_combined_summary.csv
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

Expanded sweep:

```text
job_ids: 55421321, 55421323, 55422136, 55422137, 55422138, 55422139, 55422141, 55422142
cases: 160
class pairs: 0-vs-1, 3-vs-8, 4-vs-9, 5-vs-8
PCA/qubits: 4, 8, 12, 16
GPU-hours: 0.409
summary: data/processed/perlmutter/digits_expanded_55421321_55422142_summary.json
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
benchmarks/workloads/  Practical ML/chemistry/optimization/simulation suite
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
