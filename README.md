# QSupremacy

QSupremacy is the repository name. The HPCA manuscript now uses the display
system name **QArchGauge**: a Perlmutter-based architecture-guided practical
quantum-advantage modeling project.
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
| Body budget | 13 total pages; references start on page 12 |
| Main suite | 3,552 cases on 32 Perlmutter GPU nodes |
| Workloads | ML, chemistry, optimization, scientific simulation |
| Previous-paper structure audit | PASS via JSON artifacts |
| Previous-paper LaTeX style audit | PASS via JSON artifacts |
| Paper evidence audit | PASS |
| Submission readiness audit | `SUBMISSION_READY`, 0 blocking errors, 0 warnings |

Main 3,552-case medians:

| Workload | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML / AI | 2,048 | 3,726.4x | 0.3125 |
| Chemistry / drug-discovery proxy | 224 | 42,491.4x | 0.0203 |
| Optimization | 768 | 287,045.6x | 0.2500 |
| Scientific simulation | 512 | 3,071.0x | 0.0188 |

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
submission readiness: SUBMISSION_READY, warning_count 0
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
| Main 32-node summary | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json` |
| Advantage projection | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json` |
| Workload taxonomy | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json` |

Markdown policy: only README files and `plan.md` are kept in the repository.
