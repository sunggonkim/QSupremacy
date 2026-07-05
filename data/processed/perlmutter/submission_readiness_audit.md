# Submission Readiness Audit

Status: **EVIDENCE_READY_WITH_SUBMISSION_RISKS**

Page count: `12`

| Check | Severity | Status | Detail |
| --- | --- | --- | --- |
| main_pdf_exists | error | PASS | paper/main.pdf exists |
| page_count_known | error | PASS | pdfinfo can read page count |
| page_count_atc_style | warning | PASS | current page count is 12; typical systems submissions need a target-specific page budget |
| latex_no_undefined | error | PASS | LaTeX log has no undefined references or citations |
| bibtex_no_warnings | error | PASS | BibTeX log has no warnings |
| paper_no_todos | error | PASS | paper sources contain no TODO/TBD/placeholder hits: none |
| evidence_audit_pass | error | PASS | paper evidence audit reports PASS |
| anonymous_submission | warning | PASS | current manuscript uses an anonymous Paper ID author block |
| target_template_selected | warning | PASS | current manuscript uses the ATC 2026 recommended ACM SIGPLAN-style acmart template with CCS and keywords |
| repeated_hardware_trials | warning | RISK | explicit warmup-separated repeated hardware trials are not yet measured for every sensitivity point |
