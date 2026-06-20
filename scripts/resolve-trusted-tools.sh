#!/bin/sh
set -eu

tool=${1:-}

is_executable() {
  [ -n "$1" ] && [ -f "$1" ] && [ -x "$1" ]
}

is_absolute() {
  case "$1" in
    /*) return 0 ;;
    *) return 1 ;;
  esac
}

resolve_python() {
  for candidate in \
    /usr/bin/python3 \
    /opt/homebrew/bin/python3.14 \
    /opt/homebrew/bin/python3.13 \
    /opt/homebrew/bin/python3.12 \
    /opt/homebrew/bin/python3.11 \
    /opt/homebrew/bin/python3.10 \
    /opt/homebrew/bin/python3.9 \
    /Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 \
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 \
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 \
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 \
    /Library/Frameworks/Python.framework/Versions/3.10/bin/python3.10 \
    /Library/Frameworks/Python.framework/Versions/3.9/bin/python3.9 \
    /usr/local/bin/python3
  do
    if is_executable "$candidate" && "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
    then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

resolve_xcrun_tool() {
  requested_tool=$1
  if is_executable /usr/bin/xcrun; then
    resolved=$(/usr/bin/xcrun --find "$requested_tool" 2>/dev/null || true)
    if is_absolute "$resolved" && is_executable "$resolved"; then
      printf '%s\n' "$resolved"
      return 0
    fi
  fi
  return 1
}

resolve_swiftc() {
  if resolve_xcrun_tool swiftc; then
    return 0
  fi
  for candidate in /usr/bin/swiftc /usr/local/bin/swiftc; do
    if is_executable "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

resolve_xcodebuild() {
  if resolve_xcrun_tool xcodebuild; then
    return 0
  fi
  if is_executable /usr/bin/xcodebuild; then
    printf '%s\n' /usr/bin/xcodebuild
    return 0
  fi
  return 1
}

case "$tool" in
  sh)
    printf '%s\n' /bin/sh
    ;;
  python)
    resolve_python
    ;;
  swiftc)
    resolve_swiftc
    ;;
  xcodebuild)
    resolve_xcodebuild
    ;;
  *)
    printf '%s\n' "usage: $0 sh|python|swiftc|xcodebuild" >&2
    exit 2
    ;;
esac
