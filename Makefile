.PHONY: analyze-debug analyze-release build build-debug build-release check contract-test lint native-test native-test-release preflight require-python test verify

override SHELL := /bin/sh
.SHELLFLAGS := -eu -c
override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
override TRUSTED_TOOLS := $(ROOT)/scripts/resolve-trusted-tools.sh
override PYTHON := $(shell /bin/sh "$(TRUSTED_TOOLS)" python 2>/dev/null || true)
override SWIFTC := $(shell /bin/sh "$(TRUSTED_TOOLS)" swiftc 2>/dev/null || true)
override XCODEBUILD := $(shell /bin/sh "$(TRUSTED_TOOLS)" xcodebuild 2>/dev/null || true)
CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj
override PREFLIGHT_NONCE := $(shell /usr/bin/uuidgen 2>/dev/null || /usr/bin/openssl rand -hex 16)
override PREFLIGHT_RECEIPT := /tmp/swift-sample-apps-preflight-$(PREFLIGHT_NONCE)

require-python:
	@if [ -z "$(PYTHON)" ]; then \
		printf '%s\n' "trusted Python 3 not found in reviewed absolute locations" >&2; \
		exit 1; \
	fi

lint: require-python
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode hygiene

preflight: lint
	$(PYTHON) "$(ROOT)/scripts/verify-trusted-candidate.py" --mode all
	@/usr/bin/printf '%s\n' "$(PREFLIGHT_NONCE)" > "$(PREFLIGHT_RECEIPT).tmp"
	@/bin/mv -f "$(PREFLIGHT_RECEIPT).tmp" "$(PREFLIGHT_RECEIPT)"

test: preflight
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode samples
	@if [ -n "$(SWIFTC)" ]; then \
		/bin/sh "$(ROOT)/scripts/test-background-selection.sh"; \
	else \
		echo "trusted swiftc unavailable; skipping background selection Swift tests"; \
	fi

contract-test: preflight
	$(PYTHON) "$(ROOT)/scripts/run-contract-tests.py"

native-test: preflight
	@test "$$(/bin/cat "$(PREFLIGHT_RECEIPT)")" = "$(PREFLIGHT_NONCE)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=latest' CODE_SIGNING_ALLOWED=NO test; \
	else \
		echo "trusted xcodebuild unavailable; skipping native background switcher tests"; \
	fi

native-test-release: preflight
	@test "$$(/bin/cat "$(PREFLIGHT_RECEIPT)")" = "$(PREFLIGHT_NONCE)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Release -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=latest' CODE_SIGNING_ALLOWED=NO ENABLE_TESTABILITY=YES test; \
	else \
		echo "trusted xcodebuild unavailable; skipping Release native tests"; \
	fi

build: preflight
	@test "$$(/bin/cat "$(PREFLIGHT_RECEIPT)")" = "$(PREFLIGHT_NONCE)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -target background_switcher -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "trusted xcodebuild not found; static sample checks completed"; \
	fi

build-debug: preflight
	@test "$$(/bin/cat "$(PREFLIGHT_RECEIPT)")" = "$(PREFLIGHT_NONCE)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "trusted xcodebuild unavailable; skipping Debug build"; \
	fi

build-release: preflight
	@test "$$(/bin/cat "$(PREFLIGHT_RECEIPT)")" = "$(PREFLIGHT_NONCE)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "trusted xcodebuild unavailable; skipping Release build"; \
	fi

analyze-debug: preflight
	@test "$$(/bin/cat "$(PREFLIGHT_RECEIPT)")" = "$(PREFLIGHT_NONCE)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO analyze; \
	else \
		echo "trusted xcodebuild unavailable; skipping Debug analysis"; \
	fi

analyze-release: preflight
	@test "$$(/bin/cat "$(PREFLIGHT_RECEIPT)")" = "$(PREFLIGHT_NONCE)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO analyze; \
	else \
		echo "trusted xcodebuild unavailable; skipping Release analysis"; \
	fi

verify: preflight test contract-test native-test build

check: verify
