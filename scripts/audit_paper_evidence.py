#!/usr/bin/env python3
"""Audit the P0 evidence-to-paper contract for QArchGauge."""

import csv
import hashlib
import json
import os
import re


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(
    ROOT, "data", "processed", "perlmutter", "paper_evidence_audit.json"
)


def path(rel_path):
    return os.path.join(ROOT, rel_path)


def exists(rel_path):
    return os.path.isfile(path(rel_path))


def load_json(rel_path):
    if not exists(rel_path):
        return {}
    with open(path(rel_path), errors="replace") as handle:
        return json.load(handle)


def read_text(rel_path):
    if not exists(rel_path):
        return ""
    with open(path(rel_path), errors="replace") as handle:
        return handle.read()


def csv_rows(rel_path):
    if not exists(rel_path):
        return -1
    with open(path(rel_path), newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def check(label, passed, actual=None, expected=None):
    return {
        "label": label,
        "passed": bool(passed),
        "actual": actual,
        "expected": expected,
    }


def equal(label, actual, expected):
    return check(label, actual == expected, actual, expected)


def close(label, actual, expected, tolerance=1e-9):
    passed = actual is not None and abs(float(actual) - float(expected)) <= tolerance
    return check(label, passed, actual, expected)


def file_check(rel_path, min_bytes=1):
    size = os.path.getsize(path(rel_path)) if exists(rel_path) else 0
    return check(
        "file: {}".format(rel_path),
        exists(rel_path) and size >= min_bytes,
        {"exists": exists(rel_path), "bytes": size},
        {"exists": True, "min_bytes": min_bytes},
    )


def sha256(rel_path):
    digest = hashlib.sha256()
    with open(path(rel_path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contains(label, rel_path, needles):
    text = read_text(rel_path)
    missing = [needle for needle in needles if needle not in text]
    return check(label, exists(rel_path) and not missing, {"missing": missing}, needles)


def excludes(label, rel_path, needles):
    text = read_text(rel_path)
    present = [needle for needle in needles if needle in text]
    return check(label, exists(rel_path) and not present, {"present": present}, [])


def item(name, claim, evidence, checks):
    return {
        "name": name,
        "claim": claim,
        "evidence": evidence,
        "checks": checks,
        "passed": all(entry["passed"] for entry in checks),
    }


def paper_text():
    sources = [
        "paper/0.Main.tex",
        "paper/1.Introduction.tex",
        "paper/2.Background.tex",
        "paper/3.Design.tex",
        "paper/4.Evaluation.tex",
        "paper/5.Discussion.tex",
        "paper/5.RelatedWork.tex",
        "paper/6.Conclusion.tex",
    ]
    return "\n".join(read_text(source) for source in sources)


def included_figures():
    figures = []
    for rel_path in [
        "paper/1.Introduction.tex",
        "paper/2.Background.tex",
        "paper/3.Design.tex",
        "paper/4.Evaluation.tex",
        "paper/5.Discussion.tex",
    ]:
        for match in re.findall(
            r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", read_text(rel_path)
        ):
            figures.append("paper/{}".format(match))
    return sorted(set(figures))


def main():
    quality = load_json("data/processed/perlmutter/quality_qualified_target_map.json")
    finite = load_json("data/processed/perlmutter/finite_shot_quality_sensitivity.json")
    schedule = load_json("data/processed/perlmutter/dependency_schedule_coverage.json")
    stats = load_json("data/processed/perlmutter/statistical_robustness.json")
    ft = load_json("data/processed/perlmutter/ft_reliability_and_space_budget.json")
    joint = load_json("data/processed/perlmutter/joint_bottleneck_phase_map.json")
    replacement = load_json(
        "data/processed/perlmutter/component_replacement_case_studies.json"
    )
    cifar = load_json("data/processed/perlmutter/ml_cifar10_matched_comparison.json")
    manifest = load_json("data/processed/perlmutter/paper_artifact_manifest.json")
    text = paper_text()

    default_quality = quality.get("by_tolerance_multiplier", {}).get("1.0", {})
    corpus = stats.get("corpus", {})
    finite_records = finite.get("records", [])
    finite_10k = [record for record in finite_records if record.get("shots") == 10000]
    finite_10k_counts = {}
    eligible_10k_counts = {}
    for workload in ["ml", "chemistry", "optimization", "simulation"]:
        selected = [record for record in finite_10k if record.get("workload") == workload]
        finite_10k_counts[workload] = len(selected)
        eligible_10k_counts[workload] = sum(
            1
            for record in selected
            if record.get("quality_pass_probability", 0) >= 0.9
            and record.get("same_record_quality_shot_trace")
            and record.get("full_algorithm_loop_covered")
        )

    schedule_coverage = schedule.get("coverage", {})
    ft_sim = (
        ft.get("by_workload_default_strict", {})
        .get("simulation", {})
        .get("quality_qualified_records", {})
    )
    ft_range = ft_sim.get("factory_crossover_multiplier_range", [])
    ft_factory_count = ft_sim.get("factory_count_to_crossover_range", [])
    joint_design = joint.get("design", {})
    joint_headline = joint.get("headline", {})
    joint_lsqca = joint_headline.get("lsqca_result", {})
    replacement_headline = replacement.get("headline", {})

    items = []
    items.append(
        item(
            "controlled_corpus",
            "The evidence set is 3,552 records from 222 structural configurations and 16 seeds per configuration.",
            [
                "data/processed/perlmutter/statistical_robustness.json",
                "paper/4.Evaluation.tex",
            ],
            [
                equal("statistics audit", stats.get("audit_status"), "PASS"),
                equal("controlled records", corpus.get("records"), 3552),
                equal("structural configurations", corpus.get("structural_configurations"), 222),
                equal("seed values", corpus.get("seed_values"), 16),
                equal(
                    "family record counts",
                    corpus.get("by_workload"),
                    {"ml": 2048, "chemistry": 224, "optimization": 768, "simulation": 512},
                ),
                contains(
                    "paper distinguishes records, configurations, and seeds",
                    "paper/4.Evaluation.tex",
                    ["3,552 records", "222 structural configurations", "16 distinct seeds per configuration"],
                ),
            ],
        )
    )

    items.append(
        item(
            "quality_qualified_targets",
            "Only 12 same-record full-loop Sim cases at 10,000 shots receive application-level hardware targets.",
            [
                "data/processed/perlmutter/quality_qualified_target_map.json",
                "paper/4.Evaluation.tex",
            ],
            [
                equal("quality audit", quality.get("audit_status"), "PASS"),
                equal(
                    "quality completion gate",
                    quality.get("p0_completion_status"),
                    "PASS_WITH_RESTRICTED_ELIGIBLE_SUBSET",
                ),
                equal(
                    "default noiseless pass counts",
                    {
                        key: default_quality.get(key, {}).get("noiseless_quality_pass_count")
                        for key in ["ml", "chemistry", "optimization", "simulation"]
                    },
                    {"ml": 0, "chemistry": 48, "optimization": 0, "simulation": 256},
                ),
                equal(
                    "default hardware eligible counts",
                    {
                        key: default_quality.get(key, {}).get("hardware_target_eligible_count")
                        for key in ["ml", "chemistry", "optimization", "simulation"]
                    },
                    {"ml": 0, "chemistry": 0, "optimization": 0, "simulation": 12},
                ),
                equal("quality target CSV rows", csv_rows("data/processed/perlmutter/quality_qualified_target_map.csv"), 10656),
                contains(
                    "paper enforces quality-first eligibility",
                    "paper/4.Evaluation.tex",
                    [
                        "Only the 12 Sim. cases",
                        "same-record, full-loop, quality-qualified hardware targets",
                        "explicitly conditional lower bounds",
                    ],
                ),
            ],
        )
    )

    items.append(
        item(
            "finite_shot_quality",
            "The direct finite-shot closure covers 68 selected records, three shot counts, and 12 replicates.",
            ["data/processed/perlmutter/finite_shot_quality_sensitivity.json"],
            [
                equal("finite-shot audit", finite.get("audit_status"), "PASS"),
                equal("selected source records", finite.get("selected_source_records"), 68),
                equal("shot grid", finite.get("shot_grid"), [1000, 10000, 100000]),
                equal("replicates per case", finite.get("replicates_per_case"), 12),
                equal("shot-level records", len(finite_records), 204),
                equal(
                    "10k selected records by family",
                    finite_10k_counts,
                    {"ml": 4, "chemistry": 8, "optimization": 24, "simulation": 32},
                ),
                equal(
                    "10k full-loop eligible records",
                    eligible_10k_counts,
                    {"ml": 0, "chemistry": 0, "optimization": 0, "simulation": 12},
                ),
            ],
        )
    )

    items.append(
        item(
            "dependency_schedule",
            "Every retained record uses compiled or source-audited static scheduling, with no aggregate fallback.",
            ["data/processed/perlmutter/dependency_schedule_coverage.json"],
            [
                equal("schedule audit", schedule.get("audit_status"), "PASS"),
                equal("schedule records", schedule_coverage.get("records"), 3552),
                equal("compiled waves", schedule_coverage.get("compiled_dependency_wave"), 224),
                equal("source-audited static loops", schedule_coverage.get("source_audited_static_loop"), 3040),
                equal("single-circuit schedules", schedule_coverage.get("source_audited_single_circuit"), 512),
                equal("aggregate fallbacks", schedule_coverage.get("aggregate_total_demand_fallback"), 0),
                equal("adaptive traces claimed", schedule_coverage.get("adaptive_optimizer_trace"), 0),
                check(
                    "first target stable across implemented schedule modes",
                    all(
                        entry.get("stable")
                        for entry in schedule.get("conditional_target_stability", {}).values()
                    ),
                    schedule.get("conditional_target_stability", {}),
                    "all stable",
                ),
            ],
        )
    )

    items.append(
        item(
            "statistical_robustness",
            "Hierarchical confidence intervals use configurations and seeds as distinct resampling levels.",
            ["data/processed/perlmutter/statistical_robustness.json"],
            [
                equal("statistics audit", stats.get("audit_status"), "PASS"),
                equal("bootstrap samples", stats.get("resampling_contract", {}).get("bootstrap_samples"), 2000),
                equal("outer resampling unit", stats.get("resampling_contract", {}).get("outer_unit"), "structural workload configuration"),
                equal("inner resampling unit", stats.get("resampling_contract", {}).get("inner_unit"), "distinct seed within selected configuration"),
                equal("same-instance repeats in main corpus", stats.get("resampling_contract", {}).get("same-instance_repeat_trials_in_main_corpus"), 0),
                equal("repeat timing gate", stats.get("timing_repeat_inventory", {}).get("passed_original_gate"), True),
            ],
        )
    )

    items.append(
        item(
            "ft_reliability",
            "Case-level reliability yields distance 13--15, 79--86 T states, and a 39,351--42,961x eligible crossover.",
            ["data/processed/perlmutter/ft_reliability_and_space_budget.json"],
            [
                equal("FT audit", ft.get("audit_status"), "PASS"),
                equal("FT eligible records", ft.get("quality_qualified_records"), 12),
                equal("QDK distance cross-check", ft.get("qdk_distance_crosscheck", {}).get("status"), "PASS"),
                equal("QDK matched records", ft.get("qdk_distance_crosscheck", {}).get("matches"), 100),
                equal("eligible distances", ft_sim.get("distance_values"), [13, 15]),
                equal("eligible T-state values", ft_sim.get("required_t_states_per_rotation_values"), [79, 82, 83, 86]),
                check(
                    "eligible crossover rounds to manuscript range",
                    len(ft_range) == 2 and round(ft_range[0]) == 39351 and round(ft_range[1]) == 42961,
                    ft_range,
                    [39351, 42961],
                ),
                check(
                    "factory count rounds to manuscript range",
                    len(ft_factory_count) == 2
                    and round(ft_factory_count[0]) == 2518441
                    and round(ft_factory_count[1]) == 2749501,
                    ft_factory_count,
                    [2518441, 2749501],
                ),
                close("nonfactory parity fraction", ft_sim.get("native_parity_feasible_fraction"), 0.5),
                contains(
                    "paper reports reliability-qualified range",
                    "paper/4.Evaluation.tex",
                    ["distance 13--15", "79--86 T states", "39,351--42,961", "2.52--2.75 million factories"],
                ),
            ],
        )
    )

    items.append(
        item(
            "joint_dse",
            "The joint sweep covers 384 scenarios and 26,112 evaluated case points with a stable factory-first low-supply region.",
            ["data/processed/perlmutter/joint_bottleneck_phase_map.json"],
            [
                equal("joint DSE audit", joint.get("audit_status"), "PASS"),
                equal("joint scenarios", joint_design.get("unique_points"), 384),
                equal("joint case points", joint_design.get("evaluated_case_points"), 26112),
                equal("probabilities not assigned", joint_design.get("scenario_probability_assigned"), False),
                equal("stable first target", joint_headline.get("stable_first_target"), "factory_supply"),
                equal("stable low-supply cells", joint_headline.get("stable_region_cells"), 6),
                contains(
                    "paper reports conditional phase transitions",
                    "paper/4.Evaluation.tex",
                    ["384 deterministic", "1--100$\\times$", "shot parallelism", "logical-cycle"],
                ),
            ],
        )
    )

    items.append(
        item(
            "component_replacement",
            "Matched LSQCA movement removes all six baseline parity cases; BOSS remains a conditional graph envelope.",
            [
                "data/processed/perlmutter/component_replacement_case_studies.json",
                "data/processed/perlmutter/joint_bottleneck_phase_map.json",
            ],
            [
                equal("replacement audit", replacement.get("audit_status"), "PASS"),
                equal("eligible replacement records", joint_lsqca.get("records"), 12),
                equal("point-SAM area wins", joint_lsqca.get("point_sam_area_improvement_records"), 0),
                equal("baseline parity records", joint_lsqca.get("runtime_parity_base_records"), 6),
                equal("lower movement parity records", joint_lsqca.get("runtime_parity_lower_records"), 0),
                equal("upper movement parity records", joint_lsqca.get("runtime_parity_upper_records"), 0),
                close("lower movement median inflation", joint_lsqca.get("median_runtime_inflation_lower"), 3.115300958273699),
                close("upper movement median inflation", joint_lsqca.get("median_runtime_inflation_upper"), 5.230601916547398),
                equal("standalone area wins", replacement_headline.get("eligible_point_sam_area_improvement_cases"), 0),
                contains(
                    "paper uses matched-event replacement",
                    "paper/4.Evaluation.tex",
                    ["without borrowing its reported mean speedup", "3.12$\\times$", "5.23$\\times$", "BOSS-compatible graph envelope"],
                ),
            ],
        )
    )

    items.append(
        item(
            "ml_cifar_matched_feature_proxy",
            "CIFAR-10 compares native and circuit features on the same split and exposes a deployment-facing native frontier.",
            ["data/processed/perlmutter/ml_cifar10_matched_comparison.json"],
            [
                equal("CIFAR schema", cifar.get("schema"), "qsup.ml-cifar10-matched-comparison.v2"),
                close("native accuracy", cifar.get("native", {}).get("test_accuracy"), 0.8185),
                close("quantum-feature accuracy", cifar.get("quantum_feature", {}).get("test_accuracy"), 0.336),
                close("runtime ratio", cifar.get("ratios", {}).get("quantum_to_native_compute_runtime"), 2.0374640841208773),
                equal("same feature budget", cifar.get("quantum_feature", {}).get("features"), 108),
                contains(
                    "paper reports matched CIFAR contract",
                    "paper/4.Evaluation.tex",
                    ["same CIFAR-10 50,000/10,000 split", "115.16~s", "33.60\\%", "Pool-108"],
                ),
            ],
        )
    )

    risk_checks = [
        contains(
            "HPC evidence is not QPU timing",
            "paper/1.Introduction.tex",
            ["Their performance is not future-QPU performance", "Neither qubit count nor GPU count is treated as advantage evidence"],
        ),
        contains(
            "controlled and deployment evidence remain separate",
            "paper/2.Background.tex",
            ["Controlled 4--20-qubit records", "Distributed 36--40-qubit state-vector runs establish HPC simulation capacity only"],
        ),
        contains(
            "adaptive and factory-internal gaps are explicit",
            "paper/3.Design.tex",
            ["uncompiled adaptive traces remain explicit unsupported flags", "not presented as the full BOSS compiler"],
        ),
        contains(
            "large Chem lacks matched VQE closure",
            "paper/4.Evaluation.tex",
            ["do not have a matched large-space VQE-quality closure", "are not assigned a physical target"],
        ),
        contains(
            "PPA and real-QPU limits are explicit",
            "paper/5.Discussion.tex",
            ["no adaptive or mid-circuit dependency trace is claimed", "measured QPU output"],
        ),
        excludes(
            "no unsupported priority or novelty claims",
            "paper/1.Introduction.tex",
            ["first classical-versus-quantum", "largest quantum simulation", "GPU scaling predicts QPU"],
        ),
    ]
    items.append(
        item(
            "review_risk_traceability",
            "The manuscript states the controlled-scale, projection, adaptive-trace, large-Chem, PPA, and novelty boundaries at the point of use.",
            [
                "paper/1.Introduction.tex",
                "paper/2.Background.tex",
                "paper/3.Design.tex",
                "paper/4.Evaluation.tex",
                "paper/5.Discussion.tex",
            ],
            risk_checks,
        )
    )

    figures = included_figures()
    figure_checks = [file_check(figure, 1024) for figure in figures]
    figure_checks.extend(
        [
            equal("included figure count", len(figures), 20),
            check(
                "only one two-column figure",
                text.count("\\begin{figure*}") == 1
                and "fig:large-proxy-quality-cost" in read_text("paper/4.Evaluation.tex"),
                text.count("\\begin{figure*}"),
                1,
            ),
        ]
    )
    items.append(
        item(
            "paper_figures",
            "All and only manuscript-included PDF figures are present and nonempty.",
            figures,
            figure_checks,
        )
    )

    items.append(
        item(
            "manuscript_claims",
            "The abstract, evaluation, discussion, and conclusion use the authoritative P0 scope and values.",
            [
                "paper/0.Main.tex",
                "paper/4.Evaluation.tex",
                "paper/5.Discussion.tex",
                "paper/6.Conclusion.tex",
            ],
            [
                contains(
                    "abstract reports the restricted quality contract",
                    "paper/0.Main.tex",
                    ["only 12 simulation records", "39,351--42,961", "384 deterministic joint-design scenarios"],
                ),
                contains(
                    "conclusion preserves conditional scope",
                    "paper/6.Conclusion.tex",
                    ["12 same-record, full-loop Sim. targets", "matched LSQCA movement", "not a simulator speedup"],
                ),
                excludes(
                    "obsolete physical headlines removed",
                    "paper/0.Main.tex",
                    ["10,000--16,300", "fixed $d=15$", "16-T assumption"],
                ),
                check("manuscript has quality-first vocabulary", text.count("quality") >= 30, text.count("quality"), ">=30"),
            ],
        )
    )

    manifest_packages = manifest.get("packages", [])
    manifest_files = [
        file_record
        for package in manifest_packages
        for file_record in package.get("files", [])
    ]
    hash_mismatches = [
        file_record.get("path")
        for file_record in manifest_files
        if file_record.get("exists")
        and (
            not exists(file_record.get("path", ""))
            or sha256(file_record["path"]) != file_record.get("sha256")
        )
    ]
    items.append(
        item(
            "artifact_manifest",
            "The generated manifest resolves every P0 evidence package to concrete files.",
            ["data/processed/perlmutter/paper_artifact_manifest.json"],
            [
                equal("manifest schema", manifest.get("schema"), "qarchgauge.strong-accept-manifest.v1"),
                equal("manifest package count", len(manifest_packages), 13),
                equal("manifest pass", manifest.get("passed"), True),
                check(
                    "manifest package IDs unique",
                    len({package.get("id") for package in manifest_packages}) == len(manifest_packages),
                    [package.get("id") for package in manifest_packages],
                    "unique",
                ),
                check(
                    "all manifest files resolve",
                    all(
                        file_record.get("exists")
                        for package in manifest_packages
                        for file_record in package.get("files", [])
                    ),
                    "resolved",
                    True,
                ),
                check(
                    "all manifest SHA-256 fingerprints match",
                    not hash_mismatches,
                    hash_mismatches,
                    [],
                ),
            ],
        )
    )

    items.append(
        item(
            "submission_package",
            "The paper source, bibliography, PDF, README, and audit entry points are present.",
            ["paper/main.pdf", "README.md", "paper/references.bib"],
            [
                file_check("paper/main.pdf", 100000),
                file_check("paper/references.bib", 10000),
                contains(
                    "README reproduces all P0 audits",
                    "README.md",
                    [
                        "audit_quality_qualified_targets.py",
                        "audit_dependency_schedule_coverage.py",
                        "audit_statistical_robustness.py",
                        "audit_ft_reliability_budget.py",
                        "audit_joint_dse.py",
                        "make -B -C paper audit",
                    ],
                ),
            ],
        )
    )

    result = {
        "schema": "qarchgauge.paper-evidence-audit.v2",
        "scope": "P0-A through P0-F evidence-to-paper contract",
        "items": items,
        "passed": all(entry["passed"] for entry in items),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
