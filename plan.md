# QSupremacy Research Plan

Last updated: 2026-07-05

## 0. Current Operating Rule

Do **not** run new experiments by default.

The current goal is to keep the research plan, paper plan, and evidence map
complete and internally consistent. New Slurm jobs should be launched only if a
human explicitly approves a new experimental campaign after reviewing this plan.

Current paper evidence is already sufficient for the present manuscript:

| Gate | Current status | Evidence |
| --- | --- | --- |
| Paper build | PASS, 12 pages | `make -B -C paper` |
| Paper evidence audit | PASS | `scripts/audit_paper_evidence.py` |
| Submission readiness | `SUBMISSION_READY`, warning 0 | `scripts/audit_submission_readiness.py` |
| Previous-paper alignment | `ALIGNED_BY_COUNTS` | `scripts/audit_previous_paper_alignment.py` |
| Previous-paper completion audit | PASS | `paper/previous_paper_completion_audit.md` |

Therefore the near-term work is paper polish, artifact consistency, and
submission targeting. Additional measurements are optional follow-up work, not
required for the current claims.

## 1. One-Sentence Thesis

This project does **not** claim that current quantum hardware beats HPC.
It uses Perlmutter measurements to model **how fast and how accurate future
quantum hardware/software must become** before quantum-circuit applications can
beat strong native HPC baselines on the same task and quality target.

The central comparison is:

```text
native HPC application path
vs.
same application expressed as a quantum-circuit workflow,
simulated with HPC quantum simulators,
then projected to future quantum hardware
```

This is intentionally **not**:

```text
NumPy simulator vs cuQuantum simulator
```

Simulator-vs-simulator tests are only environment, correctness, or backend
diversity checks. They are not the scientific endpoint.

## 2. Paper Claim Boundary

The paper should make these claims:

1. Practical quantum advantage is an application-level break-even condition.
2. The break-even condition depends on runtime and quality together.
3. Native baselines materially change the required quantum speedup.
4. Workload families have different advantage frontiers.
5. HPC quantum simulation is a measurement instrument for threshold modeling,
   not evidence that today's quantum hardware wins.

The paper should **not** claim:

1. Present-day quantum advantage.
2. Universal quantum advantage across all applications.
3. Distributed single-circuit simulator scaling unless the code actually uses a
   distributed simulator for one circuit.
4. That queue wait time is part of the scientific runtime model.
5. That one toy workload represents AI, chemistry, optimization, or simulation.

## 3. Application Families

The workload suite covers practical domains where broad quantum-computing
claims are common.

| Family | Practical claim | Native baseline | Quantum-circuit path | Quality target |
| --- | --- | --- | --- | --- |
| ML / AI | Quantum ML can improve learning | Softmax, MLP, ridge, RBF kernel ridge, kNN, nearest centroid | Quantum feature map, quantum kernel, QNN/VQC | Accuracy/loss |
| Chemistry / drug-discovery proxy | VQE can estimate molecular energies | Dense exact, sparse Lanczos/eigensolver | VQE-style ansatz over Pauli Hamiltonians | Ground-state energy error |
| Optimization | QAOA can improve graph/portfolio/scheduling search | Exact enumeration, greedy, local search, simulated annealing | QAOA-style circuit | Objective gap / approximation ratio |
| Scientific simulation | Hamiltonian simulation is a natural quantum workload | Dense exact dynamics, sparse Krylov-style baseline | Trotterized TFIM/Heisenberg circuit | State or observable error |

Out of scope:

- Quantum cryptography, communication, sensing, and device physics.
- Claims that cannot be mapped to native path vs quantum-circuit path.
- Pure simulator microbenchmarks as final evidence.

## 4. Core Research Questions

1. What is the measured time-to-quality of the native HPC path?
2. What is the measured time-to-quality of the quantum-circuit path simulated on
   Perlmutter?
3. How much faster must future quantum hardware execution be to beat the native
   path?
4. Which component dominates the quantum path: encoding, circuit construction,
   circuit execution, shots, optimizer loop, measurement, or postprocessing?
5. How sensitive is the break-even point to qubits, depth, shots, quality-gap
   recovery, native baseline strength, and error overhead?
6. Which workloads are speed-limited, quality-limited, encoding-limited,
   shot-limited, error-overhead-limited, or native-dominated?

## 5. Formal Model

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

Quantum-circuit simulation path:

```text
T_quantum_sim =
  T_input
+ T_preprocess
+ T_encoding
+ T_circuit_construction
+ T_simulator_execution
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

First-level measured threshold:

```text
required_speedup = T_quantum_sim / T_native
```

Projected hardware execution:

```text
T_hardware_execute =
  N_shots * (N_1q * t_1q + N_2q * t_2q + N_meas * t_meas)
  / parallel_shot_factor
```

Break-even condition:

```text
T_quantum_hw <= T_native
```

Quality condition:

```text
quality_quantum >= quality_target
```

The advantage region is the set of hardware and quality-recovery assumptions
that satisfy both runtime and quality conditions.

## 6. Completed Evidence Summary

No additional jobs are needed to support the current paper claims.

| Evidence component | Current result |
| --- | --- |
| Expanded digits calibration | 160 cases, completed |
| Main practical suite | 3,552 cases on 32 Perlmutter GPU nodes, completed |
| Weak scaling | 8, 16, and 32 GPU nodes, completed |
| Strong scaling | Fixed 3,552-case profile on 4, 8, and 16 nodes, plus matching 32-node endpoint |
| Strong-native baseline gate | Completed |
| Accept-profile chemistry/simulation baseline gate | 116 cases, completed |
| OpenFermion/PySCF chemistry coverage | 104 cases up to 8 qubits, completed |
| Repeat timing gate | 12 measured trials after warmup, max quantum-runtime CV `0.0400` |
| Paper figures | 11 PDF figures generated |
| Evidence audit | PASS |
| Submission readiness | `SUBMISSION_READY` |

Main 3,552-case result:

| Family | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML / AI | 2,048 | `3,726.4x` | `0.3125` |
| Chemistry | 224 | `42,491.4x` | `0.0203` |
| Optimization | 768 | `287,045.6x` | `0.2500` |
| Scientific simulation | 512 | `3,071.0x` | `0.0188` |

Key interpretation:

```text
The quantum-circuit paths do not beat native HPC today.
The useful result is the measured threshold frontier:
how much speed and quality recovery future quantum systems need.
```

## 7. Authoritative Artifacts

The paper-ready artifact set is:

| Artifact | Path |
| --- | --- |
| Manuscript | `paper/main.pdf` |
| Main LaTeX source | `paper/0.Main.tex` |
| Evidence audit | `data/processed/perlmutter/paper_evidence_audit.md` |
| Submission readiness audit | `data/processed/perlmutter/submission_readiness_audit.md` |
| Artifact manifest | `data/processed/perlmutter/paper_artifact_manifest.md` |
| Reviewer-risk map | `paper/reviewer_readiness.md` |
| Previous-paper alignment map | `paper/previous_paper_alignment.md` |
| Previous-paper alignment metrics | `data/processed/perlmutter/previous_paper_alignment_metrics.md` |
| Previous-paper completion audit | `paper/previous_paper_completion_audit.md` |
| Advantage projection | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.md` |
| Workload taxonomy | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json` |
| Main 32-node summary | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv` |

Current validation commands:

```bash
make -B -C paper
python3 scripts/audit_previous_paper_alignment.py
python3 scripts/audit_paper_evidence.py
python3 scripts/audit_submission_readiness.py
```

Expected result:

```text
paper/main.pdf: 12 pages
previous-paper alignment: ALIGNED_BY_COUNTS
paper evidence audit: PASS
submission readiness: SUBMISSION_READY, warning_count 0
LaTeX/BibTeX warnings: none
```

## 8. Paper Structure Plan

The paper follows the accepted ScaleQsim/AURORA-Q structure under
`paper/PreviousPapers`.

| Section | Purpose | Current file | Completion status |
| --- | --- | --- | --- |
| Abstract | Problem, approach, result | `paper/0.Main.tex` | Complete |
| Introduction | Motivation, gap, observations, positioning table, contributions | `paper/1.Introduction.tex` | Complete |
| Background | Application paths, terminology, break-even model | `paper/2.Background.tex` | Complete |
| Design | Measurement framework, workload control, path execution, threshold analysis | `paper/3.Design.tex` | Complete |
| Evaluation | RQ-style evidence, scaling, frontier, stability, projection | `paper/4.Evaluation.tex` | Complete |
| Discussion | Threats, scope, artifact traceability | `paper/5.Discussion.tex` | Complete |
| Related Work | Short previous-paper style categories | `paper/5.RelatedWork.tex` | Complete |
| Conclusion | Lesson-focused close | `paper/6.Conclusion.tex` | Complete |

Previous-paper alignment evidence:

| Alignment requirement | Evidence | Status |
| --- | --- | --- |
| Logic structure | `paper/previous_paper_alignment.md` | PASS |
| Line-by-line mapping | `previous_paper_alignment_metrics.md` current/template source lines | PASS |
| Paragraph-by-paragraph roles | `previous_paper_alignment_metrics.md` role inventory | PASS |
| Word-count alignment | `ALIGNED_BY_COUNTS`, no known gaps | PASS |
| Style alignment | no style-fingerprint gaps | PASS |
| Non-copying boundary | `paper/previous_paper_completion_audit.md` | PASS |

## 9. Evaluation Narrative

The evaluation should answer six systems questions:

| RQ | Question | Evidence |
| --- | --- | --- |
| RQ1 | Does quantum-circuit ML beat native ML today? | Expanded digits and practical ML results |
| RQ2 | How much does output quality change the threshold? | Quality-gap and quality-recovery analysis |
| RQ3 | Do conclusions hold beyond ML? | Chemistry, optimization, simulation suite |
| RQ4 | How sensitive is the result to native-baseline strength? | Strong-native baseline gate and accept-profile baselines |
| RQ5 | Does the measurement workflow scale on Perlmutter? | Weak/strong 4-32 node scaling summaries |
| RQ6 | What future hardware region is required? | Advantage frontier and projection table |

The paper should always state the main lesson:

```text
Quantum advantage is a workload-specific feasible region, not a slogan.
```

## 10. Baseline Policy

The native baseline for each case is the fastest implemented native method that
meets the quality rule. If no native method meets the target, the best-quality
native method is recorded and the case is marked accordingly.

| Family | Native selection policy |
| --- | --- |
| ML | Fastest model within tolerance of best native test accuracy |
| Chemistry | Dense exact and sparse Lanczos/eigensolver candidates; report best quality and selected runtime baseline |
| Optimization | Fastest method matching best objective/cut value when feasible |
| Simulation | Dense exact for small validation; sparse/Krylov where implemented |

Scientific interpretation:

- Strengthening native baselines can increase the required quantum speedup.
- This is not a failed result.
- It is evidence that weaker baselines underestimated the advantage threshold.

## 11. Simulator Backend Policy

The main comparison is application-level, not simulator-level.

| Backend category | Role in this paper |
| --- | --- |
| cuQuantum / cuStateVec | Primary measured quantum-circuit simulation path |
| qsim | Backend-diversity validation and selected comparison |
| CUDA-Q | Framework validation, especially chemistry/VQE-style workflows |
| Qiskit Aer CPU | Framework smoke only unless GPU support is confirmed |
| Aer GPU / PennyLane Lightning GPU / other wrappers | Do not include in large claims unless installed and validated |
| ScaleQsim/qsimh-style distributed paths | Follow-up only unless wired into this repo runner |

Important rule:

```text
Adding wrappers over the same cuStateVec backend does not by itself strengthen
the science. Method diversity matters only if it changes simulation method,
application path, or measurement interpretation.
```

## 12. Perlmutter Scaling Interpretation

The current scale-out results are throughput scaling over independent cases.
They are **not** distributed single-circuit simulation.

Valid claim:

```text
The workflow can evaluate many quantum-circuit application instances across
Perlmutter GPU nodes and produce stable threshold summaries.
```

Invalid claim:

```text
The system implements distributed state-vector simulation for one large circuit.
```

Scaling evidence currently supports:

- weak scaling through 8/16/32 GPU nodes
- fixed-work scaling through 4/8/16 nodes plus 32-node endpoint
- no failed cases in the main scale-out evidence used by the paper
- summary and accounting records for official jobs

## 13. Optional Future Experiments

These are **not active tasks**. They should not be launched unless explicitly
approved.

| Optional extension | Why it might help | Launch condition |
| --- | --- | --- |
| Larger chemistry active spaces | Stronger drug-discovery proxy | Reviewer asks for larger chemistry or new molecule coverage |
| More realistic ML datasets | Reduce toy-workload criticism | Stable local dataset and native baseline are available |
| Larger optimization instances | Better practical optimization coverage | Native exact/heuristic baseline can still be measured fairly |
| Tensor-network backend | Simulator-method diversity | cuTensorNet/Aer tensor-network path is installed and smoke-tested |
| Distributed single-circuit simulation | Separate simulator-systems claim | MPI/cuQuantum distributed or ScaleQsim path is integrated |
| More repeated timing trials | Stronger timing stability evidence | Current repeat gate is challenged by reviewers |

No optional experiment should run unless:

1. The expected paper claim is written first.
2. The native baseline and quality target are defined.
3. The manifest size justifies the requested nodes.
4. A smoke/preflight passes.
5. The user explicitly approves the allocation.

## 14. Stop Conditions For Any Future Experiment

Stop immediately and do not scale further if:

- More than 1% of cases fail or timeout.
- Output filenames collide.
- The manifest is too small to keep allocated GPUs busy.
- Native baseline selection is missing or wrong.
- Quality metrics are absent.
- Summary scripts cannot reproduce exact official case counts.
- The result would only show simulator speed without improving the advantage
  threshold model.

## 15. Current Repository Map

```text
README.md
plan.md

benchmarks/digits/
  run_digits_supremacy.py
  summarize_digits_results.py

benchmarks/smoke/
  simple_quantum_smoke.py
  ml_vs_quantum_circuit_smoke.py
  backend_diversity_smoke.py
  validate_login_smoke.py

benchmarks/workloads/
  run_practical_suite.py
  summarize_practical_results.py
  hamiltonians/

jobs/perlmutter/
  backend_diversity_1gpu_shared.sbatch
  backend_diversity_1gpu_debug.sbatch
  digits_supremacy_1gpu_shared.sbatch
  digits_supremacy_expanded_1gpu_shared.sbatch
  practical_suite_1gpu_shared.sbatch
  practical_suite_sweep_1gpu_shared.sbatch
  practical_suite_scale_nodes.sbatch
  practical_suite_repeat_timing_gate.sbatch

scripts/
  audit_paper_evidence.py
  audit_previous_paper_alignment.py
  audit_submission_readiness.py
  generate_paper_figures.py
  generate_workload_taxonomy.py
  summarize_accept_baselines.py
  summarize_advantage_projection.py
  summarize_chemistry_coverage.py
  summarize_repeat_timing_gate.py

paper/
  0.Main.tex
  1.Introduction.tex
  2.Background.tex
  3.Design.tex
  4.Evaluation.tex
  5.Discussion.tex
  5.RelatedWork.tex
  6.Conclusion.tex
  previous_paper_alignment.md
  previous_paper_completion_audit.md
  reviewer_readiness.md
  figures/
```

## 16. Definition Of Done

This plan is complete when:

- It states that no new experiments should run by default.
- It defines the thesis and claim boundary.
- It lists completed evidence and authoritative artifacts.
- It separates current paper work from optional future experiments.
- It records previous-paper alignment evidence.
- It gives stop conditions for any future allocation.
- It matches the current repository state and audits.

Current status: **complete for planning; no experiment launch is implied**.
