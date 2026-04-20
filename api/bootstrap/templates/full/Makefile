setup:
	@if ! git rev-parse --git-dir > /dev/null 2>&1; then \
		echo "Initializing Git repository..."; \
		git init; \
	fi
	@if command -v pip >/dev/null 2>&1; then \
		pip install -r requirements.txt; \
	elif command -v pip3 >/dev/null 2>&1; then \
		pip3 install -r requirements.txt; \
	else \
		echo "Error: neither pip nor pip3 is installed" >&2; \
		exit 1; \
	fi
	pre-commit install
	pre-commit install --hook-type commit-msg

format:
	ruff check --fix .
	ruff format .

lint:
	ruff check .

clean:
	rm -rf *.egg-info build dist
