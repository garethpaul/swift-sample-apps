# Trusted Verifier Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Establish a base-owned verifier and non-spoofable deployment gate before attempting another semantic repair.

**Architecture:** Phase one adds only a trusted `pull_request_target` workflow, a hermetic verifier, exact reviewed semantic templates, and tests. After that commit is independently reviewed and merged, phase two creates a fresh one-commit semantic repair whose only changed files must exactly match the three base-owned templates. The trusted workflow treats the pull request checkout as Git object data and never executes pull request code.

**Tech Stack:** GitHub Actions, protected GitHub environments, repository branch protection or rulesets, Python 3 isolated mode, POSIX shell, Git object plumbing, Swift/Xcode in the existing untrusted `pull_request` workflow.

Status: Completed

---

## Why Two Pull Requests Are Mandatory

The rejected v1-v13 candidates tried to introduce semantic behavior and the mechanism that authenticated that behavior in the same untrusted commit. A pull request can rotate its verifier, tests, workflow, payload, and expected digest together. GitHub Actions check names do not solve that problem: a pull request-controlled workflow can emit the same job name through the same GitHub Actions App identity.

The bootstrap therefore does not change the app. Its exact parent is `e0b72f53b6ef73989b8dcd12473c8476c92baf02`, and v1-v13 must remain sibling non-ancestors. The bootstrap becomes a trust root only after independent review and merge to `master`. A semantic repair opened before that merge cannot be authenticated by this design.

## Phase One: Trusted Bootstrap

The bootstrap adds `.github/workflows/trusted-swift-sample-gate.yml`. On `pull_request_target`, GitHub loads that workflow from the base branch. The workflow checks out `${{ github.workflow_sha }}` into `trusted-base` and the pull request's public fork/head SHA into `candidate`. The candidate checkout is untrusted data: submodules, LFS, caches, credential persistence, candidate actions, candidate scripts, candidate Make targets, and candidate test binaries are all excluded.

The job has only `contents: read`, uses an ephemeral GitHub-hosted runner, references no repository or environment secrets, and targets the empty environment `swift-sample-trusted-verifier-v1`. Before the candidate checkout, a base-owned isolated Python preflight reads the public GitHub environment API and requires selected deployment branches with exactly one `master` branch policy. A missing or auto-created unprotected environment therefore fails closed. The launcher clears shell, Git, dynamic-loader, Python, and coverage startup variables, then invokes `/usr/bin/python3 -I -S -B` under an allowlisted environment. Tests explicitly inject `PYTHONPATH`, `PYTHONHOME`, `sitecustomize`, `usercustomize`, `PYTHONSTARTUP`, and coverage startup hooks.

The verifier confirms that its workflow, policy, launcher, templates, and verifier bytes are exact blobs from the workflow SHA. It requires the candidate head to be one commit with the trusted base as its sole parent. It reads commit/tree/blob objects with `/usr/bin/git --no-replace-objects`; it does not import, build, source, or execute candidate content.

## Merge Authority and Context Spoofing

`Trusted Swift Sample Structural Gate / base-owned-structural-gate` is diagnostic only. It must not be the sole required status context because another pull request workflow can reuse that name through the GitHub Actions App.

The authoritative gate is a required successful deployment to `swift-sample-trusted-verifier-v1`. After the bootstrap merges:

1. Create the environment with no secrets and no environment variables.
2. Restrict deployment branches/tags to the selected branch `master` only.
3. Disable administrator bypass for the applicable protection rule where the repository plan exposes that option.
4. Add `swift-sample-trusted-verifier-v1` to **Require deployments to succeed before merging** on `master`, using the existing branch protection rule or an active repository ruleset.
5. Keep existing `contract`, `build`, and CodeQL requirements as defense in depth, but do not treat their Actions context names as the trust root.

With that configuration, a `pull_request` workflow runs on a merge ref or head branch and cannot deploy to the selected `master` environment. A pull request cannot alter the base-owned `pull_request_target` workflow used for its event. A fork branch named `master` is not the base repository's protected `master` deployment ref. The protected deployment is therefore the merge authority; the same-named Actions check is not.

No GitHub settings are changed by this commit. The environment and required-deployment configuration must be inspected immediately after creation and again before the semantic repair is considered mergeable.

## Phase Two: Exact Semantic Repair

After the signed bootstrap merge becomes the live default, create a fresh branch directly from that exact default. The semantic candidate must contain exactly one commit and exactly these three changed paths:

1. `background_switcher/background_switcher/BackgroundSelection.swift`
2. `background_switcher/background_switcher/ViewController.swift`
3. `background_switcher/background_switcherTests/background_switcherTests.swift`

Each blob must exactly match its reviewed base-owned template under `trusted-verifier/expected/`. The candidate may not change workflows, the verifier, policy, templates, Makefiles, scripts, project files, portable tests, documentation, dependencies, submodules, symlinks, executable modes, or any additional path.

The trusted deployment verifies topology and exact blobs without executing candidate code. Separately, the ordinary read-only `pull_request` workflow runs portable checks, native XCTest, build, analyze, and CodeQL on the exact semantic head. The semantic pull request requires both layers: base-owned byte authentication and untrusted-runner behavior/build evidence.

## Hosted Validation Before Semantic Merge

The post-bootstrap review must record all of the following against the exact semantic SHA:

- A same-repository pull request receives the trusted deployment from the base-owned workflow.
- A public fork pull request receives the same deployment without any secret or manual workflow-code approval dependency.
- A malicious pull request workflow using the diagnostic job name does not satisfy the required deployment.
- Changes to `.github/workflows`, `trusted-verifier`, an extra path, a second commit, a merge commit, a wrong template byte, a symlink, or an executable mode are rejected.
- `PYTHONPATH`, `PYTHONHOME`, `PYTHONUSERBASE`, `PYTHONSTARTUP`, `sitecustomize`, `usercustomize`, coverage hooks, `BASH_ENV`, `ENV`, Git replacement objects, and Git config injection do not alter the verifier.
- Exact-head Linux contract, macOS native tests/build/analyze, Actions CodeQL, and Python CodeQL pass.
- The two historical generic API-key findings remain disclosed; provider-side rotation, revocation, deletion, audit-log review, and misuse review remain unverified until external evidence proves them.

## What the Bootstrap Proves

- The future semantic candidate is a direct one-commit child of the merged bootstrap default.
- Only the three reviewed semantic paths changed.
- Their modes and bytes exactly match templates stored in the signed base/default commit.
- The verifier and policy executed from the base workflow SHA under isolated Python startup.
- Candidate code was never executed by the privileged `pull_request_target` job.

## What the Bootstrap Does Not Prove

- It does not prove runtime behavior, Xcode compatibility, accessibility, animation behavior, or physical-device behavior.
- It does not protect its own bootstrap pull request; independent review and merge are prerequisites.
- It does not become merge-enforcing until the empty protected environment and required-deployment rule are configured.
- It does not make a GitHub Actions check name unspoofable. The protected deployment is the equivalent non-spoofable authority.
- It does not rotate or revoke historical provider credentials.

## Verification Record

- The trusted bootstrap unit suite covers exact bytes, topology, trust-boundary changes, trusted-checkout mutation, direct non-isolated Python, startup/coverage injection, workflow fork safety, least permissions, and deployment authority policy.
- `make check` passed from the repository and an external working directory.
- Actionlint, ShellCheck, Python compilation, Ruff, security scans, candidate-range secret scanning, diff checks, and Git integrity are required in the final evidence bundle.

## References

- GitHub `pull_request_target` behavior and warnings: <https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows>
- GitHub secure-use guidance: <https://docs.github.com/en/actions/reference/security/secure-use>
- Deployment environment branch restrictions: <https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments>
- Required deployments in protection rules/rulesets: <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets>
- Required status-check source limitations: <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks>
