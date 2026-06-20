#!/usr/bin/env python3
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V11TrustContractTests(unittest.TestCase):
    def test_workflow_checks_exact_head_with_parent_object(self):
        workflow = (ROOT / ".github/workflows/check.yml").read_text(encoding="utf-8")
        self.assertEqual(workflow.count("ref: ${{ github.event.pull_request.head.sha || github.sha }}"), 2)
        self.assertEqual(workflow.count("fetch-depth: 2"), 2)

    def test_every_xcode_target_requires_completed_preflight(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        for target in (
            "native-test",
            "native-test-release",
            "build",
            "build-debug",
            "build-release",
            "analyze-debug",
            "analyze-release",
        ):
            self.assertRegex(makefile, rf"(?m)^{target}: preflight$")
        self.assertIn("$(PREFLIGHT_RECEIPT)", makefile)

    def test_parent_derived_behavior_oracle_accepts_pristine_candidate(self):
        result = subprocess.run(
            ["python3", str(ROOT / "scripts/verify-trusted-candidate.py"), "--mode", "behavior"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("parent-derived behavior oracle passed", result.stdout)

    def test_contract_runner_does_not_count_assertion_calls(self):
        runner = (ROOT / "scripts/run-contract-tests.py").read_text(encoding="utf-8")
        self.assertNotIn("EXPECTED_ASSERTION_COUNTS", runner)
        self.assertNotIn("assertNotEqual =", runner)
        self.assertIn("TRUSTED_MUTATIONS", runner)


if __name__ == "__main__":
    unittest.main(verbosity=2)
