#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SHA_PATTERN = re.compile(r"[0-9a-f]{40}")


class VerificationError(RuntimeError):
    pass


def require_isolated_python():
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.ignore_environment):
        raise VerificationError("trusted verifier requires isolated Python with -I -S")
    if "" in sys.path:
        raise VerificationError("isolated Python must not search the current directory")


def command_environment():
    return {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": os.environ.get("HOME", "/tmp/swift-sample-trusted-home"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin:/bin",
    }


def run_git(repository, *arguments, check=True, binary=False):
    command = [
        "/usr/bin/git",
        "--no-replace-objects",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "diff.external=",
        "-C",
        str(repository),
        *arguments,
    ]
    result = subprocess.run(
        command,
        env=command_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=not binary,
        check=False,
    )
    if check and result.returncode != 0:
        output = result.stdout.decode("utf-8", "replace") if binary else result.stdout
        raise VerificationError(output.strip())
    return result


def require_sha(value, label):
    if not SHA_PATTERN.fullmatch(value or ""):
        raise VerificationError(f"{label} must be a full lowercase commit SHA")


def require_digest(value, label):
    if not re.fullmatch(r"[0-9a-f]{64}", value or ""):
        raise VerificationError(f"{label} must be a lowercase SHA-256 digest")


def git_text(repository, *arguments):
    return run_git(repository, *arguments).stdout.strip()


def git_bytes(repository, *arguments):
    return run_git(repository, *arguments, binary=True).stdout


def blob_at(repository, commit, path):
    return git_bytes(repository, "cat-file", "blob", f"{commit}:{path}")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_policy(base_repository, base_sha):
    raw = blob_at(base_repository, base_sha, "trusted-verifier/policy.json")
    try:
        policy = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VerificationError(f"trusted policy is invalid: {error}") from error
    if policy.get("schema") != 1:
        raise VerificationError("trusted policy schema must be 1")
    return policy, raw


def verify_trusted_checkout(base_repository, base_sha, policy):
    if git_text(base_repository, "rev-parse", "HEAD") != base_sha:
        raise VerificationError("trusted checkout HEAD differs from workflow SHA")
    trusted_paths = policy.get("trusted_paths")
    if not isinstance(trusted_paths, list) or not trusted_paths:
        raise VerificationError("trusted policy must enumerate its trust boundary")
    for relative in trusted_paths:
        if not isinstance(relative, str) or relative.startswith("/") or ".." in Path(relative).parts:
            raise VerificationError("trusted policy contains an invalid path")
        working_path = base_repository / relative
        if not working_path.is_file() or working_path.is_symlink():
            raise VerificationError(f"trusted checkout path is not a regular file: {relative}")
        if working_path.read_bytes() != blob_at(base_repository, base_sha, relative):
            raise VerificationError(f"trusted checkout bytes differ from workflow SHA: {relative}")


def verify_topology(candidate_repository, base_sha, head_sha, rejected_commits):
    if git_text(candidate_repository, "rev-parse", "HEAD") != head_sha:
        raise VerificationError("candidate checkout HEAD differs from event head SHA")
    parents = git_text(candidate_repository, "rev-list", "--parents", "-n", "1", head_sha).split()
    if parents != [head_sha, base_sha]:
        raise VerificationError("trusted base must be the candidate's sole parent")
    if git_text(candidate_repository, "rev-list", "--count", f"{base_sha}..{head_sha}") != "1":
        raise VerificationError("candidate must contain exactly one commit above the trusted base")
    for rejected in rejected_commits:
        require_sha(rejected, "rejected candidate")
        exists = run_git(candidate_repository, "cat-file", "-e", f"{rejected}^{{commit}}", check=False)
        if exists.returncode != 0:
            continue
        ancestor = run_git(candidate_repository, "merge-base", "--is-ancestor", rejected, head_sha, check=False)
        if ancestor.returncode == 0:
            raise VerificationError(f"rejected candidate is an ancestor: {rejected}")


def changed_paths(candidate_repository, base_sha, head_sha):
    raw = git_bytes(
        candidate_repository,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "--no-renames",
        "--diff-filter=ACDMRT",
        "-r",
        "-z",
        base_sha,
        head_sha,
    )
    try:
        paths = [part.decode("utf-8") for part in raw.split(b"\0") if part]
    except UnicodeDecodeError as error:
        raise VerificationError("candidate changed path is not valid UTF-8") from error
    return paths


def tree_entry(candidate_repository, head_sha, path):
    raw = git_bytes(candidate_repository, "ls-tree", "-z", head_sha, "--", path)
    entries = [entry for entry in raw.split(b"\0") if entry]
    if len(entries) != 1:
        raise VerificationError(f"candidate target must have one tree entry: {path}")
    metadata, separator, encoded_path = entries[0].partition(b"\t")
    if separator != b"\t" or encoded_path.decode("utf-8", "strict") != path:
        raise VerificationError(f"candidate tree entry is malformed: {path}")
    mode, object_type, object_sha = metadata.decode("ascii").split()
    if object_type != "blob":
        raise VerificationError(f"candidate target must be a blob: {path}")
    return mode, object_sha


def verify_reviewed_files(base_repository, candidate_repository, base_sha, head_sha, policy):
    expected_files = policy.get("expected_files")
    if not isinstance(expected_files, dict) or not expected_files:
        raise VerificationError("trusted policy must define expected semantic files")
    actual_paths = changed_paths(candidate_repository, base_sha, head_sha)
    expected_paths = sorted(expected_files)
    if sorted(actual_paths) != expected_paths:
        unexpected = sorted(set(actual_paths).difference(expected_paths))
        missing = sorted(set(expected_paths).difference(actual_paths))
        details = []
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        raise VerificationError("candidate changed-file boundary differs (" + "; ".join(details) + ")")

    verified = {}
    for path in expected_paths:
        contract = expected_files[path]
        template = contract.get("template")
        expected_mode = contract.get("mode")
        expected_digest = contract.get("sha256")
        if not isinstance(template, str) or not isinstance(expected_mode, str) or not isinstance(expected_digest, str):
            raise VerificationError(f"trusted file contract is malformed: {path}")
        require_digest(expected_digest, f"trusted file digest for {path}")
        template_path = f"trusted-verifier/{template}"
        template_bytes = blob_at(base_repository, base_sha, template_path)
        if digest(template_bytes) != expected_digest:
            raise VerificationError(f"trusted template digest differs from policy: {path}")
        mode, object_sha = tree_entry(candidate_repository, head_sha, path)
        if mode != expected_mode:
            raise VerificationError(f"candidate mode differs from reviewed mode: {path}")
        candidate_bytes = git_bytes(candidate_repository, "cat-file", "blob", object_sha)
        if candidate_bytes != template_bytes:
            raise VerificationError(f"candidate reviewed bytes differ: {path}")
        verified[path] = expected_digest
    return verified


def write_receipt(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def verify(arguments):
    require_isolated_python()
    base_repository = arguments.base_repository.resolve()
    candidate_repository = arguments.candidate_repository.resolve()
    base_sha = arguments.base_sha
    head_sha = arguments.head_sha
    require_sha(base_sha, "trusted base SHA")
    require_sha(head_sha, "candidate head SHA")
    arguments.receipt.unlink(missing_ok=True)

    policy, policy_bytes = load_policy(base_repository, base_sha)
    verify_trusted_checkout(base_repository, base_sha, policy)
    rejected = policy.get("rejected_bootstrap_ancestors")
    if not isinstance(rejected, list) or len(rejected) != 13:
        raise VerificationError("trusted policy must retain all thirteen rejected candidates")
    verify_topology(candidate_repository, base_sha, head_sha, rejected)
    verified_files = verify_reviewed_files(base_repository, candidate_repository, base_sha, head_sha, policy)
    candidate_tree = git_text(candidate_repository, "rev-parse", f"{head_sha}^{{tree}}")
    workflow_bytes = blob_at(
        base_repository,
        base_sha,
        ".github/workflows/trusted-swift-sample-gate.yml",
    )
    write_receipt(
        arguments.receipt,
        {
            "candidate_head_sha": head_sha,
            "candidate_tree_sha": candidate_tree,
            "policy_sha256": digest(policy_bytes),
            "schema": 1,
            "status": "passed",
            "trusted_base_sha": base_sha,
            "trusted_workflow_sha256": digest(workflow_bytes),
            "verified_files": verified_files,
        },
    )
    print("base-owned trusted verifier accepted exact reviewed semantic bytes")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-repository", type=Path, required=True)
    parser.add_argument("--candidate-repository", type=Path, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    return parser.parse_args()


def main():
    try:
        verify(parse_arguments())
    except (OSError, VerificationError) as error:
        print(f"trusted verifier rejected candidate: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
