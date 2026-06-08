# Issue 1: Use HTTPS Sample Endpoints

## Context

GitHub issue: `garethpaul/swift-sample-apps#1`

Several legacy Swift samples load runtime image or web URLs over plain HTTP. Those requests can expose traffic in transit and may be blocked by modern platform security defaults.

## Plan

1. Replace the reported Instagram CDN, Taobao, and Gareth Paul sample URL literals with HTTPS equivalents.
2. Preserve the legacy Swift control flow and Xcode project files.
3. Add a source-level verifier that rejects cleartext `http://` Swift runtime endpoints.

## Verification

- Run `bash scripts/check-https-runtime-endpoints.sh`.
- Run `git diff --check`.
