# Background Switcher Build Canary

Status: Completed

## Context

Portable checks covered all six archived samples, but CI never invoked Xcode.
The Parse and Facebook projects reference absent legacy SDK frameworks, so a
repository-wide build would fail before evaluating the self-contained samples.

## Changes

- Added fixed Ubuntu 24.04 contract and macOS 15 build jobs with concurrency
  cancellation and pinned action revisions.
- Selected `background_switcher` as the explicit self-contained build canary.
- Migrated that app to Swift 5 syntax and an iOS 12 deployment target.
- Made Makefile paths independent of the caller's working directory.
- Extended static checks to preserve the canary boundary and avoid attempting
  projects that require missing legacy SDK frameworks.

## Verification

- `make check`
- `make -f /path/to/swift-sample-apps/Makefile check` from outside the repository
- negative workflow and Makefile mutation checks
- `git diff --check`
- GitHub Actions `contract` and `build` jobs
