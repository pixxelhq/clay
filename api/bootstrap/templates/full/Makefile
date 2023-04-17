setup:
		if ! git rev-parse --git-dir > /dev/null 2>&1; then \
			echo "Initializing Git repository..."; \
			git init; \
		fi

		# Find pip / pip3 and install the requirements
		if command -v pip &> /dev/null; then \
			echo "Using pip at: $$(command -v pip)"; \
			pip install -r requirements.txt; \
		elif command -v pip3 &> /dev/null; then \
			echo "Using pip3 at: $$(command -v pip3)"; \
			pip3 install -r requirements.txt; \
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
		clay create dockerfile specifications/model_specification.yaml {{.ModelName}}

docker-image:
		docker build -t {{.ModelName | ToLower}} --secret id=GITLAB_TOKEN .

test-docker-image:
		docker run {{.ModelName | ToLower}} "$$(cat {{.ModelName}}/sample_model_inputs.json)"

package-and-test-model:
		@echo "Creating Dockerfile..."
		make dockerfile
		@echo "Building Docker Container / Image..."
		make docker-image
		@echo "Testing image with {{.ModelName}}/sample_model_inputs.json"
		make test-docker-image
