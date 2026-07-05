# Paper Evidence Audit

Overall status: **PASS**

| Evidence item | Claim | Status | Files |
| --- | --- | --- | --- |
| expanded_digits | 160-case digits calibration with kernel and QNN/VQC thresholds | PASS | `data/processed/perlmutter/digits_expanded_55421321_55422142_summary.json`<br>`data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv` |
| large_practical_suite | 3,552-case strong-native practical suite on 32 Perlmutter GPU nodes | PASS | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json`<br>`data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv`<br>`data/raw/perlmutter/accounting/sacct_practical_suite_strongnative_32node_large128c0c127_20260704060230.txt` |
| workload_taxonomy | Bottleneck taxonomy over the 3,552-case strong-native suite | PASS | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json`<br>`paper/figures/workload_taxonomy.pdf` |
| advantage_projection | Advantage fractions over projected speedup and quality-gap recovery | PASS | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json`<br>`data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.md`<br>`paper/figures/advantage_frontier.pdf` |
| chemistry_active_space | 104-case OpenFermion/PySCF chemistry coverage gate | PASS | `data/processed/perlmutter/practical_suite_chem_active_6q8q_1node_20260704233824_chemistry_coverage.json`<br>`data/processed/perlmutter/practical_suite_chem_active_6q8q_1node_20260704233824_chemistry_coverage.md`<br>`data/raw/perlmutter/accounting/sacct_practical_suite_chem_active_6q8q_1node_20260704233824.txt` |
| paper_figures | Main paper figures are valid PDF artifacts for performance, scaling, quality, and frontier analysis | PASS | `paper/figures/intro_application_gap.pdf`<br>`paper/figures/design_overview.pdf`<br>`paper/figures/scaling_summary.pdf`<br>`paper/figures/strong_native_comparison.pdf`<br>`paper/figures/practical_suite_summary.pdf`<br>`paper/figures/digits_required_speedup.pdf`<br>`paper/figures/digits_quality_speedup.pdf`<br>`paper/figures/advantage_frontier.pdf`<br>`paper/figures/salloc_pilot_comparison.pdf`<br>`paper/figures/workload_taxonomy.pdf` |
