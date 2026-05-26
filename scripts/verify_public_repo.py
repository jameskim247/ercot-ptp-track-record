#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
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

OUTCOME_SUMMARY_COLUMNS = (
    "as_of_date",
    "delivery_date",
    "carrier",
    "manifest_sha256",
    "methodology_version",
    "outcome_status",
    "rows_counted_sha256",
    "position_count",
    "priced_position_count",
    "missing_price_position_count",
    "total_mw",
    "filled_position_count",
    "filled_mw",
    "fill_rate",
    "hit_rate",
    "realized_filled_pnl",
    "realized_pnl_if_filled",
    "worst_path_hour_pnl",
    "expected_ev",
    "expected_filled_ev",
    "ercot_data_source",
    "ercot_data_product",
    "ercot_data_snapshot_sha256",
    "ercot_data_fetch_time_utc",
    "ercot_data_watermark",
    "private_outcome_sha256",
)

DAILY_LEDGER = Path("hashes/daily_manifest_hashes.csv")
BACKFILL_LEDGER = Path("hashes/backfill_manifest_hashes.csv")
OUTCOME_SUMMARIES = Path("reports/audits/daily_outcome_summaries.csv")

FORBIDDEN_PATH_PATTERNS = (
    re.compile(r"(^|/)scored_signals_\d{4}-\d{2}-\d{2}\.(csv|json|parquet)$", re.IGNORECASE),
    re.compile(r"(^|/)positions_\d{4}-\d{2}-\d{2}\.(csv|json|parquet)$", re.IGNORECASE),
    re.compile(r"(^|/)book_delta_\d{4}-\d{2}-\d{2}\.(csv|json|parquet)$", re.IGNORECASE),
    re.compile(r"(^|/)advisory_detail_\d{4}-\d{2}-\d{2}\.(csv|json)$", re.IGNORECASE),
    re.compile(r"(^|/)advisory_debug_\d{4}-\d{2}-\d{2}\.(csv|json)$", re.IGNORECASE),
    re.compile(r"(^|/)w31_vs_w0(/|_|-|$)", re.IGNORECASE),
    re.compile(r"(^|/)private_audit(/|$)", re.IGNORECASE),
)

FORBIDDEN_CONTENT_PATTERNS = (
    re.compile(r"\bshadow_bid\b", re.IGNORECASE),
    re.compile(r"\bshadow_award_probability\b", re.IGNORECASE),
    re.compile(r"(^|[,{])\s*source\s*[:=]", re.IGNORECASE),
    re.compile(r"(^|[,{])\s*sink\s*[:=]", re.IGNORECASE),
    re.compile(r"(^|[,{])\s*mw\s*[:=]", re.IGNORECASE),
    re.compile(r"\bpair_id\s*,\s*hour_ending\b", re.IGNORECASE),
    re.compile(r"\bsource\s*,\s*sink\b", re.IGNORECASE),
    re.compile(r"\bsettlement_point\b", re.IGNORECASE),
)

CONTENT_SCAN_SUFFIXES = {".csv", ".json", ".md", ".txt", ".yml", ".yaml"}
CONTENT_SCAN_EXEMPT = {
    "scripts/verify_public_repo.py",
    "hashes/verification_guide.md",
}
ALLOWED_TIMESTAMP_STATUSES = {"timestamp_pending", "opentimestamps_proof", "timestamp_failed_giving_up"}
ALLOWED_OUTCOME_STATUSES = {"outcome_joined", "outcome_partial", "settlement_missing"}


def _read_csv_rows(path: Path, columns: tuple[str, ...]) -> tuple[list[dict[str, str]], list[str]]:
    if not path.is_file():
        return [], [f"missing csv: {path}"]
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != columns:
            return [], [f"schema mismatch in {path}: {reader.fieldnames}"]
        return list(reader), []


def _read_base_csv_rows(
    root: Path,
    *,
    base_ref: str,
    relpath: Path,
    columns: tuple[str, ...],
) -> tuple[list[dict[str, str]], list[str]]:
    result = subprocess.run(
        ["git", "--no-optional-locks", "show", f"{base_ref}:{relpath.as_posix()}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return [], []
    reader = csv.DictReader(result.stdout.splitlines())
    if tuple(reader.fieldnames or ()) != columns:
        return [], [f"base schema mismatch at {base_ref}:{relpath.as_posix()}: {reader.fieldnames}"]
    return list(reader), []


def _is_timestamp_only_upgrade(prior: dict[str, str], current: dict[str, str]) -> bool:
    for column in LEDGER_COLUMNS:
        if column in {"timestamp_status", "opentimestamps_proof_path"}:
            continue
        if prior.get(column, "") != current.get(column, ""):
            return False
    return (
        prior.get("timestamp_status") == "timestamp_pending"
        and not prior.get("opentimestamps_proof_path")
        and current.get("timestamp_status") == "opentimestamps_proof"
        and bool(current.get("opentimestamps_proof_path"))
    )


def _verify_append_only_csv(
    root: Path,
    *,
    relpath: Path,
    columns: tuple[str, ...],
    base_ref: str,
    allow_timestamp_upgrade: bool = False,
) -> list[str]:
    current_rows, current_errors = _read_csv_rows(root / relpath, columns)
    if current_errors:
        return current_errors
    base_rows, base_errors = _read_base_csv_rows(root, base_ref=base_ref, relpath=relpath, columns=columns)
    if base_errors:
        return base_errors
    if len(current_rows) < len(base_rows):
        return [f"{relpath.as_posix()} is not append-only: row count shrank {len(base_rows)} -> {len(current_rows)}"]
    for idx, prior in enumerate(base_rows):
        current = current_rows[idx]
        expected = {name: prior.get(name, "") for name in columns}
        actual = {name: current.get(name, "") for name in columns}
        if actual == expected:
            continue
        if allow_timestamp_upgrade and _is_timestamp_only_upgrade(prior, current):
            continue
        return [f"{relpath.as_posix()} is not append-only: prior row {idx + 2} was modified"]
    return []


def _verify_daily_ledger(root: Path, append_only_base_ref: str | None) -> tuple[list[dict[str, str]], list[str]]:
    rows, errors = _read_csv_rows(root / DAILY_LEDGER, LEDGER_COLUMNS)
    if append_only_base_ref:
        errors.extend(
            _verify_append_only_csv(
                root,
                relpath=DAILY_LEDGER,
                columns=LEDGER_COLUMNS,
                base_ref=append_only_base_ref,
                allow_timestamp_upgrade=True,
            )
        )

    seen: set[tuple[str, str, str, str]] = set()
    manifest_hashes: set[str] = set()
    for idx, row in enumerate(rows, start=2):
        key = (row["as_of_date"], row["delivery_date"], row["carrier"], row["prospective_or_backfill"])
        if key in seen:
            errors.append(f"duplicate daily ledger key at line {idx}: {key}")
        seen.add(key)
        manifest_hashes.add(row["manifest_sha256"])
        if row["carrier"] != "w31":
            errors.append(f"daily ledger line {idx} must use carrier=w31, got {row['carrier']!r}")
        if row["prospective_or_backfill"] != "prospective":
            errors.append(f"daily ledger line {idx} must be prospective-only")
        if not row["manifest_sha256"]:
            errors.append(f"daily ledger line {idx} missing manifest_sha256")
        if not row["methodology_version"]:
            errors.append(f"daily ledger line {idx} missing methodology_version")
        if row["valid_day_status"] == "excluded" and not row["exclusion_reason"]:
            errors.append(f"daily ledger line {idx} excluded without exclusion_reason")
        if row["timestamp_status"] not in ALLOWED_TIMESTAMP_STATUSES:
            errors.append(f"daily ledger line {idx} has unexpected timestamp_status={row['timestamp_status']!r}")
        proof_path = row["opentimestamps_proof_path"]
        if row["timestamp_status"] == "opentimestamps_proof":
            if not proof_path:
                errors.append(f"daily ledger line {idx} missing opentimestamps_proof_path")
            elif not proof_path.startswith("hashes/opentimestamps/"):
                errors.append(f"daily ledger line {idx} proof path must be under hashes/opentimestamps/")
        if proof_path and not (root / proof_path).is_file():
            errors.append(f"daily ledger line {idx} proof path does not exist: {proof_path}")
        correction_of = row["correction_of_manifest_sha256"]
        if correction_of and correction_of not in manifest_hashes:
            errors.append(f"daily ledger line {idx} correction_of_manifest_sha256 does not reference an earlier row")
    return rows, errors


def _verify_backfill_ledger(root: Path, append_only_base_ref: str | None) -> list[str]:
    rows, errors = _read_csv_rows(root / BACKFILL_LEDGER, LEDGER_COLUMNS)
    if append_only_base_ref:
        errors.extend(
            _verify_append_only_csv(
                root,
                relpath=BACKFILL_LEDGER,
                columns=LEDGER_COLUMNS,
                base_ref=append_only_base_ref,
            )
        )
    seen: set[tuple[str, str, str, str]] = set()
    for idx, row in enumerate(rows, start=2):
        key = (row["as_of_date"], row["delivery_date"], row["carrier"], row["prospective_or_backfill"])
        if key in seen:
            errors.append(f"duplicate backfill ledger key at line {idx}: {key}")
        seen.add(key)
        if row["carrier"] != "w31":
            errors.append(f"backfill ledger line {idx} must use carrier=w31, got {row['carrier']!r}")
        if row["prospective_or_backfill"] != "backfill":
            errors.append(f"backfill ledger line {idx} must be marked backfill")
    return errors


def _verify_outcome_summaries(
    root: Path,
    *,
    ledger_rows: list[dict[str, str]],
    append_only_base_ref: str | None,
) -> list[str]:
    path = root / OUTCOME_SUMMARIES
    if not path.exists():
        return []
    rows, errors = _read_csv_rows(path, OUTCOME_SUMMARY_COLUMNS)
    if append_only_base_ref:
        errors.extend(
            _verify_append_only_csv(
                root,
                relpath=OUTCOME_SUMMARIES,
                columns=OUTCOME_SUMMARY_COLUMNS,
                base_ref=append_only_base_ref,
            )
        )

    ledger_by_manifest = {row["manifest_sha256"]: row for row in ledger_rows if row.get("manifest_sha256")}
    seen: set[tuple[str, str, str, str]] = set()
    for idx, row in enumerate(rows, start=2):
        key = (row["as_of_date"], row["delivery_date"], row["carrier"], row["manifest_sha256"])
        if key in seen:
            errors.append(f"duplicate outcome summary key at line {idx}: {key}")
        seen.add(key)
        if row["carrier"] != "w31":
            errors.append(f"outcome summary line {idx} must use carrier=w31, got {row['carrier']!r}")
        if row["outcome_status"] not in ALLOWED_OUTCOME_STATUSES:
            errors.append(f"outcome summary line {idx} has unexpected outcome_status={row['outcome_status']!r}")
        if not row["methodology_version"]:
            errors.append(f"outcome summary line {idx} missing methodology_version")
        if not row["rows_counted_sha256"]:
            errors.append(f"outcome summary line {idx} missing rows_counted_sha256")
        if not row["private_outcome_sha256"]:
            errors.append(f"outcome summary line {idx} missing private_outcome_sha256")
        if row["outcome_status"] in {"outcome_joined", "outcome_partial"} and not row["ercot_data_snapshot_sha256"]:
            errors.append(f"outcome summary line {idx} missing ercot_data_snapshot_sha256")
        ledger_row = ledger_by_manifest.get(row["manifest_sha256"])
        if ledger_row is None:
            errors.append(f"outcome summary line {idx} does not reference a public ledger manifest")
        elif (
            ledger_row["as_of_date"] != row["as_of_date"]
            or ledger_row["delivery_date"] != row["delivery_date"]
            or ledger_row["carrier"] != row["carrier"]
            or ledger_row["methodology_version"] != row["methodology_version"]
        ):
            errors.append(f"outcome summary line {idx} does not match referenced ledger row")
    return errors


def _verify_reports(root: Path) -> list[str]:
    errors: list[str] = []
    for report_root in (root / "reports" / "weekly", root / "reports" / "monthly"):
        if not report_root.exists():
            continue
        for markdown_path in report_root.glob("*.md"):
            if markdown_path.name == "README.md":
                continue
            rel = markdown_path.relative_to(root).as_posix()
            text = markdown_path.read_text(encoding="utf-8")
            if "Generated by ptp-trade track-record automation. Do not edit by hand." not in text:
                errors.append(f"report missing generated header: {rel}")
            if "Rows counted SHA256:" not in text:
                errors.append(f"report missing rows_counted_sha256: {rel}")
            if "Methodology versions:" not in text:
                errors.append(f"report missing methodology versions: {rel}")
            if not markdown_path.with_suffix(".csv").is_file():
                errors.append(f"report missing companion csv: {markdown_path.with_suffix('.csv').relative_to(root).as_posix()}")
    return errors


def _verify_privacy_boundary(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        lowered = rel.lower()
        for pattern in FORBIDDEN_PATH_PATTERNS:
            if pattern.search(lowered):
                errors.append(f"forbidden public artifact path: {rel}")
                break
        if rel in CONTENT_SCAN_EXEMPT or path.suffix.lower() not in CONTENT_SCAN_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in FORBIDDEN_CONTENT_PATTERNS:
            if pattern.search(text):
                errors.append(f"forbidden raw-signal content pattern {pattern.pattern!r} in {rel}")
                break
    return errors


def verify(root: Path, *, append_only_base_ref: str | None = None) -> list[str]:
    errors: list[str] = []
    ledger_rows, ledger_errors = _verify_daily_ledger(root, append_only_base_ref)
    errors.extend(ledger_errors)
    errors.extend(_verify_backfill_ledger(root, append_only_base_ref))
    errors.extend(_verify_outcome_summaries(root, ledger_rows=ledger_rows, append_only_base_ref=append_only_base_ref))
    errors.extend(_verify_reports(root))
    errors.extend(_verify_privacy_boundary(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify public ERCOT PTP track-record repo guardrails.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument(
        "--append-only-base-ref",
        default=None,
        help="Optional git ref whose public CSV rows must remain an exact prefix of current rows.",
    )
    args = parser.parse_args()
    errors = verify(Path(args.root).resolve(), append_only_base_ref=args.append_only_base_ref)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VERIFY_OK public_track_record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
