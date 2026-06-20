#!/usr/bin/python3
import argparse
import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXACT_DEFAULT = "e0b72f53b6ef73989b8dcd12473c8476c92baf02"
SELECTION_SOURCE = ROOT / "background_switcher/background_switcher/BackgroundSelection.swift"
PORTABLE_TEST = ROOT / "Tests/BackgroundSelectionTests/main.swift"
NATIVE_TEST = ROOT / "background_switcher/background_switcherTests/background_switcherTests.swift"
CONTRACT_TEST = ROOT / "Tests/test_background_selection_execution_contract.py"


def run(command, *, input_text=None):
    return subprocess.run(
        [str(part) for part in command],
        cwd=ROOT,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def git(*arguments):
    result = run(["/usr/bin/git", *arguments])
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip())
    return result.stdout


def verify_topology():
    head = git("rev-parse", "HEAD").strip()
    if head == EXACT_DEFAULT:
        return
    parents = git("show", "-s", "--format=%P", head).split()
    if parents != [EXACT_DEFAULT]:
        raise RuntimeError("candidate must have exact default as its sole parent")


def parent_text(path):
    return git("show", f"{EXACT_DEFAULT}:{path}")


def parent_cases():
    source = parent_text("Tests/BackgroundSelectionTests/main.swift")
    cases = []
    for expected, tag, name in re.findall(
        r'expectKey\((nil|"[^"]+"), tag: (-?\d+|Int\.min), caseName: "([^"]+)"\)',
        source,
    ):
        cases.append((expected, tag, name))
    if cases != [
        ('"Background1"', "1", "first background"),
        ('"Background2"', "2", "second background"),
        ("nil", "0", "zero tag"),
        ("nil", "-1", "negative tag"),
        ("nil", "Int.min", "minimum integer tag"),
        ("nil", "3", "out-of-range tag"),
    ]:
        raise RuntimeError("exact parent behavior oracle is incomplete or unexpected")
    return cases


def verify_test_semantics(cases):
    portable = PORTABLE_TEST.read_text(encoding="utf-8")
    if re.search(r"\bif\s+(?:false|0)\b", portable):
        raise RuntimeError("portable behavior assertions are disabled")
    if "fatalError" not in portable or "actual != expected" not in portable:
        raise RuntimeError("portable behavior assertions must fail on mismatches")
    for expected, tag, name in cases:
        required = f'expectKey({expected}, tag: {tag}, caseName: "{name}")'
        if required not in portable:
            raise RuntimeError(f"portable behavior assertion missing: {required}")

    native = NATIVE_TEST.read_text(encoding="utf-8")
    if re.search(r"XCTAssert(?:True|False)\(\s*(?:true|false)\s*\)", native):
        raise RuntimeError("native XCTest contains a vacuous constant assertion")
    required_native = (
        'XCTAssertEqual(BackgroundSelection.first.key, "Background1")',
        'XCTAssertEqual(BackgroundSelection.second.key, "Background2")',
        "XCTAssertEqual(BackgroundSelection.selection(forButtonTag: 1), .first)",
        "XCTAssertEqual(BackgroundSelection.selection(forButtonTag: 2), .second)",
        "XCTAssertNil(BackgroundSelection.selection(forButtonTag: 0))",
        "testLatestSelectionWinsAcrossOverlappingAnimations",
        "testReduceMotionChangeStopsActiveTransitionAtLatestSelection",
        "testSelectionMappingRemainsCorrectAfterRepeatedAndDelayedAccess",
    )
    for contract in required_native:
        if contract not in native:
            raise RuntimeError(f"native XCTest semantic contract missing: {contract}")

    tree = ast.parse(CONTRACT_TEST.read_text(encoding="utf-8"), filename=str(CONTRACT_TEST))
    classes = [
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "BackgroundSelectionExecutionContractTests"
    ]
    if len(classes) != 1:
        raise RuntimeError("contract mutation suite must define one reviewed test class")
    methods = [
        node
        for node in classes[0].body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    if len(methods) != 32:
        raise RuntimeError("contract mutation suite must retain exactly 32 substantive tests")
    for method in methods:
        if method.decorator_list:
            raise RuntimeError(f"contract mutation cannot be skipped or decorated: {method.name}")
        names = {node.id for node in ast.walk(method) if isinstance(node, ast.Name)}
        calls = set()
        for node in ast.walk(method):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr.startswith("assert")
                and node.args
                and all(isinstance(argument, ast.Constant) for argument in node.args[:2])
            ):
                raise RuntimeError(f"contract mutation contains a vacuous constant assertion: {method.name}")
        if "DisposableRepository" not in names or not ({"run", "assert_lint_rejects"} & calls):
            raise RuntimeError(f"contract mutation does not exercise a disposable repository: {method.name}")


def generated_harness(cases):
    checks = "\n".join(
        f'expectKey({expected}, tag: {tag}, caseName: "{name}")'
        for expected, tag, name in cases
    )
    return f'''private func expectKey(_ expected: String?, tag: Int, caseName: String) {{
    let actual = BackgroundSelection.key(forButtonTag: tag)
    if actual != expected {{
        fatalError("\\(caseName): expected \\(String(describing: expected)), got \\(String(describing: actual))")
    }}
}}

{checks}
'''


def trusted_swiftc():
    resolver = ROOT / "scripts/resolve-trusted-tools.sh"
    result = run(["/bin/sh", resolver, "swiftc"])
    return result.stdout.strip() if result.returncode == 0 else ""


def verify_behavior():
    verify_topology()
    cases = parent_cases()
    verify_test_semantics(cases)
    source = SELECTION_SOURCE.read_text(encoding="utf-8")
    if "import UIKit" in source:
        raise RuntimeError("production mapping must remain framework-independent")
    compiler = trusted_swiftc()
    if compiler:
        with tempfile.TemporaryDirectory(prefix="background-parent-oracle-") as directory:
            directory = Path(directory)
            harness = directory / "main.swift"
            binary = directory / "parent-oracle"
            harness.write_text(generated_harness(cases), encoding="utf-8")
            command = [compiler]
            sdk = run(["/usr/bin/xcrun", "--show-sdk-path", "--sdk", "macosx"])
            if sdk.returncode == 0:
                command.extend(["-sdk", sdk.stdout.strip()])
            command.extend([SELECTION_SOURCE, harness, "-o", binary])
            compiled = run(command)
            if compiled.returncode != 0:
                raise RuntimeError(f"parent-derived harness did not compile:\n{compiled.stdout}")
            executed = run([binary])
            if executed.returncode != 0:
                raise RuntimeError(f"parent-derived behavior mismatch:\n{executed.stdout}")
    print("parent-derived behavior oracle passed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("behavior", "all"), default="all")
    arguments = parser.parse_args()
    try:
        verify_behavior()
    except (OSError, RuntimeError) as error:
        print(f"trusted candidate verification failed: {error}", file=sys.stderr)
        return 1
    if arguments.mode == "all":
        print("trusted candidate preflight passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
