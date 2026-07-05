# Previous-Paper Alignment Map

This note tracks how the current manuscript follows the accepted-paper logic in
`paper/PreviousPapers`. It is an internal writing guide, not submitted paper
text. The closest structural template is AURORA-Q for section rhythm and
ScaleQsim for systems-performance evaluation language.

## Section Rhythm

| Current section | Previous-paper role followed | Current implementation |
| --- | --- | --- |
| Abstract | Problem, approach, result in short bold blocks | `paper/0.Main.tex` uses `Problem`, `Approach`, and `Result` blocks with measured numbers. |
| Introduction opening | Motivation, limitation, HPC simulation role | Paragraphs 1--4 move from broad quantum claims to the missing application-level threshold model. |
| Introduction figure | First visual statement of the systems gap | Fig. 1 plays the same role as the ScaleQsim/AURORA intro scalability figures. |
| Introduction observations | Short bold claims before positioning table | Five `Observation` paragraphs separate simulator speed, native baselines, break-even modeling, workload diversity, and advantage frontiers. |
| Introduction positioning table | Related-work table before the final pitch | Table 1 mirrors the previous papers' early comparison table. |
| Introduction close | Key idea, paper statement, contributions | The final paragraphs follow the accepted-paper pattern: distinguish from prior work, present the system, then list contributions. |
| Background | Compact definitions before design | Background defines native path, quantum path, Perlmutter/cuQuantum, and threshold variables before the design section. |
| Design overview | Overview figure plus design boundary | The first design paragraphs follow AURORA's overview-first style and explicitly state what the paper is not. |
| Design body | Bold mechanism paragraphs under subsections | Design uses short `\textbf{}` lead-ins for workload control, native path, quantum path, logging, and threshold analysis. |
| Evaluation setup | Hardware, benchmark, baselines, feasibility | The setup now mirrors AURORA's evaluation opening with explicit bold lead-ins. |
| Evaluation body | RQ-style systems results with answer paragraphs | Each RQ gives evidence first and then a short `Answer` paragraph, matching the accepted papers' claim-after-figure rhythm. |
| Discussion | Threats and artifact map | Discussion turns reviewer risks into explicit validity and artifact-traceability statements. |
| Related work | Short scoped categories | Related work keeps the same compact category style as the previous papers. |
| Conclusion | Short lesson-focused close | Conclusion restates measured thresholds and the main systems insight without adding new claims. |

## Count and Style Checks

| Item | Current paper | Previous-paper target |
| --- | --- | --- |
| Source layout | Numbered section files plus main wrapper | Matches AURORA-Q and ScaleQsim layout. |
| Introduction length | Approximately AURORA-sized | AURORA is the closest target; ScaleQsim is longer because it contains draft notes. |
| Introduction comparison table | Present before the final pitch | Matches both previous papers. |
| Bold lead-in style | Used heavily in design/evaluation | Matches AURORA-Q's paragraph style. |
| Evaluation setup lead-ins | Hardware, Benchmark, Baselines, Feasibility | Matches AURORA-Q's evaluation setup rhythm. |
| Evaluation answer rhythm | RQ evidence followed by `Answer` | Matches prior systems-paper result explanation style. |
| Artifact evidence | Manifest, audits, reviewer-risk notes | Extends prior style with reproducibility evidence for this project. |

## Non-Copying Boundary

The manuscript follows the accepted papers' logic and paragraph roles, but it
does not copy their prose. The content is specific to quantum supremacy
threshold modeling: native HPC baselines, quantum-circuit application paths,
cuQuantum instrumentation, Perlmutter scaling, and advantage frontiers.
