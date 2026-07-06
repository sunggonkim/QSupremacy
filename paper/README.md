# Paper

Target: HPCA-style architecture-guided practical quantum-advantage modeling and
analysis paper. The submitted display system name is QArchGauge.

The manuscript is in `paper/0.Main.tex` with numbered section files. The built
PDF is `paper/main.pdf`.

## Build

```bash
make -B -C paper
```

The current expanded-evidence build produces a 15-page PDF with references
starting on page 13. The evidence is complete, but the final submission draft
must be compressed back to the 11-page HPCA body budget.

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
submission readiness EVIDENCE_READY_WITH_SUBMISSION_RISKS, warning_count 1
```

For a low-cost environment check:

```bash
scripts/run_login_smoke.sh
```

## Sources

Accepted-paper sources used for structure and style reference are unpacked under
`paper/PreviousPapers/` and are intentionally ignored by git. The paper follows
their section rhythm, RQ-style evaluation structure, `subfigure` usage, compact
table style, shared legend panels, and selective observation boxes without
copying prose.
