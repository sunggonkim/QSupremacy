#!/usr/bin/env python3
"""Materialize sklearn's bundled digits dataset as a small NPZ file."""

import argparse
import json
import os
import platform
import sys
import time

import numpy as np
from sklearn.datasets import load_digits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="data/datasets/sklearn_digits.npz",
        help="Output NPZ path.",
    )
    args = parser.parse_args()

    digits = load_digits()
    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    metadata = {
        "source": "sklearn.datasets.load_digits",
        "created_unix": time.time(),
        "python": sys.version,
        "platform": platform.platform(),
        "n_samples": int(digits.data.shape[0]),
        "n_features": int(digits.data.shape[1]),
        "target_names": [int(x) for x in digits.target_names.tolist()],
    }

    np.savez_compressed(
        args.output,
        data=digits.data.astype(np.float64),
        images=digits.images.astype(np.float64),
        target=digits.target.astype(np.int64),
        target_names=digits.target_names.astype(np.int64),
        metadata=json.dumps(metadata, sort_keys=True),
    )
    print(args.output)


if __name__ == "__main__":
    main()
