---
name: boxlang-plugin
description: "Create or modify BoxLang plugins for completions, inline documentation, and go-to-definition. Use when extending the plugin system with new features."
---

# BoxLang Plugin Skill

Use this skill when creating or modifying plugins for the BoxLang Sublime Text package.

## Plugin System Overview

Plugins are Python modules under `src/plugins_/` that extend the `BoxlangPlugin` base class. They provide:
- **Completions** — Auto-complete suggestions based on context
- **Completion Docs** — Documentation shown during auto-complete
- **Inline Documentation** — F1/hover popup documentation
- **Go-to-Definition** — File navigation from symbol

## Plugin Registration

Plugins are registered in `src/boxlang_plugins.py`:

```python
directory = [
    "basecompletions",
    "boxdocs",
    "cfcs",
    "dotpaths",
    "typecompletions",
    "applicationbx",       # Reserved
    "in_file_completions", # Reserved
]
```

The loader scans each module for a class named `BoxlangPlugin` that subclasses the base class and instantiates it.

## Base Class (`src/plugins_/plugin.py`)

```python
class BoxlangPlugin:
    """Base class for BoxLang plugins."""

    def get_completion_docs(self, boxlang_view):
        """Get completion documentation. Returns CompletionDoc or None."""
        return None

    def get_completions(self, boxlang_view):
        """Get completions. Returns CompletionList or None."""
        return None

    def get_goto_boxlang_file(self, boxlang_view):
        """Get file navigation info. Returns GotoBoxlangFile or None."""
        return None

    def get_inline_documentation(self, boxlang_view, doc_type):
        """Get inline documentation. Returns Documentation or None."""
        return None

    def get_method_preview(self, boxlang_view):
        """Get method preview. Returns MethodPreview or None."""
        return None
```

## BoxlangView Context

The `boxlang_view` parameter provides context about the current cursor position:

### Properties
| Property | Type | Description |
|----------|------|-------------|
| `view` | `sublime.View` | The Sublime Text view |
| `position` | `int` | Cursor position |
| `prefix` | `str` | Text being typed |
| `type` | `str` | Context: `"tag"`, `"tag_attributes"`, `"dot"`, `"script"` |
| `project_name` | `str` | Project file path |
| `file_path` | `str` | Current file path |
| `dot_context` | `list[Symbol]` | Chain of identifiers before `.` |
| `tag_name` | `str` | Current tag name (e.g., `"bx:query"`) |
| `tag_attribute_name` | `str` | Current attribute being typed |
| `tag_location` | `str` | `"tag_name"`, `"tag_attribute_name"`, `"tag_attributes"` |
| `function_call_params` | `BoxlangFunctionCallParams` | Parsed function call arguments |
| `view_metadata` | `dict` | Parsed metadata for current file |

### Named Tuples
```python
CompletionList(completions, priority, exclude_lower_priority)
Documentation(doc_regions, doc_html_variables, on_navigate, priority)
CompletionDoc(doc_regions, doc_html_variables, on_navigate)
MethodPreview(preview_regions, preview_html_variables, on_navigate, priority)
GotoBoxlangFile(file_path, symbol)
```

## Creating a New Plugin

### Step 1: Create Module

```
src/plugins_/myplugin/__init__.py
```

### Step 2: Implement BoxlangPlugin

```python
import sublime
from ... import utils

class BoxlangPlugin:
    """My custom plugin."""

    def get_completions(self, boxlang_view):
        if boxlang_view.type != "script":
            return None

        completions = [
            sublime.CompletionItem(
                "myFunction",
                "myplugin",
                "myFunction($1)$0",
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_FUNCTION, "f", "myplugin"),
                details="Does something useful"
            )
        ]
        return boxlang_view.CompletionList(completions, 0, False)

    def get_inline_documentation(self, boxlang_view, doc_type):
        if not boxlang_view.view.match_selector(
            boxlang_view.position, "entity.name.function.boxlang"
        ):
            return None

        word = boxlang_view.view.substr(boxlang_view.view.word(boxlang_view.position))
        if word == "myFunction":
            return boxlang_view.Documentation(
                [boxlang_view.view.word(boxlang_view.position)],
                {
                    "side_color": "#4C9BB0",
                    "html": {
                        "header": "myFunction()",
                        "body": "<p>Does something useful</p>",
                        "links": []
                    }
                },
                None,
                0
            )
        return None

    def get_goto_boxlang_file(self, boxlang_view):
        # Return file path or URL for navigation
        return None

    def get_completion_docs(self, boxlang_view):
        # Return documentation shown during auto-complete
        return None

    def get_method_preview(self, boxlang_view):
        # Return method signature preview
        return None
```

### Step 3: Register Plugin

Add to `directory` list in `src/boxlang_plugins.py`:
```python
directory = [
    ...
    "myplugin",
]
```

## Completion Item Types

```python
sublime.CompletionItem(
    trigger,           # Display text
    annotation,        # Small annotation (e.g., "function", "method")
    completion,        # Insertion text or snippet
    completion_format, # sublime.COMPLETION_FORMAT_TEXT or SNIPPET
    kind,              # (kind_id, icon, detail)
    details,           # Detailed description
    # Optional:
    text_edit,         # sublime.TextEdit for precise insertion
    command,           # Command to run on selection
)
```

### Kind IDs
| ID | Name | Typical Use |
|----|------|-------------|
| `sublime.KIND_ID_FUNCTION` | Function | Methods, BIFs |
| `sublime.KIND_ID_VARIABLE` | Variable | Properties, variables |
| `sublime.KIND_ID_MARKUP` | Markup | Tags |
| `sublime.KIND_ID_KEYWORD` | Keyword | Language keywords |
| `sublime.KIND_ID_TYPE` | Type | Classes, types |
| `sublime.KIND_ID_AMBIGUOUS` | Ambiguous | Generic items |
| `sublime.KIND_ID_NAVIGATION` | Navigation | Go-to items |

### Priority System
- Higher priority completions appear first
- `exclude_lower_priority=True` hides all lower-priority completions
- Typical priorities: 0 (base), 10 (type-aware), 100 (context-specific)

## Documentation HTML Format

```python
{
    "side_color": "#4C9BB0",
    "html": {
        "header": "Function signature or tag",
        "body": "<p>Description</p><h2>Parameters</h2>...",
        "links": [
            {"href": "https://...", "text": "Open in Docs"}
        ]
    }
}
```

### Available CSS Classes
- `entity_name_function` — Function names (yellow)
- `entity_name_tag_boxlang` — Tag names (blue)
- `entity_other_attribute_name` — Attributes (light blue)
- `storage_type` — Types (green)
- `variable_parameter_function` — Parameters (light blue)
- `keyword_other` — Keywords (purple)
- `card`, `card-header`, `card-body` — Card layout
- `code` — Inline code
- `active`, `required`, `optional` — Parameter states

## Existing Plugins Reference

| Plugin | Context | Provides |
|--------|---------|----------|
| `basecompletions` | All | BIFs, tags, member functions from JSON |
| `boxdocs` | Script/Tag | Inline docs linking to ortusbooks.com |
| `cfcs` | Script/Dot | Variable-to-component completions |
| `dotpaths` | Script/Dot | Import/new/createObject dot-path completions |
| `typecompletions` | Dot | Type-aware member method completions |

## Plugin Lifecycle

1. **Load:** `_plugin_loaded()` function called after all plugins loaded
2. **Completion:** `get_completions()` called on each auto-complete trigger
3. **Documentation:** `get_inline_documentation()` called on F1/hover
4. **Navigation:** `get_goto_boxlang_file()` called on Ctrl/Cmd+click

## Best Practices

1. **Check context type first** — Return `None` early if not relevant
2. **Use selectors** — `boxlang_view.view.match_selector(position, "scope")` for precise matching
3. **Cache expensive operations** — Use `_plugin_loaded()` for one-time setup
4. **Return proper named tuples** — Use `boxlang_view.CompletionList()`, etc.
5. **Handle missing data gracefully** — Return `None`, not errors
6. **Use settings** — `utils.get_setting("boxlang_*")` for configurable behavior
