#!/usr/bin/env python3
import argparse
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_SOURCE = ROOT / "background_switcher" / "background_switcher" / "BackgroundSelection.swift"
ADAPTER_SOURCE = ROOT / "Tests" / "BackgroundSelectionTests" / "main.swift"

EXPECTED_PRODUCTION_SOURCE = """\
enum BackgroundSelection: CaseIterable {
    case first
    case second

    var key: String {
        switch self {
        case .first:
            return "Background1"
        case .second:
            return "Background2"
        }
    }

    var title: String {
        switch self {
        case .first:
            return "Background 1"
        case .second:
            return "Background 2"
        }
    }

    var buttonTag: Int {
        switch self {
        case .first:
            return 1
        case .second:
            return 2
        }
    }

    static func selection(forButtonTag tag: Int) -> BackgroundSelection? {
        switch tag {
        case 1:
            return .first
        case 2:
            return .second
        default:
            return nil
        }
    }

    static func key(forButtonTag tag: Int) -> String? {
        return selection(forButtonTag: tag)?.key
    }
}
"""

EXPECTED_ADAPTER_SOURCE = """\
import Foundation

private func emit(_ line: String) {
    let data = Data((line + "\\n").utf8)
    FileHandle.standardOutput.write(data)
}

private func observation(for rawTag: String) -> String {
    guard let tag = Int(rawTag) else {
        return "\\(rawTag)|malformed"
    }

    guard let selection = BackgroundSelection.selection(forButtonTag: tag) else {
        return "\\(tag)|none"
    }

    return "\\(tag)|selection|\\(selection.buttonTag)|\\(selection.key)|\\(selection.title)"
}

for rawTag in CommandLine.arguments.dropFirst() {
    emit(observation(for: rawTag))
}
"""

BROKEN_PRODUCTION_SOURCE = EXPECTED_PRODUCTION_SOURCE.replace(
    "        case 2:\n            return .second",
    "        case 2:\n            return nil",
    1,
)

SWIFT_INT_MIN = -(2 ** 63)
SWIFT_INT_MAX = 2 ** 63 - 1


class VerificationError(Exception):
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()

    try:
        validate_static_sources()
        if not args.static_only:
            verify_black_box_mapping()
    except VerificationError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


def validate_static_sources():
    require_exact_source(PRODUCTION_SOURCE, EXPECTED_PRODUCTION_SOURCE, "BackgroundSelection.swift")
    require_exact_source(ADAPTER_SOURCE, EXPECTED_ADAPTER_SOURCE, "BackgroundSelectionTests/main.swift")


def require_exact_source(path, expected, label):
    try:
        actual = path.read_text(encoding="utf-8")
    except OSError as error:
        raise VerificationError(f"{label} is unreadable: {error}")
    if actual != expected:
        raise VerificationError(
            f"{label} must match the audited pure source exactly; "
            "state, counters, custom initializers, process/environment access, "
            "filesystem access, clock access, output, and test-aware behavior are not allowed"
        )


def verify_black_box_mapping():
    toolchain = resolve_trusted_swift_toolchain()
    if toolchain is None:
        if platform.system() == "Darwin":
            raise VerificationError("trusted Apple swiftc could not be resolved")
        print("trusted swiftc unavailable on non-Darwin; structural verification completed")
        return

    with tempfile.TemporaryDirectory(prefix="background-selection-verifier.") as temp_dir:
        temp = Path(temp_dir)
        real_observer = compile_observer(
            toolchain,
            EXPECTED_PRODUCTION_SOURCE,
            EXPECTED_ADAPTER_SOURCE,
            temp,
            "real-observer",
        )
        broken_observer = compile_observer(
            toolchain,
            BROKEN_PRODUCTION_SOURCE,
            EXPECTED_ADAPTER_SOURCE,
            temp,
            "broken-observer",
        )

        for name, sequence in observation_sequences().items():
            assert_observer_matches(real_observer, name, sequence)

        broken_sequence = ["1", "2", "0", str(SWIFT_INT_MIN), "not-an-int"]
        if observer_matches(broken_observer, broken_sequence):
            raise VerificationError("known-broken production was accepted by the black-box oracle")

    print("Background selection structural and black-box verification passed.")


def resolve_trusted_swift_toolchain():
    if platform.system() == "Darwin":
        developer_dir = run_checked(["/usr/bin/xcode-select", "-p"]).strip()
        swiftc = run_checked(["/usr/bin/xcrun", "--find", "swiftc"]).strip()
        sdk = run_checked(["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"]).strip()
        allowed_prefix = f"{developer_dir}/Toolchains/"
        if not swiftc.startswith(allowed_prefix) or not swiftc.endswith("/usr/bin/swiftc"):
            raise VerificationError(f"untrusted swiftc path: {swiftc}")
        swiftc_path = Path(swiftc)
        sdk_path = Path(sdk)
        if swiftc_path.exists() and os.access(str(swiftc_path), os.X_OK) and sdk_path.exists():
            return {"swiftc": str(swiftc_path), "sdk": str(sdk_path)}
        return None

    for candidate in (
        "/usr/bin/swiftc",
        "/usr/local/bin/swiftc",
        "/opt/swift/usr/bin/swiftc",
        "/opt/homebrew/bin/swiftc",
    ):
        path = Path(candidate)
        if path.exists() and os.access(str(path), os.X_OK):
            return {"swiftc": str(path), "sdk": None}
    return None


def run_checked(command):
    try:
        completed = subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise VerificationError(f"failed to run {' '.join(command)}: {error}")
    return completed.stdout


def compile_observer(toolchain, production_source, adapter_source, temp, name):
    source_dir = temp / name
    source_dir.mkdir()
    production_path = source_dir / "BackgroundSelection.swift"
    adapter_path = source_dir / "main.swift"
    output_path = temp / f"{name}-bin"
    production_path.write_text(production_source, encoding="utf-8")
    adapter_path.write_text(adapter_source, encoding="utf-8")

    command = [toolchain["swiftc"]]
    if toolchain["sdk"]:
        command.extend(["-sdk", toolchain["sdk"]])
    command.extend([str(production_path), str(adapter_path), "-o", str(output_path)])
    try:
        subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        raise VerificationError(f"failed to compile {name}: {error.stderr.strip()}")
    return output_path


def observation_sequences():
    baseline = [str(tag) for tag in (1, 2, 0, -1, SWIFT_INT_MIN, SWIFT_INT_MAX, 3)]
    exact_4097 = ["1"] * 4097
    mixed_long = []
    for index in range(1024):
        mixed_long.extend((str(index + 3), "1", "-1", "2"))
    malformed = ["not-an-int", "", "1.0", str(SWIFT_INT_MAX + 1), str(SWIFT_INT_MIN - 1)]
    return {
        "baseline": baseline,
        "exact-4097": exact_4097,
        "mixed-long": mixed_long,
        "malformed": malformed,
    }


def assert_observer_matches(observer, name, sequence):
    if not observer_matches(observer, sequence):
        actual = run_observer(observer, sequence)
        expected = [expected_line(raw_tag) for raw_tag in sequence]
        for index, (actual_line, expected_line_value) in enumerate(zip(actual, expected), start=1):
            if actual_line != expected_line_value:
                raise VerificationError(
                    f"{name} observation {index} mismatch: "
                    f"expected {expected_line_value!r}, got {actual_line!r}"
                )
        raise VerificationError(f"{name} observation count mismatch")


def observer_matches(observer, sequence):
    return run_observer(observer, sequence) == [expected_line(raw_tag) for raw_tag in sequence]


def run_observer(observer, sequence):
    try:
        completed = subprocess.run(
            [str(observer), *sequence],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:
        raise VerificationError(f"observer execution failed: {error.stderr.strip()}")
    return completed.stdout.splitlines()


def expected_line(raw_tag):
    try:
        tag = int(raw_tag)
    except ValueError:
        return f"{raw_tag}|malformed"
    if tag < SWIFT_INT_MIN or tag > SWIFT_INT_MAX:
        return f"{raw_tag}|malformed"
    if tag == 1:
        return "1|selection|1|Background1|Background 1"
    if tag == 2:
        return "2|selection|2|Background2|Background 2"
    return f"{tag}|none"


if __name__ == "__main__":
    raise SystemExit(main())
