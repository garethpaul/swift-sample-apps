# Todo Task Input Guard

Status: Completed

## Problem

The archived todo sample appended every submitted name, including empty and
whitespace-only values. That produced invisible table rows, then cleared the
form and navigated away even though no meaningful task had been entered.

## Decision

- Validate task names in `TaskManager`, the owner of the task collection.
- Reject empty and whitespace-only names without rewriting accepted text.
- Return whether insertion succeeded.
- End editing, clear fields, and switch tabs only after accepted insertion.
- Preserve the historical Swift/UIKit style and static-only verification
  boundary instead of broad modernization.

## Verification

- The sample contract failed before the manager returned acceptance or trimmed
  name input.
- Five hostile mutations cover missing acceptance, weakened whitespace checks,
  success ordering, blank acceptance, and an unguarded UI transition.
- Repository and external-directory `make check` run the focused mutation suite.
- Native behavior remains unclaimed because this historical sample has no
  pinned compatible Swift/Xcode toolchain.
