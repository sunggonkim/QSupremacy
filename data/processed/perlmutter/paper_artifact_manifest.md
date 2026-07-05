# Paper Artifact Manifest

Updated: 2026-07-05 UTC

This manifest maps the paper's main evidence-backed claims to the scripts,
Slurm jobs, processed files, figures, and automated audit items that support
them. It is meant to make the paper auditable without re-reading every run log.

| Claim id | Paper claim | Primary artifacts | Audit item |
| --- | --- | --- | --- |
| `expanded_digits` | 160-case digits calibration comparing native sklearn ML against quantum kernel and QNN/VQC circuit paths. | `data/processed/perlmutter/digits_expanded_55421321_55422142_summary.json`<br>`data/processed/perlmutter/digits_expanded_55421321_55422142_summary.csv`<br>`paper/figures/digits_required_speedup.pdf`<br>`paper/figures/digits_quality_speedup.pdf` | `expanded_digits` |
| `large_practical_suite` | 3,552-case strong-native practical suite on 32 Perlmutter GPU nodes across ML, chemistry, optimization, and simulation. | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json`<br>`data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv`<br>`data/raw/perlmutter/accounting/sacct_practical_suite_strongnative_32node_large128c0c127_20260704060230.txt` | `large_practical_suite` |
| `advantage_projection` | Projected advantage is reported as a frontier over quantum execution improvement and quality-gap recovery. | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json`<br>`data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.md`<br>`paper/figures/advantage_frontier.pdf` | `advantage_projection` |
| `workload_taxonomy` | The measured bottleneck taxonomy separates speed-limited cases from quality-limited cases by workload family. | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json`<br>`paper/figures/workload_taxonomy.pdf` | `workload_taxonomy` |
| `chemistry_active_space` | OpenFermion/PySCF chemistry active-space coverage gate validates 104 chemistry cases up to 8 qubits. | `data/processed/perlmutter/practical_suite_chem_active_6q8q_1node_20260704233824_chemistry_coverage.json`<br>`data/processed/perlmutter/practical_suite_chem_active_6q8q_1node_20260704233824_chemistry_coverage.md`<br>`data/raw/perlmutter/accounting/sacct_practical_suite_chem_active_6q8q_1node_20260704233824.txt` | `chemistry_active_space` |
| `repeat_timing` | A warmup-separated repeat timing gate checks that representative hardware timings are stable enough for submission. | `data/processed/perlmutter/repeat_timing_gate_latest.json`<br>`data/processed/perlmutter/repeat_timing_gate_latest.md`<br>`jobs/perlmutter/practical_suite_repeat_timing_gate.sbatch` | `submission_readiness.repeated_hardware_trials` |
| `paper_figures` | All generated paper plots are PDF artifacts and are checked by the evidence audit. | `scripts/generate_paper_figures.py`<br>`paper/figures/*.pdf` | `paper_figures` |
| `submission_package` | The paper package builds to an HPCA 2027-style double-blind PDF with references starting on page 12 after an 11-page body, evidence/readiness checks passing, and all-author references. | `paper/main.pdf`<br>`data/processed/perlmutter/paper_evidence_audit.md`<br>`data/processed/perlmutter/submission_readiness_audit.md` | `submission_readiness` |

The machine-readable copy is
`data/processed/perlmutter/paper_artifact_manifest.json`.
