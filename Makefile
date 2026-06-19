.PHONY: build check lint native-test test verify

PYTHON ?= python3
XCODEBUILD ?= xcodebuild
override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj

lint:
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode hygiene

test::
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode samples
	PYTHON="$(PYTHON)" "$(ROOT)/scripts/test-background-selection.sh"
	@if [ "$${BACKGROUND_CONTRACT_MUTATION:-0}" != "1" ]; then \
		$(PYTHON) "$(ROOT)/Tests/test_background_selection_execution_contract.py" -v; \
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
