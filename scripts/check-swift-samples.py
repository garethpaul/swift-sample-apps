#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_PLANS = ROOT / "docs" / "plans"
CANONICAL_PLAN = DOCS_PLANS / "2026-06-08-swift-sample-apps-baseline.md"
NOTE_INDEX_PLAN = DOCS_PLANS / "2026-06-09-note-index-guard.md"
TODO_INDEX_PLAN = DOCS_PLANS / "2026-06-09-todo-index-guard.md"
FACEBOOK_PAYLOAD_PLAN = DOCS_PLANS / "2026-06-10-facebook-payload-and-ci.md"
CI_HARDENING_PLAN = DOCS_PLANS / "2026-06-12-portable-ci-hardening.md"
BUILD_CANARY_PLAN = DOCS_PLANS / "2026-06-10-background-switcher-build.md"
RESPONSIVE_CANARY_PLAN = DOCS_PLANS / "2026-06-10-responsive-background-switcher.md"
BACKGROUND_SELECTION_PLAN = DOCS_PLANS / "2026-06-12-latest-background-selection.md"
ACCESSIBLE_BACKGROUND_CONTROLS_PLAN = DOCS_PLANS / "2026-06-13-accessible-background-controls.md"
BACKGROUND_SELECTION_SEMANTICS_PLAN = DOCS_PLANS / "2026-06-13-background-selection-semantics.md"
ROOT_OVERRIDE_PLAN = DOCS_PLANS / "2026-06-14-make-root-override-protection.md"
BACKGROUND_REDUCE_MOTION_PLAN = DOCS_PLANS / "2026-06-14-background-reduce-motion.md"
BACKGROUND_SELECTION_TEST_PLAN = DOCS_PLANS / "2026-06-16-background-selection-swift-tests.md"
BACKGROUND_TEST_EXECUTION_PLAN = DOCS_PLANS / "2026-06-19-background-test-execution-contract.md"
MAKE_AUTHORITY_PLAN = DOCS_PLANS / "2026-06-21-make-authority-isolation.md"
SAMPLE_INDEX_PLAN = DOCS_PLANS / "2026-06-25-sample-service-index.md"
NOTE_EDITOR_OWNERSHIP_PLAN = DOCS_PLANS / "2026-06-25-note-editor-ownership.md"
TODO_INPUT_PLAN = DOCS_PLANS / "2026-06-26-todo-task-input.md"
NOTE_EDITOR_OWNERSHIP_RUNNER = ROOT / "scripts" / "test-note-editor-ownership.py"
TODO_INPUT_RUNNER = ROOT / "scripts" / "test-todo-task-input.py"
WORKFLOW = ROOT / ".github" / "workflows" / "check.yml"
EXPECTED_WORKFLOW = """name: Check

on:
  pull_request:
  push:
    branches:
      - master
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: check-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  contract:
    runs-on: ubuntu-24.04
    timeout-minutes: 5
    steps:
      - name: Check out repository
        uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3
        with:
          persist-credentials: false
      - name: Set up Python
        uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0
        with:
          python-version: "3.12"
      - name: Run portable verification
        run: /usr/bin/make check

  build:
    runs-on: macos-15
    timeout-minutes: 15
    steps:
      - name: Check out repository
        uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3
        with:
          persist-credentials: false
      - name: Show Xcode version
        run: xcodebuild -version
      - name: Run background selection behavior tests
        run: /usr/bin/make test
      - name: Run native background switcher tests
        run: /usr/bin/make native-test
      - name: Build background switcher canary
        run: /usr/bin/make build
"""
SAMPLES = (
    "background_switcher",
    "basic-note-taker",
    "facebook-login",
    "parse_example",
    "swift-objects-example",
    "todo-list",
)
TEXT_SUFFIXES = {".h", ".md", ".pbxproj", ".plist", ".swift", ".txt"}
KNOWN_CREDENTIAL_MARKERS = (
    "9af1a259-2b33-4ca7-b605-28a2cc112608",
    "8eQR5sFwbogIl6Ehs1AUvJKXc8hrnyFePaNYeSek",
    "NCS4G5MSMNpbdiUWM67v2d7EmFJeKFl5TRbyZ8VD",
)
TOKENIZED_URL_RE = re.compile(r"https?://[^\"'\\s]+[?&]token=[A-Za-z0-9._~-]{12,}")
SYNC_IMAGE_LOAD_RE = re.compile(r"NSData\s*\(\s*contentsOfURL")
INSECURE_SWIFT_URL_RE = re.compile(r"NSURL\s*\(\s*string:\s*\"http://")
SWIFT_PRINT_RE = re.compile(r"\bprint(?:ln)?\s*\(")
LOCAL_XCODE_PATH_RE = re.compile(r"(/Users/|/home/|path = (?:\.\./)+(?:Desktop|Documents)/)")
FACEBOOK_LOGIN_CONTROLLER = "facebook-login/facebook-login/ViewController.swift"
PARSE_APP_DELEGATE = "parse_example/parse_example/AppDelegate.swift"
NOTE_LIST_CONTROLLER = "basic-note-taker/basic-note-taker/NoteListViewController.swift"
NOTE_EDITOR_CONTROLLER = "basic-note-taker/basic-note-taker/NoteEditorViewController.swift"
TODO_LIST_CONTROLLER = "todo-list/todo-list/FirstViewController.swift"
TODO_TASK_MANAGER = "todo-list/todo-list/TaskManager.swift"
TODO_ADD_CONTROLLER = "todo-list/todo-list/SecondViewController.swift"
SWIFT_OBJECTS_CONTROLLER = "swift-objects-example/swift-objects-example/ViewController.swift"
BACKGROUND_SWITCHER_CONTROLLER = "background_switcher/background_switcher/ViewController.swift"
BACKGROUND_SELECTION_SOURCE = ROOT / "background_switcher/background_switcher/BackgroundSelection.swift"
BACKGROUND_SELECTION_TEST = ROOT / "Tests/BackgroundSelectionTests/main.swift"
BACKGROUND_SELECTION_RUNNER = ROOT / "scripts/test-background-selection.sh"
MAKE_AUTHORITY_RUNNER = ROOT / "scripts/test-makefile-root.sh"


def tracked_files():
    output = subprocess.check_output(["git", "ls-files"], cwd=str(ROOT), text=True)
    return output.splitlines()


def tracked_text_files():
    for path in tracked_files():
        candidate = ROOT / path
        if candidate.name.startswith("README") or candidate.suffix in TEXT_SUFFIXES:
            yield path, candidate.read_text(encoding="utf-8", errors="ignore")


def has_active_swift_print(text):
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        if SWIFT_PRINT_RE.search(stripped):
            return True
    return False


def hygiene_checks():
    errors = []
    if not CANONICAL_PLAN.exists():
        errors.append("docs/plans/2026-06-08-swift-sample-apps-baseline.md is missing")
    if not NOTE_INDEX_PLAN.exists():
        errors.append("docs/plans/2026-06-09-note-index-guard.md is missing")
    if not TODO_INDEX_PLAN.exists():
        errors.append("docs/plans/2026-06-09-todo-index-guard.md is missing")
    if not FACEBOOK_PAYLOAD_PLAN.exists():
        errors.append("docs/plans/2026-06-10-facebook-payload-and-ci.md is missing")
    if not CI_HARDENING_PLAN.exists():
        errors.append("docs/plans/2026-06-12-portable-ci-hardening.md is missing")
    if not BUILD_CANARY_PLAN.exists():
        errors.append("docs/plans/2026-06-10-background-switcher-build.md is missing")
    if not RESPONSIVE_CANARY_PLAN.exists():
        errors.append("docs/plans/2026-06-10-responsive-background-switcher.md is missing")
    if not BACKGROUND_SELECTION_PLAN.exists():
        errors.append("docs/plans/2026-06-12-latest-background-selection.md is missing")
    if not ACCESSIBLE_BACKGROUND_CONTROLS_PLAN.exists():
        errors.append("docs/plans/2026-06-13-accessible-background-controls.md is missing")
    if not BACKGROUND_SELECTION_SEMANTICS_PLAN.exists():
        errors.append("docs/plans/2026-06-13-background-selection-semantics.md is missing")
    if not ROOT_OVERRIDE_PLAN.exists():
        errors.append("docs/plans/2026-06-14-make-root-override-protection.md is missing")
    if not BACKGROUND_REDUCE_MOTION_PLAN.exists():
        errors.append("docs/plans/2026-06-14-background-reduce-motion.md is missing")
    if not BACKGROUND_SELECTION_TEST_PLAN.exists():
        errors.append("docs/plans/2026-06-16-background-selection-swift-tests.md is missing")
    if not BACKGROUND_TEST_EXECUTION_PLAN.exists():
        errors.append("docs/plans/2026-06-19-background-test-execution-contract.md is missing")
    if not MAKE_AUTHORITY_PLAN.exists():
        errors.append("docs/plans/2026-06-21-make-authority-isolation.md is missing")
    if not SAMPLE_INDEX_PLAN.exists():
        errors.append("docs/plans/2026-06-25-sample-service-index.md is missing")
    if not NOTE_EDITOR_OWNERSHIP_PLAN.exists():
        errors.append("docs/plans/2026-06-25-note-editor-ownership.md is missing")
    if not TODO_INPUT_PLAN.exists():
        errors.append("docs/plans/2026-06-26-todo-task-input.md is missing")
    if not NOTE_EDITOR_OWNERSHIP_RUNNER.exists():
        errors.append("scripts/test-note-editor-ownership.py is missing")
    else:
        note_runner = NOTE_EDITOR_OWNERSHIP_RUNNER.read_text(encoding="utf-8")
        if "[sys.executable, str(CHECKER), \"--mode\", \"samples\"]" not in note_runner:
            errors.append("note editor mutation runner must reuse its configured Python interpreter")
        if '["python3", str(CHECKER)' in note_runner:
            errors.append("note editor mutation runner must not hard-code python3")
    if not TODO_INPUT_RUNNER.exists():
        errors.append("scripts/test-todo-task-input.py is missing")
    else:
        todo_runner = TODO_INPUT_RUNNER.read_text(encoding="utf-8")
        if "[sys.executable, str(CHECKER), \"--mode\", \"samples\"]" not in todo_runner:
            errors.append("todo input mutation runner must reuse its configured Python interpreter")
        if '["python3", str(CHECKER)' in todo_runner:
            errors.append("todo input mutation runner must not hard-code python3")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    sample_index_contracts = (
        "## Sample Index",
        "| `background_switcher` | Responsive, accessible background selection with current Swift behavior tests. | None. | Portable source checks, standalone Swift tests, native XCTest, and a current Xcode build canary. |",
        "| `basic-note-taker` | In-memory note list and editor using legacy table-view patterns. | None. | Static archive checks only; its historical Swift/Xcode toolchain is not pinned. |",
        "| `facebook-login` | Legacy Facebook login and optional profile display flow. | Legacy Facebook iOS SDK plus developer-local app configuration; never commit app credentials. | Static archive checks only because the SDK is not checked in. |",
        "| `parse_example` | Legacy Parse object-save callback example. | Legacy Parse iOS SDK plus developer-local application ID and client key; checked-in values are placeholders. | Static archive checks only because the SDK is not checked in. |",
        "| `swift-objects-example` | UIKit control catalog with local-only web-view content. | None. | Static archive checks only; its historical Swift/Xcode toolchain is not pinned. |",
        "| `todo-list` | In-memory task entry, display, and deletion sample. | None. | Static archive checks only; its historical Swift/Xcode toolchain is not pinned. |",
        "Only `background_switcher` is maintained as a current build",
    )
    for contract in sample_index_contracts:
        if contract not in readme:
            errors.append(f"README sample index is missing: {contract}")
    documentation_contracts = {
        "README.md": "basic note sample keeps editor delegation weak",
        "SECURITY.md": "basic note archive keeps editor delegation class-bound and weak",
        "VISION.md": "Keep basic note editor delegation weak",
        "CHANGES.md": "cycle: note editor ownership",
    }
    for relative_path, contract in documentation_contracts.items():
        if contract not in (ROOT / relative_path).read_text(encoding="utf-8"):
            errors.append(f"{relative_path} must preserve note editor ownership guidance")
    todo_documentation = {
        "README.md": "Todo insertion rejects empty",
        "VISION.md": "Reject blank todo names before insertion",
        "CHANGES.md": "cycle: todo task input",
    }
    for relative_path, contract in todo_documentation.items():
        if contract not in (ROOT / relative_path).read_text(encoding="utf-8"):
            errors.append(f"{relative_path} must preserve todo task-input guidance")

    plans = sorted(DOCS_PLANS.glob("*.md")) if DOCS_PLANS.exists() else []
    if not plans:
        errors.append("docs/plans must contain at least one completed plan")
    for plan_path in plans:
        plan = plan_path.read_text(encoding="utf-8")
        if "Status: Completed" not in plan or "make check" not in plan:
            errors.append(f"{plan_path.relative_to(ROOT)} must record completed status and make check verification")
    if BACKGROUND_REDUCE_MOTION_PLAN.exists():
        reduce_motion_plan = BACKGROUND_REDUCE_MOTION_PLAN.read_text(encoding="utf-8")
        for evidence in (
            "repository and external-directory `make check` passed",
            "hostile Reduce Motion mutations were rejected",
        ):
            if evidence not in reduce_motion_plan:
                errors.append(f"{BACKGROUND_REDUCE_MOTION_PLAN.relative_to(ROOT)} must record verification evidence: {evidence}")
    if BACKGROUND_SELECTION_TEST_PLAN.exists():
        selection_test_plan = BACKGROUND_SELECTION_TEST_PLAN.read_text(encoding="utf-8")
        for evidence in (
            "Status: Completed",
            "repository and external-directory `make check` passed",
            "hostile background selection mutations were rejected",
            "swiftc is unavailable",
            "hosted macOS",
        ):
            if evidence not in selection_test_plan:
                errors.append(f"{BACKGROUND_SELECTION_TEST_PLAN.relative_to(ROOT)} must record verification evidence: {evidence}")

    for path in tracked_files():
        if "/xcuserdata/" in path or path.endswith(".xcuserstate"):
            errors.append(f"tracked Xcode user state should be removed: {path}")

    workflow_files = sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
    if workflow_files != [WORKFLOW]:
        errors.append("repository must keep exactly one reviewed GitHub Actions workflow")
    workflow = WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.exists() else ""
    if workflow != EXPECTED_WORKFLOW:
        errors.append("GitHub Actions workflow must match the reviewed portable verification contract")

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    root_declaration = "override ROOT := $(shell path='$(subst ','\"'\"',$(value MAKEFILE_LIST))'; path=$$(printf '%s' \"$$path\" | /usr/bin/sed 's/^ //'); [ -f \"$$path\" ] || exit 1; directory=$$(/usr/bin/dirname -- \"$$path\"); CDPATH= cd -- \"$$directory\" && /bin/pwd -P)"
    if makefile.count(root_declaration) != 1:
        errors.append("Makefile must contain exactly one protected repository-root declaration")
    tool_contracts = (
        "PYTHON ?= python3",
        "XCODEBUILD ?= xcodebuild",
        "SWIFTC ?= swiftc",
        "override PYTHON := $(value PYTHON)",
        "override XCODEBUILD := $(value XCODEBUILD)",
        "override SWIFTC := $(value SWIFTC)",
        "export PYTHON XCODEBUILD SWIFTC",
        "override SHELL := /bin/sh",
        "override .SHELLFLAGS := -c",
    )
    if any(makefile.count(contract) != 1 for contract in tool_contracts):
        errors.append("Makefile must keep one authoritative declaration for each trusted tool and shell setting")
    elif max(makefile.index(contract) for contract in tool_contracts) > makefile.index(root_declaration):
        errors.append("Makefile must keep tool overrides before the protected repository root")
    for contract in (
        ".DEFAULT_GOAL := check",
        ".PHONY: __repository-make-authority build check lint native-test root-test test verify",
        ".SECONDEXPANSION:",
        "$(error MAKEFLAGS must not be overridden for repository verification)",
        "$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)",
        "$(error MAKEFILES must be empty; repository verification requires this Makefile to be loaded alone)",
        "$(error MAKEFILE_LIST must not be overridden)",
        "$(error repository Makefile path could not be resolved)",
        "build: lint",
        "root-test:",
        "verify: root-test lint test native-test build",
        "check: verify",
        '"$$ROOT/scripts/check-swift-samples.py" --mode hygiene',
        '"$$ROOT/scripts/check-swift-samples.py" --mode samples',
        '"$$ROOT/scripts/test-note-editor-ownership.py"',
        '"$$ROOT/scripts/test-todo-task-input.py"',
        '"$$ROOT/scripts/test-background-selection.sh"',
        '"$$ROOT/scripts/test-makefile-root.sh"',
        'swiftc unavailable; skipping background selection Swift tests',
        "override CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj",
        "native-test:",
        "-scheme background_switcher",
        "platform=iOS Simulator,name=iPhone 16 Pro,OS=latest",
        "test;",
        "xcodebuild unavailable; skipping native background switcher tests",
        "-target background_switcher",
        "generic/platform=iOS Simulator",
        "CODE_SIGNING_ALLOWED=NO",
    ):
        if contract not in makefile:
            errors.append(f"Makefile must keep background switcher build contract: {contract}")
    if "docs/plans/2026-06-14-make-root-override-protection.md" not in (ROOT / "README.md").read_text(encoding="utf-8"):
        errors.append("README must index Make root override protection evidence")
    if "docs/plans/2026-06-14-background-reduce-motion.md" not in (ROOT / "README.md").read_text(encoding="utf-8"):
        errors.append("README must index background Reduce Motion evidence")
    if str(MAKE_AUTHORITY_PLAN.relative_to(ROOT)) not in (ROOT / "README.md").read_text(encoding="utf-8"):
        errors.append("README must index Make authority isolation evidence")
    if not MAKE_AUTHORITY_RUNNER.is_file():
        errors.append("Make authority runner is missing")
    else:
        authority_runner = MAKE_AUTHORITY_RUNNER.read_text(encoding="utf-8")
        for contract in (
            "35 executed target/authority cases",
            "1 literal-dollar tool case",
            "1 raw tool Make-syntax rejection",
            "2 MAKEFILE_LIST rejections",
            "2 contained startup-boundary cases",
            "10 mode-flag rejections",
            "SWIFT_SAMPLES_BACKTICK_MARKER",
        ):
            if contract not in authority_runner:
                errors.append(f"Make authority runner contract is missing: {contract}")
        if not (MAKE_AUTHORITY_RUNNER.stat().st_mode & 0o111):
            errors.append("Make authority runner must be executable")
    if MAKE_AUTHORITY_PLAN.is_file():
        authority_plan = MAKE_AUTHORITY_PLAN.read_text(encoding="utf-8")
        for evidence in (
            "Status: Completed",
            "`make root-test` passed 35 target/authority cases",
            "Repository and external-directory `make check` passed",
            "Hosted contract and build jobs passed",
        ):
            if evidence not in authority_plan:
                errors.append(f"{MAKE_AUTHORITY_PLAN.relative_to(ROOT)} must record verification evidence: {evidence}")
    if "for project in */*.xcodeproj" in makefile:
        errors.append("Makefile must not build samples that require absent legacy SDK frameworks")

    canary_project = (ROOT / "background_switcher/background_switcher.xcodeproj/project.pbxproj").read_text(encoding="utf-8")
    for contract in (
        "IPHONEOS_DEPLOYMENT_TARGET = 12.0;",
        "SWIFT_VERSION = 5.0;",
        'PRODUCT_BUNDLE_IDENTIFIER = "com.gpj.background-switcher";',
    ):
        if contract not in canary_project:
            errors.append(f"background switcher project must keep current setting: {contract}")
    if canary_project.count("BackgroundSelection.swift in Sources") != 2:
        errors.append("background switcher project must compile BackgroundSelection.swift exactly once")
    if canary_project.count("/* BackgroundSelection.swift */ =") != 1:
        errors.append("background switcher project must keep one BackgroundSelection.swift file reference")

    canary_source = (ROOT / "background_switcher/background_switcher/ViewController.swift").read_text(encoding="utf-8")
    for contract in ("for selection in BackgroundSelection.allCases", "#selector(buttonClicked(_:))", "UIView.transition("):
        if contract not in canary_source:
            errors.append(f"background switcher must keep Swift 5 source contract: {contract}")
    if "width: CGFloat = 320" in canary_source or "height: CGFloat = 568" in canary_source:
        errors.append("background switcher must not use a fixed legacy device canvas")
    if "guard let selection = BackgroundSelection.selection(forButtonTag: sender.tag) else {" not in canary_source:
        errors.append("background switcher controller must delegate tag mapping to BackgroundSelection")
    if 'let imageSelector = "Background\\(sender.tag)"' in canary_source:
        errors.append("background switcher controller must not interpolate unchecked button tags")

    if not BACKGROUND_SELECTION_SOURCE.exists():
        errors.append("background selection production source is missing")
    else:
        selection_source = BACKGROUND_SELECTION_SOURCE.read_text(encoding="utf-8")
        for contract in (
            "enum BackgroundSelection: Int, CaseIterable",
            "case first = 1",
            "case second = 2",
            'return "Background\\(rawValue)"',
            'return "Background \\(rawValue)"',
            "return BackgroundSelection(rawValue: tag)",
            "return selection(forButtonTag: tag)?.key",
        ):
            if contract not in selection_source:
                errors.append(f"background selection production contract is missing: {contract}")
        if "import UIKit" in selection_source:
            errors.append("background selection mapping must remain framework-independent")

    expected_cases = (
        'expectKey("Background1", tag: 1, caseName: "first background")',
        'expectKey("Background2", tag: 2, caseName: "second background")',
        'expectKey(nil, tag: 0, caseName: "zero tag")',
        'expectKey(nil, tag: -1, caseName: "negative tag")',
        'expectKey(nil, tag: Int.min, caseName: "minimum integer tag")',
        'expectKey(nil, tag: 3, caseName: "out-of-range tag")',
    )
    if not BACKGROUND_SELECTION_TEST.exists():
        errors.append("background selection executable test is missing")
    else:
        selection_test = BACKGROUND_SELECTION_TEST.read_text(encoding="utf-8")
        for contract in expected_cases:
            if contract not in selection_test:
                errors.append(f"background selection executable case is missing: {contract}")

    if not BACKGROUND_SELECTION_RUNNER.exists():
        errors.append("background selection test runner is missing")
    else:
        runner = BACKGROUND_SELECTION_RUNNER.read_text(encoding="utf-8")
        for contract in (
            'BUILD_DIR=$(mktemp -d',
            "trap cleanup 0",
            "trap 'exit 129' 1",
            "trap 'exit 130' 2",
            "trap 'exit 143' 15",
            "background_switcher/background_switcher/BackgroundSelection.swift",
            "Tests/BackgroundSelectionTests/main.swift",
            '"$BUILD_DIR/background-selection-tests"',
        ):
            if contract not in runner:
                errors.append(f"background selection runner contract is missing: {contract}")
        executable = '"$BUILD_DIR/background-selection-tests"'
        if f'-o {executable}' not in runner:
            errors.append("background selection runner must compile the expected test binary")
        if [line.strip() for line in runner.splitlines()].count(executable) != 1:
            errors.append("background selection runner must execute the compiled test binary exactly once")
        if not (BACKGROUND_SELECTION_RUNNER.stat().st_mode & 0o111):
            errors.append("background selection test runner must be executable")

    if str(BACKGROUND_TEST_EXECUTION_PLAN.relative_to(ROOT)) not in (ROOT / "README.md").read_text(encoding="utf-8"):
        errors.append("README must index background test execution contract evidence")

    for document in ("README.md", "SECURITY.md", "VISION.md", "CHANGES.md"):
        if "Background selection behavior" not in (ROOT / document).read_text(encoding="utf-8"):
            errors.append(f"{document} must document executable background selection behavior")
    for contract in (
        "UIView(frame: view.bounds)",
        "UIImageView(frame: contentView.bounds)",
        "contentView.autoresizingMask = [.flexibleWidth, .flexibleHeight]",
        "imageView.autoresizingMask = [.flexibleWidth, .flexibleHeight]",
        "let buttonStack = UIStackView()",
        "buttonStack.translatesAutoresizingMaskIntoConstraints = false",
        "let safeArea = contentView.safeAreaLayoutGuide",
        "buttonStack.centerXAnchor.constraint(equalTo: safeArea.centerXAnchor)",
        "buttonStack.centerYAnchor.constraint(equalTo: safeArea.centerYAnchor)",
        "buttonStack.leadingAnchor.constraint(greaterThanOrEqualTo: safeArea.leadingAnchor, constant: 20)",
        "buttonStack.trailingAnchor.constraint(lessThanOrEqualTo: safeArea.trailingAnchor, constant: -20)",
        "button.heightAnchor.constraint(greaterThanOrEqualToConstant: 44)",
        "button.titleLabel?.font = UIFont.preferredFont(forTextStyle: .body)",
        "button.titleLabel?.adjustsFontForContentSizeCategory = true",
        "button.titleLabel?.numberOfLines = 0",
        "button.titleLabel?.textAlignment = .center",
        "buttonStack.addArrangedSubview(button)",
    ):
        if contract not in canary_source:
            errors.append(f"background switcher responsive layout contract is missing: {contract}")
    if "button.frame =" in canary_source or "button.center =" in canary_source:
        errors.append("background switcher controls must not use manual frame or center geometry")
    return errors


def samples_checks():
    errors = []
    for sample in SAMPLES:
        project_files = list((ROOT / sample).glob("*.xcodeproj/project.pbxproj"))
        swift_files = list((ROOT / sample).glob("**/*.swift"))
        test_files = list((ROOT / sample).glob("**/*Tests.swift"))
        if not project_files:
            errors.append(f"missing Xcode project for sample: {sample}")
        if not swift_files:
            errors.append(f"missing Swift source files for sample: {sample}")
        if not test_files:
            errors.append(f"missing Swift test files for sample: {sample}")

    for required in ("README.md", "SECURITY.md", "VISION.md", "LICENSE"):
        if not (ROOT / required).exists():
            errors.append(f"missing repository document: {required}")
    for doc_path in ("README.md", "SECURITY.md", "VISION.md", "CHANGES.md"):
        if "background selection semantics" not in (ROOT / doc_path).read_text(encoding="utf-8").lower():
            errors.append(f"{doc_path} must document background selection semantics")
        if "reduce motion background changes" not in (ROOT / doc_path).read_text(encoding="utf-8").lower():
            errors.append(f"{doc_path} must document Reduce Motion background changes")

    for path, text in tracked_text_files():
        for marker in KNOWN_CREDENTIAL_MARKERS:
            if marker in text:
                errors.append(f"tracked credential-like marker must be removed from {path}")
        if TOKENIZED_URL_RE.search(text):
            errors.append(f"tracked tokenized URL must be replaced with a placeholder in {path}")
        if path.endswith(".swift") and SYNC_IMAGE_LOAD_RE.search(text):
            errors.append(f"synchronous network image loading must be removed from {path}")
        if path.endswith(".swift") and INSECURE_SWIFT_URL_RE.search(text):
            errors.append(f"insecure remote URL literals must be replaced with local or HTTPS placeholders in {path}")
        if path.endswith(".swift") and has_active_swift_print(text):
            errors.append(f"active Swift print/println debug logging must be removed from {path}")
        if path.endswith(".pbxproj") and LOCAL_XCODE_PATH_RE.search(text):
            errors.append(f"local Xcode paths must be replaced with repo-relative placeholders in {path}")
        if path == FACEBOOK_LOGIN_CONTROLLER and "var error: NSError?" in text:
            errors.append(f"Facebook login error handling must not shadow the delegate NSError in {path}")
        if path == FACEBOOK_LOGIN_CONTROLLER and "error!" in text:
            errors.append(f"Facebook login error handling must not force-unwrap NSError values in {path}")
        if path == FACEBOOK_LOGIN_CONTROLLER:
            for contract in (
                'profileID = userObj["id"] as? String',
                'name = userObj["name"] as? String',
                'statusLabel?.text = "Unable to load your Facebook profile."',
                "FBErrorCategory.UserCancelled) {\n            return",
            ):
                if contract not in text:
                    errors.append(f"Facebook login payload contract is missing from {path}: {contract}")
            if 'userObj["id"] as String' in text or 'userObj["name"] as String' in text:
                errors.append(f"Facebook user payload fields must not be force-cast in {path}")
        if path == PARSE_APP_DELEGATE and 'NSLog("Done")' in text:
            errors.append(f"Parse save callback must not log success before checking errors in {path}")
        if path == PARSE_APP_DELEGATE and "if err != nil" not in text:
            errors.append(f"Parse save callback must check the NSError before reporting completion in {path}")
        if path == PARSE_APP_DELEGATE and "Parse save failed" not in text:
            errors.append(f"Parse save callback must log save failures in {path}")
        if path == PARSE_APP_DELEGATE and "Parse save did not complete" not in text:
            errors.append(f"Parse save callback must log unsuccessful saves without NSError metadata in {path}")
        if path == NOTE_LIST_CONTROLLER and "func note(indexPath: NSIndexPath) -> String {" in text:
            errors.append(f"basic note lookup must return an optional instead of indexing unconditionally in {path}")
        if path == NOTE_LIST_CONTROLLER and "func note(indexPath: NSIndexPath) -> String?" not in text:
            errors.append(f"basic note lookup must return nil for stale index paths in {path}")
        if path == NOTE_LIST_CONTROLLER and "indexPath.row < 0 || indexPath.row >= notes.count" not in text:
            errors.append(f"basic note lookup must guard indexPath.row before reading notes in {path}")
        if path == NOTE_LIST_CONTROLLER and "if let selectedNoteText = note(indexPath)" not in text:
            errors.append(f"basic note selection must optional-bind note lookup before opening the editor in {path}")
        if path == NOTE_LIST_CONTROLLER and "cell.textLabel.text = note(indexPath)" in text:
            errors.append(f"basic note cells must not assign an unchecked note lookup in {path}")
        if path == NOTE_LIST_CONTROLLER and "sselectedNote >= 0 && sselectedNote < notes.count" not in text:
            errors.append(f"basic note editor updates must guard selectedNote before writing notes in {path}")
        if path == NOTE_LIST_CONTROLLER and "var editor: NoteEditorViewController?" in text:
            errors.append(f"basic note list must not retain the pushed editor in {path}")
        if path == NOTE_LIST_CONTROLLER:
            selection_flow = (
                "selectedNote = indexPath.row",
                "let editor = NoteEditorViewController(note: selectedNoteText)",
                "editor.delegate = self",
                "navigationController.pushViewController(editor, animated: true)",
            )
            if any(fragment not in text for fragment in selection_flow):
                errors.append(f"basic note selection ownership flow is incomplete in {path}")
            elif [text.index(fragment) for fragment in selection_flow] != sorted(
                text.index(fragment) for fragment in selection_flow
            ):
                errors.append(f"basic note selection must publish index before delegate assignment and navigation in {path}")
        if path == NOTE_EDITOR_CONTROLLER and "protocol NoteEditorViewControllerDelegate: class" not in text:
            errors.append(f"basic note editor delegate protocol must remain class-bound in {path}")
        if path == NOTE_EDITOR_CONTROLLER and "weak var delegate: NoteEditorViewControllerDelegate?" not in text:
            errors.append(f"basic note editor delegate must remain weak in {path}")
        if path == TODO_TASK_MANAGER and "func taskAtIndex(index: Int) -> task?" not in text:
            errors.append(f"todo task lookup must return nil for stale indexes in {path}")
        if path == TODO_TASK_MANAGER and "func removeTaskAtIndex(index: Int) -> Bool" not in text:
            errors.append(f"todo task removal must report whether an index was removed in {path}")
        if path == TODO_TASK_MANAGER:
            add_contracts = (
                "func addTask(name: String , desc:String) -> Bool",
                "name.stringByTrimmingCharactersInSet(NSCharacterSet.whitespaceAndNewlineCharacterSet()).isEmpty",
                "return false",
                "tasks.append(task(name: name, desc: desc))",
                "return true",
            )
            if any(contract not in text for contract in add_contracts):
                errors.append(f"todo task insertion must reject blank names and report acceptance in {path}")
            elif [text.index(contract) for contract in add_contracts] != sorted(
                text.index(contract) for contract in add_contracts
            ):
                errors.append(f"todo task insertion must reject blank names before appending in {path}")
        if path == TODO_ADD_CONTROLLER:
            accepted_flow = (
                "if taskMngr.addTask(txtTask.text, desc: txtDesc.text) {",
                "self.view.endEditing(true)",
                'txtTask.text = ""',
                'txtDesc.text = ""',
                "self.tabBarController.selectedIndex = 0",
            )
            if any(contract not in text for contract in accepted_flow):
                errors.append(f"todo add UI must clear and navigate only after accepted insertion in {path}")
            elif [text.index(contract) for contract in accepted_flow] != sorted(
                text.index(contract) for contract in accepted_flow
            ):
                errors.append(f"todo add UI acceptance flow is out of order in {path}")
        if path == TODO_TASK_MANAGER and "index < 0 || index >= tasks.count" not in text:
            errors.append(f"todo task manager must guard indexes before reading or removing tasks in {path}")
        if path == TODO_LIST_CONTROLLER and "taskMngr.tasks.removeAtIndex(indexPath.row)" in text:
            errors.append(f"todo table delete must not remove an unchecked task index in {path}")
        if path == TODO_LIST_CONTROLLER and "taskMngr.tasks[indexPath.row]" in text:
            errors.append(f"todo table cells must not read unchecked task indexes in {path}")
        if path == TODO_LIST_CONTROLLER and "if taskMngr.removeTaskAtIndex(indexPath.row)" not in text:
            errors.append(f"todo table delete must use guarded task removal in {path}")
        if path == TODO_LIST_CONTROLLER and "if let currentTask = taskMngr.taskAtIndex(indexPath.row)" not in text:
            errors.append(f"todo table cells must optional-bind guarded task lookup in {path}")
        if path == SWIFT_OBJECTS_CONTROLLER and "return self.items!.count" in text:
            errors.append(f"swift objects table must not force unwrap items for row counts in {path}")
        if path == SWIFT_OBJECTS_CONTROLLER and "objectAtIndex(indexPath.row)  as String" in text:
            errors.append(f"swift objects selection must not read unchecked item indexes in {path}")
        if path == SWIFT_OBJECTS_CONTROLLER and "objectAtIndex(indexPath.row) as String" in text:
            errors.append(f"swift objects cells must not read unchecked item indexes in {path}")
        if path == SWIFT_OBJECTS_CONTROLLER and "func item(indexPath: NSIndexPath) -> String?" not in text:
            errors.append(f"swift objects item lookup must return nil for stale indexes in {path}")
        if path == SWIFT_OBJECTS_CONTROLLER and "indexPath.row < 0 || indexPath.row >= currentItems.count" not in text:
            errors.append(f"swift objects item lookup must guard indexPath.row before reading items in {path}")
        if path == SWIFT_OBJECTS_CONTROLLER and "if let itemTitle = item(indexPath)" not in text:
            errors.append(f"swift objects cells must optional-bind guarded item lookup in {path}")
        if path == SWIFT_OBJECTS_CONTROLLER and "if let selectedItemTitle = item(indexPath)" not in text:
            errors.append(f"swift objects selection must optional-bind guarded item lookup in {path}")
        if path == BACKGROUND_SWITCHER_CONTROLLER:
            if "UIView.animate(withDuration: 0.4" in text or "self.imageView.alpha =" in text:
                errors.append(f"background selection must not use delayed two-stage alpha animation in {path}")
            if "UIView.transition(" not in text or "with: imageView" not in text:
                errors.append(f"background selection must transition the image view directly in {path}")
            if "options: [.transitionCrossDissolve, .beginFromCurrentState, .allowUserInteraction]" not in text:
                errors.append(f"background transition must remain interruptible and interactive in {path}")
            if "duration: 0.4" not in text:
                errors.append(f"background transition must preserve the sample duration in {path}")
            transition_assignment = (
                "animations: {\n"
                "                        self.imageView.backgroundColor = backgroundColor\n"
                "                    },\n"
                "                    completion: nil"
            )
            if transition_assignment not in text:
                errors.append(f"background transition must assign color without a delayed completion write in {path}")
            if 'if let backgroundColor = self.backgroundDict[selection.key]' not in text:
                errors.append(f"background selection must preserve guarded color lookup in {path}")
            if "private var backgroundButtons: [UIButton] = []" not in text:
                errors.append(f"background controls must retain buttons for selection updates in {path}")
            if "backgroundButtons.append(button)" not in text:
                errors.append(f"background controls must retain each configured button in {path}")
            if "if let initialButton = backgroundButtons.first {\n            updateSelectedButton(initialButton)\n        }" not in text:
                errors.append(f"background controls must initialize the first selected state safely in {path}")
            reduce_motion_order = (
                "if let backgroundColor = self.backgroundDict[selection.key] {\n"
                "            selectedBackground = selection\n"
                "            updateSelectedButton(sender)\n"
                "            if reduceMotionEnabledProvider() {"
            )
            if reduce_motion_order not in text:
                errors.append(f"background selection semantics must update only after valid color lookup in {path}")
            reduce_motion_contract = (
                "if reduceMotionEnabledProvider() {\n"
                "                imageView.layer.removeAllAnimations()\n"
                "                imageView.backgroundColor = backgroundColor\n"
                "            } else {\n"
                "                UIView.transition("
            )
            if reduce_motion_contract not in text:
                errors.append(f"background changes must bypass animation when Reduce Motion is enabled in {path}")
            if "button.isSelected = button === selectedButton" not in text:
                errors.append(f"background selection must remain exclusive in {path}")
            if "button.accessibilityTraits.insert(.selected)" not in text or "button.accessibilityTraits.remove(.selected)" not in text:
                errors.append(f"background selection must synchronize the selected accessibility trait in {path}")
            if "button.contentEdgeInsets = UIEdgeInsets(top: 12, left: 16, bottom: 12, right: 16)" not in text:
                errors.append(f"background controls must preserve padded Dynamic Type targets in {path}")
            for contract in (
                "button.accessibilityLabel = selection.title",
                "button.accessibilityTraits.insert(.button)",
                "buttonStack.accessibilityElements = backgroundButtons",
                "UIAccessibility.reduceMotionStatusDidChangeNotification",
                "imageView.layer.removeAllAnimations()",
                "imageView.backgroundColor = backgroundColor(for: selectedBackground)",
            ):
                if contract not in text:
                    errors.append(f"background accessibility and motion contract is missing in {path}: {contract}")

    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("hygiene", "samples"), required=True)
    args = parser.parse_args()

    errors = hygiene_checks() if args.mode == "hygiene" else samples_checks()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"{args.mode} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
