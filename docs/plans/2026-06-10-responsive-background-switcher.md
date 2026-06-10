# Responsive Background Switcher

## Status: Completed

## Context

The hosted build canary still created its content with a fixed 320x568 frame.
On larger devices and after rotation, the background image stopped at those
legacy dimensions and left part of the root view uncovered.

## Work Completed

- Derived the content canvas and image frame from the current view bounds.
- Added flexible width and height autoresizing to keep both layers full-size.
- Kept the sample buttons horizontally centered as the available width changes.
- Added static contracts that reject the fixed legacy canvas and require the
  responsive sizing behavior.

## Verification

- `make check`
- Negative source mutation restoring the fixed 320x568 canvas
- `git diff --check`

The hosted macOS CI job performs the real iOS Simulator build because
`xcodebuild` is not available in the Linux development environment.
