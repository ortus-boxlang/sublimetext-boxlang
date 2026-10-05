# BoxLang Language Support for Sublime Text

[![Tests](https://github.com/ortus-boxlang/sublimetext-boxlang/actions/workflows/tests.yml/badge.svg)](https://github.com/ortus-boxlang/sublimetext-boxlang/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Comprehensive BoxLang language support for Sublime Text 4. Provides syntax highlighting, intelligent completions, inline documentation, code formatting, type inference, and build tools for the BoxLang programming language.

---

## Features

### Syntax Highlighting

- **`.bx`** — Script classes with full syntax support
- **`.bxs`** — Script-only files
- **`.bxm`** — Module templates with embedded script blocks

### Intelligent Completions

- **940+ Built-in Functions** (639 core + 303 module) with parameter hints and snippet insertion
- **86 BoxLang Tags** (`bx:` components) (49 core + 37 module) with attribute completions
- **370+ Member Functions** for native types (string, array, struct, query, numeric, date, datetime, list, xml)
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
- **Go to Definition** — Command Palette navigation to classes and functions
- **Syntax Check** — `boxlang check` on save (and optionally while typing) with squiggles, gutter icons, inline error annotations, an error panel, and F4/Shift+F4 navigation
- **TestBox Runner** — Run the current bundle, the spec at the cursor, or all tests with the BoxLang runner (or a project web runner) and see failures inline
- **Error Panel** — Parse error display with F4/Shift+F4 navigation
- **Status Bar** — Version, indexing progress, and error counts
- **Code Snippets** — 19 built-in snippets for common patterns, including sets, ranges, inner classes, query transformers and scheduled tasks

---

## Requirements

| Dependency | Version | Purpose |
|------------|---------|---------|
| Sublime Text | 4 (Build 4180+) | Editor platform |
| BoxLang | 1.17.0+ | CLI for parsing, syntax checking, formatting, compilation |
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

| Action | macOS | Linux | Windows |
|--------|-------|-------|---------|
| Show inline documentation | `F1` | `F1` | `F1` |
| Toggle controller/view | `Ctrl+F1` | `Ctrl+F1` | `Ctrl+F1` |
| Format code | `Shift+Option+F` | `Shift+Alt+F` | `Shift+Alt+F` |
| Inject DI property | `Shift+Option+D` | `Shift+Alt+D` | `Shift+Alt+D` |
| Insert `writeDump()` | `Ctrl+Option+D` | `Ctrl+Alt+D` | `Ctrl+Alt+D` |
| Insert `writeOutput()` | `Ctrl+Shift+O` | `Ctrl+Shift+O` | `Ctrl+Shift+O` |
| Insert `abort;` | `Ctrl+Option+A` | `Ctrl+Alt+A` | `Ctrl+Alt+A` |
| Wrap selection in `##` | `#` | `#` | `#` |
| Go to definition | `Cmd+Click` (also `Ctrl+Click`) | `Ctrl+Click` | `Ctrl+Click` |
| Next parse error | `F4` | `F4` | `F4` |
| Previous parse error | `Shift+F4` | `Shift+F4` | `Shift+F4` |
| Build & run (Sublime default) | `Cmd+B` | `Ctrl+B` | `Ctrl+B` |

> Note: On some macOS keyboards, use `Fn` with function keys (`F1`, `F4`, etc.) if media keys are enabled.

---

## Build System

| Variant | Command | Use Case |
|---------|---------|----------|
| **Run** | `boxlang "$file"` | Execute current file |
| **Run with Arguments** | `boxlang "$file" ${args}` | Execute with CLI args |
| **Run with Debug** | `boxlang --bx-debug "$file"` | Run with Debug output |
| **Compile File** | `boxlang compile --source "$file" --target "./bin"` | Compile single file |
| **Compile Project** | `boxlang compile --source "$file_path" --target "./bin"` | Compile entire project |
| **Check Syntax** | `boxlang check "$file"` | Validate syntax without running the file (BoxLang 1.17+) |
| **Check Project** | `boxlang check --source "$project"` | Validate every file in the project (BoxLang 1.17+) |
| **Feature Audit** | `boxlang featureaudit --source "$file_path"` | Audit CFML→BoxLang compatibility |

---

## Syntax Checking

The package runs [`boxlang check`](https://boxlang.ortusbooks.com/getting-started/ide-tooling/boxlang-syntax-check) (BoxLang 1.17+) to find syntax errors without executing your code.

- **On save** (default): errors are underlined, listed in the error panel, and counted in the status bar. Use `F4` / `Shift+F4` to jump between them.
- **While typing** (opt-in): set `boxlang_check_on_type` to `true`. The unsaved buffer is checked after a pause of `boxlang_check_on_type_delay_ms` (default 1000 ms), without opening the panel.
- **On demand**: run `BoxLang: Check Syntax` from the Command Palette, or pick the `BoxLang: Check Syntax` build variant for clickable errors in the build output. `BoxLang: Check Project` (command and build variant) checks every file in the project.
- **Where errors show**: a squiggle, a gutter icon, the first line of the message inline at the end of the line, a hover popup on the gutter icon, and the full text in the error panel. Turn the icon or inline text off with `boxlang_error_gutter_icons` and `boxlang_error_inline_annotations`.
- Works for `.bx`, `.bxs`, `.bxm`, and the CFML extensions (`.cfc`, `.cfm`, `.cfs`) when CFML fallback is enabled.

If your BoxLang is older than 1.17 the check is skipped and the status bar tells you why.

---

## TestBox

Run tests from the Command Palette (`BoxLang: TestBox ...`):

| Command | Runs |
|---------|------|
| `TestBox Run Bundle (Current File)` | The bundle for the current file |
| `TestBox Run Spec at Cursor` | The `it()` / `test()` / `function testXxx()` above the cursor (or the enclosing `describe()` suite) |
| `TestBox Run All Tests` | Everything in `directory` (default `tests.specs`) |
| `TestBox Run Last` | Repeats the previous run |

By default tests run through TestBox's **BoxLang runner** (`testbox/system/runners/BoxLangRunner.bx`, TestBox 7+). It is auto-detected from your project; set `runner_path` if yours lives elsewhere. Results appear in an output panel with clickable `file:line` failures, and failing lines in open files get a squiggle, gutter icon and inline message.

### Using a web runner (per project)

A web runner is opt-in per project. Put the runner URL in your `.sublime-project`:

```json
{
  "settings": {
    "boxlang_testbox": {
      "http_runner_url": "http://localhost:8080/tests/runner.bxm"
    }
  }
}
```

Tests then run over HTTP with `reporter=json` (plus `bundles`, `directory`, `testSpecs` or `testSuites` as needed) and the results are shown the same way.

| `boxlang_testbox` key | Default | Description |
|-----------------------|---------|-------------|
| `runner_path` | `""` | Path to `BoxLangRunner.bx`, relative to the project root. Empty = auto-detect |
| `http_runner_url` | `""` | Web runner URL. Empty = use the BoxLang runner |
| `directory` | `"tests.specs"` | Dot-path directory used by Run All Tests |
| `extra_args` | `[]` | Extra BoxLang runner arguments, e.g. `["--labels=unit"]` |
| `timeout` | `300` | Seconds to wait for a run |

---

## Settings

Open settings: `Preferences: BoxLang Settings` (Command Palette)

> **Note:** The table below shows frequently used settings. For the complete list (30 settings), see `Preferences: BoxLang Settings` in Sublime Text or [BoxLang.sublime-settings](BoxLang.sublime-settings).

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `boxlang_executable_path` | `null` | Custom BoxLang CLI path |
| `boxlang_enable_cfml_fallback` | `false` | Enable `.cfc`/`.cfm`/`.cfs` support |
| `boxlang_bif_completions` | `"required"` | BIF style: `basic`, `required`, `full` |
| `boxlang_class_completions` | `"required"` | Component style: `basic`, `required`, `full` |
| `boxlang_class_completion_names` | `"basic"` | Include return type: `basic`, `full` |
| `boxlang_instantiated_component_completions` | `true` | Variable-to-component mapping completions |
| `boxlang_auto_insert_closing_tag` | `false` | Auto-insert closing `bx:` tag on `>` |
| `boxlang_check_on_save` | `true` | Run `boxlang check` when a file is saved |
| `boxlang_check_show_panel` | `true` | Open the error panel when a check finds errors |
| `boxlang_check_on_type` | `false` | Also check while typing (debounced, checks the unsaved buffer) |
| `boxlang_check_on_type_delay_ms` | `1000` | Delay after the last keystroke before checking (min 100) |
| `boxlang_error_gutter_icons` | `true` | Gutter icon on lines with syntax errors |
| `boxlang_error_inline_annotations` | `true` | Show the first line of each error at the end of the line |
| `boxlang_format_on_save` | `false` | Auto-format on save |
| `boxlang_auto_compile_on_save` | `false` | Auto-compile to `./bin` on save |
| `boxlang_compile_target` | `"./bin"` | Compilation target directory |
| `boxlang_hover_docs` | `true` | Enable hover documentation |
| `boxlang_completion_docs` | `true` | Enable completion docs popup |
| `boxlang_status_bar_enabled` | `true` | Show status bar info |
| `boxlang_class_folders` | `[ { "path": ".", ... } ]` | Class folders for indexing and variable mapping (defaults to project root) |
| `boxlang_controller_folders` | `["controllers","handlers"]` | Controller folder names for toggle |
| `boxlang_view_folders` | `["views"]` | View folder names for toggle |
| `boxlang_testbox_enabled` | `true` | Enable TestBox integration |

### Project Configuration

Add to your `.sublime-project` file:

```json
{
  "settings": {
    "boxlang_class_folders": [
      {
        "path": ".",
        "variable_names": ["{class}", "{class_folder_singularized}"],
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
| `bxlocalclass` | Local or inner class (1.14+) |
| `bxabstract` | Abstract class (1.14+) |
| `bxset` | Set literal (1.14+) |
| `bxrange` | Range (1.14+) |
| `bxclassmap` | Class reference as constructor, `map( User )` (1.14+) |
| `bxtransformer` | `queryExecute` with a query transformer (1.14+) |
| `bxscheduler` | `schedulerNew()` with a server-fixed task (1.18+) |
| `bxtask` | Scheduled task with `.onOneServer()` (1.18+) |
| `bxclassintercept` | Class instantiation interception point (1.18+) |

---

## Running Tests

The package includes a comprehensive test suite using pytest and TestBox-style expectations (313 tests across 17 files).

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
├── unit/                    # Unit tests (12 files, 191 tests)
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
│   ├── test_wizard.py
│   └── test_bug_fixes.py    # Regression tests for all reviewed bugs
├── integration/             # Integration tests (3 files, 45 tests)
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

| File Type       | Parser     | Method                                  |
| --------------- | ---------- | --------------------------------------- |
| `.bx` / `.bxs`  | AST Parser | `boxlang --bx-printast` (100% accuracy) |
| `.bxm`          | Tag Parser | Flexible tokenizer (not strict XML)     |

### Plugin System

Completions and documentation are provided by pluggable modules:

| Plugin                | Purpose                                                    |
| --------------------- | ---------------------------------------------------------- |
| `basecompletions`     | BIFs, tags, member functions from JSON data                |
| `boxdocs`             | URL-based inline documentation                             |
| `classes`             | Variable-to-component completions                          |
| `dotpaths`            | Import/new/createObject dot-path completions               |
| `typecompletions`     | Type-aware member method completions                       |
| `applicationbx`       | Application.bx lifecycle method completions                |
| `in_file_completions` | Current-file function, variable, and property completions  |

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

## Updating Completion Data

Completion data (BIFs, tags, member functions, and inline doc parameters) is generated from the
[boxlang-docs](https://github.com/ortus-boxlang/boxlang-docs) repository using
[scripts/generate_completions.py](scripts/generate_completions.py).

### What gets generated

| File | Contents |
| ---- | -------- |
| `boxlang_functions.json` | 940+ BIF names → description + snippet pairs |
| `boxlang_tags.json` | 86 tag names → required/optional attribute lists |
| `boxlang_member_functions.json` | Member methods per type (string, array, struct, …) |
| `boxlang_function_params.json` | Full parameter data used by F1/hover doc popups |

Coverage includes **core** BoxLang plus all **modules**:
compat-cfml, CSRF, ESAPI, image-manipulation, password-encryption, RSS, WDDX, web-support,
ui-compatibility, bx-couchbase, bx-csv, bx-jwt, bx-ldap, bx-meilisearch, bx-plus, bx-plus-pdf,
bx-redis, bx-spreadsheet.

### SOP — Running the generator

#### First time (clone the docs repo)

```bash
python3 scripts/generate_completions.py --clone
```

This clones `boxlang-docs` to `../boxlang-docs` (sibling of this repo) and generates all JSON files.

#### After a BoxLang release or docs update

```bash
# Pull latest docs and regenerate
python3 scripts/generate_completions.py --update

# Or if the docs repo is in a custom location
python3 scripts/generate_completions.py --update --docs-path /path/to/boxlang-docs
```

#### Reviewing the output

The script prints a summary of what was found:

```
Parsing BIF files...
  compat-cfml: +40 BIFs
  image-manipulation: +55 BIFs
  ...
Found 942 BIFs total (639 core + 303 module)
```

Check `[warn]` lines in stderr — they indicate markdown files the parser could not extract a
function name from (usually placeholder `README.md` files; a count of zero warnings is ideal).

#### Committing the updated JSON

The generated JSON files are checked into the repository under
`src/plugins_/basecompletions/json/`. After running the script, commit all four files together:

```bash
git add src/plugins_/basecompletions/json/
git commit -m "chore: update completion data from boxlang-docs"
```

#### Prerequisites

- Python 3.11+
- `boxlang-docs` repo cloned (or use `--clone` / `--docs-path`)
- No other dependencies — uses stdlib only

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
6. **Single-threaded indexing** — Files indexed sequentially; will be parallelized in Phase 4

---

## Roadmap

### Phase 2 (Complete)

- [x] Syntax highlighting (`.bx`, `.bxs`, `.bxm`)
- [x] 940+ BIF, 86 tag, and 370+ member function completions
- [x] Dot-path and type-aware completions
- [x] Component indexing with inheritance resolution
- [x] Inline documentation (F1 popup, hover, completion docs)
- [x] Code formatting via `boxlang format`
- [x] Build system (run, compile, debug, audit)
- [x] Error panel with F4/Shift+F4 navigation
- [x] Syntax checking via `boxlang check`
- [x] Type inference engine (medium depth)
- [x] Go-to-definition via Command Palette
- [x] Status bar integration (version, indexing, errors)
- [x] 10 code snippets for common patterns
- [x] `applicationbx` plugin — Application.bx lifecycle completions
- [x] `in_file_completions` plugin — in-file symbol completions
- [x] Root-level event listener registration
- [x] Sub-package command re-export for ST4 compatibility

### Phase 3

- [ ] Auto-close tags on `>`

### Phase 4

- [ ] Java class introspection


## Documentation

Full BoxLang documentation: [boxlang.ortusbooks.com](https://boxlang.ortusbooks.com)

---

## License

Apache License 2.0 — see [license.txt](license.txt) for details.

---

## Credits

Built by [Ortus Solutions](https://www.ortussolutions.com) for the BoxLang community.

Architecture inspired by the [sublimetext-cfml](https://github.com/jcberquist/sublimetext-cfml) package, reimagined and rebuilt from the ground up for BoxLang.
