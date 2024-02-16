init:
	pip install -r python/requirements/requirements-dev.txt
	pre-commit install
	pre-commit install --hook-type commit-msg

package:
		make build/package
		make push/package

build/package:
		pip install build
		python -m build ./python

push/package:
		pip install twine
		python -m twine upload \
						--repository-url https://gitlab.com/api/v4/projects/38508365/packages/pypi \
						--username ${CLAY_REGISTRY_NAME} \
						--password ${CLAY_REGISTRY_PASS} \
						--verbose \
						--skip-existing \
						python/dist/*


test:
	go test ./...
	cd python; pytest -vv

.PHONY: docs

build-docs:
		cd mkdocs; mkdocs build

serve-docs:
		cd mkdocs; mkdocs serve

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
