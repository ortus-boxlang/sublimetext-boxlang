---
name: boxlang-testing
description: "Write and run tests for the BoxLang Sublime Text package. Use pytest with TestBox-style expectations. Covers parser tests, type resolver tests, plugin tests, and integration tests."
---

# BoxLang Testing Skill

Use this skill when writing or running tests for the BoxLang Sublime Text package.

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── expectations.py          # TestBox-style expectation helpers
├── unit/
│   ├── test_ast_parser.py   # AST parser unit tests
│   ├── test_tag_parser.py   # Tag parser unit tests
│   ├── test_type_resolver.py # Type inference tests
│   ├── test_utils.py        # Utility function tests
│   └── test_cli.py          # CLI wrapper tests
├── integration/
│   ├── test_completions.py  # Completion system tests
│   ├── test_indexing.py     # Component indexing tests
│   └── test_plugins.py      # Plugin system tests
└── fixtures/                # Test fixture files
    ├── sample_class.bx      # Sample .bx file for parsing
    ├── sample_module.bxm    # Sample .bxm file for parsing
    └── sample_script.bxs    # Sample .bxs file for parsing
```

## Running Tests

### All Tests
```bash
# From project root
python -m pytest tests/

# With verbose output
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Specific Test Files
```bash
python -m pytest tests/unit/test_ast_parser.py
python -m pytest tests/unit/test_type_resolver.py -v
```

### Specific Test Markers
```bash
python -m pytest tests/ -m slow       # Slow tests
python -m pytest tests/ -m fast       # Fast tests
python -m pytest tests/ -m parser     # Parser tests only
python -m pytest tests/ -m "not cli"  # Skip CLI-dependent tests
```

### Using Makefile (if available)
```bash
make test           # Run all tests
make test-unit      # Run unit tests only
make test-coverage  # Run with coverage
make test-watch     # Watch mode
```

### Using run_tests.py
```bash
python tests/run_tests.py              # Run all tests
python tests/run_tests.py --unit       # Unit tests only
python tests/run_tests.py --verbose    # Verbose output
python tests/run_tests.py --coverage   # With coverage
python tests/run_tests.py --watch      # Watch mode
python tests/run_tests.py --report     # Generate HTML report
```

## TestBox-Style Expectations

The `expectations.py` module provides TestBox-style fluent assertions:

```python
from tests.expectations import expect

# Basic expectations
expect(actual).to_be(expected)
expect(actual).to_be_equal(expected)
expect(actual).to_be_true()
expect(actual).to_be_false()
expect(actual).to_be_none()
expect(actual).to_be_instance_of(SomeClass)

# Collection expectations
expect(collection).to_contain(item)
expect(collection).to_have_length(n)
expect(collection).to_include(item)
expect(dict_obj).to_have_key("key")
expect(dict_obj).to_have_length(n)

# String expectations
expect(string).to_start_with(prefix)
expect(string).to_end_with(suffix)
expect(string).to_contain(substring)
expect(string).to_match(pattern)

# Numeric expectations
expect(value).to_be_gt(other)
expect(value).to_be_gte(other)
expect(value).to_be_lt(other)
expect(value).to_be_lte(other)
expect(value).to_be_close_to(other, delta)

# Negation
expect(actual).not_to_be(expected)
expect(actual).not_to_contain(item)
```

## Writing Tests

### Parser Tests

```python
import pytest
from src.component_parser.ast_parser import ASTParser
from tests.expectations import expect

class TestASTParser:
    """Tests for the AST parser."""

    def test_parse_class_declaration(self, sample_class_ast):
        """Test parsing a class declaration."""
        metadata = ASTParser._extract_metadata(sample_class_ast)

        expect(metadata["name"]).to_be("UserService")
        expect(metadata["extends"]).to_be("BaseService")
        expect(metadata["implements"]).to_contain("IUserService")
        expect(metadata["functions"]).to_have_length(3)
        expect(metadata["properties"]).to_have_length(2)

    def test_parse_function_with_args(self, sample_function_ast):
        """Test parsing a function with arguments."""
        metadata = ASTParser._extract_metadata(sample_function_ast)
        func = metadata["functions"]["find"]

        expect(func["name"]).to_be("find")
        expect(func["return_type"]).to_be("query")
        expect(func["access"]).to_be("public")
        expect(func["args"]).to_have_length(2)
        expect(func["args"][0]["name"]).to_be("criteria")
        expect(func["args"][0]["required"]).to_be_true()

    def test_parse_error_handling(self, mocker):
        """Test handling of parse errors."""
        mocker.patch("src.boxlang_cli.run_ast", return_value=(None, "AST error"))
        result = ASTParser.parse("/path/to/file.bx")

        expect(result["parse_errors"]).to_contain("AST error")
        expect(result["name"]).to_be_none()
```

### Type Resolver Tests

```python
import pytest
from src.type_resolver import TypeResolver
from tests.expectations import expect

class TestTypeResolver:
    """Tests for the type inference engine."""

    def test_resolve_string_literal(self):
        """Test resolving string literal type."""
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression('"hello"')
        expect(result).to_be("string")

    def test_resolve_array_literal(self):
        """Test resolving array literal type."""
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("[1, 2, 3]")
        expect(result).to_be("array")

    def test_resolve_struct_literal(self):
        """Test resolving struct literal type."""
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression('{"key": "value"}')
        expect(result).to_be("struct")

    def test_resolve_new_expression(self):
        """Test resolving new expression type."""
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("new UserService()")
        expect(result).to_be("component:UserService")

    def test_resolve_bif_return_type(self):
        """Test resolving BIF return type."""
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("arrayNew()")
        expect(result).to_be("array")

    def test_resolve_create_object(self):
        """Test resolving createObject type."""
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression(
            'createObject("component", "model.UserService")'
        )
        expect(result).to_be("component:model.UserService")
```

### Plugin Tests

```python
import pytest
from src.plugins_.basecompletions import get_completions
from tests.expectations import expect

class TestBaseCompletions:
    """Tests for base completions plugin."""

    def test_tag_completions(self, mock_boxlang_view_tag):
        """Test tag name completions."""
        result = get_completions(mock_boxlang_view_tag)

        expect(result).not_to_be_none()
        expect(result.completions).not_to_be_empty()
        # Check that bx:query is in completions
        triggers = [c.trigger for c in result.completions]
        expect(triggers).to_contain("query")

    def test_bif_completions(self, mock_boxlang_view_script):
        """Test BIF completions."""
        result = get_completions(mock_boxlang_view_script)

        expect(result).not_to_be_none()
        triggers = [c.trigger for c in result.completions]
        expect(triggers).to_contain("writeDump")
        expect(triggers).to_contain("arrayNew")
```

## Fixtures

### conftest.py Fixtures

```python
import pytest

@pytest.fixture
def sample_class_ast():
    """Sample AST output for a class declaration."""
    return {
        "statements": [
            {"ASTType": "BoxExpressionStatement", "expression": {"ASTType": "BoxIdentifier", "name": "class"}},
            {"ASTType": "BoxExpressionStatement", "expression": {"ASTType": "BoxIdentifier", "name": "UserService"}},
            {"ASTType": "BoxExpressionStatement", "expression": {"ASTType": "BoxAssignment", "left": {"name": "extends"}, "right": {"ASTType": "BoxStringLiteral", "value": "BaseService"}}},
            {"ASTType": "BoxStatementBlock", "body": []}
        ]
    }

@pytest.fixture
def mock_boxlang_view_tag():
    """Mock BoxlangView in tag context."""
    view = MockBoxlangView()
    view.type = "tag"
    view.tag_name = "bx:query"
    view.tag_location = "tag_name"
    return view
```

### Test Fixture Files

Place sample `.bx`, `.bxs`, `.bxm` files in `tests/fixtures/` for parser tests.

## Mocking Sublime Text API

Since the Sublime Text API is not available in pytest, use mocks:

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_sublime():
    """Mock sublime module."""
    sublime = MagicMock()
    sublime.CompletionItem = MagicMock
    sublime.COMPLETION_FORMAT_SNIPPET = 1
    sublime.KIND_ID_FUNCTION = 1
    return sublime

@pytest.fixture(autouse=True)
def patch_sublime(mock_sublime):
    """Auto-patch sublime module for all tests."""
    with patch.dict("sys.modules", {"sublime": mock_sublime, "sublime_plugin": MagicMock()}):
        yield
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.fast
def test_quick_parser():
    pass

@pytest.mark.slow
def test_full_indexing():
    pass

@pytest.mark.parser
def test_ast_parsing():
    pass

@pytest.mark.cli
def test_cli_detection():
    pass

@pytest.mark.integration
def test_completion_flow():
    pass
```

## Coverage Configuration

```ini
# .coveragerc
[run]
source = src
omit =
    src/plugins_/applicationbx/*
    src/plugins_/in_file_completions/*
    tests/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
```

## CI Integration

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest pytest-mock pytest-cov
      - run: pytest tests/ -v --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4
```
