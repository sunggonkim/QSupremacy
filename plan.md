# QSupremacy Research and Execution Plan

Last updated: 2026-07-03

## 0. One-Sentence Thesis

This project does **not** try to prove that quantum computers beat HPC today.
It models, with real Perlmutter measurements, **how fast quantum hardware must become** for quantum-circuit applications to beat strong native HPC/ML baselines at the same output quality.

The central comparison is:

```text
native application on HPC
vs.
same application expressed as a quantum-circuit workflow,
simulated with cuQuantum/qsim-style HPC simulation,
then projected to future quantum hardware
```

This is intentionally **not**:

```text
NumPy simulator vs cuQuantum simulator
```

Simulator-vs-simulator tests are only smoke tests for correctness and environment validation.

## 1. Scope

People often say, vaguely, that quantum computers will solve practical problems better than classical machines. This paper makes that claim measurable.

The paper focuses on application families where practical quantum advantage is commonly claimed:

| Family | Practical Claim | Native HPC Baseline | Quantum-Circuit Path | Quality Target |
| --- | --- | --- | --- | --- |
| ML / AI | Quantum ML can beat classical ML | Logistic/softmax, MLP, classical kernel/head | Quantum feature map, quantum kernel, QNN/VQC | Accuracy/loss |
| Chemistry / Drug Discovery | VQE can help molecular energy estimation | Exact diagonalization or chemistry/surrogate baseline | VQE-style Pauli Hamiltonian circuit | Ground-state energy error |
| Optimization | QAOA can solve graph/portfolio/scheduling better | Exact/heuristic MaxCut solver | QAOA-style circuit | Approximation ratio/objective |
| Scientific Simulation | Hamiltonian simulation is a natural quantum workload | Dense exact dynamics / numerical solver | Trotterized TFIM/Heisenberg circuit | Observable error |

Out of scope for this paper:

- Quantum cryptography, communication, sensing, and device physics as standalone fields.
- Claims that do not map to `native application vs quantum-circuit application`.
- Pure simulator speed comparisons as final evidence.

## 2. Core Research Questions

1. For each practical workload, what is the measured time-to-quality of the native HPC path?
2. For the same workload, what is the measured time-to-quality of the quantum-circuit path when simulated with cuQuantum on Perlmutter?
3. Given the measured circuit metadata, how much faster must future quantum hardware execution be to match or beat the native path?
4. Which overhead dominates the quantum path: data encoding, circuit construction, circuit execution, measurements/observables, optimizer loops, or classical postprocessing?
5. How sensitive is the break-even point to qubit count, depth, shots, optimizer iterations, error mitigation/correction overhead, and native HPC improvement?
6. Which practical workloads are structurally plausible for future advantage, and which are blocked by encoding or quality loss?

## 3. Current Evidence

### 3.1 Completed Measured Results

The first full measured workload is the expanded `sklearn digits` binary classification suite.

Artifacts:

- Raw results: `data/raw/perlmutter/digits_expanded/`
- Summary JSON: `data/processed/perlmutter/digits_expanded_55421321_55422142_summary.json`
- Summary CSV: `data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv`
- Accounting: `data/raw/perlmutter/accounting/sacct_digits_expanded_55421321_55422142.txt`

Measured scope:

- 160 cases
- Class pairs: `0-vs-1`, `3-vs-8`, `4-vs-9`, `5-vs-8`
- Samples: `128`, `256`
- PCA/qubits: `4`, `8`, `12`, `16`
- Quantum models: quantum kernel, QNN/VQC
- Native models: logistic regression, MLP
- Completed as eight shared-GPU chunks

Key measured results:

| Metric | Result |
| --- | --- |
| Total GPU-hours | `0.4089` |
| Slurm billed core-hours | `13.0844` |
| Quantum kernel required speedup | min `338.6x`, median `421.9x`, max `1038.7x` |
| QNN/VQC required speedup | min `21.1x`, median `64.9x`, max `171.7x` |
| Quantum kernel accuracy | min `0.5312`, median `0.8750`, max `1.0000` |
| QNN/VQC accuracy | min `0.4688`, median `0.7500`, max `0.9531` |

Interpretation:

- This does **not** show quantum advantage today.
- It shows how to convert an application comparison into a hardware threshold.
- The QNN/VQC path needs less speedup than quantum kernels but often misses native quality.
- Quality must be part of the advantage definition; runtime alone is not enough.

### 3.2 Implemented Practical Suite

The practical suite is implemented but the full Perlmutter sweep has not completed yet.

Code:

- Runner: `benchmarks/workloads/run_practical_suite.py`
- Summarizer: `benchmarks/workloads/summarize_practical_results.py`
- Hamiltonian fixture: `benchmarks/workloads/hamiltonians/molecular_chain_4q.json`
- Smoke job: `jobs/perlmutter/practical_suite_1gpu_shared.sbatch`
- Sweep job: `jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch`

Current practical sweep size:

```text
190 case templates
```

Breakdown:

| Family | Cases |
| --- | ---: |
| Real multiclass digits ML | 108 |
| VQE-style chemistry | 10 |
| QAOA optimization | 36 |
| Hamiltonian/scientific simulation | 36 |
| Total | 190 |

Practical suite dimensions:

- ML:
  - Dataset: real `sklearn_digits`
  - Classes: `0,1,2`, `3,5,8`, `0,1,2,3`
  - Samples: `128`, `192`, `256`
  - PCA/qubits: `4`, `6`, `8`
  - Circuit depths: `1`, `2`
  - Seeds: `17`, `23`
  - Native baselines: softmax regression, MLP

- Chemistry:
  - Built-in H2 Hamiltonian as quality anchor
  - Generic Pauli Hamiltonian JSON input path
  - 4-qubit molecular-chain surrogate fixture
  - VQE-style hardware-efficient ansatz
  - Native baseline: exact diagonalization

- Optimization:
  - MaxCut
  - Graph families: `ring`, `chordal`, `ladder`
  - Nodes: `4`, `5`
  - QAOA grid sizes: `7`, `9`, `11`
  - Native baseline: exact enumeration

- Scientific simulation:
  - Models: `tfim`, `heisenberg`
  - Qubits: `4`, `5`, `6`
  - Trotter steps: `4`, `6`, `8`
  - Native baseline: dense exact dynamics
  - Quantum path: first-order Trotter circuit

### 3.3 Current Pilot Status

One allocation-safe pilot job has been submitted:

```bash
QS_CHUNK_ID=0 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
```

Pilot job:

```text
job_id: 55432715
state: COMPLETED
exit: 0:0
elapsed: 00:01:44
stderr: 0 bytes
cases: 12
```

Pilot result artifacts:

```text
logs/qsup-prac-sweep-1g-55432715.out
logs/qsup-prac-sweep-1g-55432715.err
data/raw/perlmutter/practical_suite_sweep/practical_55432715_*.json
data/processed/perlmutter/practical_suite_55432715_summary.json
data/processed/perlmutter/practical_suite_55432715_summary.csv
data/raw/perlmutter/accounting/sacct_practical_pilot_55432715.txt
```

Remaining chunks are submitted as two bundled jobs, not 15 separate jobs:

```text
job_id: 55452410, chunks 1-8, state PENDING at submission check
job_id: 55452411, chunks 9-15, state PENDING at submission check
```

## 4. Definitions

### 4.1 End-to-End Runtime

Native path:

```text
T_native =
  T_input
+ T_preprocess
+ T_native_model_or_solver
+ T_native_eval
+ T_postprocess
+ T_io
```

Quantum-circuit path on cuQuantum:

```text
T_quantum_sim =
  T_input
+ T_preprocess
+ T_encoding
+ T_circuit_construction
+ T_cuquantum_execution
+ T_measurement_or_observable
+ T_classical_head_or_optimizer
+ T_postprocess
+ T_io
```

Projected future quantum hardware path:

```text
T_quantum_hw =
  T_input
+ T_preprocess
+ T_encoding
+ T_circuit_compile
+ T_hardware_execution
+ T_measurement
+ T_error_mitigation_or_correction
+ T_classical_postprocess
```

Queue time is recorded separately. The paper should report both:

- compute-only time
- allocation/user-visible time including queue/scheduler effects

### 4.2 Quality Gate

Quantum advantage is invalid if quality is worse and the loss is not reported.

Each workload must define a quality gate:

| Workload | Quality Metric |
| --- | --- |
| ML | test accuracy / loss |
| Chemistry | absolute ground-energy error |
| Optimization | approximation ratio / objective gap |
| Simulation | absolute observable error |

Runtime comparisons must be time-to-quality, not raw time alone.

### 4.3 Break-Even Projection

The first-level projection is the measured simulator-to-native threshold:

```text
required_speedup = T_quantum_sim / T_native
```

The next-level hardware projection uses circuit metadata:

```text
T_hardware_execute =
  N_shots * (N_1q * t_1q + N_2q * t_2q + N_meas * t_meas)
  / parallel_shot_factor
```

Break-even condition:

```text
T_quantum_hw <= T_native
```

The paper should report threshold heatmaps over:

- logical 1Q/2Q gate time
- measurement time
- shot count
- shot parallelism
- error mitigation/correction overhead
- native HPC improvement factor

## 5. Experimental Runbook

### 5.1 Login Smoke Gate

Always run this before spending allocation:

```bash
scripts/run_login_smoke.sh
```

This validates:

- cuQuantum/CuPy/cuStateVec imports
- state-vector correctness
- application-level ML vs quantum-circuit ML smoke
- practical suite smoke for ML, chemistry, optimization, simulation
- JSON schema and basic quality checks

Expected output:

```text
PASS: login smoke outputs validated
```

### 5.2 Practical Pilot

The current pilot command is:

```bash
QS_CHUNK_ID=0 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
```

Current job:

```text
55432715
```

Monitor:

```bash
squeue -j 55432715 -o '%i %j %T %M %l %R'
sacct -j 55432715 --format=JobID,State,ExitCode,Elapsed,AllocTRES -P
```

Expected output files after completion:

```text
logs/qsup-prac-sweep-1g-55432715.out
logs/qsup-prac-sweep-1g-55432715.err
data/raw/perlmutter/practical_suite_sweep/practical_55432715_*.json
data/processed/perlmutter/practical_suite_55432715_summary.json
data/processed/perlmutter/practical_suite_55432715_summary.csv
```

Pilot pass criteria:

- Slurm state is `COMPLETED`
- Exit code is `0:0`
- stderr is empty or only harmless warnings
- summary JSON exists
- summary reports all cases assigned to chunk `0/16`
- no individual workload JSON has `status != ok`
- elapsed time is comfortably under `00:30:00`

If the pilot fails:

1. Do not submit remaining chunks.
2. Inspect stderr and the last `case_start`.
3. Fix code or split into more chunks.
4. Re-run login smoke.
5. Submit one pilot again.

### 5.3 Submit Remaining Practical Chunks

Only after the pilot passes:

```bash
QS_CHUNK_IDS=1,2,3,4,5,6,7,8 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch

QS_CHUNK_IDS=9,10,11,12,13,14,15 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
```

Monitor all practical jobs:

```bash
squeue -u "$USER" -o '%i %j %T %M %l %R' | grep qsup-prac
```

After all chunks complete, combine summaries:

```bash
/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/workloads/summarize_practical_results.py \
  'data/raw/perlmutter/practical_suite_sweep/practical_*.json' \
  --summary-json data/processed/perlmutter/practical_suite_combined_summary.json \
  --csv data/processed/perlmutter/practical_suite_combined_summary.csv
```

Collect accounting:

```bash
sacct -j <jobid_list> \
  --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,AllocTRES%80 \
  -P > data/raw/perlmutter/accounting/sacct_practical_suite_<job_range>.txt
```

## 6. Paper Plan

The target paper is an ATC-style systems paper:

```text
Quantum Supremacy Modeling and Analysis:
How Fast Must Quantum Hardware Be to Beat Native HPC?
```

### Abstract

Must say:

- Practical quantum advantage claims are vague.
- We compare native application paths against quantum-circuit application paths.
- cuQuantum is used as an HPC-based measurement tool, not as the final competitor.
- Output is a hardware threshold, not a claim of current quantum advantage.
- First measured result: digits suite.
- Full practical suite: ML, chemistry, optimization, simulation.

### Introduction

Flow:

1. People claim quantum computers will solve real applications.
2. But practical advantage depends on workload, quality, data encoding, shots, and native HPC.
3. Simulator-vs-simulator results do not answer this.
4. We propose a threshold-modeling method.
5. We evaluate with Perlmutter and cuQuantum.
6. Contributions:
   - application-level comparison framework
   - Perlmutter measured digits result
   - practical workload suite
   - hardware break-even model

### Design

Must include:

- workload control
- native and quantum path decomposition
- quality gate
- circuit metadata extraction
- break-even projection
- Slurm/accounting policy

### Evaluation

Current evaluation sections:

1. Setup: Perlmutter, cuQuantum, shared GPU jobs
2. Completed digits result
3. Practical suite pilot and full sweep
4. Quality sensitivity
5. Runtime breakdown
6. Allocation and cost
7. Hardware projection heatmaps

Until practical sweep finishes, label those results as planned or pending.

## 7. Risks and Mitigations

| Risk | Why It Matters | Mitigation |
| --- | --- | --- |
| Quantum path has lower quality | Runtime-only claims become invalid | Always report quality gap and time-to-quality |
| Data encoding dominates | Advantage disappears | Measure encoding separately |
| Tiny workloads exaggerate Python overhead | Misleading threshold | Use login smoke only for validation; use GPU sweeps for results |
| Native baseline too weak | Artificial quantum advantage | Include multiple native baselines: softmax, MLP, exact solvers |
| Full-node allocation waste | Perlmutter time wasted | Use shared 1-GPU chunks first |
| Practical sweep exceeds walltime | Lost jobs and partial data | Pilot chunk first; increase chunk count if needed |
| Queue time distorts compute model | Scheduler effects hide compute behavior | Report compute time and allocation/accounting separately |
| Chemistry fixture is not production molecule | Weak drug-discovery claim | Use fixture for pipeline; add OpenFermion/PySCF-generated Hamiltonians later |

## 8. Immediate Next Actions

Current active state:

```text
Pilot job 55432715 completed successfully.
Remaining bundled jobs 55452410 and 55452411 are pending due to scheduler priority.
```

Next actions:

1. Wait for bundled jobs `55452410` and `55452411` to start and complete.
2. Check:

   ```bash
   squeue -j 55452410,55452411 -o '%i %j %T %M %l %R'
   sacct -j 55452410,55452411 --format=JobID,State,ExitCode,Elapsed,AllocTRES -P
   ```

3. If completed, inspect:

   ```bash
   ls -lh logs/qsup-prac-sweep-1g-55452410.*
   ls -lh logs/qsup-prac-sweep-1g-55452411.*
   ls -lh data/raw/perlmutter/practical_suite_sweep/practical_55452410_*.json
   ls -lh data/raw/perlmutter/practical_suite_sweep/practical_55452411_*.json
   ```

4. Combine pilot and bundle results.
5. Save Slurm accounting for all practical jobs.
6. Update `paper/4.Evaluation.tex` with practical suite measurements.
7. Commit raw summaries, accounting, and paper update.

## 9. Completion Criteria

The project is not complete until all of the following are true:

- Login smoke passes.
- Digits expanded result is measured and summarized.
- Practical suite pilot completes successfully.
- Practical suite full 190-case sweep completes or is intentionally reduced with a documented reason.
- Combined practical summary JSON/CSV exists.
- Slurm accounting is saved.
- Paper evaluation includes:
  - digits measured results
  - practical suite measured results
  - allocation cost
  - quality gaps
  - hardware threshold analysis
- README and `plan.md` match the actual state.

## 10. Current Repository Map

```text
README.md
plan.md

benchmarks/digits/
  run_digits_supremacy.py
  summarize_digits_results.py

benchmarks/smoke/
  simple_quantum_smoke.py
  ml_vs_quantum_circuit_smoke.py
  validate_login_smoke.py

benchmarks/workloads/
  run_practical_suite.py
  summarize_practical_results.py
  hamiltonians/molecular_chain_4q.json

jobs/perlmutter/
  digits_supremacy_1gpu_shared.sbatch
  digits_supremacy_expanded_1gpu_shared.sbatch
  practical_suite_1gpu_shared.sbatch
  practical_suite_sweep_1gpu_shared.sbatch

data/raw/perlmutter/
  digits_expanded/
  practical_suite_sweep/
  accounting/

data/processed/perlmutter/
  digits_expanded_55421321_55422142_summary.json
  practical_suite_combined_summary.json  # after full practical sweep

paper/
  0.Main.tex
  1.Introduction.tex
  2.Background.tex
  3.Design.tex
  4.Evaluation.tex
  5.RelatedWork.tex
  6.Conclusion.tex
```
