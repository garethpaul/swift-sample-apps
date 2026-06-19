# Latest Background Selection

## Status: Completed

## Context

`background_switcher` changes color through a fade-out completion handler and a
second fade-in. Rapid taps create overlapping completion handlers, allowing an
older tap to assign its color after a newer selection and leaving the displayed
background inconsistent with the latest user action.

## Priority

The most recent button selection must update the background immediately in one
interruptible transition, without a delayed stale completion write.

## Requirements

- R1. Replace the two-stage alpha animation with one UIKit transition whose
  animation block assigns the selected color.
- R2. Use current-state animation behavior so rapid taps transition from the
  current presentation rather than queueing stale completion work.
- R3. Keep interaction enabled during the transition.
- R4. Preserve color lookup, button tags, duration, responsive layout, and the
  no-op behavior for unknown tags.
- R5. Add static contracts, hostile mutations, documentation, and full
  `make check` verification including the hosted canary build.

## Scope Boundaries

- Do not modernize the five legacy sample targets in this change.
- Do not change colors, button text, storyboard, deployment target, signing, or
  public sample structure.
- Do not claim simulator interaction testing without Apple tooling.

## Implementation Units

### Interruptible latest-selection transition

**Files:** `background_switcher/background_switcher/ViewController.swift`

- Use a single cross-dissolve transition with current-state and interaction
  options, assigning the selected color synchronously in the animation block.

### Regression contract and maintenance record

**Files:** `scripts/check-swift-samples.py`, `README.md`, `SECURITY.md`,
`VISION.md`, `CHANGES.md`, `docs/plans/2026-06-12-latest-background-selection.md`

- Reject delayed completion writes, missing transition options, or drift in the
  existing duration and guarded color lookup.

## Verification Plan

- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- focused transition mutations
- external-directory `make check`
- `git diff --check`
- exact-head hosted macOS 15 canary build before merge

## Work Completed

- Replaced the two-stage alpha animation with one cross-dissolve transition.
- Assigned the selected color in the animation block with no delayed completion
  mutation.
- Enabled current-state and user-interaction options so rapid taps remain
  interruptible and the latest selection wins.
- Preserved guarded color lookup, button tags, duration, and responsive layout.
- Extended source contracts and maintenance documentation.

## Verification

- `python3 scripts/check-swift-samples.py --mode samples` passed.
- Four focused hostile transition mutations were rejected.
- `make check` passed hygiene and sample contracts; local `xcodebuild` was
  unavailable on Linux and the Makefile ran its documented static-only path.
- The same full gate passed from an external working directory.
- Python checker compilation and `git diff --check` passed.
- Plan-aware correctness, Swift lifecycle/race, maintainability, testing, and
  project-standards review found no actionable issues.

## Remaining Risks

- Static contracts and compilation do not simulate rapid touch interaction or
  visually inspect the transition.
