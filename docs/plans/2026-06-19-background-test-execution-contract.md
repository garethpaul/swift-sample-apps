# Background Test Execution Contract

Status: Completed

## Context

Finite black-box background-selection probes cannot prove that production is a
pure mapping. A custom raw-value initializer with static call-count state can
behave correctly for every finite verifier ceiling and fail on the next valid
selection. Caller-controlled `PYTHON`, `XCODEBUILD`, `SWIFTC`, and `PATH`
wrappers can also make local Make evidence non-authoritative if Make trusts
them.

## Requirements

- Preserve the production selection mapping as a small audited pure switch.
- Reject added state, counters, custom raw-value initialization, process or
  environment access, filesystem access, clock access, output, and test-aware
  branches structurally rather than by increasing a finite call ceiling.
- Keep the Swift adapter as raw observation only; expectations and verdicts
  remain in the Python verifier.
- Keep a known-broken production negative control and long-sequence regression
  checks, including the 4,097-call bypass, as evidence that the oracle runs.
- Resolve Python, Swift, and Xcode tools from trusted absolute locations so
  Make variables, `PATH` wrappers, and symlinks cannot replace the gates.
- Preserve hosted iOS Simulator validation.

## Work Completed

- Replaced `RawRepresentable` production with an explicit `switch`-backed
  `BackgroundSelection` model and a `buttonTag` property.
- Added `scripts/verify-background-selection.py`, which exact-source validates
  production and adapter files before compiling any black-box observer.
- Changed the Swift adapter to emit raw observations only.
- Added regression tests for the exact 4,097-call counter bypass, counter
  threshold families, test-aware production, caller Make overrides, PATH
  wrappers, and symlink probes.
- Added trusted tool resolution for Make and direct runner execution.
- Indexed the structural proof evidence in README, SECURITY, VISION, and
  CHANGES.

## Verification

- Exact 4,097-call and broader counter-threshold mutations passed before the
  structural verifier and are rejected after it.
- Process/test-aware production mutations are rejected structurally.
- Caller `PYTHON`, `XCODEBUILD`, `SWIFTC`, PATH-wrapper, and symlink probes do
  not replace trusted local gates.
- Repository and external-directory `make check` must pass before publication.
- Exact-head hosted `build` and `contract` checks remain required after push.
