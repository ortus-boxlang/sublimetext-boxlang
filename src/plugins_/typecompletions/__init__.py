"""
Type-aware member completions for BoxLang.
Provides completions based on inferred types from variable assignments,
new expressions, literals, and function return types.
"""

import sublime
from ... import utils
from ...type_resolver import TypeResolver
from ...component_index import component_index

SIDE_COLOR = "color(#4C9BB0 blend(var(--background) 60%))"


def get_dot_completions(boxlang_view):
    """Get type-aware completions for dot context."""
    if not boxlang_view.dot_context:
        return None

    resolver = TypeResolver(boxlang_view.view, boxlang_view.position)
    resolved_type = resolver.resolve_dot_chain_type(boxlang_view.dot_context)

    if resolved_type == "any":
        return None

    completions = _get_type_completions(resolved_type, boxlang_view)
    if completions:
        return boxlang_view.CompletionList(completions, 10, False)

    return None


def _get_type_completions(resolved_type, boxlang_view):
    """Get completions for a resolved type."""
    completions = []

    if resolved_type.startswith("component:"):
        component_path = resolved_type[len("component:"):]
        completions = _get_component_member_completions(component_path, boxlang_view)
    else:
        completions = _get_builtin_type_completions(resolved_type, boxlang_view)

    return completions


def _get_component_member_completions(component_path, boxlang_view):
    """Get member completions for a component."""
    completions = []

    metadata = component_index.get_indexed_metadata_by_dotpath(component_path)
    if not metadata:
        return completions

    functions = metadata.get("functions", {})
    completion_style = utils.get_setting("boxlang_cfc_completions") or "required"
    completion_names = utils.get_setting("boxlang_cfc_completion_names") or "basic"

    for func_name, func_meta in sorted(functions.items()):
        if func_meta.get("access") == "private":
            continue

        args = func_meta.get("args", [])
        return_type = func_meta.get("return_type", "")

        if completion_names == "full" and return_type:
            hint = f"(): {return_type}"
        else:
            hint = "method"

        if completion_style == "basic":
            content = f"{func_name}($0)"
        elif completion_style == "required":
            required_args = [a for a in args if a.get("required", False)]
            snippet_args = ", ".join([f"${{{i+1}:{a.get('name', '')}}}" for i, a in enumerate(required_args)])
            content = f"{func_name}({snippet_args}$0)"
        else:
            snippet_args = ", ".join([f"${{{i+1}:{a.get('name', '')}}}" for i, a in enumerate(args)])
            content = f"{func_name}({snippet_args}$0)"

        completions.append(
            sublime.CompletionItem(
                func_name if completion_names == "basic" else f"{func_name}():{return_type}" if return_type else func_name,
                hint,
                content,
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_FUNCTION, "m", component_path.split(".")[-1]),
                details=func_meta.get("description", "")
            )
        )

    properties = metadata.get("properties", {})
    for prop_name, prop_meta in sorted(properties.items()):
        prop_type = prop_meta.get("type", "")
        completions.append(
            sublime.CompletionItem(
                f"get{prop_name.capitalize()}",
                f"accessor: {prop_type}",
                f"get{prop_name.capitalize()}()",
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_FUNCTION, "g", "getter"),
            )
        )
        completions.append(
            sublime.CompletionItem(
                f"set{prop_name.capitalize()}",
                f"accessor: {prop_type}",
                f"set{prop_name.capitalize()}(${{1:{prop_name}}}$0)",
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_FUNCTION, "s", "setter"),
            )
        )

    if metadata.get("extends"):
        parent_completions = _get_component_member_completions(metadata["extends"], boxlang_view)
        completions.extend(parent_completions)

    return completions


def _get_builtin_type_completions(type_name, boxlang_view):
    """Get completions for a built-in type."""
    completions = []

    type_methods = {
        "string": [
            ("len\tnumeric", "len()"),
            ("length\tnumeric", "length()"),
            ("left\tstring", "left($1)$0"),
            ("right\tstring", "right($1)$0"),
            ("mid\tstring", "mid($1, $2)$0"),
            ("trim\tstring", "trim()"),
            ("lCase\tstring", "lCase()"),
            ("uCase\tstring", "uCase()"),
            ("replace\tstring", "replace($1, $2)$0"),
            ("find\tnumeric", "find($1)$0"),
            ("split\tarray", "split($1)$0"),
            ("substring\tstring", "substring($1, $2)$0"),
            ("toNumeric\tnumeric", "toNumeric()"),
            ("toBoolean\tboolean", "toBoolean()"),
            ("toString\tstring", "toString()"),
        ],
        "array": [
            ("len\tnumeric", "len()"),
            ("length\tnumeric", "length()"),
            ("append\tvoid", "append($1)$0"),
            ("prepend\tvoid", "prepend($1)$0"),
            ("delete\tvoid", "delete($1)$0"),
            ("sort\tarray", "sort()"),
            ("reverse\tarray", "reverse()"),
            ("slice\tarray", "slice($1, $2)$0"),
            ("find\tnumeric", "find($1)$0"),
            ("contains\tboolean", "contains($1)$0"),
            ("isEmpty\tboolean", "isEmpty()"),
        ],
        "struct": [
            ("len\tnumeric", "len()"),
            ("length\tnumeric", "length()"),
            ("keyArray\tarray", "keyArray()"),
            ("valueArray\tarray", "valueArray()"),
            ("delete\tvoid", "delete($1)$0"),
            ("clear\tvoid", "clear()"),
            ("isEmpty\tboolean", "isEmpty()"),
            ("keyExists\tboolean", "keyExists($1)$0"),
        ],
        "query": [
            ("len\tnumeric", "len()"),
            ("length\tnumeric", "length()"),
            ("columnArray\tarray", "columnArray()"),
            ("addColumn\tvoid", "addColumn($1, $2)$0"),
            ("deleteRow\tvoid", "deleteRow($1)$0"),
        ],
        "numeric": [
            ("abs\tnumeric", "abs()"),
            ("ceiling\tnumeric", "ceiling()"),
            ("floor\tnumeric", "floor()"),
            ("round\tnumeric", "round()"),
            ("toString\tstring", "toString()"),
        ],
    }

    methods = type_methods.get(type_name, [])
    for key, content in methods:
        parts = key.split("\t")
        name = parts[0]
        hint = parts[1] if len(parts) > 1 else ""

        completions.append(
            sublime.CompletionItem(
                name,
                hint,
                content,
                sublime.COMPLETION_FORMAT_SNIPPET,
                kind=(sublime.KIND_ID_FUNCTION, "f", type_name),
            )
        )

    return completions


def get_completions(boxlang_view):
    """Main entry point for type-aware completions."""
    if boxlang_view.type == "dot":
        return get_dot_completions(boxlang_view)
    return None
