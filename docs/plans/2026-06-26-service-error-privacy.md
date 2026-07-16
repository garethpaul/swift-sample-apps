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

## Follow-up: enforce the property, not the wording

Review found the first contract pinned the exact log strings
(`'NSLog("Unexpected Facebook login error")' not in text`). That made the
contract reject the *better* diagnostic — `NSLog("... code=%ld", error.code)`
no longer contains the pinned substring — so improving the message would have
required editing the test that guards it. `error.code` and `error.domain` are
not provider metadata, and this plan's own requirement is to identify the
failing integration without copying provider metadata, so those forms should
have been acceptable from the start.

### Changes

- Replaced the exact-string requirements with a prefix requirement plus two
  regexes enforcing the actual property: no raw `NSError` reaches the log,
  whether passed as a `%@` argument or interpolated as `\(error)`.
- Added interpolation mutations. The original contract caught `\(error)` only
  incidentally, via the missing pinned substring; once the wording lock is
  relaxed that incidental cover disappears, so the interpolation regex is
  load-bearing. Verified by neutralizing it: the leak then passes.
- Added `ALLOWED_FORMS` cases asserting bounded `code`/`domain` diagnostics are
  accepted, so a future tightening cannot silently re-block the better fix.

### Verification

- `scripts/test-service-error-privacy.py`: 4 hostile mutations rejected, 2
  bounded diagnostics accepted, sources restored.
- Old contract vs improved form: old exits 1 ("must keep a bounded
  diagnostic"); new exits 0. The raw `%@` regression is still rejected by both.
- `make check` exit 0. Swift remains uncompiled here and in CI, which builds
  only `background_switcher`; these contracts are static checks, not builds.
