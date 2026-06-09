# Swift Objects Index Guard

## Status: Completed

## Context

The swift-objects sample displayed table rows and opened detail views by
force-unwrapping the `items` array and indexing it directly from table view
callbacks. UIKit normally asks for valid rows, but archive samples should avoid
simple stale-index crashes when table state and local arrays drift during
maintenance.

## Objectives

- Guard item lookup before reading from the `items` array.
- Keep row counts safe when the optional item list is unavailable.
- Keep table cells rendering safely if an index path cannot be resolved.
- Avoid opening a detail view for stale selection indexes.
- Add static coverage for the swift-objects index boundary.

## Work Completed

- Added `item(indexPath:)` to return an optional title for guarded reads.
- Updated row counts to tolerate missing item arrays.
- Updated cell rendering to optional-bind item lookup and fall back to an empty
  label for stale rows.
- Updated selection handling to optional-bind item lookup before opening the
  detail view.
- Extended `scripts/check-swift-samples.py` to preserve the swift-objects guard.
- Updated README, VISION, and CHANGES.

## Verification

- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make lint`
- `make check`
- `make verify`
- `git diff --check`

`xcodebuild` is not installed in this environment, so `make check` reports that
the Xcode build was not run after static verification passes.
