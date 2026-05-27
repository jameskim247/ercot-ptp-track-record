# Direct Push Control Change

Date: 2026-05-27

This note records the control change that makes routine W31 track-record publication direct-push compatible while preserving signed commits and protected branch controls.

Effective control model:

- Signed commits remain required on `main`.
- Force pushes and branch deletion remain disabled.
- Required pull-request review and required pre-push status check were removed from `main`.
- The publication operator must run local public/private verification before pushing.
- GitHub Actions remains the post-push public verification signal.
- Rollback evidence was captured before this change under snapshot id `20260527T055241Z_ercot-ptp-track-record`.

Operational implication: routine daily hash publications can use `--commit --signed-commit --push --require-public-push-compatible` instead of opening a pull request.
