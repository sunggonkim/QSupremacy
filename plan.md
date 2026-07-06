# QSupremacy Plan

## Goal

Model practical quantum advantage as an architecture-guided application-level
break-even condition. The paper display system name is **QArchGauge**.

```text
native HPC/ML application path
vs.
same workload converted to a quantum-circuit application path,
simulated with cuQuantum, then projected to future quantum hardware
```

The paper should answer how fast, how parallel, and how accurate future quantum
hardware must be before each workload family can beat the native path. It should
also identify the computer-architecture bottleneck: logical gate throughput,
shot parallelism, error/quality recovery, host-control overhead, native baseline
strength, or algorithmic quality.

## Current Status

| Area | Status |
| --- | --- |
| Paper PDF | Built at `paper/main.pdf` |
| HPCA body budget | References start on page 12 |
| Main practical suite | 3,552 cases, 32 Perlmutter GPU nodes |
| Workload coverage | ML, chemistry, optimization, scientific simulation |
| Previous-paper logic/style | JSON audits PASS |
| Evidence audit | PASS |
| Submission readiness | `SUBMISSION_READY`, warning count 0 |

## Validation Commands

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
paper/main.pdf: builds successfully
previous-paper alignment: ALIGNED_BY_COUNTS
previous-paper deep trace: PASS
previous-paper style audit: PASS
paper evidence audit: PASS
submission readiness: SUBMISSION_READY, warning_count 0
```

## Authoritative JSON Artifacts

| Artifact | Path |
| --- | --- |
| Evidence audit | `data/processed/perlmutter/paper_evidence_audit.json` |
| Submission readiness audit | `data/processed/perlmutter/submission_readiness_audit.json` |
| Artifact manifest | `data/processed/perlmutter/paper_artifact_manifest.json` |
| Previous-paper alignment metrics | `data/processed/perlmutter/previous_paper_alignment_metrics.json` |
| Previous-paper deep trace | `data/processed/perlmutter/previous_paper_deep_trace.json` |
| Previous-paper style audit | `data/processed/perlmutter/previous_paper_style_audit.json` |
| Main 32-node summary | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json` |
| Advantage projection | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json` |

## Remaining Paper Work

No additional Perlmutter experiments are required for the current paper claims.
Before submission, replace the HPCA `NaN` submission number and recheck the final
conference template/instructions.
