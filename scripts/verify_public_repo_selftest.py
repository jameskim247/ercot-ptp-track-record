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


def _append_pending_timestamp_fixture(repo: Path, verifier) -> Path:
    manifest_sha = "b" * 64
    row = {name: "" for name in verifier.LEDGER_COLUMNS}
    row.update(
        {
            "as_of_date": "2026-05-26",
            "delivery_date": "2026-05-27",
            "carrier": "w31",
            "model_label": "weather-w31-selftest",
            "git_commit": "deadbeef",
            "config_hash": "c" * 64,
            "carrier_metadata_sha256": "d" * 64,
            "methodology_version": "m2026.05.26.v1",
            "prospective_or_backfill": "prospective",
            "pipeline_status": "SUCCESS",
            "valid_day_status": "valid",
            "publication_time_ct": "2026-05-26T09:45:00-05:00",
            "manifest_sha256": manifest_sha,
            "advisory_detail_sha256": "e" * 64,
            "advisory_csv_sha256": "f" * 64,
            "positions_sha256": "1" * 64,
            "scored_signals_sha256": "2" * 64,
            "pipeline_log_sha256": "3" * 64,
            "timestamp_status": "timestamp_pending",
        }
    )
    with (repo / verifier.DAILY_LEDGER).open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=verifier.LEDGER_COLUMNS).writerow(row)

    proof_input = repo / verifier._timestamp_proof_input_relpath(row)
    proof_input.parent.mkdir(parents=True, exist_ok=True)
    proof_input.write_text(verifier._timestamp_proof_input_payload(row), encoding="utf-8")
    return proof_input


def _append_opentimestamps_fixture(repo: Path, verifier) -> None:
    manifest_sha = "c" * 64
    row = {name: "" for name in verifier.LEDGER_COLUMNS}
    row.update(
        {
            "as_of_date": "2026-05-26",
            "delivery_date": "2026-05-27",
            "carrier": "w31",
            "model_label": "weather-w31-selftest",
            "git_commit": "deadbeef",
            "config_hash": "d" * 64,
            "carrier_metadata_sha256": "e" * 64,
            "methodology_version": "m2026.05.26.v1",
            "prospective_or_backfill": "prospective",
            "pipeline_status": "SUCCESS",
            "valid_day_status": "valid",
            "publication_time_ct": "2026-05-26T09:45:00-05:00",
            "manifest_sha256": manifest_sha,
            "advisory_detail_sha256": "f" * 64,
            "advisory_csv_sha256": "1" * 64,
            "positions_sha256": "2" * 64,
            "scored_signals_sha256": "3" * 64,
            "pipeline_log_sha256": "4" * 64,
            "timestamp_status": "opentimestamps_proof",
        }
    )
    proof_input = repo / verifier._timestamp_proof_input_relpath(row)
    proof_input.parent.mkdir(parents=True, exist_ok=True)
    proof_input.write_text(verifier._timestamp_proof_input_payload(row), encoding="utf-8")
    proof_path = proof_input.with_suffix(".ots")
    proof_path.write_text("fake opentimestamps proof\n", encoding="utf-8")
    row["opentimestamps_proof_path"] = proof_path.relative_to(repo).as_posix()

    with (repo / verifier.DAILY_LEDGER).open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=verifier.LEDGER_COLUMNS).writerow(row)

    proof_row = {name: "" for name in verifier.TIMESTAMP_PROOF_COLUMNS}
    proof_row.update(
        {
            "as_of_date": row["as_of_date"],
            "delivery_date": row["delivery_date"],
            "carrier": row["carrier"],
            "manifest_sha256": manifest_sha,
            "public_ledger_row_sha256": verifier._ledger_row_sha256(row),
            "timestamp_status": "opentimestamps_proof",
            "proof_input_path": proof_input.relative_to(repo).as_posix(),
            "proof_input_sha256": verifier._sha256_file(proof_input),
            "opentimestamps_proof_path": row["opentimestamps_proof_path"],
            "opentimestamps_proof_sha256": verifier._sha256_file(proof_path),
            "timestamped_at_utc": "2026-05-26T15:00:00+00:00",
            "notes": "same-run",
        }
    )
    with (repo / verifier.TIMESTAMP_PROOFS).open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=verifier.TIMESTAMP_PROOF_COLUMNS).writerow(proof_row)


def _write_fake_ots(path: Path, *, exit_code: int) -> Path:
    path.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" != \"verify\" ]; then\n"
        "  echo unexpected command >&2\n"
        "  exit 64\n"
        "fi\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _write_report_fixture(repo: Path, verifier) -> Path:
    row = {
        "as_of_date": "2026-05-26",
        "delivery_date": "2026-05-27",
        "carrier": "w31",
        "manifest_sha256": "a" * 64,
        "methodology_version": "m2026.05.26.v1",
        "outcome_status": "outcome_joined",
        "rows_counted_sha256": "3" * 64,
        "position_count": "10",
        "priced_position_count": "10",
        "missing_price_position_count": "0",
        "total_mw": "100",
        "filled_position_count": "5",
        "filled_mw": "50",
        "fill_rate": "0.5",
        "hit_rate": "0.6",
        "realized_filled_pnl": "100",
        "realized_pnl_if_filled": "200",
        "worst_path_hour_pnl": "-10",
        "expected_ev": "75",
        "expected_filled_ev": "35",
        "ercot_data_source": "ercot-public-lmp-lake",
        "ercot_data_product": "lmp_hourly_da_rt",
        "ercot_data_snapshot_sha256": "4" * 64,
        "ercot_data_fetch_time_utc": "2026-05-30T12:00:00+00:00",
        "ercot_data_watermark": "2026-05-27",
        "private_outcome_sha256": "5" * 64,
    }
    outcome_path = repo / verifier.OUTCOME_SUMMARIES
    outcome_path.parent.mkdir(parents=True, exist_ok=True)
    with outcome_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=verifier.OUTCOME_SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerow(row)

    report_dir = repo / "reports" / "weekly"
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / "2026-05-27_to_2026-05-27.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=verifier.OUTCOME_SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerow(row)

    start = verifier.date.fromisoformat("2026-05-27")
    report_date = verifier.date.fromisoformat("2026-05-30")
    markdown_path = report_dir / "2026-05-27_to_2026-05-27.md"
    summary = verifier._report_summary(
        repo,
        kind="weekly",
        rows=[row],
        start_date=start,
        end_date=start,
        report_date=report_date,
        min_delay_days=2,
    )
    markdown_path.write_text(verifier._render_report_markdown(summary, [row]), encoding="utf-8")
    return markdown_path


def main() -> int:
    verifier = _load_verifier()
    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        _append_terminal_timestamp_fixture(repo, verifier, notes="ots retry gave up after configured retry window")
        _write_report_fixture(repo, verifier)
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

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        _append_terminal_timestamp_fixture(repo, verifier, notes="ots retry gave up after configured retry window")
        markdown_path = _write_report_fixture(repo, verifier)
        text = markdown_path.read_text(encoding="utf-8")
        markdown_path.write_text(text.replace("- Realized filled PnL: 100.0", "- Realized filled PnL: 999999.0"), encoding="utf-8")
        errors = verifier.verify(repo)
        if not any("markdown does not match deterministic regeneration" in error for error in errors):
            print("tampered report markdown should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        proof_input = _append_pending_timestamp_fixture(repo, verifier)
        errors = verifier.verify(repo)
        if errors:
            print("pending timestamp input fixture should verify, got:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

        proof_input.write_text("tampered\n", encoding="utf-8")
        errors = verifier.verify(repo)
        if not any("pending timestamp input payload mismatch" in error for error in errors):
            print("tampered pending timestamp input should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        tmp = Path(tmp_raw)
        repo = _copy_public_fixture(tmp)
        _append_opentimestamps_fixture(repo, verifier)
        errors = verifier.verify(repo, verify_opentimestamps=True, ots_bin=str(_write_fake_ots(tmp / "ots", exit_code=0)))
        if errors:
            print("OpenTimestamps CLI verification fixture should verify, got:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

        errors = verifier.verify(repo, verify_opentimestamps=True, ots_bin=str(_write_fake_ots(tmp / "bad-ots", exit_code=23)))
        if not any("OpenTimestamps verification failed" in error for error in errors):
            print("failing OpenTimestamps CLI should fail verification", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    print("SELFTEST_OK public_verifier")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
