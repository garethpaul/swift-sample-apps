# Portable CI Hardening

## Status: Completed

## Context

The portable sample checks ran on a floating Ubuntu image and checkout retained
GitHub credentials. The workflow had no concurrency cancellation or manual
dispatch, while Makefile paths assumed the caller was in the repository root.

The self-contained `background_switcher` canary now compiles on hosted current
Xcode. The five remaining legacy projects are still static-only because their
SDK or migration requirements are not yet satisfied.

## Objectives

- Fix the hosted portable runner and keep all actions immutable.
- Disable persisted checkout credentials in both portable and macOS jobs while
  retaining read-only permissions.
- Cancel superseded runs and support manual verification.
- Make local checks independent of the caller's working directory.
- Enforce the complete reviewed workflow rather than isolated fragments.

## Work Completed

- Fixed the portable job to Ubuntu 24.04 and made both jobs use credential-free
  checkout.
- Added concurrency cancellation and `workflow_dispatch`.
- Preserved the root-anchored background-switcher canary build.
- Replaced fragment checks with an exact single-workflow contract.

## Verification

- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `make -f /path/to/swift-sample-apps/Makefile check` from an external cwd
- `git diff --check`
