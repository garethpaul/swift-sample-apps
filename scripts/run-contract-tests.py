#!/usr/bin/python3
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = ROOT / "Tests" / "test_background_selection_execution_contract.py"
EXPECTED_TESTS = {
    "BackgroundSelectionExecutionContractTests.test_contract_runner_rejects_class_level_skip_laundering",
    "BackgroundSelectionExecutionContractTests.test_contract_runner_rejects_missing_identity_skips_and_expected_failures",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_application_overload_in_alternate_project_source",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_application_overload_in_extension",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_conditional_compilation_argv_and_self_assignment",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_global_counter_helper_route",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_app_delegate_window_shape_accessors_observers_and_modifiers",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_background_dict_computed_wrong_map_bypass",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_canonical_comment_evil_file_ref_bypass",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_compiled_view_controller_class_actor_lazy_and_property_wrapper_state",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_computed_subscript_background_lookup_even_with_canonical_text_present",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_delayed_uikit_backed_mapping_corruption",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_escaped_static_var_state_in_mapping",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_exact_internal_hidden_flip_internal_func_threshold_bypass",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_exact_property_shape_drift_for_mutability_type_initializer_and_modifiers",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_modifier_permutation_state_in_compiled_source",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_multiline_attributes_backticks_wrappers_lazy_keypath_and_subscript_variants",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_multiline_modifier_prefix_on_canonical_property_declaration",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_nested_static_closure_counter_in_background_selection",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_observers_and_accessors_on_every_approved_view_controller_property",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_path_escape_duplicate_generated_and_build_setting_sources",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_selected_background_didset_side_effect",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_uikit_conditional_button_tag_rewrite_before_canonical_mapping",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_unsupported_accessor_syntax_in_background_selection_properties",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_xcode_compiled_allcases_extension_counter_bypass",
    "BackgroundSelectionExecutionContractTests.test_lint_rejects_xcode_compiled_selection_overload_and_global_state",
    "BackgroundSelectionExecutionContractTests.test_make_test_ignores_hostile_make_tool_variables_and_symlinks",
    "BackgroundSelectionExecutionContractTests.test_make_test_rejects_path_front_forged_shell_and_tools",
    "BackgroundSelectionExecutionContractTests.test_runner_direct_invocation_rejects_path_front_forged_sh",
}


def normalized_test_id(test):
    return ".".join(test.id().split(".")[-2:])


def flatten_tests(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten_tests(test)
        else:
            yield test


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
    suite = load_suite()
    discovered = [normalized_test_id(test) for test in flatten_tests(suite)]
    if len(discovered) != len(set(discovered)) or set(discovered) != EXPECTED_TESTS:
        print("contract test inventory does not match the audited identities", file=sys.stderr)
        print(f"expected: {sorted(EXPECTED_TESTS)}", file=sys.stderr)
        print(f"found: {sorted(discovered)}", file=sys.stderr)
        return 1

    result = AttestedRunner(verbosity=2).run(suite)
    if (
        not result.wasSuccessful()
        or result.testsRun != len(EXPECTED_TESTS)
        or set(result.started) != EXPECTED_TESTS
        or set(result.succeeded) != EXPECTED_TESTS
        or result.skipped
        or result.expectedFailures
        or result.unexpectedSuccesses
    ):
        print("contract tests did not all execute and succeed exactly once", file=sys.stderr)
        return 1
    print(f"Attested {len(EXPECTED_TESTS)} contract tests with zero skips or expected failures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
