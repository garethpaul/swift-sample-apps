#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)

trap 'exit 129' 1
trap 'exit 130' 2
trap 'exit 143' 15

PYTHON=$("$ROOT_DIR/scripts/resolve-trusted-tools.sh" python) || {
  printf '%s\n' "trusted Python 3.9+ unavailable" >&2
  exit 1
}

exec "$PYTHON" "$ROOT_DIR/scripts/verify-background-selection.py"
