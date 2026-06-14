# Make Root Override Protection

## Status: Planned

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

## Planned Work

- Mark the Makefile root assignment as an explicit GNU Make override.
- Require one protected declaration, tool ordering, alias dependencies,
  canary paths, README indexing, and this plan's evidence.

## Verification Plan

- Run hygiene, sample, and full Make gates under bounded hostile-root cases.
- Reject declaration, ordering, alias, path, README, and plan mutations.
- Audit the exact diff, protected sample/project/workflow paths, generated
  artifacts, secrets, and whitespace.
- Require contract and hosted macOS canary jobs on the exact PR head.

## Scope Boundary

This change does not alter Swift source, project settings, sample assets,
workflow policy, deployment targets, or accessibility behavior.
