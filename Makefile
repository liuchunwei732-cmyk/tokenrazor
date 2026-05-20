.PHONY: install test clean build

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=tokenrazor

lint:
	ruff check tokenrazor/
	black --check tokenrazor/

format:
	black tokenrazor/
	ruff check --fix tokenrazor/

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .coverage htmlcov/

build: clean
	python3 -m build

run:
	python3 -m tokenrazor.cli prune $(ARGS)
