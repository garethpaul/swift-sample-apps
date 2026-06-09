# AGENTS.md

## Repository purpose

`garethpaul/swift-sample-apps` is an Apple platform application or Swift sample. Creating a master repo for the slew of random iOS apps.

## Project structure

- `Makefile` - repository verification targets
- `scripts` - baseline checks and helper scripts
- `docs` - plans, notes, and generated README assets
- `background_switcher` - repository source or sample assets
- `basic-note-taker` - repository source or sample assets
- `facebook-login` - repository source or sample assets
- `parse_example` - repository source or sample assets
- `plans` - repository source or sample assets
- `swift-objects-example` - repository source or sample assets
- `todo-list` - repository source or sample assets

## Development commands

- Install dependencies: no repository-specific install command is documented.
- Full baseline: `make check`
- Combined verification: `make verify`
- Lint/static checks: `make lint`
- Tests: `make test`
- Build: `make build`
- If a command above skips because a platform toolchain is missing, verify on a machine with that SDK before claiming platform behavior is tested.

## Coding conventions

- Language mix noted in the README: Swift (25), C/C++ headers (2).

## Testing guidance

- Test-related files detected: `background_switcher/background_switcherTests/background_switcherTests.swift`, `basic-note-taker/basic-note-takerTests/basic_note_takerTests.swift`, `facebook-login/facebook-loginTests/facebook_loginTests.swift`, `parse_example/parse_exampleTests/parse_exampleTests.swift`, `swift-objects-example/swift-objects-exampleTests/swift_objects_exampleTests.swift`, `todo-list/todo-listTests/todo_listTests.swift`
- Start with the narrowest relevant test or Make target, then run `make check` before handing off if the change is not documentation-only.
- Keep README verification notes in sync when commands, fixtures, or supported toolchains change.

## PR / change guidance

- Keep diffs focused on the requested repository and avoid unrelated modernization or formatting churn.
- Preserve public APIs, sample behavior, file formats, and documented environment variables unless the task explicitly changes them.
- Update tests, README notes, or docs/plans when behavior, security posture, or validation commands change.
- Call out skipped platform validation, legacy toolchain assumptions, and any risky files touched in the final summary.

## Safety and gotchas

- No required secret or credential file was identified in the repository scan. If you add integrations later, keep secrets out of git.
- Facebook and Parse examples should keep app IDs, client keys, and access tokens in local setup only; checked-in examples should use placeholders or non-secret sample URLs.
- Facebook and Parse SDK frameworks should be supplied locally under each sample's `Frameworks` directory when opening those archived projects in Xcode.
- This looks like an Apple platform project or sample. Xcode, Swift, CocoaPods, and deployment target versions may need to match the original project era.
- See `SECURITY.md` for vulnerability reporting and safe research guidance.
- See `VISION.md` for project direction and contribution guardrails.

## Agent workflow

1. Inspect the README, Makefile, manifests, and the files directly related to the request.
2. Make the smallest source or docs change that satisfies the task; avoid generated, vendored, or local-environment files unless required.
3. Run the narrowest useful validation first, then `make check` or the documented package/platform gate when available.
4. If a required SDK, service credential, or external runtime is unavailable, record the skipped command and why.
5. Summarize changed files, commands run, and remaining risks or follow-up validation.
