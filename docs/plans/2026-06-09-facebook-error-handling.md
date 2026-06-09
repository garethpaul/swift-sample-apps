# Facebook Error Handling Guard

## Status: Completed

## Context

The Facebook login sample's error delegate accepted an `NSError`, then shadowed
it with a new optional `nil` variable before branching through the Facebook SDK
error utility. The fallback path also force-unwrapped that shadowed value for
logging, which could crash exactly when the sample was trying to report a login
failure.

## Objectives

- Preserve the delegate-supplied Facebook SDK error object.
- Remove the forced unwrap from the generic error logging path.
- Extend static sample checks so this regression is caught without requiring
  Xcode on the verification machine.

## Work Completed

- Removed the local `NSError?` shadow from the Facebook login error handler.
- Changed fallback logging to pass the delegate error directly.
- Added checker rules that reject the shadowed error pattern and forced
  `NSError` unwraps in the Facebook login controller.
- Updated README, VISION, and CHANGES with the new guardrail.

## Verification

- `python3 scripts/check-swift-samples.py --mode samples`
- `make lint`
- `make test`
- `make build`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Add per-sample README notes for the Facebook SDK version expected by the
  archived project.
- Replace older `UIAlertView` usage when the archive moves to a newer Swift and
  iOS deployment target.
