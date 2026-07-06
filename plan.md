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
| Main practical suite | 3,552 cases, 128 GPUs |
| 256-GPU fixed work | 3,552 cases in 261 seconds |
| 256-GPU larger-workload gate | 7,104 cases in 514 seconds |
| Workload coverage | ML, chemistry, optimization, scientific simulation |
| Previous-paper logic/style | JSON audits PASS |
| Evidence audit | PASS |
| Submission readiness | `SUBMISSION_READY`, warning count 0 |

## Critical Review Integration Map

The two inserted reviews converge on five acceptance-critical issues. The paper
should address them through the manuscript's normal logic, not as a rebuttal
list.

| Review pressure | Manuscript response |
| --- | --- |
| Projection model is too abstract. | Design must decompose `T_error` into compile/map/route/decode/magic-state/data-load/control/queue terms and define effective `P_shots` as a bounded system resource. Evaluation should read the speed axis as a microarchitecture target, not a simulator speedup slogan. |
| `P_shots`, recovery, and tolerance are underspecified. | Design must treat shot parallelism as limited by device, decoder, control, queue, and finite evaluations. Evaluation must include a tolerance-sensitivity figure and explain that quality recovery is a requirement axis, not a measured free improvement. |
| Native baselines may be too weak. | Baseline sections must state the strongest implemented auditable baseline, show the strong-native shift, and explicitly frame future SOTA native methods as moving the frontier rightward rather than invalidating the method. |
| Scaling and seven-second circuit paths need systems explanation. | Evaluation must report quantum-runtime IQRs, explain the fixed small-circuit orchestration floor, and clarify that 128--256 GPU plateau is independent-case throughput granularity rather than distributed single-circuit MPI/cuQuantum synchronization. |
| Algorithm/workload scope may bias conclusions. | Discussion must state fixed QAOA/QNN/VQC choices as auditable scope, explain that better ansatz or training trades quality recovery against more depth/evaluations/control overhead, and avoid extrapolating small active spaces into deployment-scale chemistry. |

Style target: follow the PreviousPapers pattern: design figure first, then
component procedure; evaluation figure first, then data and systems
interpretation; use observation boxes for synthesized insight rather than
tables of raw facts.

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
| Main 128-GPU summary | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json` |
| 256-GPU fixed-work summary | `data/processed/perlmutter/practical_suite_strongscale_64node_largefull_c0c255_20260705024742_summary.json` |
| 256-GPU larger-workload summary | `data/processed/perlmutter/practical_suite_strongnative_64node_large256c0c255_20260705024742_summary.json` |
| Advantage projection | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json` |

## Remaining Paper Work

No additional leadership-system experiments are required for the current paper claims.
Before submission, replace the HPCA `NaN` submission number and recheck the final
conference template/instructions.

