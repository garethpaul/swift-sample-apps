import XCTest
@testable import background_switcher

final class BackgroundSwitcherTests: XCTestCase {
    func testSelectionMappingIsStable() {
        XCTAssertEqual(BackgroundSelection.supportedCases(), [.first, .second])
        XCTAssertEqual(BackgroundSelection.first.buttonTag, 1)
        XCTAssertEqual(BackgroundSelection.second.buttonTag, 2)
        XCTAssertEqual(BackgroundSelection.selection(forButtonTag: 1), .first)
        XCTAssertEqual(BackgroundSelection.selection(forButtonTag: 2), .second)
        XCTAssertNil(BackgroundSelection.selection(forButtonTag: 0))
        XCTAssertNil(BackgroundSelection.selection(forButtonTag: 3))
        XCTAssertEqual(BackgroundSelection.first.key, "Background1")
        XCTAssertEqual(BackgroundSelection.second.key, "Background2")
        XCTAssertEqual(BackgroundSelection.first.title, "Background 1")
        XCTAssertEqual(BackgroundSelection.second.title, "Background 2")
    }

    func testButtonsExposeLabelsTraitsAndExclusiveSelection() {
        let viewController = makeViewController()
        let buttons = backgroundButtons(in: viewController.view)

        XCTAssertEqual(buttons.map(\.accessibilityLabel), ["Background 1", "Background 2"])
        XCTAssertTrue(buttons.allSatisfy { $0.accessibilityTraits.contains(.button) })
        let buttonStack = firstStackView(in: viewController.view)
        XCTAssertEqual(buttonStack?.accessibilityElements as? [UIButton], buttons)
        XCTAssertTrue(buttons[0].isSelected)
        XCTAssertTrue(buttons[0].accessibilityTraits.contains(.selected))
        XCTAssertFalse(buttons[1].isSelected)
        XCTAssertFalse(buttons[1].accessibilityTraits.contains(.selected))

        buttons[1].sendActions(for: .touchUpInside)

        XCTAssertFalse(buttons[0].isSelected)
        XCTAssertFalse(buttons[0].accessibilityTraits.contains(.selected))
        XCTAssertTrue(buttons[1].isSelected)
        XCTAssertTrue(buttons[1].accessibilityTraits.contains(.selected))
    }

    func testLatestSelectionWinsAcrossOverlappingAnimations() {
        let viewController = makeViewController()
        viewController.reduceMotionEnabledProvider = { false }
        let buttons = backgroundButtons(in: viewController.view)

        buttons[1].sendActions(for: .touchUpInside)
        buttons[0].sendActions(for: .touchUpInside)

        XCTAssertEqual(viewController.imageView.backgroundColor, viewController.backgroundColor(for: .first))
        XCTAssertTrue(buttons[0].isSelected)
        XCTAssertFalse(buttons[1].isSelected)
    }

    func testReduceMotionChangeStopsActiveTransitionAtLatestSelection() {
        var reduceMotionEnabled = false
        let viewController = makeViewController()
        viewController.reduceMotionEnabledProvider = { reduceMotionEnabled }
        let buttons = backgroundButtons(in: viewController.view)

        buttons[1].sendActions(for: .touchUpInside)
        XCTAssertNotNil(viewController.imageView.layer.animationKeys())

        reduceMotionEnabled = true
        NotificationCenter.default.post(
            name: UIAccessibility.reduceMotionStatusDidChangeNotification,
            object: nil
        )

        XCTAssertNil(viewController.imageView.layer.animationKeys())
        XCTAssertEqual(viewController.imageView.backgroundColor, viewController.backgroundColor(for: .second))
        XCTAssertTrue(buttons[1].isSelected)
    }

    func testSelectionMappingRemainsCorrectAfterRepeatedAndDelayedAccess() {
        let viewController = makeViewController()
        viewController.reduceMotionEnabledProvider = { true }
        let buttons = backgroundButtons(in: viewController.view)

        for index in 0..<5_000 {
            let selection = index.isMultiple(of: 2) ? BackgroundSelection.first : .second
            let button = index.isMultiple(of: 2) ? buttons[0] : buttons[1]
            button.sendActions(for: .touchUpInside)

            XCTAssertEqual(BackgroundSelection.selection(forButtonTag: button.tag), selection)
            XCTAssertEqual(viewController.backgroundDict[selection.key], viewController.backgroundColor(for: selection))
            XCTAssertEqual(viewController.imageView.backgroundColor, viewController.backgroundColor(for: selection))
        }

        let delayedCheck = expectation(description: "mapping remains stable after delayed access")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.01) {
            XCTAssertEqual(BackgroundSelection.selection(forButtonTag: 1), .first)
            XCTAssertEqual(BackgroundSelection.selection(forButtonTag: 2), .second)
            XCTAssertEqual(
                viewController.backgroundDict[BackgroundSelection.first.key],
                viewController.backgroundColor(for: .first)
            )
            XCTAssertEqual(
                viewController.backgroundDict[BackgroundSelection.second.key],
                viewController.backgroundColor(for: .second)
            )
            delayedCheck.fulfill()
        }
        wait(for: [delayedCheck], timeout: 1.0)
    }

    private func makeViewController() -> ViewController {
        let viewController = ViewController()
        viewController.loadViewIfNeeded()
        return viewController
    }

    private func backgroundButtons(in view: UIView) -> [UIButton] {
        let directButtons = view.subviews.compactMap { $0 as? UIButton }
        return (directButtons + view.subviews.flatMap(backgroundButtons(in:))).sorted { $0.tag < $1.tag }
    }

    private func firstStackView(in view: UIView) -> UIStackView? {
        if let stackView = view as? UIStackView {
            return stackView
        }
        return view.subviews.lazy.compactMap(firstStackView(in:)).first
    }
}
