# Sample Service Index

## Status: Completed

## Priority

1. Give readers one complete index of every checked-in sample.
2. State each sample's purpose and external service or SDK requirements.
3. Distinguish the maintained build canary from legacy static-only projects.
4. Keep credential and production-readiness boundaries explicit.

## Context

The README listed repository directories but did not explain what each sample
demonstrates, which legacy services it needs, or which projects are exercised
by current Xcode. This was the first outstanding item in `VISION.md`.

## Requirements

- R1. Add one README table row for every canonical sample directory.
- R2. Describe purpose, required services or SDKs, and verification status.
- R3. Identify Facebook and Parse configuration as developer-local and
  credential-free in source control.
- R4. State that only `background_switcher` is a current build/native-test
  canary and avoid current-build claims for the legacy samples.
- R5. Add static contracts and synchronize security, roadmap, and change notes.

## Implementation Units

### U1. Add the canonical sample table

**Files:** `README.md`

Describe all six projects with concise purpose, dependency, and validation
columns plus a clear legacy boundary.

### U2. Enforce table completeness

**Files:** `scripts/check-swift-samples.py`

Require the table heading, every canonical sample row, both legacy service
names, local-configuration wording, build boundary, and completed plan evidence.

### U3. Synchronize maintenance guidance

**Files:** `SECURITY.md`, `VISION.md`, `CHANGES.md`,
`docs/plans/2026-06-25-sample-service-index.md`

Connect service requirements to credential hygiene and remove the completed
roadmap item.

## Verification Plan

- Prove the hygiene checker fails before the table and plan exist.
- Run hygiene and sample source checks directly.
- Run `make check` from the repository and an external directory.
- Inspect the exact diff and hosted portable/native/build checks.

## Scope Boundaries

- Do not add, download, or claim compatibility with legacy Facebook/Parse SDKs.
- Do not change sample source, Xcode projects, or runtime behavior.
- Do not claim current builds for static-only archive projects.
- Do not commit service credentials or real user data.

## Work Completed

- Added a six-row purpose, service, and verification index.
- Added static completeness and service-boundary contracts.
- Synchronized security, roadmap, and maintenance guidance.

## Verification

- The red-first hygiene check rejected the missing plan, heading, six rows, and
  legacy Facebook/Parse service descriptions on 2026-06-25.
- A focused mutation changing the basic-note purpose was rejected by the exact
  row contract on 2026-06-25.
- `python3 -m py_compile scripts/check-swift-samples.py` passed on 2026-06-25.
- Root and external-directory `/usr/bin/make check` both passed 35 Make
  authority cases plus hygiene and sample contracts on 2026-06-25; `swiftc`
  and `xcodebuild` skipped truthfully because they are unavailable locally.
- `git diff --check` passed.
- No legacy service SDK, credential, simulator, or live account was used.
