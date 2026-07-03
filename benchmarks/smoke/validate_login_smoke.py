#!/usr/bin/env python3
"""Validate login-node smoke test outputs."""

import argparse
import json
import math
import sys


def load(path):
    with open(path) as f:
        return json.load(f)


def validate_statevector(path):
    data = load(path)
    errors = []
    numpy_result = data.get("numpy_statevector", {})
    if numpy_result.get("status") != "ok":
        errors.append("{}: numpy_statevector not ok".format(path))
    norm = numpy_result.get("checksum", {}).get("norm")
    if norm is None or not math.isclose(norm, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        errors.append("{}: numpy norm invalid {}".format(path, norm))

    cusv = data.get("custatevec_statevector")
    if cusv is not None:
        if cusv.get("status") != "ok":
            errors.append("{}: custatevec_statevector not ok".format(path))
        q_norm = cusv.get("checksum", {}).get("norm")
        if q_norm is None or not math.isclose(q_norm, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            errors.append("{}: custatevec norm invalid {}".format(path, q_norm))
    return errors


def validate_ml(path, min_native_acc, min_quantum_acc):
    data = load(path)
    errors = []
    native = data.get("native_ml_path", {})
    quantum = data.get("quantum_circuit_ml_path", {})
    if quantum.get("status") != "ok":
        errors.append("{}: quantum path not ok: {}".format(path, quantum.get("error")))
    native_acc = native.get("test_accuracy", -1.0)
    quantum_acc = quantum.get("test_accuracy", -1.0)
    if native_acc < min_native_acc:
        errors.append("{}: native acc {} < {}".format(path, native_acc, min_native_acc))
    if quantum_acc < min_quantum_acc:
        errors.append("{}: quantum acc {} < {}".format(path, quantum_acc, min_quantum_acc))
    if native.get("runtime_sec", 0.0) <= 0.0:
        errors.append("{}: native runtime missing".format(path))
    if quantum.get("total_runtime_sec", 0.0) <= 0.0:
        errors.append("{}: quantum runtime missing".format(path))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--statevector", action="append", default=[])
    parser.add_argument("--ml", action="append", default=[])
    parser.add_argument("--min-native-acc", type=float, default=0.8)
    parser.add_argument("--min-quantum-acc", type=float, default=0.75)
    args = parser.parse_args()

    errors = []
    for path in args.statevector:
        errors.extend(validate_statevector(path))
    for path in args.ml:
        errors.extend(validate_ml(path, args.min_native_acc, args.min_quantum_acc))

    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1

    print("PASS: login smoke outputs validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
