# Background Selection Semantics

## Status: Completed

## Context

The background switcher now provides safe-area-constrained 44-point Dynamic
Type buttons, but it does not retain or expose which background is selected.
After a color change, VoiceOver users receive no durable selected-state signal.

## Priority

The two controls represent a mutually exclusive choice. Their accessibility
traits should match the visible background, starting with Background 1 and
changing only after the existing guarded color lookup succeeds.

## Objectives

- Retain the created background buttons for selection updates.
- Mark Background 1 selected during initial setup.
- After a successful color lookup, mark only the tapped button selected.
- Keep invalid tags unable to change the background or selection state.
- Preserve titles, order, tags, transition behavior, target sizing, Dynamic
  Type, safe-area constraints, and the iOS 12 deployment floor.

## Implementation Units

### U1. Maintain selected state

**Files:** `background_switcher/background_switcher/ViewController.swift`

Store each button, initialize the first as selected, and centralize selection
updates so `.selected` accessibility traits match `isSelected` after a valid
background choice.

### U2. Preserve the accessibility contract

**Files:** `scripts/check-swift-samples.py`, `README.md`, `VISION.md`,
`SECURITY.md`, `CHANGES.md`

Require retained buttons, initial selection, valid-lookup ordering, exclusive
selection, and the selected accessibility trait. Add focused missing-state,
ordering, trait, exclusivity, documentation, and plan-status mutations.

## Verification

- `python3 scripts/check-swift-samples.py --mode samples` passed locally.
- The first full `make check` reached the plan-completion gate and correctly
  rejected this plan while its status was still Planned.
- Completed-plan `make check` passed locally and from `/tmp`; static checks
  passed and reported that local `xcodebuild` is unavailable.
- Seven focused mutations were rejected: missing retained storage, missing
  append, missing initial state, selection before lookup, nonexclusive state,
  missing selected trait, and regressed plan status.
- Parsed 1 workflow YAML file, 14 plists, and 14 JSON files; Python syntax,
  diff whitespace, generated-artifact, and intended-diff secret audits passed.
- Plan-aware review found no actionable findings. Browser testing is not
  applicable because this is a native UIKit sample without a web route.
- The hosted macOS 15 background-switcher build remains the native compilation
  authority and will be recorded on the exact pushed head.

## Work Completed

- Retained each background button and initialized Background 1 as selected.
- Updated selection only inside the existing successful color-lookup branch.
- Kept `isSelected` and the `.selected` accessibility trait exclusive and in
  sync across both controls.
- Added static contracts and user-facing documentation for the behavior.

## Scope Boundary

This change does not alter colors, animation, layout, button text, touch
targets, the five legacy sample targets, or claim VoiceOver device validation.
