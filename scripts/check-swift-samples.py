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
BUILD_CANARY_PLAN = DOCS_PLANS / "2026-06-10-background-switcher-build.md"
WORKFLOW = ROOT / ".github" / "workflows" / "check.yml"
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
TODO_LIST_CONTROLLER = "todo-list/todo-list/FirstViewController.swift"
TODO_TASK_MANAGER = "todo-list/todo-list/TaskManager.swift"
SWIFT_OBJECTS_CONTROLLER = "swift-objects-example/swift-objects-example/ViewController.swift"


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
    if not BUILD_CANARY_PLAN.exists():
        errors.append("docs/plans/2026-06-10-background-switcher-build.md is missing")

    plans = sorted(DOCS_PLANS.glob("*.md")) if DOCS_PLANS.exists() else []
    if not plans:
        errors.append("docs/plans must contain at least one completed plan")
    for plan_path in plans:
        plan = plan_path.read_text(encoding="utf-8")
        if "Status: Completed" not in plan or "make check" not in plan:
            errors.append(f"{plan_path.relative_to(ROOT)} must record completed status and make check verification")

    for path in tracked_files():
        if "/xcuserdata/" in path or path.endswith(".xcuserstate"):
            errors.append(f"tracked Xcode user state should be removed: {path}")

    workflow = WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.exists() else ""
    for contract in (
        "permissions:",
        "contents: read",
        "concurrency:",
        "cancel-in-progress: true",
        "contract:",
        "runs-on: ubuntu-24.04",
        "timeout-minutes: 5",
        "build:",
        "runs-on: macos-15",
        "timeout-minutes: 15",
        "workflow_dispatch:",
        "actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10",
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405",
        'python-version: "3.12"',
        "run: make check",
        "run: make build",
    ):
        if contract not in workflow:
            errors.append(f"GitHub Actions workflow must keep contract: {contract}")

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for contract in (
        "ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))",
        "CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj",
        "-target background_switcher",
        "generic/platform=iOS Simulator",
        "CODE_SIGNING_ALLOWED=NO",
    ):
        if contract not in makefile:
            errors.append(f"Makefile must keep background switcher build contract: {contract}")
    if "for project in */*.xcodeproj" in makefile:
        errors.append("Makefile must not build samples that require absent legacy SDK frameworks")

    canary_project = (ROOT / "background_switcher/background_switcher.xcodeproj/project.pbxproj").read_text(encoding="utf-8")
    for contract in ("IPHONEOS_DEPLOYMENT_TARGET = 12.0;", "SWIFT_VERSION = 5.0;"):
        if contract not in canary_project:
            errors.append(f"background switcher project must keep current setting: {contract}")

    canary_source = (ROOT / "background_switcher/background_switcher/ViewController.swift").read_text(encoding="utf-8")
    for contract in ("for i in buttonTitles.indices", "#selector(buttonClicked(_:))", "UIView.animate(withDuration: 0.4"):
        if contract not in canary_source:
            errors.append(f"background switcher must keep Swift 5 source contract: {contract}")
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
        if path == TODO_TASK_MANAGER and "func taskAtIndex(index: Int) -> task?" not in text:
            errors.append(f"todo task lookup must return nil for stale indexes in {path}")
        if path == TODO_TASK_MANAGER and "func removeTaskAtIndex(index: Int) -> Bool" not in text:
            errors.append(f"todo task removal must report whether an index was removed in {path}")
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
