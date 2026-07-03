# Paper Draft

Target: ATC-style quantum supremacy modeling and analysis paper.

Status: scaffold only. Do not submit this draft as-is. The current draft contains methodology, workload design, and result placeholders, but not enough experimental evidence for an ATC submission.

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

## Required Results Before Submission

- Login-node smoke gate must pass.
- Perlmutter shared-GPU sweep must run long enough to avoid allocation waste.
- Full GPU-node jobs must use all requested GPUs.
- `sklearn digits` native ML baselines must be complete.
- Quantum kernel classifier must be complete.
- QNN/VQC classifier must be complete.
- Results must include repeated trials, variance, warmup policy, and time-to-quality.
- `sacct` metadata must be parsed for elapsed time, queue time, and charged node-hours.
- Hardware projection must report required gate time, shot throughput, logical qubits, and error overhead.

## Build

```bash
cd paper
make
```

The Makefile loads `texlive/2024` on Perlmutter before running `pdflatex`. The current LaTeX file uses a lightweight two-column article scaffold. Replace it with the official target conference template before submission.

## Sources To Check Before Submission

- ATC CFP and formatting instructions for the chosen year.
- Target conference artifact evaluation policy.
- NERSC Perlmutter job, QOS, and charge policy.
- NVIDIA cuQuantum and cuStateVec documentation.
