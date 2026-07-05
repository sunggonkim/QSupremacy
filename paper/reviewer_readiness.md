# Reviewer Readiness Notes

This note tracks the main review risks for the current paper package and the
evidence that answers each risk. It is not part of the submitted manuscript; it
is an internal acceptance-readiness checklist.

| Review risk | Likely criticism | Current answer | Evidence |
| --- | --- | --- | --- |
| Novelty boundary | This is only another quantum-simulator benchmark. | The paper does not claim a new simulator. It uses simulation as instrumentation for same-task native-versus-quantum break-even modeling. | `paper/1.Introduction.tex`, `paper/3.Design.tex`, `paper/5.RelatedWork.tex` |
| Native baseline strength | The quantum path may look bad or good only because the classical baseline is weak. | Native paths are selected from multiple candidates per family, and a separate accept-profile gate stresses chemistry and simulation baselines. | `paper/4.Evaluation.tex`, `paper/figures/strong_native_comparison.pdf`, `data/processed/perlmutter/practical_suite_accept_baselines_1node_20260704150409_accept_baselines.json` |
| Toy workload concern | Digits alone is too small for a systems paper. | Digits is used only as a controlled calibration. The main evidence is a 3,552-case suite across ML, chemistry, optimization, and simulation. | `paper/4.Evaluation.tex`, `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json` |
| Practical chemistry concern | Chemistry examples may be hand-written surrogates. | The chemistry coverage gate includes OpenFermion/PySCF active-space fixtures and records 104 completed GPU-node cases. | `paper/4.Evaluation.tex`, `data/processed/perlmutter/practical_suite_chem_active_6q8q_1node_20260704233824_chemistry_coverage.json` |
| Hardware projection concern | Simulator time is not future hardware time. | The paper reports required speedup and advantage frontiers; it does not equate cuQuantum runtime with hardware runtime. | `paper/3.Design.tex`, `paper/4.Evaluation.tex`, `paper/figures/advantage_frontier.pdf` |
| Fault-tolerance model | The projection hides surface-code and logical-level overheads inside one term. | The design now labels the projection as a first-order lower bound, decomposes `T_error` qualitatively, and names the surface-code variables a future calibrated stack must provide. | `paper/3.Design.tex`, `paper/5.Discussion.tex`, `paper/references.bib` |
| Hardware calibration | Required speedup is not translated to IBM/Google/IonQ/Rigetti timelines. | The discussion explicitly says the current result is not a vendor-calibrated timeline and should be read as a threshold any future hardware model must satisfy. | `paper/5.Discussion.tex` |
| Quality concern | Faster quantum execution is meaningless if output quality is worse. | Every threshold is interpreted jointly with quality gap and quality-gap recovery. The taxonomy separates speed-limited from quality-limited cases. | `paper/4.Evaluation.tex`, `paper/figures/workload_taxonomy.pdf`, `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json` |
| Quality normalization | Chemistry/simulation quality gaps can exceed one without clear semantics. | The design defines tolerance-scaled quality gaps and the chemistry coverage table states that values above one are more than one workload tolerance away from the reference. | `paper/3.Design.tex`, `paper/4.Evaluation.tex` |
| Quality-gap recovery axis | The frontier uses an unmeasured recovery parameter. | The evaluation calls recovery a requirement axis, not a measured mitigation result, and keeps mitigation overhead as a future-model input. | `paper/4.Evaluation.tex`, `paper/5.Discussion.tex` |
| Simulator choice sensitivity | State-vector cuQuantum can overstate cost for tensor-network-friendly circuits. | The paper states that cuQuantum is the stable instrumentation path and that tensor-network, path-integral, stabilizer, or specialized simulators could shift the measured quantum path. | `paper/5.Discussion.tex` |
| Benchmark-suite context | The related work may miss modern quantum benchmark suites. | The introduction and related work now position against SupermarQ, QASMBench, MQT Bench, and QAOAKit. | `paper/1.Introduction.tex`, `paper/5.RelatedWork.tex`, `paper/references.bib` |
| QAOA tuning | Fixed-grid QAOA may understate optimization quality. | The discussion calls fixed-grid QAOA a workload-representativeness limitation and separates this from the paper's threshold-modeling claim. | `paper/5.Discussion.tex` |
| Scaling concern | The pipeline may only work for small single-node runs. | The large profile runs through 32 Perlmutter GPU nodes, with weak and fixed-work scaling reported. | `paper/4.Evaluation.tex`, `paper/figures/scaling_summary.pdf` |
| Timing stability concern | Results may be one-time CUDA/Python first-use artifacts. | A warmup-separated repeat timing gate completed with 12 measured trials and max quantum-runtime CV 0.0400. | `paper/4.Evaluation.tex`, `data/processed/perlmutter/repeat_timing_gate_latest.json` |
| Artifact traceability | The paper numbers may not be traceable to files. | The artifact manifest maps claims to jobs, scripts, processed artifacts, figures, and audit checks. | `data/processed/perlmutter/paper_artifact_manifest.md`, `scripts/audit_paper_evidence.py` |
| Raw JSON auditability | Summaries alone may be too indirect for external checking. | The artifact map points to processed summaries, selected raw subsets, accounting records, and scripts that reproduce the paper tables and figures. | `paper/5.Discussion.tex`, `data/processed/perlmutter/paper_artifact_manifest.md`, `scripts/audit_paper_evidence.py` |
| Submission hygiene | The package may contain undefined references, personal paths, or nonanonymous metadata. | The readiness audit checks page count, HPCA line spacing, undefined references, BibTeX warnings, source anonymity, PDF metadata anonymity, TODOs, and artifact documentation. | `data/processed/perlmutter/submission_readiness_audit.md`, `scripts/audit_submission_readiness.py` |

Remaining paper-risk notes:

- The result is a threshold-modeling paper, not a claim of current quantum
  advantage.
- The chemistry workloads are active-space evidence, not production-scale
  drug-discovery campaigns.
- The scaling result is throughput scaling over independent application cases,
  not distributed simulation of one large circuit.
- The next submission pass should focus on prose polish, venue-specific
  formatting, and tightening any table/figure captions that reviewers may read
  before the full methodology.
