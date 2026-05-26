#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


LEDGER_COLUMNS = (
    "as_of_date",
    "delivery_date",
    "carrier",
    "model_label",
    "git_commit",
    "config_hash",
    "carrier_metadata_sha256",
    "methodology_version",
    "prospective_or_backfill",
    "pipeline_status",
    "valid_day_status",
    "publication_time_ct",
    "manifest_sha256",
    "correction_of_manifest_sha256",
    "corrected_by_manifest_sha256",
    "advisory_detail_sha256",
    "advisory_csv_sha256",
    "positions_sha256",
    "scored_signals_sha256",
    "pipeline_log_sha256",
    "timestamp_status",
    "opentimestamps_proof_path",
    "exclusion_reason",
    "notes",
)


FORBIDDEN_PATTERNS = (
    "scored_signals_",
    "advisory_detail_20",
    "positions_20",
    "w31_vs_w0",
    "carrier=w0",
)


def _read_ledger(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    if not path.is_file():
        return [], [f"missing ledger: {path}"]
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != LEDGER_COLUMNS:
            errors.append(f"schema mismatch in {path}: {reader.fieldnames}")
            return [], errors
        return list(reader), errors


def verify(root: Path) -> list[str]:
    errors: list[str] = []
    daily_rows, daily_errors = _read_ledger(root / "hashes" / "daily_manifest_hashes.csv")
    backfill_rows, backfill_errors = _read_ledger(root / "hashes" / "backfill_manifest_hashes.csv")
    errors.extend(daily_errors)
    errors.extend(backfill_errors)

    seen: set[tuple[str, str, str, str]] = set()
    for idx, row in enumerate(daily_rows, start=2):
        key = (row["as_of_date"], row["delivery_date"], row["carrier"], row["prospective_or_backfill"])
        if key in seen:
            errors.append(f"duplicate daily ledger key at line {idx}: {key}")
        seen.add(key)
        if row["carrier"] == "w0":
            errors.append(f"W0 row is forbidden in daily ledger at line {idx}")
        if row["carrier"] != "w31":
            errors.append(f"unexpected carrier in daily ledger at line {idx}: {row['carrier']}")
        if row["prospective_or_backfill"] != "prospective":
            errors.append(f"daily ledger must be prospective-only at line {idx}")
        if not row["methodology_version"]:
            errors.append(f"missing methodology_version in daily ledger at line {idx}")
        if row["valid_day_status"] == "excluded" and not row["exclusion_reason"]:
            errors.append(f"excluded row missing exclusion_reason at line {idx}")
        if row["timestamp_status"] != "timestamp_pending":
            proof = row["opentimestamps_proof_path"]
            if not proof:
                errors.append(f"timestamp proof missing at line {idx}")
            elif not (root / proof).is_file():
                errors.append(f"timestamp proof path does not exist at line {idx}: {proof}")

    for idx, row in enumerate(backfill_rows, start=2):
        if row["prospective_or_backfill"] != "backfill":
            errors.append(f"backfill ledger row must be marked backfill at line {idx}")
        if row["carrier"] == "w0":
            errors.append(f"W0 row is forbidden in public backfill ledger at line {idx}")

    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = str(path.relative_to(root))
        if rel in {
            "scripts/verify_public_repo.py",
            "hashes/verification_guide.md",
            "methodology/carrier_policy.md",
            "carrier/current.md",
            "README.md",
        }:
            continue
        lowered = rel.lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in lowered:
                errors.append(f"forbidden public artifact path: {rel}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify public ERCOT PTP track-record repo guardrails.")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    errors = verify(Path(args.root).resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VERIFY_OK public_track_record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
