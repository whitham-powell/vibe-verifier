.PHONY: install test test-coverage lint format clean build docs

# Default Python interpreter
PYTHON := python3

# Check if uv is available
UV_AVAILABLE := $(shell command -v uv 2> /dev/null)

# Use uv if available, otherwise fall back to pip
ifdef UV_AVAILABLE
    PIP := uv pip
    VENV_CREATE := uv venv .venv --python 3.10
else
    PIP := $(PYTHON) -m pip
    VENV_CREATE := $(PYTHON) -m venv .venv
endif

install:
	$(PIP) install -e .
	$(PIP) install -r requirements.txt

install-dev:
ifndef UV_AVAILABLE
	$(PIP) install --upgrade pip setuptools wheel
endif
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

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

clean-env:
	rm -rf .venv/
	rm -rf .direnv/
	rm -f .python-version.local

build:
	$(PYTHON) setup.py sdist bdist_wheel

docs:
	# Add documentation generation here if needed
	@echo "Documentation generation not yet implemented"

run-example:
	vibe-verifier tests/test_data/sample_repos/python_project

check: lint test
	@echo "All checks passed!"

setup-dev:
ifdef UV_AVAILABLE
	./scripts/setup-dev-uv.sh
else
	@echo "uv not found, using pip setup..."
	./scripts/setup-dev.sh
endif

install-uv:
	@echo "Installing uv package manager..."
	curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "uv installed! Please restart your shell or run: source ~/.cargo/env"

help:
	@echo "Available targets:"
	@echo "  setup-dev     - Run automated development setup (uses uv if available)"
	@echo "  install-uv    - Install uv package manager"
	@echo "  install       - Install the package and dependencies"
	@echo "  install-dev   - Install with development dependencies"
	@echo "  test          - Run all tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  test-unit     - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  lint          - Run linting tools"
	@echo "  format        - Format code with black and isort"
	@echo "  clean         - Remove build artifacts and cache"
	@echo "  clean-env     - Remove virtual environment"
	@echo "  build         - Build distribution packages"
	@echo "  check         - Run lint and tests"