# BoxLang Language Support for Sublime Text

[![Tests](https://github.com/ortus-boxlang/sublimetext-boxlang/actions/workflows/tests.yml/badge.svg)](https://github.com/ortus-boxlang/sublimetext-boxlang/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Comprehensive BoxLang language support for Sublime Text 4. Provides syntax highlighting, intelligent completions, inline documentation, code formatting, type inference, and build tools for the BoxLang programming language.

---

## Features

### Syntax Highlighting
- **`.bx`** — Script classes with full syntax support
- **`.bxs`** — Script-only files
- **`.bxm`** — Module templates with embedded script blocks

### Intelligent Completions
- **560 Built-in Functions** with parameter hints and snippet insertion
- **41 BoxLang Tags** (`bx:` components) with attribute completions
- **72 Member Functions** for native types (string, array, struct, query, numeric)
- **Dot-Path Completions** for `import`, `new`, and `createObject()` statements
- **Type-Aware Completions** based on inferred variable types
- **Component Indexing** with inheritance resolution for project-wide completions

### Inline Documentation
- **F1 Popup** — Full documentation with parameter references
- **Hover Docs** — Quick info on mouse hover
- **Completion Docs** — Parameter hints during auto-complete
- **Go to Docs** — Navigate to [boxlang.ortusbooks.com](https://boxlang.ortusbooks.com)

### Developer Tools
- **Code Formatting** via `boxlang format` CLI
- **Build System** — Run, compile, debug, and audit BoxLang files
- **Go to Definition** — Ctrl/Cmd+Click to navigate to classes and functions
- **Error Panel** — Parse error display with F4/Shift+F4 navigation
- **Status Bar** — Version, indexing progress, and error counts
- **Code Snippets** — 10 built-in snippets for common patterns

---

## Requirements

| Dependency | Version | Purpose |
|------------|---------|---------|
| Sublime Text | 4 (Build 4180+) | Editor platform |
| BoxLang | 1.13.0+ | CLI for parsing, formatting, compilation |
| Python | 3.11+ | Plugin runtime (bundled with Sublime Text) |

> **Note:** Syntax highlighting works without BoxLang installed. Full feature set requires the BoxLang CLI available in your PATH.

---

## Installation

### Via Package Control (Recommended)

1. Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Select `Package Control: Install Package`
3. Search for `BoxLang` and press Enter

### Manual Installation

```bash
git clone https://github.com/ortus-boxlang/sublimetext-boxlang.git \
  ~/Library/Application\ Support/Sublime\ Text/Packages/BoxLang
```

Then restart Sublime Text.

---

## First Run

On first launch, the setup wizard will:

1. **Detect BoxLang** — Check if `boxlang` is available in your PATH
2. **Configure CFML Support** — Optionally enable `.cfc`/`.cfm`/`.cfs` handling (disabled by default if CFML package is installed)
3. **Show Quick Tips** — Display essential keyboard shortcuts

Re-run the wizard anytime: `BoxLang: Run Setup Wizard` (Command Palette)

---

## Key Bindings

| Shortcut | Action |
|----------|--------|
| `F1` | Show inline documentation |
| `Ctrl+F1` | Toggle controller/view |
| `Shift+Alt+F` | Format code |
| `Shift+Alt+D` | Inject DI property |
| `Ctrl+Alt+D` | Insert `writeDump()` |
| `Ctrl+Shift+O` | Insert `writeOutput()` |
| `Ctrl+Alt+A` | Insert `abort;` |
| `#` | Wrap selection in `##` |
| `Ctrl/Cmd+Click` | Go to definition |
| `F4` | Next parse error |
| `Shift+F4` | Previous parse error |
| `Ctrl+B` | Build & run |

---

## Build System

| Variant | Command | Use Case |
|---------|---------|----------|
| **Run** | `boxlang "$file"` | Execute current file |
| **Run with Arguments** | `boxlang "$file" ${args}` | Execute with CLI args |
| **Compile File** | `boxlang compile --source "$file" --target "./bin"` | Compile single file |
| **Compile Project** | `boxlang compile --source "$file_path" --target "./bin"` | Compile entire project |
| **Debug** | `boxlang --bx-debug "$file"` | Run with debug output |
| **Feature Audit** | `boxlang featureaudit --source "$file_path"` | Audit CFML→BoxLang compatibility |

---

## Settings

Open settings: `BoxLang: Settings` (Command Palette)

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `boxlang_executable_path` | `null` | Custom BoxLang CLI path |
| `boxlang_enable_cfml_fallback` | `false` | Enable `.cfc`/`.cfm`/`.cfs` support |
| `boxlang_bif_completions` | `"required"` | BIF style: `basic`, `required`, `full` |
| `boxlang_cfc_completions` | `"required"` | Component style: `basic`, `required`, `full` |
| `boxlang_cfc_completion_names` | `"basic"` | Include return type: `basic`, `full` |
| `boxlang_auto_compile_on_save` | `false` | Auto-compile to `./bin` on save |
| `boxlang_format_on_save` | `false` | Auto-format on save |
| `boxlang_hover_docs` | `true` | Enable hover documentation |
| `boxlang_completion_docs` | `true` | Enable completion docs popup |

### Project Configuration

Add to your `.sublime-project` file:

```json
{
  "settings": {
    "boxlang_cfc_folders": [
      {
        "path": "model",
        "variable_names": ["{cfc}", "{cfc_folder_singularized}"],
        "accessors": true
      }
    ]
  },
  "mappings": [
    { "path": "/absolute/path/to/project", "mapping": "/" }
  ]
}
```

---

## Code Snippets

| Trigger | Description |
|---------|-------------|
| `bxclass` | Class declaration with extends |
| `bxinterface` | Interface declaration |
| `bxcomponent` | Component declaration |
| `bxfunc` | Function declaration |
| `bxtest` | Test block (`describe`/`it`) |
| `bxtry` | Try/catch block |
| `bxfor` | For loop |
| `bxforeach` | For-in loop |
| `bxif` | If statement |
| `bxscript` | `<bx:script>` block |

---

## Running Tests

The package includes a comprehensive test suite with **218 tests** using pytest and TestBox-style expectations.

### Quick Start

```bash
# Run all tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Using the Test Runner

```bash
# All tests
python tests/run_tests.py

# Unit tests only
python tests/run_tests.py --unit

# Integration tests only
python tests/run_tests.py --integration

# With coverage
python tests/run_tests.py --coverage

# Generate HTML coverage report
python tests/run_tests.py --report

# Watch mode (re-runs on file changes)
python tests/run_tests.py --watch

# Run specific test file
python tests/run_tests.py --file tests/unit/test_ast_parser.py

# Run tests with specific marker
python tests/run_tests.py --marker fast
```

### Using Make

```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-coverage     # Run with coverage
make test-report       # Generate HTML coverage report
make test-watch        # Watch mode
make test-file FILE=tests/unit/test_ast_parser.py
make test-marker MARKER=fast
make test-list         # List all available tests
make clean             # Clean test artifacts
```

### Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and Sublime Text mocks
├── expectations.py          # TestBox-style fluent assertions
├── run_tests.py             # Custom test runner CLI
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Test dependencies
├── unit/                    # Unit tests (13 files, 179 tests)
│   ├── test_ast_parser.py
│   ├── test_tag_parser.py
│   ├── test_type_resolver.py
│   ├── test_cli.py
│   ├── test_events.py
│   ├── test_utils.py
│   ├── test_error_panel.py
│   ├── test_status_bar.py
│   ├── test_documentation_helpers.py
│   ├── test_parser_router.py
│   └── test_wizard.py
├── integration/             # Integration tests (3 files, 39 tests)
│   ├── test_completions.py
│   ├── test_indexing.py
│   └── test_plugins.py
└── fixtures/                # Sample BoxLang files
    ├── sample_class.bx
    ├── sample_script.bxs
    └── sample_module.bxm
```

### TestBox-Style Expectations

The test suite uses a fluent assertion API inspired by TestBox:

```python
from tests.expectations import expect

# Equality
expect(actual).to_be(expected)
expect(actual).not_to_be(expected)

# Type checks
expect(value).to_be_instance_of(SomeClass)
expect(value).to_be_true()
expect(value).to_be_false()
expect(value).to_be_none()
expect(value).not_to_be_none()

# Collections
expect(collection).to_contain(item)
expect(collection).to_have_length(5)
expect(collection).to_be_empty()
expect(dict_obj).to_have_key("key")

# Strings
expect(string).to_start_with("prefix")
expect(string).to_end_with("suffix")
expect(string).to_contain_string("substring")
expect(string).to_match(r"regex.*pattern")

# Negation
expect(value).not_to_contain(item)
expect(value).not_to_start_with("prefix")
expect(value).not_to_end_with("suffix")
expect(value).not_to_contain_string("substring")

# Numeric
expect(value).to_be_gt(other)
expect(value).to_be_gte(other)
expect(value).to_be_lt(other)
expect(value).to_be_lte(other)
expect(value).to_be_close_to(other, delta=0.001)
```

### Installing Test Dependencies

```bash
# Using pip
pip install pytest pytest-mock pytest-cov

# Or use the provided requirements file
pip install -r tests/requirements.txt
```

### CI/CD

Tests run automatically on push and pull requests via GitHub Actions (Python 3.11, 3.12, 3.13). Coverage reports are uploaded to Codecov.

---

## Architecture

### Parsing Strategy

| File Type | Parser | Method |
|-----------|--------|--------|
| `.bx` / `.bxs` | AST Parser | `boxlang --bx-printast` (100% accuracy) |
| `.bxm` | Tag Parser | Flexible tokenizer (not strict XML) |

### Plugin System

Completions and documentation are provided by pluggable modules:

| Plugin | Purpose |
|--------|---------|
| `basecompletions` | BIFs, tags, member functions from JSON data |
| `boxdocs` | URL-based inline documentation |
| `cfcs` | Variable-to-component completions |
| `dotpaths` | Import/new/createObject dot-path completions |
| `typecompletions` | Type-aware member method completions |

### Type Inference

Medium-depth type resolution from:
- Literal values (`"string"`, `123`, `[]`, `{}`, `true/false`)
- `new` expressions (`new UserService()` → `component:UserService`)
- `createObject()` calls
- BIF return types (60+ known functions)
- Variable assignment tracing
- Dot chain resolution
- Component metadata lookup

---

## Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write** tests for new functionality
4. **Run** the test suite (`make test`)
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Guidelines

- **AST-only parsing** for `.bx`/`.bxs` — no regex fallback
- **Self-closing tags** must be derived from BoxLang source `@BoxComponent` annotations
- **Plugin system** — extend `BoxlangPlugin` base class for new features
- **Type inference** — keep at medium depth; no full static analysis
- **Zero dead code** — no non-BoxLang features from CFML patterns
- **CLI required** — all parsing/formatting/compilation delegates to `boxlang` CLI

---

## Known Limitations

1. **AST for `.bxm`** — `boxlang --bx-printast` does not support markup files; uses flexible tag parser
2. **AST class parsing** — BoxLang v1.13.0 parses `class` as `BoxIdentifier` expressions, requiring sequential pattern matching
3. **Java introspection** — `createObject("java", "...")` types resolve as `"any"` (deferred)
4. **MCP server** — Available but deferred to Phase 5
5. **In-memory index** — No disk persistence; rebuilt each session

---

## Roadmap

### Phase 3
- [ ] `applicationbx` plugin (Application.cfc-like completions)
- [ ] `in_file_completions` plugin (in-file symbol completions)
- [ ] Auto-close tags on `>`
- [ ] Auto-format on save
- [ ] Auto-compile on save

### Phase 4
- [ ] Java class introspection
- [ ] Disk-persistent index
- [ ] Parallel indexing
- [ ] Code lens support
- [ ] Symbol renaming

### Phase 5
- [ ] MCP server integration for live docs
- [ ] LSP compatibility layer
- [ ] Debug adapter protocol

---

## Documentation

Full BoxLang documentation: [boxlang.ortusbooks.com](https://boxlang.ortusbooks.com)

---

## License

MIT License — see [license.txt](license.txt) for details.

---

## Credits

Built by [Ortus Solutions](https://www.ortussolutions.com) for the BoxLang community.

Architecture inspired by the [sublimetext-cfml](https://github.com/jcberquist/sublimetext-cfml) package, reimagined and rebuilt from the ground up for BoxLang.
