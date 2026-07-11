# Paper

Target: HPCA-style architecture-guided practical quantum-advantage modeling and
analysis paper. The submitted display system name is QArchGauge.

The manuscript is in `paper/0.Main.tex` with numbered section files. The built
PDF is `paper/main.pdf`.

## Build

```bash
make -B -C paper
```

The current build produces a 14-page PDF with references starting on page 12,
so the body fits the 11-page HPCA submission budget. The title-page submission
number remains `NaN` until HotCRP assigns the real paper number.

The current evaluation includes the completed regular 16/32/64-node weak-scaling
ladder and direct 7,104-case fixed-work runs on 64, 128, and 256 GPUs. The
pending 32-GPU fixed-work job 55792240 is optional extra evidence; the submitted
paper uses only direct fixed-work points in the strong-scaling figure.

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
submission readiness SUBMISSION_READY, warning_count 0, references_start_page 12
```

The PDF readability spot check also verifies that `QArchGauge` extracts cleanly
from the PDF text and that the weak-scaling figure appears before the
strong-scaling figure.

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
