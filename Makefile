.PHONY: build check lint test verify

PYTHON ?= python3
XCODEBUILD ?= xcodebuild

lint:
	$(PYTHON) scripts/check-swift-samples.py --mode hygiene

test:
	$(PYTHON) scripts/check-swift-samples.py --mode samples

build: lint
	@if command -v "$(XCODEBUILD)" >/dev/null 2>&1; then \
		for project in */*.xcodeproj; do \
			target=$$(basename "$$project" .xcodeproj); \
			"$(XCODEBUILD)" -project "$$project" -target "$$target" -sdk iphonesimulator CODE_SIGNING_ALLOWED=NO build; \
		done; \
	else \
		echo "xcodebuild not found; static sample checks completed"; \
	fi

verify: lint test build

check: verify
