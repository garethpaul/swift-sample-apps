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
    env = kwargs.pop("env", None)
    if env is None:
        env = os.environ.copy()
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
    make_executable(
        fakebin / "python3",
        """
        #!/bin/sh
        printf '%s\n' "forged python accepted $*" >&2
        exit 0
        """,
    )
    make_executable(
        fakebin / "swiftc",
        """
        #!/bin/sh
        printf '%s\n' "forged swiftc accepted $*" >&2
        exit 0
        """,
    )
    make_executable(
        fakebin / "xcodebuild",
        """
        #!/bin/sh
        printf '%s\n' "forged xcodebuild accepted $*" >&2
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


def add_project_source(repo, filename, source):
    source_path = repo / "background_switcher" / "background_switcher" / filename
    source_path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
    project = repo / "background_switcher" / "background_switcher.xcodeproj" / "project.pbxproj"
    text = project.read_text(encoding="utf-8")
    build_id = "F00DBA5E0000000000000001"
    file_id = "F00DBA5E0000000000000002"
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
        f"{{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = {filename}; sourceTree = \"<group>\"; }};\n",
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
    run([GIT, "add", str(source_path), str(project)], repo, check=True)


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
                "make test accepted a forged PATH-front sh/python3/swiftc while required docs were broken",
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
                "make test accepted hostile SHELL/PYTHON/SWIFTC/XCODEBUILD overrides and symlinked tools",
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
                "direct runner execution accepted a PATH-front forged sh from #!/usr/bin/env sh",
            )

    def test_lint_rejects_xcode_compiled_allcases_extension_counter_bypass(self):
        with DisposableRepository() as repo:
            add_project_source(
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

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint ignored an Xcode-compiled BackgroundSelection.allCases extension with global/env/counter state",
            )

    def test_lint_rejects_xcode_compiled_selection_overload_and_global_state(self):
        with DisposableRepository() as repo:
            add_project_source(
                repo,
                "BackgroundSelectionOverload.swift",
                """
                private var globalSelectionProbe = 0

                extension BackgroundSelection {
                    static func selection(forButtonTag tag: Int, testProbe: Bool = true) -> BackgroundSelection? {
                        globalSelectionProbe += 1
                        return testProbe ? .first : BackgroundSelection(rawValue: tag)
                    }
                }
                """,
            )

            result = run([MAKE, "lint"], repo)

            self.assertNotEqual(
                result.returncode,
                0,
                "lint ignored an Xcode-compiled BackgroundSelection overload with global mutable state",
            )


if __name__ == "__main__":
    unittest.main()
