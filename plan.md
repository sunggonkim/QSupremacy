# QSupremacy Research and Execution Plan

Last updated: 2026-07-04

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

### 2.1 Required Paper Insights

The paper should not be framed as "quantum simulators are inefficient." That is true but too small. The main message is:

```text
Quantum advantage is not one speedup number.
It is a workload-specific feasible region over quality, native baseline strength,
logical gate time, shot parallelism, error overhead, and classical control cost.
```

Therefore, the evaluation must produce these insight artifacts:

| Insight artifact | Question it answers | Required output |
| --- | --- | --- |
| Advantage frontier | Where does the quantum path become faster than native HPC? | Heatmap over projected quantum speedup, quality-gap recovery, and later gate/shot/error overhead |
| Time-to-quality curve | Does the quantum path reach the same quality before the native path? | Quality vs runtime curves, not only final accuracy |
| Bottleneck decomposition | What prevents advantage for this workload? | Fraction of time in encoding, circuit build, quantum execution, optimizer, measurement, postprocess |
| Native stress test | Does the conclusion survive stronger classical baselines? | Required speedup after selecting the best quality-valid native method |
| Workload taxonomy | Which application families are plausible, far, or blocked? | Table classifying each family as speed-limited, quality-limited, encoding-limited, shot-limited, or native-dominated |
| Claim checklist | What must be true before someone can claim practical quantum advantage? | Same task, same quality, best native baseline, hardware projection, error overhead, repeated trials |

This makes the contribution an analysis framework for quantum advantage, with HPC simulation used as the measurement instrument.

Current artifact status:

| Artifact | Current status |
| --- | --- |
| Advantage frontier | Implemented as `paper/figures/advantage_frontier.pdf` using the strong-native 190-case practical sweep |
| Native stress test | ML and optimization runner logic strengthened; strong-native 1-node run completed as job `55468746` |
| 1-32 node plan | Batch runner added as `jobs/perlmutter/practical_suite_scale_nodes.sbatch`; one-, two-, and four-node gates completed, eight-node gate submitted |
| Workload taxonomy | Implemented as `paper/figures/workload_taxonomy.pdf` and `data/processed/perlmutter/practical_suite_strongnative_1node_int_20260704012008_taxonomy.json` |
| Large manifest | Implemented as `QS_SWEEP_PROFILE=large`; preflight reports 3,552 case templates |

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

### 3.2 Completed Practical Suite

The practical suite has completed on Perlmutter as a shared-GPU sweep. This is the current application-coverage result beyond the controlled binary digits sweep.

Code:

- Runner: `benchmarks/workloads/run_practical_suite.py`
- Summarizer: `benchmarks/workloads/summarize_practical_results.py`
- Hamiltonian fixture: `benchmarks/workloads/hamiltonians/molecular_chain_4q.json`
- Smoke job: `jobs/perlmutter/practical_suite_1gpu_shared.sbatch`
- Sweep job: `jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch`

Measured practical sweep size:

```text
190 completed cases
```

Breakdown:

| Family | Cases |
| --- | ---: |
| Real multiclass digits ML | 108 |
| VQE-style chemistry | 10 |
| QAOA optimization | 36 |
| Hamiltonian/scientific simulation | 36 |
| Total | 190 |

Artifacts:

- Raw results: `data/raw/perlmutter/practical_suite_sweep/practical_554531*.json`
- Combined summary JSON: `data/processed/perlmutter/practical_suite_55453128_55453131_summary.json`
- Combined summary CSV: `data/processed/perlmutter/practical_suite_55453128_55453131_summary.csv`
- Accounting: `data/raw/perlmutter/accounting/sacct_practical_suite_55453128_55453131.txt`

Measured result:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML | 108 | `524.3x` | `0.2865` |
| Chemistry | 10 | `67,528.7x` | `0.0117` |
| Optimization | 36 | `161,776.0x` | `0.2500` |
| Scientific simulation | 36 | `8,747.4x` | `0.0250` |

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

### 3.3 Current Perlmutter Job Status

The practical sweep used a pilot first, then a corrected bundled run. The paper should use the corrected 190-case run as the official practical-suite result.

Official practical-suite jobs:

```text
55453128: chemistry + optimization + simulation, chunks 0,1, COMPLETED, 00:07:29
55453129: chemistry + optimization + simulation, chunks 2,3, COMPLETED, 00:07:06
55453130: ML, chunks 0,1,2,3, COMPLETED, 00:07:18
55453131: ML, chunks 4,5,6,7, COMPLETED, 00:06:52
```

Validation:

```text
Slurm state: COMPLETED for all four official jobs
Timeout/failed cases: none
Official raw JSON count: 190
Combined CSV lines: 191 including header
paper/main.pdf: builds with practical-suite figure
```

Historical notes:

```text
55432715 was the successful pilot.
55452410 and 55452411 were cancelled after an ML case stalled; partial outputs are not paper results.
55452899 and 55452900 completed chemistry-only subsets because comma-separated sbatch --export values were parsed incorrectly; they are not paper results.
```

### 3.4 Completed salloc Bundled Pilot

A short interactive allocation test was completed to validate bundled execution inside one allocation instead of submitting many independent jobs.

Command shape:

```bash
salloc -A m1248 -C gpu -q shared_interactive -t 00:12:00 \
  -n 2 -c 32 --gpus=2 --job-name=qsup-prac-2gpu-int \
  bash -lc 'cd /pscratch/sd/s/sgkim/Skim-Qsupreme && \
    QS_RUN_TAG=${SLURM_JOB_ID}_prac2gint_c0c1of4 \
    QS_CASE_TIMEOUT=90s QS_CHUNK_COUNT=4 QS_TASK_COUNT=2 \
    QS_CPUS_PER_CHUNK=32 \
    jobs/perlmutter/practical_suite_4gpu_salloc_run.sh'
```

Final successful job:

```text
job_id: 55454998
qos: shared_interactive
resources: 2 A100 GPUs, 64 CPU cores
elapsed: 00:06:54
state: COMPLETED
exit: 0:0
stderr: 0 bytes
raw JSON files: 96
```

Artifacts:

- Runner: `jobs/perlmutter/practical_suite_4gpu_salloc_run.sh`
- Summary JSON: `data/processed/perlmutter/practical_suite_55454998_prac2gint_c0c1of4_summary.json`
- Summary CSV: `data/processed/perlmutter/practical_suite_55454998_prac2gint_c0c1of4_summary.csv`
- Accounting: `data/raw/perlmutter/accounting/sacct_practical_suite_55454998.txt`
- Logs: `logs/qsup-prac-4gpu-55454998_prac2gint_c0c1of4_c*.out`

Measured subset result:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML | 54 | `615.7x` | `0.2865` |
| Chemistry | 6 | `49,476.5x` | `0.2446` |
| Optimization | 18 | `210,056.9x` | `0.2500` |
| Scientific simulation | 18 | `11,629.0x` | `0.0250` |

Implementation lessons:

- Use `shared_interactive` for short `salloc` tests; regular `shared` and `debug` can sit in priority queue.
- Use one `srun` step with multiple tasks instead of launching multiple overlapping `srun` steps.
- Let `SLURM_PROCID` choose the chunk ID.
- Keep `QS_CHUNK_COUNT` separate from `QS_TASK_COUNT`; this allows a short run over chunks `0..TASK_COUNT-1` out of a larger manifest.
- For full 4-GPU node tests, use the same runner with `QS_CHUNK_COUNT=4` and `QS_TASK_COUNT=4`.

### 3.5 Completed Strong-Native One-Node Gate

After strengthening the native baselines, the full 190-case practical suite was rerun inside one interactive Perlmutter GPU-node allocation. This is the current strongest practical-suite result.

Command shape:

```bash
salloc -A m1248 -C gpu -q interactive -t 00:20:00 \
  -N 1 --ntasks-per-node=4 -c 32 --gpus=4 \
  --job-name=qsup-strongnative-1n \
  bash -lc 'cd /pscratch/sd/s/sgkim/Skim-Qsupreme && \
    QS_RUN_TAG=strongnative_1node_int_20260704012008 \
    QS_CHUNK_COUNT=4 QS_TASK_COUNT=4 QS_CASE_TIMEOUT=120s \
    QS_CPUS_PER_CHUNK=32 \
    jobs/perlmutter/practical_suite_4gpu_salloc_run.sh'
```

Final successful job:

```text
job_id: 55468746
qos: interactive
resources: 1 Perlmutter GPU node, 4 A100 GPUs, 128 CPU cores
elapsed: 00:06:59
state: COMPLETED
exit: 0:0
stderr: 0 bytes
raw JSON files: 190
```

Artifacts:

- Summary JSON: `data/processed/perlmutter/practical_suite_strongnative_1node_int_20260704012008_summary.json`
- Summary CSV: `data/processed/perlmutter/practical_suite_strongnative_1node_int_20260704012008_summary.csv`
- Accounting: `data/raw/perlmutter/accounting/sacct_practical_suite_strongnative_1node_int_20260704012008.txt`
- Logs: `logs/qsup-prac-4gpu-strongnative_1node_int_20260704012008_c*.out`

Measured strong-native result:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML | 108 | `3,483.4x` | `0.2943` |
| Chemistry | 10 | `39,654.6x` | `0.0117` |
| Optimization | 36 | `378,588.2x` | `0.2500` |
| Scientific simulation | 36 | `9,634.5x` | `0.0250` |

Native model selection:

| Family | Selected native methods |
| --- | --- |
| ML | RBF kernel ridge 30 cases, nearest centroid 26, kNN 24, softmax 16, linear ridge 12 |
| Chemistry | exact diagonalization 10 cases |
| Optimization | greedy assignment 30 cases, exact enumeration 6 |
| Scientific simulation | exact dense eigendecomposition 36 cases |

Baseline stress-test interpretation:

| Family | Initial median speedup | Strong-native median speedup | Change |
| --- | ---: | ---: | ---: |
| ML | `524.3x` | `3,483.4x` | `6.64x` larger |
| Chemistry | `67,528.7x` | `39,654.6x` | `0.59x` due runtime variance; baseline method unchanged |
| Optimization | `161,776.0x` | `378,588.2x` | `2.34x` larger |
| Scientific simulation | `8,747.4x` | `9,634.5x` | `1.10x` larger |

This result validates the paper's baseline warning: a weak native baseline can understate the quantum hardware speed required for advantage. The paper should use this strong-native result as the main practical-suite threshold and keep the earlier 190-case result as a baseline-stress comparison.

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

### 5.2 Historical Practical Pilot

The successful pilot command was:

```bash
QS_CHUNK_ID=0 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
```

Pilot job:

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

### 5.3 Official 190-Case Practical Sweep

The first bundled command form was:

```bash
QS_CHUNK_IDS=1,2,3,4,5,6,7,8 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch

QS_CHUNK_IDS=9,10,11,12,13,14,15 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
```

Do not use comma-separated values inside `sbatch --export=...`; Slurm splits on commas. Use shell environment prefixes instead. The official 190-case result used this corrected pattern:

```bash
QS_WORKLOAD_FAMILIES=chemistry,optimization,simulation \
QS_CHUNK_COUNT=4 QS_CHUNK_IDS=0,1 QS_CASE_TIMEOUT=90s \
  sbatch --export=ALL jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch

QS_WORKLOAD_FAMILIES=chemistry,optimization,simulation \
QS_CHUNK_COUNT=4 QS_CHUNK_IDS=2,3 QS_CASE_TIMEOUT=90s \
  sbatch --export=ALL jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch

QS_WORKLOAD_FAMILIES=ml \
QS_CHUNK_COUNT=8 QS_CHUNK_IDS=0,1,2,3 QS_CASE_TIMEOUT=90s \
  sbatch --export=ALL jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch

QS_WORKLOAD_FAMILIES=ml \
QS_CHUNK_COUNT=8 QS_CHUNK_IDS=4,5,6,7 QS_CASE_TIMEOUT=90s \
  sbatch --export=ALL jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
```

Monitor all practical jobs:

```bash
squeue -u "$USER" -o '%i %j %T %M %l %R' | grep qsup-prac
```

After all chunks complete, combine only the official job IDs. Do not use `practical_*.json`, because historical pilot and cancelled-job partial outputs may exist in the same directory:

```bash
/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/workloads/summarize_practical_results.py \
  'data/raw/perlmutter/practical_suite_sweep/practical_554531*.json' \
  --summary-json data/processed/perlmutter/practical_suite_55453128_55453131_summary.json \
  --csv data/processed/perlmutter/practical_suite_55453128_55453131_summary.csv
```

Collect accounting:

```bash
sacct -j <jobid_list> \
  --format=JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,AllocTRES%80 \
  -P > data/raw/perlmutter/accounting/sacct_practical_suite_<job_range>.txt
```

## 6. Simulator Backend and Environment Audit

The paper should not pretend that one simulator wrapper represents all quantum-circuit simulation. The right comparison is still native application versus quantum-circuit application, but the quantum-circuit path should be tested through more than one credible simulation path when possible.

### 6.1 Official Documentation Basis

The simulator plan is based on official vendor/project documentation:

| Source | Relevant fact for this project |
| --- | --- |
| NERSC Perlmutter architecture | A GPU node has 4 NVIDIA A100 GPUs, so 1/2/4/8/16/32 nodes correspond to 4/8/16/32/64/128 GPUs. |
| NERSC QOS policy | `debug` supports up to 8 GPU nodes for 0.5 hours; `shared` can charge only the fraction of a node used. |
| NVIDIA cuQuantum | cuStateVec is the state-vector baseline; cuTensorNet is the tensor-network/contraction path; cuStateVec Ex scales from single GPU to multi-node systems. |
| Google qsim | qsim is a full state-vector simulator integrated with Cirq; qsim supports CPU, native GPU, and cuQuantum-backed modes. |
| Qiskit Aer | Aer supports CPU simulation, GPU only when installed with GPU support, and a GPU-only tensor-network method through cuTensorNet. |
| NVIDIA CUDA-Q | CUDA-Q provides a Python/C++ hybrid quantum programming model and NVIDIA/cuStateVec simulation targets, including multi-GPU options. |
| PennyLane Lightning GPU | Lightning GPU uses NVIDIA cuQuantum for GPU-accelerated state-vector simulation. |

### 6.2 Local Perlmutter Environment Findings

Checked local installs under `/pscratch/sd/s/sgkim/`:

| Candidate | Local path/env | Smoke result | Decision |
| --- | --- | --- | --- |
| cuQuantum direct | `/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python` | `cuquantum 26.01.0`, `cupy 13.6.0`, cuStateVec smoke OK | Primary measured backend |
| qsim/qsimcirq | `PYTHONPATH=/pscratch/sd/s/sgkim/ehan/quantum/qsim-main` with `/pscratch/sd/s/sgkim/zainab-qsims/cudaq-env/bin/python` | qsim CPU smoke OK; qsim GPU smoke OK | Add as backend-diversity smoke and selected comparison |
| ScaleQsim executable | `/pscratch/sd/s/sgkim/zainab-qsims/ScaleQsim/apps/qsim_base.x`, `qsimh_base.x` | Executables present; not yet wired into this repo runner | Candidate for distributed/systems follow-up |
| CUDA-Q | `/pscratch/sd/s/sgkim/zainab-qsims/cudaq-env/bin/python` | CUDA-Q `0.14.2`, default target `nvidia`/cuStateVec, simple sample OK | Strong framework backend for VQE/chemistry path |
| Qiskit Aer | same `cudaq-env` | Aer CPU smoke OK; Aer GPU not supported in this install | CPU/framework smoke only unless rebuilt with GPU support |
| PennyLane/Lightning GPU | current envs | not installed in checked envs | Do not include before large run |
| Qulacs/QuEST/Qibo | local candidates exist in old trees, not validated for this repo | not validated | Do not include before large run |

Important interpretation:

- Adding many wrappers over the same cuStateVec backend does not make the science stronger by itself.
- The stronger diversification is by simulation method:
  - state-vector: cuQuantum/cuStateVec, qsim
  - tensor-network: cuQuantum/cuTensorNet or Aer `tensor_network` if GPU build exists
  - hybrid/partition: qsimh/ScaleQsim-style path
  - framework path: CUDA-Q for chemistry/VQE-style workloads
- For the next paper-quality run, use cuQuantum direct as the primary backend and add qsim/CUDA-Q as validation/comparison backends. Do not spend 32 nodes on Aer GPU unless Aer is rebuilt and `AerSimulator().available_devices()` reports `GPU`.

### 6.3 One-GPU Debug Sanity Gate

Before any larger run, submit one short one-GPU sanity job. Prefer `shared` when the goal is only backend validation, because it charges the fractional node. Use `debug` only when explicitly validating the debug QOS/full-node path.

```bash
sbatch jobs/perlmutter/backend_diversity_1gpu_shared.sbatch

# Optional full-node debug-QOS variant:
# sbatch jobs/perlmutter/backend_diversity_1gpu_debug.sbatch
```

This job validates:

- one GPU is visible through Slurm
- cuQuantum direct import path
- qsim CPU and qsim GPU path
- CUDA-Q cuStateVec target
- Qiskit Aer CPU path and explicit Aer GPU status
- one application-level practical-suite smoke across ML, chemistry, optimization, and simulation

Expected output files:

```text
data/raw/perlmutter/backend_sanity/backend_diversity_<jobid>.json
data/raw/perlmutter/backend_sanity/practical_suite_<jobid>.json
logs/qsup-backend-sanity-<jobid>.out
logs/qsup-backend-sanity-<jobid>.err
```

Pass criteria:

- Slurm state is `COMPLETED`.
- Backend JSON has `"pass": true`.
- Required backend statuses are `ok` for `cuquantum_direct`, `qsim_cpu`, `qsim_gpu`, and `cudaq_custatevec`.
- Practical-suite smoke validates with `PASS: login smoke outputs validated`.
- Aer GPU may report unsupported in the current env; this is recorded but not a blocker.

Current result:

```text
job_id: 55454471
qos: shared
resources: 1 A100 GPU, 32 CPU cores
state: COMPLETED
elapsed: 00:00:26
stderr: 0 bytes
backend pass: true
required backends ok: cuQuantum direct, qsim CPU, qsim GPU, CUDA-Q cuStateVec
optional Aer GPU: unsupported in current install, recorded as non-blocking
```

## 7. Baseline Audit Before Any 32-Node Run

The initial 190-case result was enough for a first threshold-modeling result, but not enough to defend the native side. The strengthened baseline logic has now been run as the official `strong-native` one-node gate. Before spending up to 32 Perlmutter nodes, use the strong-native result as the main baseline and expand the manifest so larger allocations have enough useful work.

### 7.1 Current Baselines

| Family | Current native baseline | Current quantum-circuit path | Status |
| --- | --- | --- | --- |
| Binary digits ML | Logistic regression, MLP | Quantum kernel, QNN/VQC | Good calibration baseline |
| Practical ML | Softmax, MLP, linear ridge, RBF kernel ridge, kNN, nearest centroid | Quantum feature circuit + softmax head | Strengthened and measured in job `55468746` |
| Chemistry | Dense exact diagonalization for H2 and 4-qubit Pauli Hamiltonian | VQE-style ansatz on cuStateVec | Good correctness baseline, not production chemistry |
| Optimization | Exact enumeration, greedy assignment, local search, simulated annealing | QAOA p=1 grid search | Strengthened and measured in job `55468746`; larger instances pending |
| Simulation | Dense exact eigendecomposition for 4/5/6-qubit TFIM/Heisenberg | First-order Trotter circuit | Good small-instance baseline, not scalable simulation |

### 7.2 Baseline Implementation Status

Implemented in this round:

| Family | Implemented baseline strengthening | Evidence |
| --- | --- | --- |
| ML | NumPy linear ridge, RBF kernel ridge, kNN, nearest centroid added alongside softmax and MLP | `benchmarks/workloads/run_practical_suite.py` |
| ML | Native selection rule chooses the fastest model within tolerance of best native test accuracy | `selection_rule=fastest_model_within_tolerance_of_best_test_accuracy` in JSON |
| Optimization | Greedy, local search, and simulated annealing added alongside exact enumeration | `benchmarks/workloads/run_practical_suite.py` |
| Optimization | Native selection rule chooses fastest method matching the best cut value | `selection_rule=fastest_model_matching_best_cut` in JSON |
| Summary | CSV now records selected native model and native model count | `benchmarks/workloads/summarize_practical_results.py` |

Still needed before the final 32-node paper run:

| Family | Required additional native baselines | Why |
| --- | --- | --- |
| ML | GPU/PyTorch MLP or stronger tree/boosting baseline if available in a stable Perlmutter env | Avoid comparing quantum ML against only small NumPy models |
| ML | Larger datasets: MNIST/Fashion-MNIST or OpenML tabular if available locally | `sklearn_digits` is useful but too small for a main large-scale claim |
| Chemistry | PySCF/OpenFermion-generated molecular Hamiltonians, at least LiH/H2O small active spaces | The current 4-qubit fixture is a pipeline test, not a drug-discovery benchmark |
| Chemistry | Sparse/Lanczos eigensolver baseline for Hamiltonians that exceed dense diagonalization | Dense exact diagonalization becomes an unfair or impossible native baseline at larger qubit counts |
| Optimization | MILP/HiGHS if available, larger graph generators, and portfolio/scheduling instances | Practical claims are not only 4/5-node MaxCut |
| Optimization | Larger MaxCut plus portfolio/scheduling instances | Practical claims are not only 4/5-node MaxCut |
| Simulation | Sparse Krylov `expm_multiply`, TEBD/MPS if available, and dense exact only for validation | Dense eigendecomposition is not the strong baseline for larger chains |
| All | Repeated trials, warmup-separated timings, breakdown timers | Current medians mix some initialization and Python overhead |

Baseline acceptance rule:

```text
For each workload instance, the native baseline time must be the best valid time
among all implemented native methods that meet the same quality target.
```

If a stronger native baseline lowers `T_native`, the required quantum speedup increases. If a stronger native baseline raises quality but takes longer, the quality gap may increase while the speed threshold changes. Both outcomes are scientifically acceptable and must be reported.

## 8. Perlmutter Scale-Out Plan Up To 32 Nodes

The goal of using more Perlmutter nodes is not to make the current tiny workloads faster. The goal is to answer two scaling questions:

1. How does the quantum-circuit simulation path scale when the circuit size and batch count increase?
2. How does the required quantum hardware speedup change when native baselines are strengthened and workloads become less toy-like?

Do not start at 32 nodes. Use gated stages.

NERSC policy basis checked on 2026-07-04:

- Perlmutter GPU nodes have 4 NVIDIA A100 GPUs per node.
- GPU `debug` QOS allows up to 8 nodes for 0.5 hours.
- GPU `shared` QOS can request 1 or 2 GPUs and is charged fractionally.
- `regular` jobs reserve exclusive nodes, so only use it when the manifest is large enough.

Official references:

- https://docs.nersc.gov/systems/perlmutter/architecture/
- https://docs.nersc.gov/jobs/policy/
- https://docs.nersc.gov/systems/perlmutter/running-jobs/

### 8.1 Required Engineering Before Multi-Node Runs

The current practical runner is a single-process, one-GPU-per-case runner. It can fill many GPUs by launching many independent cases, but it is not yet a true distributed simulator. Therefore, there are two possible scale-out modes:

| Mode | Meaning | When to use |
| --- | --- | --- |
| Embarrassingly parallel sweep | Many independent workload cases across nodes/GPUs | Near-term 1-32 node experiment |
| Distributed single-circuit simulation | One large circuit/state-vector split across many GPUs/nodes | Later, after adding MPI/cuQuantum distributed or qsim distributed support |

For the next run, use embarrassingly parallel sweeps. Do not claim distributed single-circuit scaling unless the code actually uses distributed state-vector/tensor-network simulation.

Before submitting more than one node:

- Add per-case warmup control.
- Add per-case timeout.
- Add unique result prefixes to avoid collisions.
- Add a manifest file listing all case IDs, parameters, and expected output files.
- Add a preflight command that prints the case count per job before submission. Current support: `QS_PREFLIGHT_ONLY=1`.
- Add summarization that selects only official job IDs, not all historical partial JSON files.
- Add native baseline selection logic: best quality-valid native runtime among all baselines. Current support: implemented for ML and optimization.
- Confirm that each node can keep its four A100 GPUs busy with independent processes.

Current implementation status:

```text
standard profile: 190 case templates
large profile: 3,552 case templates
large profile command: QS_SWEEP_PROFILE=large
preflight support: QS_PREFLIGHT_ONLY=1
```

### 8.2 Node Scaling Stages

| Stage | Nodes | GPUs | Purpose | Submit only if |
| --- | ---: | ---: | --- | --- |
| S0 | Login | 0 | Correctness and schema smoke | Always first |
| S1 | Shared 1 GPU sanity | 1 shared GPU | Backend-diversity and application sanity with fractional charging | S0 passes |
| S2 | Shared 1 GPU sweep | 1 shared GPU | Single-case and chunk sanity with official sweep runner | S1 passes |
| S3 | 1 full node | 4 GPUs | Validate per-node packing and no file collisions | S2 passes |
| S4 | 2 nodes | 8 GPUs | Validate multi-node array behavior and summary scripts | S3 has enough independent cases |
| S5 | 4 nodes | 16 GPUs | Small official scaling point | S4 completes cleanly |
| S6 | 8 nodes | 32 GPUs | Medium scaling point | S5 result quality and accounting are clean |
| S7 | 16 nodes | 64 GPUs | Large scaling point | S6 shows useful throughput and no scheduler/file issues |
| S8 | 32 nodes | 128 GPUs | Final scale-out point | S7 passes and workload size justifies 128 GPUs |

### 8.3 Workload Size For 32 Nodes

The standard 190-case suite is too small for 32 nodes. It completed in minutes on one full GPU node. A 32-node run needs the large profile or a larger manifest:

| Family | Current size | 32-node target size |
| --- | ---: | ---: |
| ML | 108 cases, 4-8 qubits | 2,048 large-profile cases with 4-10 qubits and repeated trials; later larger datasets |
| Chemistry | 10 cases, 2/4 qubits | 224 large-profile VQE cases, layers 1-2; later multiple molecular Hamiltonians |
| Optimization | 36 cases, 4/5 nodes | 768 large-profile QAOA cases, 4-7 nodes; later p=2/3 and larger graphs |
| Simulation | 36 cases, 4-6 qubits | 512 large-profile cases, 4-7 qubits; later sparse/Krylov or MPS baselines |

For a 32-node embarrassingly parallel run, target at least:

```text
128 GPUs * 10 minutes of useful case work per GPU
```

If the manifest cannot provide that much useful work, do not use 32 nodes.

Large-profile preflight:

```bash
QS_PREFLIGHT_ONLY=1 QS_SWEEP_PROFILE=large QS_CHUNK_COUNT=128 QS_CHUNK_ID=0 \
  SLURM_JOB_ID=preflight_large \
  bash jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
```

Observed preflight result:

```text
total_case_templates=3552
chunk0_cases_with_128_chunks=28
```

### 8.4 Proposed Official Scale-Out Matrix

Run the same official manifest at each node count, with enough case batching to keep GPUs busy:

| Node count | GPUs | Walltime request | Expected use |
| ---: | ---: | --- | --- |
| 1 | 4 | completed in 00:06:59 | Full-node packing validation, standard profile |
| 2 | 8 | 00:30:00 | Multi-node sanity, standard or large profile |
| 4 | 16 | 00:30:00 | First scaling curve point, large profile |
| 8 | 32 | 00:30:00 | Medium scaling point, large profile and debug QOS |
| 16 | 64 | 01:00:00 | Large scaling point, large profile and regular QOS |
| 32 | 128 | 01:00:00 | Final throughput point, large profile and regular QOS |

Concrete submission sequence:

```bash
# Preflight only: prints chunk assignment without running cases.
QS_PREFLIGHT_ONLY=1 QS_CHUNK_COUNT=4 \
  sbatch -q debug -t 00:10:00 -N 1 \
  jobs/perlmutter/practical_suite_scale_nodes.sbatch

# S3 completed: one full GPU node, four independent GPU tasks.
# job_id=55468746, run_tag=strongnative_1node_int_20260704012008

# S4: 2-node sanity. Use standard first if only checking launch mechanics.
QS_CHUNK_COUNT=8 QS_CASE_TIMEOUT=120s \
  sbatch -q debug -t 00:30:00 -N 2 \
  jobs/perlmutter/practical_suite_scale_nodes.sbatch

# S5-S6: use the large profile so there is enough work per GPU.
QS_SWEEP_PROFILE=large QS_CHUNK_COUNT=16 QS_CASE_TIMEOUT=180s \
  sbatch -q debug -t 00:30:00 -N 4 \
  jobs/perlmutter/practical_suite_scale_nodes.sbatch

QS_SWEEP_PROFILE=large QS_CHUNK_COUNT=32 QS_CASE_TIMEOUT=180s \
  sbatch -q debug -t 00:30:00 -N 8 \
  jobs/perlmutter/practical_suite_scale_nodes.sbatch

# S7-S8: only after the 8-node run is clean.
QS_SWEEP_PROFILE=large QS_CHUNK_COUNT=64 QS_CASE_TIMEOUT=180s \
  sbatch -q regular -t 01:00:00 -N 16 \
  jobs/perlmutter/practical_suite_scale_nodes.sbatch

QS_SWEEP_PROFILE=large QS_CHUNK_COUNT=128 QS_CASE_TIMEOUT=180s \
  sbatch -q regular -t 01:00:00 -N 32 \
  jobs/perlmutter/practical_suite_scale_nodes.sbatch
```

This runner uses one Slurm task per GPU and one workload chunk per task. This is throughput scaling over independent cases. It is not distributed single-circuit simulation.

Metrics to report:

- completed cases per second
- GPU-hours and node-hours
- median and tail case runtime
- GPU occupancy from logs or Nsight/system telemetry if available
- simulator runtime breakdown
- native baseline runtime breakdown
- required speedup distribution per workload family
- quality-gap distribution per workload family

### 8.5 Stop Conditions

Stop and do not scale to the next node count if any of these happen:

- More than 1% of cases fail or timeout.
- Any output file collision occurs.
- GPU utilization is low because the manifest is too small.
- Native baseline selection is wrong or missing for a family.
- Quality gates are not met or not recorded.
- Summary scripts cannot reproduce the case count exactly from official job IDs.

### 8.6 What 32 Nodes Should Prove

The 32-node result should prove:

1. \SystemName can evaluate many practical quantum-circuit application instances on Perlmutter without scheduler or output-management artifacts.
2. Threshold results remain stable under larger case counts and stronger native baselines.
3. Different application families have different required hardware speedups.
4. Larger HPC simulation capacity does not itself imply quantum advantage; it improves the measurement and modeling fidelity.

It should not prove:

- that cuQuantum, qsim, or any simulator is "bad"
- that quantum computers are worse than HPC in principle
- that one application result generalizes to all quantum computing

The large run is useful only if it sharpens the advantage frontier and the workload taxonomy in Section 2.1.

## 9. Paper Plan

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
8. Advantage frontier by workload family
9. Workload taxonomy: speed-limited, quality-limited, encoding-limited, shot-limited, native-dominated
10. Claim checklist for practical quantum advantage

The current paper already includes the digits and 190-case practical-suite results. The next paper version should prioritize advantage-frontier and workload-taxonomy figures before adding more simulators. Stronger baselines and 1-32 node scaling matter only because they make those insights credible.

## 10. Risks and Mitigations

| Risk | Why It Matters | Mitigation |
| --- | --- | --- |
| Quantum path has lower quality | Runtime-only claims become invalid | Always report quality gap and time-to-quality |
| Data encoding dominates | Advantage disappears | Measure encoding separately |
| Tiny workloads exaggerate Python overhead | Misleading threshold | Use login smoke only for validation; use GPU sweeps for results |
| Native baseline too weak | Artificial quantum advantage | Use strengthened selection across ML and optimization baselines; add chemistry/simulation sparse baselines before large runs |
| Full-node allocation waste | Perlmutter time wasted | Use shared 1-GPU chunks first |
| 32-node run too small | Looks wasteful and gives no scaling signal | Only run 32 nodes after target manifest has enough work |
| Embarrassingly parallel run mistaken for distributed simulation | Overclaims simulator scalability | Label it as throughput scaling unless distributed cuQuantum/qsim is implemented |
| Too many simulator wrappers | Dilutes the paper and duplicates cuStateVec underneath | Keep cuQuantum direct primary; use qsim/CUDA-Q for validation and method diversity |
| Aer GPU unavailable | Planned GPU backend silently runs on CPU | Require `available_devices()` to show `GPU`; otherwise record Aer as CPU-only |
| Practical sweep exceeds walltime | Lost jobs and partial data | Pilot chunk first; increase chunk count if needed |
| Queue time distorts compute model | Scheduler effects hide compute behavior | Report compute time and allocation/accounting separately |
| Chemistry fixture is not production molecule | Weak drug-discovery claim | Use fixture for pipeline; add OpenFermion/PySCF-generated Hamiltonians later |
| Paper sounds like simulator criticism | Contribution becomes too narrow | Frame simulators as measurement tools; make hardware frontier and advantage conditions the main output |

## 11. Immediate Next Actions

Current active state:

```text
Digits expanded sweep completed.
Practical 190-case suite completed with official jobs 55453128-55453131.
Backend-diversity 1-GPU shared sanity completed with job 55454471.
Bundled salloc 2-GPU shared_interactive pilot completed with job 55454998.
Paper Evaluation includes measured figures and table.
Advantage-frontier figure generated at paper/figures/advantage_frontier.pdf.
Stronger ML and optimization native baseline logic implemented.
Strong-native one-node gate completed with job 55468746.
Workload taxonomy generated at paper/figures/workload_taxonomy.pdf.
Large manifest preflight implemented with QS_SWEEP_PROFILE=large and 3,552 cases.
Scale-out batch runner added at jobs/perlmutter/practical_suite_scale_nodes.sbatch.
Two-node large-profile scale-out gate completed with job 55470269: 224 cases, 8 GPUs, no failed cases.
Four-node large-profile scale-out gate completed with job 55470822: 448 cases, 16 GPUs, no failed cases.
Eight-node large-profile scale-out gate submitted as job 55475423 and should be left running until final Slurm state.
```

Next actions:

1. Do not launch a 32-node run yet.
2. Add chemistry sparse/Lanczos and simulation sparse-Krylov baselines before any paper-scale 16/32 node result.
3. Wait for the 8-node gate (`55475423`) to reach a final Slurm state; do not cancel due to queue/start-time estimates.
4. If the 8-node gate is clean, update the paper and then decide whether the 16-node regular run is worth the allocation.
5. Use `regular` for 16/32 nodes only after the 8-node result is clean.
6. Scale through 4, 8, 16, and 32 nodes only if the stop conditions in Section 8.5 are not triggered.

## 12. Completion Criteria

The project is not complete until all of the following are true:

- Login smoke passes.
- Digits expanded result is measured and summarized.
- Practical suite pilot completes successfully.
- Practical suite full 190-case sweep completes.
- Backend-diversity 1-GPU shared sanity completes.
- Bundled `salloc` pilot completes.
- Combined practical summary JSON/CSV exists.
- Slurm accounting is saved.
- Paper evaluation includes:
  - digits measured results
  - practical suite measured results
  - allocation cost
  - quality gaps
  - hardware threshold analysis
  - advantage-frontier figure
  - workload taxonomy figure
- Strong-native practical suite rerun exists and is summarized.
- One-node full-packing scale-out gate passes.
- Two-node large-profile scale-out gate passes.
- Four-node large-profile scale-out gate passes.
- Baseline-stress figure compares initial and strong-native practical suites.
- Scale-out gate figure compares one-node, two-node, and four-node bundled runs.
- Large-profile preflight exists and reports enough cases for 32-node planning.
- README and `plan.md` match the actual state.

## 13. Current Repository Map

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
  backend_diversity_1gpu_debug.sbatch
  backend_diversity_1gpu_shared.sbatch
  digits_supremacy_1gpu_shared.sbatch
  digits_supremacy_expanded_1gpu_shared.sbatch
  practical_suite_1gpu_shared.sbatch
  practical_suite_sweep_1gpu_shared.sbatch
  practical_suite_scale_nodes.sbatch

data/raw/perlmutter/
  digits_expanded/
  practical_suite_sweep/
  accounting/

data/processed/perlmutter/
  digits_expanded_55421321_55422142_summary.json
  practical_suite_55453128_55453131_summary.json
  practical_suite_55453128_55453131_summary.csv
  practical_suite_strongnative_1node_int_20260704012008_summary.json
  practical_suite_strongnative_1node_int_20260704012008_taxonomy.json
  practical_suite_strongnative_2node_large128c0c7_fix_20260704022146_summary.json
  practical_suite_strongnative_4node_large128c0c15_20260704024223_summary.json

scripts/
  generate_paper_figures.py
  generate_workload_taxonomy.py

paper/
  figures/
  0.Main.tex
  1.Introduction.tex
  2.Background.tex
  3.Design.tex
  4.Evaluation.tex
  5.RelatedWork.tex
  6.Conclusion.tex
```
