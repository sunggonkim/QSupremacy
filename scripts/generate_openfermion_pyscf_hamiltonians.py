#!/usr/bin/env python3
"""Generate small OpenFermion/PySCF molecular Hamiltonian fixtures.

The practical suite keeps Hamiltonians as Pauli-term JSON so Perlmutter jobs can
consume generated chemistry instances without importing PySCF inside every case.
"""

import argparse
import json
import os

from openfermion import MolecularData, jordan_wigner
from openfermionpyscf import run_pyscf


MOLECULES = {
    "h2_sto3g_4q": {
        "geometry": [("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 0.7414))],
        "basis": "sto-3g",
        "multiplicity": 1,
        "charge": 0,
        "occupied_indices": None,
        "active_indices": None,
        "description": "OpenFermion/PySCF H2 STO-3G Jordan-Wigner Hamiltonian.",
    },
    "lih_sto3g_active_4q": {
        "geometry": [("Li", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 1.45))],
        "basis": "sto-3g",
        "multiplicity": 1,
        "charge": 0,
        "occupied_indices": [0],
        "active_indices": [1, 2],
        "description": "OpenFermion/PySCF LiH STO-3G active-space Hamiltonian.",
    },
    "lih_sto3g_active_6q": {
        "geometry": [("Li", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 1.45))],
        "basis": "sto-3g",
        "multiplicity": 1,
        "charge": 0,
        "occupied_indices": [0],
        "active_indices": [1, 2, 3],
        "description": "OpenFermion/PySCF LiH STO-3G 6-qubit active-space Hamiltonian.",
    },
    "lih_sto3g_active_8q": {
        "geometry": [("Li", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 1.45))],
        "basis": "sto-3g",
        "multiplicity": 1,
        "charge": 0,
        "occupied_indices": [0],
        "active_indices": [1, 2, 3, 4],
        "description": "OpenFermion/PySCF LiH STO-3G 8-qubit active-space Hamiltonian.",
    },
    "h2o_sto3g_active_4q": {
        "geometry": [
            ("O", (0.0, 0.0, 0.0)),
            ("H", (0.0, 0.757, 0.586)),
            ("H", (0.0, -0.757, 0.586)),
        ],
        "basis": "sto-3g",
        "multiplicity": 1,
        "charge": 0,
        "occupied_indices": [0, 1, 2, 3],
        "active_indices": [4, 5],
        "description": "OpenFermion/PySCF H2O STO-3G active-space Hamiltonian.",
    },
    "h2o_sto3g_active_6q": {
        "geometry": [
            ("O", (0.0, 0.0, 0.0)),
            ("H", (0.0, 0.757, 0.586)),
            ("H", (0.0, -0.757, 0.586)),
        ],
        "basis": "sto-3g",
        "multiplicity": 1,
        "charge": 0,
        "occupied_indices": [0, 1, 2],
        "active_indices": [3, 4, 5],
        "description": "OpenFermion/PySCF H2O STO-3G 6-qubit active-space Hamiltonian.",
    },
    "h2o_sto3g_active_8q": {
        "geometry": [
            ("O", (0.0, 0.0, 0.0)),
            ("H", (0.0, 0.757, 0.586)),
            ("H", (0.0, -0.757, 0.586)),
        ],
        "basis": "sto-3g",
        "multiplicity": 1,
        "charge": 0,
        "occupied_indices": [0, 1, 2],
        "active_indices": [3, 4, 5, 6],
        "description": "OpenFermion/PySCF H2O STO-3G 8-qubit active-space Hamiltonian.",
    },
}


def term_to_word(term, n_qubits):
    chars = ["I"] * n_qubits
    for index, pauli in term:
        chars[int(index)] = str(pauli).upper()
    return "".join(chars)


def generate_molecule(name, spec, out_dir):
    molecule = MolecularData(
        geometry=spec["geometry"],
        basis=spec["basis"],
        multiplicity=spec["multiplicity"],
        charge=spec["charge"],
        description=name,
    )
    molecule = run_pyscf(molecule, run_scf=True, run_fci=False)
    molecular_hamiltonian = molecule.get_molecular_hamiltonian(
        occupied_indices=spec["occupied_indices"],
        active_indices=spec["active_indices"],
    )
    qubit_hamiltonian = jordan_wigner(molecular_hamiltonian)
    n_qubits = 0
    for term in qubit_hamiltonian.terms:
        for index, _ in term:
            n_qubits = max(n_qubits, int(index) + 1)

    terms = []
    for term, coeff in sorted(qubit_hamiltonian.terms.items()):
        word = term_to_word(term, n_qubits)
        coeff_complex = complex(coeff)
        if abs(coeff_complex.imag) > 1.0e-10:
            raise ValueError("{} has non-real coefficient {}".format(name, coeff))
        terms.append({"pauli": word, "coefficient": float(coeff_complex.real)})

    out = {
        "name": name,
        "description": spec["description"],
        "source": "OpenFermion {} + PySCF {}".format(
            __import__("openfermion").__version__,
            __import__("pyscf").__version__,
        ),
        "geometry": [
            {"atom": atom, "xyz": [float(x) for x in xyz]}
            for atom, xyz in spec["geometry"]
        ],
        "basis": spec["basis"],
        "multiplicity": int(spec["multiplicity"]),
        "charge": int(spec["charge"]),
        "occupied_indices": spec["occupied_indices"],
        "active_indices": spec["active_indices"],
        "n_qubits": int(n_qubits),
        "n_electrons": int(molecule.n_electrons),
        "n_orbitals": int(molecule.n_orbitals),
        "hf_energy": float(molecule.hf_energy),
        "terms": terms,
    }

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "{}.json".format(name))
    with open(path, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    return path, len(terms), n_qubits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir",
        default="benchmarks/workloads/hamiltonians",
        help="Directory for generated Pauli Hamiltonian JSON files.",
    )
    parser.add_argument(
        "--molecules",
        default=",".join(MOLECULES),
        help="Comma-separated molecule keys to generate.",
    )
    args = parser.parse_args()

    selected = [item.strip() for item in args.molecules.split(",") if item.strip()]
    for name in selected:
        if name not in MOLECULES:
            raise SystemExit("Unknown molecule key: {}".format(name))
        path, term_count, n_qubits = generate_molecule(name, MOLECULES[name], args.out_dir)
        print("{} n_qubits={} terms={} path={}".format(name, n_qubits, term_count, path))


if __name__ == "__main__":
    main()
