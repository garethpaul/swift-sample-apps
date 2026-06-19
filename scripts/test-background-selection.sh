#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=
for candidate in /usr/bin/python3 /usr/local/bin/python3; do
  if [ -x "$candidate" ]; then
    PYTHON=$candidate
    break
  fi
done

if [ -z "$PYTHON" ]; then
  printf '%s\n' 'trusted Python 3 is unavailable' >&2
  exit 1
fi

exec "$PYTHON" "$ROOT_DIR/scripts/verify-background-selection.py" --root "$ROOT_DIR"
