#!/usr/bin/python3
import ast
import hashlib
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = ROOT / "Tests/test_background_selection_execution_contract.py"
VERIFIER = ROOT / "scripts/verify-trusted-candidate.py"
EXPECTED_TEST_IDS = (
    'BackgroundSelectionExecutionContractTests.test_contract_runner_rejects_class_level_skip_laundering',
    'BackgroundSelectionExecutionContractTests.test_contract_runner_rejects_exact_name_noop_suite_after_digest_rotation',
    'BackgroundSelectionExecutionContractTests.test_contract_runner_rejects_missing_identity_skips_and_expected_failures',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_application_overload_in_alternate_project_source',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_application_overload_in_extension',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_conditional_compilation_argv_and_self_assignment',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_global_counter_helper_route',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_window_shape_accessors_observers_and_modifiers',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_background_dict_computed_wrong_map_bypass',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_canonical_comment_evil_file_ref_bypass',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_compiled_view_controller_class_actor_lazy_and_property_wrapper_state',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_computed_subscript_background_lookup_even_with_canonical_text_present',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_delayed_uikit_backed_mapping_corruption',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_escaped_static_var_state_in_mapping',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_every_executable_xcode_graph_route',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_exact_internal_hidden_flip_internal_func_threshold_bypass',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_exact_property_shape_drift_for_mutability_type_initializer_and_modifiers',
    'BackgroundSelectionExecutionContractTests.test_lint_requires_automatic_xcode_generated_swift_sources_disabled',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_modifier_permutation_state_in_compiled_source',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_multiline_attributes_backticks_wrappers_lazy_keypath_and_subscript_variants',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_multiline_modifier_prefix_on_canonical_property_declaration',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_nested_static_closure_counter_in_background_selection',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_observers_and_accessors_on_every_approved_view_controller_property',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_path_escape_duplicate_generated_and_build_setting_sources',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_selected_background_didset_side_effect',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_uikit_conditional_button_tag_rewrite_before_canonical_mapping',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_unsupported_accessor_syntax_in_background_selection_properties',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_xcode_compiled_allcases_extension_counter_bypass',
    'BackgroundSelectionExecutionContractTests.test_lint_rejects_xcode_compiled_selection_overload_and_global_state',
    'BackgroundSelectionExecutionContractTests.test_make_test_ignores_hostile_make_tool_variables_and_symlinks',
    'BackgroundSelectionExecutionContractTests.test_make_test_rejects_path_front_forged_shell_and_tools',
    'BackgroundSelectionExecutionContractTests.test_runner_direct_invocation_rejects_path_front_forged_sh',
)


def normalized_test_id(test):
    return ".".join(test.id().split(".")[-2:])


def flatten_tests(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten_tests(test)
        else:
            yield test


class ExactResult(unittest.TextTestResult):
    def __init__(self, *arguments, **keywords):
        super().__init__(*arguments, **keywords)
        self.started = []
        self.succeeded = []

    def startTest(self, test):
        self.started.append(normalized_test_id(test))
        super().startTest(test)

    def addSuccess(self, test):
        self.succeeded.append(normalized_test_id(test))
        super().addSuccess(test)


def verify_suite_semantics(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "BackgroundSelectionExecutionContractTests"]
    if len(classes) != 1:
        raise RuntimeError("missing exact contract mutation test class")
    methods = {node.name: node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
    expected_names = {identity.rsplit(".", 1)[1] for identity in EXPECTED_TEST_IDS}
    if set(methods) != expected_names:
        raise RuntimeError("contract mutation test identities changed")
    for name, method in methods.items():
        if method.decorator_list:
            raise RuntimeError(f"contract mutation cannot be skipped or decorated: {name}")
        names = {node.id for node in ast.walk(method) if isinstance(node, ast.Name)}
        calls = set()
        for node in ast.walk(method):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
            if isinstance(node.func, ast.Attribute) and node.func.attr.startswith("assert") and node.args and all(isinstance(argument, ast.Constant) for argument in node.args[:2]):
                raise RuntimeError(f"contract mutation contains a vacuous constant assertion: {name}")
        if "DisposableRepository" not in names or not ({"run", "assert_lint_rejects"} & calls):
            raise RuntimeError(f"contract mutation does not exercise a disposable repository: {name}")


def load_suite():
    specification = importlib.util.spec_from_file_location("contract_tests", TEST_FILE)
    if specification is None or specification.loader is None:
        raise RuntimeError("unable to load contract test module")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return unittest.defaultTestLoader.loadTestsFromTestCase(module.BackgroundSelectionExecutionContractTests)


def swap_mapping(repository):
    source = repository / "background_switcher/background_switcher/BackgroundSelection.swift"
    text = source.read_text(encoding="utf-8")
    text = text.replace('return "Background1"', 'return "__SWAP__"', 1)
    text = text.replace('return "Background2"', 'return "Background1"', 1)
    text = text.replace('return "__SWAP__"', 'return "Background2"', 1)
    source.write_text(text, encoding="utf-8")


def disable_portable_assertions(repository):
    path = repository / "Tests/BackgroundSelectionTests/main.swift"
    path.write_text(path.read_text(encoding="utf-8").replace("if actual != expected {", "if false {", 1), encoding="utf-8")


def replace_native_tests(repository):
    path = repository / "background_switcher/background_switcherTests/background_switcherTests.swift"
    path.write_text("import XCTest\nfinal class BackgroundSwitcherTests: XCTestCase { func testPlaceholder() { XCTAssertTrue(true) } }\n", encoding="utf-8")


def vacuous_contract_suite(repository):
    path = repository / "Tests/test_background_selection_execution_contract.py"
    methods = "\n".join(f"    def {identity.rsplit('.', 1)[1]}(self):\n        self.assertNotEqual(0, 1)" for identity in EXPECTED_TEST_IDS)
    path.write_text("import unittest\n\nclass BackgroundSelectionExecutionContractTests(unittest.TestCase):\n" + methods + "\n", encoding="utf-8")
    checker = repository / "scripts/check-swift-samples.py"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    text = checker.read_text(encoding="utf-8")
    text, count = re.subn(r'(CONTRACT_TEST_SOURCE:\s*")[0-9a-f]{64}("\s*,)', rf"\g<1>{digest}\g<2>", text, count=1)
    if count != 1:
        raise RuntimeError("unable to rotate mutable contract digest")
    checker.write_text(text, encoding="utf-8")


TRUSTED_MUTATIONS = (
    ("swapped production mapping", swap_mapping, "parent-derived behavior mismatch"),
    ("disabled portable assertions", disable_portable_assertions, "portable behavior assertions are disabled"),
    ("placeholder native XCTest", replace_native_tests, "vacuous constant assertion"),
    ("vacuous suite plus coordinated digest rotation", vacuous_contract_suite, "vacuous constant assertion"),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_trusted_mutations():
    protected = (TEST_FILE, VERIFIER, ROOT / "scripts/run-contract-tests.py")
    before = {path: digest(path) for path in protected}
    for name, mutate, expected in TRUSTED_MUTATIONS:
        temporary = Path(tempfile.mkdtemp(prefix="swift-v11-owned-mutation-"))
        repository = temporary / "repo"
        try:
            shutil.copytree(ROOT, repository, symlinks=True, ignore=shutil.ignore_patterns("build", "DerivedData", "__pycache__"))
            mutate(repository)
            result = subprocess.run(
                [sys.executable, str(repository / "scripts/verify-trusted-candidate.py"), "--mode", "behavior"],
                cwd=repository,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if result.returncode == 0 or expected not in result.stdout:
                raise RuntimeError(f"trusted mutation was not rejected: {name}\n{result.stdout}")
        finally:
            shutil.rmtree(temporary, ignore_errors=True)
    after = {path: digest(path) for path in protected}
    if before != after:
        raise RuntimeError("trusted mutation runner did not restore the reviewed repository")


def main():
    try:
        verify_suite_semantics(TEST_FILE)
        suite = load_suite()
    except (OSError, RuntimeError, SyntaxError) as error:
        print(f"contract suite rejected before execution: {error}", file=sys.stderr)
        return 1
    discovered = {normalized_test_id(test) for test in flatten_tests(suite)}
    expected = set(EXPECTED_TEST_IDS)
    if discovered != expected or suite.countTestCases() != len(expected):
        print("contract tests do not match the exact trusted identity set", file=sys.stderr)
        return 1
    runner = unittest.TextTestRunner(verbosity=2, resultclass=ExactResult)
    result = runner.run(suite)
    if not result.wasSuccessful() or set(result.started) != expected or set(result.succeeded) != expected or result.skipped or result.expectedFailures or result.unexpectedSuccesses:
        print("contract tests did not all execute and succeed exactly once", file=sys.stderr)
        return 1
    try:
        run_trusted_mutations()
    except (OSError, RuntimeError) as error:
        print(f"trusted mutation verification failed: {error}", file=sys.stderr)
        return 1
    print(f"Executed {len(expected)} substantive contract tests and {len(TRUSTED_MUTATIONS)} runner-owned hostile mutations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
