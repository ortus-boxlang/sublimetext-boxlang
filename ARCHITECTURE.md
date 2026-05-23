# Architecture — BoxLang Sublime Text Package

> Complete architectural documentation for the `sublimetext-boxlang` Sublime Text 4 package.

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [System Architecture](#system-architecture)
4. [Module Deep Dive](#module-deep-dive)
5. [Data Flow](#data-flow)
6. [Plugin System](#plugin-system)
7. [Parsing Pipeline](#parsing-pipeline)
8. [Type Inference Engine](#type-inference-engine)
9. [Completion Pipeline](#completion-pipeline)
10. [Documentation System](#documentation-system)
11. [Indexing System](#indexing-system)
12. [Error Handling](#error-handling)
13. [Configuration](#configuration)
14. [Build & Run](#build--run)
15. [Extending the Package](#extending-the-package)
16. [Testing](#testing)
17. [Performance Considerations](#performance-considerations)
18. [Known Limitations](#known-limitations)
19. [Future Roadmap](#future-roadmap)

---

## Overview

The BoxLang Sublime Text package provides comprehensive language support for [BoxLang](https://boxlang.ortusbooks.com/), a modern JVM-based programming language that is the successor to CFML. The package delivers:

- **Syntax highlighting** for `.bx`, `.bxs`, and `.bxm` files
- **Intelligent completions** (BIFs, tags, member functions, dot-paths, type-aware)
- **Inline documentation** (F1 popup, hover docs, completion docs)
- **Go-to-definition** (file navigation + URL docs)
- **Code formatting** via `boxlang format`
- **Build & run** with multiple variants
- **Component indexing** with inheritance resolution
- **Type inference** for medium-depth static analysis

### Dependencies

| Dependency | Purpose | Required |
|------------|---------|----------|
| Sublime Text 4 (Build 4180+) | Editor platform | Yes |
| Python 3.12+ | Plugin runtime | Yes (bundled with ST) |
| BoxLang CLI v1.13.0+ | AST parsing, formatting, compilation | Yes (for full features) |

---

## Design Principles

### 1. AST-First Parsing
All `.bx`/`.bxs` parsing delegates to `boxlang --bx-printast`. Zero regex fallback. This ensures 100% accuracy since the AST comes from the actual BoxLang compiler.

### 2. CLI Delegation
Formatting, compilation, and building all use the BoxLang CLI. The package never implements its own formatter or compiler.

### 3. Plugin-Based Extensibility
Completions, documentation, and navigation are provided by pluggable modules. Each plugin is independent and can be enabled/disabled.

### 4. Zero Dead Code
No legacy CFML features. Only BoxLang-specific functionality. If a feature exists in the CFML package but not in BoxLang, it is not included.

### 5. Graceful Degradation
When BoxLang CLI is not available, syntax highlighting still works. Indexing and formatting are disabled, but the editor remains functional.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Sublime Text 4                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Syntax  │  │  Build   │  │  Keymap  │  │  Command Palette │   │
│  │  Files   │  │  System  │  │  /Mouse  │  │  Entries         │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Python Plugin (src/)                     │   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │
│  │  │ __init__.py  │  │ boxlang_cli  │  │ boxlang_view     │  │   │
│  │  │ (Entry)      │──│ (CLI Wrapper)│  │ (View Context)   │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │   │
│  │         │                 │                    │            │   │
│  │  ┌──────▼─────────────────▼────────────────────▼─────────┐  │   │
│  │  │              Completion Orchestrator                   │  │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │  │   │
│  │  │  │basecomp  │ │ boxdocs  │ │  cfcs    │ │ dotpaths │ │  │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │  │   │
│  │  │  ┌──────────┐ ┌──────────┐                            │  │   │
│  │  │  │ typecomp │ │   ...    │                            │  │   │
│  │  │  └──────────┘ └──────────┘                            │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │
│  │  │  Component   │  │    Type      │  │     Error        │  │   │
│  │  │  Indexer     │  │  Resolver    │  │     Panel        │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │   │
│  │         │                 │                                 │   │
│  │  ┌──────▼─────────────────▼──────────────────────────────┐  │   │
│  │  │              Component Parser                          │  │   │
│  │  │  ┌──────────────┐  ┌──────────────┐                   │  │   │
│  │  │  │  AST Parser  │  │  Tag Parser  │                   │  │   │
│  │  │  │ (.bx/.bxs)   │  │ (.bxm)       │                   │  │   │
│  │  │  └──────────────┘  └──────────────┘                   │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │
│  │  │    Status    │  │    Inline    │  │   Go-to-Def      │  │   │
│  │  │    Bar       │  │    Docs      │  │   Navigation     │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        BoxLang CLI                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ --version│  │--bx-     │  │ format   │  │ compile          │   │
│  │          │  │printast  │  │          │  │                  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module Deep Dive

### `src/__init__.py` — Plugin Entry Point

**Responsibility:** Initialize the package when Sublime Text loads it.

**Lifecycle:**
1. `plugin_loaded()` — Called by Sublime Text on package load
   - Initialize BoxLang CLI detection (background thread)
   - Run first-time wizard if not completed
   - Notify all modules via `_plugin_loaded()` hook
2. `plugin_unloaded()` — Called on package unload

**Command Registration:**
Scans all loaded modules for classes ending in `Command` and registers them with Sublime Text.

### `src/boxlang_cli.py` — CLI Wrapper

**Responsibility:** Interface with the BoxLang CLI for version detection, AST parsing, formatting, and compilation.

**Architecture:**
- **Detection:** Runs `boxlang --version` in a daemon thread on initialization
- **Callbacks:** `on_detection_complete(callback)` registers callbacks for async notification
- **State:** Global variables `_boxlang_installed`, `_boxlang_version`, `_boxlang_executable`
- **Thread Safety:** All CLI calls run in background threads; callbacks marshal back to main thread

**API:**
```python
boxlang_cli.initialize()                          # Start detection
boxlang_cli.on_detection_complete(callback)       # Register callback
boxlang_cli.is_installed()                        # bool
boxlang_cli.get_version()                         # str
boxlang_cli.get_executable()                      # str
boxlang_cli.run_ast(file_path)                    # (ast_dict, error)
boxlang_cli.run_ast_code(code)                    # (ast_dict, error)
boxlang_cli.run_format(file_path)                 # (success, error)
boxlang_cli.run_compile(source, target)           # (success, error)
```

### `src/boxlang_view.py` — View Context

**Responsibility:** Analyze the current cursor position to determine what kind of completions/documentation to provide.

**Context Detection Flow:**
```
position → determine_type() → set context properties
    ├── "tag"          → set_tag_info()
    ├── "tag_attributes" → set_tag_info(True)
    ├── "dot"          → set_dot_context() + get_function_call_params()
    └── "script"       → get_function_call_params()
```

**Key Methods:**
- `determine_type()` — Matches selectors to determine context type
- `set_dot_context()` — Builds chain of identifiers before `.`
- `get_function_call_params()` — Parses function call arguments
- `get_dot_context(pt)` — Recursively builds identifier chain

### `src/completions.py` — Completion Orchestrator

**Responsibility:** Collect completions from all plugins and merge them into a single list.

**Flow:**
```
on_query_completions → get_completions(view, position, prefix)
    ├── Create BoxlangView
    ├── For each plugin: get_completions(boxlang_view)
    │   └── Collect CompletionList objects
    ├── Determine minimum priority (if exclude_lower_priority)
    ├── For each plugin: get_completion_docs(boxlang_view)
    │   └── Display inline documentation popup
    └── Return merged completion list
```

### `src/inline_documentation.py` — Documentation System

**Responsibility:** Display popup documentation for symbols (F1, hover, completion docs).

**Features:**
- Multi-page documentation with pagination
- Syntax-aware HTML generation (matches color scheme)
- Link navigation (opens browser or navigates pages)
- Region highlighting for documented symbols

**Templates:**
- `templates/inline_documentation.html` — F1/hover popup
- `templates/completion_doc.html` — Auto-complete doc popup
- `templates/pagination.html` — Page navigation

---

## Data Flow

### Completion Request Flow

```
User types "user."
    │
    ▼
Sublime Text → on_query_completions(view, position, prefix)
    │
    ▼
completions.get_completions(view, position, prefix)
    │
    ├── Create BoxlangView(view, position, prefix)
    │   └── determine_type() → "dot"
    │   └── set_dot_context() → [Symbol("user", ...)]
    │
    ├── For each plugin:
    │   ├── basecompletions → member function completions
    │   ├── cfcs → variable-to-component completions
    │   ├── dotpaths → component method completions
    │   └── typecompletions → type-aware method completions
    │
    ├── Merge all CompletionList objects
    │   └── Apply priority filtering
    │
    └── Return merged list to Sublime Text
```

### Documentation Request Flow

```
User presses F1
    │
    ▼
Sublime Text → boxlang_inline_documentation command
    │
    ▼
inline_documentation.py
    │
    ├── Create BoxlangView(view, position)
    │
    ├── For each plugin: get_inline_documentation(boxlang_view, "inline_doc")
    │   ├── boxdocs → URL-based docs from ortusbooks.com
    │   ├── cfcs → component variable documentation
    │   └── ... → other plugin docs
    │
    ├── Sort by priority
    │
    ├── Generate HTML from template
    │   └── Apply color scheme styles
    │
    └── Show popup with pagination
```

---

## Plugin System

### Plugin Base Class

```python
class BoxlangPlugin:
    def get_completions(self, boxlang_view): ...
    def get_completion_docs(self, boxlang_view): ...
    def get_inline_documentation(self, boxlang_view, doc_type): ...
    def get_goto_boxlang_file(self, boxlang_view): ...
    def get_method_preview(self, boxlang_view): ...
```

### Plugin Loading

```python
# boxlang_plugins.py
directory = ["basecompletions", "boxdocs", "cfcs", "dotpaths", "typecompletions", ...]

for p in directory:
    m = importlib.import_module(".plugins_." + p, __package__)
    for a in dir(m):
        v = m.__dict__[a]
        if a == "BoxlangPlugin" and issubclass(v, BoxlangPlugin):
            plugins.append(v())
```

### Plugin Contract

Each plugin method receives a `BoxlangView` instance and returns:
- `None` — Plugin not applicable for this context
- Named tuple — Plugin has data to contribute

**Return Types:**
| Method | Return Type | Fields |
|--------|-------------|--------|
| `get_completions` | `CompletionList` | `completions`, `priority`, `exclude_lower_priority` |
| `get_completion_docs` | `CompletionDoc` | `doc_regions`, `doc_html_variables`, `on_navigate` |
| `get_inline_documentation` | `Documentation` | `doc_regions`, `doc_html_variables`, `on_navigate`, `priority` |
| `get_goto_boxlang_file` | `GotoBoxlangFile` | `file_path`, `symbol` |
| `get_method_preview` | `MethodPreview` | `preview_regions`, `preview_html_variables`, `on_navigate`, `priority` |

---

## Parsing Pipeline

### Dual Parser Strategy

```
parse_file(file_path)
    │
    ├── Extension = .bx or .bxs → ASTParser.parse(file_path)
    │   │
    │   ├── boxlang_cli.run_ast(file_path)
    │   │   └── boxlang --bx-printast <file>
    │   │
    │   ├── Parse JSON AST output
    │   │
    │   ├── _find_class_info(statements)
    │   │   └── Pattern-match sequential AST nodes
    │   │
    │   └── _extract_function / _extract_property
    │       └── Extract metadata from AST nodes
    │
    └── Extension = .bxm → TagParser.parse(file_path)
        │
        ├── Read file content
        │
        ├── _extract_tags(content)
        │   └── Regex-based tag extraction
        │
        ├── Classify tags (self-closing / optional body / required body)
        │
        └── For <bx:script> blocks:
            └── ASTParser.parse_string(script_content)
```

### AST Pattern Matching

The BoxLang AST does not emit a `BoxClassDeclaration` node. Instead, class declarations are represented as sequential statements that must be pattern-matched:

```
Statement 0: BoxExpressionStatement { BoxIdentifier("class") }
Statement 1: BoxExpressionStatement { BoxIdentifier("ClassName") }
Statement 2: BoxExpressionStatement { BoxAssignment("extends", BoxStringLiteral("Parent")) }
Statement 3: BoxExpressionStatement { BoxAssignment("implements", BoxStringLiteral("I1,I2")) }
Statement 4: BoxStatementBlock { body: [functions, properties] }
```

The `_find_class_info()` method walks through statements sequentially, looking for this pattern.

---

## Type Inference Engine

### Resolution Sources

```
TypeResolver.resolve_dot_chain_type(dot_context)
    │
    ├── _resolve_first_element(symbol)
    │   ├── Check variable assignment → infer from RHS
    │   ├── Check if name starts with uppercase → component
    │   └── Default → "any"
    │
    └── For each subsequent symbol in chain:
        ├── If current type = "component:X"
        │   └── Look up member in component metadata
        │       ├── Check functions → return_type
        │       ├── Check properties → type
        │       └── Check parent class (extends) → recurse
        │
        └── If current type = built-in type
            └── Look up member in builtin method table
```

### Type Resolution Priority

1. **Literal values** — `"string"`, `123`, `[]`, `{}`, `true/false`
2. **`new` expressions** — `new ComponentName()` → `component:ComponentName`
3. **`createObject()`** — `createObject("component", "path")` → `component:path`
4. **BIF return types** — 60+ known BIFs with known return types
5. **Variable assignments** — Trace back to assignment, infer from RHS
6. **Component metadata** — Look up function return types from indexed components

---

## Completion Pipeline

### Completion Sources (by priority)

| Plugin | Context | Priority | Description |
|--------|---------|----------|-------------|
| `basecompletions` | All | 0 | BIFs, tags, member functions from JSON |
| `dotpaths` | Script/Dot | 0 | Import/new/createObject dot-paths |
| `cfcs` | Script/Dot | 0 | Variable-to-component completions |
| `typecompletions` | Dot | 10 | Type-aware member method completions |

### Completion Styles

**BIF Completions** (configurable):
- `basic` — Function name only: `writeDump`
- `required` — Required params: `writeDump(${1:var})`
- `full` — All params: `writeDump(${1:var}, ${2:top}, ${3:abort})`

**Component Completions** (configurable):
- Same styles as BIFs
- Names: `basic` (`find`) or `full` (`find():query`)

---

## Documentation System

### Documentation Sources

| Source | Type | URL Pattern |
|--------|------|-------------|
| BIFs | Inline | `boxlang.ortusbooks.com/.../built-in-functions/bifs/{name}` |
| Tags | Inline | `boxlang.ortusbooks.com/.../components/{name}` |
| Components | Indexed | From project index metadata |
| Variables | Indexed | From variable-to-component mapping |

### Popup Architecture

```
┌─────────────────────────────────────────┐
│  [side-color bar]  function_name()      │  ← Header
├─────────────────────────────────────────┤
│  Description text                       │  ← Body
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ param_name: type                  │  │  ← Card
│  │ Description of parameter          │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │ param_name: type                  │  │  ← Card
│  │ Description of parameter          │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│  boxlang.ortusbooks.com/.../function    │  ← Links
├─────────────────────────────────────────┤
│  ← 1/3 →                                │  ← Pagination
└─────────────────────────────────────────┘
```

---

## Indexing System

### Indexing Flow

```
index_project(project_name, callback)
    │
    ├── Get project data (.sublime-project)
    │   └── boxlang_cfc_folders configuration
    │
    ├── Walk configured folders
    │   └── Collect all .bx/.bxs files
    │
    ├── For each file (async):
    │   ├── parse_file(file_path)
    │   │   └── ASTParser or TagParser
    │   │
    │   ├── _file_to_dot_path(file_path)
    │   │   └── Using project mappings
    │   │
    │   └── Store in project_indexes[project_name][dot_path]
    │
    └── callback(indexed, total) for progress
```

### Dot-Path Resolution

```
resolve_path(project_name, current_file, dot_path)
    │
    ├── Convert dot path to file path
    │   └── "model.UserService" → "model/UserService.bx"
    │
    ├── For each project mapping:
    │   ├── Check if file path starts with mapping prefix
    │   ├── Calculate relative path
    │   └── Resolve to absolute path
    │
    └── Return file path if exists, else None
```

### Inheritance Resolution

```
_extend_metadata(metadata, project_name)
    │
    ├── If metadata has "extends":
    │   ├── resolve_path() to find parent file
    │   ├── get_extended_metadata_by_file_path()
    │   │   └── Recursively extend parent
    │   └── Merge parent functions (child overrides)
    │
    └── Return extended metadata
```

---

## Error Handling

### Parse Errors

When AST parsing fails:
1. Error captured in `parse_errors` array of metadata
2. `error_panel.show_errors()` displays in output panel
3. Error regions highlighted in source file
4. F4/Shift+F4 navigates between errors

### CLI Errors

When BoxLang CLI is unavailable:
1. Detection completes with `is_installed() = False`
2. Wizard shows install instructions
3. Syntax highlighting still works
4. Indexing, formatting, and compilation are disabled

### Graceful Degradation

| Feature | CLI Required | Fallback |
|---------|--------------|----------|
| Syntax highlighting | No | Always works |
| BIF completions | No | JSON-driven |
| Tag completions | No | JSON-driven |
| Component indexing | Yes | Disabled |
| Dot-path completions | Yes | Disabled |
| Type inference | Yes | Returns "any" |
| Formatting | Yes | Disabled |
| Build/Run | Yes | Disabled |

---

## Configuration

### Settings File

`settings/boxlang.sublime-settings` contains all package settings with defaults.

### Project Configuration

In `.sublime-project`:
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

### Settings Priority

1. Project settings (`.sublime-project`)
2. User settings (`boxlang.sublime-settings` in User package)
3. Default settings (`settings/boxlang.sublime-settings`)

---

## Build & Run

### Build System

`BoxLang.sublime-build` defines the default build and variants:

| Variant | Command | Use Case |
|---------|---------|----------|
| Default | `boxlang "$file"` | Run current file |
| Run with Arguments | `boxlang "$file" ${args}` | Run with CLI args |
| Compile File | `boxlang compile --source "$file" --target "./bin"` | Compile single file |
| Compile Project | `boxlang compile --source "$file_path" --target "./bin"` | Compile entire project |
| Debug | `boxlang --bx-debug "$file"` | Debug execution |
| Feature Audit | `boxlang featureaudit --source "$file_path"` | Audit BoxLang features |

### Auto-Compile on Save

When `boxlang_auto_compile_on_save: true`:
- On file save, runs `boxlang compile`
- Target directory from `boxlang_compile_target` (default: `./bin`)

---

## Extending the Package

### Adding a New Plugin

1. Create `src/plugins_/myplugin/__init__.py`
2. Implement `BoxlangPlugin` class
3. Add `"myplugin"` to `directory` in `src/boxlang_plugins.py`
4. Call `_plugin_loaded()` for initialization if needed

### Adding a New Syntax Feature

1. Update relevant `.sublime-syntax` file
2. Add new scope to `SELECTORS` in `inline_documentation.py` if needed
3. Add style setting in `boxlang.sublime-settings` if needed

### Adding a New CLI Feature

1. Add method to `boxlang_cli.py`
2. Follow async pattern with callback support
3. Add error handling for timeout and missing CLI

### Adding a New Completion Type

1. Create new plugin or extend existing one
2. Implement `get_completions()` with proper context checks
3. Return `CompletionList` with appropriate priority

---

## Testing

### Test Structure

```
tests/
├── conftest.py           # Pytest fixtures
├── expectations.py       # TestBox-style assertions
├── run_tests.py          # Test runner CLI
├── unit/                 # Unit tests
├── integration/          # Integration tests
└── fixtures/             # Test fixture files
```

### Running Tests

```bash
# All tests
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=src --cov-report=html

# Specific file
python -m pytest tests/unit/test_ast_parser.py -v

# Using test runner
python tests/run_tests.py --coverage --verbose
```

### TestBox-Style Expectations

```python
from tests.expectations import expect

expect(actual).to_be(expected)
expect(collection).to_contain(item)
expect(string).to_match(pattern)
expect(value).to_be_gt(other)
```

---

## Performance Considerations

### Async Operations

All potentially blocking operations run in background threads:
- CLI detection (`boxlang --version`)
- AST parsing (`boxlang --bx-printast`)
- Project indexing (file walking + parsing)
- Formatting (`boxlang format`)
- Compilation (`boxlang compile`)

### Caching

| Cache | Key | Invalidation |
|-------|-----|--------------|
| Buffer metadata | `view.buffer_id()` | On modification (500ms debounce) |
| Variable mappings | `project_name` | On index rebuild |
| Dot-path completions | `project_name` | On index rebuild |
| Type resolution | `(type, var_name, position)` | Per-session |
| CLI detection | Global | On plugin reload |

### Indexing Optimization

- Files indexed sequentially in background thread
- Progress callback updates status bar
- Index stored in memory (no disk persistence)
- Re-indexed on project change or manual trigger

---

## Known Limitations

1. **AST for `.bxm`** — `boxlang --bx-printast` does not support markup files; uses regex-based tag parser
2. **AST class parsing** — BoxLang v1.13.0 parses `class` as `BoxIdentifier` expressions, requiring sequential pattern matching
3. **Java introspection** — `createObject("java", "...")` types resolve as `"any"`; deferred to later phase
4. **MCP server** — Available at `boxlang.ortusbooks.com/~gitbook/mcp` but deferred to Phase 5
5. **No disk persistence** — Index is in-memory only; rebuilt on each session
6. **Single-threaded indexing** — Files indexed sequentially; could be parallelized

---

## Future Roadmap

### Phase 2 (Current)
- [x] Error panel with F4 navigation
- [x] Type inference engine (medium depth)
- [x] Type-aware completions
- [x] Status bar integration
- [x] Mouse bindings for go-to-definition
- [x] Code snippets

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

## Contributing

1. Read `AGENTS.md` for project knowledge base
2. Load relevant skill from `.agents/skills/` for domain-specific guidance
3. Follow existing code conventions (naming, structure, patterns)
4. Add tests for new features
5. Run `python -m pytest tests/` before submitting
6. No dead code — remove unused features from CFML patterns
7. AST-only parsing for `.bx`/`.bxs` — no regex fallback
