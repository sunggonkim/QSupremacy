#!/usr/bin/env python3
"""Audit manuscript readiness beyond evidence availability."""

import json
import os
import re
import subprocess


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "submission_readiness_audit.json"
)
OUT_MD = os.path.join(
    ROOT, "data", "processed", "perlmutter", "submission_readiness_audit.md"
)


def read_text(rel_path):
    with open(os.path.join(ROOT, rel_path), errors="replace") as f:
        return f.read()


def exists(rel_path):
    return os.path.exists(os.path.join(ROOT, rel_path))


def run(cmd):
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except OSError as exc:
        return 127, "", str(exc)


def check(name, passed, severity, detail):
    return {
        "name": name,
        "passed": bool(passed),
        "severity": severity,
        "detail": detail,
    }


def pdf_pages():
    code, stdout, _ = run(["pdfinfo", "paper/main.pdf"])
    if code == 0:
        match = re.search(r"^Pages:\s+(\d+)", stdout, re.MULTILINE)
        if match:
            return int(match.group(1))
    if exists("paper/main.log"):
        match = re.search(r"Output written on main\.pdf \((\d+) pages", read_text("paper/main.log"))
        if match:
            return int(match.group(1))
    return None


def grep_any(pattern, rel_paths):
    hits = []
    regex = re.compile(pattern, re.IGNORECASE)
    for rel_path in rel_paths:
        if not exists(rel_path):
            continue
        for index, line in enumerate(read_text(rel_path).splitlines(), start=1):
            if regex.search(line):
                hits.append("{}:{}".format(rel_path, index))
    return hits


def main():
    evidence = {}
    if exists("data/processed/perlmutter/paper_evidence_audit.json"):
        try:
            evidence = json.loads(
                read_text("data/processed/perlmutter/paper_evidence_audit.json")
            )
        except ValueError:
            evidence = {}

    main_tex = read_text("paper/0.Main.tex")
    main_log = read_text("paper/main.log") if exists("paper/main.log") else ""
    blg = read_text("paper/main.blg") if exists("paper/main.blg") else ""
    pages = pdf_pages()

    paper_sources = [
        "paper/0.Main.tex",
        "paper/1.Introduction.tex",
        "paper/2.Background.tex",
        "paper/3.Design.tex",
        "paper/4.Evaluation.tex",
        "paper/5.Discussion.tex",
        "paper/5.RelatedWork.tex",
        "paper/6.Conclusion.tex",
        "paper/references.bib",
    ]
    todo_hits = grep_any(r"\b(TODO|TBD|placeholder|undefined citation)\b", paper_sources)

    checks = [
        check("main_pdf_exists", exists("paper/main.pdf"), "error", "paper/main.pdf exists"),
        check("page_count_known", pages is not None, "error", "pdfinfo can read page count"),
        check(
            "page_count_atc_style",
            pages is not None and pages <= 12,
            "warning",
            "current page count is {}; typical systems submissions need a target-specific page budget".format(
                pages if pages is not None else "unknown"
            ),
        ),
        check(
            "latex_no_undefined",
            not re.search(
                r"undefined|Citation .* undefined|Reference .* undefined|There were undefined references",
                main_log,
                re.IGNORECASE,
            ),
            "error",
            "LaTeX log has no undefined references or citations",
        ),
        check(
            "bibtex_no_warnings",
            "Warning--" not in blg,
            "error",
            "BibTeX log has no warnings",
        ),
        check(
            "paper_no_todos",
            len(todo_hits) == 0,
            "error",
            "paper sources contain no TODO/TBD/placeholder hits: {}".format(
                ", ".join(todo_hits) if todo_hits else "none"
            ),
        ),
        check(
            "evidence_audit_pass",
            bool(evidence.get("passed")),
            "error",
            "paper evidence audit reports PASS",
        ),
        check(
            "anonymous_submission",
            "Anonymous Authors" in main_tex,
            "warning",
            "current manuscript keeps anonymous authors",
        ),
        check(
            "target_template_selected",
            "\\documentclass[10pt,twocolumn]{article}" not in main_tex,
            "warning",
            "current manuscript still uses lightweight article class rather than a target conference template",
        ),
        check(
            "repeated_hardware_trials",
            False,
            "warning",
            "explicit warmup-separated repeated hardware trials are not yet measured for every sensitivity point",
        ),
    ]

    blocking_errors = [item for item in checks if item["severity"] == "error" and not item["passed"]]
    warnings = [item for item in checks if item["severity"] == "warning" and not item["passed"]]
    if blocking_errors:
        status = "BLOCKED"
    elif warnings:
        status = "EVIDENCE_READY_WITH_SUBMISSION_RISKS"
    else:
        status = "SUBMISSION_READY"

    summary = {
        "status": status,
        "page_count": pages,
        "blocking_error_count": len(blocking_errors),
        "warning_count": len(warnings),
        "checks": checks,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    with open(OUT_MD, "w") as f:
        f.write("# Submission Readiness Audit\n\n")
        f.write("Status: **{}**\n\n".format(status))
        f.write("Page count: `{}`\n\n".format(pages if pages is not None else "unknown"))
        f.write("| Check | Severity | Status | Detail |\n")
        f.write("| --- | --- | --- | --- |\n")
        for item in checks:
            f.write(
                "| {} | {} | {} | {} |\n".format(
                    item["name"],
                    item["severity"],
                    "PASS" if item["passed"] else "RISK",
                    item["detail"].replace("|", "/"),
                )
            )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
