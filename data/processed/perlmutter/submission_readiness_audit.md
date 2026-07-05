# Submission Readiness Audit

Status: **SUBMISSION_READY**

Page count: `12`

| Check | Severity | Status | Detail |
| --- | --- | --- | --- |
| main_pdf_exists | error | PASS | paper/main.pdf exists |
| page_count_known | error | PASS | pdfinfo can read page count |
| main_pdf_fresh | error | PASS | paper/main.pdf and paper/main.log are newer than paper sources and figures |
| page_count_atc_style | warning | PASS | current page count is 12; typical systems submissions need a target-specific page budget |
| latex_no_undefined | error | PASS | LaTeX log has no undefined references or citations |
| latex_no_overfull_hbox | warning | PASS | LaTeX log has no overfull hbox warnings |
| latex_no_lmod_noise | warning | PASS | LaTeX log has no Lmod initialization noise |
| bibtex_no_warnings | error | PASS | BibTeX log has no warnings |
| paper_no_todos | error | PASS | paper sources contain no TODO/TBD/placeholder hits: none |
| evidence_audit_pass | error | PASS | paper evidence audit reports PASS |
| anonymous_submission | warning | PASS | current manuscript uses an anonymous Paper ID author block |
| paper_source_anonymity | warning | PASS | paper sources and paper README contain no obvious author, institution, local-path, or personal GitHub leaks: none |
| target_template_selected | warning | PASS | current manuscript uses the ATC 2026 recommended ACM SIGPLAN-style acmart template with CCS and keywords |
| repeated_hardware_trials | warning | PASS | warmup-separated repeat timing gate passed with 12 measured cases and max quantum runtime CV 0.0400 |
| artifact_quickstart_documented | warning | PASS | README files document paper-readiness audits and the allocation-free login smoke gate |
| reviewer_risk_map_documented | warning | PASS | reviewer-risk notes cover expected acceptance risks and are linked from README files |
| reviewer_risk_evidence_paths_valid | warning | PASS | reviewer-risk evidence paths are present and tracked: 17 paths |
| previous_paper_alignment_documented | warning | PASS | previous-paper paragraph and style alignment is documented and linked |
