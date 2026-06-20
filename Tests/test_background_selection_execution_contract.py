#!/usr/bin/python3
import os
import shutil
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GIT = Path("/usr/bin/git")
MAKE = Path("/usr/bin/make")


def run(command, cwd, **kwargs):
    env = kwargs.pop("env", os.environ.copy())
    return subprocess.run(
        [str(part) for part in command],
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )


class DisposableRepository:
    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="swift-sample-contract.")
        self.path = Path(self._tmp.name) / "repo"
        self.path.mkdir()
        files = run(
            [GIT, "ls-files", "--cached", "--others", "--exclude-standard"],
            ROOT,
            check=True,
        ).stdout.splitlines()
        for relative in files:
            if relative.startswith("background_switcher/build/"):
                continue
            source = ROOT / relative
            destination = self.path / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                destination.symlink_to(os.readlink(source))
            elif source.is_file():
                shutil.copy2(source, destination)
        run([GIT, "init", "-q"], self.path, check=True)
        run([GIT, "add", "-A"], self.path, check=True)
        return self.path

    def __exit__(self, exc_type, exc, tb):
        self._tmp.cleanup()


def make_executable(path, content):
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def hostile_path(repo):
    fakebin = repo / "fakebin"
    fakebin.mkdir(exist_ok=True)
    for tool in ("python3", "swiftc", "xcodebuild"):
        make_executable(
            fakebin / tool,
            f"""
            #!/bin/sh
            printf '%s\\n' "forged {tool} accepted $*" >&2
            exit 0
            """,
        )
    make_executable(
        fakebin / "sh",
        """
        #!/bin/sh
        printf '%s\n' "forged sh accepted $*" >&2
        printf '%s\n' "Background selection Swift tests passed."
        exit 0
        """,
    )
    return f"{fakebin}{os.pathsep}{os.environ.get('PATH', '')}"


def project_file(repo):
    return repo / "background_switcher" / "background_switcher.xcodeproj" / "project.pbxproj"


def add_source_file(repo, filename, source):
    source_path = repo / "background_switcher" / "background_switcher" / filename
    source_path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
    return source_path


def add_swift_file_reference(repo, filename, path=None, source_tree='"<group>"'):
    project = project_file(repo)
    text = project.read_text(encoding="utf-8")
    build_id = "F00DBA5E0000000000000001"
    file_id = "F00DBA5E0000000000000002"
    file_path = path if path is not None else filename
    text = text.replace(
        "/* Begin PBXBuildFile section */\n",
        "/* Begin PBXBuildFile section */\n"
        f"\t\t{build_id} /* {filename} in Sources */ = "
        f"{{isa = PBXBuildFile; fileRef = {file_id} /* {filename} */; }};\n",
    )
    text = text.replace(
        "/* Begin PBXFileReference section */\n",
        "/* Begin PBXFileReference section */\n"
        f"\t\t{file_id} /* {filename} */ = "
        f"{{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = {file_path}; sourceTree = {source_tree}; }};\n",
    )
    text = text.replace(
        "\t\t\t\tFD4BC181193F84C100102D5D /* BackgroundSelection.swift */,\n",
        "\t\t\t\tFD4BC181193F84C100102D5D /* BackgroundSelection.swift */,\n"
        f"\t\t\t\t{file_id} /* {filename} */,\n",
    )
    text = text.replace(
        "\t\t\t\tFD4BC180193F84C100102D5D /* BackgroundSelection.swift in Sources */,\n",
        "\t\t\t\tFD4BC180193F84C100102D5D /* BackgroundSelection.swift in Sources */,\n"
        f"\t\t\t\t{build_id} /* {filename} in Sources */,\n",
    )
    project.write_text(text, encoding="utf-8")
    run([GIT, "add", "-A"], repo, check=True)


def replace(path, old, new):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"missing expected text in {path}: {old}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def inject_selection_mapping_prefix(selection_path, source):
    text = selection_path.read_text(encoding="utf-8")
    prefix = textwrap.dedent(source).strip()
    for marker in ("switch tag {", "return BackgroundSelection(rawValue: tag)"):
        if marker in text:
            selection_path.write_text(text.replace(marker, f"{prefix}\n        {marker}", 1), encoding="utf-8")
            return
    raise AssertionError("missing expected BackgroundSelection mapper body")


def inject_after_second_case(selection_path, source):
    text = selection_path.read_text(encoding="utf-8")
    insertion = textwrap.dedent(source)
    for marker in ("case second = 2\n", "case second\n"):
        if marker in text:
            selection_path.write_text(text.replace(marker, f"{marker}{insertion}", 1), encoding="utf-8")
            return
    raise AssertionError("missing expected BackgroundSelection second case")


class BackgroundSelectionExecutionContractTests(unittest.TestCase):
    def test_make_test_rejects_path_front_forged_shell_and_tools(self):
        with DisposableRepository() as repo:
            readme = repo / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                .replace("Background selection semantics", "Background selector semantics")
                .replace("background selection semantics", "background selector semantics"),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PATH"] = hostile_path(repo)

            result = run([MAKE, "test"], repo, env=env)

            self.assertNotEqual(
                result.returncode,
                0,
                "make test accepted PATH-front forged sh/python3/swiftc while required docs were broken",
            )

    def test_make_test_ignores_hostile_make_tool_variables_and_symlinks(self):
        with DisposableRepository() as repo:
            changes = repo / "CHANGES.md"
            changes.write_text(
                changes.read_text(encoding="utf-8").replace("background selection semantics", "background selector semantics"),
                encoding="utf-8",
            )
            fakebin = repo / "fakebin"
            fakebin.mkdir()
            true_link = fakebin / "python3-symlink"
            true_link.symlink_to("/usr/bin/true")
            env = os.environ.copy()
            env["PATH"] = hostile_path(repo)

            result = run(
                [
                    MAKE,
                    "test",
                    f"SHELL={fakebin / 'sh'}",
                    f"PYTHON={true_link}",
                    f"SWIFTC={fakebin / 'swiftc'}",
                    "XCODEBUILD=/usr/bin/true",
                ],
                repo,
                env=env,
            )

            self.assertNotEqual(
                result.returncode,
                0,
                "make test accepted hostile Make variables and symlinked tools",
            )

    def test_runner_direct_invocation_rejects_path_front_forged_sh(self):
        with DisposableRepository() as repo:
            swift_test = repo / "Tests" / "BackgroundSelectionTests" / "main.swift"
            swift_test.write_text('fatalError("the real compiled test must run")\n', encoding="utf-8")
            env = os.environ.copy()
            env["PATH"] = hostile_path(repo)

            result = run([repo / "scripts" / "test-background-selection.sh"], repo, env=env)

            self.assertNotEqual(
                result.returncode,
                0,
                "direct runner execution accepted PATH-front forged sh from #!/usr/bin/env sh",
            )

    def test_lint_rejects_canonical_comment_evil_file_ref_bypass(self):
        with DisposableRepository() as repo:
            add_source_file(
                repo,
                "EvilBackgroundSelection.swift",
                """
                enum BackgroundSelection: Int, CaseIterable {
                    case first = 1
                    case second = 2

                    var key: String { return "Background\\(rawValue)" }
                    var title: String { return "Background \\(rawValue)" }
                    static func selection(forButtonTag tag: Int) -> BackgroundSelection? {
                        return tag == 1 ? .second : BackgroundSelection(rawValue: tag)
                    }
                    static func key(forButtonTag tag: Int) -> String? {
                        return selection(forButtonTag: tag)?.key
                    }
                }
                """,
            )
            project = project_file(repo)
            text = project.read_text(encoding="utf-8")
            text = text.replace(
                "\t\tFD4BC15A193F84C100102D5D /* ViewController.swift */ = {isa = PBXFileReference;",
                "\t\tF00DBA5E0000000000000002 /* EvilBackgroundSelection.swift */ = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = EvilBackgroundSelection.swift; sourceTree = \"<group>\"; };\n"
                "\t\tFD4BC15A193F84C100102D5D /* ViewController.swift */ = {isa = PBXFileReference;",
            )
            text = text.replace(
                "FD4BC180193F84C100102D5D /* BackgroundSelection.swift in Sources */ = {isa = PBXBuildFile; fileRef = FD4BC181193F84C100102D5D /* BackgroundSelection.swift */; };",
                "FD4BC180193F84C100102D5D /* BackgroundSelection.swift in Sources */ = {isa = PBXBuildFile; fileRef = F00DBA5E0000000000000002 /* EvilBackgroundSelection.swift */; };",
            )
            project.write_text(text, encoding="utf-8")
            run([GIT, "add", "-A"], repo, check=True)

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint trusted canonical comments while PBXBuildFile fileRef compiled an evil path",
            )

    def test_lint_rejects_path_escape_duplicate_generated_and_build_setting_sources(self):
        with DisposableRepository() as repo:
            add_source_file(repo, "GeneratedSelection.swift", "extension BackgroundSelection {}\n")
            add_swift_file_reference(repo, "GeneratedSelection.swift", path="../GeneratedSelection.swift")
            project = project_file(repo)
            text = project.read_text(encoding="utf-8")
            text = text.replace(
                "SWIFT_VERSION = 5.0;",
                "SWIFT_VERSION = 5.0;\n\t\t\t\tOTHER_SWIFT_FLAGS = \"-primary-file $(SRCROOT)/background_switcher/GeneratedSelection.swift\";",
                1,
            )
            text = text.replace(
                "F00DBA5E0000000000000001 /* GeneratedSelection.swift in Sources */,\n",
                "F00DBA5E0000000000000001 /* GeneratedSelection.swift in Sources */,\n\t\t\t\tF00DBA5E0000000000000001 /* GeneratedSelection.swift in Sources */,\n",
            )
            project.write_text(text, encoding="utf-8")
            run([GIT, "add", "-A"], repo, check=True)

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint accepted path traversal, duplicate refs, generated sources, and Swift source build settings",
            )

    def test_lint_rejects_xcode_compiled_allcases_extension_counter_bypass(self):
        with DisposableRepository() as repo:
            add_source_file(
                repo,
                "BackgroundSelectionAllCasesOverride.swift",
                """
                import Foundation

                private var globalBackgroundSelectionAllCasesCounter = 0

                extension BackgroundSelection {
                    static var allCases: [BackgroundSelection] {
                        globalBackgroundSelectionAllCasesCounter += 1
                        if ProcessInfo.processInfo.environment["BACKGROUND_SELECTION_TEST_MODE"] == "1" {
                            return [.first, .second]
                        }
                        if globalBackgroundSelectionAllCasesCounter > 1_000_000 {
                            return [.second, .first, .first]
                        }
                        return [.first, .second]
                    }
                }
                """,
            )
            add_swift_file_reference(repo, "BackgroundSelectionAllCasesOverride.swift")

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint ignored an Xcode-compiled BackgroundSelection.allCases extension with global/env/counter state",
            )

    def test_lint_rejects_xcode_compiled_selection_overload_and_global_state(self):
        with DisposableRepository() as repo:
            add_source_file(
                repo,
                "BackgroundSelectionOverload.swift",
                """
                private var globalSelectionProbe = 0

                extension BackgroundSelection {
                    static func selection(forButtonTag tag: Int, testProbe: Bool = true) -> BackgroundSelection? {
                        globalSelectionProbe += 1
                        return testProbe ? .first : BackgroundSelection.selection(forButtonTag: tag)
                    }
                }
                """,
            )
            add_swift_file_reference(repo, "BackgroundSelectionOverload.swift")

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint ignored an Xcode-compiled BackgroundSelection overload with global mutable state",
            )

    def test_lint_rejects_nested_static_closure_counter_in_background_selection(self):
        with DisposableRepository() as repo:
            selection_source = repo / "background_switcher" / "background_switcher" / "BackgroundSelection.swift"
            selection_source.write_text(
                textwrap.dedent(
                    """
                    enum BackgroundSelection: Int, CaseIterable {
                        case first = 1
                        case second = 2

                        var key: String {
                            return "Background\\(rawValue)"
                        }

                        var title: String {
                            return "Background \\(rawValue)"
                        }

                        static func selection(forButtonTag tag: Int) -> BackgroundSelection? {
                            struct Threshold {
                                static var counter = 0
                            }
                            let mapper = { [tag] in
                                Threshold.counter += 1
                                if ProcessInfo.processInfo.environment["XCTestConfigurationFilePath"] != nil {
                                    return BackgroundSelection(rawValue: tag)
                                }
                                if Threshold.counter > 1_000_000 {
                                    return .second
                                }
                                return BackgroundSelection(rawValue: tag)
                            }
                            return mapper()
                        }

                        static func key(forButtonTag tag: Int) -> String? {
                            return selection(forButtonTag: tag)?.key
                        }
                    }
                    """
                ).lstrip(),
                encoding="utf-8",
            )
            run([GIT, "add", "-A"], repo, check=True)

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint ignored nested static state, closure capture, env/test branch, and threshold counter",
            )

    def test_lint_rejects_app_delegate_global_counter_helper_route(self):
        with DisposableRepository() as repo:
            app_delegate = repo / "background_switcher" / "background_switcher" / "AppDelegate.swift"
            replace(
                app_delegate,
                "import UIKit\n",
                textwrap.dedent(
                    """
                    import UIKit

                    private var appDelegateBackgroundSelectionProbe = 0

                    func appDelegateBackgroundSelectionOverride(_ tag: Int) -> BackgroundSelection? {
                        appDelegateBackgroundSelectionProbe = appDelegateBackgroundSelectionProbe + 1
                        if appDelegateBackgroundSelectionProbe > 1_000_000 {
                            return .second
                        }
                        return nil
                    }
                    """
                ).lstrip(),
            )
            selection = repo / "background_switcher" / "background_switcher" / "BackgroundSelection.swift"
            inject_selection_mapping_prefix(
                selection,
                """
                if let override = appDelegateBackgroundSelectionOverride(tag) {
                    return override
                }
                """,
            )
            run([GIT, "add", "-A"], repo, check=True)

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint accepted AppDelegate global >1M state routed from the selection mapper",
            )

    def test_lint_rejects_escaped_static_var_state_in_mapping(self):
        with DisposableRepository() as repo:
            selection = repo / "background_switcher" / "background_switcher" / "BackgroundSelection.swift"
            inject_after_second_case(selection, "\n    static var `x` = 0\n")
            inject_selection_mapping_prefix(
                selection,
                """
                `x` = `x` + 1
                if `x` > 1_000_000 {
                    return .second
                }
                """,
            )
            run([GIT, "add", "-A"], repo, check=True)

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint accepted escaped static var state inside the selection mapper",
            )

    def test_lint_rejects_app_delegate_conditional_compilation_argv_and_self_assignment(self):
        with DisposableRepository() as repo:
            app_delegate = repo / "background_switcher" / "background_switcher" / "AppDelegate.swift"
            replace(
                app_delegate,
                "import UIKit\n",
                textwrap.dedent(
                    """
                    import UIKit

                    #if canImport(UIKit)
                    private var conditionalBackgroundState = CommandLine.arguments.count
                    #endif

                    func conditionalBackgroundHelper(_ tag: Int) -> Int {
                        var candidate = tag
                        candidate = candidate
                        return candidate
                    }
                    """
                ).lstrip(),
            )
            run([GIT, "add", "-A"], repo, check=True)

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint accepted conditional compilation, argv awareness, global state, helper routing surface, and self-assignment in AppDelegate",
            )

    def test_lint_rejects_compiled_view_controller_class_actor_lazy_and_property_wrapper_state(self):
        with DisposableRepository() as repo:
            controller = repo / "background_switcher" / "background_switcher" / "ViewController.swift"
            replace(
                controller,
                "import UIKit\n",
                textwrap.dedent(
                    """
                    import UIKit

                    @propertyWrapper
                    struct HiddenWrapper {
                        var wrappedValue: Int
                    }

                    actor HiddenActor {
                        static var count = 0
                    }

                    class HiddenState {
                        lazy var value = 0
                        @HiddenWrapper var wrapped = 0
                    }
                    """
                ).lstrip(),
            )
            run([GIT, "add", "-A"], repo, check=True)

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint accepted class/actor/lazy/property-wrapper state in a compiled ViewController source",
            )

    def test_lint_rejects_exact_internal_hidden_flip_internal_func_threshold_bypass(self):
        with DisposableRepository() as repo:
            controller = repo / "background_switcher" / "background_switcher" / "ViewController.swift"
            replace(
                controller,
                "import UIKit\n",
                """
                import UIKit

                internal var hiddenFlip = false

                internal func hiddenSelectionTag(_ tag: Int) -> Int {
                    if tag > 1_000_000 {
                        hiddenFlip = !hiddenFlip
                        return 2
                    }
                    return tag
                }
                """,
            )
            replace(
                controller,
                "        guard let selection = BackgroundSelection.selection(forButtonTag: sender.tag) else {",
                "        sender.tag = hiddenSelectionTag(sender.tag)\n        guard let selection = BackgroundSelection.selection(forButtonTag: sender.tag) else {",
            )
            run([GIT, "add", "-A"], repo, check=True)

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint accepted the exact internal var hiddenFlip + internal func >1M mapper bypass",
            )

    def test_lint_rejects_modifier_permutation_state_in_compiled_source(self):
        with DisposableRepository() as repo:
            add_source_file(
                repo,
                "ModifierPermutationSelection.swift",
                """
                #if canImport(UIKit)
                import UIKit

                @propertyWrapper
                internal struct `HiddenWrapper` {
                    internal var wrappedValue: Bool
                }

                extension BackgroundSelection {
                    @available(iOS 13.0, *)
                    fileprivate static
                    var `hiddenFlip`: Bool {
                        get { false }
                        set { _ = newValue }
                    }

                    @discardableResult
                    nonisolated public static func
                    helperRoute
                    (
                        _ tag: Int
                    ) -> BackgroundSelection? {
                        var\u2003candidate = tag; candidate = 1_000_001
                        return candidate > 1_000_000 ? .second : nil
                    }

                    @HiddenWrapper
                    package static var wrappedFlip = false
                }
                #endif
                """,
            )
            add_swift_file_reference(repo, "ModifierPermutationSelection.swift")

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint accepted attribute/modifier permutations, escaped identifiers, semicolon-packed local state, and Unicode whitespace in a compiled helper route",
            )

    def test_lint_rejects_uikit_conditional_button_tag_rewrite_before_canonical_mapping(self):
        with DisposableRepository() as repo:
            controller = repo / "background_switcher" / "background_switcher" / "ViewController.swift"
            replace(
                controller,
                "import UIKit\n",
                textwrap.dedent(
                    """
                    import UIKit

                    #if canImport(UIKit)
                    fileprivate func rewriteBackgroundSelectionTag(_ tag: Int) -> Int {
                        var rewrittenTag = tag
                        if tag > 1_000_000 {
                            rewrittenTag = 2
                        }
                        return rewrittenTag
                    }
                    #endif
                    """
                ).lstrip(),
            )
            replace(
                controller,
                "        guard let selection = BackgroundSelection.selection(forButtonTag: sender.tag) else {",
                textwrap.dedent(
                    """
                            #if canImport(UIKit)
                            sender.tag = rewriteBackgroundSelectionTag(sender.tag)
                            #endif
                            guard let selection = BackgroundSelection.selection(forButtonTag: sender.tag) else {
                    """
                ).rstrip(),
            )
            run([GIT, "add", "-A"], repo, check=True)

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint accepted a UIKit-only helper assignment that rewrites the button tag before canonical selection mapping",
            )


if __name__ == "__main__":
    unittest.main()
