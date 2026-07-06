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

## Review Checkpoint Ledger

The appended reviews are consolidated into checkpoints rather than preserved as
raw rebuttal text. Each checkpoint should strengthen the manuscript narrative
without turning the paper into a point-by-point response.

| ID | Checkpoint | Manuscript-level action | Current status |
| --- | --- | --- | --- |
| C1 | HPCA framing and prior-paper style | Keep the paper architecture-facing: design figures before procedures, evaluation figures before interpretation, and observation boxes for synthesized lessons. | Reflected through `paper/3.Design.tex`, `paper/4.Evaluation.tex`, and previous-paper audits. |
| C2 | Projection model physicality | Decompose `T_error`, bound effective shot parallelism, and state how surface-code distance, cycle time, decoder latency, magic-state throughput, control, data loading, and queueing plug into the same frontier. | Reflected; strengthen with clearer simulator/hardware separation and physical speed-axis interpretation. |
| C3 | Shot parallelism and hybrid-loop limits | Treat `P_shots` as a bounded system resource and make QNN/QAOA host-device iteration overhead visible through metadata and prose. | Partly reflected; add concise text tying shot parallelism to control/decoder/queue limits. |
| C4 | Native baseline strength | State the strongest implemented auditable baselines, show how stronger native paths move thresholds, and explicitly avoid claiming final domain SOTA. | Reflected; strengthen with hardware-utilization boundary and moving-target language. |
| C5 | Simulator versus future hardware | Make clear that cuQuantum measures the circuit application path and metadata; projected hardware latency is not state-vector runtime. | Partly reflected; add explicit contamination boundary in Design/Evaluation. |
| C6 | Long-tail and tolerance sensitivity | Do not rely only on medians. Show or describe p90/max threshold pressure, tolerance sensitivity, and why some tails are native-fast or quality-limited. | Partly reflected; add tail-pressure figure/prose and preserve tolerance-sensitivity figure. |
| C7 | Scaling plateau explanation | Explain 128--256 GPU strong-scaling plateau as independent-case task granularity and per-case floor, not distributed single-circuit synchronization. | Reflected; keep weak and strong scaling separated. |
| C8 | Algorithmic flexibility | Avoid overclaiming fixed QAOA/VQC grids as final algorithms; explain the quality-vs-depth/evaluation tradeoff for richer ansatz and training. | Reflected; strengthen in taxonomy/discussion. |
| C9 | Artifact credibility | Keep raw JSON/CSV/accounting artifacts, figure generation, and readiness audits connected to claims. | Reflected through manifest, evidence audit, and submission-readiness audit. |
| C10 | ML native baseline ceiling | State that scikit-learn ML baselines are auditable but not a production GPU deep-learning or boosted-tree ceiling; add a future strong-native gate for PyTorch CNN/ResNet-style models and XGBoost/LightGBM-style baselines. | Reflected in Evaluation; actual SOTA gate remains future work. |
| C11 | Native hardware utilization proof | Do not claim Tensor Core or memory-bandwidth saturation without counters; plan a Roofline/Nsight Compute gate for native ML and optimization kernels. | Reflected as a required next profiling gate, not fabricated evidence. |
| C12 | Scaling plateau profiling | Current 128--256 GPU plateau is supported by Slurm/task-granularity evidence, but not an Nsight Systems Gantt breakdown. | Reflected as profiling boundary and next experiment. |
| C13 | Physical speed axis readability | Put effective quantum execution time on the Figure 13 secondary x-axis so $10^4$--$10^6\times$ reads as time, not only a dimensionless speedup. | Reflected in regenerated Figure 13 and caption. |
| C14 | Energy and power projection | Extend the future-hardware frontier with parameterized native GPU energy and quantum decoder/fridge/control energy terms; do not instantiate with unmeasured power values. | Reflected in Discussion as a parameterized energy model. |

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
previous-paper alignment: checks pass with TRACKED_WITH_KNOWN_GAPS status
previous-paper deep trace: PASS
previous-paper style audit: PASS
paper evidence audit: PASS
submission readiness: SUBMISSION_READY, warning_count 0, references_start_page 12
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
