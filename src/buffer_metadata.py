"""
Buffer metadata caching for BoxLang files.
"""

import timeit
from . import utils
from . import events
from .component_parser import parse_file

buffer_metadata_cache = {}


def get_minimal_file_string(view):
    """Get a minimal representation of the file for parsing."""
    min_string = ""

    tag_component_regions = view.find_by_selector("meta.class.boxlang")

    if len(tag_component_regions) > 0:
        min_string += view.substr(tag_component_regions[0]) + "\n"
        current_funct = ""
        for r in view.find_by_selector(
            "meta.function.boxlang, meta.function.body.tag.boxlang meta.tag.argument.boxlang"
        ):
            text = view.substr(r)
            if text.lower().startswith("<bx:funct") and len(current_funct) > 0:
                min_string += current_funct + "</bx:function>\n"
                current_funct = ""
            current_funct += text + "\n"
        min_string += current_funct + "</bx:function>\n"
    else:
        script_selectors = [
            ("comment.block.documentation.boxlang -meta.class", "\n"),
            ("meta.class.declaration.boxlang", " {\n"),
            ("meta.tag.property.boxlang", ";\n"),
        ]

        for selector, separator in script_selectors:
            for r in view.find_by_selector(selector):
                min_string += view.substr(r) + separator

        funct_regions = "meta.class.body.boxlang comment.block.documentation.boxlang, meta.function.declaration.boxlang -meta.function.body.boxlang"
        for r in view.find_by_selector(funct_regions):
            string = view.substr(r)
            min_string += string + ("\n" if string.endswith("*/") else "{ }\n")

        min_string += "}"

    return min_string


def get_cached_view_metadata(view):
    """Get cached metadata for a view, or parse if not cached."""
    if view.buffer_id() in buffer_metadata_cache:
        return buffer_metadata_cache[view.buffer_id()][1]
    return get_view_metadata(view)


def get_view_metadata(view):
    """Parse and cache metadata for a view."""
    start_time = timeit.default_timer()

    file_path = utils.normalize_path(view.file_name()) if view.file_name() else ""

    if file_path:
        # Use the AST/tag parser for file-based parsing
        base_meta = parse_file(file_path)
    else:
        # Fall back to minimal string parsing for unsaved buffers
        file_string = get_minimal_file_string(view)
        base_meta = {"parse_errors": ["Unsaved buffer - parsing not available"]}

    if utils.get_setting("boxlang_log_in_file_parse_time"):
        parse_time = timeit.default_timer() - start_time
        message = "BoxLang: parsed {} in {}ms"
        print(message.format(view.file_name() or "file", round(parse_time * 1000)))

    # Extend with empty collections for compatibility
    extended_meta = dict(base_meta)
    extended_meta.update(
        {
            "functions": extended_meta.get("functions", {}),
            "function_file_map": {},
            "properties": extended_meta.get("properties", {}),
            "property_file_map": {},
        }
    )

    project_name = utils.get_project_name(view)
    if project_name and extended_meta.get("extends"):
        from .component_index import resolve_path, get_extended_metadata_by_file_path
        extends_file_path = resolve_path(
            project_name, file_path, extended_meta["extends"]
        )
        root_meta = get_extended_metadata_by_file_path(
            project_name, extends_file_path
        )
        if root_meta:
            for key in [
                "functions",
                "function_file_map",
                "properties",
                "property_file_map",
            ]:
                extended_meta[key].update(root_meta.get(key, {}))

    extended_meta["function_file_map"].update(
        {funct_key: file_path for funct_key in extended_meta.get("functions", {})}
    )
    extended_meta["property_file_map"].update(
        {prop_key: file_path for prop_key in extended_meta.get("properties", {})}
    )

    buffer_metadata_cache[view.buffer_id()] = timeit.default_timer(), extended_meta

    return extended_meta


def on_view_loaded(view):
    """Handle view loaded event."""
    if not view.match_selector(0, "embedding.boxlang"):
        return
    get_view_metadata(view)


def on_view_modified(view):
    """Handle view modified event."""
    if not view.match_selector(0, "embedding.boxlang"):
        return

    if view.buffer_id() in buffer_metadata_cache:
        last_updated, meta = buffer_metadata_cache[view.buffer_id()]
        if timeit.default_timer() - last_updated < 0.5:
            return
    get_view_metadata(view)


def on_view_closed(view):
    """Handle view closed event."""
    if view.buffer_id() in buffer_metadata_cache:
        del buffer_metadata_cache[view.buffer_id()]


events.subscribe("on_load_async", on_view_loaded)
events.subscribe("on_modified_async", on_view_modified)
events.subscribe("on_close", on_view_closed)
