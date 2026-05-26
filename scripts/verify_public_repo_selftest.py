#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_verifier():
    path = REPO_ROOT / "scripts" / "verify_public_repo.py"
    spec = importlib.util.spec_from_file_location("verify_public_repo_under_selftest", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _copy_public_fixture(root: Path) -> Path:
    target = root / "repo"
    shutil.copytree(
        REPO_ROOT,
        target,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
    )
    return target


def _append_terminal_timestamp_fixture(repo: Path, verifier, *, notes: str) -> None:
    manifest_sha = "a" * 64
    row = {name: "" for name in verifier.LEDGER_COLUMNS}
    row.update(
        {
            "as_of_date": "2026-05-26",
            "delivery_date": "2026-05-27",
            "carrier": "w31",
            "model_label": "weather-w31-selftest",
            "git_commit": "deadbeef",
            "config_hash": "b" * 64,
            "carrier_metadata_sha256": "c" * 64,
            "methodology_version": "m2026.05.26.v1",
            "prospective_or_backfill": "prospective",
            "pipeline_status": "SUCCESS",
            "valid_day_status": "valid",
            "publication_time_ct": "2026-05-26T09:45:00-05:00",
            "manifest_sha256": manifest_sha,
            "advisory_detail_sha256": "d" * 64,
            "advisory_csv_sha256": "e" * 64,
            "positions_sha256": "f" * 64,
            "scored_signals_sha256": "1" * 64,
            "pipeline_log_sha256": "2" * 64,
            "timestamp_status": "timestamp_pending",
        }
    )
    with (repo / verifier.DAILY_LEDGER).open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=verifier.LEDGER_COLUMNS).writerow(row)

    proof_input = repo / "hashes" / "opentimestamps" / "2026" / "05" / "2026-05-26_w31_aaaaaaaaaaaa.txt"
    proof_input.parent.mkdir(parents=True, exist_ok=True)
    proof_input.write_text("terminal timestamp proof input\n", encoding="utf-8")

    proof_row = {name: "" for name in verifier.TIMESTAMP_PROOF_COLUMNS}
    proof_row.update(
        {
            "as_of_date": row["as_of_date"],
            "delivery_date": row["delivery_date"],
            "carrier": row["carrier"],
            "manifest_sha256": manifest_sha,
            "public_ledger_row_sha256": verifier._ledger_row_sha256(row),
            "timestamp_status": "timestamp_failed_giving_up",
            "proof_input_path": proof_input.relative_to(repo).as_posix(),
            "proof_input_sha256": verifier._sha256_file(proof_input),
            "timestamped_at_utc": "2026-06-03T12:00:00+00:00",
            "notes": notes,
        }
    )
    with (repo / verifier.TIMESTAMP_PROOFS).open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=verifier.TIMESTAMP_PROOF_COLUMNS).writerow(proof_row)


def main() -> int:
    verifier = _load_verifier()
    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        _append_terminal_timestamp_fixture(repo, verifier, notes="ots retry gave up after configured retry window")
        errors = verifier.verify(repo)
        if errors:
            print("terminal timestamp fixture should verify, got:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        _append_terminal_timestamp_fixture(repo, verifier, notes="")
        errors = verifier.verify(repo)
        if not any("failed timestamp line" in error and "requires notes" in error for error in errors):
            print("terminal timestamp fixture without notes should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    print("SELFTEST_OK public_verifier")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
