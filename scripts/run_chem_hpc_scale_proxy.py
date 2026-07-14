#!/usr/bin/env python3
"""Checkpointed all-electron PySCF scale extension for native Chem evidence."""

import argparse
import json
import os
import platform
import socket
import time
from pathlib import Path

from pyscf import cc, gto, lib, mp, scf


CASES = {
    "n2_ccpvtz": {
        "name": "N2",
        "atom": "N 0 0 -0.55; N 0 0 0.55",
        "basis": "cc-pvtz",
    },
    "h2o_augccpvtz": {
        "name": "H2O",
        "atom": "O 0 0 0; H 0 -0.757 0.587; H 0 0.757 0.587",
        "basis": "aug-cc-pvtz",
    },
}


def write_checkpoint(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temporary.replace(path)


def timed(function):
    start = time.perf_counter()
    value = function()
    return value, time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=sorted(CASES), required=True)
    parser.add_argument("--threads", type=int, default=64)
    parser.add_argument("--max-memory-mb", type=int, default=400000)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    lib.num_threads(args.threads)
    spec = CASES[args.case]
    output_path = Path(args.output)
    payload = {
        "schema": "qsup.chem-hpc-scale-proxy.v1",
        "scope": (
            "all-electron native chemistry scale extension; no matched large "
            "VQE execution or deployment-scale advantage is claimed"
        ),
        "case_id": args.case,
        "molecule": spec["name"],
        "basis": spec["basis"],
        "status": "initializing",
        "environment": {
            "host": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "threads": lib.num_threads(),
            "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "slurm_cpus_per_task": os.environ.get("SLURM_CPUS_PER_TASK"),
        },
        "stages": {},
    }
    write_checkpoint(output_path, payload)

    try:
        mol = gto.M(
            atom=spec["atom"],
            basis=spec["basis"],
            max_memory=args.max_memory_mb,
            verbose=4,
        )
        payload.update({
            "atomic_orbitals": int(mol.nao_nr()),
            "electrons": int(mol.nelectron),
            "spin_orbital_qubits": int(2 * mol.nao_nr()),
        })
        spin_orbitals = 2 * mol.nao_nr()
        occupied_spin_orbitals = mol.nelectron
        virtual_spin_orbitals = spin_orbitals - occupied_spin_orbitals
        payload["quantum_contract"] = {
            "scope": (
                "same-instance combinatorial upper contract; no integral pruning, "
                "Pauli grouping, circuit compilation, or VQE energy is claimed"
            ),
            "occupied_spin_orbitals": int(occupied_spin_orbitals),
            "virtual_spin_orbitals": int(virtual_spin_orbitals),
            "uccsd_single_excitations": int(
                occupied_spin_orbitals * virtual_spin_orbitals
            ),
            "uccsd_double_excitations": int(
                occupied_spin_orbitals
                * (occupied_spin_orbitals - 1)
                // 2
                * virtual_spin_orbitals
                * (virtual_spin_orbitals - 1)
                // 2
            ),
            "unpruned_jw_pauli_worst_case": int(
                2 * mol.nao_nr() ** 2 + 32 * mol.nao_nr() ** 4
            ),
        }
        payload["status"] = "running_hf"
        write_checkpoint(output_path, payload)

        mf, runtime = timed(lambda: scf.RHF(mol).run())
        payload["stages"]["hf"] = {
            "runtime_sec": runtime,
            "energy_hartree": float(mf.e_tot),
            "converged": bool(mf.converged),
        }
        payload.update({
            "occupied_spatial_orbitals": int(mol.nelectron // 2),
            "virtual_spatial_orbitals": int(mol.nao_nr() - mol.nelectron // 2),
            "status": "running_mp2",
        })
        write_checkpoint(output_path, payload)

        mp2_result, runtime = timed(lambda: mp.MP2(mf).run())
        payload["stages"]["mp2"] = {
            "runtime_sec": runtime,
            "energy_hartree": float(mp2_result.e_tot),
        }
        payload["status"] = "running_ccsd"
        write_checkpoint(output_path, payload)

        ccsd_result, runtime = timed(lambda: cc.CCSD(mf).run())
        payload["stages"]["ccsd"] = {
            "runtime_sec": runtime,
            "energy_hartree": float(ccsd_result.e_tot),
            "converged": bool(ccsd_result.converged),
        }
        payload["status"] = "running_triples"
        write_checkpoint(output_path, payload)

        triples, runtime = timed(ccsd_result.ccsd_t)
        payload["stages"]["triples"] = {
            "runtime_sec": runtime,
            "correction_hartree": float(triples),
            "ccsdt_energy_hartree": float(ccsd_result.e_tot + triples),
        }
        payload["total_native_runtime_sec"] = sum(
            stage["runtime_sec"] for stage in payload["stages"].values()
        )
        payload["status"] = "complete"
    except Exception as error:
        payload["status"] = "failed"
        payload["error"] = repr(error)
        write_checkpoint(output_path, payload)
        raise

    write_checkpoint(output_path, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
