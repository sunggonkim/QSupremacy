# Paper Draft

Target: ATC-style quantum supremacy modeling and analysis paper.

Status: evidence-backed draft. The manuscript now includes measured Perlmutter results for the digits calibration sweep, the 3,552-case practical suite, weak/strong scaling through 32 GPU nodes, strengthened native baselines, chemistry active-space coverage, advantage-frontier analysis, and a bottleneck taxonomy. It now builds with the ATC 2026 recommended ACM `acmart` SIGPLAN-style template.

Current readiness audit: `scripts/audit_submission_readiness.py` reports `EVIDENCE_READY_WITH_SUBMISSION_RISKS`. Blocking evidence, build, and template checks pass; the remaining explicit risk is full warmup-separated repeated hardware trials.

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
- Submission-readiness audit: complete and currently `EVIDENCE_READY_WITH_SUBMISSION_RISKS`.
- Remaining submission risk: repeated hardware trials and explicit warmup-separated timing.

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

## Sources To Check Before Submission

- ATC CFP and formatting instructions for the chosen year.
- Target conference artifact evaluation policy.
- NERSC Perlmutter job, QOS, and charge policy.
- NVIDIA cuQuantum and cuStateVec documentation.
