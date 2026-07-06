# Paper

Target: HPCA-style architecture-guided practical quantum-advantage modeling and
analysis paper. The submitted display system name is QArchGauge.

The manuscript is in `paper/0.Main.tex` with numbered section files. The built
PDF is `paper/main.pdf`.

## Build

```bash
make -B -C paper
```

The current build produces a 13-page PDF with references starting on page 12.

## Artifact Quickstart

Run from the repository root:

```bash
make -B -C paper
python3 scripts/audit_paper_evidence.py
python3 scripts/audit_previous_paper_alignment.py
python3 scripts/audit_previous_paper_deep_trace.py
python3 scripts/audit_previous_paper_style.py
python3 scripts/audit_submission_readiness.py
```

Expected state:

```text
paper/main.pdf builds
paper evidence audit PASS
previous-paper alignment/deep-trace/style audits PASS
submission readiness SUBMISSION_READY
```

For a low-cost environment check:

```bash
scripts/run_login_smoke.sh
```

## Sources

Accepted-paper sources used for structure and style reference are unpacked under
`paper/PreviousPapers/` and are intentionally ignored by git. The paper follows
their section rhythm, RQ-style evaluation structure, `subfigure` usage, compact
table style, and `\textbf{}` lead-in rhythm without copying prose.
