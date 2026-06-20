.PHONY: analyze-debug analyze-release build build-debug build-release candidate-check candidate-contract-test candidate-preflight candidate-test check contract-test external-trust lint native-test native-test-release preflight require-python test verify

override SHELL := /bin/sh
.SHELLFLAGS := -eu -c
override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
override TRUSTED_TOOLS := $(ROOT)/scripts/resolve-trusted-tools.sh
override PYTHON := $(shell /bin/sh "$(TRUSTED_TOOLS)" python 2>/dev/null || true)
override SWIFTC := $(shell /bin/sh "$(TRUSTED_TOOLS)" swiftc 2>/dev/null || true)
override XCODEBUILD := $(shell /bin/sh "$(TRUSTED_TOOLS)" xcodebuild 2>/dev/null || true)
override TRUSTED_ORACLE_PATH := $(if $(TRUSTED_ORACLE),$(abspath $(TRUSTED_ORACLE)),)
override TRUSTED_MANIFEST_PATH := $(if $(TRUSTED_MANIFEST),$(abspath $(TRUSTED_MANIFEST)),)
CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj
override PREFLIGHT_NONCE := $(shell /usr/bin/uuidgen 2>/dev/null || /usr/bin/openssl rand -hex 16)
override PREFLIGHT_RECEIPT := /tmp/swift-sample-apps-v12-preflight-$(PREFLIGHT_NONCE).json

require-python:
	@if [ -z "$(PYTHON)" ]; then \
		printf '%s\n' "trusted Python 3 not found in reviewed absolute locations" >&2; \
		exit 1; \
	fi

external-trust: require-python
	@if [ -z "$(TRUSTED_ORACLE_PATH)" ] || [ -z "$(TRUSTED_MANIFEST_PATH)" ] || [ -z "$(TRUSTED_ORACLE_SHA256)" ] || [ -z "$(TRUSTED_MANIFEST_SHA256)" ]; then \
		printf '%s\n' "external v12 oracle, manifest, and repository-owned digests are required" >&2; \
		exit 1; \
	fi
	@case "$(TRUSTED_ORACLE_PATH)" in "$(ROOT)"/*) printf '%s\n' "trusted oracle must be outside the candidate checkout" >&2; exit 1;; esac
	@case "$(TRUSTED_MANIFEST_PATH)" in "$(ROOT)"/*) printf '%s\n' "trusted manifest must be outside the candidate checkout" >&2; exit 1;; esac
	@test -f "$(TRUSTED_ORACLE_PATH)" -a ! -L "$(TRUSTED_ORACLE_PATH)"
	@test -f "$(TRUSTED_MANIFEST_PATH)" -a ! -L "$(TRUSTED_MANIFEST_PATH)"
	$(PYTHON) "$(TRUSTED_ORACLE_PATH)" verify --repository "$(ROOT)" --manifest "$(TRUSTED_MANIFEST_PATH)" --oracle-sha256 "$(TRUSTED_ORACLE_SHA256)" --manifest-sha256 "$(TRUSTED_MANIFEST_SHA256)" --receipt "$(PREFLIGHT_RECEIPT)"
	@test -s "$(PREFLIGHT_RECEIPT)"

lint: require-python
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode hygiene

candidate-preflight: lint
	$(PYTHON) "$(ROOT)/scripts/verify-trusted-candidate.py" --mode all

candidate-test: candidate-preflight
	$(PYTHON) "$(ROOT)/scripts/check-swift-samples.py" --mode samples
	@if [ -n "$(SWIFTC)" ]; then \
		/bin/sh "$(ROOT)/scripts/test-background-selection.sh"; \
	else \
		echo "trusted swiftc unavailable; skipping background selection Swift tests"; \
	fi

candidate-contract-test: candidate-preflight
	$(PYTHON) "$(ROOT)/scripts/run-contract-tests.py"

candidate-check: candidate-test candidate-contract-test

preflight: external-trust candidate-preflight

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
	@test -s "$(PREFLIGHT_RECEIPT)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=latest' CODE_SIGNING_ALLOWED=NO test; \
	else \
		echo "trusted xcodebuild unavailable; skipping native background switcher tests"; \
	fi

native-test-release: preflight
	@test -s "$(PREFLIGHT_RECEIPT)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Release -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=latest' CODE_SIGNING_ALLOWED=NO ENABLE_TESTABILITY=YES test; \
	else \
		echo "trusted xcodebuild unavailable; skipping Release native tests"; \
	fi

build: preflight
	@test -s "$(PREFLIGHT_RECEIPT)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -target background_switcher -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "trusted xcodebuild not found; static sample checks completed"; \
	fi

build-debug: preflight
	@test -s "$(PREFLIGHT_RECEIPT)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "trusted xcodebuild unavailable; skipping Debug build"; \
	fi

build-release: preflight
	@test -s "$(PREFLIGHT_RECEIPT)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "trusted xcodebuild unavailable; skipping Release build"; \
	fi

analyze-debug: preflight
	@test -s "$(PREFLIGHT_RECEIPT)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Debug -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO analyze; \
	else \
		echo "trusted xcodebuild unavailable; skipping Debug analysis"; \
	fi

analyze-release: preflight
	@test -s "$(PREFLIGHT_RECEIPT)"
	@if [ -n "$(XCODEBUILD)" ]; then \
		"$(XCODEBUILD)" -project "$(CANARY_PROJECT)" -scheme background_switcher -configuration Release -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO analyze; \
	else \
		echo "trusted xcodebuild unavailable; skipping Release analysis"; \
	fi

verify: preflight test contract-test native-test build

check: external-trust candidate-check native-test build
