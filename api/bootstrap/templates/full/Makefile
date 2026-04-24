setup:
	@if ! git rev-parse --git-dir > /dev/null 2>&1; then \
		echo "Initializing Git repository..."; \
		git init; \
	fi
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	uv pip install -r requirements.txt
	pre-commit install
	pre-commit install --hook-type commit-msg

format:
	ruff check --fix .
	ruff format .

lint:
	ruff check .

clean:
	rm -rf *.egg-info build dist
