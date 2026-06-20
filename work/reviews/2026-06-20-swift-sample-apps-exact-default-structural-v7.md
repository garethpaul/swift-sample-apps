# Swift Sample Apps Exact-Default Structural Repair v7

## Scope

- Base: `e0b72f53b6ef73989b8dcd12473c8476c92baf02`.
- Local branch: `repair/exact-default-structural-v7`.
- No push or GitHub mutation was performed.
- Rejected repair commits through `8e082f230ca94ba9210d32a962bbe6c5eff6c5fb` must not be ancestors of the final commit.

## Repair

- Preserved v6 absolute-tool defenses:
  - Make uses `/bin/sh` and a trusted absolute-path tool resolver.
  - Python, Swift compiler, and Xcode build tools are resolved from reviewed absolute paths.
  - The Swift runner no longer trusts `/usr/bin/env sh` or PATH-front tool lookups.
- Preserved v6 semantic PBX defenses:
  - PBX data is parsed instead of trusting comments.
  - The background app/test source closure must resolve to the exact reviewed Swift source set.
  - Duplicate build refs, duplicate file refs, duplicate paths, path escapes, generated Swift paths, and Swift source/build-setting injection are rejected.
- Preserved v6 pure background selection mapping:
  - Removed `RawRepresentable`/`rawValue` and `CaseIterable`/`allCases` routing.
  - Added explicit `supportedCases()`, `buttonTag`, `key`, `title`, and switch-only `selection(forButtonTag:)`.
- Added v7 semantic Swift declaration/modifier scanning for app-compiled sources:
  - Tokenizes Swift after stripping comments/strings, tracks brace depth, and fails closed on unsupported syntax such as unbalanced braces or unterminated escaped identifiers.
  - Detects declarations regardless of access control, attributes, modifier order, multiline layout, semicolon packing, escaped identifiers, and Unicode whitespace.
  - Rejects unapproved top-level helper state/functions, unapproved member state/functions/types, local mutable state, static/class/lazy/attributed member state, and helper assignments that rewrite button tags before canonical selection mapping.

## TDD Evidence

- Initial RED on exact base:
  - `/usr/bin/python3 Tests/test_background_selection_execution_contract.py -v`
  - 15 failures: base accepted prior hostile PBX/tooling mutations plus the v7 `internal var hiddenFlip` / `internal func` `> 1_000_000` tag-rewrite bypass.
- Intermediate RED after porting v6 repair content:
  - `/usr/bin/python3 Tests/test_background_selection_execution_contract.py -v`
  - 1 failure: v6 accepted the exact `internal var hiddenFlip` + `internal func hiddenSelectionTag` bypass in compiled `ViewController.swift`.
- Final GREEN:
  - `/usr/bin/python3 Tests/test_background_selection_execution_contract.py -v`
  - 15 tests passed.

## Verification

- `/usr/bin/python3 -m py_compile scripts/check-swift-samples.py Tests/test_background_selection_execution_contract.py`: passed.
- `make lint`: passed.
- `make lint test contract-test`: passed from repository root.
- `make -f /Users/gpj/Documents/Codex/2026-06-18/goal-go-through-and-maintain-my/work/repairs/swift-sample-apps/repo/Makefile lint test contract-test` from `/tmp`: passed.
- Python matrix passed compile, contract, hygiene, and samples:
  - Python 3.9.6 (`/usr/bin/python3`);
  - Python 3.14.5 (`/opt/homebrew/bin/python3.14`);
  - Python 3.11.15 (`/opt/homebrew/bin/python3.11`);
  - Python 3.12.8 (`/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12`).
- `actionlint`: passed.
- `shellcheck scripts/resolve-trusted-tools.sh scripts/test-background-selection.sh`: passed.
- `git diff --check`: passed.
- `make build`: passed for the `background_switcher` iOS Simulator target.
- `gitleaks detect --source . --no-git --redact --no-banner`: passed.

## Limitations

- Native XCTest execution was attempted through `make check`, direct `xcodebuild test` by device ID, and a retry after rebooting the target iPhone 16 Pro simulator. All attempts built successfully but then blocked in Xcode/CoreSimulator before test execution with `waiting for workers to materialize`; direct runs ended as interrupted with result bundles under `~/Library/Developer/Xcode/DerivedData/background_switcher-*/Logs/Test/`.
- Direct `simctl install`/`launch` was also attempted after `make build`; CoreSimulator first reported the target device as shutdown, then hung in `simctl bootstatus` after reboot was requested.
- Full-history `gitleaks detect --source . --redact --no-banner` still reports two pre-existing historical redacted `generic-api-key` findings:
  - `139d58548f7580ab7fc64cb3c7c56dc08cd53bbc` at `parse_example/parse_example/ViewController.swift:18`;
  - `b99b2f5e648a6ef771c723b4c73da58bf250a7aa` at `background_switcher/background_switcher/ViewController.swift:29`.
- Current-tree Gitleaks is clean.
