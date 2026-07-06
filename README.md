# QSupremacy

QSupremacy is the repository name. The HPCA manuscript now uses the display
system name **QArchGauge**: an architecture-guided practical quantum-advantage
modeling project evaluated on a Top-20 TOP500 leadership-scale HPC system.
It compares native HPC/ML application paths against quantum-circuit versions of
the same workloads, simulated with cuQuantum and projected to future quantum
hardware.

The paper claim is intentionally not "quantum is faster today." The measured
result is a threshold model: how much faster and more accurate future quantum
systems must become before a workload can beat a strong native path.
The architecture result is the bottleneck label behind that threshold: whether a
future quantum system should prioritize logical gate throughput, shot
parallelism, error/quality recovery, host-control overhead, or algorithmic
quality.

## Current Paper State

The HPCA-style paper is built and evidence-backed.
The current figures follow the previous-paper pattern of compact subfigures with
shared legend panels, and the evaluation uses observation boxes for architecture
bottleneck insights.

| Item | Status |
| --- | --- |
| Manuscript PDF | `paper/main.pdf` builds successfully |
| Body budget | Expanded evidence draft; references start on page 13 |
| Main suite | 3,552 cases on 128 GPUs |
| 256-GPU fixed work | 3,552 cases in 261 seconds |
| 256-GPU larger-workload gate | 7,104 cases in 514 seconds |
| ML production-native gate | 32 same-input cases with PyTorch AMP CNN/MLP and XGBoost GPU-hist |
| ML profiling gate | Nsight Systems + dmon captured; Nsight Compute counter failure recorded |
| Workloads | ML, chemistry, optimization, scientific simulation |
| Previous-paper structure audit | PASS via JSON artifacts |
| Previous-paper LaTeX style audit | PASS via JSON artifacts |
| Paper evidence audit | PASS |
| Submission readiness audit | `EVIDENCE_READY_WITH_SUBMISSION_RISKS`, 0 blocking errors, 1 length warning |

Main 3,552-case medians:

| Workload | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML / AI | 2,048 | 3,726.4x | 0.3125 |
| Chemistry / drug-discovery proxy | 224 | 42,491.4x | 0.0203 |
| Optimization | 768 | 287,045.6x | 0.2500 |
| Scientific simulation | 512 | 3,071.0x | 0.0188 |

ML production-native gate:

| Item | Result |
| --- | ---: |
| Cases | 32 |
| Previous selected-native median threshold | 8,876.8x |
| Combined selected-native median threshold | 8,601.6x |
| Production-only median threshold | 49.3x |
| Combined selections | 24 previous suite, 8 PyTorch AMP CNN |
| Production selections | 25 PyTorch AMP CNN, 5 XGBoost GPU-hist, 2 PyTorch AMP MLP |
| Profiled GPU-kernel fraction | 0.8% |
| Profiled host-orchestration fraction | 99.2% |

## Paper Readiness Quickstart

Run from the repository root:

```bash
make -B -C paper
python3 scripts/audit_previous_paper_alignment.py
python3 scripts/audit_previous_paper_deep_trace.py
python3 scripts/audit_previous_paper_style.py
python3 scripts/audit_paper_evidence.py
python3 scripts/audit_submission_readiness.py
```

Expected result:

```text
previous-paper alignment: ALIGNED_BY_COUNTS
previous-paper deep trace: PASS
previous-paper style audit: PASS
paper evidence audit: PASS
submission readiness: EVIDENCE_READY_WITH_SUBMISSION_RISKS, warning_count 1
```

For allocation-free sanity checks:

```bash
scripts/run_login_smoke.sh
```

## Key JSON Artifacts

| Artifact | Path |
| --- | --- |
| Paper evidence audit | `data/processed/perlmutter/paper_evidence_audit.json` |
| Submission readiness audit | `data/processed/perlmutter/submission_readiness_audit.json` |
| Artifact manifest | `data/processed/perlmutter/paper_artifact_manifest.json` |
| Previous-paper alignment metrics | `data/processed/perlmutter/previous_paper_alignment_metrics.json` |
| Previous-paper deep trace | `data/processed/perlmutter/previous_paper_deep_trace.json` |
| Previous-paper style audit | `data/processed/perlmutter/previous_paper_style_audit.json` |
| Main 128-GPU summary | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json` |
| 256-GPU fixed-work summary | `data/processed/perlmutter/practical_suite_strongscale_64node_largefull_c0c255_20260705024742_summary.json` |
| 256-GPU larger-workload summary | `data/processed/perlmutter/practical_suite_strongnative_64node_large256c0c255_20260705024742_summary.json` |
| ML production-native gate | `data/processed/perlmutter/ml_strong_native_gate_latest.json` |
| ML profiling gate | `data/processed/perlmutter/ml_strong_native_profile_latest.json` |
| Advantage projection | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json` |
| Workload taxonomy | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json` |

Markdown policy: only README files and `plan.md` are kept in the repository.
