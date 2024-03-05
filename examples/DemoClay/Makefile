setup:
		if ! git rev-parse --git-dir > /dev/null 2>&1; then \
			echo "Initializing Git repository..."; \
			git init; \
		fi

		# Find pip / pip3 and install the requirements
		if command -v pip &> /dev/null; then \
			echo "Using pip at: $$(command -v pip)"; \
			pip install -r requirements-dev.txt -r requirements.txt; \
		elif command -v pip3 &> /dev/null; then \
			echo "Using pip3 at: $$(command -v pip3)"; \
			pip3 install -r requirements-dev.txt -r requirements.txt; \
		else \
			echo "Error: pip and pip3 are not installed"; \
		fi

		pre-commit install
		pre-commit install --hook-type commit-msg

validate:
		pytest -v
		pre-commit run --all-files

format:
		pre-commit run --all-files

test:
		pytest -v

clean:
		rm -rf *.egg-info
		rm -rf **/__pycache__
		rm -rf .pytest_cache

dockerfile:
		clay create dockerfile DemoClay/specifications/model_specification_dev.yaml DemoClay

generate-secrets:
		echo $$CODEARTIFACT_AUTH_TOKEN > 

clean-secrets:
		rm  

docker-image: generate-secrets
		sudo DOCKER_BUILDKIT=1 docker build \
		--secret id=CODEARTIFACT_AUTH_TOKEN,src= \
		--build-arg AWS_ENV_PROFILE=$(AWS_ENV_PROFILE) \
		-t democlay \
		-f Dockerfile \
		.
		$(MAKE) clean-secrets

test-docker-image:
		docker run democlay "$$(cat DemoClay/sample_model_inputs.json)"

test-docker-image-gpu:
		docker run --rm --runtime nvidia --gpus all DemoClay "$$(cat DemoClay/sample_model_inputs.json)"

package-and-test-model:
		@echo "Creating Dockerfile..."
		make dockerfile
		@echo "Building Docker Container / Image..."
		make docker-image
		@echo "Testing image with DemoClay/sample_model_inputs.json"
		make test-docker-image
