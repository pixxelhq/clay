init:
	pip install -r python/requirements/requirements-dev.txt
	pre-commit install
	pre-commit install --hook-type commit-msg

init-requirements:
	pip install -r python/requirements/requirements-dev.txt

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

.PHONY: docs

spell-check-docs:
	codespell mkdocs/docs/*.md

build-docs:
		cd mkdocs; mkdocs build

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
	sudo docker compose -f examples/runner/docker-compose.yml up -d --build minio
	echo 'Waiting for Minio to be ready...'
	sleep 10
	sudo docker compose -f examples/runner/docker-compose.yml up -d --build createbucket && sleep 5
	sudo docker-compose -f examples/runner/docker-compose.yml build --build-arg EXECUTOR='kube' model
	cd examples/runner && sudo docker-compose run -e EXECUTOR='kube' model "$$(cat demo-test/sample_model_inputs.json)"

test-with-runnerv2:
	sudo docker compose -f examples/runner/docker-compose.yml up -d --build minio
	sudo docker-compose -f examples/runner/docker-compose.yml build --build-arg EXECUTOR='argo' model
	cd examples/runner && sudo docker-compose run -e EXECUTOR='argo' model

tear-down:
	cd examples/runner && sudo docker-compose down --volumes --remove-orphans
	rm -r examples/runner/minio_storage
