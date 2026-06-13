# Background Selection Semantics

## Status: Planned

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

- Focused source contract and full `make check` locally and from outside the
  repository root.
- Hosted macOS 15 background_switcher canary build through the pull-request
  event.
- Focused hostile mutations plus workflow YAML, plist, asset JSON, Python
  checker, secret, artifact, and `git diff --check` audits.

## Scope Boundary

This change does not alter colors, animation, layout, button text, touch
targets, the five legacy sample targets, or claim VoiceOver device validation.
