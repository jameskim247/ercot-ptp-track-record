# Risk Metrics

Public reports may include delayed aggregate metrics such as:

- Valid-day count.
- Excluded-day count.
- Expected EV.
- Expected filled EV.
- Realized filled PnL.
- Fill rate.
- Hit rate.
- Worst day.
- Max drawdown.
- Sharpe / Sortino where enough observations exist.

Every public performance claim must reference ledger rows and delayed outcome summaries. Reports spanning methodology changes must segment results by methodology version.

## Report Cadence

Daily outcome summaries are eligible for publication only after the advisory delivery date has passed, the settlement/outcome join is complete, and all rows counted by the summary reference valid prospective public ledger rows.

Weekly reports are generated for the previous calendar week after at least five settlement-complete valid outcome days are available for that week. If fewer than five valid outcome days are available, the weekly report is skipped rather than partially reported.

Monthly reports are generated after month-end outcome completeness checks pass and at least 30 delayed valid prospective track-record days are available. Monthly reports must state the row count, date range, methodology versions covered, and whether any days were invalid or excluded.

Reports are never generated from backfill rows. Backfill evidence, if ever published, remains separate from prospective performance claims.
