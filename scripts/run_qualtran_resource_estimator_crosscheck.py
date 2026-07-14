#!/usr/bin/env python3
"""Cross-check matched QAOA logical counts with Google Qualtran cost models."""

import argparse
import importlib.metadata
import json
from pathlib import Path

from qualtran.resource_counting import GateCounts
from qualtran.surface_code import AlgorithmSummary, PhysicalCostModel


MODELS = {
    "gidney_fowler_d25": PhysicalCostModel.make_gidney_fowler,
    "beverland_d25": PhysicalCostModel.make_beverland_et_al,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--qdk-artifact",
        default="data/processed/perlmutter/qdk_resource_estimator_qaoa_crosscheck.json",
    )
    parser.add_argument(
        "--output",
        default="data/processed/perlmutter/qualtran_resource_estimator_qaoa_crosscheck.json",
    )
    args = parser.parse_args()

    qdk = json.loads(Path(args.qdk_artifact).read_text())
    output = {
        "schema": "qsup.qualtran-resource-estimator-crosscheck.v1",
        "scope": (
            "independent Qualtran surface-code cross-check using the matched logical "
            "rotation/measurement counts reported by QDK; one p=1 QAOA circuit per "
            "size, excluding shots, parameter search, host/control tails, and "
            "application-quality recovery"
        ),
        "source_artifact": args.qdk_artifact,
        "software": {"qualtran": importlib.metadata.version("qualtran")},
        "data_code_distance": 25,
        "records": [],
    }

    for qdk_record in qdk["records"]:
        logical = qdk_record["estimates"]["qubit_gate_ns_e3"]["input_logical_counts"]
        algorithm = AlgorithmSummary(
            n_algo_qubits=int(logical["qubits"]),
            n_logical_gates=GateCounts(
                t=int(logical["t_count"]),
                rotation=int(logical["rotation_count"]),
                measurement=int(logical["measurement_count"]),
            ),
            n_rotation_layers=int(logical["rotation_depth"]),
        )
        record = {
            "nodes_qubits": int(qdk_record["nodes_qubits"]),
            "density": float(qdk_record["density"]),
            "seed": int(qdk_record["seed"]),
            "edges": int(qdk_record["edges"]),
            "logical_input": logical,
            "models": {},
        }
        for name, constructor in MODELS.items():
            model = constructor(data_d=25)
            record["models"][name] = {
                "duration_hr": float(model.duration_hr(algorithm)),
                "duration_sec": float(model.duration_hr(algorithm) * 3600.0),
                "physical_qubits": int(model.n_phys_qubits(algorithm)),
                "estimated_failure_probability": float(model.error(algorithm)),
            }
        output["records"].append(record)

    path = Path(args.output)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"output": str(path), "records": len(output["records"])}, indent=2))


if __name__ == "__main__":
    main()
