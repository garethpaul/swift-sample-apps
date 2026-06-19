# Background Native Deep Review

Status: Completed

## Scope

Deep-review the stacked background-switcher changes in pull requests #4 through
#11, including rapid selection, deterministic mapping, accessibility semantics,
runtime Reduce Motion changes, animation ownership, native XCTest execution,
and hosted CI contracts.

## Findings

1. The checked-in XCTest target did not compile on current Xcode because its
   2014 placeholder used the removed `measureBlock` API. Existing CI only built
   the app target and ran a standalone Swift mapping harness, so this failure
   was invisible.
2. Reduce Motion was sampled only when a button was tapped. Enabling the system
   preference during an active cross-dissolve left that animation running until
   completion.
3. Button tags, labels, dictionary keys, and colors were maintained in parallel
   collections. A future insertion or reorder could silently map a visible
   control to the wrong color.
4. System buttons inherited usable labels and button traits, but the contract
   was implicit and focus order was not executable proof.

## Root Cause and Provenance

- Native XCTest failure: introduced by the original 2014 test template commit
  `b99b2f5e`; carried forward because pull requests #4 through #11 did not run
  the native test target. Confidence: clear.
- Runtime Reduce Motion gap: introduced by pull request #9 commit `88153db7`,
  which checked `UIAccessibility.isReduceMotionEnabled` only inside the tap
  handler. Confidence: clear.
- Parallel mapping risk: carried forward from the original sample and made more
  visible by the executable mapping work in pull request #10. Confidence: clear.

## Fix

- Replace the placeholder tests with native XCTest coverage for mapping, rapid
  overlapping selection, selected state, labels, button traits, focus order,
  and runtime Reduce Motion cancellation.
- Observe `UIAccessibility.reduceMotionStatusDidChangeNotification`, remove any
  active image-view animations when motion becomes reduced, and restore the
  latest selected target color.
- Make `BackgroundSelection` the single deterministic source for tags, keys,
  and labels, with color ownership kept in one exhaustive controller switch.
- Add `make native-test`, include it in `make check` when Xcode is available,
  and execute it explicitly in the hosted macOS job.

## Verification

- Current Xcode native XCTest: 4 tests passed on an iPhone 16 Pro simulator.
- Standalone Swift mapping runner passed.
- Static checker rejected missing native-test workflow and Make contracts before
  those contracts were added.
- Final repository and external-directory `make check` passed.

## Residual Risk

No physical device, VoiceOver spoken-output session, Switch Control session, or
manual visual comparison was performed. Simulator XCTest proves state, labels,
traits, focus ordering, animation cancellation, and final color ownership, but
not subjective transition appearance or assistive-technology speech quality.
