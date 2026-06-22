# Outage Recovery Policy

## m2026.05.26.v1+recovery-2026-06-21

### What this covers

Between 2026-05-29 and 2026-06-05 the delayed outcome-join pipeline suffered an
outage. Six prospective trading days produced normal pre-deadline advisories, but
their delayed settlement outcomes were not joined on the normal schedule. Those
six outcomes have since been recovered by joining the retained positions to the
matured ERCOT DA/RT settlement prices:

| as_of_date | delivery_date | provenance | realized_filled_pnl |
|---|---|---|---:|
| 2026-05-29 | 2026-05-30 | recovered backfill (retained paper-output positions; no contemporaneous public hash — lowest tier) | -11968.26 |
| 2026-06-01 | 2026-06-02 | prospective (public hash `8ae1e969…`, OpenTimestamps-anchored; private manifest reconstructed and hash-verified against the attested artifacts) | -24468.475 |
| 2026-06-02 | 2026-06-03 | recovered backfill (retained private-vault manifest) | 1677.9725 |
| 2026-06-03 | 2026-06-04 | recovered backfill (retained private-vault manifest) | -240.935 |
| 2026-06-04 | 2026-06-05 | recovered backfill (retained private-vault manifest) | -3961.8925 |
| 2026-06-05 | 2026-06-06 | recovered backfill (retained private-vault manifest) | 25299.746667 |

### How recovered outcomes are counted and marked

These outcomes are counted in `reports/audits/daily_outcome_summaries.csv` and in
the weekly/monthly reports, but they are marked so they remain distinguishable
from normal prospective rows at two levels:

- every recovered outcome carries `outcome_methodology_version =
  m2026.05.26.v1+recovery-2026-06-21`;
- the five backfill-tier outcomes reference rows in
  `hashes/backfill_manifest_hashes.csv`, not the prospective daily ledger;
- any report that includes recovered outcomes renders a `## Recovery-Included
  Outcomes` section that states the recovery day count and PnL alongside the
  prospective-only day count and PnL, so both series can be read separately.

2026-06-01 is a genuine prospective day: it has a pre-deadline public hash row and
an OpenTimestamps proof. Only its consolidated private manifest file was lost
(recorded in `releases/private_vault_exceptions.csv` as
`private_manifest_unrecoverable`); it was reconstructed from the surviving
artifacts whose component hashes match the public attestation, so its recovered
outcome references the original prospective ledger row.

### What this policy does not do

- It does not forge prospective ledger rows or OpenTimestamps proofs for days that
  lacked them.
- It does not delete or alter `releases/publication_exceptions.csv` or
  `releases/private_vault_exceptions.csv`; those honest outage records remain.
- A backfill ledger row may back an outcome only when that outcome carries the
  recovery methodology marker; the public verifier enforces this.
