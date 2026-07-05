# Line-by-Line Reviewer Response Map

This internal note maps the pasted review feedback to the current manuscript,
artifacts, or planned follow-up work. It is not part of the submitted paper.

| Feedback line | Current action | Evidence |
| --- | --- | --- |
| Hardware projection is first-order and hides compilation, routing, mitigation/correction, queueing in `T_error`. | Keep the model as a lower bound, but decompose `T_error` and add a concrete surface-code-style instantiation with distance, cycle time, decoder latency, operation multipliers, and shot parallelism. | `paper/3.Design.tex`, `paper/5.Discussion.tex`, `paper/references.bib` |
| No concrete calibration to technology stack. | Added an illustrative non-vendor calibrated stack: `d=25`, `tau_c=1us`, logical operation multipliers, decoder latency, and `P_shots=1e4`. The paper states this is not a vendor timeline. | `paper/3.Design.tex` |
| Problem instances are small: chemistry/simulation active spaces are up to 8 qubits. | Keep the evidence, but explicitly state that they are active-space gates and not production drug-discovery scale. | `paper/4.Evaluation.tex`, `paper/5.Discussion.tex` |
| Digits is limited. | Treat digits as calibration only; main evidence remains 3,552 cases across ML, chemistry, optimization, and simulation. | `paper/1.Introduction.tex`, `paper/4.Evaluation.tex` |
| QAOA and VQC/QNN choices are narrow. | Added algorithmic-sensitivity threat: fixed ansatz/grid choices can bias quality-limited classifications; better optimizers/encodings map to quality-gap recovery. | `paper/5.Discussion.tex` |
| Native baselines may be weak: ML lacks CNN; optimization lacks commercial MILP. | Clarified implemented baselines and explicitly list CNNs, boosted trees, Gurobi/CPLEX, tensor networks, and CCSD(T) as stronger unimplemented baselines that would likely move thresholds right. | `paper/5.Discussion.tex`, `paper/reviewer_readiness.md` |
| Tolerance choices are under-justified. | Added explicit per-family tolerances and stated they are strict model inputs, not universal domain standards. Aligned taxonomy tolerances with projection tolerances. | `paper/3.Design.tex`, `paper/4.Evaluation.tex`, `scripts/generate_workload_taxonomy.py` |
| Accuracy vs. qubit number appears inconsistent with PCA dimensions. | Added qubit-accounting note: digits uses one qubit per PCA feature, i.e., 4/8/12/16 qubits. The plotted figures are threshold/quality summaries from measured records, not 50--1000 qubit hardware-roadmap figures. | `paper/4.Evaluation.tex` |
| Need shot, optimizer, mitigation, and simulator sensitivity. | The paper now separates measured dimensions from future sensitivity. Shot parallelism is in the projection model; unmeasured optimizer/ansatz/mitigation sensitivity is tied to quality-gap recovery and threats. | `paper/3.Design.tex`, `paper/4.Evaluation.tex`, `paper/5.Discussion.tex` |
| Figures must be unambiguous and fully labeled. | Current plots are generated from scripts and audit-checked as PDF artifacts. The line-by-line response flags figure provenance through JSON/CSV and generated figure scripts. | `scripts/generate_paper_figures.py`, `scripts/audit_paper_evidence.py`, `data/processed/perlmutter/paper_artifact_manifest.md` |
| Name `QSUPREMACY` may distract. | Changed the manuscript display name to neutral `QAdvantage`. Repository and some historical file names remain unchanged. | `paper/0.Main.tex`, `paper/5.Discussion.tex` |
| Missing QHPC integration/scheduling perspectives. | Added related work on hybrid workflow scheduling and orchestration, including Qurator and Kubernetes-based quantum-classical workflows. | `paper/5.RelatedWork.tex`, `paper/references.bib` |
| Missing industry evaluation frameworks / traffic-light assessments. | Added QED-C application-oriented benchmarks and QCHALLenge-style industry traffic-light assessment to related work. | `paper/5.RelatedWork.tex`, `paper/references.bib` |
| Connect threshold modeling to fault-tolerant resource estimation. | Added Azure Quantum Resource Estimator and Webber hardware-specification/resource-estimation references; added worked lower-bound surface-code parameterization. | `paper/3.Design.tex`, `paper/5.RelatedWork.tex`, `paper/references.bib` |
| Frontier formulation is useful but hardware region remains notional. | Added explicit statement that the speedup axis can be interpreted as a requirement on the entire logical-runtime numerator under any chosen FT stack. | `paper/3.Design.tex`, `paper/4.Evaluation.tex` |
| Broad workload coverage and audits are strengths. | Preserve the artifact map, readiness audit, and evidence audit. No change needed except updating the response map. | `data/processed/perlmutter/paper_artifact_manifest.md`, `scripts/audit_paper_evidence.py` |
| Sensitivity sweeps are partial. | Recorded as an explicit limitation rather than an implicit assumption; future work includes shot, optimizer, ansatz, mitigation, tensor-network, and larger active-space sweeps. | `paper/4.Evaluation.tex`, `paper/5.Discussion.tex`, `plan.md` |
| How are shots chosen and how does shot parallelism affect the frontier? | The current circuits use the recorded shot/evaluation metadata and model shot parallelism with `P_shots`; broader shot sweeps remain a follow-up experiment. | `paper/3.Design.tex`, `paper/4.Evaluation.tex` |
| Can alternative simulator backends change `T_qsim`? | The paper states yes: tensor-network, path-integral, stabilizer, or specialized simulators could change `T_qsim`, but the native baseline and quality rule remain fixed. | `paper/5.Discussion.tex` |
| Can quality-gap recovery map to practical techniques? | Clarified that recovery is a requirement axis for better ansatz, encodings, optimizers, mitigation, or fault tolerance, not a measured mitigation result. | `paper/4.Evaluation.tex`, `paper/5.Discussion.tex` |
| Overall assessment: promising but needs stronger baselines, tolerance justification, calibrated hardware scenario. | Addressed in the manuscript with explicit limits and a worked hardware instantiation; stronger baselines remain future work unless new experiments are approved. | `paper/3.Design.tex`, `paper/4.Evaluation.tex`, `paper/5.Discussion.tex`, `plan.md` |

## Active Experiment Follow-Up

The 64-node extension requested after the current paper plan is queued:

| Job | Mode | Nodes | Intended evidence |
| --- | ---: | ---: | --- |
| `55520623` | Weak scaling | 64 | 7,104-case weak-scaling extension with roughly fixed per-GPU work |
| `55520624` | Fixed work | 64 | 3,552-case fixed-work time-to-solution extension |

These jobs are pending and are not yet used as completed paper evidence.
