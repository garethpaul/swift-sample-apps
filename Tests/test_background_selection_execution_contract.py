import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKGROUND_SELECTION = ROOT / "background_switcher" / "background_switcher" / "BackgroundSelection.swift"


STATEFUL_SELECTION_TEMPLATE = """\
enum BackgroundSelection: Int, CaseIterable {{
    case first = 1
    case second = 2

    private static var initializationCount = 0

    init?(rawValue: Int) {{
        BackgroundSelection.initializationCount += 1
        if BackgroundSelection.initializationCount > {threshold} {{
            return nil
        }}

        switch rawValue {{
        case 1:
            self = .first
        case 2:
            self = .second
        default:
            return nil
        }}
    }}

    var buttonTag: Int {{
        return rawValue
    }}

    var key: String {{
        return "Background\\(rawValue)"
    }}

    var title: String {{
        return "Background \\(rawValue)"
    }}

    static func selection(forButtonTag tag: Int) -> BackgroundSelection? {{
        return BackgroundSelection(rawValue: tag)
    }}

    static func key(forButtonTag tag: Int) -> String? {{
        return selection(forButtonTag: tag)?.key
    }}
}}
"""


TEST_AWARE_SELECTION = """\
import Foundation

enum BackgroundSelection: Int, CaseIterable {
    case first = 1
    case second = 2

    var buttonTag: Int {
        return rawValue
    }

    var key: String {
        return "Background\\(rawValue)"
    }

    var title: String {
        return "Background \\(rawValue)"
    }

    static func selection(forButtonTag tag: Int) -> BackgroundSelection? {
        if CommandLine.arguments.first?.contains("background-selection-tests") == true {
            return BackgroundSelection(rawValue: tag)
        }
        return nil
    }

    static func key(forButtonTag tag: Int) -> String? {
        return selection(forButtonTag: tag)?.key
    }
}
"""


class BackgroundSelectionExecutionContractTests(unittest.TestCase):
    maxDiff = None

    def test_exact_4097_counter_bypass_is_rejected(self):
        with copied_repo() as repo:
            write_selection(repo, STATEFUL_SELECTION_TEMPLATE.format(threshold=4096))

            result = run_make(repo, "test")

        self.assertNotEqual(
            result.returncode,
            0,
            "make test accepted production that returns nil for valid selections on call 4097",
        )

    def test_counter_threshold_family_is_rejected_structurally(self):
        for threshold in (16, 17, 257, 4096, 65536):
            with self.subTest(threshold=threshold):
                with copied_repo() as repo:
                    write_selection(repo, STATEFUL_SELECTION_TEMPLATE.format(threshold=threshold))

                    result = run_make(repo, "test")

                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"make test accepted call-count-dependent production with threshold {threshold}",
                )

    def test_process_environment_test_awareness_is_rejected(self):
        with copied_repo() as repo:
            write_selection(repo, TEST_AWARE_SELECTION)

            result = run_make(repo, "test")

        self.assertNotEqual(
            result.returncode,
            0,
            "make test accepted production that branches on process environment",
        )

    def test_python_and_xcodebuild_make_overrides_cannot_hide_static_failures(self):
        with copied_repo() as repo:
            (repo / "README.md").write_text("truncated\n", encoding="utf-8")

            result = run_make(repo, "lint", "PYTHON=/usr/bin/true")

        self.assertNotEqual(
            result.returncode,
            0,
            "make lint accepted caller PYTHON override that skipped real checks",
        )

    @unittest.skipUnless(os.uname().sysname == "Darwin", "xcodebuild trust checks are Darwin-only")
    def test_xcodebuild_override_cannot_hide_missing_project(self):
        with copied_repo() as repo:
            shutil.rmtree(repo / "background_switcher" / "background_switcher.xcodeproj")

            result = run_make(repo, "native-test", "XCODEBUILD=/usr/bin/true")

        self.assertNotEqual(
            result.returncode,
            0,
            "make native-test accepted caller XCODEBUILD override for a missing project",
        )

    def test_path_python_wrapper_cannot_hide_static_failures(self):
        with copied_repo() as repo:
            (repo / "README.md").write_text("truncated\n", encoding="utf-8")
            with tempfile.TemporaryDirectory(prefix="swift-sample-path-probe.") as probe_dir:
                probe = Path(probe_dir)
                fake_python = probe / "python3"
                fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                fake_python.chmod(0o755)

                env = os.environ.copy()
                env["PATH"] = f"{probe}:{env.get('PATH', '')}"
                result = run_make(repo, "lint", env=env)

        self.assertNotEqual(
            result.returncode,
            0,
            "make lint accepted a PATH-front python3 wrapper that skipped real checks",
        )

    def test_python_symlink_override_cannot_hide_static_failures(self):
        with copied_repo() as repo:
            (repo / "README.md").write_text("truncated\n", encoding="utf-8")
            with tempfile.TemporaryDirectory(prefix="swift-sample-symlink-probe.") as probe_dir:
                fake_python = Path(probe_dir) / "python3"
                fake_python.symlink_to("/usr/bin/true")

                result = run_make(repo, "lint", f"PYTHON={fake_python}")

        self.assertNotEqual(
            result.returncode,
            0,
            "make lint accepted a caller PYTHON symlink to /usr/bin/true",
        )


def copied_repo():
    temp_dir = tempfile.TemporaryDirectory(prefix="swift-sample-contract.")
    destination = Path(temp_dir.name) / "repo"
    ignore = shutil.ignore_patterns(
        "__pycache__",
        ".pytest_cache",
        "DerivedData",
        "build",
    )
    shutil.copytree(ROOT, destination, ignore=ignore)

    class ManagedCopy:
        def __enter__(self):
            return destination

        def __exit__(self, exc_type, exc, tb):
            temp_dir.cleanup()

    return ManagedCopy()


def write_selection(repo, source):
    path = repo / BACKGROUND_SELECTION.relative_to(ROOT)
    path.write_text(textwrap.dedent(source), encoding="utf-8")


def run_make(repo, *args, env=None):
    completed = subprocess.run(
        ["make", *args],
        cwd=str(repo),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=240,
    )
    return completed


if __name__ == "__main__":
    unittest.main()
