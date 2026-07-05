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
REPEAT_GATE_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "repeat_timing_gate_latest.json"
)
PREVIOUS_ALIGNMENT_JSON = os.path.join(
    ROOT,
    "data",
    "processed",
    "perlmutter",
    "previous_paper_alignment_metrics.json",
)
REVIEWER_RESPONSE_AUDIT_JSON = os.path.join(
    ROOT,
    "data",
    "processed",
    "perlmutter",
    "reviewer_response_audit.json",
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


def tracked_file(rel_path):
    code, _, _ = run(["git", "ls-files", "--error-unmatch", rel_path])
    return code == 0


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
    # HPCA uses US Letter with 0.7in top and 1.0in bottom margins.
    text_height_pt = (11.0 - 0.7 - 1.0) * 72.27
    return text_height_pt / max(lines_per_column, 1)


def pdf_metadata_text():
    path = os.path.join(ROOT, "paper", "main.pdf")
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        raw = f.read().decode("latin-1", errors="replace")
    snippets = []
    for key in ["/Author", "/Title", "/Subject", "/Keywords", "/Creator", "/Producer"]:
        for match in re.finditer(re.escape(key), raw):
            start = max(match.start() - 20, 0)
            end = min(match.end() + 160, len(raw))
            snippets.append(raw[start:end])
    return "\n".join(snippets)


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


def markdown_paths(text):
    paths = []
    for match in re.findall(r"`([^`]+)`", text):
        if (
            "/" in match
            and not match.startswith("/")
            and not match.startswith("http")
            and "*" not in match
        ):
            paths.append(match)
    return sorted(set(paths))


def newest_existing(paths):
    newest_path = None
    newest_mtime = -1.0
    for rel_path in paths:
        path = os.path.join(ROOT, rel_path)
        if not os.path.exists(path):
            continue
        mtime = os.path.getmtime(path)
        if mtime > newest_mtime:
            newest_path = rel_path
            newest_mtime = mtime
    return newest_path, newest_mtime


def main():
    evidence = {}
    if exists("data/processed/perlmutter/paper_evidence_audit.json"):
        try:
            evidence = json.loads(
                read_text("data/processed/perlmutter/paper_evidence_audit.json")
            )
        except ValueError:
            evidence = {}
    repeat_gate = {}
    if os.path.exists(REPEAT_GATE_JSON):
        try:
            with open(REPEAT_GATE_JSON, errors="replace") as f:
                repeat_gate = json.load(f)
        except ValueError:
            repeat_gate = {}
    previous_alignment_metrics = {}
    if os.path.exists(PREVIOUS_ALIGNMENT_JSON):
        try:
            with open(PREVIOUS_ALIGNMENT_JSON, errors="replace") as f:
                previous_alignment_metrics = json.load(f)
        except ValueError:
            previous_alignment_metrics = {}
    reviewer_response_audit = {}
    if os.path.exists(REVIEWER_RESPONSE_AUDIT_JSON):
        try:
            with open(REVIEWER_RESPONSE_AUDIT_JSON, errors="replace") as f:
                reviewer_response_audit = json.load(f)
        except ValueError:
            reviewer_response_audit = {}

    main_tex = read_text("paper/0.Main.tex")
    main_log = read_text("paper/main.log") if exists("paper/main.log") else ""
    blg = read_text("paper/main.blg") if exists("paper/main.blg") else ""
    overfull_hits = [
        "{}".format(index)
        for index, line in enumerate(main_log.splitlines(), start=1)
        if "Overfull \\hbox" in line
    ]
    root_readme = read_text("README.md") if exists("README.md") else ""
    paper_readme = read_text("paper/README.md") if exists("paper/README.md") else ""
    reviewer_notes = (
        read_text("paper/reviewer_readiness.md")
        if exists("paper/reviewer_readiness.md")
        else ""
    )
    line_by_line_response = (
        read_text("paper/reviewer_line_by_line_response.md")
        if exists("paper/reviewer_line_by_line_response.md")
        else ""
    )
    previous_alignment = (
        read_text("paper/previous_paper_alignment.md")
        if exists("paper/previous_paper_alignment.md")
        else ""
    )
    previous_completion = (
        read_text("paper/previous_paper_completion_audit.md")
        if exists("paper/previous_paper_completion_audit.md")
        else ""
    )
    reviewer_paths = markdown_paths(reviewer_notes)
    missing_reviewer_paths = [
        rel_path for rel_path in reviewer_paths if not exists(rel_path)
    ]
    untracked_reviewer_paths = [
        rel_path for rel_path in reviewer_paths if exists(rel_path) and not tracked_file(rel_path)
    ]
    pages = pdf_pages()
    ref_start_page = references_start_page()
    leading_points = hpca_leading_points()
    metadata_text = pdf_metadata_text()
    bib_text = read_text("paper/references.bib") if exists("paper/references.bib") else ""
    bbl_text = read_text("paper/main.bbl") if exists("paper/main.bbl") else ""

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
        for name in sorted(os.listdir(os.path.join(ROOT, "paper", "figures")))
        if name.endswith(".pdf")
    ]
    build_inputs = paper_sources + figure_sources
    newest_input, newest_input_mtime = newest_existing(build_inputs)
    pdf_mtime = (
        os.path.getmtime(os.path.join(ROOT, "paper", "main.pdf"))
        if exists("paper/main.pdf")
        else -1.0
    )
    log_mtime = (
        os.path.getmtime(os.path.join(ROOT, "paper", "main.log"))
        if exists("paper/main.log")
        else -1.0
    )
    todo_hits = grep_any(r"\b(TODO|TBD|placeholder|undefined citation)\b", paper_sources)
    anonymity_sources = [
        rel_path
        for rel_path in paper_sources
        if rel_path != "paper/references.bib"
    ] + ["paper/README.md"]
    anonymity_hits = grep_any(
        r"(sgkim|sunggon|sung\s+gon|seoultech|hpcbigdata|/global|/pscratch|github\.com/sunggonkim)",
        anonymity_sources,
    )
    metadata_anonymity_hits = [
        hit
        for hit in re.findall(
            r"sgkim|sunggon|sung\s+gon|seoultech|hpcbigdata|/global|/pscratch|github\.com/sunggonkim",
            metadata_text,
            re.IGNORECASE,
        )
    ]

    checks = [
        check("main_pdf_exists", exists("paper/main.pdf"), "error", "paper/main.pdf exists"),
        check(
            "page_count_known",
            pages is not None,
            "error",
            "PDF page count can be read from pdfinfo or the LaTeX log",
        ),
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
            (
                "references start on page {}; HPCA 2027 allows an 11-page body before references".format(
                    ref_start_page
                )
                if ref_start_page is not None
                else "could not detect the References start page from LaTeX outputs"
            ),
        ),
        check(
            "line_spacing_hpca",
            leading_points is not None and leading_points >= 12.0,
            "warning",
            (
                "LaTeX log implies {:.2f}pt leading from the HPCA text block".format(
                    leading_points
                )
                if leading_points is not None
                else "could not infer line spacing from the LaTeX log"
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
            "latex_no_overfull_hbox",
            len(overfull_hits) == 0,
            "warning",
            "LaTeX log has no overfull hbox warnings{}".format(
                "" if not overfull_hits else ": lines {}".format(", ".join(overfull_hits))
            ),
        ),
        check(
            "latex_no_lmod_noise",
            "ERROR:: command not found" not in main_log,
            "warning",
            "LaTeX log has no Lmod initialization noise",
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
            "HPCA 2027 Submission \\#NaN" in main_tex
            and "Confidential Draft" in main_tex
            and "Do NOT Distribute!!" in main_tex
            and "\\author{}" in main_tex,
            "warning",
            "current manuscript uses the HPCA title-page banner and an empty author block for double-blind review",
        ),
        check(
            "paper_source_anonymity",
            len(anonymity_hits) == 0,
            "warning",
            "paper sources and paper README contain no obvious author, institution, local-path, or personal GitHub leaks: {}".format(
                ", ".join(anonymity_hits) if anonymity_hits else "none"
            ),
        ),
        check(
            "pdf_metadata_anonymity",
            len(metadata_anonymity_hits) == 0,
            "warning",
            "PDF metadata contains no obvious author, institution, local-path, or personal GitHub leaks: {}".format(
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
            "current manuscript uses the HPCA 2027-compatible IEEEtran two-column layout, margins, column gap, and bibliography style",
        ),
        check(
            "references_list_all_authors",
            not re.search(r"\b(et al\.?|and others)\b|\\etal\b", bib_text + "\n" + bbl_text, re.IGNORECASE),
            "error",
            "references.bib and main.bbl contain no et al., and others, or \\etal shorthand",
        ),
        check(
            "ai_use_appendix",
            "\\section*{AI Use}" in main_tex and "OpenAI Codex" in main_tex,
            "warning",
            "HPCA 2027 AI-use disclosure appendix is present after references",
        ),
        check(
            "repeated_hardware_trials",
            bool(repeat_gate.get("passed")),
            "warning",
            (
                "warmup-separated repeat timing gate passed with {} measured cases and max quantum runtime CV {:.4f}".format(
                    repeat_gate.get("measured_cases", 0),
                    repeat_gate.get("max_quantum_runtime_cv", 0.0) or 0.0,
                )
                if repeat_gate.get("passed")
                else "explicit warmup-separated repeated hardware trials are not yet measured"
            ),
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
            "README files document paper-readiness audits and the allocation-free login smoke gate",
        ),
        check(
            "reviewer_risk_map_documented",
            exists("paper/reviewer_readiness.md")
            and "Novelty boundary" in reviewer_notes
            and "Native baseline strength" in reviewer_notes
            and "Toy workload concern" in reviewer_notes
            and "Practical chemistry concern" in reviewer_notes
            and "Hardware projection concern" in reviewer_notes
            and "Quality concern" in reviewer_notes
            and "Fault-tolerance model" in reviewer_notes
            and "Worked hardware scenario" in reviewer_notes
            and "Simulator choice sensitivity" in reviewer_notes
            and "Quality normalization" in reviewer_notes
            and "Tolerance sensitivity" in reviewer_notes
            and "Benchmark-suite context" in reviewer_notes
            and "QHPC workflow context" in reviewer_notes
            and "QAOA tuning" in reviewer_notes
            and "ML qubit provenance" in reviewer_notes
            and "Name sensitivity" in reviewer_notes
            and "Raw JSON auditability" in reviewer_notes
            and "Line-by-line response" in reviewer_notes
            and "Scaling concern" in reviewer_notes
            and "Timing stability concern" in reviewer_notes
            and "Artifact traceability" in reviewer_notes
            and "Submission hygiene" in reviewer_notes
            and "paper/reviewer_readiness.md" in paper_readme
            and "paper/reviewer_readiness.md" in root_readme,
            "warning",
            "reviewer-risk notes cover expected acceptance risks and are linked from README files",
        ),
        check(
            "line_by_line_response_documented",
            exists("paper/reviewer_line_by_line_response.md")
            and "Line-by-Line Reviewer Response Map" in line_by_line_response
            and "Hardware projection is first-order" in line_by_line_response
            and "Problem instances are small" in line_by_line_response
            and "Native baselines may be weak" in line_by_line_response
            and "Name `QSUPREMACY` may distract" in line_by_line_response
            and "paper/reviewer_line_by_line_response.md" in root_readme
            and "paper/reviewer_line_by_line_response.md" in paper_readme,
            "warning",
            "line-by-line reviewer response map exists and is linked from README files",
        ),
        check(
            "line_by_line_response_audited",
            exists("scripts/audit_reviewer_response.py")
            and exists("data/processed/perlmutter/reviewer_response_audit.json")
            and exists("data/processed/perlmutter/reviewer_response_audit.md")
            and bool(reviewer_response_audit.get("passed"))
            and reviewer_response_audit.get("concern_count", 0) >= 16
            and reviewer_response_audit.get("author_question_count", 0) >= 10
            and "scripts/audit_reviewer_response.py" in root_readme
            and "reviewer_response_audit.md" in root_readme
            and "scripts/audit_reviewer_response.py" in paper_readme
            and "reviewer_response_audit.md" in paper_readme,
            "warning",
            "line-by-line reviewer response coverage is machine-audited and linked",
        ),
        check(
            "reviewer_risk_evidence_paths_valid",
            exists("paper/reviewer_readiness.md")
            and len(reviewer_paths) >= 12
            and not missing_reviewer_paths
            and not untracked_reviewer_paths,
            "warning",
            (
                "reviewer-risk evidence paths are present and tracked: {} paths".format(
                    len(reviewer_paths)
                )
                if not missing_reviewer_paths and not untracked_reviewer_paths
                else "missing paths: {}; untracked paths: {}".format(
                    ", ".join(missing_reviewer_paths) if missing_reviewer_paths else "none",
                    ", ".join(untracked_reviewer_paths) if untracked_reviewer_paths else "none",
                )
            ),
        ),
        check(
            "previous_paper_alignment_documented",
            exists("paper/previous_paper_alignment.md")
            and "AURORA-Q" in previous_alignment
            and "ScaleQsim" in previous_alignment
            and "Introduction comparison table" in previous_alignment
            and "Evaluation setup lead-ins" in previous_alignment
            and "Hardware, Benchmark, Baselines, Feasibility" in previous_alignment
            and "Non-Copying Boundary" in previous_alignment
            and "paper/previous_paper_alignment.md" in root_readme
            and "paper/previous_paper_alignment.md" in paper_readme,
            "warning",
            "previous-paper paragraph and style alignment is documented and linked",
        ),
        check(
            "previous_paper_alignment_metrics",
            exists("scripts/audit_previous_paper_alignment.py")
            and exists("data/processed/perlmutter/previous_paper_alignment_metrics.json")
            and exists("data/processed/perlmutter/previous_paper_alignment_metrics.md")
            and "scripts/audit_previous_paper_alignment.py" in root_readme
            and "scripts/audit_previous_paper_alignment.py" in paper_readme
            and "previous_paper_alignment_metrics.md" in root_readme
            and "previous_paper_alignment_metrics.md" in paper_readme
            and all(previous_alignment_metrics.get("checks", {}).values()),
            "warning",
            "previous-paper word, paragraph, heading, style, role-marker, paragraph-role, current-line, and template-line metrics are generated and linked",
        ),
        check(
            "previous_paper_completion_audit",
            exists("paper/previous_paper_completion_audit.md")
            and "Requirement Audit" in previous_completion
            and "Line-by-line traceability" in previous_completion
            and "Paragraph-by-paragraph roles" in previous_completion
            and "Word-count alignment" in previous_completion
            and "Style alignment" in previous_completion
            and "ALIGNED_BY_COUNTS" in previous_completion
            and "Non-Copying Boundary" in previous_completion
            and "paper/previous_paper_completion_audit.md" in root_readme
            and "paper/previous_paper_completion_audit.md" in paper_readme,
            "warning",
            "previous-paper completion audit covers logic, line, paragraph, word-count, and style requirements",
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

    with open(OUT_MD, "w") as f:
        f.write("# Submission Readiness Audit\n\n")
        f.write("Status: **{}**\n\n".format(status))
        f.write("Page count: `{}`\n\n".format(pages if pages is not None else "unknown"))
        f.write(
            "References start page: `{}`\n\n".format(
                ref_start_page if ref_start_page is not None else "unknown"
            )
        )
        f.write(
            "Inferred line spacing: `{}` pt\n\n".format(
                "{:.2f}".format(leading_points)
                if leading_points is not None
                else "unknown"
            )
        )
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
