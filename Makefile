init:
	pip install -r python/requirements/requirements-dev.txt
	pre-commit install
	pre-commit install --hook-type commit-msg

init-requirements:
			pip install pixxel-datatypes -r python/requirements/requirements-dev.txt

package:
	make build/package

build/package:
	pip install build
	python -m build ./python

python-test:
	cd python; pytest -vv

test:
	go test ./...
	cd python; pytest -vv

test-go:
	go test $(shell go list ./... | grep -v 'registry')

test-python:
	cd python; pytest -vv
	
test-registry:
	cd registry; go test ./...

.PHONY: docs

spell-check-docs:
	codespell mkdocs/docs/*.md

build-docs:
		cd mkdocs; mkdocs build

build-docs-docker-image: 
		sudo DOCKER_BUILDKIT=1 docker build \
		-t clay-docs \
		-f clay-docs.Dockerfile \
		.

serve-docs:
		cd mkdocs; mkdocs serve

docs:
	cd mkdocs; mkdocs build -v; mkdocs serve;

format:
		@cd python; \
		echo "Linting with ruff..."; \
		ruff check; \
		echo "Formatting with ruff..."; \
		ruff format . ; \
		pre-commit run

pre-commit:
		pre-commit run


.PHONY: go-binaries

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

test-with-runner:
	// TODO:To be added once we test opensource runner with clay
