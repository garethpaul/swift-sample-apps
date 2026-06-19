.PHONY: build check lint test verify

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

build: lint
	@if command -v "$(XCODEBUILD)" >/dev/null 2>&1; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -target background_switcher -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "xcodebuild not found; static sample checks completed"; \
	fi

verify: lint test build

check: verify
