# Background Test Execution Contract

Status: Completed

## Context

The default branch accepted zero-assertion and false-green mutations because a
static checker verified source text while the runner trusted caller-controlled
compiler resolution and a Swift executable owned both expectations and verdicts.

## Requirements

- Keep mapping expectations and verdicts outside production and the Swift adapter.
- Execute randomized and permuted observations in isolated fresh processes.
- Exercise variable-length boundary and high-iteration sequences well beyond
  the original sixteen-call process shape.
- Resolve the canonical Swift compiler independently of caller `PATH` and `SWIFTC`.
- Resolve Python and Xcode tools independently of caller Make overrides.
- Reject production access to process, environment, filesystem, clock, or output APIs.
- Require malformed-input and known-broken-production negative controls.
- Preserve native XCTest, Xcode build, and simulator validation.

## Work Completed

- Replaced assertion-owning Swift code with a raw black-box observation adapter.
- Added an external Python harness that owns expectations, randomizes sequence
  order, compiles opaque real and broken sources, and executes each sequence in
  a fresh process.
- Anchored Apple compiler discovery to `/usr/bin/xcode-select` and
  `/usr/bin/xcrun`; Linux uses reviewed absolute Swift toolchain locations.
- Added production and adapter boundary checks plus adversarial mutation tests.
- Made the Make test target double-colon based so an appended single-colon
  recipe fails instead of silently overriding verification.
- Added seventeenth-call, repeated-valid, and long randomized fresh-process
  shapes, including sequences above one thousand and two thousand calls.
- Made Make use reviewed absolute Python and Xcode tool resolution; caller
  `PYTHON=/usr/bin/true` and `XCODEBUILD=/usr/bin/true` cannot forge success.

## Verification

- Exact default reproduced all known zero-assertion and false-green families,
  including test-aware production and caller-controlled `PATH` compiler forgery.
- Repository and external-directory `make check` passed.
- Python, Swift, native XCTest, Xcode builds, simulator installation, and launch passed.
- Hostile runner, harness, adapter, production, Make, and compiler mutations were rejected.
- Current-tree and full-history credential scans completed; provider-side status remains external.
