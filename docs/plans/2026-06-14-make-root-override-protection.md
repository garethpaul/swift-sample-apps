# Make Root Override Protection

## Status: Completed

## Context

The Makefile derives repository and canary paths from its own location, but a
caller can replace `ROOT` through the environment or command line. That can
redirect static checks and the native canary build away from the checked-out
sample archive.

## Priority

Verification paths are a trust boundary. The repository must select its own
root while preserving intentional Python and Xcode tool overrides.

## Objectives

- Protect the repository-derived root from caller assignments.
- Preserve tool declaration order, all public aliases, and the canary path.
- Verify every alias from repository and external working directories under
  hostile environment and command-line root values.
- Add mutation-sensitive checker, README, and completed-plan contracts.
- Keep all sample behavior and hosted macOS canary coverage unchanged.

## Work Completed

- Marked the Makefile root assignment as an explicit GNU Make override.
- Required one protected declaration, tool ordering, alias dependencies,
  canary paths, README indexing, and this plan's evidence.

## Verification

Final verification records hygiene, sample, full `make check`, hostile-root,
mutation, and repository audit results. Contract and hosted macOS canary jobs
remain required on the exact PR head.

- `make check` passed hygiene and sample contracts with the documented static
  path because local `xcodebuild` is unavailable.
- All five aliases passed from repository and external working directories
  under hostile environment and command-line root assignments, for 20 cases.
- Explicit Python and Xcode tool overrides remained effective.
- Seven declaration, duplicate, placement, alias, path, README, and plan
  mutations were rejected for the intended reason.
- Exact diff, protected-path, generated-artifact, high-confidence secret, and
  whitespace audits passed.

## Scope Boundary

This change does not alter Swift source, project settings, sample assets,
workflow policy, deployment targets, or accessibility behavior.
