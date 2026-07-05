# Previous-Paper Style Audit

Overall status: **PASS**

This audit checks LaTeX idioms that are not captured by role-count alignment: `textbf` lead-ins, `subfigure` syntax, caption/label order, dense table style, float spacing, and booktabs usage.

| Check | Status | Detail |
| --- | --- | --- |
| previous_sources_available | PASS | missing previous: []; missing current: [] |
| accepted_sources_use_subfigure_style | PASS | previous subfigure environments: 30 |
| current_uses_subcaption_package | PASS | current main preamble uses subcaption package |
| current_uses_subfigure_environment | PASS | current subfigure environments: 2 |
| current_avoids_legacy_subfloat | PASS | current subfloat commands: 0 |
| subfigures_have_caption_and_label | PASS | subfigures=2, captions=2, labels=2 |
| caption_before_label_order | PASS | caption-before-label ratio: 1.00 |
| float_spacing_matches_previous_idiom | PASS | captionsetup=1, float spacing setlengths=3 |
| title_case_noindent_textbf | PASS | lowercase lead-ins: [] |
| dense_table_style_present | PASS | scriptsize=3, arraystretch=3 |
| booktabs_table_style_present | PASS | booktabs rules: 45 |
| evaluation_setup_leadins_title_case | PASS | evaluation setup lead-ins match AURORA-Q title-case rhythm |

## Metrics

| Metric | Current | Previous combined |
| --- | ---: | ---: |
| arraystretch | 3 | 1 |
| booktabs_rules | 45 | 7 |
| caption_before_label_ratio | 1.0 | 0.8888888888888888 |
| caption_setup | 1 | 3 |
| figure | 9 | 24 |
| figure_star | 0 | 5 |
| float_spacing | 3 | 3 |
| hline_rules | 0 | 15 |
| noindent_textbf | 71 | 71 |
| resizebox_column | 9 | 3 |
| scriptsize | 3 | 6 |
| subfigure_environment | 2 | 30 |
| subfigures_with_caption | 2 | 28 |
| subfigures_with_label | 2 | 28 |
| subfloat | 0 | 12 |
| table | 15 | 7 |
| table_star | 0 | 0 |
| textbf | 95 | 168 |
| vspace | 0 | 83 |
