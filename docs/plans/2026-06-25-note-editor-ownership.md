# Note Editor Ownership

Status: Completed

## Problem

The note list stores the current editor, and the editor stores its delegate
strongly. That keeps the last editor alive for the lifetime of the root list and
forms a list/editor retain cycle while delegation is active.

## Design

Make the delegate protocol class-bound and the delegate reference weak. Create
the editor as a local selection-flow value, assign the selected index before
navigation, then push without storing the editor on the list controller.

## Verification Completed

- RED: the static sample checker rejects strong delegate and stored-editor
  ownership.
- Selected-index publication is required before delegate assignment and
  navigation.
- Four hostile mutations are rejected: removing the class bound, restoring a
  strong delegate, restoring stored-editor ownership, and reordering selection.
- Codex review found the runner hard-coded `python3`; it now reuses
  `sys.executable`, and hygiene checks reject interpreter drift.
- `/usr/bin/make check` passes hygiene, samples, mutation, and 35 Make authority
  cases; `swiftc` and Xcode are unavailable locally and skip truthfully.
- `git diff --check` passes.
