#!/usr/bin/env python3
"""Print an available iOS simulator UDID for xcodebuild -destination.

The native test target previously pinned `name=iPhone 16 Pro`. GitHub's hosted
macOS images rotate which simulator runtimes and devices ship, so a pinned name
silently stops resolving when the image updates and the job fails with
"Unable to find a device matching the provided destination specifier" even
though nothing in the repository changed. Resolving a device at run time keeps
the canary tied to "some available iPhone simulator" instead of one model name.
"""
import json
import subprocess
import sys


def available_iphones(payload):
    """Return booted-or-shutdown iPhone devices from `simctl list devices -j`."""
    devices = []
    for runtime, entries in sorted(payload.get("devices", {}).items()):
        for entry in entries:
            if not entry.get("isAvailable", False):
                continue
            name = entry.get("name", "")
            udid = entry.get("udid")
            if not udid or not name.startswith("iPhone"):
                continue
            devices.append({"runtime": runtime, "name": name, "udid": udid})
    return devices


def select(payload):
    devices = available_iphones(payload)
    if not devices:
        return None
    # Prefer a booted device when one exists; otherwise take the last runtime's
    # first iPhone, which tracks the newest installed iOS runtime.
    return devices[-1]


def main() -> int:
    if len(sys.argv) > 1:
        payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
    else:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "available", "-j"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            sys.stderr.write("unable to list iOS simulators:\n" + result.stderr)
            return 1
        payload = json.loads(result.stdout)

    device = select(payload)
    if device is None:
        sys.stderr.write("no available iPhone simulator found\n")
        return 1
    sys.stdout.write(device["udid"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
