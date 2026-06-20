# Swift Sample Apps Exact-Default Structural Repair v6

## Scope

- Base: `e0b72f53b6ef73989b8dcd12473c8476c92baf02`.
- Local branch: `repair/exact-default-structural-v6`.
- No push or GitHub mutation was performed.
- Rejected repair commits through `d3699856d110195719e347090592873a31649383` are reference material only and must not be ancestors of the final commit.

## Repair

- Refactored `BackgroundSelection` into an explicit pure mapping:
  - no `RawRepresentable`/`rawValue` routing;
  - no `CaseIterable`/overridable `allCases`;
  - no stored static case list;
  - explicit `supportedCases()`, `buttonTag`, `key`, `title`, and `selection(forButtonTag:)` switches.
- Preserved the UIKit app path by updating `ViewController` and native XCTest expectations to call the explicit pure mapping.
- Preserved v5 absolute-tool defenses:
  - Make uses `/bin/sh` and a trusted tool resolver;
  - Python, Swift compiler, and Xcode build tools are resolved from reviewed absolute paths;
  - the Swift executable runner no longer trusts `/usr/bin/env sh` or PATH-front tool lookups.
- Preserved and extended semantic PBX defenses:
  - the checker parses PBX data instead of trusting comments;
  - app/test source phases must resolve to the exact expected Swift source closure;
  - duplicate build-file refs, duplicate file refs, duplicate resolved paths, path escapes, generated Swift paths, and Swift source/build-setting injection are rejected.
- Added full compiled app-source state/test-awareness scanning over `BackgroundSelection.swift`, `ViewController.swift`, and `AppDelegate.swift`:
  - rejects escaped identifiers, conditional compilation, ProcessInfo/env/argv/test-awareness tokens, global/top-level helper state, nested/helper class/actor/struct state, static/class/lazy/property-wrapper state, closure-captured state except the existing approved weak-self UI observer, self-assignment, and counter/probe/mutation-style state tokens;
  - rejects `BackgroundSelection` redefinitions/extensions outside the audited pure mapping source;
  - exact-matches the audited pure `BackgroundSelection.swift` source to establish no alternate route into stateful helpers elsewhere.

## TDD Evidence

- Initial RED on exact base:
  - `/usr/bin/python3 Tests/test_background_selection_execution_contract.py -v`
  - failed because base accepted:
    - AppDelegate global `> 1_000_000` helper route from the mapper;
    - escaped ``static var `x` `` mapper state.
- RED after porting v5 defenses:
  - `/usr/bin/python3 Tests/test_background_selection_execution_contract.py -v`
  - v5 mutations passed, but four v6 mutations failed:
    - AppDelegate global helper routing;
    - escaped static var state;
    - conditional compilation + argv + self-assignment in AppDelegate;
    - class/actor/lazy/property-wrapper state in ViewController.
- Final GREEN:
  - `/usr/bin/python3 Tests/test_background_selection_execution_contract.py -v`
  - 12 tests passed.

## Verification

- `make lint`: passed.
- `make test`: passed; includes sample checks and executable Swift mapping proof.
- `make contract-test`: passed; 12 mutation tests.
- `make native-test`: passed on Xcode 26.0.1 / iPhone 16 Pro iOS Simulator; 4 XCTest cases, 0 failures.
- `make build`: passed for `background_switcher` iOS Simulator target.
- `make check`: passed from repository root.
- `make -f /Users/gpj/Documents/Codex/2026-06-18/goal-go-through-and-maintain-my/work/repairs/swift-sample-apps/repo/Makefile check` from `/tmp`: passed.
- Python matrix passed for available trusted interpreters:
  - Python 3.9.6;
  - Python 3.14.5;
  - Python 3.11.15;
  - Python 3.12.8.
- `actionlint`: passed.
- `shellcheck scripts/resolve-trusted-tools.sh scripts/test-background-selection.sh`: passed.
- `gitleaks detect --source . --no-git --redact --no-banner`: passed.
- `git diff --check`: passed.

## Limitations

- Full-history `gitleaks detect --source . --redact --no-banner` still reports two redacted historical `generic-api-key` findings in old commits:
  - `139d58548f7580ab7fc64cb3c7c56dc08cd53bbc` at `parse_example/parse_example/ViewController.swift:18`;
  - `b99b2f5e648a6ef771c723b4c73da58bf250a7aa` at `background_switcher/background_switcher/ViewController.swift:29`.
- Current-tree Gitleaks is clean.
- Native Xcode commands emit existing project warnings about deprecated launch images, future UIScene lifecycle requirements, and the test bundle identifier setting; they do not fail the build or tests.
