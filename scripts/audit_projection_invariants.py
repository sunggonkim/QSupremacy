#!/usr/bin/env python3
"""Verify accounting and monotonicity invariants of the projection model."""

import csv
import json
import math
import os

from hpca_projection_model import (
    merge_config,
    native_deadline_sec,
    projected_components_sec,
)


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT = os.path.join(
    ROOT,
    "data/processed/perlmutter/"
    "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv",
)
OUTPUT = os.path.join(
    ROOT, "data/processed/perlmutter/projection_invariant_audit.json"
)
BATCHES = (1, 4, 16, 64)


def close(left, right, rel=1.0e-10, abs_=1.0e-12):
    return math.isclose(left, right, rel_tol=rel, abs_tol=abs_)


def mechanism_total(components, evaluations, batch):
    rounds = math.ceil(evaluations / float(batch))
    round_fraction = rounds / evaluations
    fixed = (
        components["critical_gate_sec"]
        + components["critical_decode_sec"]
        + components["controller_sec"]
    )
    feedback = round_fraction * (
        components["host_io_sec"]
        + components["queue_sec"]
        + components["context_sec"]
    )
    return fixed + feedback


def main():
    with open(INPUT, newline="") as source:
        rows = [row for row in csv.DictReader(source) if row.get("status") == "ok"]

    failures = {
        "nonnegative_components": [],
        "component_accounting": [],
        "ideal_overlap_exclusivity": [],
        "overlap_endpoint_identity": [],
        "overlap_serialization_monotonicity": [],
        "shot_lane_monotonicity": [],
        "shot_demand_monotonicity": [],
        "decoder_shot_demand_monotonicity": [],
        "measurement_group_demand_monotonicity": [],
        "routing_dilation_monotonicity": [],
        "factory_supply_monotonicity": [],
        "total_shot_execution_identity": [],
        "shot_lane_demand_cap": [],
        "shot_lane_ready_cap": [],
        "queue_service_monotonicity": [],
        "batch_one_identity": [],
        "batch_monotonicity": [],
    }
    component_keys = (
        "critical_gate_sec",
        "critical_decode_sec",
        "host_io_sec",
        "queue_sec",
        "controller_sec",
        "context_sec",
    )

    for index, row in enumerate(rows):
        identity = row.get("file", str(index))
        base = projected_components_sec(row)
        if any(base[key] < 0.0 for key in component_keys):
            failures["nonnegative_components"].append(identity)

        reconstructed = sum(base[key] for key in component_keys)
        if not close(base["total_sec"], reconstructed):
            failures["component_accounting"].append(identity)

        if base["critical_gate_sec"] > 0.0 and base["critical_decode_sec"] > 0.0:
            failures["ideal_overlap_exclusivity"].append(identity)

        overlap_zero = projected_components_sec(
            row, {"critical_path_serialization_fraction": 0.0}
        )
        overlap_half = projected_components_sec(
            row, {"critical_path_serialization_fraction": 0.5}
        )
        overlap_full = projected_components_sec(
            row, {"critical_path_serialization_fraction": 1.0}
        )
        raw_core = (
            overlap_zero["gate_pipeline_sec"]
            + overlap_zero["factory_sec"]
            + overlap_zero["decode_sec"]
        )
        if (
            not close(
                overlap_zero["core_overlap_lower_bound_sec"],
                max(
                    overlap_zero["gate_pipeline_sec"],
                    overlap_zero["factory_sec"],
                    overlap_zero["decode_sec"],
                ),
            )
            or not close(overlap_full["core_serialized_upper_bound_sec"], raw_core)
            or not close(overlap_zero["core_overlap_penalty_sec"], 0.0)
            or not close(
                overlap_full["core_overlap_penalty_sec"],
                raw_core - overlap_full["core_overlap_lower_bound_sec"],
            )
        ):
            failures["overlap_endpoint_identity"].append(identity)
        if not (
            overlap_zero["total_sec"] <= overlap_half["total_sec"] + 1.0e-15
            and overlap_half["total_sec"] <= overlap_full["total_sec"] + 1.0e-15
        ):
            failures["overlap_serialization_monotonicity"].append(identity)

        low_lanes = projected_components_sec(row, {"shot_lanes": 1.0e2})
        high_lanes = projected_components_sec(row, {"shot_lanes": 1.0e6})
        if high_lanes["gate_sec"] > low_lanes["gate_sec"] + 1.0e-15:
            failures["shot_lane_monotonicity"].append(identity)

        low_shots = projected_components_sec(
            row, {"shots_per_group": 1.0e2, "shot_lanes": 1.0e2}
        )
        high_shots = projected_components_sec(
            row, {"shots_per_group": 1.0e4, "shot_lanes": 1.0e2}
        )
        if high_shots["gate_sec"] + 1.0e-15 < low_shots["gate_sec"]:
            failures["shot_demand_monotonicity"].append(identity)

        evaluations = max(1.0, float(row.get("circuit_evaluations") or 1.0))
        groups = max(1.0, float(row.get("measurement_groups_per_eval") or 1.0))
        if high_shots["decode_sec"] + 1.0e-15 < low_shots["decode_sec"]:
            failures["decoder_shot_demand_monotonicity"].append(identity)
        one_group_row = dict(row, measurement_groups_per_eval=1.0)
        four_group_row = dict(row, measurement_groups_per_eval=4.0)
        one_group = projected_components_sec(one_group_row, {"shot_lanes": 1.0e2})
        four_groups = projected_components_sec(four_group_row, {"shot_lanes": 1.0e2})
        if (
            four_groups["gate_sec"] + 1.0e-15 < one_group["gate_sec"]
            or four_groups["decode_sec"] + 1.0e-15 < one_group["decode_sec"]
        ):
            failures["measurement_group_demand_monotonicity"].append(identity)
        local_route = projected_components_sec(
            row, {"shot_lanes": 1.0e2, "twoq_routing_multiplier": 1.0}
        )
        dilated_route = projected_components_sec(
            row, {"shot_lanes": 1.0e2, "twoq_routing_multiplier": 4.0}
        )
        if dilated_route["gate_pipeline_sec"] + 1.0e-15 < local_route["gate_pipeline_sec"]:
            failures["routing_dilation_monotonicity"].append(identity)
        abundant_factory = projected_components_sec(
            row,
            {
                "magic_states_per_twoq_proxy": 1.0,
                "magic_state_factory_rate_per_sec": 1.0e30,
            },
        )
        constrained_factory = projected_components_sec(
            row,
            {
                "magic_states_per_twoq_proxy": 1.0,
                "magic_state_factory_rate_per_sec": 1.0,
            },
        )
        if constrained_factory["gate_sec"] + 1.0e-15 < abundant_factory["gate_sec"]:
            failures["factory_supply_monotonicity"].append(identity)
        if not close(
            high_shots["total_shot_executions"],
            evaluations * groups * high_shots["shots_per_group"],
        ):
            failures["total_shot_execution_identity"].append(identity)
        demand = 1.0e4 * groups * evaluations
        saturated = projected_components_sec(
            row, {"shots_per_group": 1.0e4, "shot_lanes": demand}
        )
        oversubscribed = projected_components_sec(
            row, {"shots_per_group": 1.0e4, "shot_lanes": 10.0 * demand}
        )
        if not close(saturated["gate_sec"], oversubscribed["gate_sec"]):
            failures["shot_lane_demand_cap"].append(identity)
        ready_row = dict(row, ready_shot_executions=17.0)
        ready_cap = projected_components_sec(ready_row, {"shot_lanes": 17.0})
        ready_over = projected_components_sec(ready_row, {"shot_lanes": 1700.0})
        if (
            not close(ready_cap["effective_shot_lanes"], 17.0)
            or not close(ready_over["effective_shot_lanes"], 17.0)
            or not close(ready_cap["gate_sec"], ready_over["gate_sec"])
            or ready_over["shot_lane_evidence"] != "compiled_dependency_wave"
        ):
            failures["shot_lane_ready_cap"].append(identity)

        high_queue = projected_components_sec(
            row,
            {"queue_service_sec_per_eval": 40.0e-6, "queue_utilization": 0.70},
        )
        low_queue = projected_components_sec(
            row,
            {"queue_service_sec_per_eval": 5.0e-6, "queue_utilization": 0.20},
        )
        if low_queue["queue_sec"] > high_queue["queue_sec"] + 1.0e-15:
            failures["queue_service_monotonicity"].append(identity)

        batch_totals = [mechanism_total(base, evaluations, batch) for batch in BATCHES]
        if not close(batch_totals[0], base["total_sec"]):
            failures["batch_one_identity"].append(identity)
        if any(
            right > left + 1.0e-15
            for left, right in zip(batch_totals, batch_totals[1:])
        ):
            failures["batch_monotonicity"].append(identity)

    measured_row = {"native_runtime_sec": 1.0}
    stressed_row = {
        "native_runtime_sec": 1.0,
        "native_roofline_flops": 1.0e14,
        "native_roofline_bytes": 1.0,
    }
    measured_deadline = native_deadline_sec(measured_row, merge_config())
    stressed_deadline = native_deadline_sec(
        stressed_row,
        merge_config({
            "native_peak_flops": 1.0e15,
            "native_peak_bytes_per_sec": 1.0e15,
            "native_tensor_core_peak_flops": 1.0e15,
            "native_hbm_bandwidth_bytes_per_sec": 1.0e15,
            "native_launch_floor_sec": 0.0,
        }),
    )
    stronger_native_passed = stressed_deadline <= measured_deadline

    checks = []
    for name, identities in failures.items():
        checks.append(
            {
                "name": name,
                "passed": not identities,
                "failure_count": len(identities),
                "examples": identities[:5],
            }
        )
    checks.append(
        {
            "name": "stronger_native_never_eases_deadline",
            "passed": stronger_native_passed,
            "measured_deadline_sec": measured_deadline,
            "stressed_deadline_sec": stressed_deadline,
        }
    )
    result = {
        "schema": "qsup.projection-invariant-audit.v3",
        "input": os.path.relpath(INPUT, ROOT),
        "cases": len(rows),
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
    }
    with open(OUTPUT, "w") as destination:
        json.dump(result, destination, indent=2)
        destination.write("\n")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
