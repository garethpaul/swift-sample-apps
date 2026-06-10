# Facebook Payload Guard and CI

## Status: Completed

## Context

The Facebook login sample force-cast profile payload fields, so absent or
malformed `id` and `name` values could crash the app. A user-cancelled login
also fell through to displaying an empty alert. The portable sample checks were
not automated in CI.

## Work Completed

- Optional-cast the Facebook user dictionary and required profile fields.
- Clear stale profile UI and show a bounded fallback message when user data is
  malformed.
- Return immediately for user-cancelled login instead of displaying an empty
  alert.
- Extended static contracts to prevent forced payload casts and cancellation
  regressions.
- Added a least-privilege Python 3.12 GitHub Actions workflow using immutable
  Node 24 action references.

## Verification

- `make check`
- Negative source and workflow mutation checks
- `python3 -m py_compile scripts/check-swift-samples.py`
- `git diff --check`

`xcodebuild` is unavailable in the Linux environment, so the existing Makefile
continues to build each sample only when the Apple toolchain is installed.
