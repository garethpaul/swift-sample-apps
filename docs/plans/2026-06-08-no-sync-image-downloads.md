# No Sync Image Downloads

## Status: Completed

## Context

The background switcher and Parse examples still performed synchronous
`NSData(contentsOfURL:)` image downloads during view setup or button handling.
These archive samples should not block the main thread or reach out to remote
image hosts just to demonstrate UI behavior.

## Objectives

- Preserve the background-switching and Parse sample UI shape.
- Remove launch-time and button-time remote image downloads.
- Use local placeholder colors instead of remote sample images.
- Extend static sample checks to reject synchronous URL-backed image loading.

## Work Completed

- Replaced `background_switcher` remote image URLs with local color choices.
- Replaced the Parse example's remote placeholder image fetch with a local
  gray placeholder.
- Added a checker rule for `NSData(contentsOfURL:)` in Swift files.
- Updated README, VISION, and CHANGES.

## Verification

- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Replace remaining legacy `UIWebView` HTTP examples with local HTML or HTTPS
  placeholder pages.
- Add per-sample README notes for which examples require external SDK setup.
