#!/usr/bin/env python3
"""Refresh one Slurm accounting artifact after its allocation is terminal."""

import argparse
import csv
import io
import os
import subprocess
import tempfile
from pathlib import Path


SACCT_FORMAT = (
    "JobID,JobName,State,ExitCode,Elapsed,Submit,Start,End,AllocTRES%80"
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("job_id", type=int)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    result = subprocess.run(
        [
            "sacct",
            "-j",
            str(args.job_id),
            "--format={}".format(SACCT_FORMAT),
            "-P",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = list(csv.DictReader(io.StringIO(result.stdout), delimiter="|"))
    root_rows = [row for row in rows if row.get("JobID") == str(args.job_id)]
    if len(root_rows) != 1:
        raise RuntimeError(
            "expected one root row for job {}, found {}".format(
                args.job_id, len(root_rows)
            )
        )
    root = root_rows[0]
    state = root.get("State", "").split("+", 1)[0]
    if state != "COMPLETED" or root.get("ExitCode") != "0:0":
        raise RuntimeError(
            "job {} is not a successful terminal allocation: state={} exit={}".format(
                args.job_id, root.get("State"), root.get("ExitCode")
            )
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=args.output.name + ".", suffix=".tmp", dir=args.output.parent
    )
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(result.stdout)
        os.replace(temporary, args.output)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise

    print(
        "job_id={} state={} elapsed={} output={}".format(
            args.job_id, root["State"], root["Elapsed"], args.output
        )
    )


if __name__ == "__main__":
    main()
