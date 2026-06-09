# Local Xcode Path Guard

## Status: Completed

## Context

The Facebook and Parse archived sample projects still pointed to framework and
bridging-header locations from one developer workstation. Those paths make the
projects less portable and can leak local setup details into the archive.

## Objectives

- Keep the Facebook and Parse samples placeholder-only for service setup.
- Replace developer-local Xcode paths with repo-relative placeholders.
- Extend static checks to scan tracked Xcode project files for local paths.

## Work Completed

- Replaced the Facebook SDK framework reference with a
  `Frameworks/FacebookSDK.framework` project-relative placeholder.
- Replaced the Parse framework reference with a `Frameworks/Parse.framework`
  project-relative placeholder.
- Replaced Facebook and Parse framework search paths with
  `$(SRCROOT)/Frameworks`.
- Replaced the Parse bridging-header setting with `$(SRCROOT)/Swift.h`.
- Extended `scripts/check-swift-samples.py` to scan tracked `.pbxproj` files
  and reject local home-directory or Desktop/Documents framework paths.
- Documented the Xcode path guard in README, VISION, and CHANGES.

## Verification

- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `make verify`
- `git diff --check`

## Xcode Notes

XcodeBuildMCP tools and `xcodebuild` were not available in this environment, so
simulator build verification was not run here. The repository `make check`
wrapper still runs `xcodebuild` when that tool is available locally.
