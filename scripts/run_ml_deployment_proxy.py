#!/usr/bin/env python3
"""Train a production-shaped CIFAR-10 ResNet native baseline on one GPU."""

import argparse
import json
import platform
import socket
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


def evaluate(model, loader, device):
    model.eval()
    correct = 0
    total = 0
    started = time.perf_counter()
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.float16):
        for images, labels in loader:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            correct += int((model(images).argmax(dim=1) == labels).sum())
            total += labels.numel()
    torch.cuda.synchronize()
    return correct / total, time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="/pscratch/sd/s/sgkim/qsup_datasets/cifar10")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--output", default="data/processed/perlmutter/ml_cifar10_resnet18_proxy.json"
    )
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True
    device = torch.device("cuda")

    train_transform = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
    ])
    test_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
    ])
    train_set = datasets.ImageFolder(Path(args.data) / "train", train_transform)
    test_set = datasets.ImageFolder(Path(args.data) / "test", test_transform)
    loader_args = {
        "batch_size": args.batch_size,
        "num_workers": args.workers,
        "pin_memory": True,
        "persistent_workers": args.workers > 0,
    }
    train_loader = DataLoader(train_set, shuffle=True, drop_last=False, **loader_args)
    test_loader = DataLoader(test_set, shuffle=False, drop_last=False, **loader_args)

    model = models.resnet18(num_classes=10)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.maxpool = nn.Identity()
    model = model.to(device)
    optimizer = torch.optim.SGD(
        model.parameters(), lr=args.lr, momentum=0.9, weight_decay=5e-4
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = torch.amp.GradScaler("cuda")

    epoch_records = []
    total_started = time.perf_counter()
    for epoch in range(args.epochs):
        model.train()
        loss_sum = 0.0
        samples = 0
        started = time.perf_counter()
        for images, labels in train_loader:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", dtype=torch.float16):
                logits = model(images)
                loss = nn.functional.cross_entropy(logits, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            loss_sum += float(loss.detach()) * labels.numel()
            samples += labels.numel()
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - started
        scheduler.step()
        test_accuracy, test_sec = evaluate(model, test_loader, device)
        epoch_records.append({
            "epoch": epoch + 1,
            "train_loss": loss_sum / samples,
            "train_runtime_sec": elapsed,
            "train_images_per_sec": samples / elapsed,
            "test_accuracy": test_accuracy,
            "test_runtime_sec": test_sec,
        })
        print(json.dumps(epoch_records[-1]), flush=True)

    total_runtime = time.perf_counter() - total_started
    output = {
        "schema": "qsup.ml-native-proxy.v1",
        "scope": "CIFAR-10 GPU-native frontier; no matched quantum-image model is claimed",
        "dataset": "CIFAR-10",
        "train_samples": len(train_set),
        "test_samples": len(test_set),
        "model": "ResNet-18 CIFAR stem",
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "amp": True,
        "tf32": True,
        "total_runtime_sec": total_runtime,
        "final_test_accuracy": epoch_records[-1]["test_accuracy"],
        "best_test_accuracy": max(record["test_accuracy"] for record in epoch_records),
        "median_train_images_per_sec": float(
            torch.tensor([record["train_images_per_sec"] for record in epoch_records]).median()
        ),
        "max_cuda_memory_bytes": torch.cuda.max_memory_allocated(),
        "gpu": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "host": socket.gethostname(),
        "python": platform.python_version(),
        "epochs_detail": epoch_records,
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
