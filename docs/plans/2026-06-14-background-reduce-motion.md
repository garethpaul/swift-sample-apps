# Background Reduce Motion

## Status: Completed

## Context

The background switcher always cross-dissolves between colors. That animation
still runs when the system Reduce Motion preference is enabled, even though a
direct color update provides the same result without unnecessary motion.

## Priority

Accessibility behavior in the maintained iOS build canary should respect the
system motion preference without changing selection, validation, or rapid-tap
semantics.

## Requirements

- Preserve guarded color lookup and successful-selection ordering.
- Apply the selected color immediately when Reduce Motion is enabled.
- Retain the interruptible 0.4-second cross-dissolve otherwise.
- Keep exact color, button, selected-trait, Dynamic Type, safe-area, and iOS 12
  behavior unchanged.
- Add fail-closed source contracts, mutation-sensitive checks, and maintained
  documentation.

## Verification

- The focused sample contract passed with the preference branch, direct
  assignment, successful-selection ordering, and unchanged transition intact.
- The repository and external-directory `make check` passed in an isolated
  Git-backed copy; Linux reported the documented static-only boundary because
  `xcodebuild` is unavailable.
- Seven hostile Reduce Motion mutations were rejected: preference guard,
  immediate assignment, branch ordering, transition fallback, documentation,
  README evidence index, and plan-status regressions.
- Hosted macOS 15 background-switcher compilation remains the native build
  authority for the exact pushed head.
- Generated-artifact, credential-pattern, protected-path, and exact-diff audits
  passed before commit.

## Scope Boundary

This change does not alter transition duration for users who have not enabled
Reduce Motion, add runtime dependencies, change project settings, or claim
manual device accessibility validation.
