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
| HPCA body budget | Expanded evidence draft; references start on page 13 |
| Main practical suite | 3,552 cases, 128 GPUs |
| 256-GPU fixed work | 3,552 cases in 261 seconds |
| 256-GPU larger-workload gate | 7,104 cases in 514 seconds |
| ML production-native gate | 32 cases with PyTorch AMP CNN/MLP and XGBoost GPU-hist |
| ML profiling gate | Nsight Systems + dmon captured; Nsight Compute counters attempted and recorded as unavailable |
| Workload coverage | ML, chemistry, optimization, scientific simulation |
| Previous-paper logic/style | JSON audits PASS |
| Evidence audit | PASS |
| Submission readiness | `EVIDENCE_READY_WITH_SUBMISSION_RISKS`, warning count 1 |

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
| C10 | ML native baseline ceiling | Add same-input production-style ML native candidates and report whether they change the threshold. | Completed with 32-case PyTorch AMP CNN/MLP + XGBoost GPU-hist gate; combined median threshold is 8,601.6x and production-only median threshold is 49.3x. |
| C11 | Native hardware utilization proof | Do not claim Tensor Core or memory-bandwidth saturation without evidence; collect profiler evidence where possible. | Completed as a bounded claim: Nsight Systems captured tensor-family kernels, dmon shows low SM utilization, and Nsight Compute counter failure is recorded rather than converted into a saturation claim. |
| C12 | Scaling plateau profiling | Quantify whether small-case GPU work is kernel-bound or orchestration-bound, and connect that to the 128--256 GPU plateau without overclaiming. | Completed with a representative profiling gate: GPU kernels are 0.8% of the profiled run and host orchestration is 99.2%; no full 256-GPU Gantt trace is claimed. |
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
submission readiness: EVIDENCE_READY_WITH_SUBMISSION_RISKS, warning_count 1, references_start_page 13
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
| ML production-native gate | `data/processed/perlmutter/ml_strong_native_gate_latest.json` |
| ML profiling gate | `data/processed/perlmutter/ml_strong_native_profile_latest.json` |
| Advantage projection | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json` |

## Remaining Paper Work

No additional leadership-system experiments are required for the current claims as
written. Before submission, compress the expanded evidence draft back to the
11-page HPCA body budget, replace the HPCA `NaN` submission number, and recheck
the final conference template/instructions.

## New Review: SOSP-style External Review

### Weaknesses

#### Technical limitations or concerns
The “quality recovery” axis (R) is a hypothetical requirement rather than demonstrated progress; no concrete mitigation/FT instantiation is exercised end-to-end to show how much R can be achieved at what cost in depth/overheads.
The execution model keeps T_error and P_shots largely abstract; only an illustrative fault-tolerant mapping is given without a full resource-estimation pipeline (code distances, factory throughput, decoder scaling) instantiated per case.
Measured simulator runtime exhibits a roughly seven-second floor dominated by orchestration; projecting this down to ms/µs “effective quantum time” risks conflating host-stack artifacts with logical-operation budgets if not normalized carefully.

#### Experimental gaps or methodological issues
Workloads remain at small qubit counts and toy input scales (e.g., 4–16 qubits, sklearn digits, small active spaces). While methodologically disciplined, external validity to production-scale problems is limited.
Native baselines, while strengthened and diversified, omit some domain-SOTA methods that could further tighten thresholds (e.g., advanced MILP for larger optimization instances, domain-optimized tensor-network or projector-QMC baselines, CCSD(T)-quality references for chemistry).
Limited exploration of shots and mitigation strategies; shot-parallelism limits are acknowledged but not deeply stressed with realistic decoder/control constraints or empirical queue contention models.

#### Clarity or presentation issues
Some equations and tables show minor extraction/formatting artifacts; while not blocking, the paper could further streamline the mapping from measured cuQuantum time to logical-time projections to avoid possible misinterpretation of the seven-second floor.

#### Missing related work or comparisons
While Azure’s resource estimator and surface-code works are cited, the paper could better connect to recent end-to-end FT resource estimates for concrete algorithms (e.g., large-scale chemistry/factoring studies) and to domain-optimized classical baselines (e.g., TN/QMC in physics simulation).
Additional discussion of queueing/scheduling models in hybrid runtimes and hardware-constrained shot concurrency (device, decoder, control bandwidth) would strengthen the P_shots realism.

### Detailed Comments

#### Technical soundness evaluation
The same-input, same-quality discipline and explicit break-even condition are technically sound and address common pitfalls in quantum/classical comparisons.
The decomposition T_execute = Ns(D1 t1 + D2 t2 + Dm tm)/P_shots + T_error is reasonable as a first-order model and is clearly positioned as a lower bound; the microarchitecture map is a useful hook.
However, leaving T_error and P_shots mostly symbolic in the main results limits the conclusiveness of architecture guidance. A minimal FT instantiation (even if stylized) per family, with decoder bandwidth and magic-state constraints, would provide stronger, more concrete targets.
The use of a simulator-dominated constant floor to back out “effective quantum times” can be misleading if readers conflate host orchestration time with logical gate costs. The paper mitigates this by emphasizing dimensionless speedups, but the narrative could better isolate per-circuit kernel contributions from Python/process overhead in the projection.

#### Experimental evaluation assessment
The breadth of the suite and the rigor of logging, provenance, and failure accounting are excellent. The scale-out analysis, weak/strong scaling, and the larger-workload gate add credibility to the methodology as a system.
Native-baseline stress tests are thoughtfully designed; the profiling gate is particularly helpful in demonstrating where host orchestration dominates at small scales.
External validity is the main concern: qubit counts, problem sizes, and chemistry active spaces are small. The conclusions are framed carefully as “architecture requirements,” but readers could overgeneralize from small, structured inputs.
The bottleneck taxonomy is compelling: simulation/chemistry trend toward speed/shot limits; ML/optimization toward quality limits. This is a key practical insight that is well supported by the data.

#### Comparison with related work
Relative to ScaleQsim/AURORA-Q/cuQuantum and benchmark suites (SupermarQ, QASMBench, MQT Bench, QAOAKit), QARCHGAUGE focuses on application-level advantage thresholds with strong native baselines and explicit quality targets—an important and complementary direction.
Compared to application-oriented benchmarks (e.g., Lubinski et al.), this paper adds a break-even frontier and an architectural lens (t1/t2/tm, P_shots, T_error decomposition) and enforces same-input/same-quality discipline.
Resource-estimation works (Azure estimator, surface-code studies) are appropriately cited; however, the paper stops short of fully instantiating them for its workloads. Integrating a baseline FT instantiation for a subset of cases would elevate the contribution.

#### Broader impact and significance
The work helps the community move from “quantum is faster/slower” rhetoric to concrete, testable architecture goals. It also exposes when faster gates won’t help because quality limits dominate—valuable guidance for co-design.
It risks misinterpretation if readers treat the reported dimensionless speedups as immediately actionable without the FT/mitigation costs; the paper’s repeated caveats are appreciated but stronger normalization and a worked FT example would help.
The methodology—especially the logging/provenance discipline, failure accounting, and bottleneck taxonomy—could outlive specific workloads and be adopted across labs, fostering more honest and comparable claims.

### Questions for Authors
How sensitive are the advantage frontiers to shot count and measurement strategy? Can you provide a sensitivity sweep that varies Ns and P_shots under plausible decoder/control limits to quantify shot-limited regions more concretely?
Can you instantiate a minimal, concrete FT stack (e.g., distance, cycle time, factory throughput, decoder BW) for a subset of chemistry/simulation cases to translate S into logical times and show how T_error and P_shots tighten the frontier?
How does the seven-second per-case floor vary with circuit size, depth, and number of evaluations? Would using a compiled, lower-overhead driver (e.g., C++ orchestrator) materially change the inferred speedups?
For ML and optimization, what algorithmic or mitigation steps plausibly contribute to 50–90% “quality recovery,” and what depth/iteration overheads would they add? Can you map R to expected increases in D1/D2/Neval?
For physics simulation, have you compared against domain-optimized classical baselines (e.g., tensor-network, projector-QMC) on your specific small Hamiltonians to bound how much the native frontier could still move?
Would you consider releasing the full artifact (JSON logs, scripts, Slurm configs) to enable re-analysis of tolerance, baselines, and projection parameters by others?
How do queueing and device contention affect P_shots in realistic multi-tenant settings (e.g., shared decoders/controllers)? Could you add a simple queueing model to bound effective P_shots under contention?

### Overall Assessment
QARCHGAUGE addresses an important, often conflated question: not whether a simulator is fast, but what concrete architectural and algorithmic improvements are necessary for practical quantum advantage on real tasks. The same-input/same-quality discipline, explicit frontier over speed and quality recovery, and the bottleneck taxonomy provide actionable insights that can guide hardware architects and algorithm designers. The evaluation is unusually thorough in systems terms: large case coverage, strong provenance, baseline stress tests, and scaling evidence. The principal limitations are external validity (small qubit counts and toy-scale inputs) and the largely symbolic treatment of fault-tolerant parameters (T_error, P_shots) and quality recovery (R). Even so, the paper is careful in claims and turns measurement into design guidance instead of hype.

For SOSP, this sits at the intersection of systems measurement, architecture projection, and quantum-classical workflow design. While some aspects may feel more HPCA/ASPLOS-oriented, the methodology and findings are of broad systems interest. I recommend acceptance, contingent on strengthening the connection to a concrete FT instantiation for a subset of cases and clarifying the sensitivity of frontiers to shots and host orchestration. The work would provide valuable and timely guidance to the community.
