.DEFAULT_GOAL := check
.PHONY: __repository-make-authority build check lint native-test root-test test verify
.SECONDEXPANSION:

PYTHON ?= python3
XCODEBUILD ?= xcodebuild
SWIFTC ?= swiftc
override PYTHON := $(value PYTHON)
override XCODEBUILD := $(value XCODEBUILD)
override SWIFTC := $(value SWIFTC)
export PYTHON XCODEBUILD SWIFTC
override SHELL := /bin/sh
override .SHELLFLAGS := -c

ifneq ($(filter command line,$(origin MAKEFLAGS)),)
$(error MAKEFLAGS must not be overridden for repository verification)
endif
override REPOSITORY_MAKE_FIRST_FLAGS := $(firstword $(MAKEFLAGS))
ifneq ($(filter -%,$(REPOSITORY_MAKE_FIRST_FLAGS)),)
override REPOSITORY_MAKE_FIRST_FLAGS :=
endif
override REPOSITORY_MAKE_SHORT_FLAGS := $(REPOSITORY_MAKE_FIRST_FLAGS) $(filter-out --%,$(filter -%,$(MAKEFLAGS)))
ifneq ($(findstring n,$(REPOSITORY_MAKE_SHORT_FLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(findstring t,$(REPOSITORY_MAKE_SHORT_FLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(findstring q,$(REPOSITORY_MAKE_SHORT_FLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(findstring i,$(REPOSITORY_MAKE_SHORT_FLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(filter --just-print --dry-run --recon --touch --question --ignore-errors,$(MAKEFLAGS)),)
$(error non-executing or error-ignoring MAKEFLAGS are not supported for repository verification)
endif
ifneq ($(strip $(MAKEFILES)),)
$(error MAKEFILES must be empty; repository verification requires this Makefile to be loaded alone)
endif
override MAKEFILES :=
ifneq ($(origin MAKEFILE_LIST),file)
$(error MAKEFILE_LIST must not be overridden)
endif
override ROOT := $(shell path='$(subst ','"'"',$(value MAKEFILE_LIST))'; path=$$(printf '%s' "$$path" | /usr/bin/sed 's/^ //'); [ -f "$$path" ] || exit 1; directory=$$(/usr/bin/dirname -- "$$path"); CDPATH= cd -- "$$directory" && /bin/pwd -P)
export ROOT
ifeq ($(strip $(ROOT)),)
$(error repository Makefile path could not be resolved)
endif
override CANARY_PROJECT := $(ROOT)/background_switcher/background_switcher.xcodeproj
export CANARY_PROJECT

build check lint native-test root-test test verify: $$(if $$(filter file,$$(origin MAKEFILE_LIST)),,$$(error MAKEFILE_LIST must not be overridden))
build check lint native-test root-test test verify: $$(if $$(shell path=$$$$(/usr/bin/printf '%s' '$$(subst ','"'"',$$(MAKEFILE_LIST))' | /usr/bin/sed 's/^ //') && [ -f "$$$$path" ] && /usr/bin/printf '%s' ok),,$$(error repository Makefile must be loaded alone))
build check lint native-test root-test test verify: __repository-make-authority

__repository-make-authority::
	@:

lint:
	"$$PYTHON" "$$ROOT/scripts/check-swift-samples.py" --mode hygiene

test:
	"$$PYTHON" "$$ROOT/scripts/check-swift-samples.py" --mode samples
	@if command -v "$$SWIFTC" >/dev/null 2>&1; then \
		SWIFTC="$$SWIFTC" "$$ROOT/scripts/test-background-selection.sh"; \
	else \
		echo "swiftc unavailable; skipping background selection Swift tests"; \
	fi

native-test:
	@if command -v "$$XCODEBUILD" >/dev/null 2>&1; then \
		"$$XCODEBUILD" -project "$$CANARY_PROJECT" -scheme background_switcher -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 16 Pro,OS=latest' CODE_SIGNING_ALLOWED=NO test; \
	else \
		echo "xcodebuild unavailable; skipping native background switcher tests"; \
	fi

build: lint
	@if command -v "$$XCODEBUILD" >/dev/null 2>&1; then \
		"$$XCODEBUILD" -project "$$CANARY_PROJECT" -target background_switcher -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build; \
	else \
		echo "xcodebuild not found; static sample checks completed"; \
	fi

root-test:
	/bin/sh "$$ROOT/scripts/test-makefile-root.sh"

verify: root-test lint test native-test build

check: verify
