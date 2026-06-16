#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_AS_OF_DATE = "2099-01-01"
FIXTURE_DELIVERY_DATE = "2099-01-02"
FIXTURE_PUBLICATION_TIME_CT = "2099-01-01T09:45:00-05:00"
FIXTURE_TIMESTAMPED_AT_UTC = "2099-01-01T15:00:00+00:00"
FIXTURE_REPORT_DATE = "2099-01-05"


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


def _write_status_docs(repo: Path, verifier) -> None:
    summary = verifier._status_summary(repo)
    (repo / "README.md").write_text(verifier._render_readme(summary), encoding="utf-8")
    (repo / "carrier" / "current.md").write_text(verifier._render_current_carrier(summary), encoding="utf-8")


def _replace_status_line(path: Path, *, prefix: str, replacement: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = replacement
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise AssertionError(f"missing status line prefix {prefix!r} in {path}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _append_terminal_timestamp_fixture(repo: Path, verifier, *, notes: str) -> None:
    manifest_sha = "a" * 64
    row = {name: "" for name in verifier.LEDGER_COLUMNS}
    row.update(
        {
            "as_of_date": FIXTURE_AS_OF_DATE,
            "delivery_date": FIXTURE_DELIVERY_DATE,
            "carrier": "w31",
            "model_label": "weather-w31-selftest",
            "git_commit": "deadbeef",
            "config_hash": "b" * 64,
            "carrier_metadata_sha256": "c" * 64,
            "methodology_version": "m2026.05.26.v1",
            "prospective_or_backfill": "prospective",
            "pipeline_status": "SUCCESS",
            "valid_day_status": "valid",
            "publication_time_ct": FIXTURE_PUBLICATION_TIME_CT,
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

    proof_input = repo / "hashes" / "opentimestamps" / "2099" / "01" / "2099-01-01_w31_aaaaaaaaaaaa.txt"
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
            "timestamped_at_utc": FIXTURE_REPORT_DATE + "T12:00:00+00:00",
            "notes": notes,
        }
    )
    with (repo / verifier.TIMESTAMP_PROOFS).open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=verifier.TIMESTAMP_PROOF_COLUMNS).writerow(proof_row)
    _write_status_docs(repo, verifier)


def _append_pending_timestamp_fixture(repo: Path, verifier) -> Path:
    manifest_sha = "b" * 64
    row = {name: "" for name in verifier.LEDGER_COLUMNS}
    row.update(
        {
            "as_of_date": FIXTURE_AS_OF_DATE,
            "delivery_date": FIXTURE_DELIVERY_DATE,
            "carrier": "w31",
            "model_label": "weather-w31-selftest",
            "git_commit": "deadbeef",
            "config_hash": "c" * 64,
            "carrier_metadata_sha256": "d" * 64,
            "methodology_version": "m2026.05.26.v1",
            "prospective_or_backfill": "prospective",
            "pipeline_status": "SUCCESS",
            "valid_day_status": "valid",
            "publication_time_ct": FIXTURE_PUBLICATION_TIME_CT,
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
    _write_status_docs(repo, verifier)
    return proof_input


def _append_opentimestamps_fixture(repo: Path, verifier) -> None:
    manifest_sha = "c" * 64
    row = {name: "" for name in verifier.LEDGER_COLUMNS}
    row.update(
        {
            "as_of_date": FIXTURE_AS_OF_DATE,
            "delivery_date": FIXTURE_DELIVERY_DATE,
            "carrier": "w31",
            "model_label": "weather-w31-selftest",
            "git_commit": "deadbeef",
            "config_hash": "d" * 64,
            "carrier_metadata_sha256": "e" * 64,
            "methodology_version": "m2026.05.26.v1",
            "prospective_or_backfill": "prospective",
            "pipeline_status": "SUCCESS",
            "valid_day_status": "valid",
            "publication_time_ct": FIXTURE_PUBLICATION_TIME_CT,
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
            "timestamped_at_utc": FIXTURE_TIMESTAMPED_AT_UTC,
            "notes": "same-run",
        }
    )
    with (repo / verifier.TIMESTAMP_PROOFS).open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=verifier.TIMESTAMP_PROOF_COLUMNS).writerow(proof_row)
    _write_status_docs(repo, verifier)


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
        "as_of_date": FIXTURE_AS_OF_DATE,
        "delivery_date": FIXTURE_DELIVERY_DATE,
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
        "ercot_data_fetch_time_utc": FIXTURE_REPORT_DATE + "T12:00:00+00:00",
        "ercot_data_watermark": FIXTURE_DELIVERY_DATE,
        "private_outcome_sha256": "5" * 64,
    }
    outcome_path = repo / verifier.OUTCOME_SUMMARIES
    outcome_path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows = _read_csv(outcome_path) if outcome_path.is_file() else []
    fixture_key = (row["as_of_date"], row["delivery_date"], row["carrier"], row["manifest_sha256"])
    existing_rows = [
        existing
        for existing in existing_rows
        if (existing["as_of_date"], existing["delivery_date"], existing["carrier"], existing["manifest_sha256"]) != fixture_key
    ]
    with outcome_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=verifier.OUTCOME_SUMMARY_COLUMNS)
        writer.writeheader()
        for existing in existing_rows:
            writer.writerow({name: existing.get(name, "") for name in verifier.OUTCOME_SUMMARY_COLUMNS})
        writer.writerow(row)

    report_dir = repo / "reports" / "weekly"
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / f"{FIXTURE_DELIVERY_DATE}_to_{FIXTURE_DELIVERY_DATE}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=verifier.OUTCOME_SUMMARY_COLUMNS)
        writer.writeheader()
        writer.writerow(row)

    start = verifier.date.fromisoformat(FIXTURE_DELIVERY_DATE)
    report_date = verifier.date.fromisoformat(FIXTURE_REPORT_DATE)
    markdown_path = report_dir / f"{FIXTURE_DELIVERY_DATE}_to_{FIXTURE_DELIVERY_DATE}.md"
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
    _write_status_docs(repo, verifier)
    return markdown_path


def _assert_forbidden_public_paths(repo: Path, verifier, relpaths: tuple[str, ...]) -> bool:
    for relpath in relpaths:
        path = repo / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"private fixture\n")
    errors = verifier.verify(repo)
    missing = [
        relpath
        for relpath in relpaths
        if not any("forbidden public artifact path" in error and relpath in error for error in errors)
    ]
    if missing:
        print("private artifact paths should fail public verification:", file=sys.stderr)
        for relpath in missing:
            print(f"- missing error for {relpath}", file=sys.stderr)
        for error in errors:
            print(f"- observed: {error}", file=sys.stderr)
        return False
    return True


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
        if not _assert_forbidden_public_paths(
            repo,
            verifier,
            (
                "2026/06/01/w31/manifest.json",
                "runtime/track_record/backups/vault_backup_20990101T000000Z.tar.gz",
                "runtime/track_record/backups/vault_backup_20990101T000000Z.zip",
                "reports/audits/outcome_join.csv",
                "out/cc2/paper/logs/pipeline_2099-01-01.json",
                "out/cc2/paper/signals/positions_2099-01-01.parquet",
                "private_vault/2026/06/01/w31/manifest.json",
            ),
        ):
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        path = repo / verifier.PUBLICATION_EXCEPTIONS
        rows = _read_csv(path)
        rows.append(dict(rows[0]))
        _write_csv(path, verifier.PUBLICATION_EXCEPTION_COLUMNS, rows)
        errors = verifier.verify(repo)
        if not any("duplicate publication exception key" in error for error in errors):
            print("duplicate publication exception should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        path = repo / verifier.PUBLICATION_EXCEPTIONS
        rows = _read_csv(path)
        rows[0]["as_of_date"] = "2026-06-01"
        _write_csv(path, verifier.PUBLICATION_EXCEPTION_COLUMNS, rows)
        errors = verifier.verify(repo)
        if not any("conflicts with normal prospective ledger row" in error for error in errors):
            print("publication exception overlapping normal ledger row should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        path = repo / verifier.PRIVATE_VAULT_EXCEPTIONS
        rows = _read_csv(path)
        rows[0]["attestation_path"] = "attestations/private_manifest/2026/06/wrong.json"
        _write_csv(path, verifier.PRIVATE_VAULT_EXCEPTION_COLUMNS, rows)
        errors = verifier.verify(repo)
        if not any("attestation_path must be" in error for error in errors):
            print("private-vault exception with nondeterministic attestation path should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        path = repo / "attestations" / "private_manifest" / "2026" / "06" / "2026-06-01_w31_8ae1e9695844.json"
        payload = verifier.json.loads(path.read_text(encoding="utf-8"))
        payload["manifest_sha256"] = "0" * 64
        path.write_text(verifier.json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        errors = verifier.verify(repo)
        if not any("attestation manifest_sha256 mismatch" in error for error in errors):
            print("private-vault exception with tampered attestation payload should fail", file=sys.stderr)
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
        _append_terminal_timestamp_fixture(repo, verifier, notes="ots retry gave up after configured retry window")
        _write_report_fixture(repo, verifier)
        outcome_path = repo / verifier.OUTCOME_SUMMARIES
        with outcome_path.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        rows[0]["outcome_status"] = "outcome_partial"
        with outcome_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=verifier.OUTCOME_SUMMARY_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        errors = verifier.verify(repo)
        if not any("must be settlement-complete" in error for error in errors):
            print("incomplete public outcome summary should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        _append_terminal_timestamp_fixture(repo, verifier, notes="ots retry gave up after configured retry window")
        _write_report_fixture(repo, verifier)
        ledger_path = repo / verifier.DAILY_LEDGER
        with ledger_path.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        rows[-1]["valid_day_status"] = "invalid"
        with ledger_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=verifier.LEDGER_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        errors = verifier.verify(repo)
        if not any("references non-valid ledger row" in error for error in errors):
            print("public outcome summary referencing invalid ledger row should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

        rows[-1]["valid_day_status"] = "valid"
        rows[-1]["prospective_or_backfill"] = "backfill"
        with ledger_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=verifier.LEDGER_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        errors = verifier.verify(repo)
        if not any("references non-prospective ledger row" in error for error in errors):
            print("public outcome summary referencing backfill ledger row should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        log_path = repo / "carrier" / "operational_log.md"
        log_path.write_text(
            log_path.read_text(encoding="utf-8") + "source=SRC shadow_bid=99 /home/jk/private w0\n",
            encoding="utf-8",
        )
        errors = verifier.verify(repo)
        if not any("operational log contains forbidden public content pattern" in error for error in errors):
            print("unsafe operational log should fail", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="public-verifier-selftest-") as tmp_raw:
        repo = _copy_public_fixture(Path(tmp_raw))
        readme = repo / "README.md"
        current = repo / "carrier" / "current.md"
        _replace_status_line(readme, prefix="- Prospective live rows:", replacement="- Prospective live rows: 999")
        _replace_status_line(current, prefix="- Valid rows:", replacement="- Valid rows: 999")
        errors = verifier.verify(repo)
        if not any("deterministic regeneration: README.md" in error for error in errors):
            print("tampered README should fail status-doc verification", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        if not any("deterministic regeneration: carrier/current.md" in error for error in errors):
            print("tampered current carrier doc should fail status-doc verification", file=sys.stderr)
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
