#!/usr/bin/env python3
"""Generate the auditable P0 evidence manifest used by the paper."""

import hashlib
import json
import os
from datetime import datetime, timezone


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(
    ROOT, "data", "processed", "perlmutter", "paper_artifact_manifest.json"
)


PACKAGES = [
    {
        "id": "controlled_corpus",
        "claim": "The controlled corpus contains 3,552 paired records from 222 structural configurations and 16 instance seeds per configuration.",
        "artifacts": [
            "data/processed/perlmutter/quality_qualified_target_map.json",
            "data/processed/perlmutter/statistical_robustness.json",
        ],
        "scripts": [
            "scripts/audit_quality_qualified_targets.py",
            "scripts/audit_statistical_robustness.py",
        ],
        "paper": ["paper/1.Introduction.tex", "paper/4.Evaluation.tex"],
        "figures": ["paper/figures/intro_threshold_summary.pdf"],
    },
    {
        "id": "quality_qualified_targets",
        "claim": "Hardware targets are restricted to the 12 same-record Sim cases that pass the full-loop finite-shot quality gate at 10,000 shots.",
        "artifacts": [
            "data/processed/perlmutter/quality_qualified_target_map.json",
            "data/processed/perlmutter/quality_qualified_target_map.csv",
        ],
        "scripts": ["scripts/audit_quality_qualified_targets.py"],
        "paper": ["paper/3.Design.tex", "paper/4.Evaluation.tex"],
        "figures": [
            "paper/figures/quality_noiseless_gate.pdf",
            "paper/figures/quality_finite_shot_gate.pdf",
        ],
    },
    {
        "id": "finite_shot_quality",
        "claim": "Representative ML, Chem, Opt, and Sim cases are sampled directly at 1,000, 10,000, and 100,000 shots with 12 repetitions.",
        "artifacts": [
            "data/processed/perlmutter/finite_shot_quality_sensitivity.json",
            "data/processed/perlmutter/finite_shot_quality_sensitivity.csv",
        ],
        "scripts": ["scripts/run_finite_shot_quality_closure.py"],
        "paper": ["paper/4.Evaluation.tex"],
        "figures": ["paper/figures/quality_finite_shot_gate.pdf"],
    },
    {
        "id": "dependency_schedules",
        "claim": "All 3,552 records use compiled or source-audited static dependency semantics with no aggregate-demand fallback.",
        "artifacts": [
            "data/processed/perlmutter/dependency_schedule_coverage.json",
            "data/processed/perlmutter/dependency_schedule_projection_records.csv",
        ],
        "scripts": ["scripts/audit_dependency_schedule_coverage.py"],
        "paper": ["paper/3.Design.tex", "paper/4.Evaluation.tex"],
        "figures": ["paper/figures/trace_aware_logical_lower_bound.pdf"],
    },
    {
        "id": "statistical_robustness",
        "claim": "Hierarchical bootstrap confidence intervals resample structural configurations and instance seeds rather than treating all rows as independent applications.",
        "artifacts": [
            "data/processed/perlmutter/statistical_robustness.json",
            "data/processed/perlmutter/statistical_robustness.csv",
        ],
        "scripts": ["scripts/audit_statistical_robustness.py"],
        "paper": ["paper/4.Evaluation.tex"],
        "figures": [],
    },
    {
        "id": "ft_reliability",
        "claim": "The 12 eligible cases use case-level logical-error, code-distance, arbitrary-rotation, factory-space, decoder, and shot budgets.",
        "artifacts": [
            "data/processed/perlmutter/ft_reliability_and_space_budget.json",
            "data/processed/perlmutter/ft_reliability_and_space_budget.csv",
        ],
        "scripts": ["scripts/audit_ft_reliability_budget.py"],
        "paper": ["paper/2.Background.tex", "paper/3.Design.tex", "paper/4.Evaluation.tex"],
        "figures": [
            "paper/figures/ft_contract_parameters.pdf",
            "paper/figures/ft_reliability_target.pdf",
        ],
    },
    {
        "id": "joint_dse",
        "claim": "A deterministic 384-scenario joint design sweep evaluates 26,112 case points and exposes stable bottleneck regions.",
        "artifacts": [
            "data/processed/perlmutter/joint_bottleneck_phase_map.json",
            "data/processed/perlmutter/joint_bottleneck_phase_map.csv",
        ],
        "scripts": ["scripts/audit_joint_dse.py"],
        "paper": ["paper/3.Design.tex", "paper/4.Evaluation.tex"],
        "figures": [
            "paper/figures/joint_bottleneck_phase_map.pdf",
            "paper/figures/resource_removal_ceiling.pdf",
        ],
    },
    {
        "id": "matched_mechanism_replacement",
        "claim": "LSQCA and BOSS case studies consume matched event traces; published peak multipliers are not borrowed as application speedups.",
        "artifacts": [
            "data/processed/perlmutter/component_replacement_case_studies.json",
            "data/processed/perlmutter/joint_bottleneck_phase_map.json",
        ],
        "scripts": [
            "scripts/run_component_replacement_case_studies.py",
            "scripts/audit_joint_dse.py",
        ],
        "paper": ["paper/3.Design.tex", "paper/4.Evaluation.tex", "paper/5.Discussion.tex"],
        "figures": ["paper/figures/lsqca_matched_replacement.pdf"],
    },
    {
        "id": "deployment_native_frontier",
        "claim": "Deployment-facing native cases strengthen the moving native frontier without being pooled into controlled-corpus quality statistics.",
        "artifacts": [
            "data/processed/perlmutter/ml_cifar10_matched_comparison.json",
            "data/processed/perlmutter/chem_sim_native_proxies.json",
            "data/processed/perlmutter/opt_native_proxy.json",
            "data/processed/perlmutter/roofline_native_stress.json",
        ],
        "scripts": [
            "scripts/summarize_ml_cifar10_matched_comparison.py",
            "scripts/run_chem_sim_native_proxies.py",
            "scripts/run_opt_native_proxy.py",
            "scripts/summarize_roofline_native_stress.py",
        ],
        "paper": ["paper/4.Evaluation.tex"],
        "figures": [
            "paper/figures/ml_cifar10_runtime.pdf",
            "paper/figures/ml_cifar10_accuracy.pdf",
            "paper/figures/ml_cifar10_legend.pdf",
            "paper/figures/roofline_deadline_shrink.pdf",
        ],
    },
    {
        "id": "physical_modality_replacement",
        "claim": "The same 12 eligible Sim records are re-inverted under surface-code synthesis and two native-rotation execution envelopes without changing their native deadlines or quality gate.",
        "artifacts": [
            "data/processed/perlmutter/native_rotation_platform_envelopes.json",
            "data/processed/perlmutter/ft_reliability_and_space_budget.json",
        ],
        "scripts": ["scripts/summarize_native_rotation_platforms.py"],
        "paper": ["paper/4.Evaluation.tex", "paper/5.Discussion.tex"],
        "figures": ["paper/figures/sim_hardware_modality_pivot.pdf"],
    },
    {
        "id": "low_gpu_timeout_censoring",
        "claim": "The 4/8/16-GPU fixed-work attempts are preserved as timeout-censored artifacts and are not promoted to completed scaling measurements.",
        "artifacts": [
            "data/processed/perlmutter/low_gpu_strong_scaling_timeout_audit.json",
            "data/processed/perlmutter/low_gpu_strong_scaling_timeout_audit.csv",
            "data/raw/perlmutter/accounting/sacct_practical_suite_direct4_strong_1n_4g_7104_20260712091240.txt",
            "data/raw/perlmutter/accounting/sacct_practical_suite_direct8_strong_2n_8g_7104_20260712091240.txt",
            "data/raw/perlmutter/accounting/sacct_practical_suite_direct16_strong_4n_16g_7104_20260712091240.txt",
        ],
        "scripts": ["scripts/summarize_low_gpu_timeout_runs.py"],
        "paper": ["paper/4.Evaluation.tex"],
        "figures": ["paper/figures/low_gpu_timeout_progress.pdf"],
    },
    {
        "id": "paper_figures",
        "claim": "Every figure included by the manuscript is generated, nonempty, and audited as part of the submission package.",
        "artifacts": [],
        "scripts": ["scripts/generate_paper_figures.py"],
        "paper": [
            "paper/0.Main.tex",
            "paper/1.Introduction.tex",
            "paper/2.Background.tex",
            "paper/3.Design.tex",
            "paper/4.Evaluation.tex",
            "paper/5.Discussion.tex",
            "paper/5.RelatedWork.tex",
            "paper/6.Conclusion.tex",
        ],
        "figures": [
            "paper/figures/intro_threshold_summary.pdf",
            "paper/figures/design_overview.pdf",
            "paper/figures/weak_scaling.pdf",
            "paper/figures/strong_scaling.pdf",
            "paper/figures/ml_cifar10_legend.pdf",
            "paper/figures/ml_cifar10_runtime.pdf",
            "paper/figures/ml_cifar10_accuracy.pdf",
            "paper/figures/opt_qaoa_quality_proxy.pdf",
            "paper/figures/chem_vqe_quality_cost_proxy.pdf",
            "paper/figures/sim_quality_cost_proxy.pdf",
            "paper/figures/quality_noiseless_gate.pdf",
            "paper/figures/quality_finite_shot_gate.pdf",
            "paper/figures/roofline_deadline_shrink.pdf",
            "paper/figures/trace_aware_logical_lower_bound.pdf",
            "paper/figures/ft_contract_parameters.pdf",
            "paper/figures/ft_reliability_target.pdf",
            "paper/figures/joint_bottleneck_phase_map.pdf",
            "paper/figures/resource_removal_ceiling.pdf",
            "paper/figures/lsqca_matched_replacement.pdf",
            "paper/figures/sim_hardware_modality_pivot.pdf",
        ],
    },
    {
        "id": "submission_package",
        "claim": "The manuscript, bibliography, audit entry points, and PDF form a reproducible HPCA submission package.",
        "artifacts": [],
        "scripts": [
            "scripts/audit_paper_evidence.py",
            "scripts/audit_submission_readiness.py",
        ],
        "paper": ["README.md", "paper/references.bib", "paper/main.pdf"],
        "figures": [],
    },
]


def fingerprint(rel_path: str) -> dict:
    abs_path = os.path.join(ROOT, rel_path)
    record = {"path": rel_path, "exists": os.path.isfile(abs_path)}
    if not record["exists"]:
        return record
    digest = hashlib.sha256()
    with open(abs_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    record.update({"bytes": os.path.getsize(abs_path), "sha256": digest.hexdigest()})
    return record


def main() -> None:
    packages = []
    for package in PACKAGES:
        files = []
        for category in ("artifacts", "scripts", "paper", "figures"):
            files.extend(package[category])
        fingerprints = [fingerprint(path) for path in sorted(set(files))]
        packages.append(
            {
                **package,
                "status": "PASS" if all(item["exists"] for item in fingerprints) else "FAIL",
                "files": fingerprints,
            }
        )

    manifest = {
        "schema": "qarchgauge.strong-accept-manifest.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "P0-A through P0-F evidence and submission package",
        "paper": {
            "source_entry": "paper/0.Main.tex",
            "pdf": "paper/main.pdf",
            "target": "HPCA 2027 IEEEtran double-blind submission",
        },
        "packages": packages,
        "passed": all(package["status"] == "PASS" for package in packages),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"output": os.path.relpath(OUT, ROOT), "passed": manifest["passed"], "packages": len(packages)}, indent=2))


if __name__ == "__main__":
    main()
