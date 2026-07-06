#!/usr/bin/env python3
"""Run production-style ML native baselines for measured digits cases."""

import argparse
import csv
import json
import os
import platform
import socket
import time
from collections import Counter, OrderedDict

import numpy as np


def parse_int_list(text):
    return [int(x.strip()) for x in str(text).split(",") if x.strip()]


def accuracy(pred, y):
    return float(np.mean(np.asarray(pred, dtype=np.int64) == y))


def fit_pca_transform(x, features):
    mean = x.mean(axis=0)
    centered = x - mean
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    reduced = centered @ vt[:features].T
    scale = reduced.std(axis=0) + 1.0e-12
    return np.clip(reduced / scale, -3.0, 3.0).astype(np.float32)


def load_digits_case(path, samples, features, classes_text, seed):
    classes = parse_int_list(classes_text)
    with np.load(path, allow_pickle=False) as data:
        x_all = data["data"].astype(np.float32) / 16.0
        y_all = data["target"].astype(np.int64)
    rng = np.random.default_rng(int(seed))
    selected = []
    per_class = int(samples) // len(classes)
    remainder = int(samples) % len(classes)
    for idx, cls in enumerate(classes):
        cls_indices = np.flatnonzero(y_all == int(cls))
        rng.shuffle(cls_indices)
        take = per_class + (1 if idx < remainder else 0)
        selected.append(cls_indices[:take])
    indices = np.concatenate(selected)
    rng.shuffle(indices)
    raw_x = x_all[indices]
    raw_y = y_all[indices]
    label_map = {cls: i for i, cls in enumerate(classes)}
    y = np.array([label_map[int(v)] for v in raw_y], dtype=np.int64)
    pca_x = fit_pca_transform(raw_x, int(features))
    return raw_x.astype(np.float32), pca_x, y, classes


def split_arrays(raw_x, pca_x, y, train_frac):
    n_train = int(round(raw_x.shape[0] * float(train_frac)))
    return (
        raw_x[:n_train],
        raw_x[n_train:],
        pca_x[:n_train],
        pca_x[n_train:],
        y[:n_train],
        y[n_train:],
    )


def select_suite_cases(summary_csv, max_cases):
    with open(summary_csv, newline="") as f:
        rows = [row for row in csv.DictReader(f) if row.get("workload") == "ml"]
    groups = OrderedDict()
    for row in rows:
        if row.get("ml_dataset") != "digits":
            continue
        key = (
            row.get("digits_classes", ""),
            row.get("ml_samples", ""),
            row.get("ml_features", ""),
            row.get("ml_depth", ""),
            row.get("seed", ""),
        )
        groups.setdefault(key, row)
    selected = list(groups.values())
    selected.sort(
        key=lambda r: (
            int(r.get("ml_samples", 0)),
            int(r.get("ml_features", 0)),
            int(r.get("ml_depth", 0)),
            r.get("digits_classes", ""),
            int(r.get("seed", 0)),
        )
    )
    return selected[: int(max_cases)]


def torch_available():
    try:
        import torch

        return torch
    except Exception:
        return None


def train_torch_mlp(x_train, y_train, x_test, y_test, classes, args, seed):
    torch = torch_available()
    if torch is None:
        raise RuntimeError("torch is not importable")
    if not torch.cuda.is_available():
        raise RuntimeError("torch cuda is not available")

    import torch.nn as nn
    import torch.nn.functional as F

    class MLP(nn.Module):
        def __init__(self, n_features, n_classes, hidden):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(n_features, hidden),
                nn.ReLU(),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
                nn.Linear(hidden, n_classes),
            )

        def forward(self, x):
            return self.net(x)

    torch.manual_seed(int(seed))
    torch.cuda.manual_seed_all(int(seed))
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    start = time.perf_counter()
    device = torch.device("cuda")
    xtr = torch.tensor(x_train, dtype=torch.float32, device=device)
    ytr = torch.tensor(y_train, dtype=torch.long, device=device)
    xte = torch.tensor(x_test, dtype=torch.float32, device=device)
    yte = torch.tensor(y_test, dtype=torch.long, device=device)
    model = MLP(x_train.shape[1], int(classes), int(args.torch_hidden)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=float(args.torch_lr))
    scaler = torch.amp.GradScaler("cuda", enabled=bool(args.amp))
    batch = min(int(args.batch_size), xtr.shape[0])
    torch.cuda.synchronize()
    torch.cuda.nvtx.range_push("torch_mlp_amp_train")
    for step in range(int(args.torch_steps)):
        index = torch.randint(0, xtr.shape[0], (batch,), device=device)
        opt.zero_grad(set_to_none=True)
        with torch.amp.autocast("cuda", dtype=torch.float16, enabled=bool(args.amp)):
            loss = F.cross_entropy(model(xtr[index]), ytr[index])
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
    torch.cuda.nvtx.range_pop()
    torch.cuda.nvtx.range_push("torch_mlp_amp_infer")
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.float16, enabled=bool(args.amp)):
        train_pred = torch.argmax(model(xtr), dim=1)
        test_pred = torch.argmax(model(xte), dim=1)
    torch.cuda.nvtx.range_pop()
    torch.cuda.synchronize()
    runtime = time.perf_counter() - start
    return {
        "model": "torch_mlp_amp_pca",
        "runtime_sec": float(runtime),
        "train_accuracy": float((train_pred == ytr).float().mean().item()),
        "test_accuracy": float((test_pred == yte).float().mean().item()),
        "device": torch.cuda.get_device_name(0),
        "amp": bool(args.amp),
        "allow_tf32": True,
        "parameters": int(sum(p.numel() for p in model.parameters())),
        "max_cuda_memory_bytes": int(torch.cuda.max_memory_allocated()),
    }


def train_torch_cnn(raw_train, y_train, raw_test, y_test, classes, args, seed):
    torch = torch_available()
    if torch is None:
        raise RuntimeError("torch is not importable")
    if not torch.cuda.is_available():
        raise RuntimeError("torch cuda is not available")

    import torch.nn as nn
    import torch.nn.functional as F

    class TinyDigitsCNN(nn.Module):
        def __init__(self, n_classes):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
            self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
            self.fc1 = nn.Linear(32 * 8 * 8, 128)
            self.fc2 = nn.Linear(128, n_classes)

        def forward(self, x):
            x = F.relu(self.conv1(x))
            x = F.relu(self.conv2(x))
            x = x.flatten(1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    torch.manual_seed(int(seed))
    torch.cuda.manual_seed_all(int(seed))
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    start = time.perf_counter()
    device = torch.device("cuda")
    xtr = torch.tensor(raw_train.reshape(-1, 1, 8, 8), dtype=torch.float32, device=device)
    ytr = torch.tensor(y_train, dtype=torch.long, device=device)
    xte = torch.tensor(raw_test.reshape(-1, 1, 8, 8), dtype=torch.float32, device=device)
    yte = torch.tensor(y_test, dtype=torch.long, device=device)
    model = TinyDigitsCNN(int(classes)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=float(args.torch_lr))
    scaler = torch.amp.GradScaler("cuda", enabled=bool(args.amp))
    batch = min(int(args.batch_size), xtr.shape[0])
    torch.cuda.synchronize()
    torch.cuda.nvtx.range_push("torch_cnn_amp_train")
    for step in range(int(args.torch_steps)):
        index = torch.randint(0, xtr.shape[0], (batch,), device=device)
        opt.zero_grad(set_to_none=True)
        with torch.amp.autocast("cuda", dtype=torch.float16, enabled=bool(args.amp)):
            loss = F.cross_entropy(model(xtr[index]), ytr[index])
        scaler.scale(loss).backward()
        scaler.step(opt)
        scaler.update()
    torch.cuda.nvtx.range_pop()
    torch.cuda.nvtx.range_push("torch_cnn_amp_infer")
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.float16, enabled=bool(args.amp)):
        train_pred = torch.argmax(model(xtr), dim=1)
        test_pred = torch.argmax(model(xte), dim=1)
    torch.cuda.nvtx.range_pop()
    torch.cuda.synchronize()
    runtime = time.perf_counter() - start
    return {
        "model": "torch_cnn_amp_raw",
        "runtime_sec": float(runtime),
        "train_accuracy": float((train_pred == ytr).float().mean().item()),
        "test_accuracy": float((test_pred == yte).float().mean().item()),
        "device": torch.cuda.get_device_name(0),
        "amp": bool(args.amp),
        "allow_tf32": True,
        "parameters": int(sum(p.numel() for p in model.parameters())),
        "max_cuda_memory_bytes": int(torch.cuda.max_memory_allocated()),
    }


def train_xgboost_gpu(x_train, y_train, x_test, y_test, classes, args, seed):
    import xgboost as xgb

    start = time.perf_counter()
    clf = xgb.XGBClassifier(
        n_estimators=int(args.xgb_estimators),
        max_depth=int(args.xgb_max_depth),
        learning_rate=float(args.xgb_lr),
        objective="multi:softprob",
        num_class=int(classes),
        eval_metric="mlogloss",
        tree_method="hist",
        device="cuda",
        random_state=int(seed),
        n_jobs=1,
    )
    clf.fit(x_train, y_train)
    train_pred = clf.predict(x_train)
    test_pred = clf.predict(x_test)
    runtime = time.perf_counter() - start
    return {
        "model": "xgboost_gpu_hist_pca",
        "runtime_sec": float(runtime),
        "train_accuracy": accuracy(train_pred, y_train),
        "test_accuracy": accuracy(test_pred, y_test),
        "device": "cuda",
        "n_estimators": int(args.xgb_estimators),
        "max_depth": int(args.xgb_max_depth),
    }


def train_sklearn_histgb(x_train, y_train, x_test, y_test, args, seed):
    from sklearn.ensemble import HistGradientBoostingClassifier

    start = time.perf_counter()
    clf = HistGradientBoostingClassifier(
        max_iter=int(args.xgb_estimators),
        max_leaf_nodes=31,
        learning_rate=float(args.xgb_lr),
        random_state=int(seed),
    )
    clf.fit(x_train, y_train)
    train_pred = clf.predict(x_train)
    test_pred = clf.predict(x_test)
    runtime = time.perf_counter() - start
    return {
        "model": "sklearn_hist_gradient_boosting_cpu_pca",
        "runtime_sec": float(runtime),
        "train_accuracy": accuracy(train_pred, y_train),
        "test_accuracy": accuracy(test_pred, y_test),
        "device": "cpu",
        "max_iter": int(args.xgb_estimators),
    }


def select_model(models, tolerance):
    ok_models = [m for m in models if m.get("status", "ok") == "ok"]
    best_quality = max(ok_models, key=lambda m: (m["test_accuracy"], -m["runtime_sec"]))
    best_acc = float(best_quality["test_accuracy"])
    valid = [m for m in ok_models if float(m["test_accuracy"]) >= best_acc - float(tolerance)]
    selected = min(valid, key=lambda m: float(m["runtime_sec"]))
    fastest = min(ok_models, key=lambda m: float(m["runtime_sec"]))
    return selected, best_quality, fastest


def run_case(row, args):
    raw_x, pca_x, y, classes = load_digits_case(
        args.digits_path,
        int(row["ml_samples"]),
        int(row["ml_features"]),
        row["digits_classes"],
        int(row["seed"]),
    )
    raw_train, raw_test, x_train, x_test, y_train, y_test = split_arrays(
        raw_x, pca_x, y, args.train_frac
    )
    models = [
        {
            "model": "suite_previous_selected",
            "runtime_sec": float(row["native_runtime_sec"]),
            "train_accuracy": None,
            "test_accuracy": float(row["native_quality"]),
            "device": "recorded",
            "source": "practical_suite_summary",
        }
    ]
    requested = set(x.strip() for x in args.models.split(",") if x.strip())
    trainers = {
        "torch_mlp_amp": lambda: train_torch_mlp(
            x_train, y_train, x_test, y_test, len(classes), args, int(row["seed"]) + 11
        ),
        "torch_cnn_amp": lambda: train_torch_cnn(
            raw_train, y_train, raw_test, y_test, len(classes), args, int(row["seed"]) + 17
        ),
        "xgboost_gpu_hist": lambda: train_xgboost_gpu(
            x_train, y_train, x_test, y_test, len(classes), args, int(row["seed"]) + 23
        ),
        "sklearn_histgb": lambda: train_sklearn_histgb(
            x_train, y_train, x_test, y_test, args, int(row["seed"]) + 29
        ),
    }
    for name, trainer in trainers.items():
        if name not in requested:
            continue
        try:
            models.append(trainer())
        except Exception as exc:
            models.append(
                {
                    "model": name,
                    "status": "failed",
                    "error": "{}: {}".format(type(exc).__name__, str(exc)[:500]),
                }
            )
    selected_combined, best_combined, fastest_combined = select_model(
        models, args.quality_tolerance
    )
    production_models = [m for m in models if m.get("model") != "suite_previous_selected"]
    selected_prod = best_prod = fastest_prod = None
    if any(m.get("status", "ok") == "ok" for m in production_models):
        selected_prod, best_prod, fastest_prod = select_model(production_models, args.quality_tolerance)
    q_sec = float(row["quantum_runtime_sec"])
    return {
        "case_id": row["file"],
        "config": {
            "digits_classes": row["digits_classes"],
            "ml_samples": int(row["ml_samples"]),
            "ml_features": int(row["ml_features"]),
            "ml_depth": int(row["ml_depth"]),
            "seed": int(row["seed"]),
        },
        "reference": {
            "quantum_runtime_sec": q_sec,
            "quantum_quality": float(row["quantum_quality"]),
            "previous_native_runtime_sec": float(row["native_runtime_sec"]),
            "previous_native_quality": float(row["native_quality"]),
            "previous_required_speedup": float(row["speedup_required"]),
            "previous_selected_model": row["native_selected_model"],
        },
        "models": models,
        "selected_combined": selected_combined,
        "best_quality_combined": best_combined,
        "fastest_combined": fastest_combined,
        "selected_production": selected_prod,
        "best_quality_production": best_prod,
        "fastest_production": fastest_prod,
        "combined_required_speedup": float(q_sec / selected_combined["runtime_sec"]),
        "production_required_speedup": (
            float(q_sec / selected_prod["runtime_sec"]) if selected_prod else None
        ),
    }


def median(values):
    values = [float(v) for v in values if v is not None]
    return float(np.median(values)) if values else None


def summarize(cases):
    selected_combined = Counter(c["selected_combined"]["model"] for c in cases)
    selected_prod = Counter(
        c["selected_production"]["model"]
        for c in cases
        if c.get("selected_production") is not None
    )
    prod_failures = Counter()
    for case in cases:
        for model in case["models"]:
            if model.get("status") == "failed":
                prod_failures[model["model"]] += 1
    return {
        "case_count": len(cases),
        "previous_required_speedup_median": median(
            c["reference"]["previous_required_speedup"] for c in cases
        ),
        "combined_required_speedup_median": median(
            c["combined_required_speedup"] for c in cases
        ),
        "production_required_speedup_median": median(
            c.get("production_required_speedup") for c in cases
        ),
        "previous_native_runtime_sec_median": median(
            c["reference"]["previous_native_runtime_sec"] for c in cases
        ),
        "combined_native_runtime_sec_median": median(
            c["selected_combined"]["runtime_sec"] for c in cases
        ),
        "production_native_runtime_sec_median": median(
            c["selected_production"]["runtime_sec"]
            for c in cases
            if c.get("selected_production") is not None
        ),
        "previous_native_quality_median": median(
            c["reference"]["previous_native_quality"] for c in cases
        ),
        "combined_native_quality_median": median(
            c["selected_combined"]["test_accuracy"] for c in cases
        ),
        "production_native_quality_median": median(
            c["selected_production"]["test_accuracy"]
            for c in cases
            if c.get("selected_production") is not None
        ),
        "selected_combined_counts": dict(selected_combined),
        "selected_production_counts": dict(selected_prod),
        "model_failure_counts": dict(prod_failures),
    }


def write_csv(path, cases):
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = [
        "case_id",
        "digits_classes",
        "ml_samples",
        "ml_features",
        "ml_depth",
        "seed",
        "quantum_runtime_sec",
        "previous_native_runtime_sec",
        "previous_required_speedup",
        "combined_model",
        "combined_runtime_sec",
        "combined_quality",
        "combined_required_speedup",
        "production_model",
        "production_runtime_sec",
        "production_quality",
        "production_required_speedup",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in cases:
            prod = c.get("selected_production") or {}
            writer.writerow(
                {
                    "case_id": c["case_id"],
                    "digits_classes": c["config"]["digits_classes"],
                    "ml_samples": c["config"]["ml_samples"],
                    "ml_features": c["config"]["ml_features"],
                    "ml_depth": c["config"]["ml_depth"],
                    "seed": c["config"]["seed"],
                    "quantum_runtime_sec": c["reference"]["quantum_runtime_sec"],
                    "previous_native_runtime_sec": c["reference"][
                        "previous_native_runtime_sec"
                    ],
                    "previous_required_speedup": c["reference"][
                        "previous_required_speedup"
                    ],
                    "combined_model": c["selected_combined"]["model"],
                    "combined_runtime_sec": c["selected_combined"]["runtime_sec"],
                    "combined_quality": c["selected_combined"]["test_accuracy"],
                    "combined_required_speedup": c["combined_required_speedup"],
                    "production_model": prod.get("model", ""),
                    "production_runtime_sec": prod.get("runtime_sec", ""),
                    "production_quality": prod.get("test_accuracy", ""),
                    "production_required_speedup": c.get("production_required_speedup"),
                }
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary-csv",
        default=(
            "data/processed/perlmutter/"
            "practical_suite_strongnative_32node_large128c0c127_20260704060230_summary.csv"
        ),
    )
    parser.add_argument("--digits-path", default="data/datasets/sklearn_digits.npz")
    parser.add_argument("--max-cases", type=int, default=24)
    parser.add_argument("--train-frac", type=float, default=0.75)
    parser.add_argument(
        "--models",
        default="torch_mlp_amp,torch_cnn_amp,xgboost_gpu_hist,sklearn_histgb",
    )
    parser.add_argument("--quality-tolerance", type=float, default=0.01)
    parser.add_argument("--torch-steps", type=int, default=80)
    parser.add_argument("--torch-hidden", type=int, default=128)
    parser.add_argument("--torch-lr", type=float, default=3.0e-3)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--xgb-estimators", type=int, default=64)
    parser.add_argument("--xgb-max-depth", type=int, default=4)
    parser.add_argument("--xgb-lr", type=float, default=0.15)
    parser.add_argument("--output", required=True)
    parser.add_argument("--csv-output", default="")
    args = parser.parse_args()

    start = time.perf_counter()
    rows = select_suite_cases(args.summary_csv, args.max_cases)
    cases = [run_case(row, args) for row in rows]
    result = {
        "metadata": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "slurm_job_id": os.environ.get("SLURM_JOB_ID", ""),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
            "summary_csv": args.summary_csv,
            "digits_path": args.digits_path,
            "models": args.models,
            "amp": bool(args.amp),
            "runtime_sec": time.perf_counter() - start,
        },
        "summary": summarize(cases),
        "cases": cases,
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
    write_csv(args.csv_output, cases)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
