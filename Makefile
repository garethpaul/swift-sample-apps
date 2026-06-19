.PHONY: build check contract-test lint native-test test verify

override SHELL := /bin/sh
override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
override UNAME_S := $(shell /usr/bin/uname -s 2>/dev/null || /bin/uname -s 2>/dev/null || uname -s)
override PYTHON := $(shell "$(ROOT)/scripts/resolve-trusted-tools.sh" python 2>/dev/null)
override XCODEBUILD := $(shell "$(ROOT)/scripts/resolve-trusted-tools.sh" xcodebuild 2>/dev/null)
override SWIFTC := $(shell "$(ROOT)/scripts/resolve-trusted-tools.sh" swiftc 2>/dev/null)
CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj
REQUIRE_PYTHON = if [ -z "$(PYTHON)" ]; then printf '%s\n' "trusted Python 3.9+ unavailable" >&2; exit 1; fi

lint:
	@$(REQUIRE_PYTHON)
	"$(PYTHON)" "$(ROOT)/scripts/check-swift-samples.py" --mode hygiene

test:
	@$(REQUIRE_PYTHON)
	"$(PYTHON)" "$(ROOT)/scripts/check-swift-samples.py" --mode samples
	"$(ROOT)/scripts/test-background-selection.sh"

native-test:
	@if [ "$(UNAME_S)" != "Darwin" ]; then \
		echo "xcodebuild unavailable on non-Darwin; skipping native background switcher tests"; \
		exit 0; \
	fi; \
	if [ -z "$(XCODEBUILD)" ]; then \
		echo "trusted xcodebuild unavailable" >&2; \
		exit 1; \
	fi
	"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=latest' CODE_SIGNING_ALLOWED=NO test

build: lint
	@if [ "$(UNAME_S)" != "Darwin" ]; then \
		echo "xcodebuild unavailable on non-Darwin; static sample checks completed"; \
		exit 0; \
	fi; \
	if [ -z "$(XCODEBUILD)" ]; then \
		echo "trusted xcodebuild unavailable" >&2; \
		exit 1; \
	fi
	"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -target background_switcher -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build

contract-test:
	@$(REQUIRE_PYTHON)
	cd "$(ROOT)" && "$(PYTHON)" -m unittest Tests/test_background_selection_execution_contract.py

verify: lint test native-test build

check: verify contract-test
