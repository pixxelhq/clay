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
	cd python; pytest -vv

.PHONY: docs

build-docs:
		cd mkdocs; mkdocs build

serve-docs:
		cd mkdocs; mkdocs serve

format:
		@cd python; \
		echo "Formatting with black..."; \
		black clay; \
		echo "Formatting with isort..."; \
		isort clay; \
		echo "Linting with flake8..."; \
		flake8 clay; \
		echo "Linting with mypy..."; \
		mypy clay; \

pre-commit:
		pre-commit run --all-files
