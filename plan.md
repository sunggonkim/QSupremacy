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
| Regular strong-scaling ladder | Paper uses completed 16/32/64-node fixed-work `large` jobs 55731032, 55731033, and 55731034 with 7,104 `ok` cases each; optional 8-node / 32-GPU fixed-work extension job 55792240 is pending |
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
| Regular strong-scaling ladder | Completed in `gpu_regular`: 55731032 used 16 nodes / 64 GPUs / 7,104 fixed cases in 28 minutes 33 seconds; 55731033 used 32 nodes / 128 GPUs / 7,104 fixed cases in 15 minutes 54 seconds; 55731034 used 64 nodes / 256 GPUs / 7,104 fixed cases in 6 minutes 58 seconds. All cases were `ok`. | `data/processed/perlmutter/practical_suite_55731032_scale_16n_64g_summary.json`, `data/processed/perlmutter/practical_suite_55731033_scale_32n_128g_summary.json`, `data/processed/perlmutter/practical_suite_55731034_scale_64n_256g_summary.json` |
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
| Strong-scaling 8-node direct extension | Optional pending Slurm job 55792240; expected artifact `data/processed/perlmutter/practical_suite_direct32_strong_8n_32g_7104_20260711082639_summary.json` |
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







This paper proposes QArchGauge, a measurement-and-projection framework that turns same-input comparisons between native HPC applications and quantum-circuit application paths into concrete architecture targets for practical quantum advantage. The system records native runtime and quality, quantum runtime and circuit metadata (gates, shots, repeated evaluations), and then projects a break-even frontier over logical-operation speed, shot parallelism, decode/control overhead, and quality-gap recovery under a parametrized future hardware model. The authors evaluate 160 controlled ML cases and a 3,552-case practical suite (ML, Chemistry, Optimization, Simulation) on up to 256 GPUs, demonstrating how vague “quantum speedup” claims can be reframed as workload-specific hardware requirements.

Strengths
Technical novelty and innovation

Treats “practical quantum advantage” as an application-level, same-input/same-quality boundary rather than a kernel or simulator throughput metric.
Separates measurement (state-vector simulator as instrumentation) from projection (explicit logical ops, shot lanes, decode/control) with an auditable, per-case record.
Introduces a multi-axis frontier (speed, shots, overhead, quality recovery) and an “architecture pressure map” that pinpoints the most effective lever for future QPU designs.
Bridges HPC-native baselines and quantum-circuit paths with a principled “native deadline” framing that keeps advantage claims honest.
Experimental rigor and validation

Large-scale evidence collection: 3,552 practical cases plus 160 controlled ML cases; weak and strong scaling runs across 64–256 GPUs; provenance via Slurm/GPU metadata and JSON artifacts.
Explicit runtime-quality decoupling, quality tolerances per workload, and careful articulation that all results are lower-bound projections rather than claims of current advantage.
Sensitivity analyses over quality-recovery requirements and hardware-stack parameters (shot parallelism, control/decoder floors) to test robustness of conclusions.
Clarity of presentation

Clear statement of the “checklist” for an advantage claim (same input, best native, explicit hardware terms, quality target).
Distinguishes measured slowdown (simulator) from projected hardware runtime, avoiding the common pitfall of conflating simulator speed with application advantage.
Intuitive figures (landscape plots, bottleneck shares, pressure maps) that make the boundary and active constraints visible.
Significance of contributions

Provides a practical methodology the systems community can adopt to convert today’s quantum-circuit evidence into tomorrow’s architecture targets.
Helps de-risk roadmap discussions by quantifying how much improvement, and in what subsystem (gates vs shots vs control vs quality), is needed for specific workloads.
Offers a unifying lens to connect benchmark suites, resource estimators, and HPC–QPU runtime integration work.
Weaknesses
Technical limitations or concerns

The projection model relies on optimistic defaults (e.g., d=25 surface-code-like stack, t1/t2/measurement times, Pshots=10^4, small decode/control latencies) that may substantially understate the true requirements; justification and calibration against multiple independent resource estimators are limited.
The “quality recovery” axis (R) is treated as a requirement parameter without modeling the cost of achieving recovery (deeper circuits, more Pauli terms/shots, better ansätze/encodings), potentially overstating feasible frontiers.
Experimental gaps or methodological issues

Problem scales are small (typically ≤12 qubits; shallow circuits) and datasets are modest (e.g., PCA-reduced digits), which weakens claims about leadership-scale applicability even if the framework itself is scale-agnostic.
Native baselines, while stronger than toy references, still omit many state-of-the-art classical solvers for the target classes (e.g., tuned MILP/metaheuristics for MaxCut, tensor-network and QMC families for simulation/chemistry, and stronger ML architectures). The paper acknowledges this but relies on future work.
Quality tolerances (e.g., accuracy loss ≤0.02, energy error ≤0.01, ratio loss ≤0.02) are chosen but not deeply justified with domain significance or sensitivity shown to alternate tolerances.
Clarity or presentation issues

Some figures and tables contain transcription artifacts, undefined symbols, or shorthand (e.g., “checkmark symbol,” unlabeled figure segments), making it harder to audit exact numeric assumptions.
The mapping from code distance/cycle time to Pshots and Tdecode/Tctrl is described conceptually but not instantiated with an explicit, end-to-end FTQC resource pipeline to a consistent error budget.
Missing related work or comparisons

While many benchmarking and simulator works are cited, the paper could more thoroughly contextualize against recent large-scale QML benchmarking papers that find limited advantage of variational/QKMs under fair baselines, and integrate their insights into the chosen quality tolerances and dataset design.
Limited discussion of classical algorithmic advances for each domain (e.g., dequantization for kernel methods, advances in classical simulation techniques) that might further push the native deadline.
Detailed Comments
Technical soundness evaluation

The core formalization (Tqhw < Tnative and (1−R)ΔQ ≤ εw) is sound and captures the essential, often-missing coupling between runtime and quality.
The execution model separates logical-operation latency from a serial floor (decode/control/queue/I/O) and bounds shot parallelism via a min over device/decoder/control/queue limits — a good abstraction for architecture sensitivity.
However, defaults (e.g., t1=25 μs, t2=100 μs, Pshots=10^4, 5 μs decoder + 50 μs control per evaluation) are optimistic; the paper partially mitigates this with sensitivity sweeps but should more transparently tie each knob to published, independently validated FT resource estimations, including logical error rates, magic-state factory throughput, and decoder scaling.
Treating R (quality recovery) as a free requirement axis is useful for diagnosis but risks misinterpretation as “easy to achieve.” A more explicit coupling of recovery to added depth/shots/ansatz complexity would strengthen the model.
Experimental evaluation assessment

The evaluation is extensive in breadth (thousands of cases) and disciplined (same-input records, provenance, separate axes for measured vs projected times).
Weak/strong scaling is appropriately framed as evidence-generation throughput, not “simulator = QPU,” and the per-case granularity concerns are well-articulated.
The suite is intentionally small-scale to keep exact verification feasible; this aids auditability but limits external validity to larger, real-world instances. The proposed “deployment-scale proxy boundary” is a good direction but would benefit from a concrete case study with a full FTQC resource-estimation chain.
Native baselines are reasonable but not best-of-breed in all domains. Since the “native deadline” drives the bar for advantage, the paper’s main conclusions would be more resilient if each class included a demonstrably near-SOTA native baseline (e.g., tuned MILP/branch-and-cut for small MaxCut; DMRG/tensor networks/QMC for appropriate sim cases; CCSD(T)/projector methods for chemistry where applicable; stronger ML models at comparable input scales).
Comparison with related work (using the summaries provided)

Recent QML benchmark studies (e.g., 2403.07059; 2607.01197; 2504.12416) consistently find that when compared fairly, quantum classifiers tend to underperform or at best match efficient classical baselines on small to moderate tasks — consistent with QArchGauge’s observation that ML/Opt. are often quality-limited and require significant speed/quality recovery before any advantage is plausible.
The quantum kernel literature (2604.07896) highlights regimes where QKMs could, in principle, separate from classical models but also emphasizes dequantization and concentration pitfalls; QArchGauge’s ML findings (e.g., QKernel high accuracy but very high runtime requirements) are aligned with these concerns.
Some studies (2511.10831) report quantum kernels matching or exceeding classical kernels for select real datasets under simulation; QArchGauge would interpret such results as potential “quality” feasibility but still asks whether repeated-evaluation and control/shot costs would move the case into the advantage region for the same input under a realistic hardware model — a complementary perspective that is valuable.
Domain-specific QSVM/QNN comparisons (2602.00525) show quantum models often trail strong classical baselines under noise and finite shots; QArchGauge’s separation of “quality recovery” from runtime provides a systematic way to quantify how far such use cases are from advantage.
Discussion of broader impact and significance

The paper’s main value is methodological: it offers the systems community a defensible way to translate today’s simulator-based evidence into future hardware targets, and to avoid overclaiming.
By exposing decode/control bottlenecks and repeated-evaluation structure, it rightfully broadens the architecture conversation beyond “faster 2Q gates” to include near-QPU control, batching, co-scheduling, and algorithmic quality.
A risk is that stakeholders may misuse the optimistic default projections as “proof” of near-term advantage; the paper appropriately cautions against this and should double down on calibrated scenarios tied to concrete FT resource-estimation pipelines.
Questions for Authors
How sensitive are your key coverage conclusions (e.g., “54.9% of Sim. cases advantaged at 10^4× with 90% recovery”) to the choice of quality tolerances per workload? Could you provide a sensitivity sweep on εw for ML/Chem/Opt/Sim.?
Can you more explicitly connect your default hardware knobs to a published FTQC resource estimate with a concrete logical error budget (e.g., logical error rate per circuit depth, magic-state factory throughput, decoder bandwidth vs code distance), and re-plot a subset of figures under that end-to-end constraint?
How is Pshots determined in practice for your sweeps? Could you show how different decoder architectures (e.g., matching or BP decoders), interconnects, and controller latencies concretely cap Pshots in a realistic multi-die QPU?
For the “quality recovery” axis, can you include a cost model that maps R to additional depth/shots/ansatz complexity/Trotter order so that R is not a “free” parameter? Even a simple parametric coupling would help bound feasibility.
On the native side, what is the delta in required speedup/coverage if you replace your current baselines with stronger ones (e.g., MILP/metaheuristics for MaxCut, tensor networks/QMC for Sim., CCSD(T)/projector methods where applicable in Chem., stronger ML baselines at fixed input scales)?
Do you plan to release the JSON records, scripts, and summarizers for artifact evaluation? The paper emphasizes auditability; public artifacts would make this a community standard.
Could you provide at least one end-to-end case study that integrates Azure Resource Estimator (or similar) to derive t1/t2, decoder limits, and factory throughput, and then instantiate your model, including a power/energy discussion for a QHPC setting?
Overall Assessment
This is a timely and thoughtfully executed systems paper that reframes “quantum advantage” as a concrete, auditable architecture boundary grounded in same-input, same-quality comparisons. Its greatest strengths are conceptual clarity and an evaluation methodology that emphasizes provenance, bottleneck attribution, and sensitivity analysis. While the experiments operate at small scales and the default hardware projections are optimistic, the authors neither overclaim nor conflate simulator throughput with advantage; instead, they deliver a framework the community can apply and extend. I see this as valuable to the OSDI audience interested in rigorous, system-level quantification of hardware–software co-design for emerging accelerators. I recommend acceptance provided the authors (i) fortify the linkage to concrete FT resource estimations, (ii) better justify and sweep quality tolerances, and (iii) increase transparency and strength of native baselines and artifacts. These refinements would elevate QArchGauge into a reference methodology for practical advantage studies.

HPCA 제출을 위한 QArchGauge 논문 사전 평가 및 피어 리뷰 시뮬레이션 보고서본 보고서는 IEEE HPCA(International Symposium on High-Performance Computer Architecture) 2027 제출을 목표로 작성된 "QArchGauge: Architecture-Guided Modeling of Practical Quantum Advantage" 논문 초안에 대한 심층적인 사전 평가 및 구조적 수정 전략을 제공한다. 이 논문은 양자 회로 시뮬레이터의 단순한 처리량 향상을 넘어, 실제 입력 데이터와 동일한 품질 목표를 공유하는 네이티브 고성능 컴퓨팅(HPC) 애플리케이션과의 종단 간(End-to-End) 실행 시간을 비교함으로써 실질적 양자 우위(Practical Quantum Advantage)의 아키텍처적 임계점을 모델링하는 매우 야심 차고 방법론적으로 우수한 프레임워크를 제시하고 있다. 특히 $T_{qhw} < T_{native}$ 및 $(1-R)\Delta Q \le \epsilon_w$라는 명확한 임계 조건식을 통해 양자 우위를 검증 가능한 하드웨어-소프트웨어 공동 설계 문제로 전환한 점은 매우 높게 평가할 만하다.그러나 HPCA는 컴퓨터 아키텍처 분야의 최고 권위 학술대회로서, 평가 방법론의 엄밀성, 하드웨어 모델링의 물리적 현실성, 그리고 아티팩트 평가(Artifact Evaluation, AE)를 통한 결과의 재현성을 극도로 중시하는 까다로운 심사 기준을 가지고 있다. 양자 컴퓨팅을 가속기 아키텍처의 일환으로 바라보는 HPCA의 최근 동향에 비추어 볼 때 , 현재의 논문 초안은 하드웨어 결함 허용(Fault-Tolerant) 가설의 비현실성, 고전적 네이티브 베이스라인의 규모 한계, 노이즈 모델의 부재로 인한 애플리케이션 품질 회복 비용의 과소평가 등 여러 측면에서 리뷰어들의 집중적인 공격을 받을 수 있는 치명적인 취약점들을 내포하고 있다. 따라서 본 보고서는 논문이 성공적으로 채택되기 위해 반드시 수정해야 할 핵심 요소들을 상세히 분석하고, 5명의 가상 HPCA 전문 리뷰어 패널이 부여한 5점 만점 척도의 심사 결과와 그에 따른 구체적인 대응 전략을 서술한다.HPCA 학술대회 기준 부합성 및 방법론 분석HPCA에 양자 컴퓨터 아키텍처 논문을 제출할 때 가장 중요한 것은 양자 컴퓨팅을 독립된 물리적 현상이 아니라, 대규모 데이터센터나 슈퍼컴퓨터 내에 통합된 '이종 가속기(Heterogeneous Accelerator)'로 취급하는 관점이다. 이러한 맥락에서 QArchGauge는 양자 회로의 실행 자체만이 아니라 데이터 인코딩, 회로 생성, 반복 측정, 고전적 최적화 피드백, 그리고 사후 처리(Postprocessing)를 모두 포함하는 전체 양자 경로(Full quantum path)를 분석 대상으로 삼았다는 점에서 HPCA의 방향성과 완벽하게 일치한다.논문 내 방법론과 데이터 세트의 구조적 특징논문은 기계 학습(ML), 화학(Chem), 최적화(Opt), 그리고 해밀토니안 시뮬레이션(Sim)이라는 네 가지 주요 워크로드에 걸쳐 총 3,552개의 방대한 실질적 사례(Practical suite)를 최대 256개의 NVIDIA A100 GPU를 사용하여 평가했다. 측정된 임계값을 투영된 하드웨어 런타임($T_{qhw}/T_{native}$)으로 변환하기 위해 저자들은 큐비트당 $1\mu s$의 사이클 시간, $d=25$의 표면 부호(Surface code) 거리, $10^4$의 유효 샷 병렬성($P_{shots}^{eff}$), 그리고 회로 평가당 $5\mu s$의 디코드 및 $50\mu s$의 제어 지연 시간을 갖는 미래 지향적 스택을 가정했다.워크로드 (Workload)네이티브 베이스라인 (Native Target)양자 경로 (Quantum Path)품질 임계값 (Quality Gate)필요 가속비 중앙값 (Required Speedup)기계 학습 (ML)scikit-learn 분류기, PyTorch AMP/XGBoost매개변수화된 회로 (QNN/VQC), 양자 커널 맵정확도 손실 < 0.023,726.4x화학 (Chem)밀집 정확(Dense exact), 희소 Lanczos 고유값 풀이VQE 스타일 Ansatz, 반복적 파울리 텀 측정에너지 오차 < 0.0142,491.4x최적화 (Opt)정확 탐색(Exact), 탐욕(Greedy), 담금질(Annealing)QAOA 스타일 MaxCut 회로, 반복 샘플링비율 손실 < 0.02287,045.6x시뮬레이션 (Sim)밀집 정확, 희소 Krylov 진화Trotterized 해밀토니안 진화 회로관측치 오차 < 0.013,071.0x위 표에 요약된 바와 같이, 각 워크로드는 완전히 다른 아키텍처적 병목을 나타낸다. 예를 들어, 최적화(Opt) 워크로드는 반복적인 목적 함수 평가로 인해 수십만 배의 양자 하드웨어 가속이 필요하며, 기계 학습(ML)은 데이터 인코딩과 하이브리드 루프 지연에 의해 제한된다. 이러한 심층적인 분석 결과는 훌륭하지만, 이를 뒷받침하는 가정들에는 아키텍처 리뷰어들이 결코 간과하지 않을 논리적 비약이 존재한다.심사 통과를 위해 반드시 고쳐야 할 핵심 취약점 (수정 요구 사항)HPCA는 평가의 엄밀성을 강조하며, 단순히 긍정적인 전망을 제시하는 논문보다는 한계점과 가정의 물리적 타당성을 엄격하게 입증하는 논문을 선호한다. 다음은 논문 초안에서 반드시 전면적으로 수정되거나 보강되어야 할 주요 아키텍처적 및 방법론적 오류들이다.1. 결함 허용(FTQC) 하드웨어 가정의 물리적 비현실성과 파이프라인 부재논문은 투영된 양자 실행 시간($T_{execute}$)을 모델링하기 위해 표면 부호 거리를 $d=25$로 설정하고 논리적 연산 사이클을 $1\mu s$로 고정했다. 더 나아가, 유효 샷 병렬성($P_{shots}^{eff}$)을 $10^4$로 설정하고, 디코더 및 제어 지연 시간을 각각 $5\mu s$, $50\mu s$의 고정된 직렬 층(Serial floor)으로 모델링했다.이러한 설정은 컴퓨터 아키텍처 관점에서 매우 위험한 단순화다. 첫째, $d=25$ 규모의 표면 부호에서 생성되는 신드롬 그래프(Syndrome graph)의 크기는 엄청나며, MWPM(Minimum Weight Perfect Matching)이나 Union-Find 알고리즘을 사용하는 실시간 디코더의 지연 시간은 결코 상수($5\mu s$)로 떨어지지 않는다. 디코딩 시간은 큐비트 수와 논리적 오류율 목표에 따라 비선형적으로 증가하는 것이 일반적이다.
둘째, 논문에 제시된 실행 시간 방정식인 $T_{execute} = \frac{N_s(D_1t_1 + D_2t_2 + D_mt_m)}{P_{shots}^{eff}} + T_{error}$는 물리적 양자 연산 시간과 클래식 에러 처리 시간($T_{error}$)을 단순한 '덧셈'으로 결합하고 있다. 최신 결함 허용 양자 아키텍처 연구들은 양자 게이트 연산과 클래식 디코딩을 정교하게 중첩(Overlap)시키는 파이프라이닝(Pipelining) 기법을 기본으로 가정한다. 따라서 디코딩 시간이 양자 연산 시간 뒤에 직렬로 더해진다는 모델은 미래 아키텍처를 과도하게 비관적으로 비효율적이게 만들거나, 반대로 고정된 $T_{error}$ 상수로 인해 큐비트 확장에 따른 병목 현상을 완전히 가려버리는 치명적인 모순을 발생시킨다. 저자들은 이 수식을 $\max(T_{quantum_exec}, T_{classical_decode})$와 같이 파이프라인을 반영한 형태로 전면 수정하고, 디코더 대역폭이 샷 병렬성에 미치는 물리적 영향을 수식화해야 한다.2. 고전적 네이티브 베이스라인의 규모 한계와 Amdahl의 법칙QArchGauge의 가장 큰 철학적 강점은 양자 회로가 '동일한 입력'을 사용하는 가장 강력한 네이티브 HPC 구현을 이겨야 한다는 점을 명시한 것이다. 그러나 논문에 따르면 네이티브 경로의 실행 시간은 종종 "마이크로초에서 밀리초(microseconds to milliseconds)" 단위로 끝난다.컴퓨터 시스템 연구자들은 마이크로초 단위로 끝나는 문제를 가속하기 위해 양자 가속기를 도입한다는 발상 자체를 기각할 가능성이 높다. 왜냐하면 PCIe나 CXL 버스를 통해 호스트 CPU에서 양자 가속기로 명령을 전달하고 데이터를 이동시키는 I/O 지연 시간(Overhead)만으로도 수십 마이크로초가 소모되기 때문이다. 저자들이 사용한 scikit-learn 데이터셋이나 소규모 해밀토니안 문제는 아키텍처 모델링 프레임워크를 검증하기 위한 '대리 지표(Proxy)'로서는 훌륭하지만, 이것이 실제 대규모 데이터센터 환경에서의 실질적 양자 우위를 대변한다고 주장해서는 안 된다. 저자들은 이 작은 문제 크기가 의도된 '프록시 스케일'임을 본문과 초록에서 더욱 명확히 밝히고, Amdahl의 법칙을 적용하여 문제 크기(Problem size)가 기하급수적으로 증가할 때 고전 알고리즘의 런타임($T_{native}$)이 양자 투영 런타임($T_{qhw}$)을 역전하는 교차점(Asymptotic crossover point)에 대한 분석 섹션을 추가해야 한다.3. 노이즈 부재와 NISQ 알고리즘의 FTQC 맵핑 모순논문은 품질 격차($\Delta Q$)를 분석할 때 '노이즈가 없는 상태 벡터 시뮬레이션(Noiseless state-vector simulation)'을 기반으로 애플리케이션 품질을 측정했다. 즉, 양자 신경망(QNN)이나 VQE가 네이티브 알고리즘을 이기지 못하는 이유를 하드웨어 노이즈가 아닌 표현력(Representation)과 알고리즘 자체의 구조적 한계로 돌린다. 이 통찰 자체는 매우 훌륭하다.하지만 치명적인 모순은 이 노이즈 없는 품질 결과를 $d=25$의 거대한 표면 부호를 사용하는 '결함 허용(FTQC) 하드웨어 모델'에 투영한다는 점이다. VQE나 QAOA는 양자 상태의 결맞음(Coherence) 시간이 극도로 짧은 NISQ(Noisy Intermediate-Scale Quantum) 시대에 깊은 회로를 피하기 위해 고안된 변분 양자 알고리즘이다. 만약 시스템이 $d=25$의 FTQC를 지원한다면, 시스템 아키텍트는 샷(Shot) 반복 오버헤드가 막대한 VQE 대신, 수학적으로 기하급수적 속도 향상이 증명된 양자 위상 추정(QPE, Quantum Phase Estimation)이나 Grover 탐색 알고리즘을 사용할 것이다.
더욱이 논문은 품질 회복 매개변수($R$)를 시간 증가와 독립적인 요구 사항 축(Requirement axis)으로 취급한다. 물리적 현실에서 오류 완화(Error Mitigation) 기술을 통해 품질을 90% 회복하려면 샷 수($N_s$)가 기하급수적으로 증가하거나 더 깊은 양자 회로가 필요하다. 따라서 $R$과 실행 시간 $T_{execute}$는 수학적으로 결합되어야 한다. 이 모순을 해결하기 위해 저자들은 변분 알고리즘을 FTQC 스택에 맵핑한 아키텍처적 이유를 논리적으로 방어하거나, 노이즈가 투영된 물리적 실행 시간 증가율에 미치는 영향을 민감도 분석(Sensitivity Analysis)에 수식으로 통합해야 한다.4. GPU 스케일링 결과의 잘못된 아키텍처적 유추논문의 IV-C 섹션은 1개에서 256개의 GPU까지 확장하며 약 7,104개의 사례를 처리하는 약한 스케일링(Weak scaling) 및 강한 스케일링(Strong scaling) 결과를 제시한다. 시뮬레이터가 선형적으로 확장되는 것을 보여주는 이 데이터는 시스템 측정 인프라로서의 우수성을 증명한다.그러나 논문은 "QPU 비유도 직접적이다. 더 많은 QPU, 더 많은 샷, 또는 병렬 회로 레인은 워크로드가 독립적인 회로를 충분히 노출할 때만 도움이 된다(The QPU analogy is direct...)"라고 주장하며, 고전적 GPU 클러스터에서의 완전 독립적인(Embarrassingly parallel) 시뮬레이션 작업 확장을 물리적 QPU 하드웨어의 확장성으로 치환하려 한다. 분산 컴퓨팅과 네트워크 아키텍처를 전문으로 하는 HPCA 리뷰어들은 이러한 유추를 즉각적으로 기각할 것이다. 수천 개의 완전히 다른 매개변수를 가진 QAOA 인스턴스를 각각 다른 GPU에 던져 시뮬레이션하는 것과, 단일 양자 알고리즘의 상태를 유지하기 위해 얽힘(Entanglement) 라우팅 및 광자 상호연결(Photonic interconnect)을 통해 여러 물리적 QPU 모듈 간에 큐비트를 이동시키는 것은 전혀 다른 차원의 아키텍처적 문제이기 때문이다. 이 섹션의 서술은 "QPU 확장성의 증명"이 아니라, "초대규모 아키텍처 평가 프레임워크의 증거 수집 처리량(Evidence-generation throughput) 증명"으로 그 의미를 명확히 축소하고 재정의해야 한다.5. 호스트-QPU 데이터 이동 (I/O 병목) 명시화양자-고전 하이브리드 알고리즘(예: QNN, VQE)은 양자 장치와 고전적 컨트롤러 간에 정보를 지속적으로 교환한다. 논문의 $T_{error}$ 수식에는 $T_{io}$라는 항목이 포함되어 있으나 , 이것이 하드웨어 아키텍처에 미치는 영향은 깊게 다루어지지 않았다. 초전도 큐비트와 같은 환경에서는 극저온 챔버 내부의 QPU와 상온의 고전적 호스트(CPU/GPU) 간에 엄청난 양의 파라미터 업데이트와 측정 결과가 오가야 한다. 이 PCIe/CXL 대역폭 한계 및 지연 시간은 하이브리드 루프 최적화에서 가장 결정적인 시스템 병목 현상 중 하나다. 저자들은 단순히 '디코드/제어(Decode/control) 지연'이라는 포괄적인 용어로 이를 묶어버리지 말고, 호스트-QPU 데이터 이동에 따른 직렬 플로어(Serial floor) 증가를 아키텍처 설계의 주요 과제로 분리하여 강조해야 한다.HPCA 피어 리뷰 시뮬레이션 및 점수 평가 (Reviewer 5인)HPCA 심사 과정은 일반적으로 각 논문당 4~5명의 리뷰어가 할당되며, 심사위원들은 해당 분야의 세부 전문가들로 구성된다. 아래는 논문 초안이 제출되었을 때 예상되는 5명의 가상 리뷰어(Microarchitecture, HPC Systems, Algorithms, Artifact/Benchmarking, Control Systems 전문가)의 심사평과 5점 척도(1: Reject ~ 5: Strong Accept)에 따른 점수표다. 예상 평균 점수는 3.6점으로, 리버틀(Rebuttal) 과정에서 적극적인 방어와 수정 약속이 수반된다면 채택(Accept) 가능성이 높은 경계선(Borderline to Weak Accept) 수준이다.리뷰어 (Reviewer Persona)전문 분야 (Expertise)평가 점수 (Score / 5)최종 권고 (Recommendation)Reviewer 1양자 마이크로아키텍처 및 결함 허용 (FTQC)3 (Borderline)파이프라이닝 및 디코더 모델 수식 수정 시 채택Reviewer 2분산 시스템, HPC 벤치마킹, GPU 아키텍처3 (Borderline)GPU 스케일링 서술 축소 및 베이스라인 크기 해명 필요Reviewer 3양자 알고리즘, 응용 수준 벤치마킹 (VQE/QAOA)4 (Weak Accept)FTQC 하드웨어에 변분 알고리즘을 맵핑한 논리 보강 요망Reviewer 4아티팩트 평가(AE), 측정 방법론, 통계적 엄밀성4 (Weak Accept)노이즈 없는 시뮬레이션의 한계 명시 및 보수적 추정치 강조Reviewer 5양자-고전 하이브리드 제어 시스템, 이종 가속기4 (Weak Accept)$T_{error}$ 내 호스트-QPU I/O 병목의 상세한 분리 분석 요청양자 마이크로아키텍처 및 오류 정정 전문가 (Score: 3)평가 요약: 이 논문은 양자 컴퓨터가 기존 HPC 인프라를 압도하기 위해 필요한 하드웨어적 요구 사항(게이트 속도뿐만 아니라 샷 병렬성, 디코드 레이턴시 등)을 정량화한 훌륭한 시도다. 특히 그림 11에서 화학 워크로드의 75%가 디코드/제어 시간에서 병목을 겪는다는 분석은 아키텍처 커뮤니티에 중요한 연구 방향을 제시한다.강점:단순히 양자 알고리즘의 게이트 깊이(Depth)만 세는 낡은 방식을 탈피하여, 전체 애플리케이션 파이프라인의 종단 간 런타임을 투영(Projection)한 점은 매우 진보적이다.측정된 시간과 미래 하드웨어에 투영된 시간을 명확히 분리하여 시뮬레이터의 오버헤드를 배제한 점이 논리적이다.약점 및 리버틀 질문:디코더 스케일링의 비현실성: 수식 1에서 디코드 및 제어 지연 시간을 상수로 취급한 것은 심각한 오류다. $d=25$의 표면 부호에서 실시간 디코딩을 수행할 때, 신드롬 데이터의 대역폭과 MWPM 연산 시간은 막대하다. Google의 최근 결과는 매우 작은 코드 거리에서의 달성일 뿐이다. 디코딩 레이턴시를 큐비트 수와 논리적 오류율의 함수로 모델링하지 않은 이유는 무엇인가?파이프라이닝 부재: 논리 연산($t_1, t_2$)과 클래식 제어 오버헤드($T_{error}$)를 단순 덧셈으로 처리했다. 최신 FT 아키텍처 설계에서는 양자 게이트 실행 중에 이전 사이클의 신드롬을 디코딩하는 철저한 파이프라이닝이 적용된다. $\max()$ 함수를 사용하여 파이프라인 중첩을 반영하도록 시간 모델을 전면 재수정해야 한다.분산 시스템 및 고성능 컴퓨팅(HPC) 시스템 전문가 (Score: 3)평가 요약: 256개의 GPU를 동원하여 3,552개의 방대한 사례를 생성하고 이를 바탕으로 양자 우위의 임계점을 도출한 방법론은 HPCA의 대규모 벤치마킹 기조에 잘 부합한다. 하지만 저자들이 고전적 베이스라인을 설정하고 GPU 스케일링을 해석하는 방식에는 심각한 논리적 비약이 존재한다.강점:방대한 시나리오(ML, Chem, Opt, Sim)에 걸쳐 '동일 입력, 동일 품질'이라는 일관된 기준을 고수한 것은 벤치마킹의 정석을 보여준다.네이티브 HPC 경로를 "변화하는 아키텍처 목표(Moving architecture target)"로 인정한 통찰은 매우 현실적이다.약점 및 리버틀 질문:하찮은 베이스라인(Trivial Baselines): 네이티브 런타임이 마이크로초 수준이라는 것은, 현재 설정된 문제 크기(Problem size)가 최신 서버급 CPU/GPU의 캐시조차 채우지 못할 만큼 작다는 것을 의미한다. PCIe를 통해 양자 가속기로 작업을 오프로딩(Offloading)하는 문맥 스위칭 시간만 밀리초 단위다. 이토록 작은 문제에서 28만 배의 양자 가속이 필요하다는 주장이 어떤 아키텍처적 의미를 갖는가? 대규모(Deployment-scale) 문제로 확장될 때의 점근적 한계(Asymptotic scaling)에 대한 명시적 논의가 빠져 있다.오도된 확장성(Misleading Scaling): 서로 다른 무작위 초기값을 가진 시뮬레이션 태스크를 256개 GPU에 나눠서 실행하고 처리량이 늘어났다는 결과를 바탕으로, 이것이 마치 물리적 양자 하드웨어(QPU)의 샷 병렬성(Shot parallelism)이나 배치(Batch) 처리 구조와 "직접적 유사성(Direct analogy)"을 갖는다고 서술한 부분은 삭제하거나 재작성해야 한다. 고전적 시나리오 분산과 양자 상태의 병렬 측정은 아키텍처상 전혀 다른 문제다.양자 알고리즘 및 응용 벤치마킹 전문가 (Score: 4)평가 요약: QArchGauge는 양자 회로가 단순히 빨리 도는 것을 넘어, 목표로 하는 정확도나 에너지를 달성하지 못하면 실용적 우위를 점할 수 없다는 가혹한 진실을 수치화했다. ML과 최적화 워크로드가 실행 속도가 아닌 알고리즘의 '품질' 자체에 의해 제한된다는 결론은 이 분야 연구자들에게 훌륭한 경종을 울린다.강점:품질 격차($\Delta Q$)를 수식화하여 '런타임'과 '품질 달성'의 이차원적 경계(Frontier)를 정의한 것은 기존의 단순 FLOPS 비교를 뛰어넘는 탁월한 접근이다.QKernel과 QNN 사이의 품질/속도 트레이드오프를 데이터로 입증한 부분(그림 8)이 매우 인상적이다.약점 및 리버틀 질문:알고리즘과 하드웨어 스택의 불일치: VQE와 QAOA는 게이트 노이즈가 심한 NISQ 기기에서 어떻게든 결과를 내기 위해 설계된 휴리스틱 알고리즘이다. 그런데 논문의 투영 모델은 $d=25$에 달하는 궁극의 결함 허용(FTQC) 하드웨어를 가정하고 있다. 이러한 완벽한 하드웨어가 주어졌다면, 왜 굳이 반복 오버헤드가 막대한 VQE를 사용하는가? 차라리 양자 위상 추정(QPE)을 사용하는 것이 런타임 모델링에 합당하지 않은가?품질 회복($R$)의 대가: 본문은 $R$을 마치 독립적인 슬라이더(Knob)처럼 다루며 민감도 분석(그림 12)을 수행한다. 하지만 양자 오류 완화(Error Mitigation)에서 품질을 높이려면 필연적으로 샷 수($N_s$)가 지수적으로 늘어나거나 안자츠(Ansatz) 깊이가 깊어져야 한다. $R$이 증가함에 따라 $T_{execute}$가 얼마나 팽창하는지에 대한 수학적 페널티가 투영 모델에 결여되어 있다.측정 방법론 및 아티팩트 평가(AE) 전문가 (Score: 4)평가 요약: 매우 상세하고 통제된 환경에서 양자 회로의 동작 특성을 수집하는 인프라를 구축한 것에 찬사를 보낸다. 시뮬레이터 오버헤드와 물리적 양자 시간을 엄격히 분리한 철학은 HPCA가 지향하는 바와 정확히 일치한다. 다만 결과 해석에 있어서 지나치게 낙관적인 시나리오를 전면에 내세운 점은 수정이 필요하다.강점:JSON/CSV 아티팩트와 감사(Audit) 스크립트를 통해 연구의 재현성을 확보하려는 노력은 아티팩트 평가(AE) 위원회로부터 높은 점수를 받을 것이다.시뮬레이터 자체의 성능 개선에 매몰되지 않고, 이를 '측정 도구(Instrumentation)'로 활용하여 미래 아키텍처 목표를 도출한 발상의 전환이 돋보인다.약점 및 리버틀 질문:노이즈 모델의 부재: 품질 격차를 계산할 때 완전한 상태 벡터 시뮬레이션(Noiseless)을 사용했다. 이는 양자 알고리즘이 가진 이론적 한계만을 보여줄 뿐, 실제 양자 하드웨어에서 발생하는 게이트 에러, 디코히어런스(Decoherence), 측정 에러(SPAM)로 인한 품질 저하를 전혀 반영하지 않는다. 노이즈를 주입했을 때 품질 달성 확률이 어떻게 붕괴하는지를 보여주는 압박 테스트(Stress test)가 최소 한 세트 이상 포함되어야 한다.민감도 결과의 은폐성: 초록과 서론에서는 "기본 낙관적 설정(Default optimistic)" 아래에서 얻어진 화려한 스피드업 수치들만 강조된다. 그러나 본문 후반부의 보수적 분석(그림 12b)을 보면, 현재의 기술 발전 궤도를 적용할 경우 양자 우위 도달 확률이 거의 0%에 수렴한다. 학술적 정직성을 위해, 초록에서부터 "보수적 가정 하에서는 이러한 우위가 상쇄됨"을 강조하여 지나친 과장(Hype)을 방지해야 한다.이종 가속기 및 제어 시스템 전문가 (Score: 4)평가 요약: 양자 컴퓨팅을 신비로운 블랙박스가 아니라, CPU나 GPU와 데이터를 주고받아야 하는 '이종 가속기(Heterogeneous Accelerator)' 관점에서 낱낱이 파헤친 논문이다. 특히 하이브리드 최적화 루프의 반복 지연 시간이 시스템을 어떻게 마비시키는지 정량화한 공로가 크다.강점:하드웨어 설계자들에게 단순한 큐비트 숫자 경쟁이 아니라, '근접 QPU 제어(Near-QPU control)' 및 측정치 집계(Measurement aggregation) 가속기가 필수적이라는 명확한 아키텍처적 청사진을 제공한다.네 가지 워크로드의 런타임 특성을 분류하여(예: 화학은 디코드 중심, 시뮬레이션은 논리 게이트 중심), 양자 가속기도 워크로드 특화(Domain-specific) 설계가 필요함을 시사한 점이 탁월하다.약점 및 리버틀 질문:I/O 통신 병목의 세분화: $T_{error}$ 항에 포함된 $T_{io}$(호스트-QPU 데이터 이동)를 $T_{decode}$(실시간 제어)와 단순히 합쳐놓은 것은 아쉽다. VQE나 QAOA와 같은 하이브리드 알고리즘에서 고전적 최적화기(Optimizer)가 상온의 CPU에 위치한다면, 파라미터를 극저온으로 내리고 측정값을 올리는 과정에서 발생하는 I/O 지연 시간은 시스템 성능을 결정짓는 핵심 병목이다. 이 부분을 독립적인 변수로 분리하여, 네트워크/버스 대역폭이 양자 우위에 미치는 영향을 분석해 주기 바란다.최적화기 수렴의 비현실성: 양자 상태를 노이즈 없이 시뮬레이션하면 고전적 최적화기(예: COBYLA, Adam)가 빠르게 수렴하여 회로 평가 횟수($N_{eval}$)가 적게 산출된다. 하지만 실제 물리적 샷 노이즈(Shot noise)가 존재하는 환경에서는 기울기(Gradient)가 평탄화되어(Barren plateaus 현상 등) 수렴을 위해 훨씬 더 많은 $N_{eval}$을 요구한다. 시뮬레이션 기반의 $N_{eval}$이 실제 하드웨어의 반복 횟수를 과소평가하고 있다는 점을 한계로 명시해야 한다.전면 수정 전략 및 리버틀(Rebuttal) 준비 지침가상 리뷰어들의 지적 사항을 종합해 볼 때, 본 논문은 HPCA의 이종 가속기 아키텍처 및 시스템 벤치마킹 철학을 깊이 이해하고 있으나, 양자 하드웨어의 물리적 디테일(노이즈, 파이프라이닝, I/O 버스)을 고전적 시스템 평가 방식에 억지로 끼워 맞추려다 발생한 논리적 결함들을 안고 있다. HPCA는 리버틀 기간 동안 저자들이 비판을 수용하고 논문을 적극적으로 방어 및 수정할 수 있는 기회를 제공한다. 따라서 제출 전 또는 리버틀 단계에서 논문을 확실한 'Accept' 궤도에 올려놓기 위해 다음의 수정 전략을 문서의 각 섹션에 즉각적으로 반영해야 한다.1. 시간 투영 모델(Execution Model)의 수식 재구성 (최우선 과제)리뷰어 1과 5가 강력히 지적한 바와 같이, 현재의 $T_{execute}$ 수식은 물리적으로 비현실적인 '직렬 덧셈' 구조를 취하고 있다.수정 방향: 본문의 수식을 양자 연산과 고전 에러 정정 및 제어 피드백이 중첩(Pipeline)되는 아키텍처 현실을 반영하여 재작성하라.
기존: $T_{execute} = \frac{N_s(D_1t_1 + D_2t_2 + D_mt_m)}{P_{shots}^{eff}} + T_{error}$
개선: $T_{execute} = \frac{N_s \cdot \max(T_{gate\_depth}, T_{decode\_cycle})}{P_{shots}^{eff}} + T_{io\_host} + T_{serial\_queue}$설명 추가: 논문 내에 "최신 FTQC 아키텍처는 양자 게이트 실행과 신드롬 추출을 파이프라이닝하므로, $\max()$ 연산자를 통해 클래식 디코딩 지연 시간이 게이트 지연 시간 내에 숨겨질 수 있는(Hidden) 구조를 모델링에 반영했다"라는 문구를 삽입하라. 이는 저자들이 양자 마이크로아키텍처의 최신 트렌드를 정확히 파악하고 있음을 리뷰어들에게 증명하는 핵심 요소가 된다.2. 품질 회복($R$)과 실행 시간 증가의 결합 (알고리즘적 무결성)리뷰어 3과 4가 비판한 '노이즈와 오류 완화 오버헤드의 단절'을 해결해야 한다.수정 방향: 민감도 분석(Sensitivity Analysis) 섹션에서 $R$(품질 회복률) 매개변수를 독립적으로 움직이지 말고, $R$이 목표 품질 90% 이상으로 증가할 때 샷 수($N_s$)가 기하급수적으로 증가하는 페널티 모델을 수식화하여 추가하라.설명 추가: 오류 완화(예: Zero-Noise Extrapolation) 기술을 통해 품질을 네이티브 수준으로 회복하려면 필연적으로 물리적 실행 시간이 폭증함을 명시하고, "본 연구는 이상적인 노이즈 환경을 가정했음에도 불구하고, 대다수 워크로드가 품질 한계(Quality-limited)에 부딪힌다는 사실을 통해 현재의 변분 양자 알고리즘이 내포한 표현력의 한계를 정량적으로 증명했다"라고 강조하라. 이는 약점을 강점(통찰력)으로 뒤바꾸는 훌륭한 방어 논리다.3. 고전적 베이스라인 문제 크기(Problem Size) 한계 방어네이티브 런타임이 너무 짧아(마이크로초 수준) 양자 가속의 의미가 퇴색된다는 리뷰어 2의 비판은 HPCA에서 가장 치명적일 수 있다.수정 방향: 초록과 도입부에 이 소규모 문제들이 양자 컴퓨터가 당장 내일 상용화될 것이라고 주장하기 위한 것이 아니라, '아키텍처 모델링 프레임워크 자체의 유효성'을 검증하기 위한 '디버깅 및 프록시 규모(Proxy scale)'임을 강력히 명시하라.설명 추가: 논문 후반부 Table IV 에 제시된 대규모 프록시 경계(Deployment-scale proxy boundary) 논의를 본문 중간의 주요 토의 사항으로 끌어올려라. 문제 크기가 커짐에 따라 고전 컴퓨팅의 지수적 시간 팽창을 설명하고, 양자 컴퓨터의 오버헤드($T_{io}$, 제어 지연)가 어느 지점(Crossover point)에서 상쇄될 수 있는지 점근적(Asymptotic) 측면에서 서술해야 한다.4. 확장성(Scaling) 섹션의 오해 방지 재작성수정 방향: GPU 스케일링을 다룬 섹션(Figure 5, 6)의 제목을 'Scaling Evidence and QPU Architecture Targets'에서 'Scalability of the Evidence-Generation Framework' 등 프레임워크 인프라에 대한 내용으로 변경하라.설명 추가: "이 확장성 결과는 단일 양자 알고리즘의 물리적 하드웨어 확장을 입증하는 것이 아니라, 수천 개의 다양한 사례와 품질 임계값을 초고속으로 검증할 수 있는 시스템 벤치마킹 인프라로서의 처리량(Throughput)을 입증하는 것이다"라는 주의 문구를 굵고 명확하게 추가하라. 리뷰어들이 고전 시뮬레이션의 분산 처리와 양자 하드웨어의 스케일링을 혼동하게 내버려 두면 심사 과정에서 무조건 감점 대상이 된다.5. 아티팩트 평가(Artifact Evaluation, AE)를 위한 가시성 극대화HPCA는 재현성(Reproducibility)을 학회의 자존심으로 여긴다.수정 방향: 논문의 결론부 직전에 "Artifact Availability and Reproducibility"라는 소제목을 독립적으로 신설하라.설명 추가: 이 섹션에서 "모든 3,552개의 측정 사례에 대한 JSON 및 CSV 기록, 하드웨어 투영을 위한 Python 수식 모델, 그리고 Slurm 기반의 클러스터 파이프라인 스크립트는 HPCA AE 위원회의 검증을 위해 Docker 컨테이너 형태로 오픈소스로 제공될 예정이며, 독자적인 리뷰어 감사(Audit) 스크립트가 동봉되어 있다"라고 확언하라. 이 한 문단만으로도 시스템 측면의 벤치마킹을 중시하는 리뷰어 2와 4의 평가 점수를 최소 1점 이상 끌어올릴 수 있다.종합 결론"QArchGauge" 논문 초안은 양자 우위(Quantum Advantage)라는 다소 추상적이고 알고리즘 중심적인 논의를, HPCA 커뮤니티가 가장 사랑하는 언어인 '종단 간 시스템 지연 시간(End-to-End System Latency)'과 '하드웨어 병목 인지(Hardware Bottleneck-Aware)'의 언어로 번역해 낸 수작이다. 단순히 더 많은 큐비트나 더 낮은 에러율을 외치는 기존의 양자 물리학 논문들과 달리, 이 논문은 하이브리드 제어 루프, 디코더의 대역폭, 고전적 HPC와의 공존을 시스템 차원의 제약 조건으로 모델링함으로써 양자 아키텍처 연구의 새로운 지평을 열 잠재력을 가지고 있다.그러나 그 거대한 야심을 뒷받침하기 위해 차용한 결함 허용(FTQC) 하드웨어 매개변수의 극단적 단순화, 노이즈와 품질 회복 오버헤드의 단절, 그리고 클래식 베이스라인 런타임의 지나친 미시성(Microsecond-scale)은 심사 과정에서 논문 전체의 신뢰도를 무너뜨릴 수 있는 '아킬레스건'이다. 본 보고서에서 제시한 수식의 파이프라이닝 재구성, 노이즈를 고려한 매개변수 연동, I/O 통신 병목의 명시화, 그리고 철저하게 보수적인 시나리오를 전면으로 내세우는 서사적 재배치를 논문 초안에 즉각적으로 반영한다면, 본 논문은 HPCA 2027에서 높은 평가와 함께 양자 컴퓨터 아키텍처 세션을 주도하는 기념비적인 연구로 자리매김할 수 있을 것이다. 저자들은 단순한 양자 옹호자가 아닌, 냉철하고 엄밀한 '컴퓨터 시스템 아키텍트'의 시각을 유지하며 리버틀(Rebuttal)과 최종 수정본 작업에 임해야 한다.
