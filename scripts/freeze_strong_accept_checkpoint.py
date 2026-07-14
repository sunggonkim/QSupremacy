#!/usr/bin/env python3
"""Freeze hashes and worktree scope before strong-accept revisions."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from strong_accept_common import DEFAULT_INPUT, ROOT, json_dump, relative


CORE_PATHS = (
    "plan.md",
    "README.md",
    "paper/main.pdf",
    "paper/0.Main.tex",
    "paper/1.Introduction.tex",
    "paper/2.Background.tex",
    "paper/3.Design.tex",
    "paper/4.Evaluation.tex",
    "paper/5.Discussion.tex",
    "paper/5.RelatedWork.tex",
    "paper/6.Conclusion.tex",
    "data/processed/perlmutter/paper_artifact_manifest.json",
    "data/processed/perlmutter/paper_evidence_audit.json",
    "data/processed/perlmutter/submission_readiness_audit.json",
    "data/processed/perlmutter/physical_architecture_dse.json",
    "data/processed/perlmutter/projection_invariant_audit.json",
)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args):
    return subprocess.check_output(
        ("git",) + args,
        cwd=ROOT,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def pdf_pages(path):
    try:
        output = subprocess.check_output(("pdfinfo", str(path)), text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        output = None
    if output is not None:
        for line in output.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":", 1)[1].strip())
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(path)).pages)
    except (ImportError, OSError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=(
            "data/processed/perlmutter/"
            "strong_accept_checkpoint_20260713.json"
        ),
    )
    args = parser.parse_args()

    files = []
    for name in CORE_PATHS + (relative(DEFAULT_INPUT),):
        path = ROOT / name
        files.append({
            "path": name,
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256(path) if path.exists() else None,
        })

    pdf = ROOT / "paper/main.pdf"
    status = git("status", "--short")
    payload = {
        "schema": "qarchgauge.strong-accept-checkpoint.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": (
            "Pre-P0 checkpoint. Hashes preserve the current user worktree; "
            "this artifact is not a clean-tree claim."
        ),
        "git": {
            "head": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "status_lines": status.splitlines() if status else [],
            "dirty_entry_count": len(status.splitlines()) if status else 0,
        },
        "paper": {
            "pdf_pages": pdf_pages(pdf) if pdf.exists() else None,
            "pdf_sha256": sha256(pdf) if pdf.exists() else None,
        },
        "files": files,
    }
    json_dump(ROOT / args.output, payload)
    print(json.dumps({
        "output": args.output,
        "head": payload["git"]["head"],
        "dirty_entries": payload["git"]["dirty_entry_count"],
        "pdf_pages": payload["paper"]["pdf_pages"],
    }, indent=2))


if __name__ == "__main__":
    main()
