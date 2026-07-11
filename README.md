# QSupremacy

QSupremacy is the repository name. The HPCA manuscript now uses the display
system name **QArchGauge**: an architecture-guided practical quantum-advantage
modeling project evaluated on a Top-20 TOP500 leadership-scale HPC system.
It compares native HPC/ML application paths against quantum-circuit versions of
the same workloads, simulated with cuQuantum and projected to future quantum
hardware.

The paper claim is intentionally not "quantum is faster today." The measured
result is a threshold model: how much faster and more accurate future quantum
systems must become before a workload can beat a strong native path.
The architecture result is the bottleneck label behind that threshold: whether a
future quantum system should prioritize logical gate throughput, shot
parallelism, error/quality recovery, host-control overhead, or algorithmic
quality.

## Current Paper State

The HPCA-style paper is built and evidence-backed.
The current figures follow the previous-paper pattern of compact subfigures with
shared legend panels, and the evaluation uses observation boxes for architecture
bottleneck insights.

| Item | Status |
| --- | --- |
| Manuscript PDF | `paper/main.pdf` builds successfully |
| Body budget | HPCA-ready body; references start on page 12 |
| Main suite | 3,552 cases on 128 GPUs |
| 256-GPU larger-workload gate | 7,104 cases in 576 seconds |
| Regular weak-scaling ladder | 64/128/256 GPUs completed with 1,776 / 3,552 / 7,104 ok cases |
| Regular strong-scaling ladder | Paper uses direct 64/128/256-GPU fixed-work runs with 7,104 ok cases each; 32-GPU direct extension job 55792240 is pending as optional extra evidence |
| ML production-native gate | 32 same-input cases with PyTorch AMP CNN/MLP and XGBoost GPU-hist |
| ML profiling gate | Nsight Systems + dmon captured; Nsight Compute counter failure recorded |
| Workloads | ML, chemistry, optimization, scientific simulation |
| Previous-paper structure audit | PASS via JSON artifacts |
| Previous-paper LaTeX style audit | PASS via JSON artifacts |
| Paper evidence audit | PASS |
| Submission readiness audit | `SUBMISSION_READY`, 0 warnings, 0 blocking errors |
| PDF readability spot check | PASS: `QArchGauge` extracts cleanly; Fig. 5 precedes Fig. 6; rendered contact sheets inspected |

Main 3,552-case medians:

| Workload | Cases | Median required speedup | Median quality gap |
| --- | ---: | ---: | ---: |
| ML / AI | 2,048 | 3,726.4x | 0.3125 |
| Chemistry / drug-discovery proxy | 224 | 42,491.4x | 0.0203 |
| Optimization | 768 | 287,045.6x | 0.2500 |
| Scientific simulation | 512 | 3,071.0x | 0.0188 |

ML production-native gate:

| Item | Result |
| --- | ---: |
| Cases | 32 |
| Previous selected-native median threshold | 8,876.8x |
| Combined selected-native median threshold | 8,601.6x |
| Production-only median threshold | 49.3x |
| Combined selections | 24 previous suite, 8 PyTorch AMP CNN |
| Production selections | 25 PyTorch AMP CNN, 5 XGBoost GPU-hist, 2 PyTorch AMP MLP |
| Profiled GPU-kernel fraction | 0.8% |
| Profiled host-orchestration fraction | 99.2% |

## Paper Readiness Quickstart

Run from the repository root:

```bash
make -B -C paper
python3 scripts/audit_previous_paper_alignment.py
python3 scripts/audit_previous_paper_deep_trace.py
python3 scripts/audit_previous_paper_style.py
python3 scripts/audit_paper_evidence.py
python3 scripts/audit_submission_readiness.py
```

Expected result:

```text
previous-paper alignment: TRACKED_WITH_KNOWN_GAPS only for a non-blocking Design word-count note; all alignment checks PASS
previous-paper deep trace: PASS
previous-paper style audit: PASS
paper evidence audit: PASS
submission readiness: SUBMISSION_READY, warning_count 0, references_start_page 12
```

For allocation-free sanity checks:

```bash
scripts/run_login_smoke.sh
```

For the reviewer-response scale ladder, first run the allocation-free preflight:

```bash
QS_PREFLIGHT_ONLY=1 QS_SWEEP_PROFILE=scale_ladder_debug QS_CHUNK_COUNT=1 QS_CHUNK_ID=0 QS_WORKLOAD_FAMILIES=all bash jobs/perlmutter/practical_suite_sweep_1gpu_shared.sbatch
```

Then submit the 1-node/4-GPU debug ladder only after deciding to spend
allocation:

```bash
QS_SWEEP_PROFILE=scale_ladder_debug QS_SCALE_MODE=weak QS_CHUNK_COUNT=4 sbatch -q debug -t 00:30:00 -N 1 jobs/perlmutter/practical_suite_scale_nodes.sbatch
```

The completed regular scaling ladder used the large profile:

```bash
# Weak scaling: 1,776 / 3,552 / 7,104 cases on 64 / 128 / 256 GPUs.
QS_SWEEP_PROFILE=large QS_REPEAT_COUNT=2 QS_SCALE_MODE=weak QS_CHUNK_COUNT=64 sbatch -q regular -t 01:00:00 -N 16 jobs/perlmutter/practical_suite_scale_nodes.sbatch
QS_SWEEP_PROFILE=large QS_REPEAT_COUNT=4 QS_SCALE_MODE=weak QS_CHUNK_COUNT=128 sbatch -q regular -t 01:00:00 -N 32 jobs/perlmutter/practical_suite_scale_nodes.sbatch
QS_SWEEP_PROFILE=large QS_REPEAT_COUNT=8 QS_SCALE_MODE=weak QS_CHUNK_COUNT=256 sbatch -q regular -t 01:00:00 -N 64 jobs/perlmutter/practical_suite_scale_nodes.sbatch

# Strong scaling: completed direct fixed-work evidence on 64 / 128 / 256 GPUs.
# Optional 32-GPU direct extension is pending as job 55792240.
QS_SWEEP_PROFILE=large QS_REPEAT_COUNT=8 QS_SCALE_MODE=strong QS_CHUNK_COUNT=256 sbatch -q regular -t 01:15:00 -N 16 jobs/perlmutter/practical_suite_scale_nodes.sbatch
QS_SWEEP_PROFILE=large QS_REPEAT_COUNT=8 QS_SCALE_MODE=strong QS_CHUNK_COUNT=256 sbatch -q regular -t 01:00:00 -N 32 jobs/perlmutter/practical_suite_scale_nodes.sbatch
QS_SWEEP_PROFILE=large QS_REPEAT_COUNT=8 QS_SCALE_MODE=strong QS_CHUNK_COUNT=256 sbatch -q regular -t 01:00:00 -N 64 jobs/perlmutter/practical_suite_scale_nodes.sbatch
```

## Key JSON Artifacts

| Artifact | Path |
| --- | --- |
| Paper evidence audit | `data/processed/perlmutter/paper_evidence_audit.json` |
| Submission readiness audit | `data/processed/perlmutter/submission_readiness_audit.json` |
| Artifact manifest | `data/processed/perlmutter/paper_artifact_manifest.json` |
| Previous-paper alignment metrics | `data/processed/perlmutter/previous_paper_alignment_metrics.json` |
| Previous-paper deep trace | `data/processed/perlmutter/previous_paper_deep_trace.json` |
| Previous-paper style audit | `data/processed/perlmutter/previous_paper_style_audit.json` |
| PDF readability renders | `/tmp/qsup_render2/contact_01_06.png`, `/tmp/qsup_render2/contact_07_12.png`, `/tmp/qsup_render2/contact_13_14.png` |
| Main 128-GPU summary | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.json` |
| Weak-scaling 16-node summary | `data/processed/perlmutter/practical_suite_55731013_scale_16n_64g_summary.json` |
| Weak-scaling 32-node summary | `data/processed/perlmutter/practical_suite_55731014_scale_32n_128g_summary.json` |
| Weak-scaling 64-node summary | `data/processed/perlmutter/practical_suite_55731015_scale_64n_256g_summary.json` |
| Strong-scaling 8-node direct extension | Optional pending Slurm job 55792240; expected `data/processed/perlmutter/practical_suite_direct32_strong_8n_32g_7104_20260711082639_summary.json` |
| Strong-scaling 16-node summary | `data/processed/perlmutter/practical_suite_55731032_scale_16n_64g_summary.json` |
| Strong-scaling 32-node summary | `data/processed/perlmutter/practical_suite_55731033_scale_32n_128g_summary.json` |
| Strong-scaling 64-node summary | `data/processed/perlmutter/practical_suite_55731034_scale_64n_256g_summary.json` |
| ML production-native gate | `data/processed/perlmutter/ml_strong_native_gate_latest.json` |
| ML profiling gate | `data/processed/perlmutter/ml_strong_native_profile_latest.json` |
| Advantage projection | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_advantage_projection.json` |
| Projection scenario sweep | `data/processed/perlmutter/practical_suite_projection_scenarios.json` |
| Workload taxonomy | `data/processed/perlmutter/practical_suite_strongnative_32node_large128c0c127_20260704060230_taxonomy.json` |

Markdown policy: only README files and `plan.md` are kept in the repository.
