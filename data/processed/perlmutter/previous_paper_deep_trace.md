# Previous-Paper Deep Trace

Overall status: **PASS**

This trace lists every meaningful current manuscript paragraph or structural block, its source line span, the accepted-paper role it follows, and the previous-paper template source line used as the nearest logic anchor. It avoids copying previous-paper prose; markers are used only as short trace anchors.

Total traced blocks: `150`

## Checks

| Check | Status |
| --- | --- |
| previous_sources_available | PASS |
| all_sections_traced | PASS |
| all_current_blocks_have_roles | PASS |
| all_current_blocks_have_template_lines | PASS |
| line_level_trace_present | PASS |
| paragraph_and_structure_kinds_present | PASS |
| style_features_traced | PASS |

## Section Summary

| Section | Current source | Traced blocks | Role anchors |
| --- | --- | ---: | ---: |
| introduction | `paper/1.Introduction.tex` | 11 | 8 |
| background | `paper/2.Background.tex` | 13 | 7 |
| design | `paper/3.Design.tex` | 52 | 10 |
| evaluation | `paper/4.Evaluation.tex` | 65 | 10 |
| related | `paper/5.RelatedWork.tex` | 6 | 2 |
| conclusion | `paper/6.Conclusion.tex` | 3 | 2 |

## Line-by-Line Trace

| Section | # | Lines | Kind | Current lead | Followed role | Template anchor |
| --- | ---: | --- | --- | --- | --- | --- |
| introduction | 1 | 1-1 | section | Introduction | opening motivation | aurora:2 `Quantum computing offers` |
| introduction | 2 | 3-3 | paragraph | Quantum computing is often described through broad application promises: better machine learn... | opening motivation | aurora:2 `Quantum computing offers` |
| introduction | 3 | 5-5 | paragraph | Existing simulation systems provide the first part of this stack. Libraries such as execute | prior simulator boundary | aurora:12 `To overcome these limitations` |
| introduction | 4 | 7-13 | figure | Application-level comparison target. The key comparison is not simulator versus simulator. Th... | intro figure | aurora:23 `\begin{figure}` |
| introduction | 5 | 15-15 | paragraph | Observation 1: Simulator speed is not application speed. | observations | aurora:31 `Figure~\ref{intro_fig} shows` |
| introduction | 6 | 17-17 | paragraph | The same issue becomes stronger when the workload moves beyond one small ML example. | application diversity | aurora:45 `Many previous studies` |
| introduction | 7 | 19-19 | paragraph | Many previous studies focus on one part of this stack. Table~tab:intro-position summarizes th... | application diversity | aurora:45 `Many previous studies` |
| introduction | 8 | 21-40 | table | Study/System | positioning table | aurora:47 `\begin{table}` |
| introduction | 9 | 42-43 | paragraph | Key Idea. | key idea | aurora:73 `\AURORA distinguishes itself` |
| introduction | 10 | 45-45 | paragraph | We present , a quantum-advantage modeling and analysis study for HPC systems. starts with | key idea | aurora:73 `\AURORA distinguishes itself` |
| introduction | 11 | 47-54 | paragraph | End-to-end threshold model. | paper statement and contributions | aurora:77 `In this paper, we propose` |
| background | 1 | 1-1 | section | Background | application paths | scaleqsim:2 `\subsection{Quantum Circuit Simulation}` |
| background | 2 | 3-3 | subsection | Quantum-Circuit Application Paths | application paths | scaleqsim:2 `\subsection{Quantum Circuit Simulation}` |
| background | 3 | 5-5 | paragraph | Quantum-circuit applications map input data or problem instances into a sequence of quantum g... | application paths | scaleqsim:2 `\subsection{Quantum Circuit Simulation}` |
| background | 4 | 7-8 | paragraph | Repeated Execution. | repeated execution | scaleqsim:8 `Amplitude sampling simulation` |
| background | 5 | 10-11 | paragraph | Practical Application Families. | practical families | scaleqsim:11 `Full state vector simulation` |
| background | 6 | 13-14 | paragraph | Terminology. | terminology | scaleqsim:16 `Since full state vector simulation` |
| background | 7 | 16-16 | subsection | Native Baselines and Threshold Model | native baselines | scaleqsim:22 `\subsection{Distributed Architecture` |
| background | 8 | 18-18 | paragraph | Native HPC/ML baselines execute the same task directly on CPUs or GPUs. For the | native baselines | scaleqsim:22 `\subsection{Distributed Architecture` |
| background | 9 | 20-21 | paragraph | Perlmutter and cuQuantum. | Perlmutter/cuQuantum | aurora:80 `\subsection{Hardware Constraints` |
| background | 10 | 23-24 | paragraph | Break-even Condition. | break-even equations | aurora:84 `Bandwidth Gap and Execution Time` |
| background | 11 | 26-31 | paragraph | align T_ native =& T_ input + T_ preprocess &+ T_ train + T_ | break-even equations | aurora:84 `Bandwidth Gap and Execution Time` |
| background | 12 | 35-41 | paragraph | align T_ qc _sim =& T_ input + T_ encoding + T_ circuit &+ | break-even equations | aurora:84 `Bandwidth Gap and Execution Time` |
| background | 13 | 45-51 | paragraph | align T_ qhw =& T_ input + T_ encoding + T_ compile &+ T_ | break-even equations | aurora:84 `Bandwidth Gap and Execution Time` |
| design | 1 | 1-1 | section | \SystemName Design | overview and boundary | aurora:3 `Overview of \AURORA` |
| design | 2 | 3-4 | paragraph | Overview of \SystemName's Design. | overview and boundary | aurora:3 `Overview of \AURORA` |
| design | 3 | 6-7 | paragraph | Design Boundary. | overview and boundary | aurora:3 `Overview of \AURORA` |
| design | 4 | 9-15 | figure | Architecture and procedure of \SystemName. | overview and boundary | aurora:3 `Overview of \AURORA` |
| design | 5 | 17-17 | subsection | Overall Procedure | overall procedure | scaleqsim:8 `\subsection{Overall Procedure}` |
| design | 6 | 19-19 | paragraph | Figure~fig:design-overview shows the overall procedure. has two main phases: Measurement and ... | overall procedure | scaleqsim:8 `\subsection{Overall Procedure}` |
| design | 7 | 21-22 | paragraph | Measurement. | overall procedure | scaleqsim:8 `\subsection{Overall Procedure}` |
| design | 8 | 24-25 | paragraph | Config Record. | configuration record | scaleqsim:18 `Initialization.` |
| design | 9 | 27-28 | paragraph | Advantage Analysis. | configuration record | scaleqsim:18 `Initialization.` |
| design | 10 | 30-31 | paragraph | Failure Handling. | failure handling | scaleqsim:41 `Execution.` |
| design | 11 | 33-33 | subsection | Shared Workload Control | shared workload control | scaleqsim:54 `Two-phase State Space Partitioning` |
| design | 12 | 35-36 | paragraph | Dataset Control. | shared workload control | scaleqsim:54 `Two-phase State Space Partitioning` |
| design | 13 | 38-39 | paragraph | Instance Identity. | shared workload control | scaleqsim:54 `Two-phase State Space Partitioning` |
| design | 14 | 41-42 | paragraph | Application Control. | shared workload control | scaleqsim:54 `Two-phase State Space Partitioning` |
| design | 15 | 44-45 | paragraph | Quality Control. | shared workload control | scaleqsim:54 `Two-phase State Space Partitioning` |
| design | 16 | 47-52 | equation | Quality Normalization. | shared workload control | scaleqsim:54 `Two-phase State Space Partitioning` |
| design | 17 | 54-55 | paragraph | Why This Matters. | shared workload control | scaleqsim:54 `Two-phase State Space Partitioning` |
| design | 18 | 57-57 | subsection | Application Path Execution | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 19 | 59-59 | subsubsection | Native Path Execution | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 20 | 61-62 | paragraph | Classical Baselines. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 21 | 64-65 | paragraph | Runtime Breakdown. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 22 | 67-68 | paragraph | Baseline Selection Rule. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 23 | 70-70 | subsubsection | Quantum Kernel Path | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 24 | 72-73 | paragraph | Feature Map Execution. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 25 | 75-76 | paragraph | Cost Breakdown. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 26 | 78-79 | paragraph | Expected Bottleneck. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 27 | 81-82 | paragraph | Kernel Accounting Rule. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 28 | 84-84 | subsubsection | QNN/VQC Path | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 29 | 86-87 | paragraph | Parameterized Circuit Execution. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 30 | 89-90 | paragraph | Cost Breakdown. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 31 | 92-93 | paragraph | Why This Matters. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 32 | 95-96 | paragraph | Optimizer Rule. | application paths | scaleqsim:95 `Task-based Qubit State Management` |
| design | 33 | 98-98 | subsection | Measurement and Threshold Analysis | measurement records | scaleqsim:140 `Manage statespace structure` |
| design | 34 | 100-101 | paragraph | JSON Record. | measurement records | scaleqsim:140 `Manage statespace structure` |
| design | 35 | 103-104 | paragraph | Summary Path. | measurement records | scaleqsim:140 `Manage statespace structure` |
| design | 36 | 106-107 | paragraph | Allocation Accounting. | measurement records | scaleqsim:140 `Manage statespace structure` |
| design | 37 | 109-109 | subsubsection | Threshold Analysis | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 38 | 111-112 | paragraph | Execution Model. | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 39 | 114-119 | paragraph | align T_ execute = N_s(D_1t_1 + D_2t_2 + D_mt_m) P_ shots + T_ error | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 40 | 121-121 | paragraph | where N_s is the shot count, D_1 and D_2 are one- and two-qubit gate | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 41 | 123-124 | paragraph | Projection Scope. | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 42 | 126-129 | paragraph | Worked Hardware Instantiation. | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 43 | 131-132 | paragraph | Break-even Search. | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 44 | 138-138 | paragraph | This gives a hardware requirement rather than a vague claim of advantage. | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 45 | 140-141 | paragraph | Advantage Frontier. | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 46 | 143-144 | paragraph | Frontier Classification. | threshold analysis | scaleqsim:165 `Two-phase Mapping and Kernel Execution` |
| design | 47 | 146-146 | subsection | Advantage Claim Checklist | claim checklist | scaleqsim:237 `Adaptive Kernel Parameter Adjustment` |
| design | 48 | 148-148 | paragraph | A practical quantum-advantage claim should pass a small set of systems checks before it | claim checklist | scaleqsim:237 `Adaptive Kernel Parameter Adjustment` |
| design | 49 | 150-170 | table | Check | claim checklist | scaleqsim:237 `Adaptive Kernel Parameter Adjustment` |
| design | 50 | 172-172 | subsection | Workload Suite | workload suite | scaleqsim:306 `\ScaleQsim Implementation` |
| design | 51 | 174-174 | paragraph | Table~tab:workload-suite shows the measured workload suite. The digits workload is the contro... | workload suite | scaleqsim:306 `\ScaleQsim Implementation` |
| design | 52 | 176-193 | table | Family | workload suite | scaleqsim:306 `\ScaleQsim Implementation` |
| evaluation | 1 | 1-1 | section | Evaluation | setup | aurora:58 `\subsection{Evaluation Setup}` |
| evaluation | 2 | 3-3 | paragraph | This section evaluates in the same style as a systems performance paper: first the | setup | aurora:58 `\subsection{Evaluation Setup}` |
| evaluation | 3 | 5-5 | subsection | Evaluation Setup | setup | aurora:58 `\subsection{Evaluation Setup}` |
| evaluation | 4 | 7-8 | paragraph | Hardware Specification. | setup | aurora:58 `\subsection{Evaluation Setup}` |
| evaluation | 5 | 10-11 | paragraph | Benchmark. | setup | aurora:58 `\subsection{Evaluation Setup}` |
| evaluation | 6 | 13-14 | paragraph | Baselines. | setup | aurora:58 `\subsection{Evaluation Setup}` |
| evaluation | 7 | 16-17 | paragraph | Feasibility. | setup | aurora:58 `\subsection{Evaluation Setup}` |
| evaluation | 8 | 19-20 | paragraph | Campaign Summary. | campaign summary | aurora:9 `\begin{table}` |
| evaluation | 9 | 22-43 | table | Completed Perlmutter evidence campaign. | campaign summary | aurora:9 `\begin{table}` |
| evaluation | 10 | 45-66 | table | Measured setup for the expanded digits sweep. | campaign summary | aurora:9 `\begin{table}` |
| evaluation | 11 | 68-69 | paragraph | Evaluation Questions. | campaign summary | aurora:9 `\begin{table}` |
| evaluation | 12 | 71-91 | table | Evaluation roadmap. | campaign summary | aurora:9 `\begin{table}` |
| evaluation | 13 | 93-93 | subsection | RQ1: Native ML versus Quantum-Circuit ML | RQ1 | aurora:133 `\subsection{Performance with SOTA}` |
| evaluation | 14 | 95-95 | paragraph | Table~tab:expanded-summary summarizes the expanded sweep. Native ML remains strong across the... | RQ1 | aurora:133 `\subsection{Performance with SOTA}` |
| evaluation | 15 | 97-113 | table | Expanded digits sweep summary over 160 cases. | RQ1 | aurora:133 `\subsection{Performance with SOTA}` |
| evaluation | 16 | 115-116 | paragraph | Answer. | RQ1 | aurora:133 `\subsection{Performance with SOTA}` |
| evaluation | 17 | 118-119 | paragraph | Qubit Accounting. | RQ1 | aurora:133 `\subsection{Performance with SOTA}` |
| evaluation | 18 | 121-139 | figure | Threshold distribution. | RQ1 | aurora:133 `\subsection{Performance with SOTA}` |
| evaluation | 19 | 141-141 | subsection | RQ2: Quality Sensitivity | RQ2 | scaleqsim:58 `Comparison with \textit{Qsim}` |
| evaluation | 20 | 143-143 | paragraph | Table~tab:class-sensitivity shows that the threshold depends on the data pair. The easy pair,... | RQ2 | scaleqsim:58 `Comparison with \textit{Qsim}` |
| evaluation | 21 | 145-160 | table | Class-pair sensitivity. Values are medians. | RQ2 | scaleqsim:58 `Comparison with \textit{Qsim}` |
| evaluation | 22 | 162-163 | paragraph | Answer. | RQ2 | scaleqsim:58 `Comparison with \textit{Qsim}` |
| evaluation | 23 | 165-165 | subsection | RQ3: Practical Application Suite | RQ3 | aurora:248 `Various Circuits.` |
| evaluation | 24 | 167-167 | paragraph | The digits workload is useful because it is controlled, cheap, and easy to repeat. | RQ3 | aurora:248 `Various Circuits.` |
| evaluation | 25 | 169-169 | paragraph | also evaluates a practical suite beyond the controlled binary digits sweep. The suite covers | RQ3 | aurora:248 `Various Circuits.` |
| evaluation | 26 | 171-186 | table | Large practical suite summary over 3,552 cases. Values are medians. | RQ3 | aurora:248 `Various Circuits.` |
| evaluation | 27 | 188-194 | figure | Large practical suite over 3,552 cases. Each bar compares the selected native HPC-style basel... | RQ3 | aurora:248 `Various Circuits.` |
| evaluation | 28 | 196-197 | paragraph | Answer. | RQ3 | aurora:248 `Various Circuits.` |
| evaluation | 29 | 199-199 | subsection | RQ4: Native Baseline Stress Test | RQ4 | scaleqsim:247 `Performance and Scalability in Diverse` |
| evaluation | 30 | 201-207 | figure | Native baseline stress test. Strengthening the native side makes the ML threshold 6.6$\times$... | RQ4 | scaleqsim:247 `Performance and Scalability in Diverse` |
| evaluation | 31 | 209-210 | paragraph | Answer. | RQ4 | scaleqsim:247 `Performance and Scalability in Diverse` |
| evaluation | 32 | 212-213 | paragraph | Baseline Coverage Gate. | RQ4 | scaleqsim:247 `Performance and Scalability in Diverse` |
| evaluation | 33 | 215-230 | table | Accept-profile baseline-coverage gate on one \Perlmutter GPU node. | RQ4 | scaleqsim:247 `Performance and Scalability in Diverse` |
| evaluation | 34 | 232-233 | paragraph | Answer. | RQ4 | scaleqsim:247 `Performance and Scalability in Diverse` |
| evaluation | 35 | 235-236 | paragraph | Chemistry Active-space Coverage. | RQ4 | scaleqsim:247 `Performance and Scalability in Diverse` |
| evaluation | 36 | 238-255 | table | OpenFermion and PySCF chemistry active-space coverage gate. | RQ4 | scaleqsim:247 `Performance and Scalability in Diverse` |
| evaluation | 37 | 257-257 | paragraph | The last column is a tolerance-scaled error gap, not a probability or bounded accuracy | RQ4 | scaleqsim:247 `Performance and Scalability in Diverse` |
| evaluation | 38 | 259-259 | subsection | RQ5: Perlmutter Weak and Strong Scaling | RQ5 | aurora:262 `\subsection{Scalability with SOTA}` |
| evaluation | 39 | 261-261 | paragraph | The large-profile suite contains 3,552 application cases. We evaluate two scaling modes. In weak | RQ5 | aurora:262 `\subsection{Scalability with SOTA}` |
| evaluation | 40 | 263-281 | table | Large-profile weak and fixed-work scaling on \Perlmutter. | RQ5 | aurora:262 `\subsection{Scalability with SOTA}` |
| evaluation | 41 | 283-289 | figure | Large-profile scaling. Weak scaling keeps per-GPU work nearly fixed and increases total throu... | RQ5 | aurora:262 `\subsection{Scalability with SOTA}` |
| evaluation | 42 | 291-292 | paragraph | Answer. | RQ5 | aurora:262 `\subsection{Scalability with SOTA}` |
| evaluation | 43 | 294-294 | subsection | RQ6: Advantage Frontier and Hardware Projection | RQ6 | aurora:334 `Strong Scalability.` |
| evaluation | 44 | 296-296 | paragraph | The practical-suite result gives one speed threshold per case, but a speed-only threshold is | RQ6 | aurora:334 `Strong Scalability.` |
| evaluation | 45 | 298-304 | figure | Advantage frontier over projected quantum speedup and quality-gap recovery. Color shows the f... | RQ6 | aurora:334 `Strong Scalability.` |
| evaluation | 46 | 306-307 | paragraph | Answer. | RQ6 | aurora:334 `Strong Scalability.` |
| evaluation | 47 | 309-310 | paragraph | Tolerance Sensitivity. | RQ6 | aurora:334 `Strong Scalability.` |
| evaluation | 48 | 312-329 | table | Projected advantage fraction from the 3,552-case strong-native suite. | RQ6 | aurora:334 `Strong Scalability.` |
| evaluation | 49 | 331-331 | subsection | Operational Stability | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 50 | 333-333 | paragraph | The official practical sweep was first run as multiple shared-GPU jobs. We then validated | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 51 | 335-350 | table | table[t] Bundled salloc pilot over 96 cases. Values are medians. tabular lccc Workload & | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 52 | 352-358 | figure | figure[t] figures/salloc_pilot_comparison.pdf Comparison of median required speedups between ... | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 53 | 360-360 | paragraph | The pilot completed in 6 minutes and 54 seconds with 96 raw JSON outputs | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 54 | 362-363 | paragraph | Timing Gate. | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 55 | 365-365 | subsubsection | Hardware Projection Model | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 56 | 367-373 | equation | The projection model uses the measured native runtime, measured quantum-circuit simulation ru... | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 57 | 375-375 | paragraph | Table~tab:projection-fractions turns the frontier into concrete hardware targets. Simulation ... | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 58 | 377-378 | paragraph | Answer. | stability | scaleqsim:413 `Performance Variability and Stability` |
| evaluation | 59 | 380-380 | subsubsection | Bottleneck Taxonomy | taxonomy and sensitivity | aurora:399 `\subsection{Sensitivity Analysis}` |
| evaluation | 60 | 382-382 | paragraph | The main evaluation output is not that the simulator is slow. The simulator is | taxonomy and sensitivity | aurora:399 `\subsection{Sensitivity Analysis}` |
| evaluation | 61 | 384-390 | figure | Primary bottleneck taxonomy for the strong-native practical suite. ML and optimization are qu... | taxonomy and sensitivity | aurora:399 `\subsection{Sensitivity Analysis}` |
| evaluation | 62 | 392-392 | paragraph | Figure~fig:workload-taxonomy shows this classification for the 3,552-case large run using the... | taxonomy and sensitivity | aurora:399 `\subsection{Sensitivity Analysis}` |
| evaluation | 63 | 394-394 | paragraph | This classification is the practical insight. If a workload is speed-limited, faster logical ... | taxonomy and sensitivity | aurora:399 `\subsection{Sensitivity Analysis}` |
| evaluation | 64 | 396-396 | subsubsection | Sensitivity Scope | taxonomy and sensitivity | aurora:399 `\subsection{Sensitivity Analysis}` |
| evaluation | 65 | 398-398 | paragraph | The expanded digits sweep covers class pair, sample count, PCA dimension, circuit depth, and | taxonomy and sensitivity | aurora:399 `\subsection{Sensitivity Analysis}` |
| related | 1 | 1-1 | section | Related Work | simulation and NISQ | aurora:3 `Quantum Simulation Beyond Memory Limits` |
| related | 2 | 3-4 | paragraph | Quantum Simulation and NISQ Systems. | simulation and NISQ | aurora:3 `Quantum Simulation Beyond Memory Limits` |
| related | 3 | 6-7 | paragraph | Benchmark Suites and Application Evaluators. | simulation and NISQ | aurora:3 `Quantum Simulation Beyond Memory Limits` |
| related | 4 | 9-10 | paragraph | Quantum Applications and Native Baselines. | applications and baselines | aurora:6 `Memory and I/O Optimization in HPC Systems` |
| related | 5 | 12-13 | paragraph | Fault Tolerance and Hardware Realism. | applications and baselines | aurora:6 `Memory and I/O Optimization in HPC Systems` |
| related | 6 | 15-16 | paragraph | Hybrid Orchestration and QHPC Scheduling. | applications and baselines | aurora:6 `Memory and I/O Optimization in HPC Systems` |
| conclusion | 1 | 1-1 | section | Conclusion | paper result | scaleqsim:8 `In this paper` |
| conclusion | 2 | 3-3 | paragraph | In this paper, we present , a Perlmutter-based measurement and modeling framework for practical | paper result | scaleqsim:8 `In this paper` |
| conclusion | 3 | 5-5 | paragraph | The main lesson is that no single quantum-speedup number is meaningful across applications. With | main lesson | scaleqsim:15 `Our evaluations across` |
