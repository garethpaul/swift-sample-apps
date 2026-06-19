## Swift Sample Apps Vision

Background selection behavior should remain executable independently of UIKit
while the sample preserves its visual transition and accessibility semantics.
Its tag mapping should stay as an audited pure switch rather than a stateful or
environment-dependent production path.

Swift Sample Apps is an archive of small iOS examples, including background
switching, basic notes, Facebook login, Parse setup, Swift object examples, and
a todo list.

The repository is useful as a collection of early Swift app patterns and Xcode
project structures.

The goal is to preserve the samples as a learning archive while making each
subproject's dependencies, credentials, and modernization status clear.

The current focus is:

Priority:

- Preserve each sample app as an independent reference
- Keep service credentials out of source control
- Keep checked-in service examples placeholder-only
- Avoid main-thread remote image downloads in archive samples
- Keep web-view demos local unless a sample documents its network setup
- Avoid ad hoc Swift debug prints in archive samples
- Preserve delegate-supplied SDK errors instead of shadowing or force-unwrapping
  them
- Treat Facebook profile payloads as optional and ignore cancelled logins
- Check Parse save callback errors before reporting completion
- Guard sample table indexes before reading or updating local arrays
- Guard sample table indexes before removing local rows
- Guard swift object table indexes before opening detail views
- Keep Xcode framework and bridging-header paths repo-relative
- Maintain the top-level index of included examples
- Keep completed maintenance plans under `docs/plans`
- Keep portable CI fixed, credential-free, and reproducible from any cwd
- Keep the background-switcher Swift 5 build canary green on current Xcode
- Keep the background-switcher canvas responsive across current view sizes
- Keep rapid background selections aligned with the latest user action
- Keep background controls safe-area-aware, touch-accessible, and compatible
  with preferred text sizes
- Preserve background selection semantics for assistive technology
- Preserve structural verification for the pure background selection mapping
- Preserve Reduce Motion background changes without weakening rapid selection
  behavior
- Execute the native background-switcher XCTest target in current macOS CI
- Treat remaining Swift and SDK versions as legacy until documented per sample

Next priorities:

- Add a README table with each sample, purpose, and required services
- Document Xcode and iOS version assumptions per app
- Add setup notes for Facebook and Parse examples without secrets
- Add sample-specific notes for legacy table/data-source assumptions
- Archive or modernize samples one at a time

Contribution rules:

- One PR = one focused sample, dependency, credential, or documentation change.
- Do not commit service keys or real user data.
- Keep sample-specific changes inside that sample directory.
- Include simulator notes for app behavior changes.

## Security And Responsible Use

Canonical security policy and reporting:

- [`SECURITY.md`](SECURITY.md)

Authentication and backend samples can expose credentials or user information.
Each sample should use fake data, local configuration, and explicit service
setup instructions.

## What We Will Not Merge (For Now)

- Checked-in service credentials
- Ad hoc debug logging from sample app sources
- Shadowed or force-unwrapped SDK error objects in sample callbacks
- Developer-local absolute paths in Xcode project files
- Cross-sample rewrites without a migration plan
- Real user data in fixtures
- Production-readiness claims for archive samples

This list is a roadmap guardrail, not a permanent rule.
Strong user demand and strong technical rationale can change it.
