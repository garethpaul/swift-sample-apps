## Swift Sample Apps Vision

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
- Maintain the top-level index of included examples
- Treat Swift and SDK versions as legacy until documented per sample

Next priorities:

- Add a README table with each sample, purpose, and required services
- Document Xcode and iOS version assumptions per app
- Add setup notes for Facebook and Parse examples without secrets
- Archive or modernize samples one at a time

Contribution rules:

- One PR = one focused sample, dependency, credential, or documentation change.
- Do not commit service keys or real user data.
- Keep sample-specific changes inside that sample directory.
- Include simulator notes for app behavior changes.

## Security And Responsible Use

Authentication and backend samples can expose credentials or user information.
Each sample should use fake data, local configuration, and explicit service
setup instructions.

## What We Will Not Merge For Now

- Checked-in service credentials
- Cross-sample rewrites without a migration plan
- Real user data in fixtures
- Production-readiness claims for archive samples
