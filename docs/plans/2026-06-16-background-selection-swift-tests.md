# Background Selection Swift Tests

Status: Completed

## Context

The background-switcher canary builds with Swift 5, but its test target remains
template-only and button-tag selection is protected only by static source
contracts.

## Requirements

- Extract button-tag-to-background-key mapping into framework-independent Swift
  used directly by `ViewController`.
- Preserve one-based tags for `Background1` and `Background2` and reject zero,
  negative (including `Int.min`), and out-of-range tags without changing UI
  state or overflowing before validation.
- Execute production mapping cases from canonical `make check` when `swiftc` is
  available, with a truthful skip otherwise.
- Remove temporary compiler output on success, failure, or signal.
- Preserve colors, animation duration/options, Reduce Motion behavior,
  accessibility selection, layout, project settings, and existing sample gates.

## Verification

- Focused Swift executable and cleanup probes.
- Repository and external-directory `make check`.
- Mutation-sensitive wiring, case, runner, Make, project, docs, and plan
  contracts.
- Exact-head Ubuntu contract and macOS Swift/build checks.

## Verification Results

- `python3 -m py_compile scripts/check-swift-samples.py` and
  `sh -n scripts/test-background-selection.sh` passed.
- Fake-compiler success executed the generated binary; compiler failure status
  7 and signal status 143 also removed their temporary output directories.
- The repository and external-directory `make check` passed.
- 15 hostile background selection mutations were rejected across production
  mapping, controller wiring, exact valid and invalid outputs, cleanup, Make,
  Xcode project membership, hosted execution, plan status, and documentation.
- Local `swiftc is unavailable` and `xcodebuild` is unavailable, so executable
  Swift and simulator-build proof remains required from exact-head hosted macOS
  checks before merge.
