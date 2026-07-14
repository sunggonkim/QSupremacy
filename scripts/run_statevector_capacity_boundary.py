#!/usr/bin/env python3
"""Distributed state-vector capacity boundary probe for Perlmutter GPUs.

This is intentionally a capacity-boundary probe, not a full distributed
quantum simulator.  Each Slurm task owns one GPU and allocates the state-vector
shard implied by the total task count.  The probe then performs in-place local
single-qubit gate passes with CuPy kernels so the run proves that the target
state-vector footprint is materialized and touched on the requested GPU scale.
"""

import argparse
import glob
import json
import math
import os
import socket
import time
from pathlib import Path


INIT_KERNEL = r'''
extern "C" __global__
void init_state(float2* state, unsigned long long n, int rank) {
    unsigned long long tid = blockIdx.x * blockDim.x + threadIdx.x;
    unsigned long long stride = blockDim.x * gridDim.x;
    for (unsigned long long i = tid; i < n; i += stride) {
        float v = (float)((i & 1023ULL) + (unsigned long long)(rank & 255)) * 0.0009765625f;
        state[i] = make_float2(v, 0.0f);
    }
}
'''


H_KERNEL = r'''
extern "C" __global__
void apply_h_local(float2* state, unsigned long long pairs, int target) {
    unsigned long long tid = blockIdx.x * blockDim.x + threadIdx.x;
    unsigned long long stride = blockDim.x * gridDim.x;
    unsigned long long low_mask = (1ULL << target) - 1ULL;
    unsigned long long bit = 1ULL << target;
    const float invsqrt2 = 0.7071067811865475f;
    for (unsigned long long p = tid; p < pairs; p += stride) {
        unsigned long long low = p & low_mask;
        unsigned long long high = p >> target;
        unsigned long long i0 = (high << (target + 1)) | low;
        unsigned long long i1 = i0 | bit;
        float2 a = state[i0];
        float2 b = state[i1];
        state[i0] = make_float2((a.x + b.x) * invsqrt2, (a.y + b.y) * invsqrt2);
        state[i1] = make_float2((a.x - b.x) * invsqrt2, (a.y - b.y) * invsqrt2);
    }
}
'''


def env_int(name, default):
    value = os.environ.get(name)
    if value in (None, ""):
        return default
    return int(value)


def task_context():
    rank = env_int("SLURM_PROCID", 0)
    world = env_int("SLURM_NTASKS", 1)
    local_rank = env_int("SLURM_LOCALID", rank)
    job_id = os.environ.get("SLURM_JOB_ID", "manual")
    return rank, world, local_rank, job_id


def nearest_power_of_two(value):
    return value > 0 and (value & (value - 1)) == 0


def run_probe(args):
    import cupy as cp

    rank, world, local_rank, job_id = task_context()
    if not nearest_power_of_two(world):
        raise SystemExit("This probe expects a power-of-two task count; got {}".format(world))

    shard_bits = args.qubits - int(math.log2(world))
    if shard_bits < 20:
        raise SystemExit("Shard too small for capacity boundary: {} bits".format(shard_bits))

    visible_devices = cp.cuda.runtime.getDeviceCount()
    if visible_devices < 1:
        raise SystemExit("No CUDA device is visible to rank {}".format(rank))
    # Perlmutter's --gpus-per-task=1 masks each task to one visible GPU, whose
    # process-local ordinal is 0 even when SLURM_LOCALID is 1--3.
    device_ordinal = 0 if visible_devices == 1 else local_rank % visible_devices
    cp.cuda.Device(device_ordinal).use()
    free_before, total_mem = cp.cuda.runtime.memGetInfo()
    local_len = 1 << shard_bits
    local_bytes = local_len * cp.dtype(cp.complex64).itemsize
    if local_bytes > free_before * args.max_free_fraction:
        raise SystemExit(
            "Need {:.2f} GiB but only {:.2f} GiB is free under fraction {:.2f}".format(
                local_bytes / 2**30, free_before / 2**30, args.max_free_fraction
            )
        )

    init_kernel = cp.RawKernel(INIT_KERNEL, "init_state")
    h_kernel = cp.RawKernel(H_KERNEL, "apply_h_local")
    threads = 256

    t0 = time.perf_counter()
    state = cp.empty(local_len, dtype=cp.complex64)
    cp.cuda.Device().synchronize()
    t_alloc = time.perf_counter()

    blocks = min(args.max_blocks, max(1, (local_len + threads - 1) // threads))
    init_kernel((blocks,), (threads,), (state, local_len, rank))
    cp.cuda.Device().synchronize()
    t_init = time.perf_counter()

    gate_records = []
    target_cycle = [q for q in args.local_gate_targets if q < shard_bits]
    if not target_cycle:
        target_cycle = [0]
    for gate_index in range(args.depth):
        target = target_cycle[gate_index % len(target_cycle)]
        pairs = local_len >> 1
        gate_blocks = min(args.max_blocks, max(1, (pairs + threads - 1) // threads))
        g0 = time.perf_counter()
        h_kernel((gate_blocks,), (threads,), (state, pairs, target))
        cp.cuda.Device().synchronize()
        g1 = time.perf_counter()
        gate_records.append(
            {
                "gate_index": gate_index,
                "gate": "H",
                "local_target": target,
                "seconds": g1 - g0,
            }
        )

    checksum = float(cp.real(state[rank % local_len]).get())
    free_after, _ = cp.cuda.runtime.memGetInfo()
    t_end = time.perf_counter()

    result = {
        "schema": "qarchgauge_statevector_capacity_boundary_v1",
        "job_id": job_id,
        "run_tag": args.run_tag,
        "host": socket.gethostname(),
        "rank": rank,
        "world_size": world,
                "local_rank": local_rank,
                "visible_cuda_devices": visible_devices,
                "device_ordinal": device_ordinal,
        "gpu_device": int(cp.cuda.runtime.getDevice()),
        "qubits": args.qubits,
        "shard_bits": shard_bits,
        "local_amplitudes": local_len,
        "dtype": "complex64",
        "local_state_bytes": local_bytes,
        "local_state_gib": local_bytes / 2**30,
        "cluster_state_bytes": local_bytes * world,
        "cluster_state_tib": (local_bytes * world) / 2**40,
        "gpu_mem_total_gib": total_mem / 2**30,
        "gpu_mem_free_before_gib": free_before / 2**30,
        "gpu_mem_free_after_gib": free_after / 2**30,
        "depth": args.depth,
        "local_gate_targets": target_cycle,
        "alloc_seconds": t_alloc - t0,
        "init_seconds": t_init - t_alloc,
        "gate_seconds_total": sum(item["seconds"] for item in gate_records),
        "elapsed_seconds": t_end - t0,
        "gate_records": gate_records,
        "checksum_sample_real": checksum,
        "interpretation": (
            "capacity-boundary shard probe; local gate passes only; "
            "not a full cross-rank distributed simulator"
        ),
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "{}_{}q_rank{:05d}.json".format(args.run_tag, args.qubits, rank)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if rank == 0:
        print(json.dumps({k: result[k] for k in (
            "schema", "run_tag", "job_id", "qubits", "world_size", "shard_bits",
            "local_state_gib", "cluster_state_tib", "elapsed_seconds",
            "interpretation"
        )}, sort_keys=True))


def summarize(args):
    paths = sorted(glob.glob(args.summary_glob))
    rows = []
    for path in paths:
        with open(path) as f:
            rows.append(json.load(f))
    if not rows:
        raise SystemExit("No files matched {}".format(args.summary_glob))
    rows.sort(key=lambda row: row["rank"])
    elapsed = [row["elapsed_seconds"] for row in rows]
    gate = [row["gate_seconds_total"] for row in rows]
    summary = {
        "schema": "qarchgauge_statevector_capacity_boundary_summary_v1",
        "run_tag": rows[0]["run_tag"],
        "job_id": rows[0]["job_id"],
        "qubits": rows[0]["qubits"],
        "world_size": len(rows),
        "expected_world_size": rows[0]["world_size"],
        "complete": len(rows) == rows[0]["world_size"],
        "shard_bits": rows[0]["shard_bits"],
        "local_state_gib": rows[0]["local_state_gib"],
        "cluster_state_tib": rows[0]["cluster_state_tib"],
        "elapsed_min_sec": min(elapsed),
        "elapsed_median_sec": sorted(elapsed)[len(elapsed) // 2],
        "elapsed_max_sec": max(elapsed),
        "gate_total_min_sec": min(gate),
        "gate_total_median_sec": sorted(gate)[len(gate) // 2],
        "gate_total_max_sec": max(gate),
        "interpretation": rows[0]["interpretation"],
    }
    Path(args.summary_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary_out).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    run = sub.add_parser("run")
    run.add_argument("--qubits", type=int, required=True)
    run.add_argument("--depth", type=int, default=4)
    run.add_argument("--run-tag", required=True)
    run.add_argument("--out-dir", default="data/raw/perlmutter/statevector_capacity")
    run.add_argument("--local-gate-targets", type=int, nargs="*", default=[0, 4, 8, 12])
    run.add_argument("--max-blocks", type=int, default=2_000_000)
    run.add_argument("--max-free-fraction", type=float, default=0.92)
    run.set_defaults(func=run_probe)

    summ = sub.add_parser("summarize")
    summ.add_argument("--summary-glob", required=True)
    summ.add_argument("--summary-out", required=True)
    summ.set_defaults(func=summarize)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
