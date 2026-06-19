# Background Test Execution Contract

Status: Completed

## Context

The background-selection runner contract required the compiled binary path to
appear in `scripts/test-background-selection.sh`, but that path appears in both
the compiler output argument and the standalone execution command. Replacing
the execution command therefore passed `make check` on hosts without `swiftc`
because the compiler output still satisfied the broad substring check.

## Requirements

- Preserve the production selection mapping and executable Swift cases.
- Require the compiler output to target the expected selection test binary.
- Require exactly one standalone command that executes the compiled binary.
- Keep the portable contract effective when `swiftc` is unavailable.
- Preserve temporary-directory cleanup and hosted iOS Simulator validation.

## Work Completed

- Added a distinct contract for the Swift compiler output argument.
- Added a line-oriented contract requiring exactly one standalone execution of
  the compiled selection test binary.
- Indexed the maintenance evidence in README and CHANGES.

## Verification

- The missing-execution mutation passed `make check` before the contract fix.
- Missing, duplicated, and mismatched-output mutations are rejected after the
  fix on a host without `swiftc`.
- Repository and external-directory `make check` passed.
- Digest-pinned Swift executable tests passed from repository and external
  working directories.
- Exact-head hosted `build` and `contract` checks remain required after push.
