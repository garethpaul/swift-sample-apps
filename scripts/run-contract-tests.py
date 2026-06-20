#!/usr/bin/python3
import importlib.util
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = ROOT / "Tests" / "test_background_selection_execution_contract.py"
EXPECTED_ASSERTION_COUNTS = (
    ("BackgroundSelectionExecutionContractTests.test_contract_runner_rejects_class_level_skip_laundering", 1),
    ("BackgroundSelectionExecutionContractTests.test_contract_runner_rejects_exact_name_noop_suite_after_digest_rotation", 1),
    ("BackgroundSelectionExecutionContractTests.test_contract_runner_rejects_missing_identity_skips_and_expected_failures", 3),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_application_overload_in_alternate_project_source", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_application_overload_in_extension", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_conditional_compilation_argv_and_self_assignment", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_global_counter_helper_route", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_window_shape_accessors_observers_and_modifiers", 4),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_background_dict_computed_wrong_map_bypass", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_canonical_comment_evil_file_ref_bypass", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_compiled_view_controller_class_actor_lazy_and_property_wrapper_state", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_computed_subscript_background_lookup_even_with_canonical_text_present", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_delayed_uikit_backed_mapping_corruption", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_escaped_static_var_state_in_mapping", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_every_executable_xcode_graph_route", 9),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_exact_internal_hidden_flip_internal_func_threshold_bypass", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_exact_property_shape_drift_for_mutability_type_initializer_and_modifiers", 7),
    ("BackgroundSelectionExecutionContractTests.test_lint_requires_automatic_xcode_generated_swift_sources_disabled", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_modifier_permutation_state_in_compiled_source", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_multiline_attributes_backticks_wrappers_lazy_keypath_and_subscript_variants", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_multiline_modifier_prefix_on_canonical_property_declaration", 4),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_nested_static_closure_counter_in_background_selection", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_observers_and_accessors_on_every_approved_view_controller_property", 6),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_path_escape_duplicate_generated_and_build_setting_sources", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_selected_background_didset_side_effect", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_uikit_conditional_button_tag_rewrite_before_canonical_mapping", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_unsupported_accessor_syntax_in_background_selection_properties", 3),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_xcode_compiled_allcases_extension_counter_bypass", 1),
    ("BackgroundSelectionExecutionContractTests.test_lint_rejects_xcode_compiled_selection_overload_and_global_state", 1),
    ("BackgroundSelectionExecutionContractTests.test_make_test_ignores_hostile_make_tool_variables_and_symlinks", 1),
    ("BackgroundSelectionExecutionContractTests.test_make_test_rejects_path_front_forged_shell_and_tools", 1),
    ("BackgroundSelectionExecutionContractTests.test_runner_direct_invocation_rejects_path_front_forged_sh", 1),
)


def normalized_test_id(test):
    return ".".join(test.id().split(".")[-2:])


def flatten_tests(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten_tests(test)
        else:
            yield test


class AssertionRecorder:
    def __init__(self, original):
        self.counts = Counter()
        self.original = original

    def __enter__(self):
        counts = self.counts
        original = self.original

        def recorded_assert_not_equal(test, first, second, message=None):
            counts[normalized_test_id(test)] += 1
            return original(test, first, second, message)

        unittest.TestCase.assertNotEqual = recorded_assert_not_equal
        return self

    def __exit__(self, exc_type, exc, traceback):
        unittest.TestCase.assertNotEqual = self.original


class AttestedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started = []
        self.succeeded = []

    def startTest(self, test):
        self.started.append(normalized_test_id(test))
        super().startTest(test)

    def addSuccess(self, test):
        self.succeeded.append(normalized_test_id(test))
        super().addSuccess(test)


class AttestedRunner(unittest.TextTestRunner):
    resultclass = AttestedResult


def load_suite():
    spec = importlib.util.spec_from_file_location("contract_tests", TEST_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {TEST_FILE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return unittest.defaultTestLoader.loadTestsFromModule(module)


def main():
    expected_assertions = dict(EXPECTED_ASSERTION_COUNTS)
    expected_tests = frozenset(expected_assertions)
    original_assert_not_equal = unittest.TestCase.assertNotEqual
    suite = load_suite()
    discovered = [normalized_test_id(test) for test in flatten_tests(suite)]
    if len(discovered) != len(set(discovered)) or set(discovered) != expected_tests:
        print("contract test inventory does not match the audited identities", file=sys.stderr)
        print(f"expected: {sorted(expected_tests)}", file=sys.stderr)
        print(f"found: {sorted(discovered)}", file=sys.stderr)
        return 1

    with AssertionRecorder(original_assert_not_equal) as assertions:
        result = AttestedRunner(verbosity=2).run(suite)
    actual_assertions = {test_id: assertions.counts[test_id] for test_id in expected_tests}
    if actual_assertions != expected_assertions:
        print("contract tests did not execute the exact runner-anchored assertion outcomes", file=sys.stderr)
        print(f"expected assertions: {expected_assertions}", file=sys.stderr)
        print(f"observed assertions: {actual_assertions}", file=sys.stderr)
        return 1
    if (
        not result.wasSuccessful()
        or result.testsRun != len(expected_tests)
        or set(result.started) != expected_tests
        or set(result.succeeded) != expected_tests
        or result.skipped
        or result.expectedFailures
        or result.unexpectedSuccesses
    ):
        print("contract tests did not all execute and succeed exactly once", file=sys.stderr)
        return 1
    print(
        f"Attested {len(expected_tests)} contract tests with exact assertion outcomes, "
        "zero skips, and zero expected failures."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
