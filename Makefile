.PHONY: build check contract-test lint native-test require-python test verify

override SHELL := /bin/sh
.SHELLFLAGS := -eu -c
override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
override TRUSTED_TOOLS := $(ROOT)/scripts/resolve-trusted-tools.sh
override PYTHON := $(shell /bin/sh "$(TRUSTED_TOOLS)" python 2>/dev/null || true)
override SWIFTC := $(shell /bin/sh "$(TRUSTED_TOOLS)" swiftc 2>/dev/null || true)
override XCODEBUILD := $(shell /bin/sh "$(TRUSTED_TOOLS)" xcodebuild 2>/dev/null || true)
CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj

require-python:
	@if [ -z "$(PYTHON)" ]; then \
		printf '%s\n' "trusted Python 3 not found in reviewed absolute locations" >&2; \
		exit 1; \
	fi

lint: require-python
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode hygiene

test: require-python
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode samples
	@if [ -n "$(SWIFTC)" ]; then \
		/bin/sh "$(ROOT)/scripts/test-background-selection.sh"; \
	else \
		echo "trusted swiftc unavailable; skipping background selection Swift tests"; \
	fi

contract-test: lint
	$(PYTHON) "$(ROOT)/scripts/run-contract-tests.py"

native-test:
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=latest' CODE_SIGNING_ALLOWED=NO test; \
	else \
		echo "trusted xcodebuild unavailable; skipping native background switcher tests"; \
	fi

build: lint
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -target background_switcher -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "trusted xcodebuild not found; static sample checks completed"; \
	fi

verify: lint test contract-test native-test build

check: verify
