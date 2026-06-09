# Swift Debug Print Guard

## Status: Completed

## Context

`swift-sample-apps` is an archive of legacy iOS examples. The static checks
already guard credentials, tokenized URLs, synchronous image downloads, and
insecure URL literals. The background switcher sample still emitted loop-index
debug output while constructing buttons, which is unnecessary for archive
sample behavior.

## Objectives

- Remove nonessential debug printing from the background switcher sample.
- Add static verification so tracked Swift samples do not reintroduce active
  `print` or `println` logging.
- Keep the change local to source hygiene, without altering sample UI behavior.

## Work Completed

- Removed the loop-index `println` from
  `background_switcher/background_switcher/ViewController.swift`.
- Added an active Swift `print`/`println` detector to
  `scripts/check-swift-samples.py`.
- Documented the source hygiene guard in README, VISION, and CHANGES.

## Verification

- `python3 scripts/check-swift-samples.py --mode hygiene`
- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Replace local absolute framework paths in archived Facebook and Parse project
  files with documented placeholders.
- Add a top-level sample index with each app's service dependencies.
