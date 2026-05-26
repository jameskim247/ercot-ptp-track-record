# Exclusion Rules

Exclusions must be rare, explicit, and machine-readable.

Allowed exclusion categories:

- Upstream market data outage.
- Weather preflight failure.
- Canary failure.
- Advisory export failure before publication.
- Manual override or post-outcome rerun.
- Public publication failure that cannot be repaired without changing evidence.

Excluded days remain in the ledger with `valid_day_status=excluded` and a non-empty `exclusion_reason`.
