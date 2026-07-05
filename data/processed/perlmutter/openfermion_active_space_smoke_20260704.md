# OpenFermion/PySCF Active-Space Smoke

Date: 2026-07-04

Purpose: validate larger chemistry fixtures on the Perlmutter login node before spending GPU allocation.

Command shape:

```bash
module load cudatoolkit/12.9
/pscratch/sd/s/sgkim/kis_cuquantum/00_env/cutn_conda/bin/python \
  benchmarks/workloads/run_practical_suite.py \
  --workloads chemistry \
  --chem-grid 3 \
  --chem-layers 1 \
  --chem-hamiltonian-json <fixture>
```

| Problem | Qubits | Pauli terms | Selected native | Best quality native | Native time (s) | Quantum time (s) | Energy error |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| LiH active 6q | 6 | 62 | dense exact | sparse Lanczos | 0.000511 | 7.5518 | 0.3465 |
| H2O active 6q | 6 | 62 | dense exact | sparse Lanczos | 0.000478 | 7.5517 | 1.5536 |
| LiH active 8q | 8 | 105 | dense exact | sparse Lanczos | 0.012146 | 7.6970 | 0.6988 |
| H2O active 8q | 8 | 105 | dense exact | dense exact | 0.009895 | 7.5986 | 1.8580 |

Interpretation: the larger OpenFermion/PySCF fixtures execute through the same chemistry VQE path and evaluate both dense exact and sparse Lanczos native candidates. Dense exact is still selected for runtime at these small active-space sizes, but the sparse quality path is validated and ready for larger chemistry sweeps.
