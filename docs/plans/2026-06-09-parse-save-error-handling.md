# Parse Save Error Handling

## Status: Completed

## Context

The archived Parse sample creates a small object during launch and calls
`saveInBackgroundWithBlock`. Its callback ignored the `NSError` argument and
logged `Done` unconditionally, so save failures looked like success in local
diagnostics.

## Objectives

- Preserve the existing placeholder Parse object write.
- Check the callback `NSError` before reporting completion.
- Log explicit save failures without adding credentials or user data.
- Handle unsuccessful saves that do not provide error metadata.
- Extend static validation so the unconditional success log does not return.

## Work Completed

- Replaced the unconditional `NSLog("Done")` callback log.
- Added a failure path for non-nil Parse save errors.
- Added a non-completion diagnostic when `succeeded` is false without an error.
- Extended `scripts/check-swift-samples.py --mode samples` to require the
  callback guard.
- Updated README, VISION, and CHANGES.

## Verification

- Negative: `python3 scripts/check-swift-samples.py --mode samples` failed
  before the Swift fix because the Parse callback ignored `err` and logged
  success unconditionally.
- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `make verify`
- `git diff --check`

## Xcode Notes

`xcodebuild` was not available in this environment, so simulator build
verification was not run here. The repository `make check` wrapper still runs
`xcodebuild` when that tool is available locally.
