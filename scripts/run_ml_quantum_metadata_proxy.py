#!/usr/bin/env python3
"""Map the measured CIFAR-10 native schedule to quantum-loading metadata."""

import argparse
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--native", default="data/processed/perlmutter/ml_cifar10_resnet18_proxy.json"
    )
    parser.add_argument(
        "--output", default="data/processed/perlmutter/ml_quantum_metadata_proxy.json"
    )
    parser.add_argument("--qnn-layers", type=int, default=3)
    args = parser.parse_args()

    native = json.loads(Path(args.native).read_text())
    pixels = 32 * 32 * 3
    train_image_uses = native["train_samples"] * native["epochs"]
    test_image_uses = native["test_samples"] * native["epochs"]
    total_image_uses = train_image_uses + test_image_uses
    amplitude_qubits = math.ceil(math.log2(pixels))
    amplitude_dimension = 1 << amplitude_qubits
    generic_state_prep_rotations = amplitude_dimension - 1
    qnn_two_qubit_per_image = amplitude_qubits * args.qnn_layers
    qnn_one_qubit_per_image = amplitude_qubits * args.qnn_layers

    output = {
        "schema": "qsup.ml-quantum-metadata-proxy.v1",
        "scope": (
            "same CIFAR-10 schedule mapped to two loading contracts; no quantum "
            "image-classification quality or executable 12/3072-qubit run is claimed"
        ),
        "native_artifact": args.native,
        "dataset": native["dataset"],
        "pixels_per_image": pixels,
        "train_image_uses": train_image_uses,
        "test_image_uses": test_image_uses,
        "total_image_uses": total_image_uses,
        "angle_encoding": {
            "qubits": pixels,
            "data_rotations_per_image": pixels,
            "total_data_rotations": pixels * total_image_uses,
            "boundary": "width-prohibitive direct pixel encoding",
        },
        "amplitude_encoding": {
            "qubits": amplitude_qubits,
            "state_dimension": amplitude_dimension,
            "generic_state_prep_rotations_per_image_upper_contract": generic_state_prep_rotations,
            "total_state_prep_rotations_upper_contract": (
                generic_state_prep_rotations * total_image_uses
            ),
            "qnn_layers": args.qnn_layers,
            "qnn_one_qubit_gates_per_image": qnn_one_qubit_per_image,
            "qnn_two_qubit_gates_per_image": qnn_two_qubit_per_image,
            "total_qnn_two_qubit_gates": qnn_two_qubit_per_image * total_image_uses,
            "boundary": "compact width but generic state preparation and repeated image loading dominate",
        },
        "remaining_quality_gate": (
            "train and evaluate a quantum image model on the same split to compare "
            "against 0.8185 native test accuracy"
        ),
    }
    path = Path(args.output)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({
        "total_image_uses": total_image_uses,
        "angle_qubits": pixels,
        "amplitude_qubits": amplitude_qubits,
        "amplitude_state_prep_rotations": output["amplitude_encoding"]["total_state_prep_rotations_upper_contract"],
        "output": str(path),
    }, indent=2))


if __name__ == "__main__":
    main()
