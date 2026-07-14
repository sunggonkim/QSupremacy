#!/usr/bin/env python3
"""Close chemistry quality and execution cost across one active-space ladder."""

import argparse
import importlib.metadata
import json
import math
import os
import time
from pathlib import Path

import numpy as np
from openfermion import (
    FermionOperator,
    MolecularData,
    hermitian_conjugated,
    jordan_wigner,
)
from openfermionpyscf import run_pyscf
from pyscf import mcscf
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit.transpiler import CouplingMap
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "data/processed/perlmutter/chem_active_space_quality_closure.json"
)
DEFAULT_FIXTURE_DIR = ROOT / "benchmarks/workloads/hamiltonians"


def parse_ints(text):
    return tuple(int(value.strip()) for value in text.split(",") if value.strip())


def persist(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def display_path(path):
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def h_chain_geometry(atoms, spacing_angstrom):
    return [("H", (0.0, 0.0, spacing_angstrom * index)) for index in range(atoms)]


def qubit_operator_to_sparse_pauli(qubit_operator, qubits):
    pairs = []
    for term, coefficient in qubit_operator.terms.items():
        label = ["I"] * qubits
        for index, pauli in term:
            label[qubits - int(index) - 1] = str(pauli).upper()
        pairs.append(("".join(label), complex(coefficient)))
    return SparsePauliOp.from_list(pairs)


def write_fixture(path, name, molecule, active_orbitals, occupied_orbitals, operator):
    qubits = 2 * len(active_orbitals)
    terms = []
    for term, coefficient in sorted(operator.terms.items()):
        word = ["I"] * qubits
        for index, pauli in term:
            word[int(index)] = str(pauli).upper()
        value = complex(coefficient)
        if abs(value.imag) > 1.0e-10:
            raise ValueError("non-real molecular Hamiltonian coefficient")
        terms.append({"pauli": "".join(word), "coefficient": float(value.real)})
    payload = {
        "name": name,
        "description": (
            "OpenFermion/PySCF H8 STO-3G active-space Hamiltonian for the "
            "quality-and-cost closure ladder."
        ),
        "source": "OpenFermion {} + PySCF {}".format(
            importlib.metadata.version("openfermion"),
            importlib.metadata.version("pyscf"),
        ),
        "geometry": [
            {"atom": atom, "xyz": [float(value) for value in xyz]}
            for atom, xyz in molecule.geometry
        ],
        "basis": molecule.basis,
        "multiplicity": int(molecule.multiplicity),
        "charge": int(molecule.charge),
        "occupied_indices": occupied_orbitals,
        "active_indices": active_orbitals,
        "n_qubits": qubits,
        "n_active_electrons": int(molecule.n_electrons - 2 * len(occupied_orbitals)),
        "hf_energy": float(molecule.hf_energy),
        "terms": terms,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def chemistry_ansatz(qubits, electrons, reps):
    """Pair-UCC circuit over occupied-to-virtual closed-shell excitations."""
    circuit = QuantumCircuit(qubits)
    circuit.x(range(electrons))
    parameters = []
    spatial_orbitals = qubits // 2
    occupied_orbitals = electrons // 2
    for rep in range(reps):
        for occupied in range(occupied_orbitals):
            for virtual in range(occupied_orbitals, spatial_orbitals):
                parameter = Parameter(
                    "r{}_pair{}_{}".format(rep, occupied, virtual)
                )
                excitation = FermionOperator(
                    (
                        (2 * virtual, 1),
                        (2 * virtual + 1, 1),
                        (2 * occupied + 1, 0),
                        (2 * occupied, 0),
                    ),
                    1.0,
                )
                hermitian_generator = 1.0j * (
                    excitation - hermitian_conjugated(excitation)
                )
                pauli_generator = qubit_operator_to_sparse_pauli(
                    jordan_wigner(hermitian_generator), qubits
                )
                parameters.append(parameter)
                circuit.append(
                    PauliEvolutionGate(pauli_generator, time=parameter),
                    range(qubits),
                )
    # Decompose once so each optimizer evaluation executes a reusable gate DAG.
    circuit = transpile(
        circuit,
        basis_gates=["rz", "sx", "x", "cx"],
        optimization_level=1,
        seed_transpiler=17,
    )
    return circuit, parameters


def energy_function(circuit, parameters, hamiltonian):
    evaluations = {"count": 0, "best": float("inf")}

    def evaluate(values):
        bound = circuit.assign_parameters(dict(zip(parameters, values)), inplace=False)
        state = Statevector.from_instruction(bound)
        energy = float(np.real(state.expectation_value(hamiltonian)))
        evaluations["count"] += 1
        evaluations["best"] = min(evaluations["best"], energy)
        return energy

    return evaluate, evaluations


def optimize_ansatz(
    circuit,
    parameters,
    hamiltonian,
    restarts,
    max_evaluations,
    seed,
    warm_start=None,
):
    rng = np.random.default_rng(seed)
    starts = []
    if warm_start is not None:
        initial = np.zeros(len(parameters), dtype=float)
        initial[: len(warm_start)] = warm_start
        starts.append(initial)
    else:
        starts.append(np.zeros(len(parameters), dtype=float))
    while len(starts) < restarts:
        starts.append(rng.normal(0.0, 0.08, size=len(parameters)))

    best = None
    total_evaluations = 0
    started = time.perf_counter()
    for restart, initial in enumerate(starts):
        objective, counter = energy_function(circuit, parameters, hamiltonian)
        result = minimize(
            objective,
            initial,
            method="COBYLA",
            options={
                "maxiter": max_evaluations,
                "rhobeg": 0.20,
                "tol": 1.0e-5,
                "catol": 1.0e-8,
            },
        )
        total_evaluations += counter["count"]
        candidate = {
            "restart": restart,
            "energy_ha": float(result.fun),
            "parameters": [float(value) for value in result.x],
            "evaluations": int(counter["count"]),
            "optimizer_success": bool(result.success),
            "optimizer_message": str(result.message),
        }
        if best is None or candidate["energy_ha"] < best["energy_ha"]:
            best = candidate
    best["total_evaluations_all_restarts"] = total_evaluations
    best["optimization_wall_sec"] = time.perf_counter() - started
    return best


def topology(name, qubits):
    if name == "all_to_all":
        return CouplingMap.from_full(qubits, bidirectional=True)
    if name == "line":
        return CouplingMap.from_line(qubits, bidirectional=True)
    if name == "grid":
        return CouplingMap.from_grid(2, qubits // 2, bidirectional=True)
    raise ValueError(name)


def compile_record(circuit, parameters, values, topology_name, seed):
    bound = circuit.assign_parameters(dict(zip(parameters, values)), inplace=False)
    measured = bound.copy()
    measured.measure_all()
    compiled = transpile(
        measured,
        basis_gates=["rz", "sx", "x", "cx"],
        coupling_map=topology(topology_name, circuit.num_qubits),
        optimization_level=3,
        seed_transpiler=seed,
    )
    counts = {str(name): int(count) for name, count in compiled.count_ops().items()}
    return {
        "topology": topology_name,
        "depth": int(compiled.depth()),
        "two_qubit_depth": int(
            compiled.depth(
                filter_function=lambda instruction: instruction.operation.name == "cx"
            )
        ),
        "one_qubit_gates": int(
            sum(counts.get(name, 0) for name in ("rz", "sx", "x"))
        ),
        "two_qubit_gates": int(counts.get("cx", 0)),
        "measurement_ops": int(counts.get("measure", 0)),
        "gate_counts": counts,
    }


def measurement_record(hamiltonian, target_error_ha, fixed_shots):
    labels = hamiltonian.paulis.to_labels()
    non_identity_indices = [
        index for index, label in enumerate(labels) if set(label) != {"I"}
    ]
    measured = SparsePauliOp(
        hamiltonian.paulis[non_identity_indices],
        hamiltonian.coeffs[non_identity_indices],
    )
    groups = measured.group_commuting(qubit_wise=True)
    group_l1 = [float(np.sum(np.abs(group.coeffs))) for group in groups]
    total_l1 = float(sum(group_l1))
    weights = np.asarray(group_l1, dtype=float)
    allocation = np.maximum(
        1,
        np.rint(fixed_shots * weights / max(total_l1, 1.0e-12)).astype(int),
    )
    # This is a state-independent variance bound, not a measured shot requirement.
    worst_case_shots = int(math.ceil((total_l1 / target_error_ha) ** 2))
    return {
        "pauli_terms_total": int(len(hamiltonian)),
        "pauli_terms_measured": int(len(measured)),
        "qwc_groups": int(len(groups)),
        "largest_qwc_group": int(max(len(group) for group in groups)),
        "coefficient_l1_measured": total_l1,
        "fixed_shot_budget": int(fixed_shots),
        "fixed_shots_allocated": int(np.sum(allocation)),
        "state_independent_shot_bound_for_target_error": worst_case_shots,
        "target_standard_error_ha": float(target_error_ha),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chain-atoms", type=int, default=8)
    parser.add_argument("--spacing-angstrom", type=float, default=1.4)
    parser.add_argument("--active-orbitals", default="2,4,6,8")
    parser.add_argument("--reps", default="1,2")
    parser.add_argument("--restarts", type=int, default=2)
    parser.add_argument("--evals-per-parameter", type=float, default=2.0)
    parser.add_argument("--minimum-evals", type=int, default=60)
    parser.add_argument("--maximum-evals", type=int, default=220)
    parser.add_argument("--target-error-ha", type=float, default=0.01)
    parser.add_argument("--fixed-shots", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR)
    args = parser.parse_args()

    active_values = parse_ints(args.active_orbitals)
    reps_values = parse_ints(args.reps)
    if args.chain_atoms % 2:
        raise ValueError("the closed-shell chain requires an even atom count")
    if any(value > args.chain_atoms for value in active_values):
        raise ValueError("active orbitals exceed the STO-3G chain orbital count")

    raw_dir = ROOT / "data/raw/perlmutter/chem_active_space"
    raw_dir.mkdir(parents=True, exist_ok=True)
    molecule = MolecularData(
        geometry=h_chain_geometry(args.chain_atoms, args.spacing_angstrom),
        basis="sto-3g",
        multiplicity=1,
        charge=0,
        description="h{}_chain_{:.2f}a".format(
            args.chain_atoms, args.spacing_angstrom
        ),
        filename=str(raw_dir / "h{}_chain".format(args.chain_atoms)),
    )
    scf_started = time.perf_counter()
    molecule = run_pyscf(molecule, run_scf=True, run_fci=False)
    scf_wall = time.perf_counter() - scf_started
    mean_field = molecule._pyscf_data["scf"]

    output = {
        "schema": "qsup.chem-active-space-quality-closure.v1",
        "status": "running",
        "scope": (
            "same H8 STO-3G chain at 1.4 Angstrom with nested 2/4/6/8-spatial-"
            "orbital active spaces; exact CASCI/FCI native target, noiseless "
            "pair-UCC VQE-style statevector optimization, QWC grouping, "
            "and compiled topology cost; controlled scale evidence, not a "
            "deployment-scale molecular VQE claim"
        ),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("pyscf", "openfermion", "openfermionpyscf", "qiskit", "scipy")
        },
        "host": os.uname().nodename,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "chain_atoms": args.chain_atoms,
        "spacing_angstrom": args.spacing_angstrom,
        "scf_energy_ha": float(molecule.hf_energy),
        "scf_wall_sec": scf_wall,
        "quality_target_ha": args.target_error_ha,
        "optimizer": {
            "name": "COBYLA",
            "restarts": args.restarts,
            "evals_per_parameter": args.evals_per_parameter,
            "minimum_evals": args.minimum_evals,
            "maximum_evals": args.maximum_evals,
        },
        "records": [],
    }
    persist(args.output, output)

    for active_orbitals_count in active_values:
        core_orbitals = (args.chain_atoms - active_orbitals_count) // 2
        occupied = list(range(core_orbitals))
        active = list(range(core_orbitals, core_orbitals + active_orbitals_count))
        active_electrons = molecule.n_electrons - 2 * core_orbitals
        qubits = 2 * active_orbitals_count

        fci_started = time.perf_counter()
        casci = mcscf.CASCI(mean_field, active_orbitals_count, active_electrons)
        casci.verbose = 0
        fci_energy = float(casci.kernel()[0])
        fci_wall = time.perf_counter() - fci_started

        molecular_hamiltonian = molecule.get_molecular_hamiltonian(
            occupied_indices=occupied or None,
            active_indices=active,
        )
        qubit_hamiltonian = jordan_wigner(molecular_hamiltonian)
        hamiltonian = qubit_operator_to_sparse_pauli(qubit_hamiltonian, qubits)
        fixture_name = "h8_sto3g_active_{}q".format(qubits)
        fixture_path = args.fixture_dir / (fixture_name + ".json")
        write_fixture(
            fixture_path,
            fixture_name,
            molecule,
            active,
            occupied,
            qubit_hamiltonian,
        )
        measure = measurement_record(
            hamiltonian, args.target_error_ha, args.fixed_shots
        )

        warm_start = None
        for reps in reps_values:
            circuit, parameters = chemistry_ansatz(qubits, active_electrons, reps)
            hf_values = np.zeros(len(parameters), dtype=float)
            hf_energy = float(
                np.real(
                    Statevector.from_instruction(
                        circuit.assign_parameters(dict(zip(parameters, hf_values)))
                    ).expectation_value(hamiltonian)
                )
            )
            if abs(hf_energy - molecule.hf_energy) > 1.0e-7:
                raise RuntimeError(
                    "Hamiltonian/HF ordering mismatch: {} vs {}".format(
                        hf_energy, molecule.hf_energy
                    )
                )
            max_evaluations = int(
                min(
                    args.maximum_evals,
                    max(
                        args.minimum_evals,
                        math.ceil(args.evals_per_parameter * len(parameters)),
                    ),
                )
            )
            optimized = optimize_ansatz(
                circuit,
                parameters,
                hamiltonian,
                args.restarts,
                max_evaluations,
                args.seed + 100 * qubits + reps,
                warm_start=warm_start,
            )
            warm_start = optimized["parameters"]
            compiled = [
                compile_record(
                    circuit,
                    parameters,
                    optimized["parameters"],
                    topology_name,
                    args.seed,
                )
                for topology_name in ("all_to_all", "grid", "line")
            ]
            base_cx = max(1, compiled[0]["two_qubit_gates"])
            for item in compiled:
                item["routing_multiplier_vs_all_to_all"] = (
                    item["two_qubit_gates"] / base_cx
                )
            record = {
                "active_spatial_orbitals": active_orbitals_count,
                "active_electrons": int(active_electrons),
                "qubits": qubits,
                "occupied_indices": occupied,
                "active_indices": active,
                "fixture": display_path(fixture_path),
                "fci_energy_ha": fci_energy,
                "fci_wall_sec": fci_wall,
                "hf_energy_ha": hf_energy,
                "hf_error_ha": hf_energy - fci_energy,
                "ansatz": (
                    "Jordan-Wigner pair-UCC occupied-to-virtual closed-shell "
                    "excitations compiled as Pauli evolutions"
                ),
                "ansatz_reps": reps,
                "parameters": len(parameters),
                "max_evaluations_per_restart": max_evaluations,
                "vqe_energy_ha": optimized["energy_ha"],
                "vqe_error_ha": optimized["energy_ha"] - fci_energy,
                "quality_pass_0p01_ha": bool(
                    optimized["energy_ha"] - fci_energy <= args.target_error_ha
                ),
                "optimization": optimized,
                "measurement": measure,
                "compiled": compiled,
            }
            output["records"].append(record)
            persist(args.output, output)
            print(
                json.dumps(
                    {
                        "qubits": qubits,
                        "reps": reps,
                        "vqe_error_ha": record["vqe_error_ha"],
                        "qwc_groups": measure["qwc_groups"],
                        "records": len(output["records"]),
                    }
                ),
                flush=True,
            )

    output["status"] = "complete"
    persist(args.output, output)
    print(json.dumps({"output": str(args.output), "records": len(output["records"])}, indent=2))


if __name__ == "__main__":
    main()
