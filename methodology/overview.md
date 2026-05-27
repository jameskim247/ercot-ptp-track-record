# Methodology Overview

This repository records public audit evidence for an ERCOT point-to-point advisory process. The public repo is intentionally proof-focused rather than signal-focused.

Core rules:

- Publish prospective evidence hashes before outcomes are known.
- Record invalid and excluded days instead of omitting them.
- Keep W31 as the only public carrier unless a future public carrier is explicitly promoted.
- Keep baseline and research comparison evidence private under NDA.
- Publish delayed aggregate outcomes only after settlement data is available.
- Preserve append-only history. Corrections append new rows and notes.

Public artifacts follow a commit-reveal pattern. The public repository commits to private advisory evidence with hashes, timestamps, signatures, and delayed aggregate outcomes. Private diligence materials reveal the committed substance only under the appropriate access tier.

Access tiers:

- Public: hash ledgers, timestamp proofs, verification rules, status docs, delayed aggregate reports, and correction records.
- NDA diligence: aggregate performance detail, risk decomposition, and private baseline comparison evidence.
- Executed commercial diligence: advisory and position-level evidence needed for execution review.
- Internal only: model internals, feature engineering, training data, and research workflow details.

Current methodology version: `m2026.05.26.v1`.
