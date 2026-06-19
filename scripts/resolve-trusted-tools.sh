#!/usr/bin/env sh
set -eu

tool=${1:-}

resolve_python() {
  for candidate in \
    /Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 \
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13 \
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 \
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 \
    /Library/Frameworks/Python.framework/Versions/3.10/bin/python3.10 \
    /Library/Frameworks/Python.framework/Versions/3.9/bin/python3.9 \
    /opt/homebrew/bin/python3.14 \
    /opt/homebrew/bin/python3.13 \
    /opt/homebrew/bin/python3.12 \
    /opt/homebrew/bin/python3.11 \
    /opt/homebrew/bin/python3.10 \
    /opt/homebrew/bin/python3.9 \
    /usr/local/bin/python3.14 \
    /usr/local/bin/python3.13 \
    /usr/local/bin/python3.12 \
    /usr/local/bin/python3.11 \
    /usr/local/bin/python3.10 \
    /usr/local/bin/python3.9 \
    /usr/bin/python3
  do
    if [ -x "$candidate" ] && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

resolve_xcodebuild() {
  [ "$(/usr/bin/uname -s)" = "Darwin" ] || return 1
  [ -x /usr/bin/xcode-select ] && [ -x /usr/bin/xcrun ] || return 1
  developer_dir=$(/usr/bin/xcode-select -p 2>/dev/null) || return 1
  candidate=$(/usr/bin/xcrun --find xcodebuild 2>/dev/null) || return 1
  [ "$candidate" = "$developer_dir/usr/bin/xcodebuild" ] || return 1
  [ -x "$candidate" ] || return 1
  printf '%s\n' "$candidate"
}

resolve_swiftc() {
  if [ "$(/usr/bin/uname -s)" = "Darwin" ]; then
    [ -x /usr/bin/xcode-select ] && [ -x /usr/bin/xcrun ] || return 1
    developer_dir=$(/usr/bin/xcode-select -p 2>/dev/null) || return 1
    candidate=$(/usr/bin/xcrun --find swiftc 2>/dev/null) || return 1
    prefix="$developer_dir/Toolchains/"
    suffix="/usr/bin/swiftc"
    [ "${candidate#"$prefix"}" != "$candidate" ] || return 1
    [ "${candidate%"$suffix"}" != "$candidate" ] || return 1
    [ -x "$candidate" ] || return 1
    printf '%s\n' "$candidate"
    return 0
  fi

  for candidate in /usr/bin/swiftc /usr/local/bin/swiftc /opt/swift/usr/bin/swiftc /opt/homebrew/bin/swiftc
  do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

case "$tool" in
  python)
    resolve_python
    ;;
  xcodebuild)
    resolve_xcodebuild
    ;;
  swiftc)
    resolve_swiftc
    ;;
  *)
    printf '%s\n' "usage: resolve-trusted-tools.sh python|xcodebuild|swiftc" >&2
    exit 64
    ;;
esac
