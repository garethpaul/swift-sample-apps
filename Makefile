.PHONY: build check lint native-test test verify

override SHELL := /bin/sh
override PYTHON := $(firstword $(wildcard /usr/bin/python3 /usr/local/bin/python3))
override TRUSTED_DEVELOPER_DIR := $(shell if [ -x /usr/bin/xcode-select ]; then /usr/bin/xcode-select -p 2>/dev/null; fi)
override XCODEBUILD := $(shell if [ -n "$(TRUSTED_DEVELOPER_DIR)" ] && [ -x /usr/bin/xcrun ]; then tool=$$(DEVELOPER_DIR="$(TRUSTED_DEVELOPER_DIR)" /usr/bin/xcrun --find xcodebuild 2>/dev/null); if [ "$$tool" = "$(TRUSTED_DEVELOPER_DIR)/usr/bin/xcodebuild" ]; then printf '%s\n' "$$tool"; fi; fi)
override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj

ifeq ($(PYTHON),)
$(error trusted Python 3 is unavailable)
endif

lint:
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode hygiene

test::
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode samples
	"$(ROOT)/scripts/test-background-selection.sh"
	@if [ "$${BACKGROUND_CONTRACT_MUTATION:-0}" != "1" ]; then \
		$(PYTHON) "$(ROOT)/Tests/test_background_selection_execution_contract.py" -v; \
	fi

native-test:
	@if [ -n "$(XCODEBUILD)" ] && [ -x "$(XCODEBUILD)" ]; then \
		DEVELOPER_DIR="$(TRUSTED_DEVELOPER_DIR)" "$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=latest' CODE_SIGNING_ALLOWED=NO test; \
	elif [ "$$(/usr/bin/uname -s 2>/dev/null || uname -s)" = Darwin ]; then \
		echo "trusted xcodebuild unavailable" >&2; \
		exit 1; \
	else \
		echo "xcodebuild unavailable; skipping native background switcher tests"; \
	fi

build: lint
	@if [ -n "$(XCODEBUILD)" ] && [ -x "$(XCODEBUILD)" ]; then \
		DEVELOPER_DIR="$(TRUSTED_DEVELOPER_DIR)" "$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -target background_switcher -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	elif [ "$$(/usr/bin/uname -s 2>/dev/null || uname -s)" = Darwin ]; then \
		echo "trusted xcodebuild unavailable" >&2; \
		exit 1; \
	else \
		echo "xcodebuild not found; static sample checks completed"; \
	fi

verify: lint test native-test build

check: verify
