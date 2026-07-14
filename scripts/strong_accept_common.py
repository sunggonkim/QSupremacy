#!/usr/bin/env python3
"""Shared record and statistics utilities for the strong-accept audits."""

import csv
import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT
    / "data/processed/perlmutter/"
    "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv"
)

TOLERANCES = {
    "ml": 0.02,
    "chemistry": 0.01,
    "optimization": 0.02,
    "simulation": 0.01,
}

STRUCTURAL_FIELDS = {
    "ml": (
        "digits_classes",
        "ml_samples",
        "ml_features",
        "ml_depth",
    ),
    "chemistry": (
        "chem_hamiltonian_json",
        "chem_grid",
        "chem_layers",
    ),
    "optimization": (
        "opt_nodes",
        "opt_graph",
        "opt_grid",
    ),
    "simulation": (
        "sim_model",
        "sim_initial_state",
        "sim_qubits",
        "sim_steps",
    ),
}

LADDER_FIELDS = {
    "ml": ("ml_depth",),
    "chemistry": ("chem_grid", "chem_layers"),
    "optimization": ("opt_grid",),
    "simulation": ("sim_steps",),
}


def read_rows(path=DEFAULT_INPUT):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(row, key, default=0.0):
    value = row.get(key, default)
    if value in (None, ""):
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def as_int(row, key, default=0):
    return int(round(as_float(row, key, default)))


def canonical_id(prefix, payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return "{}-{}".format(prefix, digest)


def structural_payload(row, include_ladder=True):
    workload = row.get("workload", "unknown")
    fields = list(STRUCTURAL_FIELDS.get(workload, ()))
    if not include_ladder:
        ladder = set(LADDER_FIELDS.get(workload, ()))
        fields = [field for field in fields if field not in ladder]
    return {
        "workload": workload,
        **{field: row.get(field, "") for field in fields},
    }


def structural_config_id(row):
    return canonical_id("cfg", structural_payload(row, include_ladder=True))


def ladder_group_id(row):
    return canonical_id("ladder", structural_payload(row, include_ladder=False))


def independent_instance_id(row):
    payload = structural_payload(row, include_ladder=True)
    payload["seed"] = row.get("seed", "")
    return canonical_id("instance", payload)


def record_id(row):
    return Path(row.get("file") or row.get("path") or "unknown").stem


def repeat_round(row):
    match = re.search(r"_r(\d+)_seed", row.get("file", ""))
    return int(match.group(1)) if match else None


def base_seed(row):
    seed = as_int(row, "seed", 0)
    round_id = repeat_round(row)
    if round_id is None:
        return seed
    return seed - 1000 * round_id


def quantile(values, probability):
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    position = min(1.0, max(0.0, probability)) * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def median(values):
    return quantile(values, 0.5)


def percentile_interval(values, confidence=0.95):
    values = list(values)
    alpha = (1.0 - confidence) / 2.0
    return [quantile(values, alpha), quantile(values, 1.0 - alpha)]


def json_dump(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def relative(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)
