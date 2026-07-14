#!/usr/bin/env python3
"""Run the final HPCA submission and Section 14 GO-gate audit."""

import json
import os
import re
import subprocess


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(
    ROOT, "data", "processed", "perlmutter", "submission_readiness_audit.json"
)

PAPER_SOURCES = [
    "paper/0.Main.tex",
    "paper/1.Introduction.tex",
    "paper/2.Background.tex",
    "paper/3.Design.tex",
    "paper/4.Evaluation.tex",
    "paper/5.Discussion.tex",
    "paper/5.RelatedWork.tex",
    "paper/6.Conclusion.tex",
    "paper/references.bib",
]


def path(rel_path):
    return os.path.join(ROOT, rel_path)


def exists(rel_path):
    return os.path.isfile(path(rel_path))


def read_text(rel_path):
    if not exists(rel_path):
        return ""
    with open(path(rel_path), errors="replace") as handle:
        return handle.read()


def load_json(rel_path):
    if not exists(rel_path):
        return {}
    try:
        with open(path(rel_path), errors="replace") as handle:
            return json.load(handle)
    except (ValueError, OSError):
        return {}


def run(command):
    try:
        process = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
        return process.returncode, process.stdout, process.stderr
    except OSError as error:
        return 127, "", str(error)


def check(name, passed, detail, severity="error"):
    return {
        "name": name,
        "passed": bool(passed),
        "severity": severity,
        "detail": detail,
    }


def contains(text, needles):
    return all(needle in text for needle in needles)


def paper_text():
    return "\n".join(read_text(source) for source in PAPER_SOURCES[:-1])


def included_figures():
    figures = []
    for source in PAPER_SOURCES[:-1]:
        for match in re.findall(
            r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", read_text(source)
        ):
            figures.append("paper/{}".format(match))
    return sorted(set(figures))


def pdf_pages():
    log = read_text("paper/main.log")
    match = re.search(r"Output written on main\.pdf \((\d+) pages", log)
    if match:
        return int(match.group(1))
    code, stdout, _ = run(["pdfinfo", "paper/main.pdf"])
    if code == 0:
        match = re.search(r"^Pages:\s+(\d+)", stdout, re.MULTILINE)
        if match:
            return int(match.group(1))
    return None


def references_start_page():
    aux = read_text("paper/main.aux")
    match = re.search(
        r"\\contentsline\s+\{section\}\{References\}\{(\d+)\}", aux
    )
    return int(match.group(1)) if match else None


def pdf_layout_text():
    code, stdout, _ = run(["pdftotext", "-layout", "paper/main.pdf", "-"])
    return stdout if code == 0 else ""


def pdf_file_text(rel_path):
    code, stdout, _ = run(["pdftotext", "-layout", rel_path, "-"])
    return stdout if code == 0 else ""


def pdf_graphics_audit(figures):
    """Audit final embedded font type and effective figure/caption text size."""
    try:
        import fitz
    except ImportError as error:
        return {
            "available": False,
            "error": str(error),
            "type3": [],
            "minimum_figure_text_pt": None,
            "minimum_caption_text_pt": None,
        }

    figure_fonts = set()
    for figure in figures:
        document = fitz.open(path(figure))
        for page in document:
            for block in page.get_text("dict").get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("text", "").strip():
                            figure_fonts.add(span.get("font"))
        document.close()

    document = fitz.open(path("paper/main.pdf"))
    type3 = []
    figure_sizes = []
    caption_sizes = []
    for page_index, page in enumerate(document):
        for font in page.get_fonts(full=True):
            if font[2] == "Type3":
                type3.append(
                    {"page": page_index + 1, "font_type": font[2], "font": font[3]}
                )
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    if span.get("font") in figure_fonts:
                        figure_sizes.append(float(span["size"]))
                    if text.startswith("Fig."):
                        caption_sizes.append(float(span["size"]))
    document.close()
    return {
        "available": True,
        "error": None,
        "type3": type3,
        "figure_fonts": sorted(figure_fonts),
        "minimum_figure_text_pt": min(figure_sizes) if figure_sizes else None,
        "minimum_caption_text_pt": min(caption_sizes) if caption_sizes else None,
    }


def artifact_fresh(output, inputs):
    if not exists(output) or not all(exists(item) for item in inputs):
        return False
    return os.path.getmtime(path(output)) >= max(
        os.path.getmtime(path(item)) for item in inputs
    )


def evidence_item_passed(evidence, name):
    return any(
        item.get("name") == name and item.get("passed")
        for item in evidence.get("items", [])
    )


def main():
    evidence = load_json("data/processed/perlmutter/paper_evidence_audit.json")
    manifest = load_json("data/processed/perlmutter/paper_artifact_manifest.json")
    projection = load_json("data/processed/perlmutter/projection_invariant_audit.json")
    quality = load_json("data/processed/perlmutter/quality_qualified_target_map.json")
    finite = load_json("data/processed/perlmutter/finite_shot_quality_sensitivity.json")
    schedule = load_json("data/processed/perlmutter/dependency_schedule_coverage.json")
    stats = load_json("data/processed/perlmutter/statistical_robustness.json")
    ft = load_json("data/processed/perlmutter/ft_reliability_and_space_budget.json")
    joint = load_json("data/processed/perlmutter/joint_bottleneck_phase_map.json")
    replacement = load_json(
        "data/processed/perlmutter/component_replacement_case_studies.json"
    )
    repeat = load_json("data/processed/perlmutter/repeat_timing_gate_latest.json")
    alignment = load_json(
        "data/processed/perlmutter/previous_paper_alignment_metrics.json"
    )
    deep_trace = load_json(
        "data/processed/perlmutter/previous_paper_deep_trace.json"
    )
    style = load_json("data/processed/perlmutter/previous_paper_style_audit.json")

    main = read_text("paper/0.Main.tex")
    intro = read_text("paper/1.Introduction.tex")
    background = read_text("paper/2.Background.tex")
    design = read_text("paper/3.Design.tex")
    evaluation = read_text("paper/4.Evaluation.tex")
    discussion = read_text("paper/5.Discussion.tex")
    related = read_text("paper/5.RelatedWork.tex")
    conclusion = read_text("paper/6.Conclusion.tex")
    all_paper = paper_text()
    log = read_text("paper/main.log")
    blg = read_text("paper/main.blg")
    bib = read_text("paper/references.bib")
    bbl = read_text("paper/main.bbl")
    readme = read_text("README.md")
    layout = pdf_layout_text()
    figures = included_figures()
    pages = pdf_pages()
    references_page = references_start_page()

    # Each encoded asset must resolve to a visible legend, a shared legend in
    # its enclosing figure, or direct labels. This makes legend regressions a
    # submission failure instead of relying only on a manual PDF spot check.
    figure_presentation_contract = {
        "paper/figures/intro_threshold_summary.pdf": (
            "paper/figures/intro_threshold_summary.pdf", ["ML", "Chem.", "Opt.", "Sim."]
        ),
        "paper/figures/design_overview.pdf": (
            "paper/figures/design_overview.pdf", ["Native HPC", "Circuit evidence", "Finite-shot quality gate"]
        ),
        "paper/figures/weak_scaling.pdf": (
            "paper/figures/weak_scaling.pdf", ["Actual", "Ideal"]
        ),
        "paper/figures/strong_scaling.pdf": (
            "paper/figures/strong_scaling.pdf", ["Actual", "Ideal"]
        ),
        "paper/figures/opt_qaoa_quality_proxy.pdf": (
            "paper/figures/opt_qaoa_quality_proxy.pdf", ["10q", "14q", "18q", "20q"]
        ),
        "paper/figures/chem_vqe_quality_cost_proxy.pdf": (
            "paper/figures/chem_vqe_quality_cost_proxy.pdf", ["Pair-UCC", "0.01 Ha", "measurement groups", "Energy error vs. exact"]
        ),
        "paper/figures/sim_quality_cost_proxy.pdf": (
            "paper/figures/sim_quality_cost_proxy.pdf", ["16q", "18q", "20q", "0.99"]
        ),
        "paper/figures/ml_cifar10_legend.pdf": (
            "paper/figures/ml_cifar10_legend.pdf", ["ResNet-18 frontier", "Pool-108 control", "QFeature circuit"]
        ),
        "paper/figures/ml_cifar10_runtime.pdf": (
            "paper/figures/ml_cifar10_legend.pdf", ["ResNet-18 frontier", "Pool-108 control", "QFeature circuit"]
        ),
        "paper/figures/ml_cifar10_accuracy.pdf": (
            "paper/figures/ml_cifar10_legend.pdf", ["ResNet-18 frontier", "Pool-108 control", "QFeature circuit"]
        ),
        "paper/figures/roofline_deadline_shrink.pdf": (
            "paper/figures/roofline_deadline_shrink.pdf", ["Measured runtime", "Roofline lower bound", "Runtime lower bound / measured runtime"]
        ),
        "paper/figures/quality_noiseless_gate.pdf": (
            "paper/figures/quality_noiseless_gate.pdf", ["Pass", "Fail"]
        ),
        "paper/figures/quality_finite_shot_gate.pdf": (
            "paper/figures/quality_finite_shot_gate.pdf", ["Quality pass", "Complete loop"]
        ),
        "paper/figures/trace_aware_logical_lower_bound.pdf": (
            "paper/figures/trace_aware_logical_lower_bound.pdf", ["Faster", "Slower", "Median", "Equal runtime", "Projected logical runtime"]
        ),
        "paper/figures/ft_contract_parameters.pdf": (
            "paper/figures/ft_contract_parameters.pdf", ["All shots protected", "Failed shots allowed", "Surface-code distance", "T states per rotation", "Eligible record", "Median"]
        ),
        "paper/figures/ft_reliability_target.pdf": (
            "paper/figures/ft_reliability_target.pdf", ["All shots protected", "Failed shots allowed", "Required T-state factories", "Eligible record", "Median"]
        ),
        "paper/figures/joint_bottleneck_phase_map.pdf": (
            "paper/figures/joint_bottleneck_phase_map.pdf", ["T-state supply", "Shot lanes", "Gate speed", "Already faster", "Parallel shot lanes"]
        ),
        "paper/figures/resource_removal_ceiling.pdf": (
            "paper/figures/resource_removal_ceiling.pdf", ["Current", "640k factories", "3.2M factories + 10k lanes", "Speedup if one resource were free"]
        ),
        "paper/figures/lsqca_matched_replacement.pdf": (
            "paper/figures/lsqca_matched_replacement.pdf", ["Record", "Q1--Q3", "Median", "Equal runtime"]
        ),
        "paper/figures/sim_hardware_modality_pivot.pdf": (
            "paper/figures/sim_hardware_modality_pivot.pdf", ["T-state generation", "1Q gates", "2Q gates", "Readout/reuse", "Move/control", "Share of projected runtime"]
        ),
    }
    figure_presentation_failures = []
    if set(figures) != set(figure_presentation_contract):
        figure_presentation_failures.append(
            {
                "uncontracted": sorted(set(figures) - set(figure_presentation_contract)),
                "stale": sorted(set(figure_presentation_contract) - set(figures)),
            }
        )
    for figure in figures:
        if figure not in figure_presentation_contract:
            continue
        evidence_figure, required_terms = figure_presentation_contract[figure]
        evidence_text = pdf_file_text(evidence_figure)
        missing_terms = [term for term in required_terms if term not in evidence_text]
        if missing_terms:
            figure_presentation_failures.append(
                {"figure": figure, "evidence": evidence_figure, "missing": missing_terms}
            )
    figure_presentation_pass = not figure_presentation_failures
    graphics_audit = pdf_graphics_audit(figures)

    artifact_statuses = {
        "quality": quality.get("audit_status"),
        "finite_shot": finite.get("audit_status"),
        "schedule": schedule.get("audit_status"),
        "statistics": stats.get("audit_status"),
        "ft": ft.get("audit_status"),
        "joint_dse": joint.get("audit_status"),
        "replacement": replacement.get("audit_status"),
    }
    expected_artifact_statuses = {key: "PASS" for key in artifact_statuses}
    manifest_pass = manifest.get("passed") and all(
        package.get("status") == "PASS" for package in manifest.get("packages", [])
    )

    source_and_figures = PAPER_SOURCES + figures
    anonymous_pattern = re.compile(
        r"sgkim|sunggon|sung\s+gon|seoultech|hpcbigdata|/global|/pscratch|github\.com/sunggonkim",
        re.IGNORECASE,
    )
    anonymous_hits = anonymous_pattern.findall(all_paper)
    metadata_hits = []
    if exists("paper/main.pdf"):
        with open(path("paper/main.pdf"), "rb") as handle:
            raw_pdf = handle.read().decode("latin-1", errors="replace")
        for pdf_key in ["/Author", "/Title", "/Subject", "/Keywords"]:
            for match in re.finditer(re.escape(pdf_key), raw_pdf):
                snippet = raw_pdf[match.start(): match.end() + 200]
                metadata_hits.extend(anonymous_pattern.findall(snippet))

    overfull = [
        line for line in log.splitlines() if "Overfull \\hbox" in line
    ]
    undefined = re.findall(
        r"(?:Citation|Reference).*undefined|There were undefined references",
        log,
        flags=re.IGNORECASE,
    )
    todo = re.findall(
        r"\b(?:TODO|TBD|placeholder|undefined citation)\b",
        all_paper,
        flags=re.IGNORECASE,
    )
    bad_shortcuts = re.findall(
        r"\btoy\b|our previous|normalized from completed|completed lower-end",
        all_paper,
        flags=re.IGNORECASE,
    )
    all_author_violations = re.findall(
        r"\b(?:et al\.?|and others)\b|\\etal\b", bib + "\n" + bbl, re.IGNORECASE
    )

    checks = []

    checks.extend(
        [
            check("main_pdf_exists", exists("paper/main.pdf"), "paper/main.pdf exists"),
            check(
                "main_pdf_fresh",
                artifact_fresh("paper/main.pdf", source_and_figures)
                and artifact_fresh("paper/main.log", source_and_figures),
                "PDF and log are newer than all included TeX, bibliography, and figure files",
            ),
            check("page_count_known", pages is not None, "PDF has {} total pages".format(pages)),
            check(
                "hpca_full_body_budget",
                references_page == 12,
                "references begin on page {}; the manuscript must occupy body pages 1--11".format(references_page),
            ),
            check(
                "official_template_dimensions",
                contains(
                    main,
                    [
                        r"\documentclass[10pt,conference]{IEEEtran}",
                        r"\usepackage[letterpaper,left=0.7in,right=0.7in,top=0.7in,bottom=1in]{geometry}",
                        r"\setlength{\columnsep}{0.1in}",
                        r"\bibliographystyle{IEEEtran}",
                    ],
                )
                and not re.search(
                    r"\\setlength\{\\(?:textfloatsep|floatsep|intextsep|dblfloatsep|dbltextfloatsep)\}",
                    main,
                ),
                "IEEEtran geometry is present without prohibited float-spacing compression",
            ),
            check("latex_no_undefined", not undefined, "undefined references/citations: {}".format(undefined)),
            check("latex_no_overfull_hbox", not overfull, "overfull hboxes: {}".format(len(overfull))),
            check("bibtex_no_warnings", "Warning--" not in blg, "BibTeX has no warnings"),
            check("references_list_all_authors", not all_author_violations, "all-author policy violations: {}".format(all_author_violations)),
            check("paper_no_todos", not todo, "TODO/TBD markers: {}".format(todo)),
            check("paper_no_reviewer_shortcuts", not bad_shortcuts, "review-sensitive shortcuts: {}".format(bad_shortcuts)),
            check(
                "anonymous_submission",
                contains(main, ["HPCA 2027 Submission \\#NaN", "Confidential Draft", "\\author{}"]) and not anonymous_hits and not metadata_hits,
                "double-blind banner is present; source hits={}, metadata hits={}".format(anonymous_hits, metadata_hits),
            ),
            check(
                "ai_use_disclosure",
                contains(main, ["\\section*{AI Use}", "OpenAI Codex", "executed the experiments", "approved all final", "technical claims"]),
                "AI-use disclosure identifies tool, scope, author execution, and verification",
            ),
            check(
                "figure_legend_or_direct_label_coverage",
                figure_presentation_pass,
                "all 20 included assets resolve to their own legend, a shared legend, or direct labels; failures={}".format(
                    figure_presentation_failures
                ),
            ),
            check(
                "pdf_no_type3_fonts",
                graphics_audit.get("available") and not graphics_audit.get("type3"),
                "Type 3 font objects: {}; audit error={}".format(
                    graphics_audit.get("type3"), graphics_audit.get("error")
                ),
            ),
            check(
                "figure_text_minimum_8pt",
                graphics_audit.get("available")
                and graphics_audit.get("minimum_figure_text_pt") is not None
                and graphics_audit["minimum_figure_text_pt"] >= 7.95,
                "minimum effective embedded figure text is {:.2f} pt".format(
                    graphics_audit.get("minimum_figure_text_pt") or 0.0
                ),
            ),
            check(
                "caption_text_minimum_9pt",
                graphics_audit.get("available")
                and graphics_audit.get("minimum_caption_text_pt") is not None
                and graphics_audit["minimum_caption_text_pt"] >= 8.90,
                "minimum caption text is {:.2f} pt".format(
                    graphics_audit.get("minimum_caption_text_pt") or 0.0
                ),
            ),
        ]
    )

    # Section 14 GO conditions. These are deliberately named after the plan.
    checks.append(
        check(
            "go_identity",
            contains(
                main + intro + conclusion,
                [
                    "HPC-driven architecture diagnosis framework",
                    "evidence cost, never a QPU clock",
                    "not a simulator speedup",
                ],
            )
            and "new QPU microarchitecture" not in all_paper,
            "Abstract through Conclusion frame QArchGauge as an HPC-driven inversion",
        )
    )
    checks.append(
        check(
            "go_quality_eligibility",
            evidence_item_passed(evidence, "quality_qualified_targets")
            and quality.get("p0_completion_status")
            == "PASS_WITH_RESTRICTED_ELIGIBLE_SUBSET"
            and contains(
                evaluation,
                [
                    "Only the 12 Sim. cases",
                    "same-record, full-loop, quality-qualified hardware targets",
                    "Physical numbers for every other family are explicitly conditional lower bounds",
                ],
            ),
            "only 12 direct finite-shot full-loop Sim records are hardware-target eligible",
        )
    )
    checks.append(
        check(
            "go_trace_semantics",
            evidence_item_passed(evidence, "dependency_schedule")
            and schedule.get("coverage", {}).get("aggregate_total_demand_fallback") == 0
            and all(
                record.get("stable")
                for record in schedule.get("conditional_target_stability", {}).values()
            )
            and contains(design, ["No adaptive optimizer or mid-circuit branch is invented"]),
            "all records have compiled/source-audited static semantics; no fallback or invented DAG",
        )
    )
    ft_sim = (
        ft.get("by_workload_default_strict", {})
        .get("simulation", {})
        .get("quality_qualified_records", {})
    )
    checks.append(
        check(
            "go_ft_consistency",
            evidence_item_passed(evidence, "ft_reliability")
            and ft.get("qdk_distance_crosscheck", {}).get("status") == "PASS"
            and ft_sim.get("distance_values") == [13, 15]
            and ft_sim.get("required_t_states_per_rotation_values") == [79, 82, 83, 86]
            and contains(
                evaluation,
                [
                    "case-level reliability",
                    "2.52--2.75 million factories",
                    "factory qubits",
                    "Decoder reaction",
                ],
            ),
            "quality, shots, failure budget, distance, rotations, supply, space, and decoder form one contract",
        )
    )
    checks.append(
        check(
            "go_joint_robustness",
            evidence_item_passed(evidence, "joint_dse")
            and joint.get("design", {}).get("unique_points") == 384
            and joint.get("design", {}).get("evaluated_case_points") == 26112
            and joint.get("headline", {}).get("stable_region_cells") == 6
            and contains(evaluation, ["first for every lane count", "shot parallelism", "logical-cycle latency"]),
            "first, crossover, and next targets are reported from coupled deterministic regions",
        )
    )
    joint_lsqca = joint.get("headline", {}).get("lsqca_result", {})
    checks.append(
        check(
            "go_architecture_depth",
            evidence_item_passed(evidence, "component_replacement")
            and replacement.get("audit_status") == "PASS"
            and joint_lsqca.get("runtime_parity_base_records") == 6
            and joint_lsqca.get("runtime_parity_lower_records") == 0
            and contains(evaluation, ["LSQCA point-SAM", "matched load/store events", "BOSS-compatible graph envelope"]),
            "LSQCA is re-inverted with matched events and BOSS receives a bounded conditional hook",
        )
    )
    checks.append(
        check(
            "go_statistics",
            evidence_item_passed(evidence, "statistical_robustness")
            and stats.get("corpus", {}).get("structural_configurations") == 222
            and stats.get("corpus", {}).get("seed_values") == 16
            and stats.get("resampling_contract", {}).get("bootstrap_samples") == 2000
            and "Macro-average across four workload families" in stats.get("workload_balanced", {}).get("definition", "")
            and contains(evaluation, ["hierarchical-bootstrap 95\\% intervals", "macro-averages weight the four families equally"]),
            "headlines expose denominators, hierarchical CIs, and workload-balanced weighting",
        )
    )
    checks.append(
        check(
            "go_native_frontier",
            evidence_item_passed(evidence, "ml_cifar_matched_feature_proxy")
            and contains(
                evaluation,
                [
                    "A stronger native implementation only shortens $T_{\\mathrm{native}}$",
                    "one-A100 ResNet-18",
                    "not a measured implementation or a SOTA claim",
                ],
            )
            and "stress" in design,
            "executed native paths, moving frontier, and stress-vs-measurement boundary are explicit",
        )
    )
    related_keys = [
        "supermarq",
        "qedcbench",
        "quark2022",
        "beverland2022",
        "traceq2026",
        "darq2026",
        "pinball2026",
        "boss2025",
        "lsqca2025",
        "ssync2025",
        "cyclone2026",
        "qfw2025",
        "zhou2025softqem",
        "choi2023postselectedrotation",
    ]
    checks.append(
        check(
            "go_current_positioning",
            all(
                re.search(r"@[A-Za-z]+\{\s*" + re.escape(key) + r"\s*,", bib)
                for key in related_keys
            )
            and contains(
                related,
                [
                    "Application benchmarks and native comparison",
                    "FT estimation and critical-path evidence",
                    "QPU component architectures",
                    "HPC simulation and integration",
                ],
            )
            and "None inverts" in related
            and "adds same-record quality and loop closure" in related
            and "Our replacement changes only matched events and space" in related,
            "benchmark, FT, trace/control, component, HPC runtime, and quality-mechanism neighbors have exact contrasts",
        )
    )
    checks.append(
        check(
            "go_architecture_answer",
            contains(
                intro + design + evaluation + discussion,
                [
                    "whether the output is valid, which resource to improve first, how much it must improve, which resource becomes next",
                    "39,351--42,961",
                    "factory-first throughout the 1--100$\\times$ region",
                    "After $10^4$--$5\\times10^4$ factory-supply improvement",
                ],
            )
            and "algorithm/representation first" in design,
            "the paper states what improves now, by how much, when it changes, and where claims are conditional",
        )
    )
    caption_phrases = [
        "Measured circuit-application speedup required",
        "two-stage inversion",
        "Perlmutter evidence-generation scaling",
        "Quality recovery consumes circuit work",
        "Matched CIFAR-10 outcomes",
        "Adversarial native-runtime stress",
        "Quality eligibility precedes hardware targeting",
        "Logical-runtime lower bound with free T-state generation",
        "Reliability choices set physical cost",
        "How the next useful upgrade changes",
        "Matched-event LSQCA replacement",
        "Where projected time goes under three QPU approaches",
    ]
    wide_blocks = re.findall(
        r"\\begin\{figure\*\}.*?\\end\{figure\*\}", evaluation, re.DOTALL
    )
    checks.append(
        check(
            "go_presentation",
            len(figures) == 20
            and all(exists(figure) and os.path.getsize(path(figure)) >= 1024 for figure in figures)
            and len(wide_blocks) == 1
            and "fig:large-proxy-quality-cost" in wide_blocks[0]
            and bool(layout)
            and all(phrase in layout for phrase in caption_phrases)
            and not re.findall(r"QA\s+RCH|QARCH\s+GAUGE", layout)
            and figure_presentation_pass
            and style.get("passed"),
            "20 included assets, one deliberate two-column figure, extractable captions, and style audit all pass",
        )
    )
    checks.append(
        check(
            "go_reproducibility",
            artifact_statuses == expected_artifact_statuses
            and evidence.get("passed")
            and manifest_pass
            and projection.get("passed")
            and repeat.get("passed")
            and alignment.get("passed")
            and deep_trace.get("passed")
            and deep_trace.get("total_traced_blocks", 0) >= 60
            and style.get("passed")
            and contains(
                readme,
                [
                    "generate_strong_accept_manifest.py",
                    "make -B -C paper audit",
                    "Authoritative Artifacts",
                ],
            ),
            "P0 artifacts={}, evidence={}, manifest={}, projection={}, alignment/style/trace=PASS".format(
                artifact_statuses, evidence.get("passed"), manifest_pass, projection.get("passed")
            ),
        )
    )

    # Explicit residual limits are a passing claim boundary, not a warning.
    checks.append(
        check(
            "residual_limits_disclosed",
            contains(
                discussion,
                [
                    "hardware-qualified set is only twelve 4--7-qubit Sim. records",
                    "Large Chem. lacks a matched VQE loop",
                    "no adaptive or mid-circuit dependency trace is claimed",
                    "end-to-end energy",
                    "measured QPU output",
                ],
            ),
            "real-QPU, large VQE, adaptive trace, and PPA/energy limits are explicit",
        )
    )

    blocking = [entry for entry in checks if not entry["passed"] and entry["severity"] == "error"]
    warnings = [entry for entry in checks if not entry["passed"] and entry["severity"] == "warning"]
    status = "SUBMISSION_READY" if not blocking and not warnings else (
        "BLOCKED" if blocking else "EVIDENCE_READY_WITH_SUBMISSION_RISKS"
    )
    result = {
        "schema": "qarchgauge.submission-readiness.v2",
        "status": status,
        "page_count": pages,
        "references_start_page": references_page,
        "blocking_error_count": len(blocking),
        "warning_count": len(warnings),
        "graphics_audit": graphics_audit,
        "go_gate_count": sum(entry["name"].startswith("go_") for entry in checks),
        "go_gate_pass_count": sum(
            entry["name"].startswith("go_") and entry["passed"] for entry in checks
        ),
        "checks": checks,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
