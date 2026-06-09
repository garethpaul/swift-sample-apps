# Changes

## 2026-06-09

- Guarded the todo-list sample against stale table indexes before reading or
  removing tasks.
- Guarded the basic note sample against stale table indexes before reading or
  updating the notes array.
- Updated the Parse sample save callback to handle `NSError` and unsuccessful
  saves before reporting completion.
- Replaced developer-local Facebook and Parse Xcode framework paths with
  repo-relative placeholders and added static guard coverage.
- Fixed the Facebook login error handler to use the delegate-supplied
  `NSError` instead of shadowing it with `nil`.
- Extended Swift sample checks to reject Facebook login error shadowing and
  forced `NSError` unwraps.
- Removed background-switcher loop-index debug logging from view setup.
- Extended Swift sample checks to reject active `print`/`println` debug logging
  in tracked Swift sources.

## 2026-06-08

- Replaced remote HTTP UIWebView requests with local sample HTML and added
  checker coverage for insecure Swift URL literals.
- Ignored Python bytecode caches produced by local checker syntax validation.
- Removed synchronous remote image downloads from the background switcher and
  Parse examples, with static checker coverage.
- Added `make check` as the shared repository verification alias.
- Removed hardcoded credential-like Parse values and tokenized sample image
  URLs from the Facebook, Parse, and background switcher samples.
- Extended the sample checker to scan tracked text files for known
  credential-like markers and tokenized URLs.
- Added a Makefile verification gate for sample inventory and repository
  hygiene checks.
- Removed tracked Xcode per-user state files from sample projects.
- Added ignore rules for Xcode user state and DerivedData.
- Documented the local static verification workflow.
- Added canonical `docs/plans` coverage and made hygiene checks require
  completed plans.
