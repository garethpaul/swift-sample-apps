#!/usr/bin/env python3
import argparse
import http.client
import json
import re
import ssl
import sys
import urllib.parse


REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


class EnvironmentError(RuntimeError):
    pass


def require_isolated_python():
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.ignore_environment):
        raise EnvironmentError("environment verifier requires isolated Python with -I -S")


def fetch_json(path):
    connection = http.client.HTTPSConnection(
        "api.github.com",
        timeout=15,
        context=ssl.create_default_context(),
    )
    try:
        connection.request(
            "GET",
            path,
            headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "swift-sample-trusted-environment-verifier/1",
            "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response = connection.getresponse()
        if response.status != 200:
            raise EnvironmentError(f"GitHub environment API returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))
    except (OSError, http.client.HTTPException, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise EnvironmentError(f"unable to read public GitHub environment policy: {error}") from error
    finally:
        connection.close()


def validate_environment(environment, policies, expected_name):
    if environment.get("name") != expected_name:
        raise EnvironmentError("GitHub environment name differs from the trusted policy")
    deployment_policy = environment.get("deployment_branch_policy")
    if deployment_policy != {"protected_branches": False, "custom_branch_policies": True}:
        raise EnvironmentError("environment must use selected branch policies only")
    branch_policies = policies.get("branch_policies")
    if policies.get("total_count") != 1 or branch_policies != [{"name": "master", "type": "branch"}]:
        raise EnvironmentError("environment deployment branch must be exactly master")


def verify(arguments):
    require_isolated_python()
    if not REPOSITORY_PATTERN.fullmatch(arguments.repository):
        raise EnvironmentError("repository must be an owner/name slug")
    encoded_environment = urllib.parse.quote(arguments.environment, safe="")
    root = f"/repos/{arguments.repository}/environments/{encoded_environment}"
    environment = fetch_json(root)
    policies = fetch_json(f"{root}/deployment-branch-policies?per_page=100")
    validate_environment(environment, policies, arguments.environment)
    print("protected environment policy is configured for exact master deployments")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--environment", required=True)
    return parser.parse_args()


def main():
    try:
        verify(parse_arguments())
    except EnvironmentError as error:
        print(f"trusted environment preflight failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
