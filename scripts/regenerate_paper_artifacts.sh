#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON=${PYTHON:-python3}
cd "$ROOT"

"$PYTHON" scripts/compile_chemistry_measurement_records.py \
  --output data/processed/perlmutter/chem_compiled_measurement_records.json
"$PYTHON" scripts/compile_chemistry_measurement_records.py \
  --fixtures \
    benchmarks/workloads/hamiltonians/h2_minimal_2q.json \
    benchmarks/workloads/hamiltonians/molecular_chain_4q.json \
  --output data/processed/perlmutter/chem_controlled_compiled_measurement_records.json
"$PYTHON" scripts/run_qdk_depth_resource_estimator_crosscheck.py
"$PYTHON" scripts/summarize_controlled_distributions.py \
  --input-csv data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv
"$PYTHON" scripts/summarize_advantage_projection.py \
  --input-csv data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv \
  --output-json data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json
"$PYTHON" scripts/summarize_projection_scenarios.py \
  --input-csv data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv \
  --output-json data/processed/perlmutter/practical_suite_projection_scenarios.json
"$PYTHON" scripts/summarize_physical_architecture_dse.py \
  --input-csv data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv \
  --chem-compiled data/processed/perlmutter/chem_compiled_measurement_records.json \
  --chem-controlled-compiled data/processed/perlmutter/chem_controlled_compiled_measurement_records.json \
  --qdk-depth data/processed/perlmutter/qdk_resource_estimator_qaoa_depth_crosscheck.json \
  --output data/processed/perlmutter/physical_architecture_dse.json
"$PYTHON" scripts/summarize_native_rotation_platforms.py
"$PYTHON" scripts/summarize_roofline_native_stress.py
"$PYTHON" scripts/summarize_feedback_aggregator_ablation.py
"$PYTHON" scripts/summarize_ml_cifar10_matched_comparison.py
"$PYTHON" scripts/plot_opt_qaoa_quality_proxy.py
"$PYTHON" scripts/plot_chem_vqe_quality_cost_proxy.py
"$PYTHON" scripts/plot_sim_quality_cost_proxy.py
"$PYTHON" scripts/generate_paper_figures.py
