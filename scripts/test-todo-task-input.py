#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-swift-samples.py"
TASK_MANAGER = ROOT / "todo-list/todo-list/TaskManager.swift"
ADD_CONTROLLER = ROOT / "todo-list/todo-list/SecondViewController.swift"


MUTATIONS = (
    (
        TASK_MANAGER,
        "func addTask(name: String , desc:String) -> Bool",
        "func addTask(name: String , desc:String)",
        "acceptance result",
    ),
    (
        TASK_MANAGER,
        "name.stringByTrimmingCharactersInSet(NSCharacterSet.whitespaceAndNewlineCharacterSet()).isEmpty",
        "name.isEmpty",
        "whitespace-only guard",
    ),
    (
        TASK_MANAGER,
        "        tasks.append(task(name: name, desc: desc))\n        return true",
        "        return true\n        tasks.append(task(name: name, desc: desc))",
        "append before success",
    ),
    (
        TASK_MANAGER,
        "        if name.stringByTrimmingCharactersInSet(NSCharacterSet.whitespaceAndNewlineCharacterSet()).isEmpty {\n"
        "            return false\n"
        "        }",
        "        if name.stringByTrimmingCharactersInSet(NSCharacterSet.whitespaceAndNewlineCharacterSet()).isEmpty {\n"
        "            return true\n"
        "        }",
        "blank rejection",
    ),
    (
        ADD_CONTROLLER,
        "        if taskMngr.addTask(txtTask.text, desc: txtDesc.text) {",
        "        taskMngr.addTask(txtTask.text, desc: txtDesc.text)",
        "accepted UI guard",
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
    raise SystemExit("baseline todo input contract failed: " + baseline.stdout.strip())

for path, original, replacement, name in MUTATIONS:
    source = path.read_text(encoding="utf-8")
    if source.count(original) != 1:
        raise SystemExit(f"mutation anchor changed: {name}")
    try:
        path.write_text(source.replace(original, replacement, 1), encoding="utf-8")
        result = run_checker()
        if result.returncode == 0:
            raise SystemExit(f"todo input mutation unexpectedly passed: {name}")
    finally:
        path.write_text(source, encoding="utf-8")
    print(f"rejected todo input mutation: {name}")
