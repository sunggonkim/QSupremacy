# Previous-Paper Alignment Metrics

Status: **ALIGNED_BY_COUNTS**

## Checks

| Check | Status |
| --- | --- |
| previous_sources_available | PASS |
| intro_role_and_size | PASS |
| background_two_subsections | PASS |
| design_scaleqsim_subsection_count | PASS |
| evaluation_previous_shape | PASS |
| role_markers_ordered | PASS |
| paragraph_role_inventory_present | PASS |
| paragraph_role_lines_present | PASS |
| template_role_lines_present | PASS |
| style_fingerprint_no_large_gaps | PASS |

## Section Counts

| Section | Paper | Words | Paragraphs | textbf | Subsections | Subsubsections | Figures | Tables | Items |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| introduction | ours | 975 | 8 | 15 | 0 | 0 | 1 | 1 | 0 |
| introduction | aurora | 1023 | 7 | 7 | 0 | 0 | 1 | 1 | 0 |
| introduction | scaleqsim | 1510 | 10 | 6 | 0 | 0 | 1 | 1 | 0 |
| background | ours | 622 | 8 | 5 | 2 | 0 | 0 | 0 | 0 |
| background | aurora | 746 | 11 | 2 | 2 | 0 | 3 | 0 | 0 |
| background | scaleqsim | 989 | 8 | 2 | 2 | 0 | 1 | 0 | 0 |
| design | ours | 2536 | 36 | 38 | 6 | 4 | 1 | 2 | 0 |
| design | aurora | 3497 | 37 | 33 | 5 | 0 | 3 | 0 | 0 |
| design | scaleqsim | 4581 | 36 | 23 | 6 | 0 | 4 | 0 | 0 |
| evaluation | ours | 3915 | 34 | 17 | 8 | 3 | 7 | 11 | 0 |
| evaluation | aurora | 3666 | 27 | 26 | 5 | 0 | 9 | 2 | 0 |
| evaluation | scaleqsim | 5732 | 47 | 27 | 7 | 0 | 7 | 2 | 0 |
| related | ours | 311 | 4 | 4 | 0 | 0 | 0 | 0 | 0 |
| related | aurora | 317 | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| related | scaleqsim | 512 | 6 | 0 | 2 | 0 | 0 | 0 | 0 |
| conclusion | ours | 87 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| conclusion | aurora | 89 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| conclusion | scaleqsim | 111 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |

## Known Gaps

No large word-count gaps under the current threshold.

## Style Fingerprint

| Section | Paper | Avg paragraph words | textbf / 1000 words | Paragraphs / heading |
| --- | --- | ---: | ---: | ---: |
| introduction | ours | 121.88 | 15.38 | 8.0 |
| introduction | aurora | 146.14 | 6.84 | 7.0 |
| introduction | scaleqsim | 151.0 | 3.97 | 10.0 |
| background | ours | 77.75 | 8.04 | 4.0 |
| background | aurora | 67.82 | 2.68 | 5.5 |
| background | scaleqsim | 123.62 | 2.02 | 4.0 |
| design | ours | 70.44 | 14.98 | 3.6 |
| design | aurora | 94.51 | 9.44 | 7.4 |
| design | scaleqsim | 127.25 | 5.02 | 6.0 |
| evaluation | ours | 115.15 | 4.34 | 3.09 |
| evaluation | aurora | 135.78 | 7.09 | 5.4 |
| evaluation | scaleqsim | 121.96 | 4.71 | 6.71 |
| related | ours | 77.75 | 12.86 | 4.0 |
| related | aurora | 158.5 | 6.31 | 2.0 |
| related | scaleqsim | 85.33 | 0.0 | 3.0 |
| conclusion | ours | 43.5 | 0.0 | 2.0 |
| conclusion | aurora | 89.0 | 0.0 | 1.0 |
| conclusion | scaleqsim | 55.5 | 0.0 | 2.0 |

## Style Gaps

No large style-fingerprint gaps under the current threshold.

## Paragraph Role Inventory

| Section | Order | Current source line | Template source line | Current paragraph role | Previous-paper logic followed |
| --- | ---: | ---: | --- | --- | --- |
| introduction | 1 | 3 | aurora:2 | opening motivation | Broad promise, practical HPC question, hardware limit |
| introduction | 2 | 5 | aurora:12 | prior simulator boundary | Simulation systems help, but simulator speed is not application speed |
| introduction | 3 | 7 | aurora:23 | intro figure | First visual statement of native path versus quantum path |
| introduction | 4 | 15 | aurora:31 | observations | Bold observations before positioning table |
| introduction | 5 | 17 | aurora:45 | application diversity | Why one toy workload cannot support broad quantum claims |
| introduction | 6 | 21 | aurora:47 | positioning table | Early related-work table before final pitch |
| introduction | 7 | 41 | aurora:73 | key idea | Break-even threshold model |
| introduction | 8 | 46 | aurora:77 | paper statement and contributions | System statement followed by contribution list |
| background | 1 | 3 | scaleqsim:2 | application paths | Define quantum-circuit application families |
| background | 2 | 7 | scaleqsim:8 | repeated execution | Explain why one circuit run is not the full application |
| background | 3 | 10 | scaleqsim:11 | practical families | ML, chemistry, optimization, simulation |
| background | 4 | 13 | scaleqsim:16 | terminology | Threshold and advantage-region definitions |
| background | 5 | 16 | scaleqsim:22 | native baselines | Classical target path |
| background | 6 | 20 | aurora:80 | Perlmutter/cuQuantum | Measurement platform |
| background | 7 | 23 | aurora:84 | break-even equations | Native, simulated quantum, projected hardware paths |
| design | 1 | 3 | aurora:3 | overview and boundary | State what the system is and is not |
| design | 2 | 17 | scaleqsim:8 | overall procedure | Measurement then advantage analysis |
| design | 3 | 24 | scaleqsim:18 | configuration record | Stable work representation before execution |
| design | 4 | 30 | scaleqsim:41 | failure handling | Failed paths remain measured evidence |
| design | 5 | 33 | scaleqsim:54 | shared workload control | Same input, instance identity, and quality target |
| design | 6 | 57 | scaleqsim:95 | application paths | Native, kernel, and QNN/VQC execution rules |
| design | 7 | 98 | scaleqsim:140 | measurement records | JSON, summary path, and allocation accounting |
| design | 8 | 109 | scaleqsim:165 | threshold analysis | Execution model, break-even search, and frontier classification |
| design | 9 | 141 | scaleqsim:237 | claim checklist | Systems checks before an advantage claim |
| design | 10 | 167 | scaleqsim:306 | workload suite | Measured application families |
| evaluation | 1 | 5 | aurora:58 | setup | Hardware, benchmark, baselines, feasibility |
| evaluation | 2 | 19 | aurora:9 | campaign summary | Evidence table and evaluation questions |
| evaluation | 3 | 91 | aurora:133 | RQ1 | Native ML versus quantum-circuit ML |
| evaluation | 4 | 129 | scaleqsim:58 | RQ2 | Quality sensitivity |
| evaluation | 5 | 153 | aurora:248 | RQ3 | Practical application suite |
| evaluation | 6 | 187 | scaleqsim:247 | RQ4 | Native baseline stress |
| evaluation | 7 | 247 | aurora:262 | RQ5 | Weak and strong scaling |
| evaluation | 8 | 282 | aurora:334 | RQ6 | Advantage frontier and hardware projection |
| evaluation | 9 | 316 | scaleqsim:413 | stability | Operational and repeat-timing checks |
| evaluation | 10 | 365 | aurora:399 | taxonomy and sensitivity | Bottleneck classes and remaining scope |
| related | 1 | 3 | aurora:3 | simulation and NISQ | Simulation substrate and current-device limits |
| related | 2 | 9 | aurora:6 | applications and baselines | Application families and native comparisons |
| conclusion | 1 | 3 | scaleqsim:8 | paper result | Framework and measured thresholds |
| conclusion | 2 | 5 | scaleqsim:15 | main lesson | Frontier and bottleneck taxonomy instead of slogan |
