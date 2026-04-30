.PHONY: init init-requirements ensure-uv package build/package go-binaries \
	test test-go test-python test-registry test-integration test-with-runner \
	format pre-commit \
	spell-check-docs build-docs serve-docs docs

# --- Setup ---

ensure-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}

init: ensure-uv
	uv pip install -r python/requirements/requirements-dev.txt
	pre-commit install
	pre-commit install --hook-type commit-msg

init-requirements: ensure-uv
	uv pip install ./proto/python -r python/requirements/requirements-dev.txt

# --- Build / package ---

package:
	make build/package

build/package: ensure-uv
	uv pip install build
	python -m build ./python

go-binaries:
	$(eval PROJECT_NAME := clay)
	$(eval VERSION := $(shell cat python/clay/__version__.py | grep __VERSION__ | cut -d'"' -f2))
	@echo "Version: $(VERSION)"

	$(eval OUTPUT_DIR := ./bin)
	@echo "Cleaning up $(OUTPUT_DIR)..."
	@rm -rf $(OUTPUT_DIR)
	@mkdir -p $(OUTPUT_DIR)
	@echo "Binaries will be created in ./bin"

	$(eval OSX_ARCH := amd64 arm64)
	$(eval WINDOWS_ARCH := amd64)
	$(eval LINUX_ARCH := amd64 arm64)

	@echo "Building binaries for macOS..."
	@for ARCH in $(OSX_ARCH); do \
		GOOS=darwin GOARCH=$$ARCH go build -o $(OUTPUT_DIR)/$(PROJECT_NAME)-$(VERSION)-macosx-$$ARCH; \
	done

	@echo "Building binaries for Windows..."
	@GOOS=windows GOARCH=$(WINDOWS_ARCH) go build -o $(OUTPUT_DIR)/$(PROJECT_NAME)-$(VERSION)-windows-$(WINDOWS_ARCH).exe

	@echo "Building binaries for Linux..."
	@for ARCH in $(LINUX_ARCH); do \
		GOOS=linux GOARCH=$$ARCH go build -o $(OUTPUT_DIR)/$(PROJECT_NAME)-$(VERSION)-linux-$$ARCH; \
	done

# --- Tests ---

test:
	go test ./...
	cd python; pytest -vv
	cd proto/python; pytest -vv

test-go:
	go test $(shell go list ./... | grep -v 'registry')

test-python:
	cd python; pytest -vv
	cd proto/python; pytest -vv

test-registry:
	cd registry; go test ./...

test-integration:
	go test -tags=integration ./pkg/docker/...

# TODO: to be implemented once the repo is open-sourced and we can test clay
# against the open-source runner.
test-with-runner:
	@echo "test-with-runner is not yet implemented; pending open-source runner migration."
	@exit 1

# --- Format / lint ---

format:
	@cd python; \
	echo "Linting with ruff..."; \
	ruff check; \
	echo "Formatting with ruff..."; \
	ruff format . ; \
	pre-commit run

pre-commit:
	pre-commit run

# --- Docs ---

spell-check-docs:
	codespell mkdocs/docs/*.md

build-docs:
	cd mkdocs; mkdocs build

serve-docs:
	cd mkdocs; mkdocs serve

docs:
	cd mkdocs; mkdocs build -v; mkdocs serve;
