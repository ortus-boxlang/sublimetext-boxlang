"""
Utility functions for the BoxLang package.
"""
import os
import sublime
from collections import namedtuple
Symbol = namedtuple('Symbol', 'name is_function function_region args_region name_region')

def get_plugin_name():
    """Return the package name."""
    return __package__.split('.')[0]

def get_project_list():
    """Return a list of (project_name, project_data) tuples for all open windows."""
    project_list = []
    seen = set()
    for window in sublime.windows():
        if window.project_file_name():
            name = normalize_path(window.project_file_name())
            if name not in seen:
                seen.add(name)
                project_list.append((name, window.project_data()))
        elif window.folders():
            name = normalize_path(window.folders()[0])
            if name not in seen:
                seen.add(name)
                project_list.append((name, None))
    return project_list

def get_project_name(view):
    """Return the project file path for the given view, falling back to the first open folder."""
    if view.window():
        project_file_name = view.window().project_file_name()
        if project_file_name:
            return normalize_path(project_file_name)
        folders = view.window().folders()
        if folders:
            return normalize_path(folders[0])
    return None

def get_project_name_from_window(window):
    """Return the project file path, falling back to the first open folder."""
    project_file_name = window.project_file_name()
    if project_file_name:
        return normalize_path(project_file_name)
    folders = window.folders()
    if folders:
        return normalize_path(folders[0])
    return None

def has_project_file(window):
    """Return True if the window has an actual .sublime-project file."""
    return bool(window.project_file_name())

def normalize_path(path, root_path=None):
    """Normalize a file path to use forward slashes."""
    if path is None:
        return None
    if not os.path.isabs(path) and root_path is not None:
        path = os.path.normpath(os.path.join(root_path, path))
    normalized_path = path.replace('\\', '/')
    if len(normalized_path) > 0 and normalized_path[-1] == '/':
        normalized_path = normalized_path[:-1]
    return normalized_path

def normalize_mapping(mapping, root_path=None):
    """Normalize a mapping dictionary."""
    normalized_mapping = {}
    if root_path.endswith('sublime-project'):
        root_path = os.path.dirname(root_path)
    normalized_mapping['path'] = normalize_path(mapping['path'], root_path)
    normalized_mapping_path = mapping['mapping'].replace('\\', '/')
    if normalized_mapping_path[0] != '/':
        normalized_mapping_path = '/' + normalized_mapping_path
    if normalized_mapping_path[-1] == '/':
        normalized_mapping_path = normalized_mapping_path[:-1]
    normalized_mapping['mapping'] = normalized_mapping_path
    return normalized_mapping

def format_lookup_file_path(file_path):
    """Format a file path for display in lookup results."""
    file_path = normalize_path(file_path)
    if len(file_path) > 1 and file_path[1] == ':':
        file_path = '/' + file_path[0] + file_path[2:]
    return file_path

def get_previous_character(view, position):
    """Get the position of the previous non-whitespace character."""
    if view.substr(position - 1) in [' ', '\t', '\n']:
        position = view.find_by_class(position, False, sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END)
    return position - 1

def get_next_character(view, position):
    """Get the position of the next non-whitespace character."""
    if view.substr(position) in [' ', '\t', '\n']:
        position = view.find_by_class(position, True, sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START)
    return position

def get_previous_word(view, position):
    """Get the word before the given position."""
    previous_character = get_previous_character(view, position)
    return view.substr(view.word(previous_character)).lower()

def get_scope_region_containing_point(view, pt, scope):
    """Find the region containing the given point with the specified scope."""
    scope_count = view.scope_name(pt).count(scope) - view.scope_name(pt).count('.' + scope)
    if scope_count == 0:
        return None
    scope_to_find = ' '.join([scope] * scope_count)
    for r in view.find_by_selector(scope_to_find):
        if r.contains(pt):
            return r
    return None

def get_char_point_before_scope(view, pt, scope):
    """Get the character point before a scope."""
    scope_region = get_scope_region_containing_point(view, pt, scope)
    if scope_region:
        scope_start = scope_region.begin()
        return get_previous_character(view, scope_start)
    return None

def get_dot_context(view, dot_position):
    """Get the dot context (chain of identifiers) at the given position."""
    context = []
    if view.substr(dot_position) != '.':
        return context
    if view.substr(dot_position - 1) in [' ', '\t', '\n']:
        dot_position = view.find_by_class(dot_position, False, sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END)
    base_scope_count = view.scope_name(dot_position).count('meta.function-call')
    scope_to_find = ' '.join(['meta.function-call'] * (base_scope_count + 1))
    if view.match_selector(dot_position - 1, scope_to_find):
        function_name, name_region, function_args_region = get_function_call(view, dot_position - 1)
        context.append(Symbol(function_name, True, name_region, function_args_region, name_region))
    elif view.match_selector(dot_position - 1, 'variable, meta.property, meta.instance.constructor'):
        name_region = view.word(dot_position)
        context.append(Symbol(view.substr(name_region).lower(), False, None, None, name_region))
    if len(context) > 0:
        context.extend(get_dot_context(view, name_region.begin() - 1))
    return context

def get_struct_context(view, position):
    """Get the struct context at the given position."""
    context = []
    if not view.match_selector(position, 'meta.struct-literal.boxlang'):
        return context
    previous_char_point = get_char_point_before_scope(view, position, 'meta.struct-literal.boxlang')
    if not view.match_selector(previous_char_point, 'keyword.operator.assignment.binary.boxlang,punctuation.separator.key-value.boxlang'):
        return context
    previous_char_point = get_previous_character(view, previous_char_point)
    if not view.match_selector(previous_char_point, 'meta.property,variable,meta.struct-literal.key.boxlang'):
        return context
    name_region = view.word(previous_char_point)
    context.append(Symbol(view.substr(name_region).lower(), False, None, None, name_region))
    if view.match_selector(previous_char_point, 'meta.property'):
        context.extend(get_dot_context(view, name_region.begin() - 1))
    else:
        context.extend(get_struct_context(view, name_region.begin()))
    return context

def get_setting(setting_key):
    """Get a setting from the BoxLang package settings."""
    boxlang_settings = sublime.load_settings('boxlang.sublime-settings')
    return boxlang_settings.get(setting_key)

def get_project_setting(view, setting_key, default=None):
    """Get a project-specific setting."""
    project_data = view.window().project_data() if view.window() else None
    if project_data and setting_key in project_data:
        return project_data[setting_key]
    return get_setting(setting_key) or default

def get_tag_name(view, pos):
    """Get the tag name at the given position."""
    tag_scope = 'meta.tag.boxlang - punctuation.definition.tag.begin, meta.tag.custom.boxlang - punctuation.definition.tag.begin, meta.tag.script.boxlang, meta.tag.script.bx.boxlang'
    tag_name_scope = 'entity.name.tag.boxlang, entity.name.tag.custom.boxlang, entity.name.tag.script.boxlang'
    tag_name_regions = view.find_by_selector(tag_name_scope)
    for tag_region in view.find_by_selector(tag_scope):
        if tag_region.contains(pos):
            for tag_name_region in tag_name_regions:
                if tag_region.contains(tag_name_region):
                    return view.substr(tag_name_region).lower()
    return None

def get_tag_attribute_name(view, pos):
    """Get the tag attribute name at the given position."""
    if view.match_selector(pos, 'meta.tag entity.other.attribute-name.boxlang, meta.class.declaration.boxlang entity.other.attribute-name.boxlang'):
        return view.substr(view.word(pos)).lower()
    for scope in ['string.quoted', 'string.unquoted']:
        full_scope = 'meta.tag.boxlang ' + scope + ', meta.tag.custom.boxlang ' + scope + ', meta.tag.script.boxlang ' + scope + ', meta.tag.script.bx.boxlang ' + scope + ', meta.class.declaration.boxlang ' + scope
        if view.match_selector(pos, full_scope):
            pos = get_char_point_before_scope(view, pos, scope)
            break
    full_scope = ['meta.tag.boxlang punctuation.separator.key-value', 'meta.tag.custom.boxlang punctuation.separator.key-value', 'meta.tag.script.boxlang punctuation.separator.key-value', 'meta.tag.script.bx.boxlang punctuation.separator.key-value', 'meta.class.declaration.boxlang punctuation.separator.key-value']
    if view.match_selector(pos, ','.join(full_scope)):
        return get_previous_word(view, pos)
    return None

def get_function(view, pt):
    """Get function info at the given position."""
    if view.match_selector(pt, 'meta.function.boxlang'):
        function_scope = 'meta.function.boxlang'
    else:
        function_scope = 'meta.function.declaration.boxlang'
    function_name_scope = 'entity.name.function.boxlang,entity.name.function.constructor.boxlang'
    function_region = get_scope_region_containing_point(view, pt, function_scope)
    if function_region:
        function_name_regions = view.find_by_selector(function_name_scope)
        for function_name_region in function_name_regions:
            if function_region.contains(function_name_region):
                return (view.substr(function_name_region).lower(), function_name_region, function_region)
    return None

def get_function_call(view, pt, support=False):
    """Get function call info at the given position."""
    function_call_scope = 'meta.function-call'
    if support:
        function_call_scope += '.support'
    function_region = get_scope_region_containing_point(view, pt, function_call_scope)
    if function_region:
        function_name_region = view.word(function_region.begin())
        function_args_region = sublime.Region(function_name_region.end(), function_region.end())
        return (view.substr(function_name_region).lower(), function_name_region, function_args_region)
    return None

def get_current_function_body(view, pt, component_method=True):
    """Get the current function body region."""
    selector = 'meta.function.body'
    if component_method:
        selector = 'meta.class.body ' + selector
    return get_scope_region_containing_point(view, pt, selector)

def find_variable_assignment(view, position, variable_name):
    """Find a variable assignment before the given position."""
    regex_prefix = '(\\bvariables\\.|\\s|\\bvar\\s+)'
    regex = regex_prefix + variable_name + '\\b\\s*=\\s*'
    assignments = view.find_all(regex, sublime.IGNORECASE)
    for r in reversed(assignments):
        if r.begin() < position:
            if view.substr(r).lower().startswith('var '):
                function_region = get_current_function_body(view, r.end(), False)
                if not function_region or not function_region.contains(position):
                    continue
            return r
    return None

def get_verified_path(root_path, rel_path):
    """
    Given a valid root path and an unverified relative path,
    searches to see if the full path exists (case-insensitive).
    Returns a tuple of (rel_path, exists).
    """
    normalized_root_path = normalize_path(root_path)
    rel_path_elements = normalize_path(rel_path).split('/')
    verified_path_elements = []
    for elem in rel_path_elements:
        try:
            dir_map = {f.lower(): f for f in os.listdir(normalized_root_path + '/' + '/'.join(verified_path_elements))}
        except OSError:
            return (rel_path, False)
        if elem.lower() not in dir_map:
            return (rel_path, False)
        verified_path_elements.append(dir_map[elem.lower()])
    return ('/'.join(verified_path_elements), True)