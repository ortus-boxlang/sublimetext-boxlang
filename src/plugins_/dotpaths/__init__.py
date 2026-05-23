"""
Dot path completions for BoxLang.
Provides completions for import statements, new operator, createObject, and extends.
"""

import sublime
from ...component_index import component_index
from ... import utils

projects = {}


def build_project_map(project_name):
    """Build completion map for a project."""
    global projects
    data = {}
    path_completions, constructor_completions = make_completions(project_name)
    data["path_completions"] = path_completions
    data["constructor_completions"] = constructor_completions
    projects[project_name] = data


def make_completions(project_name):
    """Create path and constructor completions from indexed components."""
    dot_paths = component_index.get_dot_paths(project_name)
    path_map = map_paths(dot_paths)
    path_completions = {}
    constructor_completions = {}

    for k in path_map:
        path_completions[k] = []
        constructor_completions[k] = []
        for c in sorted(path_map[k], key=lambda i: i["path_part"]):
            path_completions[k].append(
                make_completion(c, k, dot_paths, project_name, False)
            )
            constructor_completions[k].append(
                make_completion(c, k, dot_paths, project_name, True)
            )

    return path_completions, constructor_completions


def make_completion(path_part_dict, key, dot_paths, project_name, constructor):
    """Create a single completion item."""
    completion = path_part_dict["path_part"]
    if path_part_dict["is_component"] and constructor:
        full_key = key + ("." if len(key) > 0 else "") + completion
        component_completion = component_index.get_completions_by_file_path(
            project_name, dot_paths[full_key.lower()]["file_path"]
        ).get("constructor")
        if component_completion:
            completion = completion + component_completion.content[4:]
        else:
            completion = completion + "()"
    if not path_part_dict["is_component"]:
        completion += "."
    return (
        path_part_dict["path_part"]
        + "\t"
        + ("component" if path_part_dict["is_component"] else "path"),
        completion,
    )


def map_paths(dot_paths):
    """Map dot paths to their component parts for completion lookup."""
    path_map = {}
    for path_key in dot_paths:
        path_parts = dot_paths[path_key]["dot_path"].split(".")
        for i in range(len(path_parts)):
            key = ".".join(path_parts[:i]).lower()
            if key not in path_map:
                path_map[key] = []
            is_component = i == len(path_parts) - 1
            path_part_dict = {"path_part": path_parts[i], "is_component": is_component}
            if path_part_dict not in path_map[key]:
                path_map[key].append(path_part_dict)
    return path_map


def get_completions(project_name, dot_path, completion_type):
    """Get completions for a given dot path."""
    if (
        dot_path is not None
        and dot_path.lower() in projects[project_name][completion_type]
    ):
        return projects[project_name][completion_type][dot_path.lower()]
    return []


def get_completions_by_component_name(boxlang_view, component_name):
    """Get method completions for a component by name."""
    comp = component_index.get_completions_by_dot_path(
        boxlang_view.project_name, component_name.lower()
    )

    if not comp:
        folder_path = get_folder_path(boxlang_view, component_name)
        if folder_path:
            comp = component_index.get_completions_by_dot_path(
                boxlang_view.project_name, folder_path
            )

    if comp:
        filtered_completions = []
        for completion in comp.get("functions", []):
            if not completion.get("private", False):
                filtered_completions.append(
                    (completion.get("key", "") + "\t" + completion.get("hint", ""), completion.get("content", ""))
                )
        return filtered_completions

    return None


def get_folder_path(boxlang_view, dot_path):
    """Get folder-based path for a component."""
    if not boxlang_view.project_name:
        return None
    # Simplified - would need project settings for folder mappings
    return None


def get_script_completions(boxlang_view):
    """Get dot path completions in script context."""
    if not boxlang_view.project_name or boxlang_view.project_name not in projects:
        return None

    # Import statement completions: import path.to.
    if boxlang_view.view.match_selector(
        boxlang_view.position - 1, "meta.import.boxlang variable.other.import.boxlang"
    ):
        r = utils.get_scope_region_containing_point(
            boxlang_view.view, boxlang_view.position - 1, "meta.import.boxlang"
        )
        if r:
            import_text = boxlang_view.view.substr(r)
            # Get the part before the current segment
            parts = import_text.replace("import ", "").split(".")
            if len(parts) > 1:
                dot_path = ".".join(parts[:-1])
            else:
                dot_path = ""

            completions = get_completions(boxlang_view.project_name, dot_path, "path_completions")
            if completions:
                return boxlang_view.CompletionList(completions, 0, False)

    # New operator completions: new path.to.
    if boxlang_view.view.match_selector(
        boxlang_view.position - 1, "meta.instance.constructor.boxlang"
    ):
        r = utils.get_scope_region_containing_point(
            boxlang_view.view, boxlang_view.position - 1, "meta.instance.constructor.boxlang"
        )
        if r:
            constructor_text = boxlang_view.view.substr(r)
            # Remove "new " prefix and get path
            path_text = constructor_text[4:]
            parts = path_text.split(".")
            if len(parts) > 1:
                dot_path = ".".join(parts[:-1])
            else:
                dot_path = ""

            completions = get_completions(boxlang_view.project_name, dot_path, "constructor_completions")
            if completions:
                return boxlang_view.CompletionList(completions, 0, False)

    # createObject completions: createObject("component", "path.to.")
    if boxlang_view.view.match_selector(
        boxlang_view.position,
        "meta.function-call.support.createcomponent.boxlang string.quoted"
    ):
        r = utils.get_scope_region_containing_point(
            boxlang_view.view, boxlang_view.position, "string.quoted"
        )
        if r:
            string_text = boxlang_view.view.substr(r)
            if string_text[0] not in ['"', "'"] or string_text[-1] not in ['"', "'"]:
                return None
            path_text = string_text[1:-1]
            parts = path_text.split(".")
            if len(parts) > 1:
                dot_path = ".".join(parts[:-1])
            else:
                dot_path = ""

            completions = get_completions(boxlang_view.project_name, dot_path, "path_completions")
            if completions:
                return boxlang_view.CompletionList(completions, 0, False)

    return None


def get_dot_completions(boxlang_view):
    """Get dot completions for instantiated components."""
    if not boxlang_view.project_name or len(boxlang_view.dot_context) == 0:
        return None

    component_selector = "meta.function-call.support.createcomponent.boxlang"
    constructor_selector = "meta.instance.constructor.boxlang"
    component_name = None

    if boxlang_view.dot_context[0].name == "createobject" and boxlang_view.view.match_selector(
        boxlang_view.prefix_start - 2, component_selector
    ):
        # Extract component name from createObject args
        component_name = get_component_name_from_args(
            boxlang_view.view.substr(boxlang_view.dot_context[0].args_region)
        )
    elif boxlang_view.view.match_selector(
        boxlang_view.prefix_start - 2, constructor_selector
    ):
        component_name = ".".join([s.name for s in reversed(boxlang_view.dot_context)])
    elif is_possible_component_instance(boxlang_view.dot_context):
        # Look for variable assignment
        component_tuple = find_component_by_var_assignment(
            boxlang_view, boxlang_view.prefix_start, boxlang_view.dot_context[0].name
        )
        if component_tuple[0] is not None:
            component_name = component_tuple[0]

    if component_name:
        completions = get_completions_by_component_name(boxlang_view, component_name)
        if completions:
            return boxlang_view.CompletionList(completions, 0, False)

    return None


def get_component_name_from_args(args_text):
    """Extract component name from createObject arguments."""
    # Simple extraction - looks for "component", "path.to.Component"
    import re
    match = re.search(r'["\']component["\']\s*,\s*["\']([^"\']+)["\']', args_text)
    if match:
        return match.group(1)
    return None


def is_possible_component_instance(dot_context):
    """Check if a dot context could be a component instance."""
    if len(dot_context) == 0:
        return False
    # Check if first element looks like a variable name (not a keyword)
    first_name = dot_context[0].name.lower()
    keywords = {"var", "function", "if", "else", "for", "while", "return", "new", "import"}
    return first_name not in keywords and not first_name[0].isupper()


def find_component_by_var_assignment(boxlang_view, position, variable_name):
    """Find a variable assignment that might be an instantiated component."""
    var_assignment = utils.find_variable_assignment(
        boxlang_view.view, position, variable_name
    )
    if var_assignment:
        # Check if the assignment is a new expression
        assign_text = boxlang_view.view.substr(
            sublime.Region(var_assignment.begin(), var_assignment.end() + 50)
        )
        import re
        match = re.search(r'=\s*new\s+([\w.]+)', assign_text)
        if match:
            return (match.group(1), var_assignment)
    return (None, None)


def get_completions(boxlang_view):
    """Main entry point for dot path completions."""
    if boxlang_view.type == "dot":
        return get_dot_completions(boxlang_view)
    elif boxlang_view.type == "script":
        return get_script_completions(boxlang_view)
    return None


def _plugin_loaded():
    """Build project maps when plugin loads."""
    from ... import utils
    for project_name, _ in utils.get_project_list():
        build_project_map(project_name)
