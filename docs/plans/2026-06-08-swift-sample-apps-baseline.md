# Swift Sample Apps Baseline

## Status: Completed

## Context

`swift-sample-apps` is an archive of early Swift iOS samples covering background
switching, notes, Facebook login, Parse setup, Swift object examples, and a todo
list. The maintenance baseline should preserve the sample inventory while
keeping per-user Xcode state and credential-like markers out of git.

## Objectives

- Preserve each sample as an independent Xcode project with Swift sources and
  test stubs.
- Reject tracked Xcode user state and DerivedData-style artifacts.
- Scan tracked text files for known credential-like markers and tokenized URLs.
- Run sample inventory and hygiene checks through `make check`.
- Maintain completed maintenance plans under `docs/plans`.

## Work Completed

- Confirmed `make check` runs hygiene, sample inventory, and optional Xcode
  build checks.
- Added canonical `docs/plans` coverage for the current sample archive
  baseline.
- Extended hygiene checks to require completed `docs/plans` entries with
  `make check` verification.
- Updated README, VISION, and CHANGES to make the baseline discoverable.

## Verification

- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Add a README table describing each sample, purpose, and required services.
- Run sample builds on macOS with Xcode and document supported versions.
