# Verification Guide

## Quick Check

```bash
python3 scripts/verify_public_repo.py .
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

## Verify Timestamp Proofs

When `timestamp_status=opentimestamps_proof`, the `opentimestamps_proof_path` must exist under `hashes/opentimestamps/`.

With OpenTimestamps installed:

```bash
ots verify hashes/opentimestamps/YYYY/MM/<proof>.ots
```

## Verify Attestations

Attestations under `attestations/private_manifest/` disclose only public-safe fields: carrier, dates, manifest hash, ledger row hash, verifier commit, and signature.

The attestation proves that private verification ran. Full private manifests remain available only under NDA.

## Public Boundary

This repo proves timestamp discipline and delayed public reporting. It does not reveal raw signals, live advisories, model internals, or W0 comparator data.
