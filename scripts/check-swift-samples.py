#!/usr/bin/python3
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
        run: make check

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
        run: make test
      - name: Run native background switcher tests
        run: make native-test
      - name: Build background switcher canary
        run: make build
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
TODO_LIST_CONTROLLER = "todo-list/todo-list/FirstViewController.swift"
TODO_TASK_MANAGER = "todo-list/todo-list/TaskManager.swift"
SWIFT_OBJECTS_CONTROLLER = "swift-objects-example/swift-objects-example/ViewController.swift"
BACKGROUND_SWITCHER_CONTROLLER = "background_switcher/background_switcher/ViewController.swift"
BACKGROUND_SELECTION_SOURCE = ROOT / "background_switcher/background_switcher/BackgroundSelection.swift"
BACKGROUND_SELECTION_TEST = ROOT / "Tests/BackgroundSelectionTests/main.swift"
BACKGROUND_SELECTION_RUNNER = ROOT / "scripts/test-background-selection.sh"
BACKGROUND_SWITCHER_PROJECT = ROOT / "background_switcher/background_switcher.xcodeproj/project.pbxproj"
TRUSTED_TOOLS_RUNNER = ROOT / "scripts/resolve-trusted-tools.sh"
GIT = Path("/usr/bin/git")
BACKGROUND_APP_TARGET = "background_switcher"
BACKGROUND_TEST_TARGET = "background_switcherTests"
EXPECTED_BACKGROUND_APP_SOURCES = (
    ROOT / "background_switcher/background_switcher/BackgroundSelection.swift",
    ROOT / "background_switcher/background_switcher/ViewController.swift",
    ROOT / "background_switcher/background_switcher/AppDelegate.swift",
)
EXPECTED_BACKGROUND_TEST_SOURCES = (
    ROOT / "background_switcher/background_switcherTests/background_switcherTests.swift",
)
BACKGROUND_SELECTION_STATE_TOKENS = (
    "CommandLine",
    "ProcessInfo",
    ".environment",
    "getenv",
    "setenv",
    "UserDefaults",
    "FileManager",
    "Bundle",
    "Date(",
    "Dispatch",
    "Thread",
    "Task",
    "async",
    "await",
    "XCTest",
    "XCTestConfigurationFilePath",
    "DEBUG",
    "TEST",
    "SIMULATOR",
    "TARGET_OS",
    "dlopen",
    "dlsym",
)
BACKGROUND_SELECTION_COUNTER_TOKENS = (
    "counter",
    "threshold",
    "attempt",
    "probe",
    "toggle",
    "mutation",
)
APP_SOURCE_TEST_AWARE_TOKENS = BACKGROUND_SELECTION_STATE_TOKENS + (
    "CommandLine.arguments",
    "arguments",
    "processInfo",
    "environment",
    "NSClassFromString",
)
EXPECTED_BACKGROUND_SELECTION_SOURCE_TEXT = """enum BackgroundSelection {
    case first
    case second

    static func supportedCases() -> [BackgroundSelection] {
        return [.first, .second]
    }

    var buttonTag: Int {
        switch self {
        case .first:
            return 1
        case .second:
            return 2
        }
    }

    var key: String {
        switch self {
        case .first:
            return "Background1"
        case .second:
            return "Background2"
        }
    }

    var title: String {
        switch self {
        case .first:
            return "Background 1"
        case .second:
            return "Background 2"
        }
    }

    static func selection(forButtonTag tag: Int) -> BackgroundSelection? {
        switch tag {
        case 1:
            return .first
        case 2:
            return .second
        default:
            return nil
        }
    }

    static func key(forButtonTag tag: Int) -> String? {
        return selection(forButtonTag: tag)?.key
    }
}
"""
ALLOWED_BACKGROUND_SWIFT_SETTINGS = {
    "SWIFT_OPTIMIZATION_LEVEL",
    "SWIFT_VERSION",
}
FORBIDDEN_SWIFT_SETTING_KEYS = {
    "OTHER_SWIFT_FLAGS",
    "SWIFT_ACTIVE_COMPILATION_CONDITIONS",
    "SWIFT_EXEC",
    "SWIFT_INCLUDE_PATHS",
    "SWIFT_OBJC_BRIDGING_HEADER",
    "SWIFT_RESPONSE_FILE_PATH",
}
FORBIDDEN_SWIFT_SETTING_VALUES = (
    ".swift",
    "$(SRCROOT)",
    "$(PROJECT_DIR)",
    "-filelist",
    "-primary-file",
    "-supplementary-output-file-map",
    "-vfsoverlay",
    "-load-plugin",
    "-plugin-path",
    "-Xfrontend",
)


def tracked_files():
    if not GIT.exists():
        raise RuntimeError("trusted git is missing at /usr/bin/git")
    output = subprocess.check_output([str(GIT), "ls-files"], cwd=str(ROOT), text=True)
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


def strip_pbx_comments(text):
    result = []
    index = 0
    in_string = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if in_string:
            result.append(char)
            if char == "\\" and next_char:
                result.append(next_char)
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(text) and not (text[index] == "*" and text[index + 1] == "/"):
                result.append("\n" if text[index] == "\n" else " ")
                index += 1
            index += 2
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] != "\n":
                result.append(" ")
                index += 1
            continue
        result.append(char)
        index += 1
    return "".join(result)


def tokenize_pbx(text):
    tokens = []
    index = 0
    punctuation = set("{}()=;,")
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char in punctuation:
            tokens.append(char)
            index += 1
            continue
        if char == '"':
            index += 1
            value = []
            while index < len(text):
                char = text[index]
                if char == "\\" and index + 1 < len(text):
                    value.append(text[index + 1])
                    index += 2
                    continue
                if char == '"':
                    index += 1
                    break
                value.append(char)
                index += 1
            tokens.append("".join(value))
            continue
        start = index
        while index < len(text) and not text[index].isspace() and text[index] not in punctuation:
            index += 1
        tokens.append(text[start:index])
    return tokens


class PBXParser:
    def __init__(self, text):
        self.tokens = tokenize_pbx(strip_pbx_comments(text))
        self.index = 0

    def peek(self):
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def take(self, expected=None):
        token = self.peek()
        if token is None:
            raise ValueError("unexpected end of project file")
        if expected is not None and token != expected:
            raise ValueError(f"expected {expected!r}, found {token!r}")
        self.index += 1
        return token

    def parse(self):
        value = self.parse_value()
        if self.peek() is not None:
            raise ValueError(f"unexpected token {self.peek()!r}")
        return value

    def parse_value(self):
        token = self.peek()
        if token == "{":
            return self.parse_dict()
        if token == "(":
            return self.parse_list()
        return self.take()

    def parse_dict(self):
        result = {}
        self.take("{")
        while self.peek() != "}":
            key = self.take()
            self.take("=")
            result[key] = self.parse_value()
            self.take(";")
        self.take("}")
        return result

    def parse_list(self):
        result = []
        self.take("(")
        while self.peek() != ")":
            result.append(self.parse_value())
            if self.peek() == ",":
                self.take(",")
        self.take(")")
        return result


def parse_pbx_project(project_path):
    parsed = PBXParser(project_path.read_text(encoding="utf-8")).parse()
    if not isinstance(parsed, dict) or not isinstance(parsed.get("objects"), dict):
        raise ValueError("project file does not contain an objects dictionary")
    return parsed


def flatten_build_setting(value):
    if isinstance(value, dict):
        return " ".join(f"{key} {flatten_build_setting(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(flatten_build_setting(item) for item in value)
    return str(value)


class BackgroundProjectGraph:
    def __init__(self, project_path):
        self.project_path = project_path
        self.project_dir = project_path.parents[1]
        self.parsed = parse_pbx_project(project_path)
        self.objects = self.parsed["objects"]
        self.parents = {}
        for object_id, item in self.objects.items():
            if isinstance(item, dict) and item.get("isa") in {"PBXGroup", "PBXVariantGroup"}:
                for child in item.get("children", []):
                    if child in self.parents:
                        raise ValueError(f"duplicate group membership for {child}")
                    self.parents[child] = object_id

    def object(self, object_id, expected_isa=None):
        item = self.objects.get(object_id)
        if not isinstance(item, dict):
            raise ValueError(f"missing PBX object {object_id}")
        if expected_isa is not None and item.get("isa") != expected_isa:
            raise ValueError(f"{object_id} must be {expected_isa}, found {item.get('isa')}")
        return item

    def target_id(self, target_name):
        matches = [
            object_id
            for object_id, item in self.objects.items()
            if isinstance(item, dict)
            and item.get("isa") == "PBXNativeTarget"
            and item.get("name") == target_name
        ]
        if len(matches) != 1:
            raise ValueError(f"expected one PBXNativeTarget named {target_name}, found {len(matches)}")
        return matches[0]

    def group_components(self, object_id):
        parent_id = self.parents.get(object_id)
        if parent_id is None:
            return []
        parent = self.object(parent_id)
        components = self.group_components(parent_id)
        if parent.get("sourceTree") in (None, "<group>"):
            path = parent.get("path")
            if path:
                components.append(path)
        return components

    def resolve_file_reference(self, file_ref_id):
        file_ref = self.object(file_ref_id, "PBXFileReference")
        path = file_ref.get("path") or file_ref.get("name")
        if not path:
            raise ValueError(f"PBXFileReference {file_ref_id} is missing path")
        source_tree = file_ref.get("sourceTree")
        if source_tree != "<group>":
            raise ValueError(f"Swift source file reference {path} must use <group>, found {source_tree}")
        if "$(" in path or path.startswith("/") or ".." in Path(path).parts:
            raise ValueError(f"Swift source file reference {path} must not use generated, absolute, or escaping paths")
        components = self.group_components(file_ref_id) + [path]
        candidate = self.project_dir.joinpath(*components).resolve(strict=False)
        try:
            candidate.relative_to(ROOT)
        except ValueError as exc:
            raise ValueError(f"Swift source file reference {path} escapes the repository") from exc
        if not candidate.exists():
            raise ValueError(f"compiled Swift source does not exist: {candidate.relative_to(ROOT)}")
        return candidate

    def source_phase_id(self, target_name):
        target = self.object(self.target_id(target_name), "PBXNativeTarget")
        phases = target.get("buildPhases", [])
        source_phases = [
            phase_id
            for phase_id in phases
            if self.objects.get(phase_id, {}).get("isa") == "PBXSourcesBuildPhase"
        ]
        if len(source_phases) != 1:
            raise ValueError(f"expected one PBXSourcesBuildPhase for {target_name}, found {len(source_phases)}")
        return source_phases[0]

    def compiled_sources(self, target_name):
        phase = self.object(self.source_phase_id(target_name), "PBXSourcesBuildPhase")
        build_file_ids = phase.get("files", [])
        if len(build_file_ids) != len(set(build_file_ids)):
            raise ValueError(f"{target_name} sources phase contains duplicate PBXBuildFile references")
        file_ref_ids = []
        resolved = []
        for build_file_id in build_file_ids:
            build_file = self.object(build_file_id, "PBXBuildFile")
            file_ref_id = build_file.get("fileRef")
            if not file_ref_id:
                raise ValueError(f"PBXBuildFile {build_file_id} is missing fileRef")
            file_ref_ids.append(file_ref_id)
            resolved.append(self.resolve_file_reference(file_ref_id))
        if len(file_ref_ids) != len(set(file_ref_ids)):
            raise ValueError(f"{target_name} sources phase contains duplicate PBXFileReference refs")
        if len(resolved) != len(set(resolved)):
            raise ValueError(f"{target_name} sources phase contains duplicate resolved Swift paths")
        return tuple(resolved)

    def swift_file_references(self):
        resolved = []
        for object_id, item in self.objects.items():
            if not isinstance(item, dict) or item.get("isa") != "PBXFileReference":
                continue
            path = item.get("path") or item.get("name") or ""
            if path.endswith(".swift") or item.get("lastKnownFileType") == "sourcecode.swift":
                resolved.append((object_id, self.resolve_file_reference(object_id)))
        paths = [path for _, path in resolved]
        if len(paths) != len(set(paths)):
            raise ValueError("background project contains duplicate Swift file references")
        return resolved

    def build_setting_errors(self):
        errors = []
        for object_id, item in self.objects.items():
            if not isinstance(item, dict) or item.get("isa") != "XCBuildConfiguration":
                continue
            settings = item.get("buildSettings", {})
            if not isinstance(settings, dict):
                continue
            for key, value in settings.items():
                flattened = flatten_build_setting(value)
                if key in FORBIDDEN_SWIFT_SETTING_KEYS:
                    errors.append(f"build setting {key} must not inject Swift sources or compiler behavior")
                if key.startswith("SWIFT_") and key not in ALLOWED_BACKGROUND_SWIFT_SETTINGS:
                    errors.append(f"unexpected Swift build setting {key} in background switcher project")
                if any(forbidden in flattened for forbidden in FORBIDDEN_SWIFT_SETTING_VALUES):
                    errors.append(f"build setting {key} must not reference Swift source injection flags")
        return errors


def swift_code_without_comments_and_strings(text):
    result = []
    index = 0
    in_line_comment = False
    in_block_comment = 0
    in_string = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if in_line_comment:
            if char == "\n":
                in_line_comment = False
                result.append("\n")
            else:
                result.append(" ")
            index += 1
            continue
        if in_block_comment:
            if char == "/" and next_char == "*":
                in_block_comment += 1
                result.extend("  ")
                index += 2
                continue
            if char == "*" and next_char == "/":
                in_block_comment -= 1
                result.extend("  ")
                index += 2
                continue
            result.append("\n" if char == "\n" else " ")
            index += 1
            continue
        if in_string:
            if char == "\\" and next_char:
                result.extend("  ")
                index += 2
                continue
            if char == '"':
                in_string = False
            result.append("\n" if char == "\n" else " ")
            index += 1
            continue
        if char == "/" and next_char == "/":
            in_line_comment = True
            result.extend("  ")
            index += 2
            continue
        if char == "/" and next_char == "*":
            in_block_comment = 1
            result.extend("  ")
            index += 2
            continue
        if char == '"':
            in_string = True
            result.append(" ")
            index += 1
            continue
        result.append(char)
        index += 1
    return "".join(result)


def background_selection_state_errors(source_path):
    errors = []
    text = source_path.read_text(encoding="utf-8")
    code = swift_code_without_comments_and_strings(text)
    relative = source_path.relative_to(ROOT)
    if text.strip() != EXPECTED_BACKGROUND_SELECTION_SOURCE_TEXT.strip():
        errors.append(f"background selection source must match the audited pure mapping implementation: {relative}")
    if "import UIKit" in code:
        errors.append("background selection mapping must remain framework-independent")
    if re.search(r"\ballCases\b", code) or "CaseIterable" in code:
        errors.append(f"background selection source must not expose overridable allCases/CaseIterable: {relative}")
    if re.search(r"\brawValue\b", code):
        errors.append(f"background selection source must not use RawRepresentable/rawValue mapping: {relative}")
    for token in BACKGROUND_SELECTION_STATE_TOKENS:
        if token in code:
            errors.append(f"background selection source must not use stateful/test-aware token {token}: {relative}")
    lower_code = code.lower()
    for token in BACKGROUND_SELECTION_COUNTER_TOKENS:
        if re.search(rf"\b{re.escape(token)}\w*\b", lower_code):
            errors.append(f"background selection source must not contain counter-like token {token}: {relative}")
    if re.search(r"\{\s*\[[^\]]+\]\s*(?:in)?", code):
        errors.append(f"background selection source must not use closure capture lists: {relative}")
    if re.search(r"[-+*/%]=", code):
        errors.append(f"background selection source must not use mutating compound assignments: {relative}")
    if re.search(r"^\s*@\w+", code, flags=re.MULTILINE):
        errors.append(f"background selection source must not use property wrappers or attributes: {relative}")
    for line_number, line in enumerate(code.splitlines(), start=1):
        stripped = line.strip()
        if re.search(r"\b(?:struct|class|actor)\b", stripped):
            errors.append(f"background selection source must not declare nested/static types: {relative}:{line_number}")
        var_match = re.search(r"\bvar\s+([A-Za-z_][A-Za-z0-9_]*)\b", stripped)
        if not var_match:
            continue
        allowed_computed = re.match(r"var\s+(buttonTag|key|title)\s*:\s*[^=]+{\s*$", stripped)
        if allowed_computed and not re.search(r"\b(static|class|lazy)\b", stripped):
            continue
        errors.append(f"background selection source must not declare mutable state: {relative}:{line_number}")
    if len(re.findall(r"\bstatic\s+func\s+selection\s*\(\s*forButtonTag\b", code)) != 1:
        errors.append("background selection mapping must have exactly one selection(forButtonTag:) definition")
    return errors


def compiled_app_source_state_errors(source_path):
    errors = []
    code = swift_code_without_comments_and_strings(source_path.read_text(encoding="utf-8"))
    relative = source_path.relative_to(ROOT)
    if "`" in code:
        errors.append(f"compiled app source must not use escaped identifiers: {relative}")
    if re.search(r"^\s*#(?:if|elseif|else|endif)\b", code, flags=re.MULTILINE):
        errors.append(f"compiled app source must not use conditional compilation: {relative}")
    for token in APP_SOURCE_TEST_AWARE_TOKENS:
        if token in code:
            errors.append(f"compiled app source must not use stateful/test-aware token {token}: {relative}")
    lower_code = code.lower()
    for token in BACKGROUND_SELECTION_COUNTER_TOKENS:
        if re.search(rf"\b{re.escape(token)}\w*\b", lower_code):
            errors.append(f"compiled app source must not contain counter-like token {token}: {relative}")
    if re.search(r"[-+*/%]=", code):
        errors.append(f"compiled app source must not use mutating compound assignments: {relative}")
    for line_number, line in enumerate(code.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        binding_or_declaration = stripped.startswith(("if let ", "guard let ", "let ", "var "))
        if not binding_or_declaration and re.search(r"(?<![.\w])([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\1\b", stripped):
            errors.append(f"compiled app source must not use self-assignment: {relative}:{line_number}")
        if re.search(r"\bself\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*self\.\1\b", stripped):
            errors.append(f"compiled app source must not use self-assignment: {relative}:{line_number}")
        if stripped.startswith("@propertyWrapper") or re.match(r"@\w+(?:\([^)]*\))?\s+(?:private\s+)?(?:static\s+|class\s+|lazy\s+)?(?:var|let)\b", stripped):
            errors.append(f"compiled app source must not use property-wrapper state: {relative}:{line_number}")
        if re.search(r"\{\s*\[[^\]]+\]", stripped):
            approved_view_controller_capture = (
                source_path == ROOT / "background_switcher/background_switcher/ViewController.swift"
                and stripped == ") { [weak self] _ in"
            )
            if not approved_view_controller_capture:
                errors.append(f"compiled app source must not use closure-captured state: {relative}:{line_number}")
        if re.search(r"\b(?:static|class)\s+(?:var|let)\b", stripped):
            errors.append(f"compiled app source must not declare static/class state: {relative}:{line_number}")
        if re.search(r"\blazy\s+var\b", stripped):
            errors.append(f"compiled app source must not declare lazy state: {relative}:{line_number}")
        type_match = re.search(r"\b(struct|class|actor)\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
        if type_match:
            approved_type = (
                (source_path == ROOT / "background_switcher/background_switcher/ViewController.swift" and stripped == "class ViewController: UIViewController {")
                or (source_path == ROOT / "background_switcher/background_switcher/AppDelegate.swift" and stripped == "class AppDelegate: UIResponder, UIApplicationDelegate {")
            )
            if not approved_type:
                errors.append(f"compiled app source must not declare helper {type_match.group(1)} state: {relative}:{line_number}")
        if line == stripped and re.match(r"(?:private\s+)?(?:var|let|func)\b", stripped):
            errors.append(f"compiled app source must not declare top-level helper state/function: {relative}:{line_number}")
    return errors


def background_compiled_source_errors():
    errors = []
    try:
        graph = BackgroundProjectGraph(BACKGROUND_SWITCHER_PROJECT)
        graph.swift_file_references()
        app_sources = graph.compiled_sources(BACKGROUND_APP_TARGET)
        test_sources = graph.compiled_sources(BACKGROUND_TEST_TARGET)
        errors.extend(graph.build_setting_errors())
    except ValueError as exc:
        return [str(exc)]
    if app_sources != EXPECTED_BACKGROUND_APP_SOURCES:
        found = ", ".join(str(path.relative_to(ROOT)) for path in app_sources)
        expected = ", ".join(str(path.relative_to(ROOT)) for path in EXPECTED_BACKGROUND_APP_SOURCES)
        errors.append(f"background switcher app target must compile exactly {expected}; found {found}")
    if test_sources != EXPECTED_BACKGROUND_TEST_SOURCES:
        found = ", ".join(str(path.relative_to(ROOT)) for path in test_sources)
        expected = ", ".join(str(path.relative_to(ROOT)) for path in EXPECTED_BACKGROUND_TEST_SOURCES)
        errors.append(f"background switcher test target must compile exactly {expected}; found {found}")
    for source_path in app_sources:
        errors.extend(compiled_app_source_state_errors(source_path))
        if source_path == BACKGROUND_SELECTION_SOURCE:
            errors.extend(background_selection_state_errors(source_path))
            continue
        code = swift_code_without_comments_and_strings(source_path.read_text(encoding="utf-8"))
        if re.search(r"\b(?:enum|extension)\s+BackgroundSelection\b", code):
            errors.append(f"compiled source must not redefine or extend BackgroundSelection: {source_path.relative_to(ROOT)}")
    return errors


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
    root_declaration = "override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))"
    if makefile.count(root_declaration) != 1:
        errors.append("Makefile must contain exactly one protected repository-root declaration")
    for contract in (
        "override SHELL := /bin/sh",
        ".SHELLFLAGS := -eu -c",
        "override TRUSTED_TOOLS := $(ROOT)/scripts/resolve-trusted-tools.sh",
        "override PYTHON := $(shell /bin/sh \"$(TRUSTED_TOOLS)\" python 2>/dev/null || true)",
        "override SWIFTC := $(shell /bin/sh \"$(TRUSTED_TOOLS)\" swiftc 2>/dev/null || true)",
        "override XCODEBUILD := $(shell /bin/sh \"$(TRUSTED_TOOLS)\" xcodebuild 2>/dev/null || true)",
        ".PHONY: build check contract-test lint native-test require-python test verify",
        "require-python:",
        "build: lint",
        "contract-test: require-python",
        "verify: lint test contract-test native-test build",
        "check: verify",
        '"$(ROOT)/scripts/check-swift-samples.py" --mode hygiene',
        '"$(ROOT)/scripts/check-swift-samples.py" --mode samples',
        '/bin/sh "$(ROOT)/scripts/test-background-selection.sh"',
        'trusted swiftc unavailable; skipping background selection Swift tests',
        "CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj",
        "native-test:",
        "-scheme background_switcher",
        "platform=iOS Simulator,name=iPhone 16 Pro,OS=latest",
        "test;",
        "trusted xcodebuild unavailable; skipping native background switcher tests",
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
    if "for project in */*.xcodeproj" in makefile:
        errors.append("Makefile must not build samples that require absent legacy SDK frameworks")

    if not TRUSTED_TOOLS_RUNNER.exists():
        errors.append("trusted tool resolver is missing")
    elif TRUSTED_TOOLS_RUNNER.read_text(encoding="utf-8").splitlines()[0] != "#!/bin/sh":
        errors.append("trusted tool resolver must start with /bin/sh")

    canary_project = BACKGROUND_SWITCHER_PROJECT.read_text(encoding="utf-8")
    errors.extend(background_compiled_source_errors())
    for contract in (
        "IPHONEOS_DEPLOYMENT_TARGET = 12.0;",
        "SWIFT_VERSION = 5.0;",
        'PRODUCT_BUNDLE_IDENTIFIER = "com.gpj.background-switcher";',
    ):
        if contract not in canary_project:
            errors.append(f"background switcher project must keep current setting: {contract}")

    canary_source = (ROOT / "background_switcher/background_switcher/ViewController.swift").read_text(encoding="utf-8")
    for contract in ("for selection in BackgroundSelection.supportedCases()", "#selector(buttonClicked(_:))", "UIView.transition("):
        if contract not in canary_source:
            errors.append(f"background switcher must keep Swift 5 source contract: {contract}")
    if "BackgroundSelection.allCases" in canary_source:
        errors.append("background switcher must not use overridable BackgroundSelection.allCases")
    if "button.tag = selection.buttonTag" not in canary_source:
        errors.append("background switcher buttons must use explicit selection button tags")
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
            "enum BackgroundSelection {",
            "case first",
            "case second",
            "static func supportedCases() -> [BackgroundSelection]",
            "return [.first, .second]",
            "var buttonTag: Int",
            "case .first:",
            "case .second:",
            'return "Background1"',
            'return "Background2"',
            'return "Background 1"',
            'return "Background 2"',
            "case 1:",
            "return .first",
            "case 2:",
            "return .second",
            "return nil",
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
            "#!/bin/sh",
            'BUILD_DIR=$(/usr/bin/mktemp -d',
            'SWIFTC=$(/bin/sh "$ROOT_DIR/scripts/resolve-trusted-tools.sh" swiftc)',
            'SDKROOT=$(/usr/bin/xcrun --show-sdk-path --sdk macosx',
            '/usr/bin/mktemp',
            '/bin/rm -rf -- "$BUILD_DIR"',
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
        if "#!/usr/bin/env sh" in runner or "command -v" in runner:
            errors.append("background selection runner must not trust env sh or PATH tool lookup")
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
