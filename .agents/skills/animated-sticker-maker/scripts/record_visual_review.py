#!/usr/bin/env python3
"""Record visual QA notes and keep the report's aggregate status consistent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


NOTE_FIELDS = ("identity", "meaning", "loop", "alpha", "small_size")


def update_report(args: argparse.Namespace) -> None:
    report = json.loads(args.report.read_text(encoding="utf-8"))
    automatic_status = report.get("automatic_review", {}).get("status")
    if args.status == "pass" and automatic_status != "pass":
        raise ValueError("cannot pass visual review before automatic review passes")

    notes = {field: getattr(args, field) for field in NOTE_FIELDS}
    report["visual_review"] = {"status": args.status, "notes": notes}
    if automatic_status != "pass":
        report["status"] = "automatic_fail"
    elif args.status == "pass":
        report["status"] = "pass"
    else:
        report["status"] = "visual_fail"

    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Recorded visual review: {args.status} -> {args.report}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--status", choices=("pass", "fail"), required=True)
    for field in NOTE_FIELDS:
        parser.add_argument(f"--{field.replace('_', '-')}", required=True)
    update_report(parser.parse_args())


if __name__ == "__main__":
    main()
