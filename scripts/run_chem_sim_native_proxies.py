#!/usr/bin/env python3
"""Measure native scale-extension proxies for chemistry and simulation."""

import argparse
import gc
import json
import os
import platform
import socket
import time
from pathlib import Path

import numpy as np
from pyscf import ao2mo, cc, gto, mp, scf
from scipy.sparse.linalg import LinearOperator, expm_multiply


MOLECULES = [
    {
        "name": "LiH",
        "atom": "Li 0 0 0; H 0 0 1.6",
        "basis": "cc-pvtz",
    },
    {
        "name": "H2O",
        "atom": "O 0 0 0; H 0 -0.757 0.587; H 0 0.757 0.587",
        "basis": "cc-pvdz",
    },
    {
        "name": "N2",
        "atom": "N 0 0 -0.55; N 0 0 0.55",
        "basis": "cc-pvdz",
    },
]


def timed(function):
    started = time.perf_counter()
    value = function()
    return value, time.perf_counter() - started


def chemistry_proxy(spec):
    mol = gto.M(atom=spec["atom"], basis=spec["basis"], verbose=0)
    mf, hf_sec = timed(lambda: scf.RHF(mol).run())
    mp2, mp2_sec = timed(lambda: mp.MP2(mf).run())
    ccsd, ccsd_sec = timed(lambda: cc.CCSD(mf).run())
    triples, triples_sec = timed(ccsd.ccsd_t)
    one_body_mo = mf.mo_coeff.T @ mf.get_hcore() @ mf.mo_coeff
    eri_compact = ao2mo.kernel(mol, mf.mo_coeff, compact=True)
    eri_full = ao2mo.restore(1, eri_compact, mol.nao_nr())
    threshold = 1e-10
    one_body_nonzero = int(np.count_nonzero(np.abs(one_body_mo) > threshold))
    two_body_nonzero = int(np.count_nonzero(np.abs(eri_full) > threshold))
    spin_orbitals = 2 * mol.nao_nr()
    occupied_spin_orbitals = mol.nelectron
    virtual_spin_orbitals = spin_orbitals - occupied_spin_orbitals
    uccsd_singles = occupied_spin_orbitals * virtual_spin_orbitals
    uccsd_doubles = (
        occupied_spin_orbitals
        * (occupied_spin_orbitals - 1)
        // 2
        * virtual_spin_orbitals
        * (virtual_spin_orbitals - 1)
        // 2
    )
    return {
        "name": spec["name"],
        "basis": spec["basis"],
        "atomic_orbitals": int(mol.nao_nr()),
        "electrons": int(mol.nelectron),
        "spin_orbital_qubits": int(spin_orbitals),
        "one_body_mo_nonzero": one_body_nonzero,
        "two_body_spatial_mo_nonzero": two_body_nonzero,
        "jordan_wigner_pauli_upper_bound": int(
            2 * one_body_nonzero + 32 * two_body_nonzero
        ),
        "uccsd_single_excitations": int(uccsd_singles),
        "uccsd_double_excitations": int(uccsd_doubles),
        "hf_runtime_sec": hf_sec,
        "mp2_runtime_sec": mp2_sec,
        "ccsd_runtime_sec": ccsd_sec,
        "triples_runtime_sec": triples_sec,
        "ccsdt_total_runtime_sec": hf_sec + ccsd_sec + triples_sec,
        "hf_energy_hartree": float(mf.e_tot),
        "mp2_energy_hartree": float(mp2.e_tot),
        "ccsd_energy_hartree": float(ccsd.e_tot),
        "ccsdt_energy_hartree": float(ccsd.e_tot + triples),
        "ccsd_converged": bool(ccsd.converged),
    }


def tfim_operator(qubits, coupling, field):
    dimension = 1 << qubits
    states = np.arange(dimension, dtype=np.uint64)
    diagonal = np.zeros(dimension, dtype=np.float64)
    for q in range(qubits - 1):
        zq = 1.0 - 2.0 * ((states >> np.uint64(q)) & np.uint64(1))
        zr = 1.0 - 2.0 * ((states >> np.uint64(q + 1)) & np.uint64(1))
        diagonal -= coupling * zq * zr
    def matvec(vector):
        vector = np.asarray(vector).reshape(-1)
        out = diagonal * vector
        for q in range(qubits):
            out -= field * vector[states ^ np.uint64(1 << q)]
        return out

    return LinearOperator(
        shape=(dimension, dimension),
        matvec=matvec,
        rmatvec=matvec,
        matmat=lambda matrix: np.column_stack([matvec(matrix[:, i]) for i in range(matrix.shape[1])]),
        dtype=np.complex128,
    )


def simulation_proxy(qubits, evolution_time):
    dimension = 1 << qubits
    operator = tfim_operator(qubits, coupling=1.0, field=0.7)
    initial = np.zeros(dimension, dtype=np.complex128)
    initial[0] = 1.0
    started = time.perf_counter()
    final = expm_multiply(
        -1.0j * operator,
        initial,
        start=0.0,
        stop=evolution_time,
        num=2,
        endpoint=True,
        traceA=0.0,
    )[-1]
    runtime = time.perf_counter() - started
    norm_error = abs(float(np.vdot(final, final).real) - 1.0)
    states = np.arange(dimension, dtype=np.uint64)
    trotter_diagonal = np.zeros(dimension, dtype=np.float64)
    for q in range(qubits - 1):
        zq = 1.0 - 2.0 * ((states >> np.uint64(q)) & np.uint64(1))
        zr = 1.0 - 2.0 * ((states >> np.uint64(q + 1)) & np.uint64(1))
        trotter_diagonal -= zq * zr
    trotter_quality = []
    for steps in (4, 8, 16):
        vector = initial.copy()
        dt = evolution_time / steps
        started = time.perf_counter()
        for _ in range(steps):
            vector *= np.exp(-1.0j * dt * trotter_diagonal)
            cosine = np.cos(0.7 * dt)
            sine = 1.0j * np.sin(0.7 * dt)
            for q in range(qubits):
                bit = np.uint64(1 << q)
                low = states[(states & bit) == 0]
                high = low ^ bit
                low_values = vector[low].copy()
                high_values = vector[high].copy()
                vector[low] = cosine * low_values + sine * high_values
                vector[high] = sine * low_values + cosine * high_values
        trotter_runtime = time.perf_counter() - started
        fidelity = float(abs(np.vdot(final, vector)) ** 2)
        trotter_quality.append({
            "steps": steps,
            "runtime_sec": trotter_runtime,
            "fidelity_to_krylov": fidelity,
            "infidelity": 1.0 - fidelity,
            "one_qubit_gates": qubits * steps,
            "two_qubit_gates": (qubits - 1) * steps,
        })
    return {
        "model": "scipy_matrix_free_krylov_expm_multiply",
        "hamiltonian": "1D open-boundary transverse-field Ising",
        "qubits": qubits,
        "state_dimension": dimension,
        "state_bytes_complex128": int(initial.nbytes),
        "evolution_time": evolution_time,
        "runtime_sec": runtime,
        "norm_error": norm_error,
        "trotter_quality": trotter_quality,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sim-qubits", default="16,18,20")
    parser.add_argument("--evolution-time", type=float, default=1.0)
    parser.add_argument(
        "--output", default="data/processed/perlmutter/chem_sim_native_proxies.json"
    )
    args = parser.parse_args()

    output = {
        "schema": "qsup.chem-sim-native-proxies.v1",
        "scope": (
            "native solver scale-extension proxies; no matched large VQE or "
            "Trotter circuit execution is claimed"
        ),
        "environment": {
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
            "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
        },
        "chemistry": [],
        "simulation": [
            simulation_proxy(int(qubits), args.evolution_time)
            for qubits in args.sim_qubits.split(",")
        ],
    }
    for spec in MOLECULES:
        output["chemistry"].append(chemistry_proxy(spec))
        gc.collect()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")
    print(json.dumps({
        "chemistry_cases": len(output["chemistry"]),
        "simulation_cases": len(output["simulation"]),
        "output": str(path),
    }, indent=2))


if __name__ == "__main__":
    main()
