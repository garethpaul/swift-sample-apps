#!/usr/bin/env python3
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V12ExternalTrustContractTests(unittest.TestCase):
    def test_xcode_build_products_do_not_dirty_the_sealed_checkout(self):
        result = subprocess.run(
            ["git", "check-ignore", "background_switcher/build/v12-probe"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_authoritative_preflight_requires_external_oracle_and_manifest(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("TRUSTED_ORACLE", makefile)
        self.assertIn("TRUSTED_MANIFEST", makefile)
        self.assertIn("TRUSTED_ORACLE_SHA256", makefile)
        self.assertIn("TRUSTED_MANIFEST_SHA256", makefile)
        self.assertIn("external-trust", makefile)
        external_recipe = makefile.split("external-trust:", 1)[1].split("\nlint:", 1)[0]
        self.assertNotIn("scripts/verify-trusted-candidate.py", external_recipe)
        self.assertIn('"$(TRUSTED_ORACLE_PATH)" verify', external_recipe)
        self.assertIn('--oracle-sha256 "$(TRUSTED_ORACLE_SHA256)"', external_recipe)
        self.assertIn('--manifest-sha256 "$(TRUSTED_MANIFEST_SHA256)"', external_recipe)

    def test_candidate_local_checks_are_not_the_publication_trust_root(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertRegex(makefile, r"(?m)^candidate-check: candidate-test candidate-contract-test$")
        self.assertRegex(makefile, r"(?m)^check: external-trust candidate-check native-test build$")

    def test_hosted_jobs_require_repository_owned_external_bundle_variables(self):
        workflow = (ROOT / ".github/workflows/check.yml").read_text(encoding="utf-8")
        for variable in (
            "SWIFT_SAMPLE_V12_ORACLE_B64",
            "SWIFT_SAMPLE_V12_ORACLE_SHA256",
            "SWIFT_SAMPLE_V12_MANIFEST_B64",
            "SWIFT_SAMPLE_V12_MANIFEST_SHA256",
        ):
            self.assertIn(f"vars.{variable}", workflow)
        self.assertIn("$RUNNER_TEMP/swift-sample-v12-trust", workflow)
        self.assertNotIn("${{ runner.temp }}", workflow)

    def test_every_xcode_target_requires_external_trust(self):
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
        self.assertRegex(makefile, r"(?m)^preflight: external-trust candidate-preflight$")


if __name__ == "__main__":
    unittest.main(verbosity=2)
