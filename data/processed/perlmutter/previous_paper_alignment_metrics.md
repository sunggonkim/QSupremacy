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

## Section Counts

| Section | Paper | Words | Paragraphs | textbf | Subsections | Subsubsections | Figures | Tables | Items |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| introduction | ours | 953 | 8 | 15 | 0 | 0 | 1 | 1 | 0 |
| introduction | aurora | 1023 | 7 | 7 | 0 | 0 | 1 | 1 | 0 |
| introduction | scaleqsim | 1510 | 10 | 6 | 0 | 0 | 1 | 1 | 0 |
| background | ours | 617 | 8 | 5 | 2 | 0 | 0 | 0 | 0 |
| background | aurora | 746 | 11 | 2 | 2 | 0 | 3 | 0 | 0 |
| background | scaleqsim | 989 | 8 | 2 | 2 | 0 | 1 | 0 | 0 |
| design | ours | 2437 | 35 | 37 | 6 | 4 | 1 | 2 | 0 |
| design | aurora | 3497 | 37 | 33 | 5 | 0 | 3 | 0 | 0 |
| design | scaleqsim | 4581 | 36 | 23 | 6 | 0 | 4 | 0 | 0 |
| evaluation | ours | 3818 | 33 | 17 | 8 | 3 | 7 | 11 | 0 |
| evaluation | aurora | 3666 | 27 | 26 | 5 | 0 | 9 | 2 | 0 |
| evaluation | scaleqsim | 5732 | 47 | 27 | 7 | 0 | 7 | 2 | 0 |
| related | ours | 207 | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| related | aurora | 317 | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| related | scaleqsim | 512 | 6 | 0 | 2 | 0 | 0 | 0 | 0 |
| conclusion | ours | 87 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| conclusion | aurora | 89 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| conclusion | scaleqsim | 111 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |

## Known Gaps

No large word-count gaps under the current threshold.

## Paragraph Role Inventory

| Section | Order | Current source line | Current paragraph role | Previous-paper logic followed |
| --- | ---: | ---: | --- | --- |
| introduction | 1 | 3 | opening motivation | Broad promise, practical HPC question, hardware limit |
| introduction | 2 | 5 | prior simulator boundary | Simulation systems help, but simulator speed is not application speed |
| introduction | 3 | 7 | intro figure | First visual statement of native path versus quantum path |
| introduction | 4 | 15 | observations | Bold observations before positioning table |
| introduction | 5 | 17 | application diversity | Why one toy workload cannot support broad quantum claims |
| introduction | 6 | 21 | positioning table | Early related-work table before final pitch |
| introduction | 7 | 41 | key idea | Break-even threshold model |
| introduction | 8 | 46 | paper statement and contributions | System statement followed by contribution list |
| background | 1 | 3 | application paths | Define quantum-circuit application families |
| background | 2 | 7 | repeated execution | Explain why one circuit run is not the full application |
| background | 3 | 10 | practical families | ML, chemistry, optimization, simulation |
| background | 4 | 13 | terminology | Threshold and advantage-region definitions |
| background | 5 | 16 | native baselines | Classical target path |
| background | 6 | 20 | Perlmutter/cuQuantum | Measurement platform |
| background | 7 | 23 | break-even equations | Native, simulated quantum, projected hardware paths |
| design | 1 | 3 | overview and boundary | State what the system is and is not |
| design | 2 | 17 | overall procedure | Measurement then supremacy analysis |
| design | 3 | 24 | configuration record | Stable work representation before execution |
| design | 4 | 30 | failure handling | Failed paths remain measured evidence |
| design | 5 | 33 | shared workload control | Same input, instance identity, and quality target |
| design | 6 | 53 | application paths | Native, kernel, and QNN/VQC execution rules |
| design | 7 | 94 | measurement records | JSON, summary path, and allocation accounting |
| design | 8 | 105 | threshold analysis | Execution model, break-even search, and frontier classification |
| design | 9 | 134 | claim checklist | Systems checks before an advantage claim |
| design | 10 | 160 | workload suite | Measured application families |
| evaluation | 1 | 5 | setup | Hardware, benchmark, baselines, feasibility |
| evaluation | 2 | 19 | campaign summary | Evidence table and evaluation questions |
| evaluation | 3 | 91 | RQ1 | Native ML versus quantum-circuit ML |
| evaluation | 4 | 137 | RQ2 | Quality sensitivity |
| evaluation | 5 | 161 | RQ3 | Practical application suite |
| evaluation | 6 | 195 | RQ4 | Native baseline stress |
| evaluation | 7 | 253 | RQ5 | Weak and strong scaling |
| evaluation | 8 | 288 | RQ6 | Advantage frontier and hardware projection |
| evaluation | 9 | 322 | stability | Operational and repeat-timing checks |
| evaluation | 10 | 371 | taxonomy and sensitivity | Bottleneck classes and remaining scope |
| related | 1 | 3 | simulation and NISQ | Simulation substrate and current-device limits |
| related | 2 | 6 | applications and baselines | Application families and native comparisons |
| conclusion | 1 | 3 | paper result | Framework and measured thresholds |
| conclusion | 2 | 5 | main lesson | Frontier and bottleneck taxonomy instead of slogan |
