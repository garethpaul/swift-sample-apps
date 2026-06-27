# Service Error Privacy

## Status: Completed

## Context

The archived Facebook and Parse callbacks logged complete third-party
`NSError` objects. Provider errors may include request URLs, account metadata,
or other diagnostics that should not be copied into application logs by a
learning sample.

## Decision

Preserve generic failure diagnostics without interpolating provider error
objects. Keep user-facing Facebook error handling, Parse success handling, and
callback control flow unchanged.

## Work Completed

- Replace raw Facebook and Parse provider-error logging with bounded messages.
- Add static source contracts and hostile mutations for both integrations.
- Document the privacy boundary in repository guidance and history.

## Verification

- `python3 scripts/test-service-error-privacy.py` rejected both raw provider
  error mutations.
- Root and external-directory `make check` passed 35 Make authority cases and
  all note, todo, image, and service-error mutation suites.
- `swiftc` and `xcodebuild` skipped truthfully on Linux; hosted macOS remains
  the native execution gate.
- `git diff --check` passed before publication.
