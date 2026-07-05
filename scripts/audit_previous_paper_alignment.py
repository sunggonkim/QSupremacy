#!/usr/bin/env python3
"""Measure manuscript structure against the accepted previous-paper templates."""

import json
import os
import re


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "previous_paper_alignment_metrics.json"
)
OUT_MD = os.path.join(
    ROOT, "data", "processed", "perlmutter", "previous_paper_alignment_metrics.md"
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


ROLE_MARKERS = {
    "introduction": [
        "Quantum computing is often described",
        "\\begin{figure}",
        "Observation 1",
        "\\begin{table}",
        "Key idea",
        "This paper makes the following contributions",
    ],
    "background": [
        "\\subsection",
        "Repeated execution",
        "Practical application families",
        "Break-even condition",
    ],
    "design": [
        "Overview of",
        "\\subsection{Overall Procedure}",
        "\\subsection{Shared Workload Control}",
        "\\subsection{Application Path Execution}",
        "\\subsection{Measurement and Threshold Analysis}",
        "\\subsection{Advantage Claim Checklist}",
        "\\subsection{Workload Suite}",
    ],
    "evaluation": [
        "Evaluation Setup",
        "Hardware specification",
        "Benchmark",
        "Baselines",
        "Feasibility",
        "Evaluation questions",
        "Answer",
        "Advantage Frontier",
    ],
}


ROLE_INVENTORY = {
    "introduction": [
        ("opening motivation", "Broad promise, practical HPC question, hardware limit"),
        ("prior simulator boundary", "Simulation systems help, but simulator speed is not application speed"),
        ("intro figure", "First visual statement of native path versus quantum path"),
        ("observations", "Bold observations before positioning table"),
        ("application diversity", "Why one toy workload cannot support broad quantum claims"),
        ("positioning table", "Early related-work table before final pitch"),
        ("key idea", "Break-even threshold model"),
        ("paper statement and contributions", "System statement followed by contribution list"),
    ],
    "background": [
        ("application paths", "Define quantum-circuit application families"),
        ("repeated execution", "Explain why one circuit run is not the full application"),
        ("practical families", "ML, chemistry, optimization, simulation"),
        ("terminology", "Threshold and advantage-region definitions"),
        ("native baselines", "Classical target path"),
        ("Perlmutter/cuQuantum", "Measurement platform"),
        ("break-even equations", "Native, simulated quantum, projected hardware paths"),
    ],
    "design": [
        ("overview and boundary", "State what the system is and is not"),
        ("overall procedure", "Measurement then supremacy analysis"),
        ("configuration record", "Stable work representation before execution"),
        ("failure handling", "Failed paths remain measured evidence"),
        ("shared workload control", "Same input, instance identity, and quality target"),
        ("application paths", "Native, kernel, and QNN/VQC execution rules"),
        ("measurement records", "JSON, summary path, and allocation accounting"),
        ("threshold analysis", "Execution model, break-even search, and frontier classification"),
        ("claim checklist", "Systems checks before an advantage claim"),
        ("workload suite", "Measured application families"),
    ],
    "evaluation": [
        ("setup", "Hardware, benchmark, baselines, feasibility"),
        ("campaign summary", "Evidence table and evaluation questions"),
        ("RQ1", "Native ML versus quantum-circuit ML"),
        ("RQ2", "Quality sensitivity"),
        ("RQ3", "Practical application suite"),
        ("RQ4", "Native baseline stress"),
        ("RQ5", "Weak and strong scaling"),
        ("RQ6", "Advantage frontier and hardware projection"),
        ("stability", "Operational and repeat-timing checks"),
        ("taxonomy and sensitivity", "Bottleneck classes and remaining scope"),
    ],
    "related": [
        ("simulation and NISQ", "Simulation substrate and current-device limits"),
        ("applications and baselines", "Application families and native comparisons"),
    ],
    "conclusion": [
        ("paper result", "Framework and measured thresholds"),
        ("main lesson", "Frontier and bottleneck taxonomy instead of slogan"),
    ],
}


ROLE_CURRENT_MARKERS = {
    "introduction": {
        "opening motivation": "Quantum computing is often described",
        "prior simulator boundary": "Existing simulation systems provide",
        "intro figure": "\\begin{figure}",
        "observations": "Observation 1",
        "application diversity": "The same issue becomes stronger",
        "positioning table": "\\begin{table}",
        "key idea": "Key idea",
        "paper statement and contributions": "This paper makes the following contributions",
    },
    "background": {
        "application paths": "\\subsection{Quantum-Circuit Application Paths}",
        "repeated execution": "Repeated execution",
        "practical families": "Practical application families",
        "terminology": "Terminology",
        "native baselines": "\\subsection{Native Baselines and Threshold Model}",
        "Perlmutter/cuQuantum": "Perlmutter and cuQuantum",
        "break-even equations": "Break-even condition",
    },
    "design": {
        "overview and boundary": "Overview of",
        "overall procedure": "\\subsection{Overall Procedure}",
        "configuration record": "Config Record",
        "failure handling": "Failure Handling",
        "shared workload control": "\\subsection{Shared Workload Control}",
        "application paths": "\\subsection{Application Path Execution}",
        "measurement records": "\\subsection{Measurement and Threshold Analysis}",
        "threshold analysis": "\\subsubsection{Threshold Analysis}",
        "claim checklist": "\\subsection{Advantage Claim Checklist}",
        "workload suite": "\\subsection{Workload Suite}",
    },
    "evaluation": {
        "setup": "\\subsection{Evaluation Setup}",
        "campaign summary": "Campaign summary",
        "RQ1": "\\subsection{RQ1:",
        "RQ2": "\\subsection{RQ2:",
        "RQ3": "\\subsection{RQ3:",
        "RQ4": "\\subsection{RQ4:",
        "RQ5": "\\subsection{RQ5:",
        "RQ6": "\\subsection{RQ6:",
        "stability": "\\subsection{Operational Stability}",
        "taxonomy and sensitivity": "Bottleneck Taxonomy",
    },
    "related": {
        "simulation and NISQ": "Quantum simulation and NISQ systems",
        "applications and baselines": "Quantum applications and native baselines",
    },
    "conclusion": {
        "paper result": "In this paper",
        "main lesson": "The main lesson",
    },
}


def read_rel(rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    with open(path, errors="replace") as f:
        return f.read()


def strip_latex(text):
    text = re.sub(r"\\begin\{comment\}.*?\\end\{comment\}", "", text, flags=re.S)
    text = re.sub(r"%.*", "", text)
    return text


def prose_paragraphs(text):
    text = strip_latex(text)
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n+", text) if chunk.strip()]
    paragraphs = []
    for chunk in chunks:
        if chunk.startswith("\\begin") or chunk.startswith("\\end"):
            continue
        words = re.findall(r"[A-Za-z0-9]+", chunk)
        if len(words) >= 8 or "\\textbf" in chunk:
            paragraphs.append(chunk)
    return paragraphs


def count_metrics(text):
    clean = strip_latex(text)
    return {
        "words": len(re.findall(r"[A-Za-z0-9]+", clean)),
        "paragraphs": len(prose_paragraphs(text)),
        "textbf": clean.count("\\textbf"),
        "subsections": len(re.findall(r"^\\subsection", clean, flags=re.M)),
        "subsubsections": len(re.findall(r"^\\subsubsection", clean, flags=re.M)),
        "figures": len(re.findall(r"\\begin\{figure", clean)),
        "tables": len(re.findall(r"\\begin\{table", clean)),
        "items": len(re.findall(r"^\\s*\\item\b", clean, flags=re.M)),
    }


def distance(ours, target):
    keys = ["paragraphs", "textbf", "subsections", "subsubsections", "figures", "tables", "items"]
    total = 0.0
    for key in keys:
        denom = max(target.get(key, 0), 1)
        total += abs(ours.get(key, 0) - target.get(key, 0)) / denom
    word_denom = max(target.get("words", 0), 1)
    total += 0.5 * abs(ours.get("words", 0) - target.get("words", 0)) / word_denom
    return round(total, 3)


def marker_positions(text, markers):
    positions = {}
    for marker in markers:
        pos = text.find(marker)
        positions[marker] = pos if pos >= 0 else None
    return positions


def marker_line(text, marker):
    if marker is None:
        return None
    pos = text.find(marker)
    if pos < 0:
        return None
    return text[:pos].count("\n") + 1


def ordered_markers(positions):
    seen = [pos for pos in positions.values() if pos is not None]
    return seen == sorted(seen) and len(seen) == len(positions)


def main():
    sections = {}
    for section, paths in SECTION_FILES.items():
        section_data = {}
        texts = {}
        for label, rel_path in paths.items():
            text = read_rel(rel_path)
            if text is None:
                section_data[label] = {"path": rel_path, "missing": True}
                continue
            texts[label] = text
            section_data[label] = {"path": rel_path, "missing": False, **count_metrics(text)}

        ours = section_data.get("ours", {})
        template_distances = {}
        for label in ("aurora", "scaleqsim"):
            if not ours.get("missing") and not section_data.get(label, {}).get("missing"):
                template_distances[label] = distance(ours, section_data[label])
        if template_distances:
            section_data["closest_template"] = min(template_distances, key=template_distances.get)
            section_data["template_distance"] = template_distances

        if section in ROLE_MARKERS and "ours" in texts:
            positions = marker_positions(texts["ours"], ROLE_MARKERS[section])
            section_data["role_markers"] = positions
            section_data["role_markers_ordered"] = ordered_markers(positions)
        if section in ROLE_INVENTORY:
            section_data["paragraph_role_inventory"] = [
                {
                    "role": role,
                    "template_logic": template_logic,
                    "current_marker": ROLE_CURRENT_MARKERS.get(section, {}).get(role),
                    "current_line": marker_line(
                        texts.get("ours", ""),
                        ROLE_CURRENT_MARKERS.get(section, {}).get(role),
                    ),
                }
                for role, template_logic in ROLE_INVENTORY[section]
            ]

        sections[section] = section_data

    checks = {
        "previous_sources_available": all(
            not sections[section][label].get("missing")
            for section in sections
            for label in ("aurora", "scaleqsim")
        ),
        "intro_role_and_size": sections["introduction"].get("role_markers_ordered", False)
        and sections["introduction"]["ours"].get("subsections") == 0
        and 0.8
        <= sections["introduction"]["ours"].get("words", 0)
        / max(sections["introduction"]["aurora"].get("words", 1), 1)
        <= 1.2,
        "background_two_subsections": sections["background"]["ours"].get("subsections") == 2,
        "design_scaleqsim_subsection_count": sections["design"]["ours"].get("subsections")
        == sections["design"]["scaleqsim"].get("subsections"),
        "evaluation_previous_shape": min(
            abs(
                sections["evaluation"]["ours"].get("paragraphs", 0)
                - sections["evaluation"]["aurora"].get("paragraphs", 0)
            ),
            abs(
                sections["evaluation"]["ours"].get("paragraphs", 0)
                - sections["evaluation"]["scaleqsim"].get("paragraphs", 0)
            ),
        )
        <= 6,
        "role_markers_ordered": all(
            sections[section].get("role_markers_ordered", True)
            for section in ROLE_MARKERS
        ),
        "paragraph_role_inventory_present": all(
            len(sections[section].get("paragraph_role_inventory", [])) > 0
            for section in SECTION_FILES
        ),
        "paragraph_role_lines_present": all(
            all(item.get("current_line") for item in sections[section].get("paragraph_role_inventory", []))
            for section in SECTION_FILES
        ),
    }

    known_gaps = []
    for section, data in sections.items():
        ours = data.get("ours", {})
        if ours.get("missing"):
            continue
        candidates = [
            label
            for label in ("aurora", "scaleqsim")
            if not data.get(label, {}).get("missing")
        ]
        if not candidates:
            continue
        closest = min(
            candidates,
            key=lambda label: abs(
                ours.get("words", 0) - data[label].get("words", 0)
            ),
        )
        target = data[closest]
        word_ratio = ours.get("words", 0) / max(target.get("words", 1), 1)
        if word_ratio < 0.65 or word_ratio > 1.35:
            known_gaps.append(
                {
                    "section": section,
                    "closest_template": closest,
                    "ours_words": ours.get("words", 0),
                    "target_words": target.get("words", 0),
                    "word_ratio": round(word_ratio, 3),
                }
            )

    summary = {
        "status": "TRACKED_WITH_KNOWN_GAPS" if known_gaps else "ALIGNED_BY_COUNTS",
        "checks": checks,
        "known_gaps": known_gaps,
        "sections": sections,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    with open(OUT_MD, "w") as f:
        f.write("# Previous-Paper Alignment Metrics\n\n")
        f.write("Status: **{}**\n\n".format(summary["status"]))
        f.write("## Checks\n\n")
        f.write("| Check | Status |\n")
        f.write("| --- | --- |\n")
        for name, passed in checks.items():
            f.write("| {} | {} |\n".format(name, "PASS" if passed else "RISK"))
        f.write("\n## Section Counts\n\n")
        f.write(
            "| Section | Paper | Words | Paragraphs | textbf | Subsections | Subsubsections | Figures | Tables | Items |\n"
        )
        f.write("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        for section, data in sections.items():
            for label in ("ours", "aurora", "scaleqsim"):
                metrics = data[label]
                if metrics.get("missing"):
                    f.write("| {} | {} | missing |  |  |  |  |  |  |  |\n".format(section, label))
                    continue
                f.write(
                    "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n".format(
                        section,
                        label,
                        metrics["words"],
                        metrics["paragraphs"],
                        metrics["textbf"],
                        metrics["subsections"],
                        metrics["subsubsections"],
                        metrics["figures"],
                        metrics["tables"],
                        metrics["items"],
                    )
                )
        f.write("\n## Known Gaps\n\n")
        if known_gaps:
            f.write("| Section | Closest template | Ours words | Template words | Ratio |\n")
            f.write("| --- | --- | ---: | ---: | ---: |\n")
            for gap in known_gaps:
                f.write(
                    "| {section} | {closest_template} | {ours_words} | {target_words} | {word_ratio} |\n".format(
                        **gap
                    )
                )
        else:
            f.write("No large word-count gaps under the current threshold.\n")
        f.write("\n## Paragraph Role Inventory\n\n")
        f.write("| Section | Order | Current source line | Current paragraph role | Previous-paper logic followed |\n")
        f.write("| --- | ---: | ---: | --- | --- |\n")
        for section, data in sections.items():
            for index, item in enumerate(data.get("paragraph_role_inventory", []), start=1):
                f.write(
                    "| {} | {} | {} | {} | {} |\n".format(
                        section,
                        index,
                        item.get("current_line") or "",
                        item["role"],
                        item["template_logic"],
                    )
                )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
