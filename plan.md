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
| HPCA body budget | References start on page 12, so the current body is 11 pages before references |
| Main practical suite | 3,552 cases, 128 GPUs |
| 256-GPU fixed work | 3,552 cases in 261 seconds |
| 256-GPU larger-workload gate | 7,104 cases in 514 seconds |
| Scale-ladder debug gate | 48 larger/deeper cases on 1 node / 4 A100 GPUs; Slurm job 55708592 completed in 6 minutes 50 seconds with exit 0:0 and empty stderr logs |
| Medium scale-ladder gate | 180 Chem/Opt./Sim. cases on 4 nodes / 16 A100 GPUs; Slurm job 55710745 completed in 5 minutes 16 seconds with exit 0:0 and empty stderr logs |
| Large scale-ladder gate | 888 `large`-profile cases across ML/Chem/Opt./Sim. on 8 nodes / 32 A100 GPUs; Slurm job 55730074 completed in 12 minutes 45 seconds with exit 0:0 and empty stderr logs |
| Regular weak-scaling ladder | Completed 16/32/64-node `large` jobs 55731013, 55731014, and 55731015 with 1,776 / 3,552 / 7,104 `ok` cases |
| Regular strong-scaling ladder | Paper uses completed 16/32/64-node fixed-work `large` jobs 55731032, 55731033, and 55731034 with 7,104 `ok` cases each; completed 8-node / 32-GPU context job 55782768 adds a proportional 3,552-case half-suite point normalized only for Figure 6 context |
| Deployment-scale proxy boundary | Added as manuscript table plus JSON/CSV artifact; larger ML/Chem/Opt./Sim. extensions are scoped as proxy records, not full deployment-scale state-vector claims |
| ML production-native gate | 32 cases with PyTorch AMP CNN/MLP and XGBoost GPU-hist |
| ML profiling gate | Nsight Systems + dmon captured; Nsight Compute counters attempted and recorded as unavailable |
| Workload coverage | ML, chemistry, optimization, scientific simulation |
| Previous-paper logic/style | LaTeX style PASS; deep trace PASS; all section/role alignment checks PASS; design has one non-blocking length note in the JSON metrics |
| Evidence audit | PASS on current tracked evidence |
| Submission readiness | `SUBMISSION_READY`, warning count 0, no blocking errors |
| PDF readability spot check | PASS: readiness audit checks clean `QArchGauge` PDF text and Fig. 5/6 order; rendered contact sheets inspected |

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

## Latest Reject Diagnosis and Accept-Recovery Plan

The latest external assessment changed from accept-leaning to reject because the
core idea is strong but the trust boundary is not yet explicit enough. The
reviewer accepts the measurement/projection separation, artifact discipline, and
architecture-target framing. The rejection comes from whether the projected
frontier is credible, whether small workloads support the claimed architecture
insights, and whether readers can distinguish measured simulator slowdown from
future-QPU projected runtime.

In short, the review changed because the paper moved from being judged as a
promising idea to being judged as a top-tier systems/architecture submission.
The strengths still stand: same-input/same-quality comparison, measurement
versus projection separation, workload coverage, and auditable artifacts. The
reject pressure is about evidence boundaries: optimistic future-hardware knobs,
small problem sizes, simplified quality recovery, native-baseline ceilings, and
one confusing time-axis transition between measured cuQuantum slowdown and
projected QPU runtime.

| Reject reason | Why it matters | Accept-oriented fix |
| --- | --- | --- |
| Optimistic FT projection knobs | Defaults such as $d=25$, $1\,\mu$s cycle, $10^4$ effective shot lanes, and small serial decode/control can look like hidden assumptions that create the positive frontier. | State that the default is an optimistic lower-bound stack, add conservative/realistic/optimistic interpretation in text, and make sensitivity the main result rather than a side plot. |
| Sim. speedup inconsistency | Sim. needs 3,071$\times$ when measured as simulator application slowdown, but projected FT time is 0.03$\times$ native under the default stack. This can read as a contradiction. | Define two time axes early: measured `T_qsim/T_native` and projected `T_qhw/T_native`. Explain that Sim. flips only under the future-hardware model because it has one evaluation, low repetition, and hardware-aligned unitary evolution. |
| Scalar quality recovery | A single $R$ can look like free linear error mitigation, even though deeper ansatz, higher Trotter order, more shots, mitigation, or better encodings change runtime too. | Treat $R$ as a requirement axis, not a mechanism. Add workload-specific examples showing how quality recovery would move both quality and runtime in future experiments. |
| Small workload sizes | 4--7 qubits, ML features 4--10, and small Opt. graphs look toy-scale and can overfit conclusions to classically easy regimes. | Reframe claims as small-instance, strong-native, exact-instrumentation evidence. Do not claim deployment-scale quantum advantage. Add a concrete next-experiment ladder for larger Opt./Sim./Chem and tensor/approximate baselines. |
| Native baseline ceiling | Stronger native methods can move the native deadline and therefore the advantage frontier. | Keep the strong-native gate, explicitly call native baselines a moving target, and list domain-SOTA additions needed before any broad domain claim. |
| No hardware/noise validation | cuQuantum is instrumentation, but control/decoder/IO assumptions are not validated against hardware runs. | Cite physical QEC and resource-estimation data, bound claims to projections, and add optional small hardware/noise validation as future work rather than pretending it is already measured. |
| Artifact and presentation risk | Placeholders, caption ambiguity, and figure/axis wording can cause distrust even if data are valid. | Keep figure captions explicit: native deadline, projected total/native, quality-limited case fraction, and sensitivity assumptions. Run build plus evidence/style audits after every figure/text update. |

Priority order:

| Priority | Work item | Files | Done when |
| --- | --- | --- | --- |
| P0 | Clarify the two time axes and Sim. interpretation. | `paper/2.Background.tex`, `paper/4.Evaluation.tex` | A reviewer can no longer read 3,071$\times$ and 0.03$\times$ as contradictory. |
| P0 | Recast default FT parameters as optimistic lower-bound knobs. | `paper/3.Design.tex`, `paper/4.Evaluation.tex`, `paper/5.Discussion.tex` | The positive frontier is presented as conditional sensitivity, not a claim about current QPUs. |
| P0 | Define quality recovery as a requirement axis with workload-specific mechanisms. | `paper/2.Background.tex`, `paper/4.Evaluation.tex` | Text states that recovery mechanisms change depth, shots, evaluations, and native deadline comparisons. |
| P1 | Strengthen small-instance and native-baseline boundary. | `paper/4.Evaluation.tex`, `paper/5.Discussion.tex` | Claims are scoped to exact-instrumented small cases and strong auditable baselines. |
| P1 | Improve figure captions and table wording. | `paper/4.Evaluation.tex`, `scripts/generate_paper_figures.py` | Captions name assumptions and avoid ambiguous terms such as bare “deadline” or “pressure.” |
| P2 | Add larger follow-up experiments only after manuscript logic stabilizes. | `plan.md`, Slurm scripts | New runs are scheduled only if they answer a specific reviewer concern and do not burn node-hours for cosmetic scale. |

Experiment roadmap before the next submission:

| Tier | Experiment | Node-hour policy | Purpose |
| --- | --- | --- | --- |
| Immediate, no srun | Conservative projection sweep over existing JSON/CSV metadata. | Offline only. | Shows whether conclusions survive lower shot lanes and larger serial-control floors. |
| Immediate, no srun | Native-baseline sensitivity table from existing strong-native, ML production-native, and Chem/Sim gates. | Offline only. | Shows how much stronger native paths move the frontier. |
| Low-cost validation | 1-GPU debug smoke for any modified workload generator. | Only after code changes. | Ensures scripts still run before larger jobs. |
| Targeted scale extension | Opt. and Sim. modest-size extension within state-vector feasibility. | Submit only if the manuscript needs new evidence beyond existing 3,552 cases. | Addresses small-instance concern without pretending 64-qubit state-vector simulation is feasible. |
| Long-term | Tensor-network/approximate or hardware/noise-backed validation. | Separate campaign. | Moves from exact small-instance instrumentation toward domain-scale claims. |

## Latest Positive Review and Accept-Contingency Plan

The newest review is much more favorable. It says the core contribution is
valuable: \SystemName separates measured simulator execution from projected
future-QPU execution, keeps same-input/same-quality records, maps workload
behavior to architecture levers, and provides auditable Perlmutter evidence. The
review's final recommendation is effectively **accept if the paper tightens the
remaining trust boundaries**. The risk is not that the idea is unclear; the risk
is that a skeptical architecture reviewer may still ask whether the current
frontier survives stronger native baselines, less optimistic FT stacks, and
non-free quality recovery.

The important distinction from the previous reject-style reviews is tone. This
review accepts the framework and asks for stronger triangulation. Therefore the
next response should not over-expand the paper or burn node-hours blindly. It
should add targeted evidence and definitions that make the current claims harder
to dismiss.

| New review issue | Why it matters | Best response |
| --- | --- | --- |
| Small state-vector-executable workloads | 4--7 qubits, small active spaces, shallow QAOA/VQC, and digits/PCA may not extrapolate to deployment-scale architecture behavior. | Keep claims explicitly lower-bound and small-instance. Add a concise scale ladder: exact state-vector now, tensor/approximate or domain solvers next, hardware/noise validation later. Do not claim domain-scale advantage. |
| Optimistic FT defaults | $d=25$, $1\,\mu$s cycle, $10^4$ useful shot lanes, and 55 $\mu$s serial decode/control can look hand-picked. | Add or strengthen a triangulation paragraph/table against at least two independent FT/resource-estimation assumptions: current optimistic stack, conservative shot/control stack, and an Azure/resource-estimator-style alternative. |
| Additive execution model hides couplings | Real FTQC has lattice-surgery routing, magic-state factory concurrency, feedforward, decoder throughput, and layout contention that do not always add independently. | Add a limitation/model-variant paragraph: current model is first-order additive; contention enters by changing $T_{\mathrm{route}}$, $T_{\mathrm{ms}}$, $T_{\mathrm{decode}}$, $P_{\mathrm{shots}}^{\mathrm{eff}}$, or by using a conservative serial-control scenario. |
| Abstract quality recovery $R$ | Reviewers may read $R$ as free error mitigation. | Treat $R$ as a requirement axis and add cost-quality examples: deeper ansatz for Chem, higher Trotter order for Sim., larger kernel/feature dimension for ML, deeper QAOA/search for Opt. The ideal fix is a small offline sensitivity curve using existing metadata, not a large srun. |
| Native baselines not final SOTA | Stronger ML, Opt., Chem., and Sim. native implementations can move deadlines. | Add a "moving-native-frontier" table: current implemented strongest baseline, plausible stronger baseline, expected frontier shift, and whether existing evidence already bounds it. New srun only for one high-impact baseline if cheap. |
| Opt. native baseline pressure | Tuned MILP/metaheuristics may beat exact/greedy/local-search/SA choices on the measured graphs or larger variants. | First do an offline check for available scipy/networkx/OR-Tools-style MILP or stronger local search on existing graphs. If missing dependencies or runtime is large, mark as follow-up and avoid broad claims. |
| Sim. native baseline pressure | Projected Sim. runtime below native at small qubits could mean the native Krylov/dense implementation is weak. | Add details on native libraries/data structures/precision. If feasible, run a low-cost tuned sparse/block-Krylov or tensor-network smoke on existing Sim. cases; otherwise frame Sim. as a conditional signal. |
| D1/D2/Dm and measurement grouping unclear | Hardware projection depends on how depths, Pauli term measurements, grouping, and repeated evaluations are counted. | Add a compact definition table in Design or Evaluation Setup: how each workload computes 1Q/2Q/measurement depths, $N_{\mathrm{eval}}$, Pauli terms, grouping/commutation assumptions, and shots. |
| VQE/QAOA parameter fairness | Shallow ansatz/search choices may artificially hurt quantum quality. | Add exact parameter-grid/optimizer details and state that richer ansatz/search changes both quality and runtime. Optional small experiment: one deeper QAOA/VQE setting on a tiny subset to show direction. |
| Missing related-work triangulation | Need stronger link to Hamiltonian-simulation resource studies, analog/digital simulators, LDPC decoders, and multi-factory FT projections. | Expand Related Work or Discussion with 1--2 tight paragraphs and citations; avoid bloating Evaluation. |
| Artifact release | Reviewer asks whether JSON/CSV/code/scripts will be released. | Make artifact promise precise in README/Discussion: release JSON/CSV summaries, figure scripts, audits, Slurm configs, and projection scripts, with anonymized paths where needed. |

Priority for converting this review into a stronger accept:

| Priority | Action | Cost | Target files | Done when |
| --- | --- | --- | --- | --- |
| P0 | Add D1/D2/Dm, $N_{\mathrm{eval}}$, shot, and measurement-grouping definitions. | Manuscript only | `paper/3.Design.tex`, `paper/4.Evaluation.tex` | A reader can reproduce how circuit metadata enters $T_{\mathrm{qhw}}$. |
| P0 | Add FT/resource-estimator triangulation text. | Manuscript/offline only | `paper/3.Design.tex`, `paper/5.Discussion.tex`, `paper/references.bib` | Defaults read as one point in a sensitivity space, not a hidden claim. |
| P0 | Add native-frontier stress table or paragraph. | Manuscript/offline first | `paper/4.Evaluation.tex`, `paper/5.Discussion.tex` | Each workload has current native, plausible stronger native, and expected effect. |
| P1 | Bind $R$ to workload-specific cost-quality mechanisms. | Manuscript/offline first | `paper/4.Evaluation.tex` | Reviewers cannot interpret recovery as free mitigation. |
| P1 | Add or cite one stronger native comparator per workload if cheap. | Low-cost scripts; srun only if needed | `scripts/`, `data/processed/perlmutter/` | Existing cases are re-scored or a small smoke run completes; node-hours are not burned speculatively. |
| P1 | Clarify VQE/QAOA search grids and fairness. | Manuscript only unless subset run chosen | `paper/4.Evaluation.tex` | Parameter choices are auditable and scoped. |
| P2 | Add tensor-network/analog-digital/LDPC/multi-factory related-work triangulation. | Manuscript only | `paper/5.RelatedWork.tex`, `paper/5.Discussion.tex` | Related work covers practical advantage modeling beyond cuQuantum/benchmarks. |
| P2 | Strengthen artifact-release statement. | README/manuscript only | `README.md`, `paper/README.md`, `paper/5.Discussion.tex` | Artifact scope is explicit and reviewer can see what will be released. |

### Srun Decision Matrix for the Latest Review

The review does not imply that every weakness should be fixed with a large
Slurm campaign. Some issues are projection/modeling issues, while others need a
small amount of new execution to show that trends survive beyond toy settings.
The plan is to separate them before spending node-hours.

| Review concern | Does it need `srun`? | First action | Escalation rule |
| --- | --- | --- | --- |
| Small problem sizes: 4--7 qubits, small active spaces, shallow QAOA/VQE/VQC | **Yes, but staged.** This is the main place where real execution helps. | Run a scale ladder, not a 64-node job first: 1-GPU and 4-GPU debug subsets for larger/deeper cases. | Escalate to 8--32 GPUs only after the debug subset is clean. Use 64+ GPUs only if the medium run produces a figure the paper needs. |
| FT projection diversity | **No immediate `srun`.** | Recompute projections offline from existing JSON/CSV metadata under optimistic, conservative, Azure/resource-estimator-like, and future-LDPC-like assumptions. | No large run is needed unless new metadata fields are missing. |
| Quality recovery $R$ | **Usually no; targeted small runs are useful.** | Treat $R$ as a requirement axis in the paper. Bind it to cost-quality examples from existing metadata where possible: Chem. ansatz/optimizer depth, Sim. Trotter order/steps, Opt. QAOA depth, and ML feature/layer size. | Run 10--30 representative cases per workload only if the paper needs empirical quality-cost curves. |
| Stronger native baselines | **Sometimes.** | Try offline/local rescoring first: stronger Opt. local search/SA tuning/MILP/OR-Tools, tuned Sim. Krylov/block-Krylov/tensor-style checks, Chem. reference variants, and existing ML PyTorch/XGBoost production-native candidates. ML is lower priority because that gate already exists. | Use a small `srun` only for a high-impact native comparator that cannot run locally. Do not launch a full suite just to say "stronger native was tried." |
| Deployment-scale claim risk | **Not directly solvable with state-vector `srun`.** | Scope claims to exact, auditable, small-to-medium instrumentation and present state-vector scaling as a trend ladder. | Larger exact simulation stops when exponential state memory dominates. Deployment-scale claims require tensor/approximate simulators, domain solvers, or hardware/noise validation as future work. |

Concrete scale-ladder candidates:

| Workload family | Scale knob | Minimal smoke | Medium evidence target | What it answers |
| --- | --- | --- | --- | --- |
| ML-QNN/VQC and ML-QKernel | non-digits or larger native ML baseline, feature dimension, PCA dimension, ansatz depth, circuit layers, training/evaluation count | 10--30 cases on 1 GPU | 4--8 GPUs if runtime is stable | Whether ML conclusions are caused by tiny digits/PCA settings or by repeated circuit evaluation and quality/runtime tradeoffs. |
| Chem-VQE | molecule/active-space size, ansatz depth, optimizer steps, Pauli-term grouping | H2/LiH/H2O subset on 1 GPU | 4--16 GPUs for deeper selected variants | Whether quality gaps come from shallow ansatz/measurement cost rather than only from simulator runtime. |
| Opt-QAOA | graph size, graph density, QAOA depth $p$, search budget | small graph ladder on 1 GPU | 4--16 GPUs for selected graph/depth grid | Whether the architecture target changes as QAOA depth and repeated objective evaluation increase. |
| Sim-Ham. | qubit count, Hamiltonian sparsity, Trotter steps/order, observable count | qubit/Trotter subset on 1 GPU | 4--32 GPUs if memory permits | Whether the apparent Sim. advantage is robust or caused by a weak/small native Hamiltonian baseline. |

Execution order before any expensive job:

1. **No-srun pass:** generate projection-diversity plots/tables and moving-native-frontier sensitivity from current artifacts.
2. **Small srun pass:** run 1-GPU and 4-GPU debug subsets for the four scale ladders above. The target is correctness, metadata completeness, and whether figure trends change.
3. **Medium srun pass:** run 8--32 GPU subsets only for the workloads whose small pass changes the story or produces a clear HPCA-relevant figure.
4. **Large srun pass:** use 64+ GPUs only after the exact figure and paper claim are known. Once a job is submitted and logs show progress, do not cancel it just because wall time is longer than a scheduler estimate; monitor with `squeue` and task logs unless there is a real failure.

Implementation status:

| Item | Status | Evidence |
| --- | --- | --- |
| No-srun projection diversity | Implemented. Existing 3,552-case metadata is re-projected under conservative surface-code, resource-estimator-like, default optimistic, LDPC/future-like, and aggressive batched scenarios. | `scripts/summarize_projection_scenarios.py`, `data/processed/perlmutter/practical_suite_projection_scenarios.json`, `paper/figures/ft_shot_sensitivity.pdf` |
| Scale-ladder debug profile | Completed as Slurm job 55708592. The run executed 48 cases: 16 ML, 16 Chem, 8 Opt., and 8 Sim. cases. Median required speedups were 93,245.3x for ML, 83,347.0x for Chem, 1,373,786.6x for Opt., and 41,687.0x for Sim. | `data/processed/perlmutter/practical_suite_55708592_scale_1n_4g_summary.json`, `data/processed/perlmutter/practical_suite_55708592_scale_1n_4g_summary.csv`, `logs/qsup-prac-scale-55708592.out` |
| Medium accept-profile scale ladder | Completed as Slurm job 55710745. The run executed 180 cases on 4 nodes / 16 GPUs with 180 `ok` statuses: 104 Chem, 16 Opt., and 60 Sim. cases. Median required speedups were 69,077.5x for Chem, 1,290,038.8x for Opt., and 10,902.8x for Sim. | `data/processed/perlmutter/practical_suite_55710745_scale_4n_16g_summary.json`, `data/processed/perlmutter/practical_suite_55710745_scale_4n_16g_summary.csv`, `logs/qsup-prac-scale-55710745.out` |
| Large 8-node scale ladder | Completed as Slurm job 55730074. The run executed 888 cases on 8 nodes / 32 GPUs with 888 `ok` statuses: 512 ML, 56 Chem, 192 Opt., and 128 Sim. cases. Median required speedups were 16,399.0x for ML, 144,156.8x for Chem, 939,212.5x for Opt., and 18,944.9x for Sim. | `data/processed/perlmutter/practical_suite_55730074_scale_8n_32g_summary.json`, `data/processed/perlmutter/practical_suite_55730074_scale_8n_32g_summary.csv`, `logs/qsup-prac-scale-55730074.out` |
| Regular weak-scaling ladder | Completed in `gpu_regular`: 55731013 used 16 nodes / 64 GPUs / 1,776 cases in 9 minutes 22 seconds; 55731014 used 32 nodes / 128 GPUs / 3,552 cases in 6 minutes 59 seconds; 55731015 used 64 nodes / 256 GPUs / 7,104 cases in 9 minutes 36 seconds. All cases were `ok`; the only nonempty stderr was a benign NERSC pymon `FutureWarning`. | `data/processed/perlmutter/practical_suite_55731013_scale_16n_64g_summary.json`, `data/processed/perlmutter/practical_suite_55731014_scale_32n_128g_summary.json`, `data/processed/perlmutter/practical_suite_55731015_scale_64n_256g_summary.json` |
| Regular strong-scaling ladder | Completed in `gpu_regular`: 55731032 used 16 nodes / 64 GPUs / 7,104 fixed cases in 28 minutes 33 seconds; 55731033 used 32 nodes / 128 GPUs / 7,104 fixed cases in 15 minutes 54 seconds; 55731034 used 64 nodes / 256 GPUs / 7,104 fixed cases in 6 minutes 58 seconds. The 8-node / 32-GPU context job 55782768 completed the proportional 3,552-case half suite in 33 minutes 54 seconds with exit 0:0 and is shown as a hollow normalized context point, not as a direct fixed-work anchor. | `data/processed/perlmutter/practical_suite_review_strong_8n_32g_7104_20260711021411_summary.json`, `data/processed/perlmutter/practical_suite_55731032_scale_16n_64g_summary.json`, `data/processed/perlmutter/practical_suite_55731033_scale_32n_128g_summary.json`, `data/processed/perlmutter/practical_suite_55731034_scale_64n_256g_summary.json` |
| Recommended next small/medium run | Do not submit another run until these scaling results are mapped into paper figures and the reviewer-response narrative. | Next action is figure/table generation and manuscript integration, not more node-hours. |

Recommended next step: do **not** submit a new large Slurm campaign first. Start
with the no-srun pass and one small debug ladder. Then pick at most one or two
medium campaigns that directly answer a reviewer concern, such as larger/deeper
Opt., Sim., or Chem. cases.

## Review Checkpoint Ledger

The appended reviews are consolidated into checkpoints rather than preserved as
raw rebuttal text. Each checkpoint should strengthen the manuscript narrative
without turning the paper into a point-by-point response.

| ID | Checkpoint | Manuscript-level action | Current status |
| --- | --- | --- | --- |
| C1 | HPCA framing and prior-paper style | Keep the paper architecture-facing: design figures before procedures, evaluation figures before interpretation, and observation boxes for synthesized lessons. | Reflected through `paper/3.Design.tex`, `paper/4.Evaluation.tex`, and previous-paper audits. |
| C2 | Projection model physicality | Decompose `T_error`, bound effective shot parallelism, and state how surface-code distance, cycle time, decoder latency, magic-state throughput, control, data loading, and queueing plug into the same frontier. | Reflected in Design plus Fig. 14's concrete FT-stack sensitivity. |
| C3 | Shot parallelism and hybrid-loop limits | Treat `P_shots` as a bounded system resource and make QNN/QAOA host-device iteration overhead visible through metadata and prose. | Reflected through bounded `P_shots` prose, serial decoder/control terms, and host-orchestration profiling. |
| C4 | Native baseline strength | State the strongest implemented auditable baselines, show how stronger native paths move thresholds, and explicitly avoid claiming final domain SOTA. | Reflected through strong-native, ML production-native, baseline-boundary, Discussion, and Related Work text. |
| C5 | Simulator versus future hardware | Make clear that cuQuantum measures the circuit application path and metadata; projected hardware latency is not state-vector runtime. | Reflected in Design/Evaluation by separating simulator instrumentation from logical-time normalization. |
| C6 | Long-tail and tolerance sensitivity | Do not rely only on medians. Show or describe p90/max threshold pressure, tolerance sensitivity, and why some tails are native-fast or quality-limited. | Reflected through tail-pressure, tolerance-sensitivity, advantage-frontier, and FT/shot-sensitivity figures. |
| C7 | Scaling plateau explanation | Explain 128--256 GPU strong-scaling plateau as independent-case task granularity and per-case floor, not distributed single-circuit synchronization. | Reflected; keep weak and strong scaling separated. |
| C8 | Algorithmic flexibility | Avoid overclaiming fixed QAOA/VQC grids as final algorithms; explain the quality-vs-depth/evaluation tradeoff for richer ansatz and training. | Reflected in taxonomy, hardware projection, and Discussion as quality-vs-depth/evaluation tradeoff language. |
| C9 | Artifact credibility | Keep raw JSON/CSV/accounting artifacts, figure generation, and readiness audits connected to claims. | Reflected through manifest, evidence audit, and submission-readiness audit. |
| C10 | ML native baseline ceiling | Add same-input production-style ML native candidates and report whether they change the threshold. | Completed with 32-case PyTorch AMP CNN/MLP + XGBoost GPU-hist gate; combined median threshold is 8,601.6x and production-only median threshold is 49.3x. |
| C11 | Native hardware utilization proof | Do not claim Tensor Core or memory-bandwidth saturation without evidence; collect profiler evidence where possible. | Completed as a bounded claim: Nsight Systems captured tensor-family kernels, dmon shows low SM utilization, and Nsight Compute counter failure is recorded rather than converted into a saturation claim. |
| C12 | Scaling plateau profiling | Quantify whether small-case GPU work is kernel-bound or orchestration-bound, and connect that to the 128--256 GPU plateau without overclaiming. | Completed with a representative profiling gate: GPU kernels are 0.8% of the profiled run and host orchestration is 99.2%; no full 256-GPU Gantt trace is claimed. |
| C13 | Physical speed axis readability | Put effective quantum execution time on the Figure 13 secondary x-axis so $10^4$--$10^6\times$ reads as time, not only a dimensionless speedup. | Reflected in regenerated Figure 13 and caption. |
| C14 | Energy and power projection | Extend the future-hardware frontier with parameterized native GPU energy and quantum decoder/fridge/control energy terms; do not instantiate with unmeasured power values. | Reflected in Discussion as a parameterized energy model. |
| C15 | Concrete FT and shot sensitivity | Instantiate a stylized FT stack for the measured metadata and sweep effective shot parallelism while keeping decoder/control terms serial. | Reflected in Figure 14 and Evaluation text; this prevents the seven-second simulator floor from being read as a logical-gate budget. |
| C16 | External-validity boundary | State that small qubit counts, digits inputs, active spaces, fixed QAOA/VQC grids, and non-SOTA domain baselines bound the claims. | Reflected in Discussion and Related Work as moving-frontier language instead of final-domain-record language. |
| C17 | Low-end scaling visibility | Do not hide smaller GPU runs; show them as context when conditions differ and label any normalization explicitly. | Reflected in Fig. 5 as a 1--256 GPU weak-scaling ladder and in Fig. 6 as a 32-GPU hollow half-suite context point plus 64/128/256 direct fixed-work anchors. |

## Validation Commands

```bash
make -B -C paper
python3 scripts/audit_previous_paper_alignment.py
python3 scripts/audit_previous_paper_deep_trace.py
python3 scripts/audit_previous_paper_style.py
python3 scripts/audit_paper_evidence.py
python3 scripts/audit_submission_readiness.py
pdftotext -layout paper/main.pdf /tmp/qsup_main.txt
```

Expected result:

```text
paper/main.pdf: builds successfully
LaTeX log: no undefined references/citations and no overfull hboxes
previous-paper alignment: TRACKED_WITH_KNOWN_GAPS status only because Design is shorter than the AURORA-Q word-count heuristic; all role/shape checks PASS
previous-paper deep trace: PASS
previous-paper style audit: PASS
paper evidence audit: PASS
submission readiness: SUBMISSION_READY, warning_count 0, references_start_page 12
PDF text/readability spot check: `pdf_text_readability` PASS; no `QA RCH`/`QARCH` extraction artifacts; Fig. 5 appears before Fig. 6; rendered contact sheets show no major text overlap
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
| PDF readability renders | `/tmp/qsup_render2/contact_01_06.png`, `/tmp/qsup_render2/contact_07_12.png`, `/tmp/qsup_render2/contact_13_14.png` |
| Main 128-GPU summary | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json` |
| 256-GPU fixed-work summary | `data/processed/perlmutter/practical_suite_strongscale_64node_largefull_c0c255_20260705024742_summary.json` |
| 256-GPU larger-workload summary | `data/processed/perlmutter/practical_suite_strongnative_64node_large256c0c255_20260705024742_summary.json` |
| Scale-ladder debug summary | `data/processed/perlmutter/practical_suite_55708592_scale_1n_4g_summary.json` |
| Medium scale-ladder summary | `data/processed/perlmutter/practical_suite_55710745_scale_4n_16g_summary.json` |
| Large scale-ladder summary | `data/processed/perlmutter/practical_suite_55730074_scale_8n_32g_summary.json` |
| Weak-scaling 16-node summary | `data/processed/perlmutter/practical_suite_55731013_scale_16n_64g_summary.json` |
| Weak-scaling 32-node summary | `data/processed/perlmutter/practical_suite_55731014_scale_32n_128g_summary.json` |
| Weak-scaling 64-node summary | `data/processed/perlmutter/practical_suite_55731015_scale_64n_256g_summary.json` |
| Strong-scaling 8-node context | `data/processed/perlmutter/practical_suite_review_strong_8n_32g_7104_20260711021411_summary.json` |
| Strong-scaling 16-node summary | `data/processed/perlmutter/practical_suite_55731032_scale_16n_64g_summary.json` |
| Strong-scaling 32-node summary | `data/processed/perlmutter/practical_suite_55731033_scale_32n_128g_summary.json` |
| Strong-scaling 64-node summary | `data/processed/perlmutter/practical_suite_55731034_scale_64n_256g_summary.json` |
| Deployment-scale proxy boundary | `data/processed/perlmutter/deployment_scale_proxy.json`, `data/processed/perlmutter/deployment_scale_proxy.csv` |
| ML production-native gate | `data/processed/perlmutter/ml_strong_native_gate_latest.json` |
| ML profiling gate | `data/processed/perlmutter/ml_strong_native_profile_latest.json` |
| Advantage projection | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json` |
| Projection scenario sweep | `data/processed/perlmutter/practical_suite_projection_scenarios.json` |

## Remaining Paper Work

The main P0 interpretation fixes are reflected in the manuscript: the two
runtime axes are separated, the default FT stack is framed as an optimistic
lower-bound projection, quality recovery is described as a requirement axis,
small-instance scope is stated, and conservative shot/control sensitivity is in
the evaluation. The current PDF builds cleanly with references starting on page
12, no undefined references/citations, no overfull hboxes, and submission
readiness status `SUBMISSION_READY`. The PDF text/readability spot check also
passes after replacing the small-caps system-name macro with plain
`QArchGauge`, changing the Design section heading to avoid extraction artifacts,
and forcing the scaling figures to appear in Figure 5 then Figure 6 order.

Before submission, the remaining work is:

1. Replace the HPCA title-page `NaN` with the real submission number once it is
   assigned.
2. Recheck the final HPCA 2027 template/instructions immediately before upload;
   the current official page requires 11 pages before references, minimum 10pt
   font, 12pt leading, all-author references, page numbers, double-blind
   content, and an AI-use appendix.
3. Decide whether to expand Design substantially or leave the remaining
   previous-paper word-count note as a conservative length heuristic; all
   section/role checks, style audit, and deep-trace audit pass.
4. Launch new Slurm experiments only if a specific reviewer-risk requires new
   evidence. The current rejection pressure is primarily model trust and scope,
   not raw case count.

## Integrated SOSP-style Review Response

The latest external review was folded into the checkpoint ledger rather than
kept as raw review text. The concrete manuscript response is:

| Review concern | Paper response |
| --- | --- |
| `R`, `T_error`, and `P_shots` look too symbolic. | Added a concrete FT-stack and shot-parallelism sensitivity figure using measured gate/evaluation metadata, $d=25$, $\tau_c=1\,\mu$s, decoder latency, and residual control/queue overhead. |
| Seven-second simulator floor may be misread as logical time. | Evaluation now states that the speed axis is a normalization target, not a scaled Python/cuQuantum runtime; Fig. 14 keeps decoder/control overhead serial. |
| Small qubits and toy-scale inputs limit external validity. | Discussion now states that 4--16 qubit measurements, digits, fixed QAOA/VQC grids, and small active spaces are not deployment-scale extrapolations. |
| Domain-SOTA native baselines could move thresholds. | Discussion and Related Work explicitly name CNN/ResNet, boosted trees, tuned MILP/heuristics, tensor networks, projector QMC, and CCSD(T)-class references as moving the frontier rightward. |
| Artifact release and re-analysis should be clear. | The manifest, JSON/CSV summaries, Slurm configs, figure scripts, and audits remain connected through `paper_artifact_manifest.json` and `audit_paper_evidence.py`. |

This leaves one operational submission item and one conservative manuscript note:
replace the placeholder submission number after HotCRP registration, and decide
whether the Design section should be expanded beyond the current concise
framework description. No new srun is needed for the current manuscript fixes
unless the next revision chooses to add larger Opt./Sim./Chem scale evidence or
stronger domain-SOTA native baselines.
