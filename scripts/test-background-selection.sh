#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

exec "$PYTHON" "$ROOT_DIR/scripts/verify-background-selection.py" --root "$ROOT_DIR"
