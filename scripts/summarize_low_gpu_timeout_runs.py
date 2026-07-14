#!/usr/bin/env python3
"""Audit timeout-censored 4/8/16-GPU fixed-work scaling attempts."""

import csv
import datetime as dt
import glob
import io
import json
import re
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RECORDS = 7104
RUNS = [
    {
        "job_id": 55885604,
        "gpus": 4,
        "nodes": 1,
        "tag": "direct4_strong_1n_4g_7104_20260712091240",
    },
    {
        "job_id": 55885607,
        "gpus": 8,
        "nodes": 2,
        "tag": "direct8_strong_2n_8g_7104_20260712091240",
    },
    {
        "job_id": 55885608,
        "gpus": 16,
        "nodes": 4,
        "tag": "direct16_strong_4n_16g_7104_20260712091240",
    },
]


def slurm_seconds(value):
    days = 0
    if "-" in value:
        day_text, value = value.split("-", 1)
        days = int(day_text)
    fields = [int(field) for field in value.split(":")]
    if len(fields) == 2:
        hours, minutes, seconds = 0, fields[0], fields[1]
    else:
        hours, minutes, seconds = fields
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def capture_accounting(run):
    columns = (
        "JobIDRaw,JobName%28,Account%14,Partition%14,State%20,ExitCode,"
        "Elapsed,Timelimit,NNodes,NCPUS,AllocTRES%60"
    )
    result = subprocess.run(
        [
            "sacct",
            "-j",
            str(run["job_id"]),
            "--starttime",
            "2026-07-01",
            "--format={}".format(columns),
            "-P",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    accounting_path = (
        ROOT
        / "data/raw/perlmutter/accounting"
        / "sacct_practical_suite_{}.txt".format(run["tag"])
    )
    accounting_path.parent.mkdir(parents=True, exist_ok=True)
    accounting_path.write_text(result.stdout)
    rows = list(csv.DictReader(io.StringIO(result.stdout), delimiter="|"))
    root = next(row for row in rows if row["JobIDRaw"] == str(run["job_id"]))
    return root, accounting_path.relative_to(ROOT).as_posix()


def parse_task_logs(run):
    pattern = str(ROOT / "logs" / "qsup-prac-scale-{}_c*.out".format(run["tag"]))
    files = sorted(glob.glob(pattern))
    started = set()
    completed = set()
    completed_files = 0
    for filename in files:
        text = Path(filename).read_text(errors="replace")
        started.update(re.findall(r"^case_start=([^ ]+)", text, re.MULTILINE))
        completed.update(re.findall(r"^case_end=([^ ]+)", text, re.MULTILINE))
        completed_files += int(bool(re.search(r"^date_end=", text, re.MULTILINE)))
    return {
        "task_log_count": len(files),
        "task_logs_with_summary": completed_files,
        "started_record_count": len(started),
        "completed_record_count": len(completed),
    }


def write_plot(rows):
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Liberation Serif"],
            "font.size": 8.5,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 8.3,
            "ytick.labelsize": 8.3,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    labels = ["{} GPUs ({} h)".format(row["gpus"], row["time_limit_hours"]) for row in rows]
    values = [100.0 * row["completion_fraction"] for row in rows]
    y = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(3.35, 1.78))
    ax.barh(y, [100.0] * len(rows), color="#E7E7E7", height=0.52)
    ax.barh(y, values, color="#E6862B", height=0.52)
    for index, row in enumerate(rows):
        ax.text(
            102.5,
            index,
            "{:,}/{:,}".format(row["completed_record_count"], EXPECTED_RECORDS),
            ha="right",
            va="center",
            fontsize=8.3,
            color="#2F2F2F",
        )
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xticks((0, 25, 50, 75, 100))
    ax.set_xticklabels(("0", "25%", "50%", "75%", "100%"))
    ax.set_xlabel("Records completed before timeout")
    ax.grid(axis="x", linestyle=":", linewidth=0.45, color="#B9B9B9")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.subplots_adjust(left=0.31, right=0.99, bottom=0.29, top=0.97)
    output = ROOT / "paper/figures/low_gpu_timeout_progress.pdf"
    fig.savefig(output)
    plt.close(fig)
    return output.relative_to(ROOT).as_posix()


def main():
    rows = []
    for run in RUNS:
        accounting, accounting_path = capture_accounting(run)
        log_counts = parse_task_logs(run)
        elapsed_seconds = slurm_seconds(accounting["Elapsed"])
        time_limit_seconds = slurm_seconds(accounting["Timelimit"])
        completed = log_counts["completed_record_count"]
        row = dict(run)
        row.update(log_counts)
        row.update(
            {
                "account": accounting["Account"],
                "partition": accounting["Partition"],
                "state": accounting["State"].split("+", 1)[0],
                "exit_code": accounting["ExitCode"],
                "elapsed_seconds": elapsed_seconds,
                "time_limit_seconds": time_limit_seconds,
                "time_limit_hours": round(time_limit_seconds / 3600.0, 3),
                "expected_record_count": EXPECTED_RECORDS,
                "missing_record_count": EXPECTED_RECORDS - completed,
                "completion_fraction": completed / float(EXPECTED_RECORDS),
                "valid_fixed_work_measurement": False,
                "accounting_artifact": accounting_path,
            }
        )
        rows.append(row)

    output_dir = ROOT / "data/processed/perlmutter"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "low_gpu_strong_scaling_timeout_audit.json"
    csv_path = output_dir / "low_gpu_strong_scaling_timeout_audit.csv"
    payload = {
        "schema": "qarchgauge.low-gpu-timeout-audit.v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "audit_status": "PASS",
        "campaign_status": "TIMEOUT_CENSORED",
        "expected_records_per_run": EXPECTED_RECORDS,
        "paper_policy": (
            "The timeout-censored attempts are excluded from completed fixed-work "
            "scaling points and are never extrapolated into measured runtimes."
        ),
        "runs": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    plot_path = write_plot(rows)
    print(json_path.relative_to(ROOT))
    print(csv_path.relative_to(ROOT))
    print(plot_path)


if __name__ == "__main__":
    main()
