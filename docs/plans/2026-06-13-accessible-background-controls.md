# Accessible Background Controls

## Status: Planned

## Context

The maintained `background_switcher` canary now covers current device bounds
and preserves the latest rapid selection, but its two controls still use fixed
200-by-20-point frames at hard-coded vertical positions. The 20-point height is
below the expected minimum touch target, does not adapt to preferred text
sizes, and is not positioned through the safe area.

## Priority

The only natively compiled sample should demonstrate safe-area-aware,
accessible controls rather than carrying legacy manual button geometry.

## Requirements

- R1. Arrange both background buttons with Auto Layout inside the view's safe
  area instead of fixed frames and centers.
- R2. Give every button a minimum 44-point height while preserving the existing
  titles, tags, order, target action, and white foreground color.
- R3. Use a preferred text style and enable Dynamic Type scaling for the button
  labels.
- R4. Preserve the responsive full-view background, color lookup, transition
  duration and options, latest-selection behavior, and unknown-tag no-op.
- R5. Preserve the iOS 12 deployment target and do not introduce newer UIKit
  APIs that would break the canary baseline.
- R6. Add static contracts, hostile mutations, documentation, and full
  `make check` verification including the hosted macOS canary build.

## Scope Boundaries

- Do not modernize the five legacy sample targets.
- Do not change colors, button text, storyboard, signing, bundle identifiers,
  or deployment targets.
- Do not add third-party dependencies or claim simulator interaction testing
  without Apple tooling.
- Do not redesign the sample beyond the two existing background controls.

## Implementation Units

### Safe-area control stack

**Files:** `background_switcher/background_switcher/ViewController.swift`

- Replace manual button frames and centers with a vertical `UIStackView`.
- Constrain the stack to the safe area with centered horizontal placement and
  bounded leading, trailing, top, and bottom relationships.
- Apply minimum target height and Dynamic Type-compatible label fonts.

### Regression contract and maintenance record

**Files:** `scripts/check-swift-samples.py`, `README.md`, `SECURITY.md`,
`VISION.md`, `CHANGES.md`,
`docs/plans/2026-06-13-accessible-background-controls.md`

- Reject restored manual button geometry, missing safe-area constraints,
  undersized targets, removed Dynamic Type support, or changed transition
  behavior.
- Record the Linux static boundary and require the hosted macOS canary build.

## Verification Plan

- focused checker and source-contract tests
- `python3 -m py_compile scripts/check-swift-samples.py`
- `make check`
- focused control-layout mutations
- external-working-directory `make check`
- project/workflow parsing, staged-path, generated-artifact, secret-pattern, and
  `git diff --check` audits
- bounded exact-head push and pull-request workflow snapshot after push

## Assumptions

- UIKit safe-area anchors, `UIStackView`, preferred text styles, and
  `adjustsFontForContentSizeCategory` are available at the preserved iOS 12
  deployment floor.
- Static contracts can verify the intended accessibility and layout structure;
  actual VoiceOver, Dynamic Type rendering, rotation, and touch interaction
  still require hosted or local Apple tooling beyond compilation.
