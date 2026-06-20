#!/bin/sh
set -eu

SCRIPT_DIR=${0%/*}
if [ "$SCRIPT_DIR" = "$0" ]; then
  SCRIPT_DIR=.
fi
ROOT_DIR=$(CDPATH=; cd -- "$SCRIPT_DIR/.." && pwd -P)
SWIFTC=$(/bin/sh "$ROOT_DIR/scripts/resolve-trusted-tools.sh" swiftc)
SDKROOT=
if [ -x /usr/bin/xcrun ]; then
  SDKROOT=$(/usr/bin/xcrun --show-sdk-path --sdk macosx 2>/dev/null || true)
fi

BUILD_DIR=$(/usr/bin/mktemp -d "${TMPDIR:-/tmp}/background-selection-tests.XXXXXX")
cleanup() {
  /bin/rm -rf -- "$BUILD_DIR"
}
trap cleanup 0
trap 'exit 129' 1
trap 'exit 130' 2
trap 'exit 143' 15

if [ -n "$SDKROOT" ]; then
  "$SWIFTC" -sdk "$SDKROOT" \
    "$ROOT_DIR/background_switcher/background_switcher/BackgroundSelection.swift" \
    "$ROOT_DIR/Tests/BackgroundSelectionTests/main.swift" \
    -o "$BUILD_DIR/background-selection-tests"
else
  "$SWIFTC" \
    "$ROOT_DIR/background_switcher/background_switcher/BackgroundSelection.swift" \
    "$ROOT_DIR/Tests/BackgroundSelectionTests/main.swift" \
    -o "$BUILD_DIR/background-selection-tests"
fi
"$BUILD_DIR/background-selection-tests"

printf '%s\n' "Background selection Swift tests passed."
