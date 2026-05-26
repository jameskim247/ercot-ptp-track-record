# Valid-Day Rules

A prospective day is valid only when all required conditions hold:

- W31 config was loaded.
- Weather preflight passed.
- Advisory artifacts were produced before the cutoff.
- Canary status was OK.
- No manual rerun occurred after outcome data was available.
- Required artifacts existed and hashed successfully.
- No exclusion flag applied.

If any rule fails, the row must still be recorded as `invalid` or `excluded`.
