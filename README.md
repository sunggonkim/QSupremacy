# QSupremacy

QSupremacy is a quantum supremacy modeling and analysis project. It models when quantum-circuit applications can outperform native HPC/ML applications on Perlmutter.

The core comparison is not simulator vs simulator. The comparison is:

- native application path: classical ML/HPC model executed directly on CPU/GPU
- quantum application path: the same application converted into a quantum-circuit model, simulated with cuQuantum, then projected to future quantum hardware

## Completed Result Summary

The main Perlmutter campaign is complete through the current paper evidence gate.

| Evidence | Status |
| --- | --- |
| Login and Slurm smoke gates | PASS |
| Expanded digits calibration | 160 cases complete |
| Large practical suite | 3,552 cases complete on 32 GPU nodes |
| Weak scaling | 8, 16, and 32 GPU nodes complete |
| Strong scaling | fixed 3,552-case profile complete on 4, 8, and 16 GPU nodes; matching 32-node full-profile point complete |
| Chemistry active-space coverage | 104 OpenFermion/PySCF cases complete |
| Paper figures | 11 PDF figures generated |
| Paper evidence audit | PASS |
| Submission readiness audit | PASS after repeat-timing confidence gate |

Main measured conclusion:

```text
Current quantum-circuit application paths do not beat native HPC baselines.
The contribution is a measured threshold model: how much faster and how much
more accurate future quantum hardware/software must become before advantage is
plausible for each workload family.
```

Median required projected speedups in the main 3,552-case suite:

| Workload | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML / AI | 2,048 | 3,726.4x | 0.3125 |
| Chemistry / drug-discovery proxy | 224 | 42,491.4x | 0.0203 |
| Optimization | 768 | 287,045.6x | 0.2500 |
| Scientific simulation | 512 | 3,071.0x | 0.0188 |

The paper-ready artifacts are:

- manuscript: `paper/main.pdf`
- evidence audit: `data/processed/perlmutter/paper_evidence_audit.md`
- readiness audit: `data/processed/perlmutter/submission_readiness_audit.md`
- main 32-node summary: `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv`
- advantage projection: `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.md`

## Paper Readiness Quickstart

Run the paper checks from the repository root:

```bash
make -B -C paper
python3 scripts/audit_paper_evidence.py
python3 scripts/audit_submission_readiness.py
```

Expected current result: `paper/main.pdf` builds as a 12-page manuscript,
`scripts/audit_paper_evidence.py` reports PASS, and
`scripts/audit_submission_readiness.py` reports `SUBMISSION_READY`.

For allocation-free correctness validation before any new GPU job:

```bash
scripts/run_login_smoke.sh
```

## Repeat Timing Gate

The large sweep already contains repeated seeds and workload-level medians. For
submission timing confidence, the repository also includes a small
warmup-separated hardware repeat gate. It runs one representative case from
each workload family, discards one warmup, and records three measured trials.

```bash
sbatch jobs/perlmutter/practical_suite_repeat_timing_gate.sbatch
```

The gate uses one Perlmutter GPU node with four A100 tasks, so ML, chemistry,
optimization, and simulation run concurrently inside one allocation. Completed
results are summarized into:

- `data/processed/perlmutter/repeat_timing_gate_latest.json`
- `data/processed/perlmutter/repeat_timing_gate_latest.md`

`scripts/audit_submission_readiness.py` uses this summary to decide whether the
warmup-separated repeat-timing check passes.

Current repeat-gate status: job `55516885` completed in 58 seconds with exit
`0:0`. The gate passed with four warmup cases, 12 measured trials, zero failed
trials, and max quantum-runtime CV `0.0400`. The earlier attempt, job
`55516720`, failed after 21 seconds because the inner `srun` login shell did
not inherit the CUDA 12.9 library path needed by cuQuantum
(`libcublas.so.12`); the fixed batch script reloads `cudatoolkit/12.9` inside
each task.

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
- Initial official practical-suite sweep completed:
  190 cases across ML, chemistry, optimization, and simulation.
- Bundled `salloc` pilot completed:
  job `55454998`, 2 A100 GPUs, 96 cases, 6 minutes 54 seconds elapsed.
- Stronger native-baseline logic added for the next official run:
  ML now includes NumPy softmax, MLP, linear ridge, RBF kernel ridge, kNN, and
  nearest-centroid candidates; optimization now includes exact, greedy, local
  search, and simulated annealing candidates.
- Strong-native full-node gate completed:
  job `55468746`, 1 Perlmutter GPU node, 4 A100 GPUs, 190 cases,
  6 minutes 59 seconds elapsed.
- Two-node large-profile scale-out gate completed:
  job `55470269`, 2 Perlmutter GPU nodes, 8 A100 GPUs, 224 cases from
  chunk slots 0-7 of 128, 4 minutes 28 seconds elapsed.
- Four-node large-profile scale-out gate completed:
  job `55470822`, 4 Perlmutter GPU nodes, 16 A100 GPUs, 448 cases from
  chunk slots 0-15 of 128, 4 minutes 43 seconds elapsed, no failed cases.
- Large-profile weak scaling completed:
  jobs `55475423`, `55475476`, and `55475477` completed 896, 1,792, and
  3,552 cases on 8, 16, and 32 GPU nodes with no failed cases.
- Main large practical-suite result now uses the 32-node, 3,552-case summary:
  ML 3,726.4x, chemistry 42,491.4x, optimization 287,045.6x, and simulation
  3,071.0x median required speedup.
- Accept-profile baseline-strengthening run completed:
  job `55498688`, 1 Perlmutter GPU node, 4 A100 tasks, 116 cases,
  6 minutes 5 seconds elapsed, exit `0:0`, empty stderr logs. The run exercises
  OpenFermion/PySCF chemistry fixtures and the sparse/Lanczos/Krylov native
  baseline path.
- Larger OpenFermion/PySCF chemistry coverage completed:
  job `55515248`, 1 Perlmutter GPU node, 4 A100 tasks, 104 chemistry cases,
  5 minutes 23 seconds elapsed, exit `0:0`, empty stderr logs. LiH/H2O
  active-space Hamiltonians now cover 4, 6, and 8 qubits in the GPU coverage
  gate.
- Accept-profile result helper added:
  `scripts/summarize_accept_baselines.py` converts the completed accept-profile
  CSV into compact JSON/Markdown evidence for paper tables.
- Large-profile strong scaling completed:
  jobs `55475633`, `55475634`, and `55475635` completed the fixed 3,552-case
  profile on 4, 8, and 16 GPU nodes. Job `55475477` is the matching full-profile
  32-node point, completing the same 3,552-case profile in 4 minutes 7 seconds
  at the Slurm step level.
- Advantage-frontier figure added:
  `paper/figures/advantage_frontier.pdf`.
- Advantage-projection summary added:
  `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json`
  and matching Markdown table.
- Paper evidence audit added:
  `scripts/audit_paper_evidence.py` currently reports PASS and writes
  `data/processed/perlmutter/paper_evidence_audit.json`.
- Submission-readiness audit added:
  `scripts/audit_submission_readiness.py` currently reports
  `SUBMISSION_READY`; blocking evidence/build/template checks pass,
  and the warmup-separated repeat-timing gate passes.
- Workload taxonomy added:
  `paper/figures/workload_taxonomy.pdf` and
  `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json`.
- Large scale-out manifest profile added:
  `QS_SWEEP_PROFILE=large` expands the practical suite from 190 to 3,552 case templates.
- Paper discussion/threats section added:
  `paper/5.Discussion.tex` states what the measurements prove, where the
  native baseline risk remains, what is outside scope, and how to reproduce
  processed tables/figures.
- Paper advantage-claim checklist added:
  `paper/3.Design.tex` now states the same-task, same-quality, strong-native,
  end-to-end-cost, hardware-projection, error/shot-overhead, and repeatability
  checks used before accepting a practical quantum-advantage claim.

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

- multiclass ML: native softmax/MLP/linear-ridge/RBF-kernel-ridge/kNN/centroid
  candidates vs quantum feature circuit + softmax head
- drug discovery / chemistry: exact H2 Hamiltonian diagonalization vs VQE-style circuit
- optimization: exact/greedy/local-search/annealing MaxCut vs QAOA-style circuit
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

Current OpenFermion/PySCF fixtures:

| Molecule | Active-space fixture | Qubits | Pauli terms |
| --- | --- | ---: | ---: |
| H2 | `h2_sto3g_4q.json` | 4 | 15 |
| LiH | `lih_sto3g_active_4q.json` | 4 | 27 |
| LiH | `lih_sto3g_active_6q.json` | 6 | 62 |
| LiH | `lih_sto3g_active_8q.json` | 8 | 105 |
| H2O | `h2o_sto3g_active_4q.json` | 4 | 15 |
| H2O | `h2o_sto3g_active_6q.json` | 6 | 62 |
| H2O | `h2o_sto3g_active_8q.json` | 8 | 105 |

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
QS_CHUNK_ID=0 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch

# After the pilot passes, bundle the remaining chunk slots into two jobs.
QS_CHUNK_IDS=1,2,3,4,5,6,7,8 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
QS_CHUNK_IDS=9,10,11,12,13,14,15 QS_CHUNK_COUNT=16 \
  sbatch jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
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

Completed official practical sweep:

```text
job_ids: 55453128, 55453129, 55453130, 55453131
cases: 190
summary: data/processed/perlmutter/practical_suite_55453128_55453131_summary.json
```

Median results:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML | 108 | 524.3x | 0.2865 |
| Chemistry | 10 | 67,528.7x | 0.0117 |
| Optimization | 36 | 161,776.0x | 0.2500 |
| Simulation | 36 | 8,747.4x | 0.0250 |

Important baseline note: these 190 official cases were measured before the
stronger native-baseline gate was added. They are kept as the initial sweep for
comparison, not as the strongest current baseline result.

Completed strong-native full-node gate:

```text
job_id: 55468746
run_tag: strongnative_1node_int_20260704012008
qos: interactive
resources: 1 Perlmutter GPU node, 4 A100 GPUs, 128 CPU cores
elapsed: 00:06:59
state: COMPLETED
exit: 0:0
raw JSON files: 190
stderr: 0 bytes
summary: data/processed/perlmutter/practical_suite_strongnative_1node_int_20260704012008_summary.json
accounting: data/raw/perlmutter/accounting/sacct_practical_suite_strongnative_1node_int_20260704012008.txt
```

Median strong-native results:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML | 108 | 3,483.4x | 0.2943 |
| Chemistry | 10 | 39,654.6x | 0.0117 |
| Optimization | 36 | 378,588.2x | 0.2500 |
| Simulation | 36 | 9,634.5x | 0.0250 |

Native model selection in the strong-native run:

| Family | Selected native baselines |
| --- | --- |
| ML | RBF kernel ridge 30 cases, nearest centroid 26, kNN 24, softmax 16, linear ridge 12 |
| Chemistry | exact diagonalization 10 cases |
| Optimization | greedy assignment 30 cases, exact enumeration 6 |
| Simulation | exact dense eigendecomposition 36 cases |

Paper figures:

```text
paper/figures/advantage_frontier.pdf
paper/figures/intro_application_gap.pdf
paper/figures/design_overview.pdf
paper/figures/strong_native_comparison.pdf
paper/figures/workload_taxonomy.pdf
paper/figures/scale_out_gate.pdf
paper/figures/scaling_summary.pdf
```

The frontier plots projected quantum speedup against quality-gap recovery. A
case enters the advantage region only when the projected quantum path is both
fast enough and close enough in output quality to the selected native path.
At 90% quality-gap recovery, the 3,552-case strong-native suite projects that
`10^4x` faster quantum execution covers 54.9% of simulation cases but only 6.6%
of ML cases, while `10^5x` covers 57.1% of chemistry and 71.9% of simulation
cases. Optimization remains hardest: at 90% recovery, even `10^6x` covers only
22.9% of cases.

Completed two-node large-profile scale-out gate:

```text
job_id: 55470269
run_tag: strongnative_2node_large128c0c7_fix_20260704022146
qos: debug
resources: 2 Perlmutter GPU nodes, 8 A100 GPUs, 256 CPU cores
elapsed: 00:04:28
state: COMPLETED
exit: 0:0
chunk slots: 0-7 of 128
raw JSON files: 224
failed cases: 0
summary: data/processed/perlmutter/practical_suite_strongnative_2node_large128c0c7_fix_20260704022146_summary.json
accounting: data/raw/perlmutter/accounting/sacct_practical_suite_strongnative_2node_large128c0c7_fix_20260704022146.txt
```

Median two-node scale-gate results:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML | 128 | 46,159.0x | 0.2813 |
| Chemistry | 16 | 43,081.6x | 0.0203 |
| Optimization | 48 | 365,144.4x | 0.2500 |
| Simulation | 32 | 14,438.3x | 0.0004 |

This is a scale-out gate, not the final 3,552-case large-profile result. It
validates the multi-node bundled execution pattern: one Slurm task per GPU, one
independent chunk per task, and a single summary over all completed chunks.

Completed four-node large-profile scale-out gate:

```text
job_id: 55470822
run_tag: strongnative_4node_large128c0c15_20260704024223
qos: debug
resources: 4 Perlmutter GPU nodes, 16 A100 GPUs, 512 CPU cores
elapsed: 00:04:43
state: COMPLETED
exit: 0:0
chunk slots: 0-15 of 128
raw JSON files: 448
failed cases: 0
summary: data/processed/perlmutter/practical_suite_strongnative_4node_large128c0c15_20260704024223_summary.json
accounting: data/raw/perlmutter/accounting/sacct_practical_suite_strongnative_4node_large128c0c15_20260704024223.txt
```

Median four-node scale-gate results:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML | 256 | 40,893.5x | 0.2813 |
| Chemistry | 32 | 43,424.0x | 0.0203 |
| Optimization | 96 | 354,663.1x | 0.2500 |
| Simulation | 64 | 5,521.1x | 0.0004 |

Completed large-profile weak scaling:

| Job | Nodes | GPUs | Cases | Elapsed | Cases/sec | Cases/sec/GPU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 55475423 | 8 | 32 | 896 | 00:04:05 | 3.657 | 0.1143 |
| 55475476 | 16 | 64 | 1,792 | 00:04:04 | 7.344 | 0.1148 |
| 55475477 | 32 | 128 | 3,552 | 00:04:17 | 13.821 | 0.1080 |

Completed large-profile strong scaling:

| Job | Nodes | GPUs | Cases | Elapsed | Speedup vs 4 nodes | Efficiency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 55475633 | 4 | 16 | 3,552 | 00:30:55 | 1.00x | 1.000 |
| 55475634 | 8 | 32 | 3,552 | 00:15:13 | 2.03x | 1.016 |
| 55475635 | 16 | 64 | 3,552 | 00:11:05 | 2.79x | 0.697 |
| 55475477 | 32 | 128 | 3,552 | 00:04:17 | 7.22x | 0.902 |

Main 32-node large-profile summary:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML | 2,048 | 3,726.4x | 0.3125 |
| Chemistry | 224 | 42,491.4x | 0.0203 |
| Optimization | 768 | 287,045.6x | 0.2500 |
| Simulation | 512 | 3,071.0x | 0.0188 |

Accept-profile baseline-coverage gate:

| Family | Cases | Median required speedup | Median quality gap | Selected native baselines |
| --- | ---: | ---: | ---: | --- |
| Chemistry | 56 | 63,566.8x | 0.4468 | dense exact 56 |
| Simulation | 60 | 4,185.2x | 0.0237 | dense exact 26, sparse Krylov 34 |

Larger chemistry active-space smoke:

| Problem | Qubits | Pauli terms | Selected native | Best quality native | Quantum time |
| --- | ---: | ---: | --- | --- | ---: |
| LiH active 6q | 6 | 62 | dense exact | sparse Lanczos | 7.5518s |
| H2O active 6q | 6 | 62 | dense exact | sparse Lanczos | 7.5517s |
| LiH active 8q | 8 | 105 | dense exact | sparse Lanczos | 7.6970s |
| H2O active 8q | 8 | 105 | dense exact | dense exact | 7.5986s |

Completed larger chemistry coverage run:

```text
job_id: 55515248
run_tag: chem_active_6q8q_1node_20260704233824
state: COMPLETED
exit: 0:0
qos: debug
resources: 1 Perlmutter GPU node, 4 A100 tasks
elapsed: 00:05:23
profile: QS_SWEEP_PROFILE=accept
families: chemistry
chunks: QS_CHUNK_COUNT=4, QS_TASK_COUNT=4
case_timeout: 300s
cases: 104
raw JSON files: 104
stderr: 0 bytes
stdout: logs/qsup-prac-scale-55515248.out
stderr: logs/qsup-prac-scale-55515248.err
summary: data/processed/perlmutter/practical_suite_chem_active_6q8q_1node_20260704233824_summary.json
coverage: data/processed/perlmutter/practical_suite_chem_active_6q8q_1node_20260704233824_chemistry_coverage.md
accounting: data/raw/perlmutter/accounting/sacct_practical_suite_chem_active_6q8q_1node_20260704233824.txt
```

Larger chemistry coverage medians:

| Problem | Qubits | Cases | Median required speedup | Median quality gap | Best-quality native |
| --- | ---: | ---: | ---: | ---: | --- |
| LiH active | 6 | 12 | 21,847.9x | 0.3030 | sparse Lanczos 9, dense exact 3 |
| LiH active | 8 | 12 | 821.5x | 0.6299 | sparse Lanczos 7, dense exact 5 |
| H2O active | 6 | 12 | 21,613.0x | 1.0365 | sparse Lanczos 7, dense exact 5 |
| H2O active | 8 | 12 | 788.0x | 1.0916 | sparse Lanczos 7, dense exact 5 |

Accept-profile artifacts:

```text
summary: data/processed/perlmutter/practical_suite_accept_baselines_1node_20260704150409_summary.json
csv: data/processed/perlmutter/practical_suite_accept_baselines_1node_20260704150409_summary.csv
baseline evidence: data/processed/perlmutter/practical_suite_accept_baselines_1node_20260704150409_accept_baselines.json
accounting: data/raw/perlmutter/accounting/sacct_practical_suite_accept_baselines_1node_20260704150409.txt
```

Validation:

```text
All scaling jobs: COMPLETED, exit 0:0
Failed case / traceback / timeout logs: none
Raw JSON counts: matched expected case counts for every run
Scaling figure: paper/figures/scaling_summary.pdf
```

Bundled `salloc` pilot:

```bash
salloc -A m1248 -C gpu -q shared_interactive -t 00:12:00 \
  -n 2 -c 32 --gpus=2 --job-name=qsup-prac-2gpu-int \
  bash -lc 'cd /pscratch/sd/s/sgkim/Skim-Qsupreme && \
    QS_RUN_TAG=${SLURM_JOB_ID}_prac2gint_c0c1of4 \
    QS_CASE_TIMEOUT=90s QS_CHUNK_COUNT=4 QS_TASK_COUNT=2 \
    QS_CPUS_PER_CHUNK=32 \
    jobs/perlmutter/practical_suite_4gpu_salloc_run.sh'
```

Completed pilot result:

```text
job_id: 55454998
qos: shared_interactive
resources: 2 A100 GPUs, 64 CPU cores
elapsed: 00:06:54
state: COMPLETED
exit: 0:0
stderr: 0 bytes
raw JSON files: 96
summary: data/processed/perlmutter/practical_suite_55454998_prac2gint_c0c1of4_summary.json
```

Median pilot results:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML | 54 | 615.7x | 0.2865 |
| Chemistry | 6 | 49,476.5x | 0.2446 |
| Optimization | 18 | 210,056.9x | 0.2500 |
| Simulation | 18 | 11,629.0x | 0.0250 |

The `salloc` pilot is not the main science result. Its purpose is to verify that
one allocation can run multiple GPU chunks concurrently and produce the same
threshold-style outputs as the official sweep. The main insight is unchanged:
all workload families still require faster projected quantum execution, and the
required improvement is strongly workload dependent.

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
   - softmax/logistic-style regression
   - MLP
   - linear ridge classifier
   - RBF kernel ridge classifier
   - kNN
   - nearest centroid

2. Quantum kernel classifier
   - digits features reduced with PCA
   - quantum feature map simulated with cuQuantum
   - kernel matrix construction and classical classifier head

3. QNN/VQC classifier
   - same train/test split and feature preprocessing
   - parameterized quantum circuit simulated with cuQuantum
   - classical optimizer loop with runtime and accuracy logging

All tracks must report time-to-quality under the same dataset split and target accuracy/loss policy.

## Scale-Out Plan

Do not jump directly to 32 nodes. Use this staged path:

```bash
# Preflight only: no workload execution, just show assigned cases per chunk.
QS_PREFLIGHT_ONLY=1 QS_CHUNK_COUNT=4 \
  sbatch -q debug -t 00:10:00 -N 1 jobs/perlmutter/practical_suite_scale_nodes.sbatch

# S3: one full GPU node, 4 tasks, 4 GPUs.
QS_CHUNK_COUNT=4 \
  sbatch -q debug -t 00:30:00 -N 1 jobs/perlmutter/practical_suite_scale_nodes.sbatch

# S4-S6: debug QOS supports up to 8 GPU nodes for short validation runs.
QS_CHUNK_COUNT=8 \
  sbatch -q debug -t 00:30:00 -N 2 jobs/perlmutter/practical_suite_scale_nodes.sbatch
QS_CHUNK_COUNT=16 \
  sbatch -q debug -t 00:30:00 -N 4 jobs/perlmutter/practical_suite_scale_nodes.sbatch
QS_CHUNK_COUNT=32 \
  sbatch -q debug -t 00:30:00 -N 8 jobs/perlmutter/practical_suite_scale_nodes.sbatch

# S7-S8: only after the 8-node result is clean and the manifest is large enough.
QS_CHUNK_COUNT=64 \
  sbatch -q regular -t 01:00:00 -N 16 jobs/perlmutter/practical_suite_scale_nodes.sbatch
QS_CHUNK_COUNT=128 \
  sbatch -q regular -t 01:00:00 -N 32 jobs/perlmutter/practical_suite_scale_nodes.sbatch
```

Each Perlmutter GPU node has four A100 GPUs. The scale-out runner uses one
Slurm task per GPU and one independent workload chunk per task. This is
throughput scaling across independent cases, not distributed single-circuit
simulation.

For 16/32 node planning, use the large manifest profile:

```bash
# Login-safe dry run; no allocation. Standard profile is 190 cases.
QS_PREFLIGHT_ONLY=1 QS_SWEEP_PROFILE=standard QS_CHUNK_COUNT=4 QS_CHUNK_ID=0 \
  SLURM_JOB_ID=preflight_standard bash jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch

# Login-safe dry run; no allocation. Large profile is 3,552 cases.
QS_PREFLIGHT_ONLY=1 QS_SWEEP_PROFILE=large QS_CHUNK_COUNT=128 QS_CHUNK_ID=0 \
  SLURM_JOB_ID=preflight_large bash jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch

# Example 8-node validation with large profile.
QS_SWEEP_PROFILE=large QS_CHUNK_COUNT=32 QS_CASE_TIMEOUT=180s \
  sbatch -q debug -t 00:30:00 -N 8 jobs/perlmutter/practical_suite_scale_nodes.sbatch
```

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

The current draft is not submission-ready, but it now follows the accepted-paper
structure more closely: intro positioning table, generated intro/design figures,
RQ-style evaluation sections, multiple result figures, a related-work positioning
table, and the completed large-profile weak/strong scaling results through
32 GPU nodes.
