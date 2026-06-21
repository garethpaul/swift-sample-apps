#!/usr/bin/env sh
set -eu
PATH=/usr/bin:/bin
export PATH

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && /bin/pwd -P)
TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/swift-samples-root-control-XXXXXX")
trap 'rm -rf "$TEMP_ROOT"' EXIT HUP INT TERM
unset MAKEFILES MAKEFILE_LIST MAKEFLAGS MFLAGS MAKEOVERRIDES ROOT SHELL

CONTROL_DIR="$TEMP_ROOT/control"
CHECKOUT="$TEMP_ROOT/swift samples' [gate] \"quoted\" \`touch SWIFT_SAMPLES_BACKTICK_MARKER\`"
ATTACKER_ROOT="$TEMP_ROOT/attacker-root"
COMMAND_LOG="$TEMP_ROOT/commands.log"
FAKE_SHELL_LOG="$TEMP_ROOT/fake-shell.log"
mkdir -p "$CONTROL_DIR" "$CHECKOUT/scripts" "$ATTACKER_ROOT"
CONTROL_DIR=$(CDPATH= cd -- "$CONTROL_DIR" && /bin/pwd -P)
CHECKOUT=$(CDPATH= cd -- "$CHECKOUT" && /bin/pwd -P)
MAKEFILE="$CHECKOUT/Makefile"
cp "$ROOT_DIR/Makefile" "$MAKEFILE"

FAKE_PYTHON="$TEMP_ROOT/trusted python's \"quoted\" \`touch SWIFT_SAMPLES_PYTHON_MARKER\` \$literal"
FAKE_XCODEBUILD="$TEMP_ROOT/trusted xcodebuild's \"quoted\" \`touch SWIFT_SAMPLES_XCODE_MARKER\` \$literal"
FAKE_SWIFTC="$TEMP_ROOT/trusted swiftc's \"quoted\" \`touch SWIFT_SAMPLES_SWIFTC_MARKER\` \$literal"
for tool in "$FAKE_PYTHON" "$FAKE_XCODEBUILD" "$FAKE_SWIFTC"; do
  cat >"$tool" <<'EOF'
#!/bin/sh
printf '%s|%s|%s\n' "$PWD" "$0" "$*" >> "$SWIFT_SAMPLES_COMMAND_LOG"
EOF
  chmod +x "$tool"
done

cat >"$CHECKOUT/scripts/test-background-selection.sh" <<'EOF'
#!/bin/sh
printf '%s|selection-runner|%s\n' "$PWD" "$SWIFTC" >> "$SWIFT_SAMPLES_COMMAND_LOG"
EOF
chmod +x "$CHECKOUT/scripts/test-background-selection.sh"
cat >"$CHECKOUT/scripts/test-makefile-root.sh" <<'EOF'
#!/bin/sh
printf '%s|%s|root-test\n' "$PWD" "$0" >> "$SWIFT_SAMPLES_COMMAND_LOG"
EOF
chmod +x "$CHECKOUT/scripts/test-makefile-root.sh"

FAKE_SHELL="$TEMP_ROOT/fake-shell"
cat >"$FAKE_SHELL" <<EOF
#!/bin/sh
printf '%s\n' invoked >> '$FAKE_SHELL_LOG'
exec /bin/sh "\$@"
EOF
chmod +x "$FAKE_SHELL"

run_case() {
  target=$1 mode=$2
  rm -f "$COMMAND_LOG" "$FAKE_SHELL_LOG"
  output="$TEMP_ROOT/output"
  set +e
  case "$mode" in
    default) (cd "$CONTROL_DIR" && SWIFT_SAMPLES_COMMAND_LOG="$COMMAND_LOG" /usr/bin/make --no-print-directory --file "$MAKEFILE" PYTHON="$FAKE_PYTHON" XCODEBUILD="$FAKE_XCODEBUILD" SWIFTC="$FAKE_SWIFTC" "$target") >"$output" 2>&1 ;;
    command-root) (cd "$CONTROL_DIR" && SWIFT_SAMPLES_COMMAND_LOG="$COMMAND_LOG" /usr/bin/make --no-print-directory --file "$MAKEFILE" ROOT="$ATTACKER_ROOT" PYTHON="$FAKE_PYTHON" XCODEBUILD="$FAKE_XCODEBUILD" SWIFTC="$FAKE_SWIFTC" "$target") >"$output" 2>&1 ;;
    environment-root) (cd "$CONTROL_DIR" && ROOT="$ATTACKER_ROOT" SWIFT_SAMPLES_COMMAND_LOG="$COMMAND_LOG" /usr/bin/make --no-print-directory --file "$MAKEFILE" PYTHON="$FAKE_PYTHON" XCODEBUILD="$FAKE_XCODEBUILD" SWIFTC="$FAKE_SWIFTC" "$target") >"$output" 2>&1 ;;
    command-shell) (cd "$CONTROL_DIR" && SWIFT_SAMPLES_COMMAND_LOG="$COMMAND_LOG" /usr/bin/make --no-print-directory --file "$MAKEFILE" SHELL="$FAKE_SHELL" PYTHON="$FAKE_PYTHON" XCODEBUILD="$FAKE_XCODEBUILD" SWIFTC="$FAKE_SWIFTC" "$target") >"$output" 2>&1 ;;
    environment-shell) (cd "$CONTROL_DIR" && SHELL="$FAKE_SHELL" SWIFT_SAMPLES_COMMAND_LOG="$COMMAND_LOG" /usr/bin/make --no-print-directory --file "$MAKEFILE" PYTHON="$FAKE_PYTHON" XCODEBUILD="$FAKE_XCODEBUILD" SWIFTC="$FAKE_SWIFTC" "$target") >"$output" 2>&1 ;;
  esac
  status=$?
  set -e
  if [ "$status" -ne 0 ]; then cat "$output" >&2; exit "$status"; fi
  [ ! -e "$FAKE_SHELL_LOG" ]
  [ ! -e "$ATTACKER_ROOT/scripts/check-swift-samples.py" ]
  grep -Fq "$CHECKOUT" "$COMMAND_LOG"
}

targets='build check lint native-test root-test test verify'
modes='default command-root environment-root command-shell environment-shell'
executed=0
for target in $targets; do
  for mode in $modes; do
    run_case "$target" "$mode"
    executed=$((executed + 1))
  done
done
[ "$executed" -eq 35 ]

rm -f "$COMMAND_LOG"
(cd "$CONTROL_DIR" && SWIFT_SAMPLES_COMMAND_LOG="$COMMAND_LOG" /usr/bin/make --no-print-directory --file "$MAKEFILE" PYTHON="$FAKE_PYTHON" XCODEBUILD="$FAKE_XCODEBUILD" SWIFTC="$FAKE_SWIFTC" check) >/dev/null 2>&1
grep -Fq "$FAKE_PYTHON" "$COMMAND_LOG"
grep -Fq "$FAKE_XCODEBUILD" "$COMMAND_LOG"
grep -Fq "$FAKE_SWIFTC" "$COMMAND_LOG"
for marker in SWIFT_SAMPLES_BACKTICK_MARKER SWIFT_SAMPLES_PYTHON_MARKER SWIFT_SAMPLES_XCODE_MARKER SWIFT_SAMPLES_SWIFTC_MARKER; do
  [ ! -e "$CONTROL_DIR/$marker" ]
done

MAKE_SYNTAX_MARKER="$TEMP_ROOT/python-make-syntax-ran"
MALICIOUS_PYTHON="\$(shell /usr/bin/touch '$MAKE_SYNTAX_MARKER')"
if (cd "$CONTROL_DIR" && /usr/bin/make --no-print-directory --file "$MAKEFILE" "PYTHON=$MALICIOUS_PYTHON" lint) >"$TEMP_ROOT/python-syntax.out" 2>&1; then exit 1; fi
[ ! -e "$MAKE_SYNTAX_MARKER" ]

if (cd "$CONTROL_DIR" && /usr/bin/make --no-print-directory --file "$MAKEFILE" MAKEFILE_LIST=/tmp/untrusted check) >"$TEMP_ROOT/command-list.out" 2>&1; then exit 1; fi
grep -Fq "MAKEFILE_LIST must not be overridden" "$TEMP_ROOT/command-list.out"
if (cd "$CONTROL_DIR" && MAKEFILE_LIST=/tmp/untrusted /usr/bin/make --environment-overrides --no-print-directory --file "$MAKEFILE" check) >"$TEMP_ROOT/environment-list.out" 2>&1; then exit 1; fi
grep -Fq "MAKEFILE_LIST must not be overridden" "$TEMP_ROOT/environment-list.out"

PRELOADED="$TEMP_ROOT/preloaded.mk"
PRELOAD_MARKER="$TEMP_ROOT/preload-startup-ran"
printf '%s\n' "\$(shell /usr/bin/touch '$PRELOAD_MARKER')" >"$PRELOADED"
if (cd "$CONTROL_DIR" && MAKEFILES="$PRELOADED" /usr/bin/make --no-print-directory --file "$MAKEFILE" check) >"$TEMP_ROOT/preloaded.out" 2>&1; then exit 1; fi
grep -Fq "MAKEFILES must be empty" "$TEMP_ROOT/preloaded.out"
[ -e "$PRELOAD_MARKER" ]

EARLIER="$TEMP_ROOT/earlier.mk"
EARLIER_MARKER="$TEMP_ROOT/earlier-startup-ran"
printf '%s\n' "\$(shell /usr/bin/touch '$EARLIER_MARKER')" >"$EARLIER"
if (cd "$CONTROL_DIR" && /usr/bin/make --no-print-directory --file "$EARLIER" --file "$MAKEFILE" check) >"$TEMP_ROOT/multiple.out" 2>&1; then exit 1; fi
grep -Fq "repository Makefile path could not be resolved" "$TEMP_ROOT/multiple.out"
[ -e "$EARLIER_MARKER" ]

for flag in -n --just-print --dry-run --recon -t --touch -q --question -i --ignore-errors; do
  if (cd "$CONTROL_DIR" && /usr/bin/make "$flag" --no-print-directory --file "$MAKEFILE" check) >"$TEMP_ROOT/flag.out" 2>&1; then exit 1; fi
  grep -Fq "non-executing or error-ignoring MAKEFLAGS are not supported" "$TEMP_ROOT/flag.out"
done

printf '%s\n' "Makefile root tests passed: 35 executed target/authority cases, 1 literal-dollar tool case, 1 raw tool Make-syntax rejection, 2 MAKEFILE_LIST rejections, 2 contained startup-boundary cases, and 10 mode-flag rejections"
