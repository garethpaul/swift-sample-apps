# Todo Index Guard

## Status: Completed

## Context

The todo-list sample deleted and displayed tasks by indexing directly into
`taskMngr.tasks` from table view callbacks. UIKit normally asks for rows that
match the data source count, but archive samples should still avoid simple
stale-index crashes when table state and local arrays drift during maintenance.

## Objectives

- Guard task lookup before reading from the `tasks` array.
- Guard task deletion before removing from the `tasks` array.
- Keep table cells rendering safely if an index path cannot be resolved.
- Avoid reloading the table after a stale delete request that removed nothing.
- Add static coverage for the todo-list index boundary.

## Work Completed

- Added `taskAtIndex(index:)` to return an optional task for guarded reads.
- Added `removeTaskAtIndex(index:)` to report whether removal happened.
- Updated delete handling to reload only after a guarded removal succeeds.
- Updated cell rendering to optional-bind task lookup and fall back to empty
  labels for stale rows.
- Extended `scripts/check-swift-samples.py` to preserve the todo-list guard.
- Updated README, VISION, and CHANGES.

## Verification

- Negative: `make test` failed before the Swift fix because todo-list table
  callbacks still read and removed unchecked task indexes.
- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `make verify`
- `git diff --check`

`xcodebuild` is not installed in this environment, so `make check` reports that
the Xcode build was not run after static verification passes.

## Follow-Up Candidates

- Add sample-specific notes for legacy table/data-source assumptions.
- Add direct Xcode unit coverage for `TaskManager` on a macOS runner.
