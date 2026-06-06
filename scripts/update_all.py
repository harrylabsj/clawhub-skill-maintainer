#!/usr/bin/env python3
"""Run collection, analysis, and dashboard rendering in one command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=str(cwd), check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle", default="harrylabsj")
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--detail-concurrency", type=int, default=8)
    parser.add_argument("--skip-details", action="store_true")
    parser.add_argument("--baseline", action="store_true", help="Treat this run as a new snapshot baseline.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    report_dir = root / "reports"

    collect = [
        sys.executable,
        str(root / "scripts" / "collect_clawhub_skills.py"),
        "--handle",
        args.handle,
        "--out-dir",
        str(data_dir),
        "--page-size",
        str(args.page_size),
        "--detail-concurrency",
        str(args.detail_concurrency),
    ]
    if args.skip_details:
        collect.append("--skip-details")

    run(collect, root)
    run(
        [
            sys.executable,
            str(root / "scripts" / "analyze_skills.py"),
            "--handle",
            args.handle,
            "--data-dir",
            str(data_dir),
        ],
        root,
    )
    snapshot = [
        sys.executable,
        str(root / "scripts" / "write_snapshot.py"),
        "--handle",
        args.handle,
        "--data-dir",
        str(data_dir),
    ]
    if args.baseline:
        snapshot.append("--baseline")
    run(snapshot, root)
    run(
        [
            sys.executable,
            str(root / "scripts" / "plan_actions.py"),
            "--handle",
            args.handle,
            "--data-dir",
            str(data_dir),
            "--out-dir",
            str(report_dir / "action_plans"),
            "--approval-dir",
            str(report_dir / "approval_packets"),
        ],
        root,
    )
    run(
        [
            sys.executable,
            str(root / "scripts" / "plan_bulk_cleanup.py"),
            "--handle",
            args.handle,
            "--data-dir",
            str(data_dir),
            "--out-dir",
            str(report_dir / "bulk_cleanup"),
        ],
        root,
    )
    run(
        [
            sys.executable,
            str(root / "scripts" / "render_dashboard.py"),
            "--handle",
            args.handle,
            "--data-dir",
            str(data_dir),
            "--out-dir",
            str(report_dir),
        ],
        root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
