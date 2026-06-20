import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRUSTED = ROOT / "trusted-verifier"
WORKFLOW = ROOT / ".github" / "workflows" / "trusted-swift-sample-gate.yml"
TARGETS = (
    "background_switcher/background_switcher/BackgroundSelection.swift",
    "background_switcher/background_switcher/ViewController.swift",
    "background_switcher/background_switcherTests/background_switcherTests.swift",
)


def load_environment_verifier():
    path = TRUSTED / "verify_environment.py"
    spec = importlib.util.spec_from_file_location("trusted_environment_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(command, cwd=None, environment=None):
    return subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def git(repository, *arguments):
    result = run(["/usr/bin/git", *arguments], repository)
    if result.returncode != 0:
        raise AssertionError(result.stdout)
    return result.stdout.strip()


class TrustedBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = Path(tempfile.mkdtemp(prefix="swift-trusted-bootstrap-test-"))
        self.base = self.temporary / "base"
        self.candidate = self.temporary / "candidate"
        self.receipt = self.temporary / "receipt.json"

    def tearDown(self):
        shutil.rmtree(self.temporary, ignore_errors=True)

    def make_repository(self):
        self.base.mkdir()
        git(self.base, "init", "--quiet", "--initial-branch=master")
        git(self.base, "config", "user.name", "Trusted Bootstrap Test")
        git(self.base, "config", "user.email", "trusted-bootstrap@example.invalid")

        seed = self.base / "trusted-seed.txt"
        seed.write_text("trusted seed\n", encoding="utf-8")
        git(self.base, "add", ".")
        git(self.base, "commit", "--quiet", "-m", "test: trusted seed")
        rejected = []
        for index in range(14):
            rejected.append(self.commit_rejected_sibling(self.base, index))
        git(self.base, "checkout", "--quiet", "master")

        shutil.copytree(TRUSTED, self.base / "trusted-verifier", ignore=shutil.ignore_patterns("__pycache__"))
        workflow_destination = self.base / ".github" / "workflows" / WORKFLOW.name
        workflow_destination.parent.mkdir(parents=True)
        shutil.copy2(WORKFLOW, workflow_destination)
        self.write_policy_rejections(self.base, rejected)
        for target in TARGETS:
            destination = self.base / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("pre-bootstrap semantic bytes\n", encoding="utf-8")
        git(self.base, "add", ".")
        git(self.base, "commit", "--quiet", "-m", "test: trusted bootstrap base")
        base_sha = git(self.base, "rev-parse", "HEAD")

        clone = run(
            [
                "/usr/bin/git",
                "clone",
                "--quiet",
                "--single-branch",
                "--no-tags",
                self.base.resolve().as_uri(),
                self.candidate,
            ]
        )
        self.assertEqual(clone.returncode, 0, clone.stdout)
        git(self.candidate, "config", "user.name", "Semantic Candidate Test")
        git(self.candidate, "config", "user.email", "semantic-candidate@example.invalid")
        policy = json.loads((TRUSTED / "policy.json").read_text(encoding="utf-8"))
        for target in TARGETS:
            expected = TRUSTED / policy["expected_files"][target]["template"]
            destination = self.candidate / target
            destination.write_bytes(expected.read_bytes())
        git(self.candidate, "add", ".")
        git(self.candidate, "commit", "--quiet", "-m", "fix: apply reviewed semantic bytes")
        self.trusted_fetch_url = self.base.resolve().as_uri()
        self.candidate_fetch_url = self.candidate.resolve().as_uri()
        return base_sha, git(self.candidate, "rev-parse", "HEAD")

    def commit_rejected_sibling(self, repository, index):
        git(repository, "checkout", "--quiet", "--orphan", f"rejected-{index}")
        git(repository, "rm", "-r", "--force", "--quiet", "--ignore-unmatch", ".")
        marker = repository / f"rejected-{index}.txt"
        marker.write_text(f"rejected sibling {index}\n", encoding="utf-8")
        git(repository, "add", ".")
        git(repository, "commit", "--quiet", "-m", f"test: rejected sibling {index}")
        return git(repository, "rev-parse", "HEAD")

    def write_policy_rejections(self, repository, rejected):
        policy_path = repository / "trusted-verifier" / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["rejected_bootstrap_ancestors"] = rejected
        policy_path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def make_shallow_rejected_ancestor_repository(self):
        self.base.mkdir()
        git(self.base, "init", "--quiet", "--initial-branch=master")
        git(self.base, "config", "user.name", "Trusted Bootstrap Test")
        git(self.base, "config", "user.email", "trusted-bootstrap@example.invalid")

        root_marker = self.base / "rejected-root.txt"
        root_marker.write_text("rejected root\n", encoding="utf-8")
        git(self.base, "add", ".")
        git(self.base, "commit", "--quiet", "-m", "test: rejected root")
        rejected_root = git(self.base, "rev-parse", "HEAD")
        rejected = [rejected_root]
        for index in range(1, 13):
            rejected.append(self.commit_rejected_sibling(self.base, index))
        git(self.base, "checkout", "--quiet", "master")

        shutil.copytree(TRUSTED, self.base / "trusted-verifier", ignore=shutil.ignore_patterns("__pycache__"))
        workflow_destination = self.base / ".github" / "workflows" / WORKFLOW.name
        workflow_destination.parent.mkdir(parents=True)
        shutil.copy2(WORKFLOW, workflow_destination)
        self.write_policy_rejections(self.base, rejected)
        for target in TARGETS:
            destination = self.base / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("pre-bootstrap semantic bytes\n", encoding="utf-8")
        git(self.base, "add", ".")
        git(self.base, "commit", "--quiet", "-m", "test: trusted bootstrap base")
        base_sha = git(self.base, "rev-parse", "HEAD")

        source = self.temporary / "source"
        clone = run(["/usr/bin/git", "clone", "--quiet", "--no-hardlinks", self.base, source])
        self.assertEqual(clone.returncode, 0, clone.stdout)
        git(source, "config", "user.name", "Semantic Candidate Test")
        git(source, "config", "user.email", "semantic-candidate@example.invalid")
        policy = json.loads((self.base / "trusted-verifier" / "policy.json").read_text(encoding="utf-8"))
        for target in TARGETS:
            expected = self.base / "trusted-verifier" / policy["expected_files"][target]["template"]
            destination = source / target
            destination.write_bytes(expected.read_bytes())
        git(source, "add", ".")
        git(source, "commit", "--quiet", "-m", "fix: apply reviewed semantic bytes")
        head_sha = git(source, "rev-parse", "HEAD")

        shallow = run(
            [
                "/usr/bin/git",
                "clone",
                "--quiet",
                "--depth",
                "2",
                source.resolve().as_uri(),
                self.candidate,
            ]
        )
        self.assertEqual(shallow.returncode, 0, shallow.stdout)
        self.assertEqual(git(self.candidate, "rev-parse", "HEAD"), head_sha)
        self.assertEqual(git(self.candidate, "rev-list", "--count", "--all"), "2")
        missing = run(["/usr/bin/git", "cat-file", "-e", f"{rejected_root}^{{commit}}"], self.candidate)
        self.assertNotEqual(missing.returncode, 0, missing.stdout)
        self.trusted_fetch_url = self.base.resolve().as_uri()
        self.candidate_fetch_url = source.resolve().as_uri()
        return base_sha, head_sha

    def make_missing_rejected_object_repository(self):
        self.base.mkdir()
        git(self.base, "init", "--quiet", "--initial-branch=master")
        git(self.base, "config", "user.name", "Trusted Bootstrap Test")
        git(self.base, "config", "user.email", "trusted-bootstrap@example.invalid")

        shutil.copytree(TRUSTED, self.base / "trusted-verifier", ignore=shutil.ignore_patterns("__pycache__"))
        workflow_destination = self.base / ".github" / "workflows" / WORKFLOW.name
        workflow_destination.parent.mkdir(parents=True)
        shutil.copy2(WORKFLOW, workflow_destination)
        self.write_policy_rejections(self.base, ["f" * 40])
        for target in TARGETS:
            destination = self.base / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("pre-bootstrap semantic bytes\n", encoding="utf-8")
        git(self.base, "add", ".")
        git(self.base, "commit", "--quiet", "-m", "test: trusted bootstrap base")
        base_sha = git(self.base, "rev-parse", "HEAD")

        clone = run(["/usr/bin/git", "clone", "--quiet", "--no-hardlinks", self.base, self.candidate])
        self.assertEqual(clone.returncode, 0, clone.stdout)
        git(self.candidate, "config", "user.name", "Semantic Candidate Test")
        git(self.candidate, "config", "user.email", "semantic-candidate@example.invalid")
        policy = json.loads((self.base / "trusted-verifier" / "policy.json").read_text(encoding="utf-8"))
        for target in TARGETS:
            expected = self.base / "trusted-verifier" / policy["expected_files"][target]["template"]
            destination = self.candidate / target
            destination.write_bytes(expected.read_bytes())
        git(self.candidate, "add", ".")
        git(self.candidate, "commit", "--quiet", "-m", "fix: apply reviewed semantic bytes")
        self.trusted_fetch_url = self.base.resolve().as_uri()
        self.candidate_fetch_url = self.candidate.resolve().as_uri()
        return base_sha, git(self.candidate, "rev-parse", "HEAD")

    def verify(
        self,
        base_sha,
        head_sha,
        environment=None,
        allow_local_fetch=True,
        trusted_fetch_url=None,
        candidate_fetch_url=None,
        trusted_repository_slug="garethpaul/swift-sample-apps",
        candidate_repository_slug="garethpaul/swift-sample-apps",
    ):
        command = [
            self.base / "trusted-verifier" / "run-hermetic.sh",
            "--base-repository",
            self.base,
            "--candidate-repository",
            self.candidate,
            "--base-sha",
            base_sha,
            "--head-sha",
            head_sha,
            "--trusted-fetch-url",
            trusted_fetch_url or getattr(self, "trusted_fetch_url", self.base.resolve().as_uri()),
            "--candidate-fetch-url",
            candidate_fetch_url or getattr(self, "candidate_fetch_url", self.candidate.resolve().as_uri()),
            "--trusted-repository-slug",
            trusted_repository_slug,
            "--candidate-repository-slug",
            candidate_repository_slug,
            "--receipt",
            self.receipt,
        ]
        if allow_local_fetch:
            command.append("--allow-local-fetch")
        return run(command, environment=environment)

    def test_exact_reviewed_semantic_candidate_is_accepted(self):
        base_sha, head_sha = self.make_repository()
        result = self.verify(base_sha, head_sha)
        self.assertEqual(result.returncode, 0, result.stdout)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "passed")
        self.assertEqual(receipt["trusted_base_sha"], base_sha)
        self.assertEqual(receipt["candidate_head_sha"], head_sha)
        self.assertEqual(set(receipt["verified_files"]), set(TARGETS))

    def test_shallow_candidate_cannot_hide_rejected_ancestor(self):
        base_sha, head_sha = self.make_shallow_rejected_ancestor_repository()
        result = self.verify(base_sha, head_sha)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("rejected candidate is an ancestor", result.stdout)
        self.assertFalse(self.receipt.exists())

    def test_missing_rejected_object_fails_closed(self):
        base_sha, head_sha = self.make_missing_rejected_object_repository()
        result = self.verify(base_sha, head_sha)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("rejected candidate object is unavailable", result.stdout)
        self.assertFalse(self.receipt.exists())

    def test_local_fetch_urls_require_explicit_test_override(self):
        base_sha, head_sha = self.make_repository()
        result = self.verify(base_sha, head_sha, allow_local_fetch=False)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("trusted fetch URL must be https://github.com/garethpaul/swift-sample-apps.git", result.stdout)
        self.assertFalse(self.receipt.exists())

    def test_fetch_url_must_match_event_repository_slug(self):
        base_sha, head_sha = self.make_repository()
        result = self.verify(
            base_sha,
            head_sha,
            trusted_fetch_url="https://github.com/attacker/swift-sample-apps.git",
            candidate_fetch_url="https://github.com/garethpaul/swift-sample-apps.git",
            allow_local_fetch=False,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("trusted fetch URL must be https://github.com/garethpaul/swift-sample-apps.git", result.stdout)
        self.assertFalse(self.receipt.exists())

    def test_candidate_cannot_change_workflow_or_trust_boundary(self):
        base_sha, _ = self.make_repository()
        workflow = self.candidate / ".github" / "workflows" / "spoof.yml"
        workflow.write_text("name: spoof\n", encoding="utf-8")
        git(self.candidate, "add", ".")
        git(self.candidate, "commit", "--amend", "--quiet", "--no-edit")
        result = self.verify(base_sha, git(self.candidate, "rev-parse", "HEAD"))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("changed-file boundary differs", result.stdout)
        self.assertFalse(self.receipt.exists())

    def test_candidate_cannot_add_second_commit(self):
        base_sha, _ = self.make_repository()
        git(self.candidate, "commit", "--quiet", "--allow-empty", "-m", "test: extra commit")
        result = self.verify(base_sha, git(self.candidate, "rev-parse", "HEAD"))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("trusted base must be the candidate's sole parent", result.stdout)
        self.assertFalse(self.receipt.exists())

    def test_candidate_cannot_change_reviewed_file_mode(self):
        base_sha, _ = self.make_repository()
        git(self.candidate, "update-index", "--chmod=+x", "--", TARGETS[0])
        git(self.candidate, "commit", "--amend", "--quiet", "--no-edit")
        result = self.verify(base_sha, git(self.candidate, "rev-parse", "HEAD"))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("candidate mode differs from reviewed mode", result.stdout)
        self.assertFalse(self.receipt.exists())

    def test_candidate_cannot_replace_reviewed_file_with_symlink(self):
        base_sha, _ = self.make_repository()
        target = self.candidate / TARGETS[0]
        target.unlink()
        target.symlink_to("outside.swift")
        git(self.candidate, "add", "-A", "--", TARGETS[0])
        git(self.candidate, "commit", "--amend", "--quiet", "--no-edit")
        result = self.verify(base_sha, git(self.candidate, "rev-parse", "HEAD"))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("candidate mode differs from reviewed mode", result.stdout)
        self.assertFalse(self.receipt.exists())

    def test_wrong_semantic_bytes_are_rejected(self):
        base_sha, head_sha = self.make_repository()
        source = self.candidate / TARGETS[0]
        source.write_text(source.read_text(encoding="utf-8").replace("Background1", "Background2", 1), encoding="utf-8")
        git(self.candidate, "add", ".")
        git(self.candidate, "commit", "--amend", "--quiet", "--no-edit")
        result = self.verify(base_sha, git(self.candidate, "rev-parse", "HEAD"))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("reviewed bytes differ", result.stdout)
        self.assertFalse(self.receipt.exists())
        self.assertNotEqual(head_sha, git(self.candidate, "rev-parse", "HEAD"))

    def test_python_startup_and_coverage_injection_are_ignored(self):
        base_sha, head_sha = self.make_repository()
        injection = self.temporary / "injection"
        injection.mkdir()
        site_marker = self.temporary / "sitecustomize-ran"
        user_marker = self.temporary / "usercustomize-ran"
        coverage_marker = self.temporary / "coverage-ran"
        startup_marker = self.temporary / "startup-ran"
        (injection / "sitecustomize.py").write_text(
            "import coverage\ncoverage.process_startup()\n"
            f"from pathlib import Path\nPath({str(site_marker)!r}).write_text('ran')\n",
            encoding="utf-8",
        )
        (injection / "usercustomize.py").write_text(
            f"from pathlib import Path\nPath({str(user_marker)!r}).write_text('ran')\n",
            encoding="utf-8",
        )
        (injection / "coverage.py").write_text(
            f"from pathlib import Path\nPath({str(coverage_marker)!r}).write_text('ran')\n"
            "def process_startup():\n    return None\n",
            encoding="utf-8",
        )
        startup = injection / "startup.py"
        startup.write_text(
            f"from pathlib import Path\nPath({str(startup_marker)!r}).write_text('ran')\n",
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONPATH": str(injection),
                "PYTHONHOME": str(injection),
                "PYTHONUSERBASE": str(injection),
                "PYTHONSTARTUP": str(startup),
                "PYTHONINSPECT": "1",
                "COVERAGE_PROCESS_START": str(injection / ".coveragerc"),
                "COVERAGE_RCFILE": str(injection / ".coveragerc"),
                "BASH_ENV": str(startup),
                "ENV": str(startup),
            }
        )
        result = self.verify(base_sha, head_sha, environment=environment)
        self.assertEqual(result.returncode, 0, result.stdout)
        for marker in (site_marker, user_marker, coverage_marker, startup_marker):
            self.assertFalse(marker.exists(), result.stdout)

    def test_modified_trusted_checkout_is_rejected(self):
        base_sha, head_sha = self.make_repository()
        policy = self.base / "trusted-verifier" / "policy.json"
        policy.write_text(policy.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        result = self.verify(base_sha, head_sha)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("trusted checkout bytes differ", result.stdout)
        self.assertFalse(self.receipt.exists())

    def test_direct_nonisolated_python_launch_is_rejected(self):
        base_sha, head_sha = self.make_repository()
        result = run(
            [
                "/usr/bin/python3",
                self.base / "trusted-verifier" / "verify_candidate.py",
                "--base-repository",
                self.base,
                "--candidate-repository",
                self.candidate,
                "--base-sha",
                base_sha,
                "--head-sha",
                head_sha,
                "--trusted-fetch-url",
                self.trusted_fetch_url,
                "--candidate-fetch-url",
                self.candidate_fetch_url,
                "--trusted-repository-slug",
                "garethpaul/swift-sample-apps",
                "--candidate-repository-slug",
                "garethpaul/swift-sample-apps",
                "--allow-local-fetch",
                "--receipt",
                self.receipt,
            ]
        )
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("isolated Python", result.stdout)

    def test_workflow_is_base_owned_fork_safe_and_nonexecuting(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        required = (
            "pull_request_target:",
            "permissions:\n  contents: read",
            "environment:\n      name: swift-sample-trusted-verifier-v1",
            "ref: ${{ github.workflow_sha }}",
            "repository: ${{ github.event.pull_request.head.repo.full_name }}",
            "ref: ${{ github.event.pull_request.head.sha }}",
            "persist-credentials: false",
            "trusted-verifier/run-hermetic.sh",
            "trusted-verifier/verify_environment.py",
            "TRUSTED_FETCH_URL: https://github.com/${{ github.event.repository.full_name }}.git",
            "CANDIDATE_FETCH_URL: https://github.com/${{ github.event.pull_request.head.repo.full_name }}.git",
            "--trusted-fetch-url \"$TRUSTED_FETCH_URL\"",
            "--candidate-fetch-url \"$CANDIDATE_FETCH_URL\"",
            "--trusted-repository-slug \"$TRUSTED_REPOSITORY_SLUG\"",
            "--candidate-repository-slug \"$CANDIDATE_REPOSITORY_SLUG\"",
        )
        for contract in required:
            self.assertIn(contract, text)
        for forbidden in ("secrets.", "pull-requests: write", "contents: write", "actions/cache", "candidate/Makefile"):
            self.assertNotIn(forbidden, text)
        self.assertNotRegex(text, r"(?m)^\s*run:\s*.*candidate")
        self.assertLess(text.index("Verify protected environment policy"), text.index("Check out candidate as untrusted data"))

    def test_environment_preflight_accepts_official_response_metadata(self):
        verifier = load_environment_verifier()
        environment = {
            "id": 1618870684,
            "node_id": "EN_kwDOExample7g",
            "name": "swift-sample-trusted-verifier-v1",
            "url": "https://api.github.com/repos/garethpaul/swift-sample-apps/environments/swift-sample-trusted-verifier-v1",
            "html_url": "https://github.com/garethpaul/swift-sample-apps/deployments/activity_log?environments_filter=swift-sample-trusted-verifier-v1",
            "created_at": "2026-06-20T10:00:00Z",
            "updated_at": "2026-06-20T10:00:00Z",
            "can_admins_bypass": True,
            "protection_rules": [],
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True,
                "provider_extension": "ignored",
            },
        }
        policies = {
            "total_count": 1,
            "branch_policies": [
                {
                    "id": 21923765,
                    "node_id": "DBP_kwDOExample4Q",
                    "name": "master",
                    "type": "branch",
                }
            ],
        }
        verifier.validate_environment(environment, policies, "swift-sample-trusted-verifier-v1")

    def test_environment_preflight_accepts_live_format_response(self):
        verifier = load_environment_verifier()
        environment = {
            "id": 1,
            "node_id": "EN_live",
            "name": "swift-sample-trusted-verifier-v1",
            "url": "https://api.github.com/repos/garethpaul/swift-sample-apps/environments/swift-sample-trusted-verifier-v1",
            "html_url": "https://github.com/garethpaul/swift-sample-apps/deployments/activity_log?environments_filter=swift-sample-trusted-verifier-v1",
            "created_at": "2026-06-20T10:00:00Z",
            "updated_at": "2026-06-20T10:01:00Z",
            "can_admins_bypass": False,
            "protection_rules": [
                {
                    "id": 2,
                    "node_id": "GA_live",
                    "type": "branch_policy",
                }
            ],
            "deployment_branch_policy": {
                "protected_branches": False,
                "custom_branch_policies": True,
            },
        }
        policies = {
            "total_count": 1,
            "branch_policies": [
                {
                    "id": 3,
                    "node_id": "DBP_live",
                    "name": "master",
                    "type": "branch",
                }
            ],
        }
        verifier.validate_environment(environment, policies, "swift-sample-trusted-verifier-v1")

    def test_required_check_source_rejects_app_id_mismatch(self):
        verifier = load_environment_verifier()
        self.assertTrue(
            hasattr(verifier, "validate_required_check_source"),
            "environment verifier must validate required-check GitHub App source binding",
        )
        source = {
            "context": "trusted-swift-sample/bootstrap-v1",
            "app_id": 15368,
        }
        with self.assertRaisesRegex(verifier.EnvironmentError, "GitHub App source"):
            verifier.validate_required_check_source(
                source,
                "trusted-swift-sample/bootstrap-v1",
                98765,
            )

    def test_environment_preflight_rejects_missing_or_unsafe_semantics(self):
        verifier = load_environment_verifier()

        def valid_payloads():
            return (
                {
                    "name": "swift-sample-trusted-verifier-v1",
                    "deployment_branch_policy": {
                        "protected_branches": False,
                        "custom_branch_policies": True,
                    },
                },
                {
                    "total_count": 1,
                    "branch_policies": [
                        {
                            "id": 3,
                            "node_id": "DBP_live",
                            "name": "master",
                            "type": "branch",
                        }
                    ],
                },
            )

        cases = {
            "missing environment name": lambda environment, policies: environment.pop("name"),
            "wrong environment name": lambda environment, policies: environment.update(name="production"),
            "missing deployment policy": lambda environment, policies: environment.pop("deployment_branch_policy"),
            "deployment policy is not an object": lambda environment, policies: environment.update(
                deployment_branch_policy=[]
            ),
            "protected branches enabled": lambda environment, policies: environment[
                "deployment_branch_policy"
            ].update(protected_branches=True),
            "protected branches wrong type": lambda environment, policies: environment[
                "deployment_branch_policy"
            ].update(protected_branches=0),
            "custom policies disabled": lambda environment, policies: environment[
                "deployment_branch_policy"
            ].update(custom_branch_policies=False),
            "custom policies wrong type": lambda environment, policies: environment[
                "deployment_branch_policy"
            ].update(custom_branch_policies=1),
            "missing total count": lambda environment, policies: policies.pop("total_count"),
            "total count wrong type": lambda environment, policies: policies.update(total_count=True),
            "wrong total count": lambda environment, policies: policies.update(total_count=2),
            "missing branch policy list": lambda environment, policies: policies.pop("branch_policies"),
            "branch policies not a list": lambda environment, policies: policies.update(branch_policies={}),
            "empty branch policy list": lambda environment, policies: policies.update(branch_policies=[]),
            "extra branch policy": lambda environment, policies: policies["branch_policies"].append(
                {"name": "release/*", "type": "branch"}
            ),
            "branch policy not an object": lambda environment, policies: policies.update(branch_policies=["master"]),
            "wildcard branch": lambda environment, policies: policies["branch_policies"][0].update(name="*"),
            "branch name wrong type": lambda environment, policies: policies["branch_policies"][0].update(name=1),
            "tag policy": lambda environment, policies: policies["branch_policies"][0].update(type="tag"),
            "policy type wrong type": lambda environment, policies: policies["branch_policies"][0].update(type=None),
        }

        for name, mutate in cases.items():
            with self.subTest(name=name):
                environment, policies = valid_payloads()
                mutate(environment, policies)
                with self.assertRaises(verifier.EnvironmentError):
                    verifier.validate_environment(environment, policies, "swift-sample-trusted-verifier-v1")

    def test_portable_workflow_runs_bootstrap_unit_suite(self):
        text = (ROOT / ".github" / "workflows" / "check.yml").read_text(encoding="utf-8")
        self.assertIn("Run trusted bootstrap unit tests", text)
        self.assertIn(
            "/usr/bin/python3 -I -S -B -m unittest discover -s trusted-verifier/tests -p 'test_*.py' -v",
            text,
        )

    def test_policy_uses_protected_deployment_not_spoofable_context(self):
        policy = json.loads((TRUSTED / "policy.json").read_text(encoding="utf-8"))
        authority = policy["merge_authority"]
        self.assertEqual(authority["kind"], "required_protected_environment_deployment")
        self.assertEqual(authority["environment"], "swift-sample-trusted-verifier-v1")
        self.assertFalse(authority["diagnostic_check_context_is_authoritative"])
        self.assertEqual(set(policy["expected_files"]), set(TARGETS))
        for target, contract in policy["expected_files"].items():
            template = TRUSTED / contract["template"]
            self.assertEqual(hashlib.sha256(template.read_bytes()).hexdigest(), contract["sha256"], target)

    def test_policy_rejects_prior_v13_bootstrap(self):
        policy = json.loads((TRUSTED / "policy.json").read_text(encoding="utf-8"))
        self.assertIn(
            "51d69a25cd3903681bdabd19893f5bf596f20da2",
            policy["rejected_bootstrap_ancestors"],
        )

    def test_policy_rejects_prior_v14_bootstrap(self):
        policy = json.loads((TRUSTED / "policy.json").read_text(encoding="utf-8"))
        self.assertIn(
            "43e03891a22b79a3f497ab12555fd3016cec9138",
            policy["rejected_bootstrap_ancestors"],
        )
        self.assertEqual(len(policy["rejected_bootstrap_ancestors"]), 14)

    def test_existing_hygiene_accepts_exact_bootstrap_workflow(self):
        result = run(
            [
                "/usr/bin/python3",
                "-I",
                "-S",
                "-B",
                ROOT / "scripts" / "check-swift-samples.py",
                "--mode",
                "hygiene",
            ],
            ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_hygiene_accepts_exact_future_semantic_templates(self):
        repository = self.temporary / "future-semantic"
        clone = run(["/usr/bin/git", "clone", "--quiet", "--no-hardlinks", ROOT, repository])
        self.assertEqual(clone.returncode, 0, clone.stdout)
        shutil.copy2(ROOT / "scripts" / "check-swift-samples.py", repository / "scripts" / "check-swift-samples.py")
        policy = json.loads((TRUSTED / "policy.json").read_text(encoding="utf-8"))
        for target, contract in policy["expected_files"].items():
            destination = repository / target
            destination.write_bytes((TRUSTED / contract["template"]).read_bytes())
        result = run(
            [
                "/usr/bin/python3",
                "-I",
                "-S",
                "-B",
                repository / "scripts" / "check-swift-samples.py",
                "--mode",
                "hygiene",
            ],
            repository,
        )
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
