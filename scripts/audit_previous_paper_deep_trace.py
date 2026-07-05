#!/usr/bin/env python3
"""Generate a line-by-line and paragraph-by-paragraph previous-paper trace."""

import json
import os
import re
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT_DIR = os.path.dirname(__file__)
sys.path.insert(0, SCRIPT_DIR)

from audit_previous_paper_alignment import (  # noqa: E402
    ROLE_CURRENT_MARKERS,
    ROLE_TEMPLATE_MARKERS,
    SECTION_FILES,
    marker_line,
)


OUT_JSON = os.path.join(
    ROOT,
    "data",
    "processed",
    "perlmutter",
    "previous_paper_deep_trace.json",
)
OUT_MD = os.path.join(
    ROOT,
    "data",
    "processed",
    "perlmutter",
    "previous_paper_deep_trace.md",
)


def read_rel(rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return None
    with open(path, errors="replace") as f:
        return f.read()


def strip_latex_inline(text):
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r"\1", text)
    text = re.sub(r"[{}$\\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def first_words(text, limit=14):
    words = strip_latex_inline(text).split()
    return " ".join(words[:limit])


def block_kind(block):
    if re.search(r"\\section\*?\{", block):
        return "section"
    if re.search(r"\\subsection\*?\{", block):
        return "subsection"
    if re.search(r"\\subsubsection\*?\{", block):
        return "subsubsection"
    if r"\begin{figure" in block:
        return "figure"
    if r"\begin{table" in block:
        return "table"
    if r"\begin{equation" in block or r"\[" in block:
        return "equation"
    return "paragraph"


def block_lead(block):
    for pattern in [
        r"\\noindent\\textbf\{([^{}]+)\}",
        r"\\textbf\{([^{}]+)\}",
        r"\\subsubsection\{([^{}]+)\}",
        r"\\subsection\{([^{}]+)\}",
        r"\\section\{([^{}]+)\}",
        r"\\caption\{([^{}]+)\}",
    ]:
        match = re.search(pattern, block)
        if match:
            return match.group(1).strip()
    return first_words(block)


def word_count(block):
    return len(re.findall(r"[A-Za-z0-9]+", strip_latex_inline(block)))


def keep_block(block):
    stripped = block.strip()
    if not stripped:
        return False
    if stripped.startswith(r"\end{"):
        return False
    kind = block_kind(block)
    if kind in {"section", "subsection", "subsubsection", "figure", "table", "equation"}:
        return True
    return word_count(block) >= 8 or r"\textbf" in block


def source_blocks(text):
    lines = text.splitlines()
    blocks = []
    start = None
    current = []
    for line_number, line in enumerate(lines, start=1):
        if line.strip():
            if start is None:
                start = line_number
            current.append(line)
        elif current:
            block = "\n".join(current)
            if keep_block(block):
                blocks.append(
                    {
                        "start_line": start,
                        "end_line": line_number - 1,
                        "kind": block_kind(block),
                        "lead": block_lead(block),
                        "word_count": word_count(block),
                        "has_noindent_textbf": bool(
                            re.search(r"\\noindent\\textbf\{", block)
                        ),
                        "has_subfigure": r"\begin{subfigure}" in block,
                        "has_resizebox": r"\resizebox{\columnwidth}" in block,
                    }
                )
            start = None
            current = []
    if current:
        block = "\n".join(current)
        if keep_block(block):
            blocks.append(
                {
                    "start_line": start,
                    "end_line": len(lines),
                    "kind": block_kind(block),
                    "lead": block_lead(block),
                    "word_count": word_count(block),
                    "has_noindent_textbf": bool(re.search(r"\\noindent\\textbf\{", block)),
                    "has_subfigure": r"\begin{subfigure}" in block,
                    "has_resizebox": r"\resizebox{\columnwidth}" in block,
                }
            )
    return blocks


def role_markers_for_section(section, text):
    markers = []
    for role, marker in ROLE_CURRENT_MARKERS.get(section, {}).items():
        line = marker_line(text, marker)
        if line:
            template_source, template_marker = ROLE_TEMPLATE_MARKERS.get(section, {}).get(
                role, (None, None)
            )
            template_text = None
            template_line = None
            if template_source:
                template_path = SECTION_FILES[section].get(template_source)
                template_text = read_rel(template_path)
            if template_text and template_marker:
                template_line = marker_line(template_text, template_marker)
            markers.append(
                {
                    "role": role,
                    "current_marker": marker,
                    "current_line": line,
                    "template_source": template_source,
                    "template_marker": template_marker,
                    "template_line": template_line,
                }
            )
    return sorted(markers, key=lambda item: item["current_line"])


def assign_role(block, markers):
    if not markers:
        return {}
    candidates = [marker for marker in markers if marker["current_line"] <= block["start_line"]]
    return (candidates[-1] if candidates else markers[0]).copy()


def main():
    sections = {}
    all_rows = []
    missing = []
    for section, paths in SECTION_FILES.items():
        current_path = paths["ours"]
        text = read_rel(current_path)
        if text is None:
            missing.append(current_path)
            continue
        for label, rel_path in paths.items():
            if label != "ours" and read_rel(rel_path) is None:
                missing.append(rel_path)

        markers = role_markers_for_section(section, text)
        blocks = source_blocks(text)
        rows = []
        for index, block in enumerate(blocks, start=1):
            role = assign_role(block, markers)
            row = {
                "section": section,
                "order": index,
                "current_path": current_path,
                **block,
                **role,
            }
            rows.append(row)
            all_rows.append(row)
        sections[section] = {
            "current_path": current_path,
            "block_count": len(blocks),
            "role_marker_count": len(markers),
            "rows": rows,
        }

    checks = {
        "previous_sources_available": not missing,
        "all_sections_traced": set(sections) == set(SECTION_FILES),
        "all_current_blocks_have_roles": all(row.get("role") for row in all_rows),
        "all_current_blocks_have_template_lines": all(
            row.get("template_source") and row.get("template_line") for row in all_rows
        ),
        "line_level_trace_present": len(all_rows) >= 90,
        "paragraph_and_structure_kinds_present": {"paragraph", "figure", "table"}.issubset(
            {row["kind"] for row in all_rows}
        ),
        "style_features_traced": any(row.get("has_noindent_textbf") for row in all_rows)
        and any(row.get("has_subfigure") for row in all_rows)
        and any(row.get("has_resizebox") for row in all_rows),
    }

    summary = {
        "passed": all(checks.values()),
        "checks": checks,
        "missing": missing,
        "total_traced_blocks": len(all_rows),
        "sections": sections,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    with open(OUT_MD, "w") as f:
        f.write("# Previous-Paper Deep Trace\n\n")
        f.write("Overall status: **{}**\n\n".format("PASS" if summary["passed"] else "FAIL"))
        f.write(
            "This trace lists every meaningful current manuscript paragraph or structural block, "
            "its source line span, the accepted-paper role it follows, and the previous-paper "
            "template source line used as the nearest logic anchor. It avoids copying previous-paper "
            "prose; markers are used only as short trace anchors.\n\n"
        )
        f.write("Total traced blocks: `{}`\n\n".format(summary["total_traced_blocks"]))
        f.write("## Checks\n\n")
        f.write("| Check | Status |\n")
        f.write("| --- | --- |\n")
        for name, passed in checks.items():
            f.write("| {} | {} |\n".format(name, "PASS" if passed else "FAIL"))
        f.write("\n## Section Summary\n\n")
        f.write("| Section | Current source | Traced blocks | Role anchors |\n")
        f.write("| --- | --- | ---: | ---: |\n")
        for section, data in sections.items():
            f.write(
                "| {} | `{}` | {} | {} |\n".format(
                    section,
                    data["current_path"],
                    data["block_count"],
                    data["role_marker_count"],
                )
            )
        f.write("\n## Line-by-Line Trace\n\n")
        f.write(
            "| Section | # | Lines | Kind | Current lead | Followed role | Template anchor |\n"
        )
        f.write("| --- | ---: | --- | --- | --- | --- | --- |\n")
        for row in all_rows:
            template = "{}:{} `{}`".format(
                row.get("template_source", ""),
                row.get("template_line", ""),
                row.get("template_marker", ""),
            )
            lead = str(row.get("lead", "")).replace("|", "/")
            if len(lead) > 96:
                lead = lead[:93] + "..."
            f.write(
                "| {} | {} | {}-{} | {} | {} | {} | {} |\n".format(
                    row["section"],
                    row["order"],
                    row["start_line"],
                    row["end_line"],
                    row["kind"],
                    lead,
                    row.get("role", ""),
                    template.replace("|", "/"),
                )
            )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
