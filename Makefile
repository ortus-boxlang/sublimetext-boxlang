.PHONY: test test-unit test-integration test-coverage test-watch test-report clean install

# Use venv python if available, otherwise system python3
PYTHON := $(shell if [ -f .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

# Install test dependencies
install:
	@$(PYTHON) -m pip install -q pytest pytest-mock pytest-cov

# Default: run all tests
test:
	@$(PYTHON) tests/run_tests.py --verbose

# Unit tests only
test-unit:
	@$(PYTHON) tests/run_tests.py --unit --verbose

# Integration tests only
test-integration:
	@$(PYTHON) tests/run_tests.py --integration --verbose

# Run with coverage
test-coverage:
	@$(PYTHON) tests/run_tests.py --coverage --verbose

# Generate HTML coverage report
test-report:
	@$(PYTHON) tests/run_tests.py --coverage --report --verbose
	@echo "\nCoverage report: tests/coverage_html/index.html"

# Watch mode (requires pytest-watch)
test-watch:
	@$(PYTHON) tests/run_tests.py --watch

# Run specific test file
# Usage: make test-file FILE=tests/unit/test_ast_parser.py
test-file:
	@$(PYTHON) tests/run_tests.py --file $(FILE) --verbose

# Run tests with specific marker
# Usage: make test-marker MARKER=fast
test-marker:
	@$(PYTHON) tests/run_tests.py --marker $(MARKER) --verbose

# List all tests
test-list:
	@$(PYTHON) tests/run_tests.py --list

# Install dependencies and run tests
test-all: install test

# Clean test artifacts
clean:
	@rm -rf tests/coverage_html
	@rm -rf .pytest_cache
	@rm -rf .coverage
	@rm -rf htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned test artifacts"
