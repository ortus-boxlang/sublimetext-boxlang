# AGENTS.md - BoxLang Sublime Text Package

> Complete knowledge base for AI agents working on the `sublimetext-boxlang` Sublime Text 4 package.

## Project Overview

**Package Name:** BoxLang
**Repository:** `~/Sites/projects/sublimetext-boxlang/`
**Target:** Sublime Text 4 (Build 4180+)
**Language:** BoxLang (JVM-based CFML successor by Ortus Solutions)
**File Extensions:** `.bx` (script classes), `.bxs` (script-only), `.bxm` (module templates)
**Optional CFML Fallback:** `.cfc`, `.cfm`, `.cfs` (disabled by default)

## BoxLang CLI Dependency

The package **requires** the BoxLang CLI for core features:
- **Executable:** `boxlang` (configurable via `boxlang_executable_path` setting)
- **Detection:** Runs `boxlang --version` on plugin load in background thread
- **Location:** Typically installed via BVM at `~/.bvm/current/bin/boxlang`
- **Version:** v1.13.0+54 (current detected)

### CLI Commands Used
| Command | Purpose |
|---------|---------|
| `boxlang --version` | Version detection |
| `boxlang --bx-printast <file>` | AST parsing for `.bx`/`.bxs` |
| `boxlang --bx-printast --bx-code "..."` | AST parsing from string (for `<bx:script>` blocks) |
| `boxlang format <file>` | Code formatting |
| `boxlang compile --source <src> --target <tgt>` | Compilation to bytecode |
| `boxlang --bx-debug <file>` | Debug execution |
| `boxlang featureaudit --source <src>` | Feature audit |

## Architecture

### Core Philosophy
1. **AST-only parsing** for `.bx`/`.bxs` — zero regex fallback, 100% accuracy via `boxlang --bx-printast`
2. **Flexible tag tokenizer** for `.bxm` — not strict XML, handles self-closing tags derived from `@BoxComponent` annotations
3. **Zero dead code** from CFML package — only BoxLang features, no legacy CFML baggage
4. **Plugin-based completion/documentation system** — extensible via `BoxlangPlugin` base class

### Directory Structure
```
sublimetext-boxlang/
├── src/                              # Python source code
│   ├── __init__.py                   # Plugin entry point (plugin_loaded/unloaded)
│   ├── boxlang_cli.py                # CLI wrapper (version, AST, format, compile)
│   ├── boxlang_view.py               # View context analysis (cursor position, type detection)
│   ├── boxlang_plugins.py            # Plugin loader (loads all plugins_/*.py)
│   ├── completions.py                # Completion orchestrator
│   ├── inline_documentation.py       # Popup documentation system (F1, hover)
│   ├── documentation_helpers.py      # HTML generation helpers for docs
│   ├── minihtml.py                   # MiniHTML style utilities
│   ├── buffer_metadata.py            # Per-buffer metadata caching
│   ├── component_index/__init__.py   # Project indexer (dot-path resolution, inheritance)
│   ├── component_index/completions.py # (empty - reserved)
│   ├── component_index/documentation.py # (empty - reserved)
│   ├── component_parser/__init__.py  # Parser router (AST vs Tag)
│   ├── component_parser/ast_parser.py # AST parser for .bx/.bxs
│   ├── component_parser/tag_parser.py # Tag parser for .bxm
│   ├── error_panel.py                # Parse error display with F4 navigation
│   ├── type_resolver.py              # Medium-depth type inference engine
│   ├── status_bar.py                 # Status bar (version, indexing, errors)
│   ├── goto_boxlang_file.py          # Go-to-definition (files + URLs)
│   ├── events.py                     # Pub/sub event bus
│   ├── utils.py                      # Utility functions (paths, scopes, settings)
│   ├── commands/
│   │   ├── __init__.py
│   │   └── wizard.py                 # First-run setup wizard
│   └── plugins_/                     # Completion/documentation plugins
│       ├── __init__.py
│       ├── plugin.py                 # BoxlangPlugin base class
│       ├── basecompletions/__init__.py # BIFs, tags, member functions (JSON-driven)
│       ├── basecompletions/json/     # Completion data files
│       │   ├── boxlang_tags.json     # 41 tags
│       │   ├── boxlang_functions.json # 560 BIFs
│       │   └── boxlang_member_functions.json # 72 member functions
│       ├── boxdocs/__init__.py       # URL-based inline docs (boxlang.ortusbooks.com)
│       ├── cfcs/__init__.py          # Indexed component variable completions
│       ├── dotpaths/__init__.py      # Import/new/createObject dot-path completions
│       ├── typecompletions/__init__.py # Type-aware member method completions
│       ├── applicationbx/__init__.py # (empty - reserved for Application.cfc-like)
│       └── in_file_completions/__init__.py # (empty - reserved)
├── syntaxes/
│   ├── BoxLang.sublime-syntax        # Script syntax (source.boxlang) for .bx/.bxs
│   └── BoxLangMarkup.sublime-syntax  # Markup syntax (embedding.boxlang.markup) for .bxm
├── settings/
│   └── boxlang.sublime-settings      # All package settings
├── templates/
│   ├── inline_documentation.html     # F1/hover doc popup template
│   ├── completion_doc.html           # Auto-complete doc popup template
│   └── pagination.html               # Multi-page doc pagination
├── commands/
│   └── Default.sublime-commands      # Command palette entries
├── inputmaps/
│   └── Default.sublime-keymap        # Keyboard shortcuts
├── Default.sublime-mousemap          # Mouse bindings (Ctrl/Cmd+click go-to-def)
├── BoxLang.sublime-build             # Build system (run, compile, debug, audit)
├── metadata/
│   └── boxlang.tmPreferences         # Symbol list transformations
└── snippets/                         # Code snippets
    ├── bxclass.sublime-snippet       # Class declaration
    ├── bxinterface.sublime-snippet   # Interface declaration
    ├── bxcomponent.sublime-snippet   # Component declaration
    ├── bxfunc.sublime-snippet        # Function declaration
    ├── bxtest.sublime-snippet        # Test block (describe/it)
    ├── bxtry.sublime-snippet         # Try/catch
    ├── bxfor.sublime-snippet         # For loop
    ├── bxforeach.sublime-snippet     # For-in loop
    ├── bxif.sublime-snippet          # If statement
    └── bxscript.sublime-snippet      # <bx:script> block
```

## Key Modules

### `boxlang_cli.py` — CLI Wrapper
- **`initialize()`** — Detects BoxLang installation via `boxlang --version` in background thread
- **`run_ast(file_path)`** — Returns `(ast_dict, error)` tuple from `boxlang --bx-printast`
- **`run_ast_code(code)`** — Parses code string via `--bx-code` flag
- **`run_format(file_path)`** — Runs `boxlang format`
- **`run_compile(source, target)`** — Runs `boxlang compile`
- **`on_detection_complete(callback)`** — Register callback for detection completion
- **`is_installed()` / `get_version()` / `get_executable()`** — State accessors

### `component_parser/ast_parser.py` — AST Parser
Parses `.bx`/`.bxs` files using `boxlang --bx-printast` output.

**Key AST Pattern for Classes:**
The BoxLang AST does **not** use `BoxClassDeclaration`. Instead, class declarations parse as sequential statements:
```
BoxIdentifier("class") → BoxIdentifier("ClassName") → BoxAssignment("extends", "Parent") → BoxAssignment("implements", "Interface") → BoxStatementBlock
```

**Extracted Metadata:**
- `name` — Class name from `BoxIdentifier` after `class` keyword
- `extends` — Parent class from `BoxAssignment` with left.name="extends"
- `implements` — Interfaces from `BoxAssignment` with left.name="implements" (comma-separated)
- `functions` — From `BoxFunctionDeclaration` nodes in class body
- `properties` — From `BoxPropertyDeclaration` nodes
- `annotations` — From `BoxDocComment` → `BoxDocumentationAnnotation` nodes

### `component_parser/tag_parser.py` — Tag Parser
Flexible tokenizer for `.bxm` template files. **Not strict XML.**

**Self-Closing Tags** (from `@BoxComponent` annotations with `allowsBody=false`, `requiresBody=false`):
```
abort, associate, break, continue, dump, exit, flush, httpparam, include,
invokeargument, log, param, procparam, procresult, queryparam, rethrow,
return, schedule, setting, sleep, throw, trace, zipparam
```

**Optional Body Tags** (`allowsBody=true`, `requiresBody=false`):
```
cache, execute, http, invoke, processingdirective, thread, transaction, zip
```

**Required Body Tags** (`requiresBody=true`):
```
lock, loop, output, query, savecontent, silent, storedproc, timer, xml
```

**`<bx:script>` blocks** are parsed via `boxlang --bx-printast --bx-code "..."` and merged into metadata.

### `component_index/__init__.py` — Project Indexer
Indexes all `.bx`/`.bxs` files in configured project folders.

- **`index_project(project_name, callback)`** — Async indexing with progress callback
- **`get_indexed_metadata(project_name, dot_path)`** — Get metadata by dot path
- **`get_indexed_metadata_by_dotpath(dot_path)`** — Search all projects by dot path
- **`resolve_path(project_name, current_file, dot_path)`** — Resolve dot path to file path using project mappings
- **`get_dot_paths(project_name)`** — All indexed dot paths
- **`get_completions_by_file_path/dot_path`** — Build completion items from metadata
- **`_extend_metadata`** — Merges inherited functions from parent classes

**Project Configuration** (in `.sublime-project`):
```json
{
  "boxlang_cfc_folders": [
    {
      "path": "model",
      "variable_names": ["{cfc}", "{cfc_folder_singularized}"],
      "accessors": true
    }
  ],
  "mappings": [
    { "path": "/path/to/project", "mapping": "/" }
  ]
}
```

### `boxlang_view.py` — View Context
Analyzes cursor position to determine completion/documentation context.

**Context Types:**
- `"tag"` — Typing tag name in markup
- `"tag_attributes"` — Typing attribute name or value
- `"dot"` — After `.` accessor (member completions)
- `"script"` — General script context

**Key Properties:**
- `dot_context` — Chain of identifiers before `.` (e.g., `userService` in `userService.find()`)
- `function_call_params` — Parsed function call arguments with named/positional detection
- `tag_name` / `tag_attribute_name` / `tag_location` — Tag context details

### `plugins_/` — Plugin System

**Base Class:** `BoxlangPlugin` in `plugins_/plugin.py`
```python
class BoxlangPlugin:
    def get_completions(self, boxlang_view): ...
    def get_completion_docs(self, boxlang_view): ...
    def get_inline_documentation(self, boxlang_view, doc_type): ...
    def get_goto_boxlang_file(self, boxlang_view): ...
    def get_method_preview(self, boxlang_view): ...
```

**Plugin Loading:** `boxlang_plugins.py` loads all plugins listed in `directory` array. Any class named `BoxlangPlugin` that subclasses the base class is instantiated and added to `plugins` list.

**Current Plugins:**

| Plugin | Purpose |
|--------|---------|
| `basecompletions` | BIFs (560), tags (41), member functions (72) from JSON data |
| `boxdocs` | Inline documentation linking to boxlang.ortusbooks.com |
| `cfcs` | Variable-to-component mapping completions and go-to-definition |
| `dotpaths` | Import/new/createObject dot-path completions |
| `typecompletions` | Type-aware member method completions (uses TypeResolver) |
| `applicationbx` | Application.bx lifecycle method completions (onApplicationStart, onRequestStart, etc.) |
| `in_file_completions` | Current file symbol completions (functions, variables, properties) |

### `type_resolver.py` — Type Inference Engine
Medium-depth type inference (not full static analysis).

**Resolution Sources:**
1. **Literals** — `"string"` → string, `123` → numeric, `[]` → array, `{}` → struct, `true/false` → boolean
2. **`new` expressions** — `new UserService()` → `component:UserService`
3. **`createObject()`** — `createObject("component", "model.UserService")` → `component:model.UserService`
4. **BIF return types** — `arrayNew()` → array, `now()` → datetime, etc. (60+ known BIFs)
5. **Variable assignments** — Traces back to assignment and infers from RHS
6. **Dot chains** — Resolves type through chain of member accesses
7. **Component metadata** — Looks up function return types from indexed components

**Return Format:**
- Built-in types: `"string"`, `"array"`, `"struct"`, `"numeric"`, `"boolean"`, `"query"`, `"datetime"`, etc.
- Component types: `"component:path.to.ComponentName"`
- Unknown: `"any"`

### `error_panel.py` — Error Display
- **`show_errors(view, file_path, errors)`** — Shows errors in output panel + highlights regions
- **`clear_errors(view)`** — Clears error regions
- **`navigate_next/prev(view)`** — F4/Shift+F4 navigation between errors
- Error format: `{ "line": N, "column": N, "message": "..." }`

### `status_bar.py` — Status Bar
Displays in Sublime Text status bar:
- BoxLang version: `BoxLang v1.13.0+54`
- Indexing progress: `Indexing: 45/120 (37%)`
- Error count: `BoxLang: 3 error(s)`

### `events.py` — Pub/Sub Event Bus
Simple event system used internally:
```python
events.subscribe("on_load_async", callback)
events.trigger("on_load_async", view)
events.unsubscribe("on_load_async", callback)
```

### `buffer_metadata.py` — Buffer Metadata Cache
Caches parsed metadata per buffer ID. Subscribes to `on_load_async`, `on_modified_async`, `on_close` events. Debounces modifications (500ms cooldown).

## Settings Reference

All settings in `settings/boxlang.sublime-settings`:

| Setting | Default | Description |
|---------|---------|-------------|
| `boxlang_executable_path` | `null` | Custom BoxLang CLI path |
| `boxlang_enable_cfml_fallback` | `false` | Enable `.cfc`/`.cfm`/`.cfs` support |
| `boxlang_bif_completions` | `"required"` | BIF completion style: `basic`/`required`/`full` |
| `boxlang_cfc_completions` | `"required"` | Component completion style |
| `boxlang_cfc_completion_names` | `"basic"` | Include return type in name: `basic`/`full` |
| `boxlang_instantiated_component_completions` | `true` | Variable-to-component completions |
| `boxlang_auto_insert_closing_tag` | `false` | Auto-insert closing tag on `>` |
| `boxlang_between_tag_pair` | `"default"` | Enter behavior between tags |
| `boxlang_non_closing_tags` | `[...]` | Self-closing bx: tags list |
| `boxlang_inline_doc_regions_highlight` | `true` | Highlight doc regions |
| `boxlang_hover_docs` | `true` | Enable hover documentation |
| `boxlang_completion_docs` | `true` | Enable completion docs popup |
| `boxlang_tag_style` | `{...}` | Tag foreground color/style |
| `boxlang_tag_attribute_style` | `{...}` | Attribute foreground color/style |
| `boxlang_controller_folders` | `["controllers","handlers"]` | Controller folder names |
| `boxlang_view_folders` | `["views"]` | View folder names |
| `boxlang_testbox_enabled` | `true` | Enable TestBox integration |
| `boxlang_auto_compile_on_save` | `false` | Auto-compile to `./bin` on save |
| `boxlang_compile_target` | `"./bin"` | Compilation target directory |
| `boxlang_format_on_save` | `false` | Auto-format on save |
| `boxlang_log_in_file_parse_time` | `false` | Log parse timing |
| `boxlang_log_doc_time` | `false` | Log doc generation timing |
| `boxlang_wizard_completed` | `false` | Internal wizard flag |

## Keyboard Shortcuts

| Keys | Command | Context |
|------|---------|---------|
| `F1` | `boxlang_inline_documentation` | Show inline docs |
| `Ctrl+F1` | `boxlang_controller_view_toggle` | Toggle controller/view |
| `Ctrl+Alt+D` | Insert `writeDump(${1:var});` | Quick debug |
| `Ctrl+Shift+O` | Insert `writeOutput(${1:output});` | Quick output |
| `Ctrl+Alt+A` | Insert `abort;` | Quick abort |
| `Shift+Alt+F` | `boxlang_format` | Format code |
| `Shift+Alt+D` | `boxlang_inject_property` | DI property injection |
| `#` | `boxlang_wrap_hash` | Wrap selection in `##` |
| `Ctrl/Cmd+Click` | `boxlang_goto_file` | Go to definition |
| `F4` | `boxlang_next_error` | Next parse error |
| `Shift+F4` | `boxlang_prev_error` | Previous parse error |
| `Ctrl+B` | Build | Run current file |

## Build System Variants

| Variant | Command |
|---------|---------|
| Default | `boxlang "$file"` |
| Run with Arguments | `boxlang "$file" ${args}` |
| Compile File | `boxlang compile --source "$file" --target "./bin"` |
| Compile Project | `boxlang compile --source "$file_path" --target "./bin"` |
| Debug | `boxlang --bx-debug "$file"` |
| Feature Audit | `boxlang featureaudit --source "$file_path"` |

## Completion Data Generation

Completion JSON files are generated from BoxLang source:
- **Tags:** Extracted from `boxlang/src/main/java/ortus/boxlang/runtime/components/` (41 components)
- **BIFs:** Extracted from BoxLang function registry (560 functions)
- **Member Functions:** Extracted from BoxLang member method registry (72 methods)

## Wizard Flow

First-run wizard (`src/commands/wizard.py`):
1. **Welcome** — Detects BoxLang, shows version or install instructions
2. **CFML Support** — Asks about CFML fallback (auto-disables if CFML package installed)
3. **Done** — Shows quick tips, offers to open settings

Re-run via Command Palette: `BoxLang: Run Setup Wizard`

## Scope Selectors

### Script Syntax (`source.boxlang`)
- `variable.language.boxlang` — Highlights BoxLang language scopes: `this`, `variables`, `thread`, `session`, `client`, `server`, `cgi`, `form`, `url`, `cookie`, `application`, `request`, `arguments`, `super`
- `storage.modifier.boxlang` — `static`, `final`, `abstract` modifiers
- `storage.type.primitive.boxlang` — Built-in types: `any`, `array`, `boolean`, `numeric`, `string`, `struct`, etc.
- `storage.type.object.boxlang` — Component/class types
- `storage.type.function.boxlang` — `function` keyword and function type
- `storage.type.void.boxlang` — `void` return type
- `entity.name.class.boxlang` — Class names in `new` expressions and declarations
- `entity.name.function.boxlang` — Function names in declarations and calls
- `meta.function.declaration.boxlang` — Full function declaration scope
- `meta.function.parameters.boxlang` — Function parameter scope
- `meta.function.body.boxlang` — Function body scope
- `meta.class.declaration.boxlang` — Class declaration scope
- `meta.class.body.boxlang` — Class body scope
- `meta.block.static.boxlang` — Static block scope (`static { }`)
- `meta.instance.constructor.boxlang` — `new` constructor scope
- `meta.struct-literal.boxlang` — Struct literal scope
- `meta.sequence.boxlang` — Array literal scope
- `meta.import.boxlang` — Import statement scope
- `meta.switch.boxlang`, `meta.for.boxlang`, `meta.while.boxlang`, `meta.try.boxlang`, `meta.catch.boxlang`, `meta.finally.boxlang`, `meta.conditional.boxlang` — Control flow meta scopes
- `meta.binding.name.boxlang` — Variable binding scope
- `meta.binding.destructuring.sequence.boxlang` — Array destructuring
- `meta.binding.destructuring.mapping.boxlang` — Struct destructuring
- `meta.property.boxlang` — Property access scope
- `meta.property.constant.boxlang` — Constant property access (UPPER_CASE)
- `meta.parameter.optional.boxlang` — Optional parameter with default value
- `punctuation.accessor.boxlang` — `.` accessor
- `punctuation.accessor.safe.boxlang` — `?.` safe accessor
- `punctuation.accessor.static.boxlang` — `::` static accessor
- `punctuation.section.parameters.begin/end.boxlang` — Function parameter parentheses
- `keyword.operator.word.new.boxlang` — `new` keyword
- `keyword.operator.ternary.boxlang` — `?` and `:` ternary operators
- `keyword.operator.spread.boxlang` — `...` spread operator
- `keyword.operator.rest.boxlang` — `...` rest parameter
- `keyword.operator.logical.binary.boxlang` — `&&`, `||`, `and`, `or`, `xor`
- `keyword.operator.comparison.binary.boxlang` — `===`, `!==`, `==`, `!=`, `<>`
- `keyword.operator.relational.binary.boxlang` — `<=`, `>=`, `<`, `>`
- `keyword.operator.arithmetic.binary.boxlang` — `+`, `-`, `*`, `/`, `%`, `mod`
- `keyword.operator.assignment.augmented.binary.boxlang` — `+=`, `-=`, `*=`, `/=`, `%=`, `&=`
- `keyword.operator.concat.binary.boxlang` — `&` string concat
- `keyword.operator.binary.boxlang` — `in` operator
- `keyword.operator.arithmetic.postfix.boxlang` — `++`, `--` postfix
- `keyword.control.static.boxlang` — `static` keyword for static blocks
- `keyword.control.conditional.switch.boxlang` — `switch` keyword
- `keyword.control.conditional.case.boxlang` — `case` keyword
- `keyword.control.conditional.default.boxlang` — `default` keyword
- `keyword.control.loop.for.boxlang` — `for` keyword
- `keyword.control.loop.while.boxlang` — `while` keyword
- `keyword.control.loop.do-while.boxlang` — `do` keyword
- `keyword.control.exception.try.boxlang` — `try` keyword
- `keyword.control.exception.catch.boxlang` — `catch` keyword
- `keyword.control.exception.finally.boxlang` — `finally` keyword
- `keyword.control.flow.break.boxlang` — `break` keyword
- `keyword.control.flow.continue.boxlang` — `continue` keyword
- `keyword.control.flow.return.boxlang` — `return` keyword
- `keyword.control.flow.throw.boxlang` — `throw`/`rethrow` keywords
- `keyword.other.required.parameter.boxlang` — `required` parameter modifier
- `entity.name.label.boxlang` — Loop labels
- `variable.label.boxlang` — Label reference after `break`/`continue`
- `support.type.exception.boxlang` — Exception type in catch binding
- `variable.function.boxlang` — Function call (non-method)
- `variable.other.object.boxlang` — Variable followed by `.` or `[`
- `variable.other.constant.boxlang` — UPPER_CASE constant identifiers
- `variable.type.boxlang` — Java type in `new java`
- `constant.language.boolean.true.boxlang` — `true` literal
- `constant.language.boolean.false.boxlang` — `false` literal
- `constant.language.null.boxlang` — `null` literal
- `constant.numeric.boxlang` — Numeric literals (int, float, hex `0x...`)
- `constant.character.escape.boxlang` — String escape sequences
- `entity.other.function-parameter.boxlang` — Named parameter in function call
- `storage.type.object.array.boxlang` — Array type with `[]` brackets

### Markup Syntax (`embedding.boxlang.markup`)
- Delegates embedded `<bx:script>` and `<bx:function>` blocks to `source.boxlang`

## Known Limitations

1. **AST for `.bxm`** — `boxlang --bx-printast` does not support `.bxm`/`.cfm` markup files yet; uses flexible tag parser instead
2. **AST class parsing** — BoxLang v1.13.0 parses `class` as `BoxIdentifier` expressions, not `BoxClassDeclaration` — requires sequential statement pattern matching
3. **Java class introspection** — Deferred to later phase; `createObject("java", "...")` types resolve as `"any"`
4. **MCP server** — `https://boxlang.ortusbooks.com/~gitbook/mcp` available but deferred to Phase 5

## Related Projects

- **CFML Package:** `/Users/lmajano/Sites/projects/sublimetext-cfml` (source of architectural patterns)
- **BoxLang Docs:** `/Users/lmajano/Sites/projects/boxlang-docs` (GitBook structure)
- **BoxLang Source:** BoxLang v1.13.0+54 at `~/.bvm/current/bin/boxlang`
- **BoxLang Docs URL:** `https://boxlang.ortusbooks.com`

## Contributing Guidelines

1. **No regex fallback for `.bx`/`.bxs`** — Always use AST parser
2. **Self-closing tags** must be derived from BoxLang source `@BoxComponent` annotations
3. **Plugin system** — Extend `BoxlangPlugin` base class for new features
4. **Type inference** — Keep at medium depth; no full static analysis
5. **Zero dead code** — Remove any non-BoxLang features from CFML package patterns
6. **CLI required** — All parsing/formatting/compilation delegates to `boxlang` CLI
