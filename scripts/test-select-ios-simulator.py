#!/usr/bin/env python3
"""Contract tests for scripts/select-ios-simulator.py.

xcrun is macOS-only, so these tests drive the selector with recorded
`simctl list devices available -j` payloads. That keeps the drift behavior
verifiable on Linux, where the hosted-macOS destination bug is otherwise
invisible.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTOR = ROOT / "scripts" / "select-ios-simulator.py"

# Shape mirrors `xcrun simctl list devices available -j` on the hosted images.
IMAGE_WITH_IPHONE_16 = {
    "devices": {
        "com.apple.CoreSimulator.SimRuntime.iOS-18-0": [
            {
                "name": "iPhone 16 Pro",
                "udid": "AAAAAAAA-0000-0000-0000-000000000001",
                "isAvailable": True,
                "state": "Shutdown",
            }
        ]
    }
}

# The drift that broke CI: the image rotated and no iPhone 16 Pro remains.
IMAGE_AFTER_DRIFT = {
    "devices": {
        "com.apple.CoreSimulator.SimRuntime.iOS-18-0": [
            {
                "name": "iPhone 17 Pro",
                "udid": "BBBBBBBB-0000-0000-0000-000000000002",
                "isAvailable": True,
                "state": "Shutdown",
            }
        ],
        "com.apple.CoreSimulator.SimRuntime.iOS-26-0": [
            {
                "name": "iPhone 18 Pro",
                "udid": "CCCCCCCC-0000-0000-0000-000000000003",
                "isAvailable": True,
                "state": "Shutdown",
            }
        ],
    }
}

UNAVAILABLE_ONLY = {
    "devices": {
        "com.apple.CoreSimulator.SimRuntime.iOS-18-0": [
            {
                "name": "iPhone 16 Pro",
                "udid": "DDDDDDDD-0000-0000-0000-000000000004",
                "isAvailable": False,
                "state": "Shutdown",
            }
        ]
    }
}

IPAD_ONLY = {
    "devices": {
        "com.apple.CoreSimulator.SimRuntime.iOS-18-0": [
            {
                "name": "iPad Pro 13-inch (M4)",
                "udid": "EEEEEEEE-0000-0000-0000-000000000005",
                "isAvailable": True,
                "state": "Shutdown",
            }
        ]
    }
}


def run(payload, tmp):
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SELECTOR), str(tmp)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def main() -> int:
    tmp = ROOT / f".simctl-fixture-{id(object())}.json"
    try:
        result = run(IMAGE_WITH_IPHONE_16, tmp)
        if result.returncode != 0 or result.stdout != "AAAAAAAA-0000-0000-0000-000000000001":
            raise SystemExit(f"expected the available iPhone udid, got {result.returncode}: {result.stdout!r}")
        print("selected an available iPhone simulator")

        # The whole point: selection must survive the image losing iPhone 16 Pro.
        result = run(IMAGE_AFTER_DRIFT, tmp)
        if result.returncode != 0 or result.stdout != "CCCCCCCC-0000-0000-0000-000000000003":
            raise SystemExit(f"expected newest-runtime iPhone after drift, got {result.returncode}: {result.stdout!r}")
        print("survived hosted-image simulator drift")

        result = run(UNAVAILABLE_ONLY, tmp)
        if result.returncode == 0:
            raise SystemExit("expected failure when no simulator is available")
        print("failed closed when no simulator is available")

        result = run(IPAD_ONLY, tmp)
        if result.returncode == 0:
            raise SystemExit("expected failure when only non-iPhone devices exist")
        print("failed closed when only non-iPhone devices exist")
    finally:
        tmp.unlink(missing_ok=True)

    print("iOS simulator selection contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
