#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-swift-samples.py"
DETAIL_CONTROLLER = ROOT / "swift-objects-example/swift-objects-example/DetailViewController.swift"


MUTATIONS = (
    (
        'if let image = UIImage(named: "swift-hero.png") {',
        'var image = UIImage(named: "swift-hero.png")',
        "optional image binding",
    ),
    (
        "                imageView.image = image\n                self.view.addSubview(imageView)",
        "                self.view.addSubview(imageView)",
        "bound image assignment",
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
    raise SystemExit("baseline swift objects image contract failed: " + baseline.stdout.strip())

for original, replacement, name in MUTATIONS:
    source = DETAIL_CONTROLLER.read_text(encoding="utf-8")
    if source.count(original) != 1:
        raise SystemExit(f"mutation anchor changed: {name}")
    try:
        DETAIL_CONTROLLER.write_text(source.replace(original, replacement, 1), encoding="utf-8")
        result = run_checker()
        if result.returncode == 0:
            raise SystemExit(f"swift objects image mutation unexpectedly passed: {name}")
    finally:
        DETAIL_CONTROLLER.write_text(source, encoding="utf-8")
    print(f"rejected swift objects image mutation: {name}")
