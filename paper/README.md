# Paper

Target: HPCA-style architecture-guided practical quantum-advantage modeling and
analysis paper. The submitted display system name is QArchGauge.

The canonical manuscript is `paper/0.Main.tex` with numbered section files;
`paper/main.tex` is a compatibility wrapper. The Makefile tracks every TeX
section and generated PDF figure, so a normal `make -C paper` cannot silently
reuse a PDF older than an included source. The built PDF is `paper/main.pdf`.

## Build

```bash
make -B -C paper
```

The current substantive build produces `paper/main.pdf`, passes the evidence,
argument-role, style, and submission-readiness checks, and begins references
later on page 11 within the 11-page body limit. The PDF has 14 total pages,
including the required post-reference AI-use appendix. The title-page
submission number remains `NaN`
until HotCRP assigns the real paper number.

The current evaluation includes the completed regular 16/32/64-node weak-scaling
ladder, a completed split-equivalent 1-GPU fixed-work anchor, and direct
7,104-case fixed-work runs on 32, 64, 128, and 256 GPUs. The 1-GPU point sums
32 completed one-GPU chunks and is not reported as a single-allocation wall
clock. The paper's 3,552-case analysis corpus uses four repeat rounds; the
7,104-record scaling-only corpus extends the same grid to eight independently
shifted seed rounds and never enters the QPU projection. Direct 4/8/16-GPU
fixed-work jobs are submitted as 55816730, 55816731,
and 55816732. A no-GPU preflight confirms 7,104 templates and balanced
1,776/888/444 cases per GPU; those markers should be added only after the jobs
complete and aggregate cleanly.

The manuscript now separates three claim levels: measured same-input evidence,
projected lower-bound architecture targets, and deployment-scale claims. Current
figures provide the first two levels. A deployment-scale claim requires an
additional hardware-specific PPA/noise/tail-latency/large-native-baseline proxy
gate and is not inferred from the exact small state-vector runs.
The native baseline is also a moving frontier: deployment-facing ML records must
consider batched GPU-native CNN/ResNet or boosted-tree baselines, optimization
records must consider tuned MILP/CP-SAT/metaheuristics, and chemistry/simulation
records must consider DMRG, tensor-network, AFQMC/projector-QMC, CCSD(T)-class,
and domain Krylov/tensor proxies. The current exact records are audit points
unless those stronger native deadlines are attached.
Executed checks currently cover PyTorch AMP/XGBoost for ML, dense versus sparse
Lanczos for Chem, exact/greedy/local-search/annealing for Opt., and dense versus
sparse Krylov for Sim. Opt. also includes 18 same-input weighted MaxCut native
proxies at 50/75/100 nodes with SciPy HiGHS MILP, 16-restart local search, and
simulated annealing. This is a stronger native-frontier proxy, not a matched
large-QAOA state-vector run. A validated single-layer analytical QAOA proxy now
adds same-input 50--100-qubit expected quality and circuit metadata: median
expected/native objective ratio 0.822 and 115--1,292 logical ZZ gates. Chem
additionally measures all-electron PySCF CCSD(T) proxies up to 92 AO basis
functions, and Sim measures 16/18/20-qubit matrix-free Krylov evolution.
These are stronger native deadlines, not matched large VQE/Trotter runs. The
manuscript labels the remaining domain-scale comparators as open rather than
treating citations or roofline bounds as runs.
Direct QAOA closure is separate from that analytical deployment proxy: 50
records optimize three 10/14/18-qubit seeds plus one 20-qubit cap from $p=1$
through 5, attach finite-shot resampling, and compile all-to-all/grid/line
routing. Across the three-seed sizes, median approximation ratio rises from
0.785 to 0.938 while median all-to-all 2Q work rises from 28 to 140 gates.
The ML native frontier additionally includes completed job 55820861: CIFAR-10
ResNet-18 AMP/TF32 on one A100 with 50,000 training images, 10,000 test images,
56.5 seconds measured runtime, and 81.85% best test accuracy. Completed job
55821879 supplies the same-split quantum-feature comparison: a 12-qubit
direct-upload circuit plus ridge head reaches 33.60% accuracy in 115.16 seconds
of measured compute. This is a matched feature application, not end-to-end QNN
training. Its 60,000 direct uploads exclude a separate 245.7-million-rotation
generic state-preparation upper contract; 3,072-qubit direct angle encoding is
the complementary width bound. Chemistry proxies similarly include 48--88 spin-orbital qubits,
Pauli upper contracts, and UCCSD excitation counts without claiming large VQE
energy quality.

The projection scripts treat recorded 1Q/2Q/measurement fields as
application-total demands across circuit evaluations. Decode,
payload-dependent host-I/O, and analytical queue-tail terms remain per-evaluation
serial terms. `scripts/hpca_projection_model.py` is the shared executable model
used by the projection summary and figure generation; it includes roofline
native hooks with Tensor Core peak and HBM bandwidth limits, a
`native_deadline_sec()` gate that uses the stricter of measured
and roofline-native time when proxy FLOPs/bytes are present, payload/bandwidth
movement, queue-tail latency, decoder-bandwidth limits, controller
replacement hooks, a dependency-ready shot-lane cap, an ideal-overlap to
full-serialization bracket, and energy-to-solution estimates. Noise feedback is
retained only as an unapplied diagnostic stress; quality can change only through
a measured deeper/richer circuit record, never a free runtime multiplier. The
Design section states this critical-path contract, and
`scripts/hpca_projection_model_outline.cpp` mirrors the accounting hooks as a
C++ skeleton rather than a claimed cycle-accurate QPU. This keeps the projected
hardware model from multiplying the same circuit-evaluation work twice while
making the HPCA-specific replacement points explicit.
`scripts/audit_projection_invariants.py` checks all 3,552 controlled records
for conserved component accounting, both overlap endpoints, serialization
monotonicity, total-shot identity, monotone shot/measurement-group and queue
behavior, dependency-ready lane saturation, stronger-native deadlines, and
feedback-batch identity/monotonicity. It runs under `make -C paper audit`.
An independent Microsoft QDK/Qiskit cross-check is reproducible with
`requirements-qre.txt` and
`scripts/run_qdk_resource_estimator_crosscheck.py`; it prices one matched QAOA
circuit under two built-in FT models and intentionally excludes repeated shots,
parameter search, host/control tails, and application-quality recovery.
`scripts/run_qdk_depth_resource_estimator_crosscheck.py` additionally prices all
50 directly optimized 10/14/18/20-qubit, $p=1$--5 records and exposes the
measured-depth code-distance transitions.
Google Qualtran 0.7.0 supplies a second independent cross-check through
`requirements-qualtran.txt` and
`scripts/run_qualtran_resource_estimator_crosscheck.py`. It consumes the same
QDK logical rotation/measurement counts and reports Gidney--Fowler and
Beverland surface-code costs, making estimator spread visible instead of
treating one tool as ground truth.
The near-QPU mechanism ablation is reproduced by
`scripts/summarize_feedback_aggregator_ablation.py`. It uses all 3,552 measured
records and batches only host-I/O, analytical queue-tail, and host-context rounds while
preserving gate, decoder, controller, native, and quality costs. The sweep sets
$N_i=N_e$ and is therefore a maximum available-independence envelope; serial
dependency width is not measured and falls back to $B=1$ in the design. Its
output is `feedback_aggregator_ablation.json`, not measured RTL performance.
The companion `scripts/feedback_aggregator_reference.py` is an executable
event-driven correctness model. Directed and deterministic randomized traces
check collision isolation and conservation, expected-count mismatch/overfill, one update
per bank per cycle, backpressure, accepted-update retention, predecessor
acknowledgement, and the `B=1` identity. An exhaustive schedule cross-check
matches the analytical host-round equation over 65 independent counts, 17
serial counts, and seven batch sizes. Its audit output is
`feedback_aggregator_reference_audit.json`; it is not an RTL timing, area, or
power result.
The roofline-native stress artifact (`roofline_native_stress.json/csv`) now
exercises the native-deadline hook with an A100 Tensor Core/HBM proxy and a 10us launch
floor, so the manuscript can show how favorable projections move when the native
deadline is tightened.
The controlled Chem recovery artifact
(`chem_active_space_pair_ucc_closure.json`) comes from completed CPU job
55845034. It keeps one H$_8$ geometry, expands nested 4/8/12/16-qubit active
spaces, evaluates exact CASCI/FCI and one/two-repetition pair-UCC, groups Pauli
measurements, and compiles all-to-all/grid/line routing. Only 4 qubits close the
0.01-Ha target; QWC groups grow from 5 to 850. The derived
`chem_vqe_quality_cost_proxy.json` drives the paper panel but does not claim the
still-open 120/184-qubit molecular VQE energy result.
The physical DSE uses
`chem_controlled_compiled_measurement_records.json` for exact same-input
2/4-qubit H$_2$/chain QWC schedules and shot-weighted compiled work.
`chem_compiled_measurement_records.json` separately carries the 6/8-qubit
LiH/H$_2$O group/routing stress; its dense-entangler variants do not inherit
measured quality.
The native-rotation artifact (`native_rotation_platform_envelopes.json`)
re-prices the 3,552 records with cited neutral-atom and QCCD/TILT timing
envelopes. It is an optimistic execution-only lower bound and does not transfer
fault-tolerance guarantees or replace a full shuttling schedule.
The review-risk traceability gate is part of both the evidence audit and the
submission-readiness audit; if native-frontier, small-qubit, projection
physicality, queue/control, architecture-mechanism, or quality-recovery boundary
text is removed, readiness becomes blocked.

## Artifact Quickstart

Run from the repository root:

The `figures` target delegates to `scripts/regenerate_paper_artifacts.sh`, which
rebuilds processed summaries and all main-paper plots in dependency order.

```bash
source /etc/profile.d/zzz-lmod.sh
module load python/3.11-24.1.0
python -m pip install -r requirements-figures.txt
python -m pip install -r requirements-qre.txt
PYTHON=python make -C paper figures
make -B -C paper audit
```

Expected state:

```text
paper/main.pdf builds
the manuscript occupies pages 1--11 and references begin on page 12
LaTeX has no undefined references/citations or overfull boxes
paper evidence audit PASS
previous-paper style and deep-trace audits PASS
previous-paper argument-role alignment PASS
submission readiness is SUBMISSION_READY with zero blocking errors and warnings
```

The PDF readability spot check verifies clean `QArchGauge` extraction, 9pt
subfigure captions, color and grayscale distinction, a readable legend or
direct labels for every visual encoding, Figure 4 as the sole two-column
exception, and all later figures at one-column width. Weak/strong
scaling PDFs remain artifact-only; Evaluation reports the audited direct
32/64/128/256-GPU wall times without treating them as QPU scaling.

For a low-cost environment check:

```bash
scripts/run_login_smoke.sh
```

## Sources

Accepted-paper sources used for structure and style reference are unpacked under
`paper/PreviousPapers/` and are intentionally ignored by git. The paper follows
their section rhythm, RQ-style evaluation structure, `subfigure` usage, compact
table style, shared legend panels, and selective observation boxes without
copying prose.
