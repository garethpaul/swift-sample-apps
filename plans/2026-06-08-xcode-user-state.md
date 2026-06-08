# Xcode User State Gate

## Problem

The repository contained tracked `xcuserdata` and `.xcuserstate` files generated
by a local Xcode user profile. Those files are machine-specific and can cause
noisy diffs or stale scheme state in a multi-sample repository.

## TDD Evidence

1. Added `scripts/check-swift-samples.py` and a Makefile `lint` target.
2. Ran `make lint` before cleanup and confirmed it failed on 15 tracked Xcode
   user-state paths.
3. Removed the tracked generated files, added ignore rules, and reran the full
   verification gate.

## Verification

- `make lint`
- `make test`
- `make build`
- `make verify`
- `git diff --check`
