# Local Webview Content

## Status: Completed

## Context

The Swift object sample used two `UIWebView` examples that loaded remote
`http://` pages. Archive samples should be inspectable offline and should not
teach insecure network requests as the default web-view pattern.

## Objectives

- Preserve the `UIWebView` example entry in the Swift object sample.
- Replace remote HTTP pages with local sample HTML.
- Add static checker coverage that rejects insecure Swift URL literals.
- Keep README, VISION, and CHANGES aligned with the new guard.

## Work Completed

- Replaced both Swift object web-view requests with `loadHTMLString` local
  content.
- Added a Swift-source checker rule for `NSURL(string: "http://...")`.
- Updated repository docs so the offline web-view policy is discoverable.

## Verification

- `python3 scripts/check-swift-samples.py --mode samples`
- `make check`
- `make verify`
- `git diff --check`

## Follow-Up Candidates

- Modernize `UIWebView` examples to `WKWebView` when this archive moves beyond
  the original legacy Swift syntax.
- Add per-sample README notes for any example that intentionally requires a
  remote service.
