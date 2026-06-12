.PHONY: build check lint test verify

PYTHON ?= python3
XCODEBUILD ?= xcodebuild
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj

lint:
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode hygiene

test:
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode samples

build: lint
	@if command -v "$(XCODEBUILD)" >/dev/null 2>&1; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -target background_switcher -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "xcodebuild not found; static sample checks completed"; \
	fi

verify: lint test build

check: verify
