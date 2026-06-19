.PHONY: build check lint native-test test verify

PYTHON ?= python3
XCODEBUILD ?= xcodebuild
SWIFTC ?= swiftc
override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj

lint:
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode hygiene

test:
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode samples
	@if command -v "$(SWIFTC)" >/dev/null 2>&1; then \
		SWIFTC="$(SWIFTC)" "$(ROOT)/scripts/test-background-selection.sh"; \
	else \
		echo "swiftc unavailable; skipping background selection Swift tests"; \
	fi

native-test:
	@if command -v "$(XCODEBUILD)" >/dev/null 2>&1; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=latest' CODE_SIGNING_ALLOWED=NO test; \
	else \
		echo "xcodebuild unavailable; skipping native background switcher tests"; \
	fi

build: lint
	@if command -v "$(XCODEBUILD)" >/dev/null 2>&1; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -target background_switcher -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "xcodebuild not found; static sample checks completed"; \
	fi

verify: lint test native-test build

check: verify
