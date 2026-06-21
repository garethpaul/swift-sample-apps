# Make Authority Isolation

Status: Completed

## Context

The verification Makefile protected direct `ROOT` assignment but derived the
checkout path with a whitespace-sensitive expression. Caller-selected shells,
non-executing Make modes, preload files, and additional `-f` programs could
break or replace verification before checked-in targets completed.

## Work Completed

- Derived the repository root from the loaded Makefile with quoting that
  preserves spaces, quotes, backticks, and literal dollar characters.
- Fixed the recipe shell and shell flags while preserving trusted Python,
  Swift compiler, and Xcode build tool overrides.
- Rejected bypassing Make modes, caller `MAKEFLAGS`, preload metadata,
  overridden Makefile metadata, and visible additional files.
- Added a bounded authority harness across all seven public targets and pinned
  hosted dispatch to `/usr/bin/make`.

## Verification

- `make root-test` passed 35 target/authority cases, one literal-dollar tool
  case, one raw tool Make-syntax rejection, two `MAKEFILE_LIST` rejections, two
  contained startup-boundary cases, and ten mode-flag rejections.
- Repository and external-directory `make check` passed on the portable host.
- Exact-head hosted contract and build jobs remain required before merge.

## Trust Boundary

GNU Make can execute preload and earlier additional-file parse expressions
before a checked-in Makefile can reject them. Trusted automation must invoke
only this repository Makefile. Python, `swiftc`, and `xcodebuild` remain trusted
caller inputs so local toolchains and the supported hosted matrix continue to
work; their raw values are frozen before Make expansion and shell-quoted.

## Scope Boundary

This change does not alter Swift source, Xcode project settings, sample assets,
deployment targets, accessibility behavior, or public sample behavior.
