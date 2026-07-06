#!/usr/bin/env python3
"""Audit LaTeX idioms against the accepted previous-paper sources."""

import json
import os
import re


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "previous_paper_style_audit.json"
)
OUT_MD = os.devnull

CURRENT = [
    "paper/0.Main.tex",
    "paper/1.Introduction.tex",
    "paper/2.Background.tex",
    "paper/3.Design.tex",
    "paper/4.Evaluation.tex",
    "paper/5.Discussion.tex",
    "paper/5.RelatedWork.tex",
    "paper/6.Conclusion.tex",
]
PREVIOUS = [
    "paper/PreviousPapers/AURORA_Q_ICDCS26/0. Main.tex",
    "paper/PreviousPapers/AURORA_Q_ICDCS26/1.Introduction.tex",
    "paper/PreviousPapers/AURORA_Q_ICDCS26/2.Background.tex",
    "paper/PreviousPapers/AURORA_Q_ICDCS26/3.Design.tex",
    "paper/PreviousPapers/AURORA_Q_ICDCS26/4.Evaluation.tex",
    "paper/PreviousPapers/AURORA_Q_ICDCS26/5.Related work.tex",
    "paper/PreviousPapers/AURORA_Q_ICDCS26/6.Conclusion.tex",
    "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/1.introduction.tex",
    "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/2.Background.tex",
    "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/3.Design.tex",
    "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/4.Evaluation.tex",
    "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/5.Related Work.tex",
    "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/6.Conclusion.tex",
    "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/sample-acmsmall-submission.tex",
]


def read(rel_path):
    with open(os.path.join(ROOT, rel_path), errors="replace") as f:
        return f.read()


def exists(rel_path):
    return os.path.exists(os.path.join(ROOT, rel_path))


def combined(paths):
    return "\n".join(read(path) for path in paths if exists(path))


def count(pattern, text):
    return len(re.findall(pattern, text, flags=re.M))


def noindent_textbf_labels(text):
    return re.findall(r"\\noindent\\textbf\{([^}]+)\}", text)


def first_alpha(label):
    for char in label:
        if char.isalpha():
            return char
    return ""


def environments(text, name):
    pattern = r"\\begin\{" + re.escape(name) + r"\}.*?\\end\{" + re.escape(name) + r"\}"
    return re.findall(pattern, text, flags=re.S)


def caption_before_label_ratio(blocks):
    if not blocks:
        return 1.0
    good = 0
    total = 0
    for block in blocks:
        cap = block.find(r"\caption")
        lab = block.find(r"\label")
        if cap >= 0 and lab >= 0:
            total += 1
            if cap < lab:
                good += 1
    return good / float(total or 1)


def metrics(text):
    figure_blocks = environments(text, "figure") + environments(text, "figure*")
    table_blocks = environments(text, "table") + environments(text, "table*")
    subfigure_blocks = environments(text, "subfigure")
    labels = noindent_textbf_labels(text)
    lowercase_labels = [
        label for label in labels if first_alpha(label) and not first_alpha(label).isupper()
    ]
    return {
        "textbf": count(r"\\textbf\{", text),
        "noindent_textbf": len(labels),
        "lowercase_noindent_textbf": lowercase_labels,
        "figure": count(r"\\begin\{figure\}", text),
        "figure_star": count(r"\\begin\{figure\*\}", text),
        "table": count(r"\\begin\{table\}", text),
        "table_star": count(r"\\begin\{table\*\}", text),
        "subfigure_environment": len(subfigure_blocks),
        "subfloat": count(r"\\subfloat", text),
        "caption_setup": count(r"\\captionsetup", text),
        "vspace": count(r"\\vspace", text),
        "float_spacing": count(r"\\setlength\{\\(?:textfloatsep|floatsep|intextsep)\}", text),
        "scriptsize": count(r"\\scriptsize", text),
        "arraystretch": count(r"\\renewcommand\{\\arraystretch\}", text),
        "resizebox_column": count(r"\\resizebox\{\\columnwidth\}", text),
        "booktabs_rules": count(r"\\toprule|\\midrule|\\bottomrule", text),
        "hline_rules": count(r"\\hline", text),
        "caption_before_label_ratio": caption_before_label_ratio(figure_blocks + table_blocks),
        "subfigures_with_caption": sum(1 for block in subfigure_blocks if r"\caption" in block),
        "subfigures_with_label": sum(1 for block in subfigure_blocks if r"\label" in block),
        "legend_subfigures": sum(
            1 for block in subfigure_blocks if "legend" in block.lower()
        ),
    }


def check(name, passed, detail):
    return {"name": name, "passed": bool(passed), "detail": detail}


def main():
    missing_previous = [path for path in PREVIOUS if not exists(path)]
    missing_current = [path for path in CURRENT if not exists(path)]
    previous_text = combined(PREVIOUS)
    current_text = combined(CURRENT)
    previous_metrics = metrics(previous_text)
    current_metrics = metrics(current_text)

    checks = [
        check(
            "previous_sources_available",
            not missing_previous and not missing_current,
            "missing previous: {}; missing current: {}".format(missing_previous, missing_current),
        ),
        check(
            "accepted_sources_use_subfigure_style",
            previous_metrics["subfigure_environment"] >= 10,
            "previous subfigure environments: {}".format(previous_metrics["subfigure_environment"]),
        ),
        check(
            "current_uses_subcaption_package",
            r"\usepackage{subcaption}" in current_text,
            "current main preamble uses subcaption package",
        ),
        check(
            "current_uses_subfigure_environment",
            current_metrics["subfigure_environment"] >= 2,
            "current subfigure environments: {}".format(current_metrics["subfigure_environment"]),
        ),
        check(
            "current_avoids_legacy_subfloat",
            current_metrics["subfloat"] == 0,
            "current subfloat commands: {}".format(current_metrics["subfloat"]),
        ),
        check(
            "subfigures_have_caption_and_label",
            current_metrics["subfigures_with_caption"] + current_metrics["legend_subfigures"]
            >= current_metrics["subfigure_environment"]
            and current_metrics["subfigures_with_label"] + current_metrics["legend_subfigures"]
            >= current_metrics["subfigure_environment"],
            "subfigures={}, captions={}, labels={}, legend-only={}".format(
                current_metrics["subfigure_environment"],
                current_metrics["subfigures_with_caption"],
                current_metrics["subfigures_with_label"],
                current_metrics["legend_subfigures"],
            ),
        ),
        check(
            "caption_before_label_order",
            current_metrics["caption_before_label_ratio"] >= 0.95,
            "caption-before-label ratio: {:.2f}".format(
                current_metrics["caption_before_label_ratio"]
            ),
        ),
        check(
            "float_spacing_matches_previous_idiom",
            current_metrics["caption_setup"] >= 1 and current_metrics["float_spacing"] >= 3,
            "captionsetup={}, float spacing setlengths={}".format(
                current_metrics["caption_setup"], current_metrics["float_spacing"]
            ),
        ),
        check(
            "title_case_noindent_textbf",
            not current_metrics["lowercase_noindent_textbf"],
            "lowercase lead-ins: {}".format(current_metrics["lowercase_noindent_textbf"]),
        ),
        check(
            "compact_visual_style_present",
            current_metrics["subfigure_environment"] >= 12
            and current_metrics["legend_subfigures"] >= 1
            and current_metrics["vspace"] >= 4,
            "subfigures={}, legend-only subfigures={}, vspace={}".format(
                current_metrics["subfigure_environment"],
                current_metrics["legend_subfigures"],
                current_metrics["vspace"],
            ),
        ),
        check(
            "limited_tables_use_booktabs",
            current_metrics["table"] <= 2
            and current_metrics["booktabs_rules"] >= 3
            and current_metrics["hline_rules"] == 0,
            "tables={}, booktabs rules={}, hline rules={}".format(
                current_metrics["table"],
                current_metrics["booktabs_rules"],
                current_metrics["hline_rules"],
            ),
        ),
        check(
            "evaluation_setup_leadins_title_case",
            all(
                needle in current_text
                for needle in [
                    r"\noindent\textbf{Hardware Specification.}",
                    r"\noindent\textbf{Benchmark.}",
                    r"\noindent\textbf{Baselines.}",
                    r"\noindent\textbf{Feasibility.}",
                ]
            ),
            "evaluation setup lead-ins match AURORA-Q title-case rhythm",
        ),
    ]

    summary = {
        "passed": all(item["passed"] for item in checks),
        "previous_metrics": previous_metrics,
        "current_metrics": current_metrics,
        "checks": checks,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    with open(OUT_MD, "w") as f:
        f.write("# Previous-Paper Style Audit\n\n")
        f.write("Overall status: **{}**\n\n".format("PASS" if summary["passed"] else "FAIL"))
        f.write("This audit checks LaTeX idioms that are not captured by role-count alignment: `textbf` lead-ins, `subfigure` syntax, caption/label order, dense table style, float spacing, and booktabs usage.\n\n")
        f.write("| Check | Status | Detail |\n")
        f.write("| --- | --- | --- |\n")
        for item in checks:
            f.write(
                "| {} | {} | {} |\n".format(
                    item["name"],
                    "PASS" if item["passed"] else "FAIL",
                    str(item["detail"]).replace("|", "/"),
                )
            )
        f.write("\n## Metrics\n\n")
        f.write("| Metric | Current | Previous combined |\n")
        f.write("| --- | ---: | ---: |\n")
        for key in sorted(current_metrics):
            if isinstance(current_metrics[key], list):
                continue
            f.write(
                "| {} | {} | {} |\n".format(
                    key, current_metrics[key], previous_metrics.get(key, "")
                )
            )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
