# Operational Log

Generated automation will publish public-safe operational events here.

Allowed content:

- State transitions.
- Retry counts.
- Deadline misses.
- Public ledger row identifiers.
- Timestamp pending/resolved status.
- Correction references.

Forbidden content:

- Private vault absolute paths or hostnames.
- Raw signal rows.
- Same-day source/sink/hour/MW details.
- W0 comparator details.
- Environment variables, tokens, SSH paths, or secret-manager identifiers.
- Error messages that expose private infrastructure.
