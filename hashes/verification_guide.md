# Verification Guide

## Quick Check

```bash
python3 scripts/verify_public_repo.py .
```

For an append-only check against an earlier git ref:

```bash
python3 scripts/verify_public_repo.py . --append-only-base-ref origin/main
```

## Verify The Prospective Ledger

1. Open `hashes/daily_manifest_hashes.csv`.
2. Confirm the header matches the documented schema.
3. Confirm `carrier` is `w31`.
4. Confirm `prospective_or_backfill` is `prospective`.
5. Confirm no row has `carrier=w0`.
6. Confirm excluded rows include `exclusion_reason`.

## Verify Backfill Separation

Backfill rows belong only in `hashes/backfill_manifest_hashes.csv`. Buyer-facing prospective reports must not count backfill rows.

## Verify Append-Only History

Use git history to inspect row additions. Existing ledger rows should not be edited or deleted. Corrections must append a new row and a note under `corrections/`.

The verifier enforces this mechanically for the manifest ledgers and delayed outcome summary when `--append-only-base-ref` is supplied. Timestamp proof completion may update only `timestamp_status` and `opentimestamps_proof_path` from a pending row.

## Verify Timestamp Proofs

When `timestamp_status=opentimestamps_proof`, the `opentimestamps_proof_path` must exist under `hashes/opentimestamps/`.

With OpenTimestamps installed:

```bash
ots verify hashes/opentimestamps/YYYY/MM/<proof>.ots
```

## Verify Attestations

Attestations under `attestations/private_manifest/` disclose only public-safe fields: carrier, dates, manifest hash, ledger row hash, verifier commit, and signature.

The attestation proves that private verification ran. Full private manifests remain available only under NDA.

## Verify Outcome And Report Linkage

The public outcome summary, when present, must reference an existing public ledger `manifest_sha256`, include `rows_counted_sha256`, include the private outcome hash, and pin the ERCOT data snapshot hash once settlement data is joined.

Generated weekly and monthly reports must include a generated-file header, a companion CSV, `Rows counted SHA256`, and the methodology version set used for the covered period.

## Verify The Privacy Boundary

The verifier rejects raw signal artifact filenames and content patterns associated with execution-level rows, including `shadow_bid`, raw source/sink fields, point-level `mw`, pair/hour headers, and settlement-point rows.

## Public Boundary

This repo proves timestamp discipline and delayed public reporting. It does not reveal raw signals, live advisories, model internals, or W0 comparator data.
