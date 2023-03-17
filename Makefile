init:
	pip install -r python/requirements/requirements-dev.txt
	pre-commit install

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
						--username ${RAMEN_REGISTRY_NAME} \
						--password ${RAMEN_REGISTRY_PASS} \
						--verbose \
						--skip-existing \
						dist/*


test:
	cd python; pytest -vv

.PHONY: docs

build-docs:
		cd python/mkdocs; mkdocs build

serve-docs:
		cd python/mkdocs; mkdocs serve
