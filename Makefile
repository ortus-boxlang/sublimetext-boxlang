.PHONY: test test-unit test-integration test-coverage test-watch test-report test-file test-marker test-list test-all clean install

ifeq ($(OS),Windows_NT)
PYTHON := $(if $(wildcard .venv/Scripts/python.exe),.venv/Scripts/python.exe,python)
TEST_RUNNER := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests.ps1
INSTALL_CMD = $(PYTHON) -m pip install -q pytest pytest-mock pytest-cov
REPORT_ECHO = powershell -NoProfile -Command "Write-Host ''; Write-Host 'Coverage report: tests/coverage_html/index.html'"
else
PYTHON := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
TEST_RUNNER := $(PYTHON) tests/run_tests.py
INSTALL_CMD = $(PYTHON) -m pip install -q pytest pytest-mock pytest-cov
REPORT_ECHO = printf "\nCoverage report: tests/coverage_html/index.html\n"
endif

# Install test dependencies
install:
	@$(INSTALL_CMD)

# Default: run all tests
test:
	@$(TEST_RUNNER) --verbose

# Unit tests only
test-unit:
	@$(TEST_RUNNER) --unit --verbose

# Integration tests only
test-integration:
	@$(TEST_RUNNER) --integration --verbose

# Run with coverage
test-coverage:
	@$(TEST_RUNNER) --coverage --verbose

# Generate HTML coverage report
test-report:
	@$(TEST_RUNNER) --coverage --report --verbose
	@$(REPORT_ECHO)

# Watch mode (requires pytest-watch)
test-watch:
	@$(TEST_RUNNER) --watch

# Run specific test file
# Usage: make test-file FILE=tests/unit/test_ast_parser.py
test-file:
	@$(TEST_RUNNER) --file $(FILE) --verbose

# Run tests with specific marker
# Usage: make test-marker MARKER=fast
test-marker:
	@$(TEST_RUNNER) --marker $(MARKER) --verbose

# List all tests
test-list:
	@$(TEST_RUNNER) --list

# Install dependencies and run tests
test-all: install test

# Clean test artifacts
clean:
	@$(TEST_RUNNER) --clean
