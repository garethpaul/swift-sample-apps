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
    if not isinstance(environment, dict):
        raise EnvironmentError("GitHub environment response must be an object")
    if not isinstance(policies, dict):
        raise EnvironmentError("GitHub deployment branch policy response must be an object")

    name = environment.get("name")
    if not isinstance(name, str) or name != expected_name:
        raise EnvironmentError("GitHub environment name differs from the trusted policy")
    deployment_policy = environment.get("deployment_branch_policy")
    if not isinstance(deployment_policy, dict):
        raise EnvironmentError("environment deployment branch policy must be an object")
    protected_branches = deployment_policy.get("protected_branches")
    custom_branch_policies = deployment_policy.get("custom_branch_policies")
    if protected_branches is not False or custom_branch_policies is not True:
        raise EnvironmentError("environment must use selected branch policies only")

    total_count = policies.get("total_count")
    branch_policies = policies.get("branch_policies")
    if type(total_count) is not int or total_count != 1:
        raise EnvironmentError("environment deployment branch policy count must be exactly one")
    if not isinstance(branch_policies, list) or len(branch_policies) != 1:
        raise EnvironmentError("environment deployment branch must be exactly master")
    branch_policy = branch_policies[0]
    if not isinstance(branch_policy, dict):
        raise EnvironmentError("environment deployment branch policy must be an object")
    branch_name = branch_policy.get("name")
    branch_type = branch_policy.get("type")
    if not isinstance(branch_name, str) or not isinstance(branch_type, str):
        raise EnvironmentError("environment deployment branch fields must be strings")
    if branch_name != "master" or branch_type != "branch":
        raise EnvironmentError("environment deployment branch must be exactly master")


def validate_required_check_source(source, expected_context, expected_app_id):
    if not isinstance(source, dict):
        raise EnvironmentError("required check source must be an object")
    context = source.get("context")
    app_id = source.get("app_id")
    if not isinstance(context, str) or context != expected_context:
        raise EnvironmentError("required check context differs from the trusted policy")
    if type(expected_app_id) is not int or type(app_id) is not int or app_id != expected_app_id:
        raise EnvironmentError("required check GitHub App source differs from the trusted policy")


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
