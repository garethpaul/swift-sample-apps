# Changes

## 2026-07-16T05:20:00Z — P1 CI — cycle: iOS simulator destination drift

### Summary

`make native-test` pinned `-destination 'platform=iOS Simulator,name=iPhone 16
Pro,OS=latest'`. GitHub's hosted `macos-15` image rotated its simulators, so
that name no longer resolves and the `build` job fails with "Unable to find a
device matching the provided destination specifier" without any repository
change. Resolve an available iPhone simulator at run time instead.

### Evidence

- `build` on `fix/privacy-safe-service-errors-20260626` passed 2026-06-27 and
  failed 2026-07-16 with the destination error, on a branch whose only new
  commits touch Python contract scripts and documentation.
- `master` last ran green 2026-07-09, so the drift landed after that and will
  break `master` on its next run.
- The adjacent `build` target already used `generic/platform=iOS Simulator` and
  kept passing; only the name-pinned `test` destination broke.

### Work completed

- `scripts/select-ios-simulator.py` — resolve an available iPhone UDID from
  `xcrun simctl list devices available -j`; fail closed when none exists.
- `Makefile` — `native-test` resolves a UDID and passes
  `-destination "id=$$simulator_udid"`; the no-xcodebuild skip path is
  unchanged.
- `scripts/test-select-ios-simulator.py` — drive the selector with recorded
  simctl payloads so the behavior is verifiable on Linux, covering the exact
  drift case (image without iPhone 16 Pro), no-available-device, and iPad-only.
- `scripts/check-swift-samples.py` — the hygiene contract required the Makefile
  to keep the pinned simulator name, so it blocked this fix. Pin the resolver
  and the `id=` destination instead.

### Verification

- `make check` exit 0; selector contract passes 4 cases.
- Mutation: reverting to the pinned name now fails the hygiene contract.
- `make native-test` on Linux still skips truthfully.
- The destination itself can only be exercised on hosted macOS; that job is the
  gate for this change.

## 2026-06-26T20:28:05Z — P1 correctness — cycle: swift objects missing image

### Summary
Prevented the archived UIKit catalog from dereferencing a missing bundled image
when the `UIImageView` row is selected.

### Work completed
- Optional-bound `swift-hero.png` before reading its dimensions or constructing
  the image view; the archive intentionally leaves the detail empty when the
  optional asset is unavailable.
- Added an exact source contract, two hostile mutations, Make wiring,
  synchronized maintenance guidance, and a completed plan.

### Threads
- Started: swift objects optional image ownership.
- Continued: legacy static-only verification boundaries.
- Stopped: none.

### Validation
- RED: the sample contract rejected the unchecked image sizing before the
  source fix.
- GREEN: repository and external-directory `make check` passed 35 Make
  authority cases, four note-editor mutations, five todo-input mutations, and
  both image-guard mutations. `swiftc` and `xcodebuild` skipped truthfully on
  this host.
- Python compilation, shell syntax, and `git diff --check` passed.
- The first full gate rejected a README contract split by Markdown wrapping;
  the contract and prose were made contiguous before both full gates passed.
- Current-tree and added-line secret scans are clean. The history scan surfaced
  two pre-existing generic-key false positives in old commits; neither exists
  in the current tree, and GitHub secret scanning has no open alert.
- Hosted and exact-head review gates remain required before merge.

### Audit
- No open public pull requests or issues remained when this cycle started.
- Dependabot, code-scanning, and secret-scanning reported no open alerts.
- Unmerged remote tips are older rejected bootstrap candidates or stale
  superseded branches; none represents current unfinished product work.

### Blockers
- The swift-objects sample uses historical Swift/UIKit syntax and has no pinned
  compatible build environment, so behavior remains source-contract verified.

### Next action
- Require exact-head Codex review and hosted portable/canary gates before merge.

## 2026-06-26T11:47:00Z — P2 correctness — cycle: todo task input

### Summary
Prevented the archived todo sample from adding invisible blank-name rows or
discarding the add form after a rejected submission.

### Work completed
- Made `TaskManager.addTask` reject empty and whitespace-only names and return
  an acceptance result without rewriting valid task text.
- Gated keyboard dismissal, field clearing, and tab navigation on successful
  insertion.
- Added exact sample contracts, five hostile mutations, Make wiring,
  synchronized documentation, and a completed plan.

### Threads
- Started: todo task-input ownership.
- Continued: legacy static-only verification boundaries.
- Stopped: none.

### Validation
- RED: sample checks rejected the missing manager acceptance and guarded UI
  flow before implementation.
- GREEN: repository and external-directory `make check` pass hygiene and sample
  contracts, four note-editor mutations, five todo-input mutations, and 35 Make
  authority cases. Python compilation, shell syntax, and `git diff --check`
  also pass.
- Hosted checks remain exact-head merge gates; this host has no `swiftc` or
  `xcodebuild`, so native background canary tests/build skip truthfully.

### Blockers
- The todo sample uses historical Swift/UIKit syntax and has no pinned
  compatible build environment, so behavior remains source-contract verified.

### Next action
- Require exact-head Codex review and hosted portable/canary gates before merge.

## 2026-06-25T21:42:44Z — P1 correctness — cycle: note editor ownership

### Summary
Removed the basic note sample's list/editor retain cycle and indefinite
last-editor retention without changing note editing behavior.

### Work completed
- Made the editor delegate protocol class-bound and its delegate reference weak.
- Replaced the list controller's stored editor with a selection-local editor.
- Published the selected note index before delegation and navigation.
- Added exact static contracts and four hostile ownership mutations.

### Threads
- Started: basic note editor lifetime ownership.
- Continued: stale-index guards and archive/static-only verification boundaries.
- Stopped: none.

### Files changed
- Basic note list/editor controllers, Make and checker wiring, mutation runner,
  documentation, and `docs/plans/2026-06-25-note-editor-ownership.md`.

### Validation
- RED: sample checks rejected strong delegation and stored-editor ownership.
- GREEN: `/usr/bin/make check` passes hygiene, samples, four ownership
  mutations, and 35 Make authority cases.
- `swiftc` and Xcode skip truthfully on this host; the historical note sample
  remains static-only because its original toolchain is not pinned.
- Codex review found the mutation runner bypassed the configured `PYTHON`
  interpreter; it now reuses `sys.executable`, with a static regression guard.

### Bugs / findings
- P1: the editor strongly retained its list delegate while the list stored the
  editor, forming a cycle during editing.
- P2: the root list retained the last pushed editor indefinitely even after pop.
- P2 review: the first mutation runner hard-coded `python3`, weakening the
  Makefile's documented trusted-interpreter override.

### Blockers
- The basic note sample uses historical Swift/UIKit syntax and has no pinned
  compatible build environment; behavioral claims remain source-level only.

### Next action
- Require exact-head Codex review and hosted portable/canary/CodeQL checks.

## 2026-06-25 11:46 PDT - P2 - Index sample purpose and service boundaries

### Summary

Added the roadmap-promised README table for every checked-in sample, including
its purpose, required external services or SDKs, and current verification
boundary. The index separates the maintained background-switcher canary from
legacy static-only examples.

### Work completed

- Added one row for each of the six sample directories.
- Marked Facebook and Parse dependencies as legacy, developer-local, and
  credential-free in source control.
- Added static contracts for table completeness, service wording, completed
  plan evidence, and roadmap synchronization.

### Threads

- Started: none; this focused documentation gap was completed directly.
- Continued: none.
- Stopped: none.

### Files changed

- `README.md` — added the sample purpose, service, and verification table.
- `SECURITY.md` — tied service configuration back to credential hygiene.
- `VISION.md` — removed the completed sample-index priority.
- `scripts/check-swift-samples.py` — enforced all rows and service boundaries.
- `docs/plans/2026-06-25-sample-service-index.md` — recorded scope and evidence.

### Validation

- Red-first hygiene check — rejected the missing plan, heading, six sample
  rows, and Facebook/Parse service descriptions as expected.
- Initial synchronized documentation patch — partially applied the README then
  stopped on a mismatched generated security sentence; remaining files were
  applied with the repository's exact wording.
- Diff review — found the first contract proved row names but not purpose
  cells; tightened it to exact six-row semantics and rejected a mutated note
  purpose for the intended missing-row error.
- `python3 -m py_compile scripts/check-swift-samples.py` — passed.
- Root and external-directory `/usr/bin/make check` — both passed 35 Make
  authority cases plus hygiene and sample contracts; `swiftc` and `xcodebuild`
  skipped truthfully because they are unavailable on this Linux host.
- `git diff --check` — passed.
- Initial suspicious-addition scan used unsupported ripgrep lookahead syntax;
  the corrected PCRE2 scan passed without credential-like additions.
- Xcode/native runtime — available only through the documented macOS hosted
  jobs; local Linux validation remains portable/static.

### Bugs / findings

- P2: readers had no single source explaining each sample's purpose, service
  dependency, or whether it was actively build-tested versus static-only.

### Blockers

- Legacy Facebook and Parse SDKs are intentionally absent; those projects
  cannot be runtime-validated without historical dependencies and local setup.

### Next action

- Open the focused pull request, run exact-head Codex review, and confirm the
  hosted portable, Swift, native XCTest, and Xcode build jobs before merge.

## 2026-06-21

- Isolated verification from caller-selected roots, shells, bypassing Make
  modes, preload metadata, and additional Makefiles while preserving trusted
  Python, Swift, and Xcode tool overrides.

## 2026-06-19

- Replaced the legacy placeholder XCTest target with native tests for stable
  selection mapping, rapid taps, selected accessibility state, control labels
  and traits, and runtime Reduce Motion changes.
- Added `make native-test` to local and hosted macOS verification. The native
  target now builds with testability enabled on current Xcode.
- Runtime Reduce Motion changes now cancel an active transition and settle the
  image on the latest selected background instead of leaving motion in flight.
- Background keys, titles, tags, and colors now derive from one deterministic
  selection model rather than parallel index-based collections.
- Portable verification now rejects background-selection test runners that
  compile the behavioral harness without executing the resulting binary.

## 2026-06-16

- Background selection behavior now executes production button-tag mapping for
  valid and invalid inputs in the canonical verification path.

## 2026-06-14

- Added Reduce Motion background changes that apply successful color choices
  immediately while preserving the existing transition for other users.

## 2026-06-13

- Added exclusive background selection semantics and the selected accessibility
  trait after successful color lookup.
- Replaced fixed 20-point background button frames with a safe-area-aware
  vertical stack, 44-point minimum targets, padding, and Dynamic Type labels.

## 2026-06-12

- Replaced queued background fade completions with one interruptible
  cross-dissolve so rapid taps preserve the latest selected color.
- Fixed portable CI to Ubuntu 24.04, disabled persisted checkout credentials,
  added concurrency cancellation/manual dispatch, and made Make targets
  independent of the caller's working directory.

## 2026-06-10

- Replaced the background switcher's fixed 320x568 canvas with a flexible
  view-bounds layout that covers current devices and rotations.
- Added a fixed macOS 15 CI job that compiles the self-contained background
  switcher sample for a generic iOS Simulator.
- Migrated background switcher to Swift 5 and iOS 12 while keeping Parse and
  Facebook samples static-only because their legacy frameworks are absent.
- Fixed portable CI to Ubuntu 24.04 and made Make targets root-independent.
- Aligned the background-switcher product bundle identifier with its Info.plist
  to remove conflicting Xcode metadata.
- Rejected malformed Facebook profile payloads without forced-cast crashes.
- Stopped user-cancelled Facebook login from displaying an empty alert.
- Added a least-privilege Python 3.12 GitHub Actions verification gate.

## 2026-06-09

- Guarded the swift-objects sample against stale table indexes before reading
  item titles or opening detail views.
- Guarded the todo-list sample against stale table indexes before reading or
  removing tasks.
- Guarded the basic note sample against stale table indexes before reading or
  updating the notes array.
- Updated the Parse sample save callback to handle `NSError` and unsuccessful
  saves before reporting completion.
- Replaced developer-local Facebook and Parse Xcode framework paths with
  repo-relative placeholders and added static guard coverage.
- Fixed the Facebook login error handler to use the delegate-supplied
  `NSError` instead of shadowing it with `nil`.
- Extended Swift sample checks to reject Facebook login error shadowing and
  forced `NSError` unwraps.
- Removed background-switcher loop-index debug logging from view setup.
- Extended Swift sample checks to reject active `print`/`println` debug logging
  in tracked Swift sources.

## 2026-06-08

- Replaced remote HTTP UIWebView requests with local sample HTML and added
  checker coverage for insecure Swift URL literals.
- Ignored Python bytecode caches produced by local checker syntax validation.
- Removed synchronous remote image downloads from the background switcher and
  Parse examples, with static checker coverage.
- Added `make check` as the shared repository verification alias.
- Removed hardcoded credential-like Parse values and tokenized sample image
  URLs from the Facebook, Parse, and background switcher samples.
- Extended the sample checker to scan tracked text files for known
  credential-like markers and tokenized URLs.
- Added a Makefile verification gate for sample inventory and repository
  hygiene checks.
- Removed tracked Xcode per-user state files from sample projects.
- Added ignore rules for Xcode user state and DerivedData.
- Documented the local static verification workflow.
- Added canonical `docs/plans` coverage and made hygiene checks require
  completed plans.
