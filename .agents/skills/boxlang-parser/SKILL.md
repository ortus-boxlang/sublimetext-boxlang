---
name: boxlang-parser
description: "Work with BoxLang component parsers (AST parser for .bx/.bxs, tag parser for .bxm). Use when modifying parsing logic, adding new AST node types, or extending metadata extraction."
---

# BoxLang Parser Skill

Use this skill when working with the component parsing system for BoxLang files.

## Parser Architecture

```
component_parser/__init__.py (router)
├── ast_parser.py      → .bx, .bxs files (uses boxlang --bx-printast)
└── tag_parser.py      → .bxm files (flexible tag tokenizer)
```

## AST Parser (`ast_parser.py`)

### How It Works
1. Calls `boxlang --bx-printast <file>` (or `--bx-code "..."` for strings)
2. Parses JSON output into component metadata
3. Pattern-matches AST nodes to extract class/function/property info

### Critical AST Pattern: Class Declarations

BoxLang v1.13.0 does **NOT** emit `BoxClassDeclaration`. Classes parse as sequential statements:

```
[0] BoxExpressionStatement { expression: BoxIdentifier("class") }
[1] BoxExpressionStatement { expression: BoxIdentifier("ClassName") }
[2] BoxExpressionStatement { expression: BoxAssignment("extends", BoxStringLiteral("BaseClass")) }
[3] BoxExpressionStatement { expression: BoxAssignment("implements", BoxStringLiteral("Interface1,Interface2")) }
[4] BoxStatementBlock { body: [...] }
```

**Parsing algorithm:**
1. Find `BoxIdentifier("class")`
2. Next `BoxIdentifier` (not "extends"/"implements") = class name
3. `BoxAssignment` with left.name="extends" = parent class
4. `BoxAssignment` with left.name="implements" = interfaces (comma-separated)
5. `BoxStatementBlock` = class body

### AST Node Types

| Node Type | Purpose | Key Fields |
|-----------|---------|------------|
| `BoxIdentifier` | Variable/class names | `name` |
| `BoxAssignment` | Key-value assignments | `left`, `right` |
| `BoxStringLiteral` | String values | `value` |
| `BoxExpressionStatement` | Expression wrapper | `expression` |
| `BoxStatementBlock` | Code block | `body` |
| `BoxFunctionDeclaration` | Function definition | `name`, `args`, `type`, `accessModifier`, `annotations` |
| `BoxPropertyDeclaration` | Property definition | `name`, `type`, `accessModifier`, `value` |
| `BoxDocComment` | Documentation comment | `annotations` |
| `BoxDocumentationAnnotation` | Doc annotation | `key`, `value` |
| `BoxAnnotation` | Code annotation | `name` |

### Function Extraction

```python
def _extract_function(func_node):
    return {
        "name": func_node.get("name", "unknown"),
        "return_type": _extract_return_type(func_node.get("type", {})),
        "access": func_node.get("accessModifier", {}).get("sourceText", "").lower(),
        "args": [
            {
                "name": arg.get("name", ""),
                "type": arg.get("type"),
                "required": arg.get("required", False),
                "default": arg.get("value")
            }
            for arg in func_node.get("args", [])
        ],
        "annotations": [
            ann.get("name", "")
            for ann in func_node.get("annotations", [])
            if ann.get("ASTType") == "BoxAnnotation"
        ],
        "line": func_node.get("position", {}).get("start", {}).get("line", 0)
    }
```

### Return Type Extraction

The AST nests type info differently depending on context:
```python
# Direct type node
type_node.get("type", {}).get("sourceText")
# Or direct sourceText
type_node.get("sourceText")
```

## Tag Parser (`tag_parser.py`)

### How It Works
1. Reads `.bxm` file content
2. Uses regex to find `<bx:tagname ...>` patterns
3. Determines body presence based on tag category
4. Extracts function/property metadata from tags
5. Parses `<bx:script>` blocks via AST parser

### Tag Categories

**Self-Closing** (no body, no closing tag):
```python
SELF_CLOSING_TAGS = {
    "abort", "associate", "break", "continue", "dump", "exit",
    "flush", "httpparam", "include", "invokeargument", "log",
    "param", "procparam", "procresult", "queryparam", "rethrow",
    "return", "schedule", "setting", "sleep", "throw", "trace", "zipparam"
}
```

**Optional Body** (may or may not have closing tag):
```python
OPTIONAL_BODY_TAGS = {
    "cache", "execute", "http", "invoke", "invokeargument",
    "object", "processingdirective", "thread", "transaction", "zip"
}
```

**Required Body** (must have closing tag):
```python
REQUIRED_BODY_TAGS = {
    "lock", "loop", "output", "query", "savecontent",
    "silent", "storedproc", "timer", "xml"
}
```

### `<bx:script>` Block Parsing

Script blocks inside `.bxm` files are parsed by passing their content to the AST parser:
```python
def _parse_script_block(content):
    ast, error = boxlang_cli.run_ast_code(content)
    if error:
        return {"functions": {}}
    # Extract BoxFunctionDeclaration nodes from AST
    functions = {}
    for stmt in ast.get("statements", []):
        if stmt.get("ASTType") == "BoxFunctionDeclaration":
            func_meta = ASTParser._extract_function(stmt)
            functions[func_meta["name"]] = func_meta
    return {"functions": functions}
```

## Metadata Output Format

All parsers return this structure:
```python
{
    "name": "ClassName",           # Class name or None
    "extends": "ParentClass",      # Parent class or None
    "implements": ["Interface1"],  # List of interfaces
    "functions": {                 # Dict of function metadata
        "functionName": {
            "name": "functionName",
            "return_type": "string",
            "access": "public",
            "args": [...],
            "annotations": [...],
            "line": 10
        }
    },
    "properties": {                # Dict of property metadata
        "propertyName": {
            "name": "propertyName",
            "type": "string",
            "access": "public",
            "default": None,
            "line": 5
        }
    },
    "annotations": [...],          # Class-level annotations
    "parse_errors": [...]          # Any errors during parsing
}
```

## Adding New AST Node Support

1. Identify the AST node type from `boxlang --bx-printast` output
2. Add extraction logic in `_extract_metadata()` or new `_extract_*()` method
3. Update the metadata output format
4. Add tests for the new node type

## Adding New Tag Support

1. Determine if tag is self-closing, optional body, or required body
2. Add to appropriate set in `tag_parser.py`
3. If tag has special metadata extraction, add handler in `parse_string()`
4. Update syntax definition if needed

## Error Handling

- AST parsing errors are captured and returned in `parse_errors` array
- Tag parser gracefully handles missing closing tags (treats as self-closing)
- Script block parsing failures return empty functions dict, not errors
- File read errors are caught and returned as parse errors
