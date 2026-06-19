#!/usr/bin/env python3
import argparse
import hashlib
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PRODUCTION_PATH = Path("background_switcher/background_switcher/BackgroundSelection.swift")
ADAPTER_PATH = Path("Tests/BackgroundSelectionTests/main.swift")
BASE_TAGS = [1, 2, 0, -1, 3, -(2**63), 2**63 - 1, 41]
BOUNDARY_LENGTHS = (17, 33, 65, 129, 257, 513, 1025)
RANDOMIZED_STRESS_RUNS = 12
MINIMUM_RANDOMIZED_STRESS_LENGTH = 1025
MAXIMUM_RANDOMIZED_STRESS_LENGTH = 4096
FORBIDDEN_PRODUCTION_TOKENS = (
    "import ",
    "CommandLine",
    "ProcessInfo",
    "Bundle",
    "Thread",
    "Dispatch",
    "FileManager",
    "FileHandle",
    "Foundation",
    "Darwin",
    "Glibc",
    "getenv",
    "getpid",
    "argc",
    "argv",
    "dlopen",
    "dlsym",
    "NSClassFromString",
    "_isDebugAssertConfiguration",
    "environment",
    "Date(",
    "UUID(",
    "print(",
    "stdout",
    "stderr",
    "#if",
    "DEBUG",
    "TEST",
)
FORBIDDEN_ADAPTER_TOKENS = (
    '"Background1"',
    '"Background2"',
    "tag ==",
    "tag !=",
    "switch tag",
)


class VerificationError(RuntimeError):
    pass


def base_environment():
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": os.environ.get("HOME", "/tmp"),
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
    }


def trusted_environment():
    environment = base_environment()
    if sys.platform == "darwin":
        developer_directory = direct_command_output(["/usr/bin/xcode-select", "-p"], environment)
        environment["DEVELOPER_DIR"] = developer_directory
        environment["SDKROOT"] = direct_command_output(
            ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"],
            environment,
        )
    return environment


def direct_command_output(command, environment):
    result = subprocess.run(
        command,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise VerificationError(f"command failed: {command!r}\n{result.stdout}{result.stderr}")
    return result.stdout.strip()


def command_output(command):
    return direct_command_output(command, trusted_environment())


def resolve_canonical_swiftc():
    if sys.platform == "darwin":
        xcrun = Path("/usr/bin/xcrun")
        xcode_select = Path("/usr/bin/xcode-select")
        if not xcrun.is_file() or not xcode_select.is_file():
            raise VerificationError("canonical Apple developer tool resolvers are unavailable")
        developer_directory = Path(command_output([str(xcode_select), "-p"])).resolve()
        compiler = Path(command_output([str(xcrun), "--find", "swiftc"])).absolute()
        allowed_roots = (developer_directory, Path("/Library/Developer/CommandLineTools").resolve())
        if not any(compiler.is_relative_to(root) for root in allowed_roots):
            raise VerificationError(f"resolved Swift compiler is outside the selected toolchain: {compiler}")
    else:
        candidates = (
            Path("/usr/local/swift/usr/bin/swiftc"),
            Path("/usr/bin/swiftc"),
        )
        compiler = next((candidate.absolute() for candidate in candidates if candidate.is_file()), None)
        if compiler is None:
            raise VerificationError("canonical Swift compiler is unavailable")
    if not compiler.is_file() or not os.access(compiler, os.X_OK):
        raise VerificationError(f"resolved Swift compiler is not executable: {compiler}")
    return compiler


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_source_boundaries(production, adapter):
    production_text = production.read_text(encoding="utf-8")
    adapter_text = adapter.read_text(encoding="utf-8")
    for token in FORBIDDEN_PRODUCTION_TOKENS:
        if token in production_text:
            raise VerificationError(f"production mapping may not observe or forge the harness: {token}")
    for token in FORBIDDEN_ADAPTER_TOKENS:
        if token in adapter_text:
            raise VerificationError(f"adapter may not own mapping expectations: {token}")
    for required in (
        "Array(CommandLine.arguments.dropFirst())",
        "BackgroundSelection.selection(forButtonTag: tag)",
        "selection.rawValue",
        "selection.key",
        "selection.title",
        "invalid integer tag",
    ):
        if required not in adapter_text:
            raise VerificationError(f"adapter observation contract is missing: {required}")


def expected_line(tag):
    if tag == 1:
        return "selection:1:Background1:Background 1"
    if tag == 2:
        return "selection:2:Background2:Background 2"
    return "none"


def sequences_for_seed(seed):
    generator = random.Random(seed)
    generated_tags = []
    while len(generated_tags) < 64:
        tag = generator.randint(-(2**31), 2**31 - 1)
        if tag not in (1, 2) and tag not in generated_tags:
            generated_tags.append(tag)
    tags = [*BASE_TAGS, *generated_tags[:8]]
    sequences = [list(tags), list(reversed(tags))]
    for _ in range(10):
        sequence = list(tags)
        generator.shuffle(sequence)
        sequences.append(sequence)

    invalid_tags = [tag for tag in [*BASE_TAGS, *generated_tags] if tag not in (1, 2)]
    for length in BOUNDARY_LENGTHS:
        sequence = [generator.choice(invalid_tags) for _ in range(length)]
        sequence[0] = 1
        sequence[1] = 2
        sequence[15] = 2
        sequence[16] = 1
        sequence[-1] = 2
        sequences.append(sequence)

    permutation_pool = [1, 2, 1, 2, *invalid_tags]
    for _ in range(RANDOMIZED_STRESS_RUNS):
        length = generator.randint(MINIMUM_RANDOMIZED_STRESS_LENGTH, MAXIMUM_RANDOMIZED_STRESS_LENGTH)
        sequence = []
        while len(sequence) < length:
            block = list(permutation_pool)
            generator.shuffle(block)
            sequence.extend(block)
        sequence = sequence[:length]
        sequence[16] = generator.choice((1, 2))
        sequence[length // 2] = generator.choice((1, 2))
        sequence[-1] = generator.choice((1, 2))
        sequences.append(sequence)

    repeated_valid_sequence = [value for _ in range(1024) for value in (1, 2)]
    sequences.append(repeated_valid_sequence)
    generator.shuffle(sequences)
    return sequences


def compile_binary(compiler, production, adapter, output):
    result = subprocess.run(
        [str(compiler), str(production), str(adapter), "-o", str(output)],
        env=trusted_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise VerificationError(f"Swift compilation failed:\n{result.stdout}{result.stderr}")


def observe(binary, sequence):
    return subprocess.run(
        [str(binary), *[str(tag) for tag in sequence]],
        env=trusted_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def candidate_matches(binary, sequences):
    original_digest = digest(binary)
    for sequence in sequences:
        result = observe(binary, sequence)
        expected = [expected_line(tag) for tag in sequence]
        actual = result.stdout.splitlines()
        if result.returncode != 0 or result.stderr:
            return False, (
                f"sequence_length={len(sequence)} status={result.returncode} "
                f"actual_length={len(actual)} stderr={result.stderr!r}"
            )
        if actual != expected:
            mismatch_index = next(
                (index for index, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]),
                min(len(actual), len(expected)),
            )
            tag = sequence[mismatch_index] if mismatch_index < len(sequence) else None
            expected_value = expected[mismatch_index] if mismatch_index < len(expected) else None
            actual_value = actual[mismatch_index] if mismatch_index < len(actual) else None
            return False, (
                f"sequence_length={len(sequence)} mismatch_index={mismatch_index} tag={tag!r} "
                f"expected={expected_value!r} actual={actual_value!r} actual_length={len(actual)}"
            )
        if digest(binary) != original_digest:
            return False, "compiled observer changed during execution"
    return True, ""


def verify_candidate(binary, sequences):
    passed, detail = candidate_matches(binary, sequences)
    if not passed:
        raise VerificationError(detail)


def verify_malformed_input(binary):
    result = subprocess.run(
        [str(binary), "not-an-integer"],
        env=trusted_environment(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0 or result.stdout or result.stderr != "invalid integer tag\n":
        raise VerificationError(
            f"malformed input was not rejected exactly: status={result.returncode} "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )


def run_verification(root, seed):
    production = root / PRODUCTION_PATH
    adapter = root / ADAPTER_PATH
    validate_source_boundaries(production, adapter)
    compiler = resolve_canonical_swiftc()
    compiler_digest = digest(compiler)
    sequences = sequences_for_seed(seed)
    generator = random.Random(seed ^ 0x5A17)

    with tempfile.TemporaryDirectory(prefix="background-selection-verification-") as temporary:
        build_directory = Path(temporary)
        real_source = build_directory / f"{generator.getrandbits(96):024x}.swift"
        broken_source = build_directory / f"{generator.getrandbits(96):024x}.swift"
        real_source.write_bytes(production.read_bytes())
        broken_text = production.read_text(encoding="utf-8").replace("case second = 2", "case second = 22", 1)
        if broken_text == production.read_text(encoding="utf-8"):
            raise VerificationError("known-broken negative control could not be constructed")
        broken_source.write_text(broken_text, encoding="utf-8")

        real_binary = build_directory / f"{generator.getrandbits(96):024x}"
        broken_binary = build_directory / f"{generator.getrandbits(96):024x}"
        compilations = [(real_source, real_binary), (broken_source, broken_binary)]
        generator.shuffle(compilations)
        for source, binary in compilations:
            compile_binary(compiler, source, adapter, binary)

        verify_candidate(real_binary, sequences)
        verify_malformed_input(real_binary)
        try:
            verify_candidate(broken_binary, sequences)
        except VerificationError:
            pass
        else:
            raise VerificationError("mandatory known-broken negative control was accepted")

    if digest(compiler) != compiler_digest:
        raise VerificationError("canonical Swift compiler changed during verification")
    return compiler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--seed", type=int)
    arguments = parser.parse_args()
    seed = arguments.seed if arguments.seed is not None else int.from_bytes(os.urandom(8), "big")
    try:
        compiler = run_verification(arguments.root.resolve(), seed)
    except (OSError, VerificationError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Background selection black-box verification passed (seed {seed}, compiler {compiler}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
