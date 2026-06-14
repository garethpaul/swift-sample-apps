# Background Reduce Motion

## Status: Planned

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

- focused sample contract and full `make check`
- repository and external-directory Make invocation
- hostile preference, immediate-assignment, branch-ordering, transition,
  documentation, suite-contract, and plan-status mutations
- hosted macOS 15 background-switcher compilation on the exact pushed head
- generated-artifact, credential-pattern, protected-path, and exact-diff audits

## Scope Boundary

This change does not alter transition duration for users who have not enabled
Reduce Motion, add runtime dependencies, change project settings, or claim
manual device accessibility validation.
