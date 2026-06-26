# Swift Objects Missing Image Guard

Status: Completed

## Problem

The archived UIKit catalog offers an `UIImageView` row that loads
`swift-hero.png`, then immediately reads the image dimensions. The project does
not contain that asset, so selecting the row can dereference a missing image
and crash instead of presenting the detail screen safely.

## Decision

- Keep the historical title-based detail dispatch and legacy Swift syntax.
- Optional-bind the bundled image before reading its dimensions.
- Leave the detail screen empty when the optional archive asset is absent.
- Add a source contract and hostile mutations for the guarded load and sizing
  boundary.
- Keep runtime claims static-only because this sample has no pinned compatible
  Swift/Xcode toolchain.

## Verification

- The new sample contract failed against the unchecked image load before the
  source fix.
- Two hostile mutations reject removal of optional binding or the bound image
  assignment.
- Repository and external-directory `make check` passed 35 Make authority
  cases, four note-editor mutations, five todo-input mutations, and both image
  mutations.
- Python compilation, shell syntax, and `git diff --check` passed.
- The current-tree and added-line secret scans are clean. The history scan
  surfaced two pre-existing generic-key false positives in older commits that
  do not exist in the current tree.
- Native behavior remains unclaimed because this historical sample has no
  pinned compatible Swift/Xcode toolchain.
