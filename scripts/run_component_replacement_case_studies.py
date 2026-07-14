#!/usr/bin/env python3
"""Apply current architecture mechanisms to matched QArchGauge events.

The LSQCA study consumes each workload's logical-operand reference stream and
replaces only core floorplan/movement terms.  The BOSS-compatible study consumes
the ordered two-qubit interaction stream and reports the paper's analytical
shuttle/SWAP/recooling bounds.  Neither study borrows a published average
speedup, and neither is presented as a reimplementation of the authors' full
simulator.
"""

import argparse
import csv
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import audit_ft_reliability_budget as ft
from strong_accept_common import (
    DEFAULT_INPUT,
    ROOT,
    as_int,
    json_dump,
    median,
    quantile,
    read_rows,
    record_id,
    relative,
    structural_config_id,
)


DEFAULT_OUTPUT = ROOT / "data/processed/perlmutter/component_replacement_case_studies.json"
DEFAULT_FT = ROOT / "data/processed/perlmutter/ft_reliability_and_space_budget.json"
DEFAULT_SCHEDULE = ROOT / "data/processed/perlmutter/dependency_schedule_coverage.csv"


def read_schedule(path):
    with Path(path).open(newline="") as handle:
        return {row["record_id"]: row for row in csv.DictReader(handle)}


def one_circuit_events(row, raw, config):
    """Return ordered high-level logical operations for the implemented path."""
    workload = row["workload"]
    qubits = ft.logical_qubits(row)
    events = []
    if workload == "ml":
        depth = as_int(row, "ml_depth", 1)
        for _ in range(depth):
            for qubit in range(qubits):
                events.append(("Ry", (qubit,)))
                events.append(("Rz", (qubit,)))
            if bool(config.get("entangle", True)):
                for qubit in range(qubits - 1):
                    events.append(("CNOT", (qubit, qubit + 1)))
        scope = "one implemented ML feature circuit; repeated over samples"
    elif workload == "chemistry":
        layers = as_int(row, "chem_layers", 1)
        for _ in range(layers):
            for qubit in range(qubits):
                events.append(("Ry", (qubit,)))
            if bool(config.get("entangle", True)):
                for qubit in range(qubits - 1):
                    events.append(("CNOT", (qubit, qubit + 1)))
            for qubit in range(qubits):
                events.append(("Rz", (qubit,)))
        scope = (
            "one executed hardware-efficient ansatz; QWC basis-change references "
            "are excluded and flagged"
        )
    elif workload == "optimization":
        for qubit in range(qubits):
            events.append(("H", (qubit,)))
        for left, right in raw["problem"]["edges"]:
            events.append(("RZZ", (int(left), int(right))))
        for qubit in range(qubits):
            events.append(("Rx", (qubit,)))
        scope = "one implemented p=1 QAOA circuit; repeated over the static grid"
    else:
        steps = int(raw["problem"]["steps"])
        model = raw["problem"]["name"]
        for _ in range(steps):
            if model == "tfim":
                for qubit in range(qubits - 1):
                    events.append(("RZZ", (qubit, qubit + 1)))
            else:
                for qubit in range(qubits - 1):
                    events.extend((
                        ("RXX", (qubit, qubit + 1)),
                        ("RYY", (qubit, qubit + 1)),
                        ("RZZ", (qubit, qubit + 1)),
                    ))
            for qubit in range(qubits):
                events.append(("R1", (qubit,)))
        scope = "one implemented Trotter circuit"
    return events, scope


def repeat_events(events, evaluations):
    for _ in range(max(1, int(evaluations))):
        yield from events


def point_sam_trace(events, qubits, two_qubit_only=False):
    """Two-entry CR/LRU envelope with LSQCA's point-SAM worst-case load."""
    cache = []
    references = 0
    loads = 0
    stores = 0
    hits = 0
    load_beats = int(math.ceil(7.0 * math.sqrt(qubits)))
    for _, operands in events:
        if two_qubit_only and len(operands) == 1:
            continue
        for operand in operands:
            references += 1
            if operand in cache:
                hits += 1
                cache.remove(operand)
                cache.append(operand)
                continue
            loads += 1
            if len(cache) == 2:
                cache.pop(0)
                stores += 1
            cache.append(operand)
    stores += len(cache)
    movement_beats = (loads + stores) * load_beats
    return {
        "operand_references": references,
        "cr_hits": hits,
        "cr_misses": loads,
        "loads": loads,
        "stores": stores,
        "cr_hit_fraction": hits / max(1, references),
        "worst_case_beats_per_load_or_store": load_beats,
        "movement_code_beats": movement_beats,
    }


def ft_default_index(path):
    artifact = json.loads(Path(path).read_text())
    index = {}
    for record in artifact["quality_qualified_case_contracts"]:
        selected = next(
            contract["reliability_leading_term"]
            for contract in record["ft_contracts"]
            if contract["contract"]["contract"] == "strict_all_shots"
            and contract["contract"]["application_failure_budget"] == 0.01
            and contract["physical_error_rate"] == 1.0e-3
        )
        index[record["record_id"]] = selected
    return index, artifact


def lsqca_replacement(row, contract, events, ft_record=None):
    qubits = ft.logical_qubits(row)
    eval_events = list(repeat_events(events, contract["evaluations"]))
    lower = point_sam_trace(eval_events, qubits, two_qubit_only=True)
    upper = point_sam_trace(eval_events, qubits, two_qubit_only=False)
    conventional_cells = int(math.ceil(qubits / 0.5))
    point_sam_cells = qubits + 1 + 6
    result = {
        "logical_qubits": qubits,
        "conventional_core_cells": conventional_cells,
        "conventional_memory_density": 0.5,
        "point_sam_core_cells": point_sam_cells,
        "point_sam_memory_density": qubits / point_sam_cells,
        "point_sam_core_cell_change_vs_conventional": point_sam_cells - conventional_cells,
        "point_sam_reduces_core_cells": point_sam_cells < conventional_cells,
        "point_sam_break_even_logical_qubits": 7,
        "in_memory_single_qubit_lower_envelope": lower,
        "all_operands_loaded_upper_envelope": upper,
        "invariants": {
            "quality_unchanged": True,
            "logical_error_contract_unchanged": True,
            "rotation_and_factory_demand_unchanged": True,
            "native_deadline_unchanged": True,
            "changed_terms": ["core logical cells", "load/store movement"],
        },
    }
    if ft_record is not None:
        logical_cycle = float(ft_record["logical_cycle_sec"])
        shot_scale = (
            contract["shot_executions_per_evaluation"]
            / contract["effective_shot_lanes"]
        )
        lower_sec = lower["movement_code_beats"] * logical_cycle * shot_scale
        upper_sec = upper["movement_code_beats"] * logical_cycle * shot_scale
        baseline_nonfactory = float(ft_record["nonfactory_floor_sec"])
        result["quality_qualified_ft_integration"] = {
            "distance": ft_record["distance"],
            "baseline_nonfactory_floor_sec": baseline_nonfactory,
            "movement_lower_sec": lower_sec,
            "movement_upper_sec": upper_sec,
            "nonfactory_floor_with_lower_movement_sec": baseline_nonfactory + lower_sec,
            "nonfactory_floor_with_upper_movement_sec": baseline_nonfactory + upper_sec,
            "native_deadline_sec": ft_record["native_deadline_sec"],
            "runtime_parity_possible_with_lower_movement": (
                baseline_nonfactory + lower_sec < ft_record["native_deadline_sec"]
            ),
            "runtime_parity_possible_with_upper_movement": (
                baseline_nonfactory + upper_sec < ft_record["native_deadline_sec"]
            ),
        }
    return result


def greedy_boss_blocks(twoq_events, capacity):
    blocks = []
    current_events = []
    current_qubits = set()
    for operands in twoq_events:
        operands = tuple(operands)
        combined = current_qubits | set(operands)
        if current_events and len(combined) > capacity:
            blocks.append({
                "events": list(current_events),
                "active_qubits": sorted(current_qubits),
            })
            current_events = []
            current_qubits = set()
        current_events.append(operands)
        current_qubits.update(operands)
    if current_events:
        blocks.append({
            "events": list(current_events),
            "active_qubits": sorted(current_qubits),
        })
    return blocks


def boss_envelope(events, qubits, capacity, force_one_gate_blocks=False):
    interactions = [operands for _, operands in events if len(operands) == 2]
    if force_one_gate_blocks:
        blocks = [
            {"events": [tuple(operands)], "active_qubits": sorted(operands)}
            for operands in interactions
        ]
    else:
        blocks = greedy_boss_blocks(interactions, capacity)
    block_count = len(blocks)
    if qubits <= capacity or block_count <= 1:
        shuttle_upper = 0
    else:
        shuttle_upper = int(math.ceil(2.0 * qubits * block_count / capacity))
    swap_upper = int(math.floor(capacity / 2.0) * shuttle_upper)
    return {
        "two_qubit_interactions": len(interactions),
        "execution_zone_qubits": capacity,
        "fifo_blocks": block_count,
        "block_active_widths": [len(block["active_qubits"]) for block in blocks],
        "analytical_shuttle_upper": shuttle_upper,
        "analytical_swap_upper": swap_upper,
        "recooling_upper_sec": shuttle_upper * 40.0e-6,
        "readout_floor_sec_per_shot": 150.0e-6,
        "bound": "BOSS analytical 2*n*L/m shuttle and floor(m/2)*s SWAP upper bounds",
    }


def boss_replacement(row, events):
    qubits = ft.logical_qubits(row)
    locality_capacity = min(4, qubits)
    congestion_capacity = min(2, qubits)
    return {
        "logical_qubits": qubits,
        "locality_first_fifo_blocking": boss_envelope(
            events, qubits, locality_capacity, False
        ),
        "congestion_stressed_one_gate_blocks": boss_envelope(
            events, qubits, congestion_capacity, True
        ),
        "invariants": {
            "gate_and_interaction_sequence_unchanged": True,
            "quality_unchanged": True,
            "native_deadline_unchanged": True,
            "changed_terms": ["execution-zone blocking", "shuttle/SWAP", "recooling"],
        },
        "scope": (
            "Matched BOSS analytical envelope, not the authors' complete TILT "
            "compiler or a surface-code/QCCD composition."
        ),
    }


def distribution(values):
    values = list(values)
    if not values:
        return {"records": 0}
    return {
        "records": len(values),
        "min": min(values),
        "median": median(values),
        "p90": quantile(values, 0.9),
        "max": max(values),
    }


def summarize_subtypes(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[record["structural_config_id"]].append(record)
    output = []
    for config_id, subset in sorted(grouped.items()):
        first = subset[0]
        item = {
            "structural_config_id": config_id,
            "workload": first["workload"],
            "records": len(subset),
            "logical_qubits": first["lsqca"]["logical_qubits"],
            "lsqca_point_sam_cell_change": first["lsqca"][
                "point_sam_core_cell_change_vs_conventional"
            ],
            "lsqca_upper_movement_beats": distribution(
                record["lsqca"]["all_operands_loaded_upper_envelope"][
                    "movement_code_beats"
                ]
                for record in subset
            ),
        }
        if first["boss"] is not None:
            item["boss_locality_shuttle_upper"] = distribution(
                record["boss"]["locality_first_fifo_blocking"][
                    "analytical_shuttle_upper"
                ]
                for record in subset
            )
            item["boss_congestion_shuttle_upper"] = distribution(
                record["boss"]["congestion_stressed_one_gate_blocks"][
                    "analytical_shuttle_upper"
                ]
                for record in subset
            )
        output.append(item)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-csv", default=str(DEFAULT_INPUT))
    parser.add_argument("--schedule-csv", default=str(DEFAULT_SCHEDULE))
    parser.add_argument("--ft-budget", default=str(DEFAULT_FT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    rows = read_rows(args.input_csv)
    schedules = read_schedule(args.schedule_csv)
    eligible_ft, ft_artifact = ft_default_index(args.ft_budget)
    records = []
    for row in rows:
        rid = record_id(row)
        raw, config = ft.raw_workload(row)
        events, event_scope = one_circuit_events(row, raw, config)
        contract = ft.circuit_contract(row, schedules[rid], {}, raw)
        lsqca = lsqca_replacement(
            row, contract, events, eligible_ft.get(rid)
        )
        boss = None
        if row["workload"] in ("chemistry", "optimization"):
            boss = boss_replacement(row, events)
        flags = []
        if row["workload"] == "chemistry":
            flags.append("QWC basis-change references excluded from LSQCA trace")
        if rid not in eligible_ft:
            flags.append("not application-level quality qualified")
        records.append({
            "record_id": rid,
            "structural_config_id": structural_config_id(row),
            "workload": row["workload"],
            "hardware_target_eligible": rid in eligible_ft,
            "event_scope": event_scope,
            "event_count_per_circuit": len(events),
            "lsqca": lsqca,
            "boss": boss,
            "unsupported_scope_flags": flags,
        })

    subtypes = summarize_subtypes(records)
    eligible_records = [record for record in records if record["hardware_target_eligible"]]
    lsqca_area_improvements = sum(
        record["lsqca"]["point_sam_reduces_core_cells"]
        for record in eligible_records
    )
    lower_parity = sum(
        record["lsqca"]["quality_qualified_ft_integration"][
            "runtime_parity_possible_with_lower_movement"
        ]
        for record in eligible_records
    )
    upper_parity = sum(
        record["lsqca"]["quality_qualified_ft_integration"][
            "runtime_parity_possible_with_upper_movement"
        ]
        for record in eligible_records
    )

    internal_errors = []
    if len(records) != 3552:
        internal_errors.append("expected 3552 matched records")
    if len(subtypes) != 222:
        internal_errors.append("expected 222 matched structural subtypes")
    if len(eligible_records) != 12:
        internal_errors.append("expected 12 quality-qualified FT integrations")
    if any(
        record["lsqca"]["invariants"]["changed_terms"]
        != ["core logical cells", "load/store movement"]
        for record in records
    ):
        internal_errors.append("LSQCA replacement changed an unnamed term")
    if any(
        record["boss"] is not None
        and record["boss"]["invariants"]["changed_terms"]
        != ["execution-zone blocking", "shuttle/SWAP", "recooling"]
        for record in records
    ):
        internal_errors.append("BOSS envelope changed an unnamed term")

    payload = {
        "schema": "qarchgauge.component-replacement-case-studies.v1",
        "audit_status": "FAIL" if internal_errors else "PASS",
        "scope": (
            "Matched-event replacement envelopes for LSQCA and BOSS. Published "
            "average speedups are never used."
        ),
        "input_csv": relative(args.input_csv),
        "ft_budget": relative(args.ft_budget),
        "parameter_origins": {
            "lsqca": {
                "source": "LSQCA, HPCA 2025",
                "url": "https://arxiv.org/abs/2412.20486",
                "conventional_density": 0.5,
                "point_sam_cells": "n data + one scan + six-cell CR",
                "point_sam_worst_load_code_beats": "ceil(7*sqrt(n))",
                "replacement_policy": "two-entry LRU CR; lower bound keeps one-qubit operations in memory",
            },
            "boss": {
                "source": "BOSS, HPCA 2025",
                "url": "https://arxiv.org/abs/2412.03443",
                "shuttle_upper": "ceil(2*n*L/m)",
                "swap_upper": "floor(m/2)*shuttles",
                "recooling_sec_per_shuttle": 40.0e-6,
                "readout_floor_sec": 150.0e-6,
            },
        },
        "records": len(records),
        "structural_subtypes": len(subtypes),
        "quality_qualified_lsqqa_integrations": len(eligible_records),
        "headline": {
            "eligible_point_sam_area_improvement_cases": lsqca_area_improvements,
            "eligible_runtime_parity_cases_after_lower_movement": lower_parity,
            "eligible_runtime_parity_cases_after_upper_movement": upper_parity,
            "interpretation": (
                "The 4--7-logical-qubit eligible corpus is below point-SAM's "
                "seven-qubit core-cell break-even; LSQCA does not become the "
                "first target, and matched movement can eliminate remaining "
                "runtime-parity cases."
            ),
        },
        "subtypes": subtypes,
        "quality_qualified_records": eligible_records,
        "boss_summary": {
            workload: {
                "records": len(subset),
                "locality_shuttle_upper": distribution(
                    record["boss"]["locality_first_fifo_blocking"][
                        "analytical_shuttle_upper"
                    ]
                    for record in subset
                ),
                "congestion_shuttle_upper": distribution(
                    record["boss"]["congestion_stressed_one_gate_blocks"][
                        "analytical_shuttle_upper"
                    ]
                    for record in subset
                ),
            }
            for workload in ("chemistry", "optimization")
            for subset in [[
                record for record in records if record["workload"] == workload
            ]]
        },
        "internal_errors": internal_errors,
    }
    json_dump(args.output, payload)
    print(json.dumps({
        "output": relative(args.output),
        "audit_status": payload["audit_status"],
        "records": len(records),
        "subtypes": len(subtypes),
        "headline": payload["headline"],
        "boss_summary": payload["boss_summary"],
    }, indent=2, sort_keys=True))
    if internal_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
