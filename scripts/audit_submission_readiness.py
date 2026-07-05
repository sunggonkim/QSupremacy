#!/usr/bin/env python3
"""Audit manuscript readiness using JSON artifacts and the built PDF."""

import json
import os
import re
import subprocess


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "submission_readiness_audit.json"
)


def path(rel_path):
    return os.path.join(ROOT, rel_path)


def exists(rel_path):
    return os.path.exists(path(rel_path))


def read_text(rel_path):
    with open(path(rel_path), errors="replace") as f:
        return f.read()


def load_json(rel_path):
    if not exists(rel_path):
        return {}
    try:
        with open(path(rel_path), errors="replace") as f:
            return json.load(f)
    except ValueError:
        return {}


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
        match = re.search(
            r"Output written on main\.pdf \((\d+) pages",
            read_text("paper/main.log"),
        )
        if match:
            return int(match.group(1))
    return None


def references_start_page():
    if exists("paper/main.aux"):
        match = re.search(
            r"\\contentsline\s+\{section\}\{References\}\{(\d+)\}",
            read_text("paper/main.aux"),
        )
        if match:
            return int(match.group(1))
    if exists("paper/main.log"):
        match = re.search(r"\(\./main\.bbl.*?\[(\d+)\]", read_text("paper/main.log"), re.S)
        if match:
            return int(match.group(1))
    return None


def hpca_leading_points():
    if not exists("paper/main.log"):
        return None
    match = re.search(r"-- Lines per column: (\d+)", read_text("paper/main.log"))
    if not match:
        return None
    lines_per_column = int(match.group(1))
    text_height_pt = (11.0 - 0.7 - 1.0) * 72.27
    return text_height_pt / max(lines_per_column, 1)


def newest_existing(paths):
    newest_path = None
    newest_mtime = -1.0
    for rel_path in paths:
        if not exists(rel_path):
            continue
        mtime = os.path.getmtime(path(rel_path))
        if mtime > newest_mtime:
            newest_path = rel_path
            newest_mtime = mtime
    return newest_path, newest_mtime


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


def pdf_metadata_text():
    if not exists("paper/main.pdf"):
        return ""
    with open(path("paper/main.pdf"), "rb") as f:
        raw = f.read().decode("latin-1", errors="replace")
    snippets = []
    for key in ["/Author", "/Title", "/Subject", "/Keywords", "/Creator", "/Producer"]:
        for match in re.finditer(re.escape(key), raw):
            snippets.append(raw[max(match.start() - 20, 0): min(match.end() + 160, len(raw))])
    return "\n".join(snippets)


def main():
    evidence = load_json("data/processed/perlmutter/paper_evidence_audit.json")
    repeat_gate = load_json("data/processed/perlmutter/repeat_timing_gate_latest.json")
    previous_alignment = load_json(
        "data/processed/perlmutter/previous_paper_alignment_metrics.json"
    )
    previous_style = load_json("data/processed/perlmutter/previous_paper_style_audit.json")
    previous_trace = load_json("data/processed/perlmutter/previous_paper_deep_trace.json")

    main_tex = read_text("paper/0.Main.tex")
    main_log = read_text("paper/main.log") if exists("paper/main.log") else ""
    blg = read_text("paper/main.blg") if exists("paper/main.blg") else ""
    bib_text = read_text("paper/references.bib") if exists("paper/references.bib") else ""
    bbl_text = read_text("paper/main.bbl") if exists("paper/main.bbl") else ""
    root_readme = read_text("README.md") if exists("README.md") else ""
    paper_readme = read_text("paper/README.md") if exists("paper/README.md") else ""

    paper_sources = [
        "paper/0.Main.tex",
        "paper/1.Introduction.tex",
        "paper/2.Background.tex",
        "paper/3.Design.tex",
        "paper/4.Evaluation.tex",
        "paper/5.Discussion.tex",
        "paper/5.RelatedWork.tex",
        "paper/6.Conclusion.tex",
        "paper/Makefile",
        "paper/main.tex",
        "paper/references.bib",
    ]
    figure_sources = [
        os.path.join("paper", "figures", name)
        for name in sorted(os.listdir(path("paper/figures")))
        if name.endswith(".pdf")
    ]
    newest_input, newest_input_mtime = newest_existing(paper_sources + figure_sources)
    pdf_mtime = os.path.getmtime(path("paper/main.pdf")) if exists("paper/main.pdf") else -1.0
    log_mtime = os.path.getmtime(path("paper/main.log")) if exists("paper/main.log") else -1.0

    pages = pdf_pages()
    ref_start_page = references_start_page()
    leading_points = hpca_leading_points()
    overfull_hits = [
        str(index)
        for index, line in enumerate(main_log.splitlines(), start=1)
        if "Overfull \\hbox" in line
    ]
    todo_hits = grep_any(r"\b(TODO|TBD|placeholder|undefined citation)\b", paper_sources)
    anonymity_sources = [
        rel_path for rel_path in paper_sources if rel_path != "paper/references.bib"
    ] + ["paper/README.md"]
    anonymity_hits = grep_any(
        r"(sgkim|sunggon|sung\s+gon|seoultech|hpcbigdata|/global|/pscratch|github\.com/sunggonkim)",
        anonymity_sources,
    )
    metadata_anonymity_hits = re.findall(
        r"sgkim|sunggon|sung\s+gon|seoultech|hpcbigdata|/global|/pscratch|github\.com/sunggonkim",
        pdf_metadata_text(),
        re.IGNORECASE,
    )

    checks = [
        check("main_pdf_exists", exists("paper/main.pdf"), "error", "paper/main.pdf exists"),
        check("page_count_known", pages is not None, "error", "PDF page count can be read"),
        check(
            "main_pdf_fresh",
            exists("paper/main.pdf")
            and newest_input is not None
            and pdf_mtime >= newest_input_mtime
            and log_mtime >= newest_input_mtime,
            "error",
            (
                "paper/main.pdf and paper/main.log are newer than paper sources and figures"
                if pdf_mtime >= newest_input_mtime and log_mtime >= newest_input_mtime
                else "newest input is {}; rerun `make -B -C paper`".format(newest_input)
            ),
        ),
        check(
            "page_count_hpca_body",
            ref_start_page is not None and ref_start_page <= 12,
            "warning",
            "references start on page {}".format(ref_start_page)
            if ref_start_page is not None
            else "could not detect references start page",
        ),
        check(
            "line_spacing_hpca",
            leading_points is not None and leading_points >= 12.0,
            "warning",
            "LaTeX log implies {:.2f}pt leading".format(leading_points)
            if leading_points is not None
            else "could not infer line spacing",
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
            "latex_no_overfull_hbox",
            len(overfull_hits) == 0,
            "warning",
            "overfull hbox lines: {}".format(", ".join(overfull_hits) if overfull_hits else "none"),
        ),
        check("bibtex_no_warnings", "Warning--" not in blg, "error", "BibTeX log has no warnings"),
        check(
            "paper_no_todos",
            len(todo_hits) == 0,
            "error",
            "paper TODO/TBD/placeholder hits: {}".format(", ".join(todo_hits) if todo_hits else "none"),
        ),
        check("evidence_audit_pass", bool(evidence.get("passed")), "error", "paper evidence audit reports PASS"),
        check(
            "anonymous_submission",
            "HPCA 2027 Submission \\#NaN" in main_tex
            and "Confidential Draft" in main_tex
            and "Do NOT Distribute!!" in main_tex
            and "\\author{}" in main_tex,
            "warning",
            "HPCA title-page banner and empty double-blind author block are present",
        ),
        check(
            "paper_source_anonymity",
            len(anonymity_hits) == 0,
            "warning",
            "source anonymity hits: {}".format(", ".join(anonymity_hits) if anonymity_hits else "none"),
        ),
        check(
            "pdf_metadata_anonymity",
            len(metadata_anonymity_hits) == 0,
            "warning",
            "PDF metadata anonymity hits: {}".format(
                ", ".join(metadata_anonymity_hits) if metadata_anonymity_hits else "none"
            ),
        ),
        check(
            "target_template_selected",
            "\\documentclass[10pt,conference]{IEEEtran}" in main_tex
            and "\\usepackage[letterpaper,left=0.7in,right=0.7in,top=0.7in,bottom=1in]{geometry}" in main_tex
            and "\\setlength{\\columnsep}{0.1in}" in main_tex
            and "\\bibliographystyle{IEEEtran}" in main_tex,
            "warning",
            "HPCA-compatible IEEEtran layout markers are present",
        ),
        check(
            "references_list_all_authors",
            not re.search(r"\b(et al\.?|and others)\b|\\etal\b", bib_text + "\n" + bbl_text, re.IGNORECASE),
            "error",
            "references contain no et al. shorthand",
        ),
        check(
            "ai_use_appendix",
            "\\section*{AI Use}" in main_tex and "OpenAI Codex" in main_tex,
            "warning",
            "AI-use disclosure appendix is present after references",
        ),
        check(
            "repeated_hardware_trials",
            bool(repeat_gate.get("passed")),
            "warning",
            "repeat timing gate passed with {} measured cases".format(
                repeat_gate.get("measured_cases", 0)
            )
            if repeat_gate.get("passed")
            else "repeat timing gate has not passed",
        ),
        check(
            "artifact_quickstart_documented",
            "Paper Readiness Quickstart" in root_readme
            and "Artifact Quickstart" in paper_readme
            and "scripts/audit_paper_evidence.py" in root_readme
            and "scripts/audit_submission_readiness.py" in root_readme
            and "scripts/run_login_smoke.sh" in root_readme
            and "scripts/audit_paper_evidence.py" in paper_readme
            and "scripts/audit_submission_readiness.py" in paper_readme
            and "scripts/run_login_smoke.sh" in paper_readme,
            "warning",
            "README files document paper-readiness audits and login smoke gate",
        ),
        check(
            "previous_paper_alignment_metrics",
            exists("scripts/audit_previous_paper_alignment.py")
            and exists("data/processed/perlmutter/previous_paper_alignment_metrics.json")
            and all(previous_alignment.get("checks", {}).values()),
            "warning",
            "previous-paper section/role alignment JSON checks pass",
        ),
        check(
            "previous_paper_style_audit",
            exists("scripts/audit_previous_paper_style.py")
            and exists("data/processed/perlmutter/previous_paper_style_audit.json")
            and bool(previous_style.get("passed")),
            "warning",
            "previous-paper LaTeX style JSON audit passes",
        ),
        check(
            "previous_paper_deep_trace",
            exists("scripts/audit_previous_paper_deep_trace.py")
            and exists("data/processed/perlmutter/previous_paper_deep_trace.json")
            and bool(previous_trace.get("passed"))
            and previous_trace.get("total_traced_blocks", 0) >= 90,
            "warning",
            "previous-paper deep trace JSON covers all manuscript sections",
        ),
    ]

    blocking_errors = [item for item in checks if item["severity"] == "error" and not item["passed"]]
    warnings = [item for item in checks if item["severity"] == "warning" and not item["passed"]]
    status = "BLOCKED" if blocking_errors else (
        "EVIDENCE_READY_WITH_SUBMISSION_RISKS" if warnings else "SUBMISSION_READY"
    )

    summary = {
        "status": status,
        "page_count": pages,
        "references_start_page": ref_start_page,
        "line_spacing_points": leading_points,
        "blocking_error_count": len(blocking_errors),
        "warning_count": len(warnings),
        "checks": checks,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
