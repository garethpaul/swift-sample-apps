#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-swift-samples.py"

MUTATIONS = (
    (
        ROOT / "facebook-login/facebook-login/ViewController.swift",
        'NSLog("Unexpected Facebook login error")',
        'NSLog("Unexpected error:%@", error)',
        "Facebook raw provider error",
    ),
    (
        ROOT / "parse_example/parse_example/AppDelegate.swift",
        'NSLog("Parse save failed")',
        'NSLog("Parse save failed:%@", err)',
        "Parse raw provider error",
    ),
)


def run_checker():
    return subprocess.run(
        [sys.executable, str(CHECKER), "--mode", "samples"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


baseline = run_checker()
if baseline.returncode != 0:
    raise SystemExit("baseline service error privacy contract failed: " + baseline.stdout.strip())

for path, original, replacement, name in MUTATIONS:
    source = path.read_text(encoding="utf-8")
    if source.count(original) != 1:
        raise SystemExit(f"mutation anchor changed: {name}")
    try:
        path.write_text(source.replace(original, replacement, 1), encoding="utf-8")
        result = run_checker()
        if result.returncode == 0:
            raise SystemExit(f"service error privacy mutation unexpectedly passed: {name}")
    finally:
        path.write_text(source, encoding="utf-8")
    print(f"rejected service error privacy mutation: {name}")
