init:
	pip install -r requirements/requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -vv

.PHONY: docs

docs:
		cd sphinx; make clean; make html
