#!/usr/bin/env python3
"""Summarize strong ML native gate and profiler artifacts."""

import argparse
import csv
import json
import os
import re
from collections import Counter


TENSOR_PATTERNS = re.compile(
    r"(hmma|imma|wmma|xmma|wgmma|tensorop|ampere_fp16|ampere.*gemm|cudnn.*conv)",
    re.IGNORECASE,
)


def read_gate(path):
    with open(path) as f:
        return json.load(f)


def _float_cell(row, target):
    for key, value in row.items():
        if key and target.lower() == key.strip().lower():
            try:
                return float(str(value).replace(",", ""))
            except Exception:
                return 0.0
    return 0.0


def parse_nsys_csv(path):
    if not path or not os.path.exists(path):
        return {"exists": False}
    kernel_rows = []
    total_time_ns = 0.0
    tensor_time_ns = 0.0
    with open(path, newline="", errors="ignore") as f:
        sample = f.read(4096)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            name = " ".join(str(v) for k, v in row.items() if k and "name" in k.lower())
            if name:
                kernel_rows.append(name)
                row_time = _float_cell(row, "Total Time (ns)")
                total_time_ns += row_time
                if TENSOR_PATTERNS.search(name):
                    tensor_time_ns += row_time
    tensor_hits = [name for name in kernel_rows if TENSOR_PATTERNS.search(name)]
    return {
        "exists": True,
        "kernel_rows": len(kernel_rows),
        "gpu_kernel_time_sec": total_time_ns / 1.0e9,
        "tensor_kernel_time_sec": tensor_time_ns / 1.0e9,
        "tensor_kernel_time_fraction": (
            tensor_time_ns / total_time_ns if total_time_ns > 0 else None
        ),
        "tensor_kernel_rows": len(tensor_hits),
        "tensor_kernel_examples": tensor_hits[:10],
    }


def parse_ncu_csv(path):
    if not path or not os.path.exists(path):
        return {"exists": False}
    metrics = Counter()
    tensor_metrics = Counter()
    errors = []
    with open(path, newline="", errors="ignore") as f:
        for row in csv.reader(f):
            joined = " ".join(row)
            if "==ERROR==" in joined:
                errors.append(joined)
            if "Metric Name" in joined or "metric" in joined.lower():
                continue
            for cell in row:
                if "__" in cell or "tensor" in cell.lower() or "roofline" in cell.lower():
                    metrics[cell] += 1
                    if TENSOR_PATTERNS.search(cell):
                        tensor_metrics[cell] += 1
    return {
        "exists": True,
        "metric_name_count": len(metrics),
        "tensor_metric_name_count": len(tensor_metrics),
        "tensor_metric_examples": list(tensor_metrics.keys())[:10],
        "errors": errors[:10],
        "counter_collection_succeeded": len(errors) == 0 and len(metrics) > 0,
    }


def parse_dmon(path):
    if not path or not os.path.exists(path):
        return {"exists": False}
    samples = []
    columns = None
    with open(path, errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("# gpu"):
                columns = line.lstrip("#").split()
                continue
            if line.startswith("#"):
                continue
            parts = line.split()
            if columns and len(parts) >= len(columns):
                row = {}
                for key, value in zip(columns, parts):
                    try:
                        row[key] = float(value)
                    except Exception:
                        row[key] = value
                samples.append(row)
    def values(key):
        return [row[key] for row in samples if isinstance(row.get(key), float)]
    sm = values("sm")
    mem = values("mem")
    pwr = values("pwr")
    return {
        "exists": True,
        "samples": len(samples),
        "sm_avg_pct": sum(sm) / len(sm) if sm else None,
        "sm_max_pct": max(sm) if sm else None,
        "mem_avg_pct": sum(mem) / len(mem) if mem else None,
        "mem_max_pct": max(mem) if mem else None,
        "power_avg_w": sum(pwr) / len(pwr) if pwr else None,
        "power_max_w": max(pwr) if pwr else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate-json", required=True)
    parser.add_argument("--nsys-gate-json", default="")
    parser.add_argument("--nsys-kernel-csv", default="")
    parser.add_argument("--ncu-csv", default="")
    parser.add_argument("--dmon-csv", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    gate = read_gate(args.gate_json)
    nsys = parse_nsys_csv(args.nsys_kernel_csv)
    if args.nsys_gate_json and os.path.exists(args.nsys_gate_json):
        nsys_gate = read_gate(args.nsys_gate_json)
        prof_runtime = nsys_gate.get("metadata", {}).get("runtime_sec")
        nsys["profiled_gate_runtime_sec"] = prof_runtime
        if prof_runtime and nsys.get("gpu_kernel_time_sec") is not None:
            nsys["gpu_kernel_runtime_fraction"] = nsys["gpu_kernel_time_sec"] / prof_runtime
            nsys["host_orchestration_runtime_fraction"] = max(
                0.0, 1.0 - nsys["gpu_kernel_runtime_fraction"]
            )
    result = {
        "gate_json": args.gate_json,
        "gate_summary": gate["summary"],
        "nsys_kernel_summary": nsys,
        "ncu_summary": parse_ncu_csv(args.ncu_csv),
        "dmon_summary": parse_dmon(args.dmon_csv),
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
