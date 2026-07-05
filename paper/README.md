# Paper Draft

Target: ATC-style quantum supremacy modeling and analysis paper.

Status: evidence-backed draft. The manuscript now includes measured Perlmutter results for the digits calibration sweep, the 3,552-case practical suite, weak scaling through 32 GPU nodes, fixed-work scaling through 16 GPU nodes plus a matching 32-node full-profile point, strengthened native baselines, chemistry active-space coverage, advantage-frontier analysis, and a bottleneck taxonomy. It now builds with the ATC 2026 recommended ACM `acmart` SIGPLAN-style template.

Current readiness audit: `scripts/audit_submission_readiness.py` reports `SUBMISSION_READY`. Blocking evidence, build, template, and repeat-timing checks pass. The remaining work is paper polish for the chosen submission target, not missing core experimental evidence.

Internal reviewer-risk notes are tracked in `paper/reviewer_readiness.md`. The
submission-readiness audit checks that this file covers the main expected
criticisms: novelty boundary, native baselines, toy workloads, chemistry
coverage, hardware projection, quality, scaling, timing stability, artifact
traceability, and submission hygiene.

Note: the ATC 2026 CFP lists June 10, 2026 as the submission deadline. As of July 3, 2026, that deadline has passed, so this directory should be treated as an ATC-style manuscript for the next viable submission target unless the plan changes.

## Draft Files

```text
paper/
├── README.md
├── 0.Main.tex
├── 1.Introduction.tex
├── 2.Background.tex
├── 3.Design.tex
├── 4.Evaluation.tex
├── 5.RelatedWork.tex
├── 6.Conclusion.tex
├── 7.Ack.tex
├── main.tex
├── references.bib
├── reviewer_readiness.md
├── Makefile
├── figures/
└── tables/
```

The file structure intentionally mirrors the accepted ScaleQsim and AURORA-Q papers in `paper/PreviousPapers/`: a main LaTeX file plus numbered section files. `main.tex` is a compatibility wrapper that inputs `0.Main.tex`.

## Previous Papers

Accepted-paper sources are unpacked locally for structure reference:

```text
paper/PreviousPapers/
├── ScaleQsim_SIGMETRICS26/
│   ├── sample-acmsmall-submission.tex
│   ├── 1.introduction.tex
│   ├── 2.Background.tex
│   ├── 3.Design.tex
│   ├── 4.Evaluation.tex
│   ├── 5.Related Work.tex
│   ├── 6.Conclusion.tex
│   └── 7.Ack.tex
└── AURORA_Q_ICDCS26/
    ├── 0. Main.tex
    ├── 1.Introduction.tex
    ├── 2.Background.tex
    ├── 3.Design.tex
    ├── 4.Evaluation.tex
    ├── 5.Related work.tex
    ├── 6.Conclusion.tex
    └── 7.Ack.tex
```

`paper/PreviousPapers/` is intentionally git-ignored to avoid accidentally publishing accepted-paper source archives and extracted materials.

## Paper Thesis

Quantum supremacy should be modeled as an application-level break-even condition, not by comparing a CPU state-vector simulator against cuQuantum. This paper studies the end-to-end gap between native HPC/ML applications and quantum-circuit versions of the same workloads, then analyzes the quantum hardware requirements needed to beat the native path.

## Submission Readiness Checklist

- Login-node smoke gate: complete.
- Perlmutter shared-GPU and GPU-node sweeps: complete.
- Full GPU-node bundled execution: complete through 32 nodes.
- `sklearn digits` native ML, quantum kernel, and QNN/VQC paths: complete.
- Practical suite across ML, chemistry, optimization, and simulation: complete.
- Stronger native baselines and chemistry/simulation accept-profile gates: complete.
- Advantage frontier and projection table: complete.
- `sacct` accounting records for completed jobs: recorded in `data/raw/perlmutter/accounting/`.
- Evidence audit: complete and currently PASS.
- Submission-readiness audit: complete and currently `SUBMISSION_READY`.
- Warmup-separated repeat timing: complete as job `55516885`.

## Build

```bash
cd paper
make
```

The Makefile loads `texlive/2024` on Perlmutter before running `pdflatex`. The current LaTeX file uses the ATC 2026 recommended ACM `acmart` SIGPLAN-style scaffold with anonymous Paper ID metadata, CCS concepts, keywords, page numbers, and ACM reference formatting.

Run the current automated checks from the repository root:

```bash
python3 scripts/audit_paper_evidence.py
python3 scripts/audit_submission_readiness.py
make -B -C paper
```

## Artifact Quickstart

From the repository root, the shortest paper-readiness check is:

```bash
make -B -C paper
python3 scripts/audit_paper_evidence.py
python3 scripts/audit_submission_readiness.py
```

The expected state is a 12-page `paper/main.pdf`, a PASS paper-evidence audit,
and a `SUBMISSION_READY` readiness audit. The audits check the committed
processed summaries, accounting records, figures, page count, citations,
anonymous template metadata, repeat-timing evidence, and the paper
claim-to-artifact manifest in
`data/processed/perlmutter/paper_artifact_manifest.md`.

For a low-cost rerun on Perlmutter, use the login smoke gate first:

```bash
scripts/run_login_smoke.sh
```

This validates imports, cuQuantum availability, small state-vector correctness,
and the application-level native-versus-quantum workload path without spending
GPU allocation.

## Repeat Timing Gate

The completed timing-confidence check is intentionally small and allocation
safe, so it can be rerun when the software stack changes:

```bash
sbatch jobs/perlmutter/practical_suite_repeat_timing_gate.sbatch
```

The job uses one GPU node, four A100 tasks, one warmup per workload family, and
three measured trials per family. It writes the latest summarized evidence to
`data/processed/perlmutter/repeat_timing_gate_latest.json` and Markdown beside
it. The submission-readiness audit consumes that summary directly.

Current status: job `55516885` completed in 58 seconds with exit `0:0`. The
gate passed with four warmup cases, 12 measured trials, zero failed trials, and
max quantum-runtime CV `0.0400`. The previous attempt, job `55516720`, failed
after 21 seconds because the inner `srun` shell did not load the CUDA 12.9
library path required by cuQuantum. The job script now loads
`cudatoolkit/12.9` inside each task.

## Sources To Check Before Submission

- ATC CFP and formatting instructions for the chosen year.
- Target conference artifact evaluation policy.
- NERSC Perlmutter job, QOS, and charge policy.
- NVIDIA cuQuantum and cuStateVec documentation.
