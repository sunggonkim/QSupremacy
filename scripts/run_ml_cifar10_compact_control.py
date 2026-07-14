#!/usr/bin/env python3
"""Run compact classical controls for the matched CIFAR-10 feature path.

The controls keep the 108-feature representation and ridge head used by the
cuQuantum feature path.  They distinguish feature-map capacity from QPU
execution cost without replacing the deployment-facing ResNet-18 frontier.
"""

import argparse
import importlib.metadata
import json
import platform
import socket
import time
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA

from run_ml_cifar10_cuquantum_feature_proxy import load_split, ridge_classifier


def spatial_pool_6x6(images):
    """Average-pool flattened 32x32 RGB images to exactly 108 features."""
    image_tensor = images.reshape(-1, 32, 32, 3)
    edges = np.rint(np.linspace(0, 32, 7)).astype(np.int64)
    pooled = np.empty((images.shape[0], 6, 6, 3), dtype=np.float64)
    for row in range(6):
        for column in range(6):
            patch = image_tensor[
                :,
                edges[row] : edges[row + 1],
                edges[column] : edges[column + 1],
                :,
            ]
            pooled[:, row, column, :] = patch.mean(axis=(1, 2))
    return pooled.reshape(images.shape[0], 108)


def run_control(name, transform, train_x, train_y, test_x, test_y, ridge):
    started = time.perf_counter()
    train_features, test_features, transform_metadata = transform(train_x, test_x)
    transform_sec = time.perf_counter() - started
    classifier = ridge_classifier(
        train_features, train_y, test_features, test_y, ridge
    )
    return {
        "name": name,
        "feature_count": int(train_features.shape[1]),
        "feature_transform_runtime_sec": transform_sec,
        "ridge_head_parameters": int((train_features.shape[1] + 1) * 10),
        "total_compute_runtime_sec": transform_sec + classifier["runtime_sec"],
        "transform": transform_metadata,
        "classifier": classifier,
    }


def pooled_transform(train_x, test_x):
    return spatial_pool_6x6(train_x), spatial_pool_6x6(test_x), {
        "method": "fixed_spatial_average_pool_6x6_rgb",
        "trainable_feature_parameters": 0,
    }


def pca_transform(train_x, test_x, seed):
    model = PCA(
        n_components=108,
        svd_solver="randomized",
        iterated_power=3,
        random_state=seed,
    )
    train_features = model.fit_transform(train_x)
    test_features = model.transform(test_x)
    return train_features, test_features, {
        "method": "pca_108_randomized_svd",
        "trainable_feature_parameters": int(108 * train_x.shape[1] + 108),
        "explained_variance_ratio_sum": float(model.explained_variance_ratio_.sum()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-root", default="/pscratch/sd/s/sgkim/qsup_datasets/cifar10"
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--ridge", type=float, default=1.0e-2)
    parser.add_argument(
        "--output",
        default="data/processed/perlmutter/ml_cifar10_compact_control.json",
    )
    args = parser.parse_args()

    total_started = time.perf_counter()
    train_x, train_y = load_split(Path(args.dataset_root), "train", 0)
    test_x, test_y = load_split(Path(args.dataset_root), "test", 0)
    controls = [
        run_control(
            "Pool-108 + ridge",
            pooled_transform,
            train_x,
            train_y,
            test_x,
            test_y,
            args.ridge,
        ),
        run_control(
            "PCA-108 + ridge",
            lambda x, y: pca_transform(x, y, args.seed),
            train_x,
            train_y,
            test_x,
            test_y,
            args.ridge,
        ),
    ]
    output = {
        "schema": "qsup.ml-cifar10-compact-control.v1",
        "scope": (
            "same CIFAR-10 50k/10k split, 108-feature budget, and standardized "
            "ridge head as the fixed cuQuantum feature path; ResNet-18 remains "
            "the deployment-facing native frontier"
        ),
        "dataset": "CIFAR-10",
        "train_samples": int(train_x.shape[0]),
        "test_samples": int(test_x.shape[0]),
        "feature_budget": 108,
        "ridge_regularization": args.ridge,
        "controls": controls,
        "total_wall_sec": time.perf_counter() - total_started,
        "software": {
            "numpy": np.__version__,
            "scikit_learn": importlib.metadata.version("scikit-learn"),
            "python": platform.python_version(),
        },
        "host": socket.gethostname(),
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"output": str(path), "controls": controls}, indent=2))


if __name__ == "__main__":
    main()
