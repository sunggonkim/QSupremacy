# QArchGauge HPCA 2027 Plan

This file is the authoritative current plan. Completed revision diaries and raw
review text belong in Git history, not here.

## 1. Paper Identity

Canonical positioning:

> **QArchGauge is an HPC-driven architecture diagnosis framework that converts
> paired native-HPC and quantum-circuit measurements into workload-specific,
> falsifiable targets for future QPU development.**

Short framing:

> **QArchGauge uses leadership-class HPC as an empirical oracle for deciding
> which QPU resource delivers the next unit of application-level advantage.**

QArchGauge is not a cuQuantum speed paper, a claim that GPU scaling predicts
QPU scaling, a new QPU microarchitecture, or evidence that present quantum
hardware beats native HPC. Its architecture contribution is an **inversion
tool**:

```text
same input + application tolerance
       |                     |
       v                     v
native-HPC execution    quantum-circuit execution
       |                     |
       +--- paired record ---+
                  |
                  v
      component-preserving QPU inversion
                  |
                  v
<quality gate, first resource, crossover, next resource, low-utility resources>
```

The core question is:

> Given a measured native-HPC deadline and an application-quality target, which
> QPU resource must improve, by how much, before additional hardware progress
> can create application-level advantage?

Target title:

> **QArchGauge: HPC-Driven Architecture Targeting for Application-Level
> Quantum Advantage**

## 2. Current Decision State

| Item | Current state |
| --- | --- |
| Main evidence | 3,552 paired controlled ML/Chem/Opt./Sim. cases plus deployment-facing native frontiers, direct quality-cost closures, compiled attachments, and physical design envelopes. |
| Paper build | The deterministic build has 14 total PDF pages. The manuscript occupies pages 1--11 and references begin at the first line of page 12. Figure 4 is the only two-column `figure*`; all other figures are one-column. |
| Audits | PASS after the 20-asset figure/legend and exact 11-page-body revision. Submission readiness is `SUBMISSION_READY`: 12/12 GO gates, zero blocking errors, and zero warnings. |
| Optional scaling jobs | Jobs 55885604/55885607/55885608 are terminal `TIMEOUT` outcomes on `m5320_g`. They completed 4,298/5,794/7,092 of 7,104 records at 4/8/16 GPUs before 8/5/3-hour limits. They are timeout-censored, excluded from completed fixed-work points, and preserved in `low_gpu_strong_scaling_timeout_audit.json`. |
| Goal execution | Stages 0--6 are complete: checkpoint, evidence audits, finite-shot closure, FT reliability/space, joint DSE, matched mechanism replacement, claim freeze, manuscript/figure rewrite, deterministic rebuild, and final visual/audit gate all pass. |
| Quality and finite-shot gate | PASS with a restricted eligible subset. At the default noiseless tolerance, 48/224 Chem and 256/512 Sim records pass; ML and Opt. have zero passes. At 10,000 shots, only 12 matched Sim records satisfy the full-loop finite-shot gate. Chem covers fixed selected parameters but not its outer optimizer, ML uses a different measurable feature map, and Opt. remains quality-failing. |
| Stage-1 schedule audit | PASS for the implemented static loops: 224 compiled Chem schedules, 3,040 source-audited static loops, 512 single-circuit Sim records, and zero aggregate fallbacks. Factory remains the conditional execution target across aggregate/group-wave/serial bounds. Adaptive optimizer and mid-circuit claims remain unsupported. |
| Stage-1 statistical audit | PASS over 222 structural configurations and 16 distinct seeds per configuration using a hierarchical bootstrap. The 3,552 rows are records, not 3,552 independent applications. |
| Stage-3 FT audit | PASS with restricted application scope. The official QDK surface-code formula reproduces all 100 existing QAOA distance estimates. For the 12 quality-qualified Sim records at a 1% strict application budget and physical error $10^{-3}$, $d=13$--15 and a 79--86 T/rotation leading-term synthesis budget replace the old fixed $d=15$, 16-T assumption. The qualified factory crossover is 39,351--42,961x the 64-factory baseline, and only 6/12 records have a non-factory floor below the native deadline. All other workload summaries remain conditional. |
| Stage-4 joint DSE | PASS over 384 deterministic space-filling scenarios and 26,112 evaluated case points. The six conservative phase-map cells at 1--100x factory supply retain `factory_supply` as the first target for all 12 eligible Sim records. At 10,000x, insufficient lanes move the target to shot parallelism; at 50,000x, logical-cycle and advantage-reached states emerge. These are deterministic robustness regions, not technology probabilities. |
| Stage-4 matched replacement | PASS. An LSQCA point-SAM replacement consumes matched logical-operand events rather than a published multiplier. The 4--7-qubit eligible corpus has 0/12 core-area wins; after 50,000x factory scaling, matched load/store movement raises median runtime by 3.12x--5.23x and removes all 6 baseline parity cases. BOSS-compatible QAOA/Chem interaction bounds remain conditional QCCD envelopes. |
| Submission administration | Replace the title-page placeholder with the assigned paper number and complete HPCA registration checks before submission. |

The technical revision and clean rebuild pass the current GO contract. This is
not an acceptance guarantee: the explicit residual limits and submission
administration remain. The timeout-censored low-GPU runs do not expand the
retained application-level claims.

## 3. Defensible Thesis

The paper establishes three claims in this order.

1. **Advantage is a paired application boundary.** The native and circuit paths
   use the same input, report quality in the application's natural unit, and
   retain repetitions, shots, grouping, state preparation, and feedback.
2. **Leadership HPC is an evidence generator, not a QPU timer.** Perlmutter
   measures application quality and circuit demand over a broad corpus. The
   simulator wall time is removed before physical-QPU projection.
3. **Architecture value is workload- and phase-dependent.** QArchGauge inverts
   the moving native deadline into quality, logical-cycle, routing, rotation
   supply, shot, decoder, and control budgets, then reports the first and next
   useful resource.

The strongest current negative result is also useful: idealized feedback
aggregation changes ML/Chem/Opt. medians by only 1.10x/1.31x/1.08x and leaves
one-evaluation Sim. unchanged. Host I/O is visible but is not the first-order
cure in the measured records. This is not a universal claim that I/O never
matters; it is a measured bottleneck transition.

## 4. Architecture Output

Section III.B, **QPU Critical-Path Inversion**, is the primary architecture
contribution. It is a two-stage diagnosis. The application quality gate is
evaluated first; component-level hardware targeting is an application claim
only for records that pass that gate. Every result should then instantiate the
same five-field output:

1. **Quality gate:** whether a noiseless algorithmic path already satisfies the
   application tolerance.
2. **First resource:** the component with the largest useful marginal gain
   while all other assumptions are held fixed.
3. **Required crossover:** the improvement needed before that component stops
   dominating or runtime parity becomes possible.
4. **Next resource:** the bottleneck exposed after the first resource is
   removed or reaches its crossover.
5. **Low-utility resources:** improvements that cannot materially move the
   application boundary in the current phase.

Records that fail quality must report `algorithm/representation first` and may
show the physical critical path only as a **conditional execution lower bound**.
They must never be pooled with quality-passing records to claim that a factory,
decoder, or gate is the first application-level target. The architecture map
therefore has two visible layers: `quality-qualified hardware targets` and
`quality-failing conditional execution bottlenecks`.

For every resource, report both the measured 10x marginal gain and an
**Amdahl-style removal ceiling** obtained by recomputing the complete model
with that resource made non-limiting. Do not derive this ceiling by subtracting
one bar from a sum: the overlap, saturation, and feedback model must be
re-evaluated. This makes `low utility` quantitative and prevents a visually
small component from being promoted as an architecture priority.

The current evidence supports this bounded target map:

| Path | First architecture target | Quantitative boundary | Next target |
| --- | --- | --- | --- |
| Surface-code universal path, quality-passing cases | Synthesized-rotation / magic-state supply | The complete quality/FT contract requires 39,351--42,961x the 64-factory baseline to reach the non-factory crossover. In the joint phase map, all eligible records remain factory-first at 1--100x; the recommendation begins to split at 10,000x. | Shot parallelism under a 1,000-lane cap; otherwise logical cycle after sufficient supply. |
| Native-rotation neutral-atom envelope | Readout/reuse and useful shot throughput | Literature-calibrated execution-only counterfactual; not a fault-tolerant or current-device advantage claim. | Cycle and routing only after readout/reuse pressure falls. |
| Native-rotation QCCD/TILT, ML/Chem | Readout/service latency | Conditional timing envelope over recorded demand. | Shot/cycle pressure. |
| Native-rotation QCCD/TILT, Opt./Sim. | Routed 2Q execution | Conditional timing envelope; full movement and tail contention remain replacement contracts. | Readout/control after routed 2Q pressure falls. |
| Quality-failing cases | Encoding, ansatz, search, or approximation quality | All controlled ML and Opt., 78.6% of Chem, and 50.0% of Sim. miss tolerance even in noiseless simulation. | Hardware speed matters only after a richer measured record passes quality. |

Do not call a hardware modality a winner. The non-surface-code paths are
counterfactual execution envelopes without compatible logical-error, routing,
and measured-tail contracts.

## 5. Novelty Boundary

| Prior-work family | Representative work | Difference from QArchGauge |
| --- | --- | --- |
| Application benchmarks | [SuperMarQ](https://arxiv.org/abs/2202.11045), [QASMBench](https://arxiv.org/abs/2005.13018), [QED-C](https://arxiv.org/abs/2110.03137) | Measures circuit features, fidelity, quality, and sometimes time-to-solution, but does not bind every case to a measured native-HPC deadline and invert it into component marginal utility. |
| Classical/quantum application frameworks | [QUARK](https://arxiv.org/abs/2202.03028) | Already compares classical and quantum application implementations, so QArchGauge must not claim to be the first such comparison. Its distinction is the paired record, physical critical path, and first-to-next-resource inversion. |
| Fault-tolerant resource estimation | [Beverland et al.](https://arxiv.org/abs/2211.07629), Microsoft QDK, Google Qualtran | The closest methodological neighbor. These estimate resources for selected algorithms; QArchGauge adds a measured moving native frontier, natural-unit quality, a broad paired corpus, and workload-specific marginal utility. |
| Component architecture | [BOSS](https://arxiv.org/abs/2412.03443), [S-SYNC](https://arxiv.org/abs/2505.01316), [LSQCA](https://arxiv.org/abs/2412.20486), AFS, routing, decoder, control, and factory designs | Optimizes a component. QArchGauge diagnoses when that component is first order and where the bottleneck moves next. Published average or maximum improvements are not transferable multipliers unless the same topology and demand are compiled. |
| Current trace/QEC/co-design | [TraceQ](https://arxiv.org/abs/2508.14533), [Pinball](https://arxiv.org/abs/2512.09807), [Cyclone](https://arxiv.org/abs/2511.15910), and HPCA 2026 causality-aware grouping/control work | Exposes concrete dataflow traces, decoder bandwidth/power, QCCD topology, or grouping mechanisms. QArchGauge must either consume a compatible mechanism as a replacement case study or state exactly why its event semantics do not match. |
| HPC simulation and orchestration | cuQuantum, NWQSim, ScaleQsim, and [QFw](https://arxiv.org/abs/2509.14470) | Expands simulation capacity and hybrid orchestration. QArchGauge uses HPC to build empirical demand/quality records, not to treat simulator throughput as future-QPU speed. |
| Detailed physical models | [Decoder/reaction-time modeling](https://arxiv.org/abs/2511.10633) | Provides a richer surface-code decoder/controller reaction-time model. QArchGauge should cite it, compare assumptions, and expose it as a replacement for the current mean-latency attachment. |
| Alternative quality/rotation mechanisms | [Logical soft-information QEM](https://arxiv.org/abs/2512.09863), [postselected arbitrary rotations](https://arxiv.org/abs/2303.17380) | These can change shots, logical error, or rotation supply. They are sensitivity/replacement scenarios, not evidence that quality recovery is free. |

Defensible novelty sentence:

> Unlike prior benchmark, orchestration, and resource-estimation systems,
> QArchGauge jointly executes same-input native-HPC and circuit paths, retains
> natural-unit quality and repeated application demand in one auditable record,
> and inverts the measured boundary into workload-specific first/next QPU
> resource targets.

Avoid unqualified claims of being the first application benchmark, the first
classical-versus-quantum comparison, the first FT estimator, or the largest
quantum simulation.

## 6. Evidence Levels

| Level | Current evidence | Allowed claim |
| --- | --- | --- |
| Controlled measurement | 3,552 4--20-qubit paired records, exact quality, direct QAOA/Chem/Sim quality-cost ladders | `Measured in the controlled corpus`; never `deployment-scale advantage`. |
| Deployment-facing native frontier | ResNet-18/Pool-108, 64-thread CCSD(T), MaxCut MILP/heuristics, and matrix-free Krylov | Stronger measured native deadline, not universal domain SOTA. |
| Compiled attachment | QWC grouping, shot allocation, routing, QAOA depth/distance cross-checks | Component demand for supported cases only. |
| Capacity evidence | 36/38/40-qubit local-shard runs and 1--256-GPU case throughput | Perlmutter capacity/evidence-generation scale only; not distributed QPU behavior or application quality. |
| Physical projection | Literature parameters plus measured demand and invariant audits | `Projected lower-bound target` or `scenario`; never `measured QPU result`. |
| Quality-qualified projection | Finite-shot quality, dependency schedule, logical-error budget, and explicit physical envelope all attached to the same record | May identify the first application-level hardware target. |
| Future validation | Real QPU traces, noise, tail latency, logical QEM, full PPA/energy | Must remain explicitly unmeasured. |

The small controlled circuits are intentional because exact natural-unit
quality closure is required. Deployment frontiers and capacity records provide
scale context but must not be folded into controlled quality medians.

## 7. Strong-Accept Evidence Packages

The paper is not complete when the prose sounds architectural. It is complete
when every likely rejection argument below is closed by an audited artifact,
a visible paper result, and a claim that matches the evidence. All P0 packages
are submission-blocking. P1 work is promoted only if a retained claim needs it.

### P0-A: Quality-Qualified Architecture Diagnosis

**Risk closed:** the current paper can appear to call factories the first
application target even when every ML/Opt. record fails quality.

Required work:

1. Partition every record into `quality_pass`, `quality_fail_with_measured_ladder`,
   or `quality_fail_without_recovery_evidence` before physical targeting.
2. Recompute family/subtype statistics and the architecture map on the
   quality-passing subset only. For a family with zero passing records, report
   `algorithm/representation first`; do not name a hardware first target.
3. Retain physical timing for failed records only as a separately styled
   conditional execution lower bound.
4. Sweep natural-unit tolerances at 0.5x/1x/2x and report how pass share and the
   eligible target map change.
5. Couple shots to measured quality. At 10^3/10^4/10^5 shots, use direct or
   replayed sampling for representative ML, Chem, Opt., and Sim. records with
   multiple random seeds. Where quality cannot be measured, label the result
   runtime-only and exclude it from advantage.

Required artifact: `quality_qualified_target_map.json` plus CSV rows containing
`quality_status`, `tolerance`, `shots`, `quality_ci`, `hardware_target_eligible`,
and the reason for exclusion.

Completion gate: no figure, abstract sentence, observation, or conclusion calls
a hardware component the first application target for a quality-failing family.

### P0-B: Trace-Aware Concurrency and Feedback Semantics

**Risk closed:** the current `P_ready` may be an aggregate-demand optimistic
fallback for the complete 3,552-record DSE.

Required work:

1. Audit the exact fraction using `compiled_dependency_wave`,
   `recorded_independent_circuit_bound`, and
   `aggregate_total_demand_lower_bound`.
2. Build explicit representative schedules for every workload family and each
   distinct loop type: outer optimizer iteration, commuting-group wave, kernel
   matrix row, one-shot repetition, and any true mid-circuit dependency.
3. Populate `ready_shot_executions`, critical-path depth, group barriers, and
   host-visible reaction events from those schedules.
4. Re-evaluate all cases under three transparent bounds: aggregate-ready,
   group-wave-ready, and serial-evaluation. Map uncompiled cases to the most
   conservative compatible class rather than inventing a DAG.
5. Gate ARTERY/Qtenon-style feedback replacement on matching dynamic events.
   Outer VQE/QAOA/QNN iterations are not mid-circuit branch prediction.
6. Compare the trace contract explicitly with TraceQ and current HPCA dataflow
   work; do not claim TraceQ itself is a scheduler.

Required artifact: `dependency_schedule_coverage.json` with subtype coverage,
ready-width distributions, fallback fractions, and first/next-target stability
across all dependency modes.

Completion gate: every retained architecture conclusion either survives the
conservative schedule mode or is narrowed to the exact compiled subset.

### P0-C: Case-Level Fault-Tolerance and Spatial Feasibility

**Risk closed:** fixed code distance, aggregate factory rate, and noiseless
quality are not yet one application-level reliability contract.

Required work:

1. Define explicit application failure budgets, with at least 1% and 0.1%
   sensitivity, and state whether the budget applies per circuit, per shot, or
   to the aggregate estimator. Do not require every shot to be error-free when
   the estimator can tolerate sample errors.
2. Derive case- or subtype-specific logical volume and code distance from the
   routed circuit, shots, evaluations, and failure budget. Extend the QDK check
   beyond the 50 QAOA records or provide an audited conservative envelope for
   unsupported records.
3. Sweep 4/8/16/32 T states per arbitrary rotation and report the measured
   angle distribution where compiler artifacts preserve it. Apply small-angle
   methods only to compatible rotations.
4. Convert factory crossover into factory count, physical-site/qubit demand,
   and supply feasibility. Compare a conventional floorplan with an LSQCA-style
   load/store envelope while charging data movement and access latency.
5. Add a decoder/reaction-time envelope using current detailed models, with
   bandwidth, latency, and correction-storage terms separated. No fabricated
   queue tail is allowed.

Required artifact: `ft_reliability_and_space_budget.json` containing parameter
origin, failure target, selected distance, physical footprint, factory count,
decoder demand, and unsupported-scope flags for every summarized subtype.

Completion gate: the 10^4--1.6x10^4 factory statement is either preserved under
the reliability/space contract or replaced by a narrower, fully supported
crossover range.

### P0-D: Joint DSE and Published-Mechanism Replacement

**Risk closed:** one-factor 10x sweeps can miss interactions and make QArchGauge
look like a collection of independent knobs rather than a co-design tool.

Required work:

1. Run a bounded factorial or space-filling DSE over dependency mode,
   tolerance, finite shots, useful lanes, T/rotation, code distance/failure
   budget, factory supply, logical cycle, decoder/reaction time, native deadline,
   and overlap. Every range must be measured, cited, or explicitly a target.
2. Report first-target stability, next-target transitions, runtime/quality pass
   share, and the Amdahl-style removal ceiling. Do not assign probabilities to
   scenarios without a defensible parameter distribution.
3. Produce at least one two-dimensional bottleneck phase diagram showing where
   the architecture recommendation changes under coupled improvements.
4. Complete at least one end-to-end component replacement case study on matched
   events, not a borrowed multiplier. Preferred options are topology-aware
   BOSS/S-SYNC/Cyclone movement, LSQCA area/access tradeoff, or a
   Pinball/reaction-time decoder attachment.
5. For QCCD, use direct QAOA and compiled Chem interaction graphs to bound
   shuttle/SWAP/recooling under locality-first and congestion-stressed policies.

Required artifacts: `joint_bottleneck_phase_map.json` and
`component_replacement_case_studies.json`, with invariant checks showing that
only named terms change.

Completion gate: the main architecture recommendation remains stable over a
clearly stated region, and at least one current HPCA/ISCA mechanism is consumed
by the inversion rather than merely cited.

### P0-E: Statistical Rigor and Corpus Representativeness

**Risk closed:** 3,552 configurations can be mistaken for 3,552 independent
applications, and raw-record medians can overweight ML or repeated grid points.

Required work:

1. Report `records`, `unique instances`, `independent seeds`, `subtypes`, and
   repeat trials separately.
2. Bootstrap by independent instance/seed, not by duplicate configuration row,
   and report confidence intervals for quality pass share, runtime ratios,
   crossover factors, and target stability.
3. Provide both family-specific results and a workload-balanced aggregate. Do
   not pool 2,048 ML rows with smaller families into an unweighted global claim.
4. Retain p10/median/p90 and outliers where distributions span orders of
   magnitude. State when a deployment-facing record is structural metadata
   rather than measured circuit quality.
5. Recheck representative timing variance; add repeats only for cases whose
   uncertainty can change a paper conclusion.

Required artifact: `statistical_robustness.json` with resampling unit, seed,
confidence level, weighting rule, and claim-level intervals.

Completion gate: every headline number has a visible denominator and either a
confidence interval or a deterministic-bound explanation.

### P0-F: HPCA Narrative, Figures, and Current Related Work

**Risk closed:** a broad, dense paper can hide its architecture answer and look
shallower than mechanism-specific HPCA work.

Required work:

1. Rewrite Abstract and Intro only after P0-A--E stabilize. Lead with the paired
   boundary, the two-stage inversion, and two or three robust architecture
   findings; remove any number that changes under the conservative envelope.
2. Make Figure 1 the problem only. Remove tiny first-target tags or move their
   meaning to the final architecture map.
3. Make the final target figure show, for each workload, quality status, eligible
   first resource, crossover/range, next resource, and removal ceiling. Use a
   distinct style for conditional execution bottlenecks.
4. Replace or compress low-information modality-share plots if the joint phase
   map or replacement case study delivers a stronger architecture result.
5. Add TraceQ, Pinball, Cyclone, S-SYNC, current causality-aware grouping/control,
   detailed reaction-time work, logical soft-information QEM, QFw, and
   postselected rotations to Intro/Related Work with exact contrasts.
6. Use one final architecture-takeaway box. Evaluation paragraphs follow
   `Figure shows -> quantitative result -> cause -> architecture action`.
7. Keep Perlmutter as the empirical substrate. Call 3,552 items records or
   configurations, and mention 256 GPUs only where it supports evidence capacity,
   not as implied QPU scale.
8. Recover the 11-page body by removing duplicated setup and weak figures, not
   by shrinking plot text or line spacing.

Completion gate: a skeptical architect can answer in one minute what to improve
now, how much improvement is required, when the target changes, and which claims
are conditional.

### P1: Promote Only When Needed

1. End-to-end QNN training under the same-input, finite-shot, preparation,
   grouping, and strong-native contract.
2. Hardware-backed noisy closed-loop traces or logical soft-information QEM
   only when raw decoder/measurement evidence is available.
3. Larger active-space VQE quality closure or stronger DMRG/tensor/block-Krylov
   natives only when they can be executed and paired honestly.
4. Energy/PPA only with compatible native power and physical-stack area/power
   evidence.
5. Additional large-GPU runs only when they close a named evidence gap above;
   raw scale or record count is not a contribution.

### Explicitly Deferred or Rejected

- **No invented QPU microarchitecture.** The architecture contribution is the
  critical-path inversion and target map.
- **No blanket SOTA-native claim or cosmetic HBM number.** CCSD(T) is a CPU
  path, and low utilization on small GPU ML cases can weaken the defense. Keep
  the executed frontier plus the adversarial roofline lower-deadline stress.
- **No logical-QEM experiment without decoder posterior traces.** Cite it and
  define the replacement contract. Do not turn a reported 100x logical-error
  reduction into a free shot multiplier.
- **No fabricated DMRG/tensor-network result.** Name stronger unexecuted natives
  as moving-frontier replacements. A stronger native only tightens the quantum
  boundary.
- **No cycle-accurate, PPA, energy, or tail-latency claim** without a compatible
  architecture and measured or validated traffic source.
- **No textbook M/M/1 or M/D/1 queue inserted without arrivals and service
  traces.** The audited dependency/serialization bounds are more honest than a
  precise-looking queue with invented traffic.
- **No borrowed BOSS, S-SYNC, LSQCA, ARTERY, or Qtenon multiplier.** Recompile
  compatible workload events or retain the mechanism as a replacement
  contract. Maximum, average, and topology-specific published gains are not
  universal hardware constants.
- **No recursive quality-cost extrapolation beyond measured ladders.** It may
  suggest orders-of-magnitude growth while silently assuming convergence that
  has not been observed.
- **No theoretical analog-crossbar peak as a measured native deadline.** A
  memristor or Ising accelerator enters only with same-input output quality and
  end-to-end timing. HeteroQNN is a hybrid quantum path, not a stronger purely
  classical native baseline. Generic 10x/100x native-deadline stresses already
  test the moving-target claim without pretending an unexecuted accelerator
  was measured.
- **No more node-hours for independent small-circuit repetitions.** New Slurm
  work must close a named evidence contract that cannot be answered offline.

## 8. Execution Order and Stop Gates

The packages are intentionally dependent. Prose and figure polish start only
after the numerical claims are frozen.

| Stage | Work | Exit condition | Compute policy |
| --- | --- | --- | --- |
| 0. Freeze checkpoint | Record the current PDF, claim table, audit outputs, artifact hashes, and dirty-worktree scope. | The pre-revision state can be reproduced and no user change is overwritten. | Offline only. |
| 1. Audit existing evidence | Execute P0-A's quality partition, P0-B's dependency coverage, and P0-E's independent-unit/statistical audit over existing records. | Quality eligibility, schedule provenance, denominators, and confidence intervals are explicit. | Offline first; no Slurm. |
| 2. Close measured gaps | Run only the representative finite-shot quality and schedule/trace cases that Stage 1 proves are absent. Start with one GPU, validate schema and trends, then use one bundled allocation if needed. | Each workload has a matched quality--shot point or is explicitly excluded from advantage. | Small smoke, then one bounded campaign; no speculative scale run. |
| 3. Close the FT contract | Execute P0-C using the conservative schedules from Stage 1/2: failure budgets, logical volume, case-specific distance, rotation supply, physical space, and decoder/reaction time. | Every physical summary has reliability and spatial provenance, or an unsupported flag. | Primarily offline resource estimation. |
| 4. Produce the architecture result | Execute P0-D's joint DSE and at least one matched published-mechanism replacement. | A phase map identifies first/next targets, crossover ranges, and removal ceilings under coupled assumptions. | Offline re-pricing first; compile/run only matched missing events. |
| 5. Freeze claims and rewrite | Keep only conclusions that survive Stages 1--4; then execute P0-F across Abstract, Intro, Design, Evaluation, Discussion, figures, and related work. | Every headline number resolves to an authoritative artifact and evidence level. | No new campaign unless a rewritten claim exposes a real missing contract. |
| 6. Submission gate | Rebuild from clean inputs, inspect the PDF, run every audit, enforce the page budget, and verify anonymized release artifacts. | All Section 14 boxes pass with no unresolved P0 claim. | No compute beyond deterministic regeneration. |

Dependency order is `P0-A/B/E -> targeted measurement -> P0-C -> P0-D ->
P0-F`. P0-A, P0-B, and P0-E may run in parallel. P0-D must consume the
quality-qualified records and conservative schedule/reliability contracts;
otherwise its phase boundaries are not publication results.

Stages 0--6 are complete. The numerical claim set is frozen around the
quality-first FT contract, joint phase transition, and matched LSQCA result.
The deterministic `make -B -C paper audit` chain rebuilds the paper and passes
all Section 14 gates. No new compute campaign is justified for a retained
claim in this submission state.

## 9. Evaluation Story

The revised evaluation should read as one causal argument, from an application
contract to a hardware decision:

| Subsection | Question closed | Required evidence | Figure role |
| --- | --- | --- | --- |
| A. Evaluation Setup and Contracts | What is one independent case, what is measured, and what is projected? | Same-input contract, natural-unit tolerance, native deadline, evidence levels, unique instances/seeds, and simulator/QPU separation. | Compact setup table; Perlmutter scaling is capacity evidence only. |
| B. Deployment-Facing Native Frontier | Does the conclusion survive credible native applications and a harder deadline? | ResNet/Pool-108, CCSD(T), MaxCut native methods, Krylov, and clearly labeled roofline stress. | Matched quality--runtime evidence and concise recovery-cost evidence. |
| C. Quality-Qualified Application Boundary | Which workloads already pass algorithmic quality, and what recovery costs work? | Controlled corpus, finite-shot quality, tolerance sweep, and measured depth/quality ladders. | One distribution or phase view that separates quality-pass from quality-fail records. |
| D. Trace-Aware Logical Lower Bound | After removing simulation, what irreducible logical work remains under realistic concurrency? | Aggregate, group-wave, and serial schedule bounds with coverage fractions. | Logical lower-bound range, not another simulator-speed plot. |
| E. Reliability-Constrained Physical Diagnosis | Under a complete FT contract, which hardware resource is first and when does it cross over? | Failure budget, case-specific distance, rotations, factory/space, decoder, and physical timing. | Numerical first-to-next target map with conditional cases visibly separated. |
| F. Joint Co-Design Sensitivity | Does the recommendation survive coupled changes, and can a published architecture mechanism move the boundary? | Joint DSE, removal ceilings, and one matched mechanism replacement. | A 2D bottleneck phase map plus one compact before/after mechanism result. |

This sequence is `native target -> quality eligibility -> logical demand -> FT
feasibility -> architecture action`. It avoids treating quality, execution, and
physical implementation as interchangeable evidence. Perlmutter's 1--256-GPU
throughput belongs in Setup as evidence-generation capacity; it is not an
architecture-scaling conclusion and should not displace the phase map.

Every result paragraph follows `Figure shows -> numerical result -> structural
cause -> architecture action`. Use at most one synthesized takeaway box near the
end of Evaluation. Avoid `Result.`/`Reason.` labels and repeated observation
boxes that merely restate captions.

Figure rules:

- Figure 1 states the paired application problem only.
- The Design figure shows the two-stage quality gate and critical-path
  inversion, including exclusion/conditional paths.
- Each Evaluation figure answers one distinct question in the table above.
- The final architecture figure must expose quality status, eligible first
  resource, crossover range, next resource, and removal ceiling without prose
  embedded inside the plot.
- Use a two-column figure only when coordinated panels need shared comparison;
  otherwise use a readable one-column figure. Never recover pages by shrinking
  labels, legends, or captions below normal paper text readability.

## 10. Claim and Baseline Rules

| Claim | Minimum evidence | Allowed wording |
| --- | --- | --- |
| Controlled measurement | Same input, timing, natural-unit quality, circuit metadata, independent-unit ID, and provenance | `Measured over controlled records`. |
| Quality-qualified hardware target | Quality pass plus matched finite shots, dependency schedule, native deadline, reliability budget, and physical envelope | `First projected application-level target under ...`. |
| Quality-failing physical timing | Measured quality failure plus explicit physical attachment | `Conditional execution lower bound`; never `first application target`. |
| Projection | Measured record, explicit parameters, uncertainty range, invariant audit, and evidence-level tag | `Projected lower-bound target` or `bounded scenario`. |
| Technology envelope | Compatible demand plus cited physical parameters | `Counterfactual execution envelope`, not a vendor forecast or modality winner. |
| Deployment advantage | Strong same-input native, matched quality, loading, groups/shots, routing, physical reliability, and tails | Not currently established. |

Native-baseline defense:

- Keep measured ResNet-18/Pool-108, CCSD(T), MILP/heuristics, and Krylov.
- Keep the roofline result as an unattainable lower-deadline stress, not a
  measured implementation or proof of device saturation.
- State that stronger domain-native methods move the target outward and can be
  substituted without changing the inversion.
- Admit analog, non-von-Neumann, and domain-specific accelerators only under the
  same-input, natural-unit-quality, end-to-end-time contract. Theoretical peak
  throughput is only a stress.
- Never claim global SOTA coverage, hardware saturation, or a current quantum
  win without corresponding evidence.

Corpus and number rules:

- Call 3,552 items `records` or `configurations`, not independent applications.
- Report the number of unique instances, seeds, and subtypes beside every
  percentage or aggregate.
- Do not combine measured simulator slowdown and projected QPU/native ratio on
  one unlabeled axis.
- Distinguish measured, modeled, stress, and future-replacement values in data,
  legends, captions, and prose.

## 11. Perlmutter and Execution Policy

Perlmutter is the empirical evidence engine: it enables exact quality closure,
broad paired records, compiled attachments, and demanding native deadlines. It
does not make simulator wall time a future-QPU estimate or GPU scaling a QPU
scaling result.

1. New Slurm work must close one named field in P0-A--D that cannot be recovered
   from existing artifacts.
2. Begin with the smallest representative smoke. If successful, bundle related
   cases into one bounded allocation instead of submitting one job per point.
3. Once logs show a healthy job making progress, do not cancel it because the
   scheduler estimate or elapsed time looks surprising.
4. Prefer offline re-pricing, resampling, and DSE over additional node-hours.
5. Promote a run only after raw output, JSON/CSV summary, Slurm accounting,
   manifest, figure, and audit agree.
6. Never modify unrelated `hr_*`, CP2K, QE, or other-project jobs and artifacts.
7. Submit QArchGauge GPU work to project `m5320` (`m5320_g` in Slurm), while
   CPU-only work remains on `m1248`.

Jobs 55885604, 55885607, and 55885608 reached terminal `TIMEOUT` states after
4,298/5,794/7,092 of 7,104 records at 4/8/16 GPUs. These censored runs are
retained as artifact-only evidence and are never extrapolated into completed
fixed-work elapsed times. The paper uses the completed 32--256-GPU direct
ladder plus the explicitly marked 1-GPU split-array anchor.

## 12. Validation

The following new audits are submission requirements, not optional analysis:

| Audit | Required output |
| --- | --- |
| `scripts/audit_quality_qualified_targets.py` | Quality partition, finite-shot/tolerance coverage, hardware-target eligibility, and exclusions. |
| `scripts/audit_dependency_schedule_coverage.py` | Ready-width provenance, schedule-mode coverage, fallback fractions, and target stability. |
| `scripts/audit_ft_reliability_budget.py` | Failure budget, logical volume, selected distance, factory/space, decoder demand, and unsupported cases. |
| `scripts/audit_statistical_robustness.py` | Independent resampling unit, CIs, workload weighting, and headline-number denominators. |
| `scripts/audit_joint_dse.py` | Parameter origins, phase boundaries, removal ceilings, and matched replacement invariants. |

These scripts are planned deliverables and must not be listed as passing until
they exist and complete successfully. The final deterministic rebuild includes:

```bash
source /etc/profile.d/zzz-lmod.sh
module load python/3.11-24.1.0
python scripts/audit_quality_qualified_targets.py
python scripts/audit_dependency_schedule_coverage.py
python scripts/audit_ft_reliability_budget.py
python scripts/audit_statistical_robustness.py
python scripts/audit_joint_dse.py
python scripts/audit_projection_invariants.py
python scripts/generate_paper_figures.py
make -B -C paper audit
pdftotext -layout paper/main.pdf /tmp/qsup_main.txt
```

Also inspect every page at final size in color and grayscale. Automated success
does not excuse clipped legends, overlapping labels, tiny text, unexplained
white space, inconsistent subfigure heights, or floats detached from the prose
that interprets them.

## 13. Authoritative Artifacts

Existing evidence remains authoritative until superseded by an audited file:

| Evidence | Path |
| --- | --- |
| Main controlled suite | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv` |
| Physical architecture DSE | `data/processed/perlmutter/physical_architecture_dse.json` |
| Projection scenarios and invariants | `data/processed/perlmutter/practical_suite_projection_scenarios.json`, `data/processed/perlmutter/projection_invariant_audit.json` |
| Direct quality-cost closures | `data/processed/perlmutter/qaoa_scale_depth_closure.json`, `data/processed/perlmutter/chem_active_space_pair_ucc_closure.json` |
| Compiled Chem attachments | `data/processed/perlmutter/chem_controlled_compiled_measurement_records.json`, `data/processed/perlmutter/chem_compiled_measurement_records.json` |
| QDK/Qualtran cross-checks | `data/processed/perlmutter/qdk_resource_estimator_qaoa_depth_crosscheck.json`, `data/processed/perlmutter/qualtran_resource_estimator_qaoa_crosscheck.json` |
| Platform and native envelopes | `data/processed/perlmutter/native_rotation_platform_envelopes.json`, `data/processed/perlmutter/deployment_scale_proxy.json` |
| Evidence/readiness audits | `data/processed/perlmutter/paper_evidence_audit.json`, `data/processed/perlmutter/submission_readiness_audit.json` |
| Artifact manifest | `data/processed/perlmutter/paper_artifact_manifest.json` |

The following P0 artifacts are authoritative because their audits pass:

| Evidence package | Planned path | Status |
| --- | --- | --- |
| Quality-qualified target map | `data/processed/perlmutter/quality_qualified_target_map.json` | PASS with 12 matched Sim records eligible at 10,000 shots; all other hardware claims excluded or conditional |
| Finite-shot quality closure | `data/processed/perlmutter/finite_shot_quality_sensitivity.json` | PASS at 1,000/10,000/100,000 shots with workload-specific scope flags |
| Dependency schedule coverage | `data/processed/perlmutter/dependency_schedule_coverage.json` | PASS for implemented static loops; adaptive claims excluded |
| FT reliability and space budget | `data/processed/perlmutter/ft_reliability_and_space_budget.json` | PASS with restricted application scope; 222 subtypes and QDK 100/100 distance cross-check |
| Joint bottleneck phase map | `data/processed/perlmutter/joint_bottleneck_phase_map.json` | PASS over 384 deterministic scenarios and 26,112 case points; 1--100x supply is a 12/12 factory-first region |
| Published-mechanism replacements | `data/processed/perlmutter/component_replacement_case_studies.json` | PASS for matched LSQCA logical events and conditional BOSS-compatible QCCD bounds |
| Statistical robustness | `data/processed/perlmutter/statistical_robustness.json` | PASS |

## 14. Strong-Accept Gate

No plan can guarantee acceptance. This plan aims to remove the strongest
technical reasons for rejection. The manuscript is `GO` only when all boxes
below are true; otherwise it remains `NO-GO` or the corresponding claim is
deleted.

- [x] **Identity:** Abstract through Conclusion consistently present an
  HPC-driven architecture inversion, not a simulator benchmark or new QPU.
- [x] **Quality eligibility:** hardware first-target claims use only records
  that pass the declared application quality gate at matched finite shots.
- [x] **Trace semantics:** the headline target survives a conservative,
  workload-valid dependency schedule; fallback coverage is visible.
- [x] **FT consistency:** logical error, case failure, code distance, shots,
  rotations, factory supply, physical space, and decoder timing form one
  auditable contract.
- [x] **Joint robustness:** the first/next recommendation and crossover are
  reported as stable regions under coupled assumptions, not one-factor bars.
- [x] **Architecture depth:** at least one current HPCA/ISCA mechanism is
  applied to matched workload events and re-inverted end to end.
- [x] **Statistics:** every headline percentage and median has an independent
  denominator, workload weighting rule, and CI or deterministic-bound reason.
- [x] **Native frontier:** executed baselines and the moving-frontier limitation
  are explicit; stresses are never presented as measured implementations.
- [x] **Current positioning:** benchmark, FT-estimation, trace/QEC, component,
  orchestration, and quality-mechanism neighbors are cited with exact contrasts.
- [x] **Architecture answer:** a reviewer can identify what to improve now, by
  how much, when the target changes, and which results are conditional.
- [x] **Presentation:** each figure has one role, remains readable at final
  column size, and is placed beside the paragraph that explains its cause and
  architectural implication.
- [x] **Reproducibility:** all P0 artifacts, scripts, manifests, and audits pass
  from a clean checkout; the body is at most 11 pages excluding references.

Residual limits stay explicit even after `GO`: no measured QPU trace, no
hardware-backed logical closed loop, no full deployment-scale VQE quality
closure, no cycle-accurate PPA/energy model, and no exhaustive domain-native
frontier. These limits are acceptable only because claims stop at the audited
boundary.

## 15. Goal Prompt

Copy the following prompt verbatim to start the implementation goal:

```text
/pscratch/sd/s/sgkim/Skim-Qsupreme에서 다음 목표를 생성하고 끝까지 수행해.

목표: QArchGauge를 HPCA 2027 strong-accept-ready 상태로 만든다. plan.md를
authoritative specification으로 사용하고, Section 7의 P0-A부터 P0-F까지를
Section 8의 의존성 순서대로 실제 구현, 실행, 검증, 논문 반영한다. 조언이나
계획에서 멈추지 말고 필요한 분석 스크립트, JSON/CSV artifact, figure, LaTeX,
README, audit를 완성한다.

성공 조건:
1. quality-pass records만 application-level hardware target에 사용하고,
   quality-failing timing은 conditional lower bound로 분리한다.
2. workload-valid dependency schedules와 conservative bound에서 target이
   유지되는지 검증한다.
3. finite shots, application failure budget, case-specific code distance,
   rotation supply, factory footprint, decoder/reaction time을 하나의 FT
   reliability contract로 연결한다.
4. coupled-parameter DSE와 최소 한 개의 matched published-mechanism
   replacement를 수행해 first target, crossover, next target, removal ceiling을
   수치화한다.
5. independent instance/seed 기준 CI와 workload-balanced 결과를 제공한다.
6. 그 결과가 고정된 뒤 Abstract, Intro, Design, Evaluation, Discussion,
   Related Work와 모든 figure를 HPCA 논리로 다시 정리한다.
7. reference 제외 본문 11페이지, 최종 크기 가독성, citation/style/evidence/
   projection/submission audit zero-error를 만족한다.

작업 규칙:
- 먼저 plan.md, 전체 paper source/PDF, authoritative artifacts, git diff를 읽고
  현재 checkpoint를 보존한다. 사용자의 기존 변경을 되돌리지 않는다.
- measured, modeled, stress, future replacement를 데이터와 문장에서 분리한다.
  결과, trace, multiplier, queue, hardware capability를 만들거나 빌려 쓰지 않는다.
- 현재성이 필요한 architecture/FT claim은 웹의 primary source로 검증한다.
- 기존 artifact의 offline audit/re-pricing을 먼저 하고, 증거가 실제로 없을 때만
  1-GPU smoke 후 관련 실험을 하나의 짧은 Slurm allocation으로 묶는다.
- 정상 진행 중인 job은 scheduler 예상시간 때문에 취소하지 않는다. hr_*, CP2K,
  QE 등 다른 프로젝트 job과 artifact는 절대 건드리지 않는다.
- 각 stage가 끝날 때 plan status와 authoritative artifact를 갱신하고 audit한다.
- P0를 모두 통과하거나 retained claim을 정직하게 축소할 때까지 계속한다.
  외부 데이터나 실행 상태 때문에 진짜 막힌 경우에만 blocker와 영향받는 claim을
  정확히 보고한다.
- commit과 push는 내가 별도로 요청할 때만 한다.
```
