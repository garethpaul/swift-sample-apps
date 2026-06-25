#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-swift-samples.py"

MUTATIONS = (
    (
        ROOT / "basic-note-taker/basic-note-taker/NoteEditorViewController.swift",
        "protocol NoteEditorViewControllerDelegate: class",
        "protocol NoteEditorViewControllerDelegate",
        "class-bound delegate",
    ),
    (
        ROOT / "basic-note-taker/basic-note-taker/NoteEditorViewController.swift",
        "weak var delegate: NoteEditorViewControllerDelegate?",
        "var delegate: NoteEditorViewControllerDelegate?",
        "weak delegate",
    ),
    (
        ROOT / "basic-note-taker/basic-note-taker/NoteListViewController.swift",
        "    var notes: String[]",
        "    var editor: NoteEditorViewController?\n    var notes: String[]",
        "stored editor",
    ),
    (
        ROOT / "basic-note-taker/basic-note-taker/NoteListViewController.swift",
        """            selectedNote = indexPath.row
            let editor = NoteEditorViewController(note: selectedNoteText)""",
        """            let editor = NoteEditorViewController(note: selectedNoteText)
            selectedNote = indexPath.row""",
        "selection ordering",
    ),
)

for path, original, replacement, name in MUTATIONS:
    source = path.read_text(encoding="utf-8")
    if source.count(original) != 1:
        raise SystemExit(f"mutation anchor changed: {name}")
    try:
        path.write_text(source.replace(original, replacement, 1), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(CHECKER), "--mode", "samples"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.returncode == 0:
            raise SystemExit(f"note editor mutation unexpectedly passed: {name}")
    finally:
        path.write_text(source, encoding="utf-8")
    print(f"rejected note editor mutation: {name}")
