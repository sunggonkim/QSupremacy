#!/usr/bin/env python3
"""Audit evidence files used by the paper tables and figures."""

import csv
import json
import os


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "paper_evidence_audit.json"
)
OUT_MD = os.path.join(
    ROOT, "data", "processed", "perlmutter", "paper_evidence_audit.md"
)


def rel(path):
    return os.path.relpath(path, ROOT)


def load_json(rel_path):
    with open(os.path.join(ROOT, rel_path)) as f:
        return json.load(f)


def count_csv(rel_path):
    with open(os.path.join(ROOT, rel_path), newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def exists(rel_path):
    return os.path.exists(os.path.join(ROOT, rel_path))


def completed_accounting(rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        return False
    with open(path) as f:
        text = f.read()
    return "COMPLETED" in text and "FAILED" not in text and "TIMEOUT" not in text


def ok_item(name, claim, evidence, checks):
    passed = all(check["passed"] for check in checks)
    return {
        "name": name,
        "claim": claim,
        "evidence": evidence,
        "checks": checks,
        "passed": passed,
    }


def check_equals(label, actual, expected):
    return {
        "label": label,
        "actual": actual,
        "expected": expected,
        "passed": actual == expected,
    }


def check_close(label, actual, expected, tolerance=1e-6):
    return {
        "label": label,
        "actual": actual,
        "expected": expected,
        "tolerance": tolerance,
        "passed": abs(float(actual) - float(expected)) <= tolerance,
    }


def check_exists(rel_path):
    return {
        "label": "exists: {}".format(rel_path),
        "actual": exists(rel_path),
        "expected": True,
        "passed": exists(rel_path),
    }


def check_pdf_artifact(rel_path, min_bytes=1024):
    path = os.path.join(ROOT, rel_path)
    actual = {
        "exists": os.path.exists(path),
        "size_bytes": 0,
        "header": "",
    }
    if os.path.exists(path):
        actual["size_bytes"] = os.path.getsize(path)
        with open(path, "rb") as f:
            actual["header"] = f.read(4).decode("ascii", errors="replace")
    return {
        "label": "valid_pdf: {}".format(rel_path),
        "actual": actual,
        "expected": {
            "exists": True,
            "min_bytes": min_bytes,
            "header": "%PDF",
        },
        "passed": (
            actual["exists"]
            and actual["size_bytes"] >= min_bytes
            and actual["header"] == "%PDF"
        ),
    }


def check_text_contains(label, rel_path, needles):
    text = ""
    if exists(rel_path):
        with open(os.path.join(ROOT, rel_path), errors="replace") as f:
            text = f.read()
    missing = [needle for needle in needles if needle not in text]
    return {
        "label": label,
        "actual": {
            "file": rel_path,
            "missing": missing,
        },
        "expected": {
            "contains": needles,
        },
        "passed": exists(rel_path) and not missing,
    }


def manifest_checks(manifest_rel_path):
    required_ids = [
        "expanded_digits",
        "large_practical_suite",
        "advantage_projection",
        "workload_taxonomy",
        "chemistry_active_space",
        "repeat_timing",
        "paper_figures",
        "submission_package",
    ]
    checks = [
        check_exists(manifest_rel_path),
        check_exists("data/processed/perlmutter/paper_artifact_manifest.md"),
    ]
    if not exists(manifest_rel_path):
        return checks

    manifest = load_json(manifest_rel_path)
    claim_ids = sorted(claim["id"] for claim in manifest.get("claims", []))
    checks.append(check_equals("manifest_claim_ids", claim_ids, sorted(required_ids)))

    for claim in manifest.get("claims", []):
        claim_id = claim["id"]
        for field in ["source_jobs", "source_scripts", "artifacts", "figures_tables"]:
            for rel_path in claim.get(field, []):
                checks.append(check_exists(rel_path))
        checks.append(
            {
                "label": "audit_item_declared: {}".format(claim_id),
                "actual": bool(claim.get("audit_item")),
                "expected": True,
                "passed": bool(claim.get("audit_item")),
            }
        )
    return checks


def main():
    items = []

    digits_json = "data/processed/perlmutter/digits_expanded_55421321_55422142_summary.json"
    digits_csv = "data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv"
    digits = load_json(digits_json)
    items.append(
        ok_item(
            "expanded_digits",
            "160-case digits calibration with kernel and QNN/VQC thresholds",
            [digits_json, digits_csv],
            [
                check_exists(digits_json),
                check_exists(digits_csv),
                check_equals("csv_cases", count_csv(digits_csv), 160),
                check_close(
                    "kernel_required_speedup_median",
                    digits["aggregate"]["quantum_kernel_required_speedup"]["median"],
                    421.9348123448411,
                ),
                check_close(
                    "qnn_vqc_required_speedup_median",
                    digits["aggregate"]["qnn_vqc_required_speedup"]["median"],
                    64.92810815562814,
                ),
            ],
        )
    )

    large_json = (
        "data/processed/perlmutter/"
        "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json"
    )
    large_csv = (
        "data/processed/perlmutter/"
        "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv"
    )
    large_accounting = (
        "data/raw/perlmutter/accounting/"
        "sacct_practical_suite_strongnative_32node_large128c0c127_20260704060230.txt"
    )
    large = load_json(large_json)
    large_checks = [
        check_exists(large_json),
        check_exists(large_csv),
        check_exists(large_accounting),
        check_equals("summary_cases", large["cases"], 3552),
        check_equals("csv_cases", count_csv(large_csv), 3552),
        check_equals("accounting_completed", completed_accounting(large_accounting), True),
    ]
    for workload, cases in [
        ("ml", 2048),
        ("chemistry", 224),
        ("optimization", 768),
        ("simulation", 512),
    ]:
        large_checks.append(
            check_equals(
                "{}_cases".format(workload),
                large["by_workload"][workload]["cases"],
                cases,
            )
        )
    items.append(
        ok_item(
            "large_practical_suite",
            "3,552-case strong-native practical suite on 32 Perlmutter GPU nodes",
            [large_json, large_csv, large_accounting],
            large_checks,
        )
    )

    taxonomy_json = (
        "data/processed/perlmutter/"
        "practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json"
    )
    taxonomy = load_json(taxonomy_json)
    items.append(
        ok_item(
            "workload_taxonomy",
            "Bottleneck taxonomy over the 3,552-case strong-native suite",
            [taxonomy_json, "paper/figures/workload_taxonomy.pdf"],
            [
                check_exists(taxonomy_json),
                check_exists("paper/figures/workload_taxonomy.pdf"),
                check_equals("taxonomy_cases", taxonomy["cases"], 3552),
                check_equals(
                    "ml_quality_limited",
                    taxonomy["by_workload"]["ml"]["counts"]["quality-limited"],
                    2048,
                ),
                check_equals(
                    "simulation_speed_limited",
                    taxonomy["by_workload"]["simulation"]["counts"]["speed-limited"],
                    256,
                ),
            ],
        )
    )

    projection_json = (
        "data/processed/perlmutter/"
        "practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json"
    )
    projection_md = (
        "data/processed/perlmutter/"
        "practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.md"
    )
    projection = load_json(projection_json)
    items.append(
        ok_item(
            "advantage_projection",
            "Advantage fractions over projected speedup and quality-gap recovery",
            [projection_json, projection_md, "paper/figures/advantage_frontier.pdf"],
            [
                check_exists(projection_json),
                check_exists(projection_md),
                check_exists("paper/figures/advantage_frontier.pdf"),
                check_equals("projection_cases", projection["cases"], 3552),
                check_close(
                    "simulation_1e4_90pct_recovery",
                    projection["by_workload"]["simulation"]["grid"]["0.90"]["10000"],
                    0.548828125,
                ),
                check_close(
                    "chemistry_1e5_90pct_recovery",
                    projection["by_workload"]["chemistry"]["grid"]["0.90"]["100000"],
                    0.5714285714285714,
                ),
            ],
        )
    )

    chemistry_json = (
        "data/processed/perlmutter/"
        "practical_suite_chem_active_6q8q_1node_20260704233824_chemistry_coverage.json"
    )
    chemistry_md = (
        "data/processed/perlmutter/"
        "practical_suite_chem_active_6q8q_1node_20260704233824_chemistry_coverage.md"
    )
    chemistry_accounting = (
        "data/raw/perlmutter/accounting/"
        "sacct_practical_suite_chem_active_6q8q_1node_20260704233824.txt"
    )
    chemistry = load_json(chemistry_json)
    items.append(
        ok_item(
            "chemistry_active_space",
            "104-case OpenFermion/PySCF chemistry coverage gate",
            [chemistry_json, chemistry_md, chemistry_accounting],
            [
                check_exists(chemistry_json),
                check_exists(chemistry_md),
                check_exists(chemistry_accounting),
                check_equals("chemistry_cases", chemistry["cases"], 104),
                check_equals("chemistry_problem_count", chemistry["problem_count"], 9),
                check_equals("accounting_completed", completed_accounting(chemistry_accounting), True),
            ],
        )
    )

    scaling_figures = [
        "paper/figures/intro_application_gap.pdf",
        "paper/figures/design_overview.pdf",
        "paper/figures/scaling_summary.pdf",
        "paper/figures/scale_out_gate.pdf",
        "paper/figures/strong_native_comparison.pdf",
        "paper/figures/practical_suite_summary.pdf",
        "paper/figures/digits_required_speedup.pdf",
        "paper/figures/digits_quality_speedup.pdf",
        "paper/figures/advantage_frontier.pdf",
        "paper/figures/salloc_pilot_comparison.pdf",
        "paper/figures/workload_taxonomy.pdf",
    ]
    discovered_figures = [
        os.path.join("paper", "figures", name)
        for name in sorted(os.listdir(os.path.join(ROOT, "paper", "figures")))
        if name.endswith(".pdf")
    ]
    items.append(
        ok_item(
            "paper_figures",
            "Generated paper figures are valid PDF artifacts for performance, scaling, quality, and frontier analysis",
            scaling_figures,
            [
                check_equals(
                    "all_generated_figures_audited",
                    sorted(discovered_figures),
                    sorted(scaling_figures),
                )
            ]
            + [check_pdf_artifact(path) for path in scaling_figures],
        )
    )

    manuscript_checks = [
        check_text_contains(
            "abstract_core_numbers",
            "paper/0.Main.tex",
            [
                "160 cases",
                "421.9$\\times$",
                "64.9$\\times$",
                "3,552-case",
                "3,071.0$\\times$",
                "287,045.6$\\times$",
                "104-case OpenFermion/PySCF",
            ],
        ),
        check_text_contains(
            "practical_suite_table_numbers",
            "paper/4.Evaluation.tex",
            [
                "ML & 2,048 & 3,726.4$\\times$ & 0.3125",
                "Chemistry & 224 & 42,491.4$\\times$ & 0.0203",
                "Optimization & 768 & 287,045.6$\\times$ & 0.2500",
                "Simulation & 512 & 3,071.0$\\times$ & 0.0188",
            ],
        ),
        check_text_contains(
            "projection_and_repeat_numbers",
            "paper/4.Evaluation.tex",
            [
                "Simulation & 0.01 & 54.9\\% & 71.9\\% & 100.0\\% & 100.0\\%",
                "Chemistry & 0.01 & 0.0\\% & 57.1\\% & 100.0\\% & 100.0\\%",
                "maximum quantum-runtime coefficient of variation is 0.0400",
            ],
        ),
        check_text_contains(
            "conclusion_frontier_numbers",
            "paper/6.Conclusion.tex",
            [
                "421.9$\\times$",
                "64.9$\\times$",
                "3,552 cases",
                "54.9\\% of simulation cases",
                "57.1\\% of chemistry cases",
            ],
        ),
    ]
    items.append(
        ok_item(
            "manuscript_claims",
            "Manuscript text contains the canonical evidence-backed numeric claims",
            [
                "paper/0.Main.tex",
                "paper/4.Evaluation.tex",
                "paper/6.Conclusion.tex",
            ],
            manuscript_checks,
        )
    )

    manifest_json = "data/processed/perlmutter/paper_artifact_manifest.json"
    items.append(
        ok_item(
            "artifact_manifest",
            "Machine-readable and Markdown manifest connect paper claims to jobs, scripts, artifacts, figures, and audit items",
            [
                manifest_json,
                "data/processed/perlmutter/paper_artifact_manifest.md",
            ],
            manifest_checks(manifest_json),
        )
    )

    summary = {
        "passed": all(item["passed"] for item in items),
        "items": items,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    with open(OUT_MD, "w") as f:
        f.write("# Paper Evidence Audit\n\n")
        f.write("Overall status: **{}**\n\n".format("PASS" if summary["passed"] else "FAIL"))
        f.write("| Evidence item | Claim | Status | Files |\n")
        f.write("| --- | --- | --- | --- |\n")
        for item in items:
            files = "<br>".join("`{}`".format(path) for path in item["evidence"])
            f.write(
                "| {} | {} | {} | {} |\n".format(
                    item["name"],
                    item["claim"],
                    "PASS" if item["passed"] else "FAIL",
                    files,
                )
            )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
