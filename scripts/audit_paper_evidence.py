#!/usr/bin/env python3
"""Audit evidence files used by the paper tables and figures."""

import csv
import json
import os


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_JSON = os.path.join(
    ROOT, "data", "processed", "perlmutter", "paper_evidence_audit.json"
)
OUT_MD = os.devnull


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
        "ml_strong_native_gate",
        "deployment_proxy",
        "repeat_timing",
        "paper_figures",
        "submission_package",
    ]
    checks = [check_exists(manifest_rel_path)]
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
    large_64_json = (
        "data/processed/perlmutter/"
        "practical_suite_strongnative_64node_large256c0c255_20260705024742_summary.json"
    )
    large_64_csv = (
        "data/processed/perlmutter/"
        "practical_suite_strongnative_64node_large256c0c255_20260705024742_summary.csv"
    )
    strong_64_json = (
        "data/processed/perlmutter/"
        "practical_suite_strongscale_64node_largefull_c0c255_20260705024742_summary.json"
    )
    strong_64_csv = (
        "data/processed/perlmutter/"
        "practical_suite_strongscale_64node_largefull_c0c255_20260705024742_summary.csv"
    )
    large_64_accounting = (
        "data/raw/perlmutter/accounting/"
        "sacct_practical_suite_strongnative_64node_large256c0c255_20260705024742.txt"
    )
    strong_64_accounting = (
        "data/raw/perlmutter/accounting/"
        "sacct_practical_suite_strongscale_64node_largefull_c0c255_20260705024742.txt"
    )
    weak_ladder = [
        (
            "weak_16",
            "data/processed/perlmutter/practical_suite_55731013_scale_16n_64g_summary.json",
            "data/processed/perlmutter/practical_suite_55731013_scale_16n_64g_summary.csv",
            "data/raw/perlmutter/accounting/sacct_practical_suite_55731013_scale_16n_64g.txt",
            1776,
        ),
        (
            "weak_32",
            "data/processed/perlmutter/practical_suite_55731014_scale_32n_128g_summary.json",
            "data/processed/perlmutter/practical_suite_55731014_scale_32n_128g_summary.csv",
            "data/raw/perlmutter/accounting/sacct_practical_suite_55731014_scale_32n_128g.txt",
            3552,
        ),
        (
            "weak_64",
            "data/processed/perlmutter/practical_suite_55731015_scale_64n_256g_summary.json",
            "data/processed/perlmutter/practical_suite_55731015_scale_64n_256g_summary.csv",
            "data/raw/perlmutter/accounting/sacct_practical_suite_55731015_scale_64n_256g.txt",
            7104,
        ),
    ]
    strong_ladder = [
        (
            "strong_context_8",
            "data/processed/perlmutter/practical_suite_review_strong_8n_32g_7104_20260711021411_summary.json",
            "data/processed/perlmutter/practical_suite_review_strong_8n_32g_7104_20260711021411_summary.csv",
            "data/raw/perlmutter/accounting/sacct_practical_suite_review_strong_8n_32g_7104_20260711021411.txt",
            3552,
        ),
        (
            "strong_16",
            "data/processed/perlmutter/practical_suite_55731032_scale_16n_64g_summary.json",
            "data/processed/perlmutter/practical_suite_55731032_scale_16n_64g_summary.csv",
            "data/raw/perlmutter/accounting/sacct_practical_suite_55731032_scale_16n_64g.txt",
            7104,
        ),
        (
            "strong_32",
            "data/processed/perlmutter/practical_suite_55731033_scale_32n_128g_summary.json",
            "data/processed/perlmutter/practical_suite_55731033_scale_32n_128g_summary.csv",
            "data/raw/perlmutter/accounting/sacct_practical_suite_55731033_scale_32n_128g.txt",
            7104,
        ),
        (
            "strong_64",
            "data/processed/perlmutter/practical_suite_55731034_scale_64n_256g_summary.json",
            "data/processed/perlmutter/practical_suite_55731034_scale_64n_256g_summary.csv",
            "data/raw/perlmutter/accounting/sacct_practical_suite_55731034_scale_64n_256g.txt",
            7104,
        ),
    ]
    large = load_json(large_json)
    large_64 = load_json(large_64_json)
    strong_64 = load_json(strong_64_json)
    large_checks = [
        check_exists(large_json),
        check_exists(large_csv),
        check_exists(large_accounting),
        check_exists(large_64_json),
        check_exists(large_64_csv),
        check_exists(large_64_accounting),
        check_exists(strong_64_json),
        check_exists(strong_64_csv),
        check_exists(strong_64_accounting),
        check_equals("summary_cases", large["cases"], 3552),
        check_equals("csv_cases", count_csv(large_csv), 3552),
        check_equals("large_64_summary_cases", large_64["cases"], 7104),
        check_equals("large_64_csv_cases", count_csv(large_64_csv), 7104),
        check_equals("strong_64_summary_cases", strong_64["cases"], 3552),
        check_equals("strong_64_csv_cases", count_csv(strong_64_csv), 3552),
        check_equals("accounting_completed", completed_accounting(large_accounting), True),
        check_equals("large_64_accounting_completed", completed_accounting(large_64_accounting), True),
        check_equals("strong_64_accounting_completed", completed_accounting(strong_64_accounting), True),
    ]
    for label, json_path, csv_path, accounting_path, cases in weak_ladder + strong_ladder:
        summary = load_json(json_path)
        large_checks.extend(
            [
                check_exists(json_path),
                check_exists(csv_path),
                check_exists(accounting_path),
                check_equals("{}_summary_cases".format(label), summary["cases"], cases),
                check_equals("{}_csv_cases".format(label), count_csv(csv_path), cases),
                check_equals(
                    "{}_accounting_completed".format(label),
                    completed_accounting(accounting_path),
                    True,
                ),
            ]
        )
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
            "3,552-case suite plus regular weak-scaling gates, a 32-GPU strong-scaling context run, and direct 64/128/256-GPU fixed-work scaling anchors",
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
                check_equals(
                    "chemistry_speed_limited",
                    taxonomy["by_workload"]["chemistry"]["counts"]["speed-limited"],
                    48,
                ),
                check_equals(
                    "chemistry_quality_limited",
                    taxonomy["by_workload"]["chemistry"]["counts"]["quality-limited"],
                    176,
                ),
            ],
        )
    )

    projection_json = (
        "data/processed/perlmutter/"
        "practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json"
    )
    projection_scenarios_json = (
        "data/processed/perlmutter/practical_suite_projection_scenarios.json"
    )
    projection = load_json(projection_json)
    projection_scenarios = load_json(projection_scenarios_json)
    items.append(
        ok_item(
            "advantage_projection",
            "Advantage fractions over projected speedup and quality-gap recovery",
            [
                projection_json,
                projection_scenarios_json,
                "paper/figures/advantage_frontier.pdf",
                "paper/figures/advantage_frontier_total.pdf",
                "paper/figures/advantage_component_targets.pdf",
                "paper/figures/advantage_frontier_chemistry.pdf",
                "paper/figures/advantage_frontier_optimization.pdf",
                "paper/figures/advantage_frontier_simulation.pdf",
                "paper/figures/tolerance_sensitivity.pdf",
                "paper/figures/ft_shot_sensitivity.pdf",
            ],
            [
                check_exists(projection_json),
                check_exists(projection_scenarios_json),
                check_exists("paper/figures/advantage_frontier.pdf"),
                check_exists("paper/figures/advantage_frontier_total.pdf"),
                check_exists("paper/figures/advantage_component_targets.pdf"),
                check_exists("paper/figures/advantage_frontier_chemistry.pdf"),
                check_exists("paper/figures/advantage_frontier_optimization.pdf"),
                check_exists("paper/figures/advantage_frontier_simulation.pdf"),
                check_exists("paper/figures/tolerance_sensitivity.pdf"),
                check_exists("paper/figures/ft_shot_sensitivity.pdf"),
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
                check_equals(
                    "projection_scenario_cases",
                    projection_scenarios["cases"],
                    3552,
                ),
                check_close(
                    "projection_scenario_default_sim_ratio",
                    projection_scenarios["by_scenario"]["default_optimistic"][
                        "by_workload"
                    ]["simulation"]["median_projected_native_ratio"],
                    0.027233696161942635,
                ),
                check_close(
                    "projection_scenario_resource_ml_adv",
                    projection_scenarios["by_scenario"]["resource_estimator_like"][
                        "by_workload"
                    ]["ml"]["advantaged_fraction"],
                    0.00146484375,
                ),
            ],
        )
    )

    chemistry_json = (
        "data/processed/perlmutter/"
        "practical_suite_chem_active_6q8q_1node_20260704233824_chemistry_coverage.json"
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
            [chemistry_json, chemistry_accounting],
            [
                check_exists(chemistry_json),
                check_exists(chemistry_accounting),
                check_equals("chemistry_cases", chemistry["cases"], 104),
                check_equals("chemistry_problem_count", chemistry["problem_count"], 9),
                check_equals("accounting_completed", completed_accounting(chemistry_accounting), True),
            ],
        )
    )

    deployment_proxy_json = "data/processed/perlmutter/deployment_scale_proxy.json"
    deployment_proxy_csv = "data/processed/perlmutter/deployment_scale_proxy.csv"
    deployment_proxy = load_json(deployment_proxy_json)
    items.append(
        ok_item(
            "deployment_proxy",
            "Deployment-scale proxy boundary keeps larger workload claims scoped to proxy records rather than full state-vector simulation",
            [
                deployment_proxy_json,
                deployment_proxy_csv,
                "paper/5.Discussion.tex",
            ],
            [
                check_exists(deployment_proxy_json),
                check_exists(deployment_proxy_csv),
                check_equals("proxy_rows_json", len(deployment_proxy["rows"]), 4),
                check_equals("proxy_rows_csv", count_csv(deployment_proxy_csv), 4),
                check_text_contains(
                    "discussion_deployment_proxy_boundary",
                    "paper/5.Discussion.tex",
                    [
                        "Deployment-Scale Proxy Boundary",
                        "Table~\\ref{tab:deployment-proxy}",
                        "20-node MaxCut QAOA stress case",
                        "12-qubit 16-step Heisenberg stress case",
                        "not a deployment-scale state-vector claim",
                    ],
                ),
            ],
        )
    )

    ml_gate_json = "data/processed/perlmutter/ml_strong_native_gate_latest.json"
    ml_gate_csv = "data/processed/perlmutter/ml_strong_native_gate_latest.csv"
    ml_profile_json = "data/processed/perlmutter/ml_strong_native_profile_latest.json"
    ml_gate = load_json(ml_gate_json)["summary"]
    ml_profile = load_json(ml_profile_json)
    profile_nsys = ml_profile["nsys_kernel_summary"]
    profile_ncu = ml_profile["ncu_summary"]
    profile_dmon = ml_profile["dmon_summary"]
    items.append(
        ok_item(
            "ml_strong_native_gate",
            "Production-style ML native gate with PyTorch AMP CNN/MLP, XGBoost GPU-hist, and Nsight/dmon profiling evidence",
            [
                ml_gate_json,
                ml_gate_csv,
                ml_profile_json,
                "paper/figures/ml_strong_native_gate.pdf",
                "paper/figures/ml_profile_breakdown.pdf",
                "paper/figures/ml_native_profile_combined.pdf",
            ],
            [
                check_exists(ml_gate_json),
                check_exists(ml_gate_csv),
                check_exists(ml_profile_json),
                check_equals("ml_gate_cases", ml_gate["case_count"], 32),
                check_equals("ml_gate_csv_cases", count_csv(ml_gate_csv), 32),
                check_close(
                    "ml_previous_speedup_median",
                    ml_gate["previous_required_speedup_median"],
                    8876.825399953243,
                ),
                check_close(
                    "ml_combined_speedup_median",
                    ml_gate["combined_required_speedup_median"],
                    8601.600644667848,
                ),
                check_close(
                    "ml_production_speedup_median",
                    ml_gate["production_required_speedup_median"],
                    49.267014250506136,
                ),
                check_equals(
                    "ml_combined_torch_cnn_selected",
                    ml_gate["selected_combined_counts"]["torch_cnn_amp_raw"],
                    8,
                ),
                check_equals(
                    "ml_production_cnn_selected",
                    ml_gate["selected_production_counts"]["torch_cnn_amp_raw"],
                    25,
                ),
                check_equals(
                    "nsys_tensor_kernel_rows",
                    profile_nsys["tensor_kernel_rows"],
                    16,
                ),
                check_close(
                    "nsys_gpu_kernel_fraction",
                    profile_nsys["gpu_kernel_runtime_fraction"],
                    0.007982148769692417,
                ),
                check_close(
                    "nsys_tensor_kernel_fraction",
                    profile_nsys["tensor_kernel_time_fraction"],
                    0.1520596245304038,
                ),
                check_equals(
                    "ncu_counter_collection_succeeded",
                    profile_ncu["counter_collection_succeeded"],
                    False,
                ),
                check_close("dmon_sm_avg_pct", profile_dmon["sm_avg_pct"], 2.3),
                check_close("dmon_sm_max_pct", profile_dmon["sm_max_pct"], 33.0),
                check_pdf_artifact("paper/figures/ml_strong_native_gate.pdf"),
                check_pdf_artifact("paper/figures/ml_profile_breakdown.pdf"),
                check_pdf_artifact("paper/figures/ml_native_profile_combined.pdf"),
            ],
        )
    )

    scaling_figures = [
        "paper/figures/intro_comparison_paths.pdf",
        "paper/figures/intro_threshold_summary.pdf",
        "paper/figures/design_overview.pdf",
        "paper/figures/design_projection_flow.pdf",
        "paper/figures/evaluation_evidence_flow.pdf",
        "paper/figures/weak_scaling.pdf",
        "paper/figures/weak_scaling_efficiency.pdf",
        "paper/figures/strong_scaling.pdf",
        "paper/figures/strong_scaling_speedup.pdf",
        "paper/figures/workload_growth_time.pdf",
        "paper/figures/workload_growth_quality.pdf",
        "paper/figures/strong_native_comparison.pdf",
        "paper/figures/strong_native_legend.pdf",
        "paper/figures/strong_native_quality_shift.pdf",
        "paper/figures/ml_strong_native_gate.pdf",
        "paper/figures/ml_profile_breakdown.pdf",
        "paper/figures/ml_native_profile_combined.pdf",
        "paper/figures/threshold_tail_pressure.pdf",
        "paper/figures/projected_time_decomposition.pdf",
        "paper/figures/architecture_focus_matrix.pdf",
        "paper/figures/practical_suite_legend.pdf",
        "paper/figures/practical_suite_summary.pdf",
        "paper/figures/practical_suite_cdf.pdf",
        "paper/figures/quality_gap_summary.pdf",
        "paper/figures/quality_bottleneck_fraction.pdf",
        "paper/figures/digits_legend.pdf",
        "paper/figures/digits_required_speedup.pdf",
        "paper/figures/digits_quality_speedup.pdf",
        "paper/figures/advantage_frontier.pdf",
        "paper/figures/advantage_frontier_total.pdf",
        "paper/figures/advantage_component_targets.pdf",
        "paper/figures/advantage_frontier_chemistry.pdf",
        "paper/figures/advantage_frontier_optimization.pdf",
        "paper/figures/advantage_frontier_simulation.pdf",
        "paper/figures/tolerance_sensitivity.pdf",
        "paper/figures/ft_shot_sensitivity.pdf",
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
            "practical_suite_prose_numbers",
            "paper/4.Evaluation.tex",
            [
                "mean required speedup is 79,291$\\times$",
                "median is 15,164$\\times$",
                "3,726.4$\\times$ for ML",
                "42,491.4$\\times$ for Chem",
                "287,045.6$\\times$ for Opt.",
                "3,071.0$\\times$ for Sim.",
                "7,104-case larger-workload gate",
                "completes 7,104 cases in 576 seconds",
                "28 minutes 33 seconds",
                "6 minutes 58 seconds",
                "32-case production-style ML native gate",
                "8,601.6$\\times$",
                "49.3$\\times$",
                "Tensor-family kernels account for 15.2\\%",
                "GPU kernels occupy 0.8\\%",
            ],
        ),
        check_text_contains(
            "projection_numbers",
            "paper/4.Evaluation.tex",
            [
                "Sim. reaches 55\\% of cases at $10^4\\times$",
                "Chem reaches 57\\% at $10^5\\times$",
                "Opt. remains at 23\\% even at $10^6\\times$",
            ],
        ),
        check_text_contains(
            "repeat_numbers",
            "paper/5.Discussion.tex",
            [
                "maximum quantum-runtime CV is 0.0400",
            ],
        ),
        check_text_contains(
            "conclusion_frontier_numbers",
            "paper/6.Conclusion.tex",
            [
                "421.9$\\times$",
                "64.9$\\times$",
                "3,552 cases",
                "54.9\\% of Sim. cases",
                "57.1\\% of Chem cases",
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
            "Machine-readable manifest connects paper claims to jobs, scripts, artifacts, figures, and audit items",
            [manifest_json],
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
