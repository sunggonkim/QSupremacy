#!/usr/bin/env python3
"""Summarize digits supremacy benchmark JSON files."""

import argparse
import glob
import json
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    files = []
    for pattern in args.paths:
        files.extend(glob.glob(pattern))
    for path in sorted(files):
        with open(path) as f:
            data = json.load(f)
        cfg = data["config"]
        native = data["native_ml_path"]
        qk = data["quantum_kernel_path"]
        vqc = data["qnn_vqc_path"]
        proj = data["break_even_projection"]
        print(os.path.basename(path))
        print(
            "  samples={} pca={} depth={} vqc_iter={}".format(
                cfg["max_samples"],
                cfg["pca_dim"],
                cfg["feature_depth"],
                cfg["vqc_iterations"],
            )
        )
        print(
            "  native best: acc={:.4f} runtime={:.6f}s".format(
                native["best_test_accuracy"],
                native["best_runtime_sec"],
            )
        )
        print(
            "  qkernel: acc={:.4f} total={:.3f}s required_speedup={:.1f}x".format(
                qk["test_accuracy"],
                qk["total_runtime_sec"],
                proj["quantum_kernel"]["sim_to_native_speedup_required"],
            )
        )
        print(
            "  qnn/vqc: acc={:.4f} total={:.3f}s required_speedup={:.1f}x".format(
                vqc["test_accuracy"],
                vqc["total_runtime_sec"],
                proj["qnn_vqc"]["sim_to_native_speedup_required"],
            )
        )


if __name__ == "__main__":
    main()
