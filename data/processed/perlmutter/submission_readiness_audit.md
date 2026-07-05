# Submission Readiness Audit

Status: **SUBMISSION_READY**

Page count: `13`

References start page: `12`

Inferred line spacing: `12.00` pt

| Check | Severity | Status | Detail |
| --- | --- | --- | --- |
| main_pdf_exists | error | PASS | paper/main.pdf exists |
| page_count_known | error | PASS | PDF page count can be read from pdfinfo or the LaTeX log |
| main_pdf_fresh | error | PASS | paper/main.pdf and paper/main.log are newer than paper sources and figures |
| page_count_hpca_body | warning | PASS | references start on page 12; HPCA 2027 allows an 11-page body before references |
| line_spacing_hpca | warning | PASS | LaTeX log implies 12.00pt leading from the HPCA text block |
| latex_no_undefined | error | PASS | LaTeX log has no undefined references or citations |
| latex_no_overfull_hbox | warning | PASS | LaTeX log has no overfull hbox warnings |
| latex_no_lmod_noise | warning | PASS | LaTeX log has no Lmod initialization noise |
| bibtex_no_warnings | error | PASS | BibTeX log has no warnings |
| paper_no_todos | error | PASS | paper sources contain no TODO/TBD/placeholder hits: none |
| evidence_audit_pass | error | PASS | paper evidence audit reports PASS |
| anonymous_submission | warning | PASS | current manuscript uses the HPCA title-page banner and an empty author block for double-blind review |
| paper_source_anonymity | warning | PASS | paper sources and paper README contain no obvious author, institution, local-path, or personal GitHub leaks: none |
| pdf_metadata_anonymity | warning | PASS | PDF metadata contains no obvious author, institution, local-path, or personal GitHub leaks: none |
| target_template_selected | warning | PASS | current manuscript uses the HPCA 2027-compatible IEEEtran two-column layout, margins, column gap, and bibliography style |
| references_list_all_authors | error | PASS | references.bib and main.bbl contain no et al., and others, or \etal shorthand |
| ai_use_appendix | warning | PASS | HPCA 2027 AI-use disclosure appendix is present after references |
| repeated_hardware_trials | warning | PASS | warmup-separated repeat timing gate passed with 12 measured cases and max quantum runtime CV 0.0400 |
| artifact_quickstart_documented | warning | PASS | README files document paper-readiness audits and the allocation-free login smoke gate |
| reviewer_risk_map_documented | warning | PASS | reviewer-risk notes cover expected acceptance risks and are linked from README files |
| line_by_line_response_documented | warning | PASS | line-by-line reviewer response map exists and is linked from README files |
| line_by_line_response_audited | warning | PASS | line-by-line reviewer response coverage is machine-audited and linked |
| reviewer_risk_evidence_paths_valid | warning | PASS | reviewer-risk evidence paths are present and tracked: 22 paths |
| previous_paper_alignment_documented | warning | PASS | previous-paper paragraph and style alignment is documented and linked |
| previous_paper_alignment_metrics | warning | PASS | previous-paper word, paragraph, heading, style, role-marker, paragraph-role, current-line, and template-line metrics are generated and linked |
| previous_paper_completion_audit | warning | PASS | previous-paper completion audit covers logic, line, paragraph, word-count, and style requirements |
