#!/usr/bin/env python3
"""Audit argument-role alignment with the accepted previous papers.

The accepted papers are writing templates, not section-count templates.  This
audit therefore checks that the current HPCA manuscript preserves their
argument mechanics while using a structure appropriate for an architecture
modeling paper.
"""

import json
import os
import re


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "previous_paper_alignment_metrics.json"
)

SECTION_FILES = {
    "introduction": {
        "ours": "paper/1.Introduction.tex",
        "aurora": "paper/PreviousPapers/AURORA_Q_ICDCS26/1.Introduction.tex",
        "scaleqsim": "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/1.introduction.tex",
    },
    "background": {
        "ours": "paper/2.Background.tex",
        "aurora": "paper/PreviousPapers/AURORA_Q_ICDCS26/2.Background.tex",
        "scaleqsim": "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/2.Background.tex",
    },
    "design": {
        "ours": "paper/3.Design.tex",
        "aurora": "paper/PreviousPapers/AURORA_Q_ICDCS26/3.Design.tex",
        "scaleqsim": "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/3.Design.tex",
    },
    "evaluation": {
        "ours": "paper/4.Evaluation.tex",
        "aurora": "paper/PreviousPapers/AURORA_Q_ICDCS26/4.Evaluation.tex",
        "scaleqsim": "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/4.Evaluation.tex",
    },
    "related": {
        "ours": "paper/5.RelatedWork.tex",
        "aurora": "paper/PreviousPapers/AURORA_Q_ICDCS26/5.Related work.tex",
        "scaleqsim": "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/5.Related Work.tex",
    },
    "conclusion": {
        "ours": "paper/6.Conclusion.tex",
        "aurora": "paper/PreviousPapers/AURORA_Q_ICDCS26/6.Conclusion.tex",
        "scaleqsim": "paper/PreviousPapers/ScaleQsim_SIGMETRICS26/6.Conclusion.tex",
    },
}


ROLE_CURRENT_MARKERS = {
    "introduction": {
        "opening pressure": "Quantum computing targets",
        "simulator boundary": "Leadership systems provide a way",
        "early evidence figure": "\\begin{figure}",
        "figure lesson": "Figure~\\ref{fig:intro-gap}",
        "evidence scale": "The evidence must also separate verifiability from width",
        "prior-work positioning": "Table~\\ref{tab:intro-position}",
        "key idea": "\\noindent\\textbf{Key Idea.}",
        "contributions": "This paper makes three contributions",
    },
    "background": {
        "application substrate": "\\subsection{Application Boundary and Evidence Scale}",
        "application families": "The four families exercise different paths",
        "application boundary": "A case crosses the application boundary only when",
        "evidence levels": "Evidence scale and circuit width are distinct",
        "critical path": "\\subsection{Reliability-Constrained Critical Path}",
        "reliability envelope": "Surface-code execution couples reliability",
        "rotation constraint": "Arbitrary rotations add a second reliability constraint",
        "control and replacement": "Decoder service and the communication/control path",
    },
    "design": {
        "design thesis": "\\SystemName turns an application comparison into a replaceable architecture contract",
        "paired record": "\\subsection{Paired Evidence Record}",
        "comparison invariant": "Both paths receive the same instance identifier",
        "evidence typing": "Simulator execution recovers the exact circuit output and demand",
        "physical inversion": "\\subsection{Quality-First Physical Inversion}",
        "quality gate": "The first stage partitions every record",
        "reliability contract": "The strict reliability contract splits",
        "joint inversion": "\\subsection{Joint Target and Mechanism Inversion}",
        "first and next target": "For each eligible record and resource",
        "joint design": "One-factor results are insufficient",
        "matched replacement": "Published mechanisms use the same invariant",
        "implementation": "\\noindent\\textbf{Implementation and audits.}",
    },
    "evaluation": {
        "setup": "\\subsection{Evaluation Setup and Contracts}",
        "platform": "\\noindent\\textbf{Platform and evidence units.}",
        "scale and provenance": "\\noindent\\textbf{Scale and provenance.}",
        "deployment frontier": "\\subsection{Deployment-Facing Native Frontier}",
        "ml representation": "\\noindent\\textbf{ML representation.}",
        "quality cost": "\\noindent\\textbf{Quality costs beyond ML.}",
        "quality boundary": "\\subsection{Quality-Qualified Application Boundary}",
        "finite-shot closure": "At $10^4$ shots, ML passes",
        "logical lower bound": "\\subsection{Trace-Aware Logical Lower Bound}",
        "physical diagnosis": "\\subsection{Reliability-Constrained Physical Diagnosis}",
        "joint sensitivity": "\\subsection{Joint Co-Design Sensitivity}",
        "matched replacement": "The framework can also test a published mechanism",
        "claim closure": "\\noindent\\textbf{Observation 5:}",
    },
    "related": {
        "application benchmarking": "Application benchmarks and native comparison",
        "ft estimation": "FT estimation and critical-path evidence",
        "component architectures": "QPU component architectures",
        "hpc simulation and integration": "HPC simulation and integration",
    },
    "conclusion": {
        "paper result": "\\SystemName uses leadership HPC",
        "main lesson": "Quantum advantage is therefore",
    },
}


ROLE_TEMPLATE_MARKERS = {
    "introduction": {
        "opening pressure": ("aurora", "Quantum computing offers"),
        "simulator boundary": ("aurora", "To overcome these limitations"),
        "early evidence figure": ("aurora", "\\begin{figure}"),
        "figure lesson": ("aurora", "Figure~\\ref{intro_fig} shows"),
        "evidence scale": ("scaleqsim", "Many previous studies"),
        "prior-work positioning": ("aurora", "\\begin{table}"),
        "key idea": ("aurora", "\\AURORA distinguishes itself"),
        "contributions": ("aurora", "In this paper, we propose"),
    },
    "background": {
        "application substrate": ("scaleqsim", "\\subsection{Quantum Circuit Simulation}"),
        "application families": ("scaleqsim", "Full state vector simulation"),
        "application boundary": ("aurora", "Bandwidth Gap and Execution Time"),
        "evidence levels": ("scaleqsim", "Amplitude sampling simulation"),
        "critical path": ("scaleqsim", "\\subsection{Distributed Architecture"),
        "reliability envelope": ("aurora", "\\subsection{Hardware Constraints"),
        "rotation constraint": ("aurora", "Bandwidth Gap and Execution Time"),
        "control and replacement": ("aurora", "Performance degradation is driven by data locality"),
    },
    "design": {
        "design thesis": ("aurora", "Overview of \\AURORA"),
        "paired record": ("scaleqsim", "\\subsection{Overall Procedure}"),
        "comparison invariant": ("scaleqsim", "Initialization."),
        "evidence typing": ("scaleqsim", "Execution."),
        "physical inversion": ("scaleqsim", "Two-phase State Space Partitioning"),
        "quality gate": ("scaleqsim", "Manage statespace structure"),
        "reliability contract": ("scaleqsim", "Adaptive Kernel Parameter Adjustment"),
        "joint inversion": ("scaleqsim", "\\ScaleQsim Implementation"),
        "first and next target": ("aurora", "\\subsection{Adaptive Resource Control}"),
        "joint design": ("aurora", "Asynchronous Execution"),
        "matched replacement": ("aurora", "\\AURORA Implementation"),
        "implementation": ("scaleqsim", "\\ScaleQsim Implementation"),
    },
    "evaluation": {
        "setup": ("aurora", "\\subsection{Evaluation Setup}"),
        "platform": ("aurora", "\\begin{table}"),
        "scale and provenance": ("aurora", "Various Circuits."),
        "deployment frontier": ("aurora", "Various Circuits."),
        "ml representation": ("scaleqsim", "Comparison with \\textit{Qsim}"),
        "quality cost": ("aurora", "\\subsection{Performance with SOTA}"),
        "quality boundary": ("aurora", "\\subsection{Performance with SOTA}"),
        "finite-shot closure": ("scaleqsim", "Time Analysis"),
        "logical lower bound": ("scaleqsim", "Time Analysis"),
        "physical diagnosis": ("aurora", "\\subsection{Sensitivity Analysis}"),
        "joint sensitivity": ("aurora", "Weak Scalability."),
        "matched replacement": ("scaleqsim", "Performance Variability and Stability"),
        "claim closure": ("aurora", "\\subsection{Sensitivity Analysis}"),
    },
    "related": {
        "application benchmarking": ("scaleqsim", "Optimizing Quantum Circuit Simulation"),
        "ft estimation": ("aurora", "Memory and I/O Optimization in HPC Systems"),
        "component architectures": ("aurora", "Quantum Simulation Beyond Memory Limits"),
        "hpc simulation and integration": ("aurora", "Quantum Simulation Beyond Memory Limits"),
    },
    "conclusion": {
        "paper result": ("scaleqsim", "In this paper"),
        "main lesson": ("scaleqsim", "Our evaluations across"),
    },
}


ROLE_INVENTORY = {
    section: [(role, role.replace("-", " ")) for role in roles]
    for section, roles in ROLE_CURRENT_MARKERS.items()
}


def read_rel(rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    with open(path, errors="replace") as f:
        return f.read()


def strip_latex(text):
    text = re.sub(r"\\iffalse.*?\\fi", "", text, flags=re.S)
    text = re.sub(r"\\begin\{comment\}.*?\\end\{comment\}", "", text, flags=re.S)
    return re.sub(r"(?<!\\)%.*", "", text)


def marker_line(text, marker):
    if not text or not marker:
        return None
    pos = text.find(marker)
    return None if pos < 0 else text[:pos].count("\n") + 1


def metrics(text):
    clean = strip_latex(text)
    words = re.findall(r"[A-Za-z0-9]+", clean)
    paragraphs = [
        p for p in re.split(r"\n\s*\n+", clean)
        if len(re.findall(r"[A-Za-z0-9]+", p)) >= 8
    ]
    return {
        "words": len(words),
        "paragraphs": len(paragraphs),
        "subsections": re.findall(r"^\\subsection\{([^}]+)\}", clean, flags=re.M),
        "figures": len(re.findall(r"\\begin\{figure\*?\}", clean)),
        "tables": len(re.findall(r"\\begin\{table\*?\}", clean)),
        "textbf": clean.count("\\textbf"),
        "observation_boxes": clean.count("\\begin{observationbox}"),
    }


def ordered_role_rows(section, current_text, template_texts):
    rows = []
    for role, marker in ROLE_CURRENT_MARKERS[section].items():
        template_source, template_marker = ROLE_TEMPLATE_MARKERS[section][role]
        rows.append({
            "role": role,
            "current_marker": marker,
            "current_line": marker_line(current_text, marker),
            "template_source": template_source,
            "template_marker": template_marker,
            "template_line": marker_line(template_texts.get(template_source), template_marker),
        })
    return rows


def rows_present_and_ordered(rows, field):
    positions = [row.get(field) for row in rows]
    return all(pos is not None for pos in positions) and positions == sorted(positions)


def main():
    sections = {}
    missing = []
    for section, paths in SECTION_FILES.items():
        texts = {name: read_rel(path) for name, path in paths.items()}
        missing.extend(path for name, path in paths.items() if texts[name] is None)
        if texts["ours"] is None:
            continue
        role_rows = ordered_role_rows(section, texts["ours"], texts)
        sections[section] = {
            "ours": {"path": paths["ours"], **metrics(texts["ours"])},
            "aurora": {"path": paths["aurora"], **metrics(texts["aurora"] or "")},
            "scaleqsim": {"path": paths["scaleqsim"], **metrics(texts["scaleqsim"] or "")},
            "paragraph_role_inventory": role_rows,
            "current_roles_ordered": rows_present_and_ordered(role_rows, "current_line"),
            "template_roles_present": all(row["template_line"] for row in role_rows),
        }

    design_headings = sections.get("design", {}).get("ours", {}).get("subsections", [])
    evaluation_headings = sections.get("evaluation", {}).get("ours", {}).get("subsections", [])
    related_labels = [
        role for role, row in zip(
            ROLE_CURRENT_MARKERS["related"],
            sections.get("related", {}).get("paragraph_role_inventory", []),
        ) if row.get("current_line")
    ]
    current_sources = "\n".join(
        read_rel(paths["ours"]) or "" for paths in SECTION_FILES.values()
    )

    checks = {
        "previous_sources_available": not missing,
        "no_disabled_manuscript_blocks": "\\iffalse" not in current_sources,
        "all_argument_roles_present_and_ordered": all(
            data["current_roles_ordered"] for data in sections.values()
        ),
        "all_roles_trace_to_previous_sources": all(
            data["template_roles_present"] for data in sections.values()
        ),
        "introduction_argument_spine": sections["introduction"]["ours"]["subsections"] == [],
        "background_two_stage_spine": sections["background"]["ours"]["subsections"] == [
            "Application Boundary and Evidence Scale",
            "Reliability-Constrained Critical Path",
        ],
        "design_mechanism_spine": design_headings == [
            "Paired Evidence Record",
            "Quality-First Physical Inversion",
            "Joint Target and Mechanism Inversion",
            "Typed Architecture Decision",
        ],
        "evaluation_claim_spine": evaluation_headings == [
            "Evaluation Setup and Contracts",
            "Deployment-Facing Native Frontier",
            "Quality-Qualified Application Boundary",
            "Trace-Aware Logical Lower Bound",
            "Reliability-Constrained Physical Diagnosis",
            "Joint Co-Design Sensitivity",
        ],
        "evaluation_has_claim_closure": sections["evaluation"]["ours"]["figures"] >= 7
        and sections["evaluation"]["ours"]["observation_boxes"] >= 1,
        "related_work_covers_four_closest_categories": len(related_labels) == 4,
        "paragraph_role_inventory_present": all(
            data["paragraph_role_inventory"] for data in sections.values()
        ),
    }

    known_gaps = []
    for section, data in sections.items():
        for row in data["paragraph_role_inventory"]:
            if not row["current_line"] or not row["template_line"]:
                known_gaps.append({"section": section, **row})

    summary = {
        "passed": all(checks.values()),
        "checks": checks,
        "missing": missing,
        "known_gaps": known_gaps,
        "sections": sections,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
