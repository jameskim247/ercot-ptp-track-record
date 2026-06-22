# Methodology Changelog

## m2026.05.26.v1

- Initial public methodology.
- Public carrier code W31 is an audit identifier, not a public strategy description.
- Public ledger is prospective-only.
- Backfill ledger is separate and excluded from prospective reports.
- Corrections are append-only.
- Baseline and research comparison evidence remains private under NDA.

## m2026.05.26.v1+recovery-2026-06-21

- Outage-recovery methodology for the 2026-05-29..2026-06-05 outcome-join outage. See `methodology/recovery_policy.md`.
- Six delayed outcomes lost to the outage are recovered from retained positions plus matured settlement prices and counted, but marked via `outcome_methodology_version=m2026.05.26.v1+recovery-2026-06-21` and (for five of the six days) backfill ledger rows, so they remain distinguishable from normal prospective rows.
- The prospective-only series still excludes backfill; reports that include recovered outcomes render a `## Recovery-Included Outcomes` disclosure with the prospective-only vs recovery-inclusive split.
- A backfill ledger row may back an outcome only when that outcome is recovery-marked; this is enforced in the outcome-append path and in both verifiers.
