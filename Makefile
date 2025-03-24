init:
	pip install -r python/requirements/requirements-dev.txt
	pre-commit install
	pre-commit install --hook-type commit-msg

generate-secrets:
		aws codeartifact get-authorization-token --domain REDACTED-ARTIFACTORY --domain-owner REDACTED-AWS-ACCT --query authorizationToken --region us-east-2 --output text > CODEARTIFACT_AUTH_TOKEN.txt

clean-secrets:
		rm CODEARTIFACT_AUTH_TOKEN.txt

init-requirements:	generate-secrets
			pip install pixxel-datatypes==0.3.0 -r python/requirements/requirements-dev.txt --extra-index-url https://aws:$$(cat CODEARTIFACT_AUTH_TOKEN.txt)@REDACTED.d.codeartifact.us-east-2.amazonaws.com/pypi/python/simple/
			$(MAKE) clean-secrets

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

build-docs-docker-image: generate-secrets
		sudo DOCKER_BUILDKIT=1 docker build \
		--secret id=CODEARTIFACT_AUTH_TOKEN,src=CODEARTIFACT_AUTH_TOKEN.txt \
		--build-arg AWS_ENV_PROFILE=$(AWS_ENV_PROFILE) \
		-t clay-docs \
		-f clay-docs.Dockerfile \
		.
		$(MAKE) clean-secrets

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

test-with-runner: generate-secrets
	sudo docker compose -f examples/runner/docker-compose.yml up -d --build minio
	echo 'Waiting for Minio to be ready...'
	sleep 10
	sudo docker compose -f examples/runner/docker-compose.yml up -d --build createbucket && sleep 5
	sudo docker compose -f examples/runner/docker-compose.yml build --build-arg EXECUTOR='kube' model
	cd examples/runner && sudo docker compose run -e EXECUTOR='kube' -e FEATURE_FORCE_INPUT_TYPES_TO_V2='1' -e FEATURE_FORCE_OUTPUT_TYPES_TO_V2='1' \
	model "$$(cat demo-test/sample_model_inputs.json)"

test-with-runnerv2: generate-secrets
	sudo docker compose -f examples/runner/docker-compose.yml up -d --build minio
	echo 'Waiting for Minio to be ready...'
	sleep 10
	sudo docker compose -f examples/runner/docker-compose.yml up -d --build createbucket && sleep 5
	sudo docker compose -f examples/runner/docker-compose.yml build --build-arg EXECUTOR='argo' model
	cd examples/runner && sudo docker compose run -e EXECUTOR='argo' -e FEATURE_FORCE_INPUT_TYPES_TO_V2='1' -e FEATURE_FORCE_OUTPUT_TYPES_TO_V2='1' \
	-e ARGO_TEMPLATE='{"name":"cdy","inputs":[{"name":"some_raster","value":"s3://testinputs/inputs/some_raster/some_raster.tif","stac_url": "https://platform-gateway.example.com/atlas/stac/collections/62288e91-4372-4806-8b11-a2d9aee6e84f/items/2025_03_10_stac"}, {"name":"some_vector","value":"s3://testinputs/inputs/some_vector/some_vector.geojson"}]}' model
	$(MAKE) clean-secrets

tear-down:
	cd examples/runner && sudo docker-compose down --volumes --remove-orphans
	rm -r examples/runner/minio_storage
