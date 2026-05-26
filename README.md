# ERCOT PTP Track Record

Public audit repository for timestamped ERCOT PTP track-record discipline.

This repository publishes public proof artifacts for the current public carrier, W31. It is designed to prove process discipline: prospective hash publication, append-only handling, delayed aggregate reporting, correction lineage, and verification rules.

This repository does not publish live trade instructions, raw scored signals, model internals, W0 baseline evidence, or same-day actionable advisory details.

## Public Artifacts

- `hashes/daily_manifest_hashes.csv`: prospective public manifest hash ledger.
- `hashes/backfill_manifest_hashes.csv`: historical/backfill hash ledger, never counted in prospective reports.
- `hashes/opentimestamps/`: timestamp proofs when available.
- `attestations/private_manifest/`: signed attestations that a public hash matched a private manifest.
- `carrier/current.md`: current public carrier status.
- `reports/weekly/` and `reports/monthly/`: delayed aggregate reports once enough settled outcomes exist.
- `corrections/`: append-only correction notes.
- `methodology/`: public rules, versioning, risk metrics, exclusions, and disclaimers.

## Current Status

- Public carrier: W31.
- Methodology version: `m2026.05.26.v1`.
- Prospective live rows: not started in this repository yet.
- Backfill rows: none.

## Verification

Run:

```bash
python3 scripts/verify_public_repo.py .
```

For manual verification, start with `hashes/verification_guide.md`.

## Private Boundary

Full manifests, advisories, outcome joins, W31-vs-W0 evidence, walk-forward evidence, canary logs, and reproducibility materials remain in the private audit vault and diligence room. Serious buyers may request that package under NDA.
