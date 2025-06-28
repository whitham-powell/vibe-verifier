.PHONY: install test test-coverage lint format clean build docs

# Default Python interpreter
PYTHON := python3

install:
	$(PYTHON) -m pip install -e .
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -e .
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install pytest pytest-cov pytest-mock

test:
	$(PYTHON) -m pytest tests/ -v

test-coverage:
	$(PYTHON) -m pytest tests/ --cov=src --cov-report=html --cov-report=term

test-unit:
	$(PYTHON) -m pytest tests/test_*.py -v -k "not integration"

test-integration:
	$(PYTHON) -m pytest tests/test_integration.py -v

lint:
	$(PYTHON) -m pylint src/
	$(PYTHON) -m flake8 src/
	$(PYTHON) -m mypy src/

format:
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m isort src/ tests/

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/
	rm -rf reports/

build:
	$(PYTHON) setup.py sdist bdist_wheel

docs:
	# Add documentation generation here if needed
	@echo "Documentation generation not yet implemented"

run-example:
	vibe-verifier tests/test_data/sample_repos/python_project

check: lint test
	@echo "All checks passed!"

help:
	@echo "Available targets:"
	@echo "  install       - Install the package and dependencies"
	@echo "  install-dev   - Install with development dependencies"
	@echo "  test          - Run all tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  test-unit     - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  lint          - Run linting tools"
	@echo "  format        - Format code with black and isort"
	@echo "  clean         - Remove build artifacts and cache"
	@echo "  build         - Build distribution packages"
	@echo "  check         - Run lint and tests"