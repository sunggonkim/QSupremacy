#!/usr/bin/env python3
"""Render paper and supplementary PDF assets into GitHub-readable PNG panels."""

from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "paper" / "figures"
OUTPUT = FIGURES / "readme"
SCALE = 3.0
GAP = 16


LAYOUTS = {
    "paper_fig01.png": [["intro_threshold_summary.pdf"]],
    "paper_fig02.png": [["design_overview.pdf"]],
    "paper_fig03.png": [["weak_scaling.pdf"], ["strong_scaling.pdf"]],
    "paper_fig04.png": [[
        "opt_qaoa_quality_proxy.pdf",
        "chem_vqe_quality_cost_proxy.pdf",
        "sim_quality_cost_proxy.pdf",
    ]],
    "paper_fig05.png": [
        ["ml_cifar10_legend.pdf"],
        ["ml_cifar10_runtime.pdf", "ml_cifar10_accuracy.pdf"],
    ],
    "paper_fig06.png": [["roofline_deadline_shrink.pdf"]],
    "paper_fig07.png": [["quality_noiseless_gate.pdf", "quality_finite_shot_gate.pdf"]],
    "paper_fig08.png": [["trace_aware_logical_lower_bound.pdf"]],
    "paper_fig09.png": [["ft_contract_parameters.pdf"], ["ft_reliability_target.pdf"]],
    "paper_fig10.png": [["joint_bottleneck_phase_map.pdf"], ["resource_removal_ceiling.pdf"]],
    "paper_fig11.png": [["lsqca_matched_replacement.pdf"]],
    "paper_fig12.png": [["sim_hardware_modality_pivot.pdf"]],
    "supp_timeout_progress.png": [["low_gpu_timeout_progress.pdf"]],
    "supp_controlled_landscape.png": [
        ["practical_suite_legend.pdf"],
        ["practical_suite_summary.pdf"],
    ],
    "supp_digits_calibration.png": [
        ["digits_legend.pdf"],
        ["digits_required_speedup.pdf", "digits_quality_speedup.pdf"],
    ],
    "supp_scaling_diagnostics.png": [["weak_scaling_efficiency.pdf", "strong_scaling_speedup.pdf"]],
    "supp_sensitivity_transition.png": [["sensitivity_bottleneck_transition.pdf", "sensitivity_runtime_parity.pdf"]],
    "supp_factory_sensitivity.png": [["physical_factory_crossover.pdf", "physical_post_rotation_utility.pdf"]],
    "supp_native_rotation_detail.png": [
        ["native_rotation_platform_legend.pdf"],
        ["native_rotation_neutral_atom.pdf", "native_rotation_trapped_ion.pdf"],
    ],
    "supp_feedback_aggregator.png": [["feedback_aggregator_architecture.pdf"], ["feedback_aggregator_ablation.pdf"]],
    "supp_architecture_focus.png": [["architecture_focus_matrix.pdf"]],
    "supp_workload_coverage.png": [["workload_growth_coverage.pdf"]],
}


def render_pdf(name):
    source = FIGURES / name
    if not source.is_file():
        raise FileNotFoundError(source)
    document = fitz.open(source)
    if document.page_count != 1:
        raise RuntimeError("expected one-page figure: {}".format(source))
    pixmap = document[0].get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    document.close()
    return image


def compose(rows):
    rendered_rows = []
    for row in rows:
        images = [render_pdf(name) for name in row]
        width = sum(image.width for image in images) + GAP * (len(images) - 1)
        height = max(image.height for image in images)
        canvas = Image.new("RGB", (width, height), "white")
        x = 0
        for image in images:
            canvas.paste(image, (x, (height - image.height) // 2))
            x += image.width + GAP
        rendered_rows.append(canvas)

    width = max(row.width for row in rendered_rows)
    height = sum(row.height for row in rendered_rows) + GAP * (len(rendered_rows) - 1)
    canvas = Image.new("RGB", (width, height), "white")
    y = 0
    for row in rendered_rows:
        canvas.paste(row, ((width - row.width) // 2, y))
        y += row.height + GAP
    return canvas


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected = set()
    for output_name, rows in LAYOUTS.items():
        output_path = OUTPUT / output_name
        compose(rows).save(output_path, optimize=True)
        expected.add(output_path)
        print(output_path.relative_to(ROOT))
    for stale in OUTPUT.glob("*.png"):
        if stale not in expected:
            stale.unlink()


if __name__ == "__main__":
    main()
