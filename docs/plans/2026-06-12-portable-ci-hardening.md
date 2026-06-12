# Portable CI Hardening

## Status: Completed

## Context

The portable sample checks ran on a floating Ubuntu image and checkout retained
GitHub credentials. The workflow had no concurrency cancellation or manual
dispatch, while Makefile paths assumed the caller was in the repository root.

The six archived iOS 8 projects are not claimed to compile with current Xcode;
this pass hardens only the existing portable verification boundary.

## Objectives

- Fix the hosted portable runner and keep all actions immutable.
- Disable persisted checkout credentials and retain read-only permissions.
- Cancel superseded runs and support manual verification.
- Make local checks independent of the caller's working directory.
- Enforce the complete reviewed workflow rather than isolated fragments.

## Work Completed

- Fixed the workflow to Ubuntu 24.04 with credential-free checkout.
- Added concurrency cancellation and `workflow_dispatch`.
- Anchored checker and Xcode project discovery paths to the Makefile location.
- Replaced fragment checks with an exact single-workflow contract.

## Verification

- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `make -f /path/to/swift-sample-apps/Makefile check` from an external cwd
- `git diff --check`
