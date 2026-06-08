# Service Credential Hygiene

## Problem

The archive contained real-looking Parse application/client key literals in the
Facebook sample and tokenized image URLs in two sample view controllers. Even
for legacy demos, checked-in service credentials and bearer-style URL tokens
make the repository unsafe to copy as starter code.

## TDD Evidence

1. Extended `scripts/check-swift-samples.py --mode samples` to scan tracked text
   files for known credential-like markers and tokenized URLs.
2. Replaced tokenized sample image URLs with non-secret placeholder image URLs.
3. Removed unused hardcoded Parse-style key variables from the Facebook sample
   and documented that Parse credentials belong in local setup only.

## Verification

- `make lint`
- `make test`
- `make verify`
- `git diff --check`

`make build` attempts each sample target when `xcodebuild` is installed;
otherwise it reports that static sample checks completed.
