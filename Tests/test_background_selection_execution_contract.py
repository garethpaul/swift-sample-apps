#!/usr/bin/env python3
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = Path("background_switcher/background_switcher/BackgroundSelection.swift")
ADAPTER = Path("Tests/BackgroundSelectionTests/main.swift")
RUNNER = Path("scripts/test-background-selection.sh")
VERIFIER = Path("scripts/verify-background-selection.py")


class BackgroundSelectionExecutionContractTests(unittest.TestCase):
    maxDiff = None

    def copy_repository(self):
        temporary_directory = tempfile.TemporaryDirectory()
        repository = Path(temporary_directory.name) / "repository"
        shutil.copytree(ROOT, repository, ignore=shutil.ignore_patterns(".git", "build", "DerivedData", "__pycache__"))
        subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
        subprocess.run(["git", "add", "."], cwd=repository, check=True)
        self.addCleanup(temporary_directory.cleanup)
        return repository

    def run_gate(self, repository, environment=None):
        env = os.environ.copy()
        env["BACKGROUND_CONTRACT_MUTATION"] = "1"
        if environment:
            env.update(environment)
        return subprocess.run(
            ["make", "test", "XCODEBUILD=true"],
            cwd=repository,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=180,
        )

    def assert_mutation_rejected(self, mutate, environment=None):
        repository = self.copy_repository()
        mutate(repository)
        result = self.run_gate(repository, environment)
        self.assertNotEqual(0, result.returncode, result.stdout)

    def replace(self, repository, relative_path, old, new):
        path = repository / relative_path
        source = path.read_text(encoding="utf-8")
        self.assertIn(old, source)
        path.write_text(source.replace(old, new, 1), encoding="utf-8")

    def test_external_harness_exists_and_passes(self):
        verifier = ROOT / VERIFIER
        self.assertTrue(verifier.exists(), "missing harness-owned verifier")
        result = subprocess.run(
            [os.environ.get("PYTHON", "python3"), str(verifier), "--root", str(ROOT), "--seed", "8675309"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=180,
        )
        self.assertEqual(0, result.returncode, result.stdout)

    def test_runner_false_branch_is_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(
                repo,
                RUNNER,
                'exec "$PYTHON" "$ROOT_DIR/scripts/verify-background-selection.py" --root "$ROOT_DIR"',
                'if false; then\n  "$PYTHON" "$ROOT_DIR/scripts/verify-background-selection.py" --root "$ROOT_DIR"\nfi',
            )
        )

    def test_runner_early_success_is_rejected(self):
        self.assert_mutation_rejected(lambda repo: self.replace(repo, RUNNER, "set -eu", "set -eu\nexit 0"))

    def test_runner_uncalled_verifier_is_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(
                repo,
                RUNNER,
                'exec "$PYTHON" "$ROOT_DIR/scripts/verify-background-selection.py" --root "$ROOT_DIR"',
                'never_run() {\n  "$PYTHON" "$ROOT_DIR/scripts/verify-background-selection.py" --root "$ROOT_DIR"\n}',
            )
        )

    def test_runner_fake_success_is_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(
                repo,
                RUNNER,
                'exec "$PYTHON" "$ROOT_DIR/scripts/verify-background-selection.py" --root "$ROOT_DIR"',
                "printf '%s\\n' 'Background selection black-box verification passed'",
            )
        )

    def test_erased_harness_comparison_is_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(repo, VERIFIER, "actual != expected", "False")
        )

    def test_skipped_randomized_runs_are_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(repo, VERIFIER, "for sequence in sequences:", "for sequence in []:")
        )

    def test_skipped_negative_control_is_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(repo, VERIFIER, "verify_candidate(broken_binary, sequences)", "verify_candidate(real_binary, sequences)")
        )

    def test_adapter_with_no_observations_is_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(repo, ADAPTER, "for argument in arguments {", "if false {\nfor argument in arguments {")
        )

    def test_adapter_preserved_only_as_comments_is_rejected(self):
        def mutate(repository):
            path = repository / ADAPTER
            path.write_text("\n".join(f"// {line}" for line in path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")

        self.assert_mutation_rejected(mutate)

    def test_adapter_preserved_only_as_string_is_rejected(self):
        def mutate(repository):
            path = repository / ADAPTER
            source = path.read_text(encoding="utf-8")
            path.write_text('let preserved = #"""\n' + source + '\n"""#\n_ = preserved\n', encoding="utf-8")

        self.assert_mutation_rejected(mutate)

    def test_adapter_owned_mapping_is_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(
                repo,
                ADAPTER,
                "BackgroundSelection.selection(forButtonTag: tag)",
                "tag == 1 ? .first : tag == 2 ? .second : nil",
            )
        )

    def test_fixed_order_stateful_production_is_rejected(self):
        def mutate(repository):
            self.replace(
                repository,
                PRODUCTION,
                "enum BackgroundSelection: Int, CaseIterable {",
                "enum BackgroundSelection: Int, CaseIterable {\n    private static var callIndex = 0",
            )
            self.replace(
                repository,
                PRODUCTION,
                "    static func selection(forButtonTag tag: Int) -> BackgroundSelection? {\n        return BackgroundSelection(rawValue: tag)\n    }",
                """    static func selection(forButtonTag tag: Int) -> BackgroundSelection? {
        let values: [BackgroundSelection?] = [.first, .second, nil, nil, nil, nil, nil, nil]
        defer { callIndex += 1 }
        return values[callIndex % values.count]
    }""",
            )

        self.assert_mutation_rejected(mutate)

    def test_stateful_production_failing_on_seventeenth_valid_call_is_rejected(self):
        def mutate(repository):
            self.replace(
                repository,
                PRODUCTION,
                "    case second = 2",
                """    case second = 2
    private static var observedInitializations = 0

    init?(rawValue: Int) {
        guard BackgroundSelection.observedInitializations < 16 else {
            return nil
        }
        BackgroundSelection.observedInitializations += 1
        switch rawValue {
        case 1:
            self = .first
        case 2:
            self = .second
        default:
            return nil
        }
    }""",
            )

        self.assert_mutation_rejected(mutate)

    def test_test_aware_production_is_rejected(self):
        def mutate(repository):
            self.replace(repository, PRODUCTION, "enum BackgroundSelection", "import Foundation\n\nenum BackgroundSelection")
            self.replace(
                repository,
                PRODUCTION,
                "        return BackgroundSelection(rawValue: tag)",
                "        guard CommandLine.arguments.count > 1 else { return nil }\n        return BackgroundSelection(rawValue: tag)",
            )

        self.assert_mutation_rejected(mutate)

    def test_production_output_forgery_is_rejected(self):
        def mutate(repository):
            self.replace(
                repository,
                PRODUCTION,
                "        return BackgroundSelection(rawValue: tag)",
                '        print(tag == 1 ? "selection:1:Background1:Background 1" : "none")\n        return nil',
            )

        self.assert_mutation_rejected(mutate)

    def test_wrong_production_mapping_is_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(
                repo,
                PRODUCTION,
                "        return BackgroundSelection(rawValue: tag)",
                "        return tag == 2 ? .first : BackgroundSelection(rawValue: tag)",
            )
        )

    def test_forged_harness_output_is_rejected(self):
        self.assert_mutation_rejected(
            lambda repo: self.replace(repo, VERIFIER, "actual = result.stdout.splitlines()", "actual = expected")
        )

    def test_make_recipe_override_is_rejected(self):
        def mutate(repository):
            makefile = repository / "Makefile"
            makefile.write_text(makefile.read_text(encoding="utf-8") + "\ntest:\n\t@true\n", encoding="utf-8")

        self.assert_mutation_rejected(mutate)

    def test_caller_controlled_python_override_fails_closed(self):
        repository = self.copy_repository()
        self.replace(
            repository,
            PRODUCTION,
            "        return BackgroundSelection(rawValue: tag)",
            "        return nil",
        )
        result = subprocess.run(
            ["make", "test", "PYTHON=/usr/bin/true", "XCODEBUILD=/usr/bin/true"],
            cwd=repository,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=180,
        )
        self.assertNotEqual(0, result.returncode, result.stdout)

    def test_caller_controlled_xcodebuild_override_fails_closed(self):
        repository = self.copy_repository()
        project = repository / "background_switcher/background_switcher.xcodeproj"
        project.rename(project.with_suffix(".xcodeproj.disabled"))
        result = subprocess.run(
            ["make", "native-test", "XCODEBUILD=/usr/bin/true"],
            cwd=repository,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=180,
        )
        self.assertNotEqual(0, result.returncode, result.stdout)

    def test_caller_controlled_path_compiler_is_rejected(self):
        repository = self.copy_repository()
        tools = repository / "fake-tools"
        tools.mkdir()
        wrapper = tools / "swiftc"
        wrapper.write_text(
            "#!/usr/bin/env sh\nprintf '%s\\n' 'forged compiler executed' >&2\nexit 0\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        environment = os.environ.copy()
        environment["PATH"] = f"{tools}:{environment['PATH']}"
        result = self.run_gate(repository, environment)
        self.assertEqual(0, result.returncode, result.stdout)
        self.assertNotIn("forged compiler executed", result.stdout)

    def test_caller_controlled_swiftc_override_is_ignored(self):
        repository = self.copy_repository()
        wrapper = repository / "fake-swiftc"
        wrapper.write_text("#!/usr/bin/env sh\nexit 99\n", encoding="utf-8")
        wrapper.chmod(0o755)
        result = self.run_gate(repository, {"SWIFTC": str(wrapper)})
        self.assertEqual(0, result.returncode, result.stdout)


if __name__ == "__main__":
    unittest.main()
