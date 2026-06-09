# Basic Note Index Guard

## Status: Completed

## Context

The basic-note-taker sample indexed directly into its `notes` array from table
view callbacks and wrote editor updates back to `selectedNote` without checking
that the index was still valid. UIKit normally supplies valid index paths, but
archive samples should avoid simple stale-index crashes when table state and
local arrays drift during maintenance.

## Objectives

- Guard note lookups before reading from the `notes` array.
- Skip editor presentation when a table index path is stale.
- Keep table cells rendering safely if an index path cannot be resolved.
- Guard selected-note writes before updating the local notes array.
- Add static coverage for the basic note index boundary.

## Work Completed

- Changed `note(indexPath:)` to return an optional and validate the row.
- Optional-bound note selection before opening the editor.
- Made cell rendering fall back to an empty string for stale index paths.
- Guarded `selectedNote` before writing editor changes back to `notes`.
- Extended `scripts/check-swift-samples.py` to preserve the index guard.
- Updated README, VISION, and CHANGES.

## Verification

- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `git diff --check`

`xcodebuild` is not installed in this environment, so `make check` reports that
the Xcode build was not run after static verification passes.

## Follow-Up Candidates

- Add a README table with each sample, purpose, and required services.
- Add sample-specific notes for legacy table/data-source assumptions.
