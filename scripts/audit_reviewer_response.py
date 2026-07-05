#!/usr/bin/env python3
"""Audit coverage of the pasted reviewer-feedback response map."""

import json
import os
import re


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "reviewer_response_audit.json"
)
OUT_MD = os.path.join(
    ROOT, "data", "processed", "perlmutter", "reviewer_response_audit.md"
)
RESPONSE = "paper/reviewer_line_by_line_response.md"
PASTED = (
    "/global/homes/s/sgkim/.codex/attachments/"
    "18c4ceff-ebec-49c5-b30e-1640ea3270ba/pasted-text-1.txt"
)


REQUIRED_CONCERNS = [
    ("hardware_projection", ["Hardware projection is first-order", "T_error"]),
    ("technology_calibration", ["No concrete calibration", "d=25", "P_shots=1e4"]),
    ("small_instances", ["Problem instances are small", "8 qubits"]),
    ("digits_limited", ["Digits is limited", "3,552 cases"]),
    ("qaoa_vqc_sensitivity", ["QAOA and VQC/QNN choices are narrow", "quality-gap recovery"]),
    ("native_baselines", ["Native baselines may be weak", "Gurobi/CPLEX"]),
    ("tolerance_choices", ["Tolerance choices are under-justified", "0.01", "0.02"]),
    ("qubit_accounting", ["Accuracy vs. qubit number", "4/8/12/16"]),
    ("shot_optimizer_backend_sensitivity", ["Need shot, optimizer, mitigation", "future sensitivity"]),
    ("figure_clarity", ["Figures must be unambiguous", "audit-checked"]),
    ("name_sensitivity", ["Name `QSUPREMACY` may distract", "QAdvantage"]),
    ("qhpc_related_work", ["Missing QHPC", "Qurator"]),
    ("industry_frameworks", ["traffic-light", "QCHALLenge"]),
    ("ft_resource_estimation", ["fault-tolerant resource estimation", "Azure Quantum Resource Estimator"]),
    ("frontier_notional", ["hardware region remains notional", "logical-runtime"]),
    ("sensitivity_partial", ["Sensitivity sweeps are partial", "future work"]),
]


REQUIRED_AUTHOR_QUESTIONS = [
    "How are per-family tolerances chosen",
    "The digits qubit plot seems inconsistent",
    "Why not include CNNs",
    "Can the paper provide one concrete hardware instantiation",
    "How were shots chosen",
    "Did QAOA and VQC/QNN explore optimizer",
    "Can chemistry/simulation extend beyond 8-qubit",
    "How would alternative simulators change",
    "How does quality-gap recovery map",
    "Would the project consider renaming",
]


REQUIRED_EVIDENCE_PATHS = [
    "paper/0.Main.tex",
    "paper/3.Design.tex",
    "paper/4.Evaluation.tex",
    "paper/5.Discussion.tex",
    "paper/5.RelatedWork.tex",
    "paper/references.bib",
    "paper/reviewer_readiness.md",
    "scripts/generate_workload_taxonomy.py",
    "scripts/audit_paper_evidence.py",
    "data/processed/perlmutter/paper_artifact_manifest.md",
]


def read(path):
    if os.path.isabs(path):
        with open(path, errors="replace") as f:
            return f.read()
    with open(os.path.join(ROOT, path), errors="replace") as f:
        return f.read()


def exists(rel_path):
    return os.path.exists(os.path.join(ROOT, rel_path))


def tracked(rel_path):
    return os.system(
        "cd '{}' && git ls-files --error-unmatch '{}' >/dev/null 2>&1".format(
            ROOT, rel_path
        )
    ) == 0


def markdown_paths(text):
    paths = []
    for match in re.findall(r"`([^`]+)`", text):
        if "/" in match and not match.startswith("/") and not match.startswith("http"):
            paths.append(match)
    return sorted(set(paths))


def check_contains(text, label, needles):
    missing = [needle for needle in needles if needle not in text]
    return {
        "name": label,
        "passed": not missing,
        "missing": missing,
    }


def main():
    response = read(RESPONSE) if exists(RESPONSE) else ""
    pasted = read(PASTED) if os.path.exists(PASTED) else ""
    response_paths = markdown_paths(response)

    concern_checks = [
        check_contains(response, name, needles)
        for name, needles in REQUIRED_CONCERNS
    ]
    question_checks = [
        check_contains(response, "question:" + question, [question])
        for question in REQUIRED_AUTHOR_QUESTIONS
    ]
    evidence_checks = [
        {
            "name": "evidence:" + path,
            "passed": path in response and exists(path) and tracked(path),
            "in_response": path in response,
            "exists": exists(path),
            "tracked": tracked(path) if exists(path) else False,
        }
        for path in REQUIRED_EVIDENCE_PATHS
    ]
    pasted_checks = [
        check_contains(pasted, "pasted_feedback:" + phrase, [phrase])
        for phrase in [
            "Technical limitations or concerns",
            "Questions for Authors",
            "Overall Assessment",
        ]
    ]
    path_checks = [
        {
            "name": "response_path:" + path,
            "passed": exists(path) and tracked(path),
            "exists": exists(path),
            "tracked": tracked(path) if exists(path) else False,
        }
        for path in response_paths
        if path.startswith(("paper/", "scripts/", "data/"))
    ]

    all_checks = concern_checks + question_checks + evidence_checks + pasted_checks + path_checks
    summary = {
        "passed": all(item["passed"] for item in all_checks),
        "concern_count": len(concern_checks),
        "author_question_count": len(question_checks),
        "evidence_path_count": len(evidence_checks),
        "response_markdown_path_count": len(path_checks),
        "checks": all_checks,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    with open(OUT_MD, "w") as f:
        f.write("# Reviewer Response Audit\n\n")
        f.write("Overall status: **{}**\n\n".format("PASS" if summary["passed"] else "FAIL"))
        f.write("| Check | Status | Detail |\n")
        f.write("| --- | --- | --- |\n")
        for item in all_checks:
            detail = ""
            if item.get("missing"):
                detail = "missing: " + ", ".join(item["missing"])
            elif "exists" in item:
                detail = "exists={}, tracked={}".format(item["exists"], item["tracked"])
            f.write(
                "| {} | {} | {} |\n".format(
                    item["name"],
                    "PASS" if item["passed"] else "FAIL",
                    detail,
                )
            )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
