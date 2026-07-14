#!/usr/bin/env python3
"""Generate representative, physically explicit finite-shot quality records."""

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from strong_accept_common import (
    DEFAULT_INPUT,
    ROOT,
    TOLERANCES,
    as_float,
    as_int,
    base_seed,
    json_dump,
    median,
    percentile_interval,
    quantile,
    read_rows,
    record_id,
    relative,
    repeat_round,
)


OUTPUT = ROOT / "data/processed/perlmutter/finite_shot_quality_sensitivity.json"
I2 = np.eye(2, dtype=np.complex128)
X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
H = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128) / math.sqrt(2.0)
SDG = np.array([[1.0, 0.0], [0.0, -1.0j]], dtype=np.complex128)


def ry(theta):
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=np.complex128)


def rz(theta):
    return np.diag([
        np.exp(-0.5j * theta),
        np.exp(0.5j * theta),
    ]).astype(np.complex128)


def rx(theta):
    c = math.cos(theta / 2.0)
    s = -1.0j * math.sin(theta / 2.0)
    return np.array([[c, s], [s, c]], dtype=np.complex128)


def zero_state(qubits):
    state = np.zeros(1 << qubits, dtype=np.complex128)
    state[0] = 1.0
    return state


def apply_single(state, gate, qubit):
    step = 1 << qubit
    view = state.reshape(-1, 2 * step)
    low = view[:, :step].copy()
    high = view[:, step:].copy()
    view[:, :step] = gate[0, 0] * low + gate[0, 1] * high
    view[:, step:] = gate[1, 0] * low + gate[1, 1] * high


def apply_cnot(state, control, target):
    for index in range(state.size):
        if (index & (1 << control)) and not (index & (1 << target)):
            other = index | (1 << target)
            state[index], state[other] = state[other], state[index]


def apply_rzz(state, q0, q1, theta):
    apply_cnot(state, q0, q1)
    apply_single(state, rz(theta), q1)
    apply_cnot(state, q0, q1)


def pauli_matrix(word):
    matrices = {"I": I2, "X": X, "Y": Y, "Z": Z}
    result = matrices[word[0]]
    for char in word[1:]:
        result = np.kron(result, matrices[char])
    return result


def expectation(state, word):
    return float(np.vdot(state, pauli_matrix(word) @ state).real)


def basis_probabilities(state, basis_word):
    rotated = state.copy()
    qubits = int(round(math.log2(state.size)))
    for qubit in range(qubits):
        basis = basis_word[qubits - 1 - qubit]
        if basis == "X":
            apply_single(rotated, H, qubit)
        elif basis == "Y":
            apply_single(rotated, SDG, qubit)
            apply_single(rotated, H, qubit)
        elif basis not in ("I", "Z"):
            raise ValueError("unsupported measurement basis {}".format(basis))
    probabilities = np.abs(rotated) ** 2
    return probabilities / probabilities.sum()


def eigenvalues_for_word(word):
    qubits = len(word)
    values = np.ones(1 << qubits, dtype=np.float64)
    for basis_index in range(1 << qubits):
        value = 1.0
        for qubit in range(qubits):
            if word[qubits - 1 - qubit] != "I" and (basis_index & (1 << qubit)):
                value *= -1.0
        values[basis_index] = value
    return values


def softmax(logits):
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def train_softmax(x_train, y_train, x_test, y_test, classes, steps=300, lr=0.25):
    x_train_b = np.concatenate([x_train, np.ones((x_train.shape[0], 1))], axis=1)
    x_test_b = np.concatenate([x_test, np.ones((x_test.shape[0], 1))], axis=1)
    weights = np.zeros((x_train_b.shape[1], classes), dtype=np.float64)
    labels = np.eye(classes, dtype=np.float64)[y_train]
    for _ in range(steps):
        probabilities = softmax(x_train_b @ weights)
        gradient = x_train_b.T @ (probabilities - labels) / x_train_b.shape[0]
        weights -= lr * gradient
    predicted = np.argmax(softmax(x_test_b @ weights), axis=1)
    return float(np.mean(predicted == y_test))


def load_digits(samples, features, classes_text, seed):
    data = np.load(ROOT / "data/datasets/sklearn_digits.npz", allow_pickle=False)
    all_x = data["data"].astype(np.float64) / 16.0
    all_y = data["target"].astype(np.int64)
    classes = [int(value) for value in classes_text.split(",")]
    rng = np.random.default_rng(seed)
    selected = []
    per_class = samples // len(classes)
    remainder = samples % len(classes)
    for index, label in enumerate(classes):
        indices = np.flatnonzero(all_y == label)
        rng.shuffle(indices)
        selected.append(indices[: per_class + (1 if index < remainder else 0)])
    indices = np.concatenate(selected)
    rng.shuffle(indices)
    raw_x = all_x[indices]
    raw_y = all_y[indices]
    label_map = {label: index for index, label in enumerate(classes)}
    y = np.array([label_map[int(value)] for value in raw_y], dtype=np.int64)
    centered = raw_x - raw_x.mean(axis=0)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    reduced = centered @ vt[:features].T
    reduced = np.clip(reduced / (reduced.std(axis=0) + 1.0e-12), -3.0, 3.0)
    return reduced, y, len(classes)


def ml_probabilities(row):
    samples = as_int(row, "ml_samples")
    qubits = as_int(row, "ml_features")
    depth = as_int(row, "ml_depth")
    x, y, classes = load_digits(
        samples,
        qubits,
        row["digits_classes"],
        as_int(row, "seed"),
    )
    probabilities = []
    for sample in x:
        state = zero_state(qubits)
        for layer in range(depth):
            for qubit, value in enumerate(sample):
                angle = float(value * math.pi / 3.0)
                apply_single(state, ry(angle), qubit)
                apply_single(state, rz(angle * (layer + 1)), qubit)
            for qubit in range(qubits - 1):
                apply_cnot(state, qubit, qubit + 1)
        probabilities.append(np.abs(state) ** 2)
    probabilities = np.asarray(probabilities)
    signs = []
    labels = []
    for qubit in range(qubits):
        signs.append(eigenvalues_for_word("I" * (qubits - 1 - qubit) + "Z" + "I" * qubit))
        labels.append("Z{}".format(qubit))
    for qubit in range(qubits - 1):
        chars = ["I"] * qubits
        chars[qubits - 1 - qubit] = "Z"
        chars[qubits - 2 - qubit] = "Z"
        signs.append(eigenvalues_for_word("".join(chars)))
        labels.append("Z{}Z{}".format(qubit, qubit + 1))
    return probabilities, np.asarray(signs).T, x, y, classes, labels


def sampled_features(probabilities, signs, shots, rng):
    features = np.empty((probabilities.shape[0], signs.shape[1]), dtype=np.float64)
    for index, probs in enumerate(probabilities):
        counts = rng.multinomial(shots, probs)
        features[index] = counts @ signs / shots
    return features


def run_ml(row, shots_grid, replicates):
    probabilities, signs, _, labels, classes, feature_labels = ml_probabilities(row)
    split = int(round(len(labels) * 0.75))
    exact_features = probabilities @ signs
    exact_accuracy = train_softmax(
        exact_features[:split], labels[:split], exact_features[split:], labels[split:], classes
    )
    records = []
    for shots in shots_grid:
        values = []
        for replicate in range(replicates):
            rng = np.random.default_rng(as_int(row, "seed") * 1000003 + shots * 17 + replicate)
            features = sampled_features(probabilities, signs, shots, rng)
            values.append(train_softmax(
                features[:split], labels[:split], features[split:], labels[split:], classes
            ))
        records.append(quality_record(
            row,
            shots,
            values,
            native_quality=as_float(row, "native_quality"),
            gap=lambda quality: max(0.0, as_float(row, "native_quality") - quality),
            exact_quality=exact_accuracy,
            contract="computational-basis Z/nearest-neighbor-ZZ features with retrained softmax head",
            scope="physically_measurable_variant_not_same_feature_map",
            full_loop=True,
            extra={"measured_features": feature_labels},
        ))
    return records


def vqe_state(raw):
    workload = raw["workloads"]["chemistry"]
    qubits = int(workload["problem"]["n_qubits"])
    theta = workload["quantum_path"]["best_theta"]
    layers = int(workload["quantum_path"]["layers"])
    state = zero_state(qubits)
    index = 0
    for _ in range(layers):
        for qubit in range(qubits):
            apply_single(state, ry(float(theta[index])), qubit)
            index += 1
        for qubit in range(qubits - 1):
            apply_cnot(state, qubit, qubit + 1)
        for qubit in range(qubits):
            apply_single(state, rz(float(theta[index])), qubit)
            index += 1
    return state


def allocate_shots(total, weights):
    weights = np.asarray(weights, dtype=np.float64)
    weights = weights / weights.sum()
    raw = weights * total
    allocation = np.floor(raw).astype(int)
    allocation[allocation < 1] = 1
    difference = int(total - allocation.sum())
    if difference > 0:
        order = np.argsort(-(raw - np.floor(raw)))
        for index in order[:difference]:
            allocation[index] += 1
    elif difference < 0:
        order = np.argsort(-allocation)
        for index in order:
            if difference == 0:
                break
            removable = min(allocation[index] - 1, -difference)
            allocation[index] -= removable
            difference += removable
    if allocation.sum() != total:
        raise ValueError("shot allocation does not sum to budget")
    return allocation.tolist()


def qwc_compatible(term, basis):
    return all(left == "I" or left == right for left, right in zip(term, basis))


def chemistry_sampler(row, compiled):
    raw = json.loads((ROOT / row["path"]).read_text())
    state = vqe_state(raw)
    workload = raw["workloads"]["chemistry"]
    terms = workload["problem"]["terms"]
    bases = compiled["group_basis"]
    assignments = defaultdict(list)
    identity = 0.0
    exact_energy = 0.0
    for term in terms:
        word = term["pauli"].upper()
        coefficient = float(term["coefficient"])
        exact_energy += coefficient * expectation(state, word)
        if set(word) == {"I"}:
            identity += coefficient
            continue
        matches = [index for index, basis in enumerate(bases) if qwc_compatible(word, basis)]
        if not matches:
            raise ValueError("no QWC group for {}".format(word))
        assignments[matches[0]].append((word, coefficient, eigenvalues_for_word(word)))
    reported = float(workload["quantum_path"]["estimated_ground_energy"])
    if abs(exact_energy - reported) > 1.0e-8:
        raise ValueError("reconstructed chemistry energy mismatch: {} vs {}".format(exact_energy, reported))
    probabilities = [basis_probabilities(state, basis) for basis in bases]

    def sample(shots, rng):
        allocation = allocate_shots(shots, compiled["group_coefficient_l1_weights"])
        energy = identity
        for index, group_shots in enumerate(allocation):
            counts = rng.multinomial(group_shots, probabilities[index])
            for _, coefficient, eigenvalues in assignments[index]:
                energy += coefficient * float(counts @ eigenvalues / group_shots)
        return energy, allocation

    return exact_energy, sample


def run_chemistry(row, compiled, shots_grid, replicates):
    exact_energy, sampler = chemistry_sampler(row, compiled)
    records = []
    for shots in shots_grid:
        values = []
        allocation = None
        for replicate in range(replicates):
            rng = np.random.default_rng(as_int(row, "seed") * 1000033 + shots * 19 + replicate)
            value, allocation = sampler(shots, rng)
            values.append(value)
        records.append(quality_record(
            row,
            shots,
            values,
            native_quality=as_float(row, "native_quality"),
            gap=lambda quality: abs(quality - as_float(row, "native_quality")),
            exact_quality=exact_energy,
            contract="QWC Pauli-energy sampling with coefficient-L1 shot allocation",
            scope="same_record_fixed_parameter_output",
            full_loop=False,
            extra={
                "measurement_groups": len(compiled["group_basis"]),
                "shots_by_group": allocation,
                "outer_optimizer_sampling": "not covered",
            },
        ))
    return records


def qaoa_state(raw):
    workload = raw["workloads"]["optimization"]
    qubits = int(workload["problem"]["nodes"])
    beta = float(workload["quantum_path"]["best_beta"])
    gamma = float(workload["quantum_path"]["best_gamma"])
    state = zero_state(qubits)
    for qubit in range(qubits):
        apply_single(state, H, qubit)
    for left, right in workload["problem"]["edges"]:
        apply_rzz(state, int(left), int(right), -gamma)
    for qubit in range(qubits):
        apply_single(state, rx(2.0 * beta), qubit)
    return state


def cut_values(qubits, edges):
    values = np.zeros(1 << qubits, dtype=np.float64)
    for basis in range(1 << qubits):
        values[basis] = sum(
            ((basis >> int(left)) & 1) != ((basis >> int(right)) & 1)
            for left, right in edges
        )
    return values


def run_optimization(row, shots_grid, replicates):
    raw = json.loads((ROOT / row["path"]).read_text())
    workload = raw["workloads"]["optimization"]
    state = qaoa_state(raw)
    probabilities = np.abs(state) ** 2
    values = cut_values(int(workload["problem"]["nodes"]), workload["problem"]["edges"])
    native = float(workload["native_path"]["best_cut"])
    exact_ratio = float(probabilities @ values / native)
    reported = float(workload["quantum_path"]["approximation_ratio"])
    if abs(exact_ratio - reported) > 1.0e-8:
        raise ValueError("reconstructed QAOA ratio mismatch")
    records = []
    for shots in shots_grid:
        sampled = []
        for replicate in range(replicates):
            rng = np.random.default_rng(as_int(row, "seed") * 1000037 + shots * 23 + replicate)
            counts = rng.multinomial(shots, probabilities)
            sampled.append(float(counts @ values / shots / native))
        records.append(quality_record(
            row,
            shots,
            sampled,
            native_quality=1.0,
            gap=lambda quality: max(0.0, 1.0 - quality),
            exact_quality=exact_ratio,
            contract="computational-basis MaxCut sampling at selected parameters",
            scope="same_record_fixed_parameter_output",
            full_loop=False,
            extra={"finite_shot_parameter_search": "not covered"},
        ))
    return records


def run_simulation(row, shots_grid, replicates):
    raw = json.loads((ROOT / row["path"]).read_text())
    workload = raw["workloads"]["simulation"]
    exact = float(workload["quantum_path"]["z0_expectation"])
    native = float(workload["native_path"]["z0_expectation"])
    probability_plus = min(1.0, max(0.0, (1.0 + exact) / 2.0))
    records = []
    for shots in shots_grid:
        values = []
        for replicate in range(replicates):
            rng = np.random.default_rng(as_int(row, "seed") * 1000039 + shots * 29 + replicate)
            plus = rng.binomial(shots, probability_plus)
            values.append(2.0 * plus / shots - 1.0)
        records.append(quality_record(
            row,
            shots,
            values,
            native_quality=native,
            gap=lambda quality: abs(quality - native),
            exact_quality=exact,
            contract="terminal Z0 Bernoulli sampling",
            scope="same_record_full_application_output",
            full_loop=True,
            extra={},
        ))
    return records


def quality_record(row, shots, qualities, native_quality, gap, exact_quality, contract, scope, full_loop, extra):
    gaps = [float(gap(value)) for value in qualities]
    tolerance = TOLERANCES[row["workload"]]
    passes = [value <= tolerance for value in gaps]
    return {
        "source_record_id": record_id(row),
        "source_path": row["path"],
        "workload": row["workload"],
        "seed": as_int(row, "seed"),
        "base_seed": base_seed(row),
        "shots": int(shots),
        "replicates": len(qualities),
        "native_quality": float(native_quality),
        "exact_quantum_quality": float(exact_quality),
        "sampled_quality_median": median(qualities),
        "sampled_quality_ci_95": percentile_interval(qualities),
        "quality_gap_median": median(gaps),
        "quality_gap_ci_95": percentile_interval(gaps),
        "quality_tolerance": tolerance,
        "quality_pass_probability": sum(passes) / len(passes),
        "same_record_quality_shot_trace": scope.startswith("same_record"),
        "full_algorithm_loop_covered": bool(full_loop),
        "measurement_contract": contract,
        "evidence_scope": scope,
        "replicate_quality": [float(value) for value in qualities],
        "replicate_quality_gap": gaps,
        **extra,
    }


def load_controlled_chem(path):
    artifact = json.loads(Path(path).read_text())
    return {
        (row["fixture"], int(row["layers"])): row
        for row in artifact["records"]
        if row.get("evidence_level") == "compiled_executed_ansatz"
    }


def chem_key(row):
    fixture = Path(row.get("chem_hamiltonian_json", "")).name
    return (
        "molecular_chain_4q_surrogate" if fixture else "H2_minimal_2qubit",
        as_int(row, "chem_layers"),
    )


def select_rows(rows):
    round_zero = [row for row in rows if repeat_round(row) == 0]
    selected = []
    selected.extend(
        row for row in round_zero
        if row["workload"] == "ml"
        and row["digits_classes"] == "0,1,2"
        and as_int(row, "ml_samples") == 256
        and as_int(row, "ml_features") == 8
        and as_int(row, "ml_depth") == 2
    )
    chem = [row for row in round_zero if row["workload"] == "chemistry"]
    chem_groups = defaultdict(list)
    for row in chem:
        fixture = Path(row.get("chem_hamiltonian_json", "")).name or "h2"
        chem_groups[(fixture, base_seed(row))].append(row)
    # Select the best measured ansatz/search point for each fixture and base
    # seed. This deliberately includes the noiseless H2 pass cases needed to
    # test whether finite sampling preserves their application-quality gate.
    selected.extend(
        min(values, key=lambda row: as_float(row, "quality_gap"))
        for values in chem_groups.values()
    )
    selected.extend(
        row for row in round_zero
        if row["workload"] == "optimization"
        and as_int(row, "opt_nodes") in (4, 7)
        and as_int(row, "opt_grid") == 13
    )
    selected.extend(
        row for row in round_zero
        if row["workload"] == "simulation"
        and as_int(row, "sim_qubits") in (4, 7)
        and as_int(row, "sim_steps") in (4, 10)
    )
    return selected


def summarize(records):
    by_workload_shots = {}
    for workload in sorted({row["workload"] for row in records}):
        by_workload_shots[workload] = {}
        for shots in sorted({row["shots"] for row in records if row["workload"] == workload}):
            subset = [row for row in records if row["workload"] == workload and row["shots"] == shots]
            by_workload_shots[workload][str(shots)] = {
                "cases": len(subset),
                "median_quality_gap": median(row["quality_gap_median"] for row in subset),
                "p90_quality_gap": quantile((row["quality_gap_median"] for row in subset), 0.9),
                "mean_quality_pass_probability": sum(row["quality_pass_probability"] for row in subset) / len(subset),
                "cases_with_pass_probability_ge_0p9": sum(row["quality_pass_probability"] >= 0.9 for row in subset),
                "same_record_cases": sum(row["same_record_quality_shot_trace"] for row in subset),
                "full_loop_cases": sum(row["full_algorithm_loop_covered"] for row in subset),
            }
    return by_workload_shots


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT))
    parser.add_argument(
        "--chem-compiled",
        default=(
            "data/processed/perlmutter/"
            "chem_controlled_compiled_measurement_records.json"
        ),
    )
    parser.add_argument("--shots", default="1000,10000,100000")
    parser.add_argument("--replicates", type=int, default=12)
    parser.add_argument("--output-json", default=str(OUTPUT))
    parser.add_argument("--output-csv", default=str(OUTPUT.with_suffix(".csv")))
    args = parser.parse_args()

    shots_grid = [int(value) for value in args.shots.split(",")]
    rows = read_rows(args.input_csv)
    selected = select_rows(rows)
    chem_compiled = load_controlled_chem(ROOT / args.chem_compiled)
    records = []
    for row in selected:
        if row["workload"] == "ml":
            records.extend(run_ml(row, shots_grid, args.replicates))
        elif row["workload"] == "chemistry":
            records.extend(run_chemistry(row, chem_compiled[chem_key(row)], shots_grid, args.replicates))
        elif row["workload"] == "optimization":
            records.extend(run_optimization(row, shots_grid, args.replicates))
        elif row["workload"] == "simulation":
            records.extend(run_simulation(row, shots_grid, args.replicates))

    expected_shots = set(shots_grid)
    internal_errors = []
    for source in {row["source_record_id"] for row in records}:
        if {row["shots"] for row in records if row["source_record_id"] == source} != expected_shots:
            internal_errors.append("incomplete shot grid for {}".format(source))
    if set(row["workload"] for row in records) != set(TOLERANCES):
        internal_errors.append("not every workload is represented")

    payload = {
        "schema": "qarchgauge.finite-shot-quality-sensitivity.v1",
        "audit_status": "FAIL" if internal_errors else "PASS",
        "scope": (
            "Representative finite-shot quality closure at 1e3/1e4/1e5 shots. "
            "ML uses a physically measurable Z/ZZ variant; Chem and Opt sample "
            "fixed selected parameters and do not claim a finite-shot outer "
            "optimizer; Sim samples the complete terminal observable."
        ),
        "input_csv": relative(args.input_csv),
        "shot_grid": shots_grid,
        "replicates_per_case": args.replicates,
        "selected_source_records": len({row["source_record_id"] for row in records}),
        "selected_by_workload": dict(Counter(row["workload"] for row in selected)),
        "summary": summarize(records),
        "records": records,
        "internal_errors": internal_errors,
    }
    json_dump(args.output_json, payload)

    csv_rows = []
    for row in records:
        csv_rows.append({key: value for key, value in row.items() if not isinstance(value, (list, dict))})
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in csv_rows for key in row})
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(csv_rows)

    print(json.dumps({
        "output_json": relative(args.output_json),
        "output_csv": relative(args.output_csv),
        "audit_status": payload["audit_status"],
        "selected_by_workload": payload["selected_by_workload"],
        "summary": payload["summary"],
    }, indent=2, sort_keys=True))
    if internal_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
