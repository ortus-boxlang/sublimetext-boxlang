"""
Indexed component completions for BoxLang.
Provides completions for variables that match indexed components.
"""
import sublime
from ... import component_index
from ... import utils
SIDE_COLOR = 'color(#4C9BB0 blend(var(--background) 60%))'
variable_mappings = {}

def build_variable_mappings(project_name):
    """Build mappings from variable names to components."""
    global variable_mappings
    variable_mappings[project_name] = {}
    project_data = _get_project_data(project_name)
    if not project_data:
        return
    cfc_folders = project_data.get('boxlang_cfc_folders', [])
    if not cfc_folders:
        cfc_folders = utils.get_setting('boxlang_cfc_folders') or []
    for folder_config in cfc_folders:
        folder_path = utils.normalize_path(folder_config['path'], project_name)
        variable_templates = folder_config.get('variable_names', ['{cfc}'])
        accessors = folder_config.get('accessors', True)
        if not os.path.isdir(folder_path):
            continue
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if f.endswith('.bx'):
                    cfc_name = f[:-3]
                    folder_name = os.path.basename(root)
                    folder_singular = folder_name.rstrip('s')
                    for template in variable_templates:
                        var_name = template.replace('{cfc}', cfc_name)
                        var_name = var_name.replace('{cfc_folder}', folder_name)
                        var_name = var_name.replace('{cfc_folder_singularized}', folder_singular)
                        var_name = var_name.replace('{entityname}', cfc_name)
                        dot_path = _file_to_dot_path(os.path.join(root, f), project_name, project_data)
                        if dot_path:
                            metadata = component_index.get_indexed_metadata(project_name, dot_path)
                            if metadata:
                                variable_mappings[project_name][var_name.lower()] = {'dot_path': dot_path, 'metadata': metadata, 'accessors': accessors}

def get_script_completions(boxlang_view):
    """Get completions for indexed component variables in script."""
    if not boxlang_view.project_name or boxlang_view.project_name not in variable_mappings:
        return None
    if boxlang_view.view.match_selector(boxlang_view.position - 1, 'variable.other.readwrite.boxlang'):
        word_region = boxlang_view.view.word(boxlang_view.position - 1)
        word_text = boxlang_view.view.substr(word_region).lower()
        if word_text in variable_mappings[boxlang_view.project_name]:
            mapping = variable_mappings[boxlang_view.project_name][word_text]
            completions = _get_component_completions(boxlang_view.project_name, mapping['dot_path'], mapping['metadata'], mapping['accessors'])
            if completions:
                return boxlang_view.CompletionList(completions, 0, False)
    return None

def get_dot_completions(boxlang_view):
    """Get completions when typing . after a variable."""
    if not boxlang_view.project_name or boxlang_view.project_name not in variable_mappings:
        return None
    if len(boxlang_view.dot_context) == 0:
        return None
    var_name = boxlang_view.dot_context[0].name.lower()
    if var_name in variable_mappings[boxlang_view.project_name]:
        mapping = variable_mappings[boxlang_view.project_name][var_name]
        completions = _get_component_completions(boxlang_view.project_name, mapping['dot_path'], mapping['metadata'], mapping['accessors'])
        if completions:
            return boxlang_view.CompletionList(completions, 0, False)
    return None

def get_inline_documentation(boxlang_view, doc_type):
    """Get inline documentation for indexed component variables."""
    if not boxlang_view.project_name or boxlang_view.project_name not in variable_mappings:
        return None
    word_region = boxlang_view.view.word(boxlang_view.position)
    word_text = boxlang_view.view.substr(word_region).lower()
    if word_text in variable_mappings[boxlang_view.project_name]:
        mapping = variable_mappings[boxlang_view.project_name][word_text]
        return _build_documentation(boxlang_view, word_text, mapping, word_region)
    return None

def get_goto_boxlang_file(boxlang_view):
    """Get file navigation for indexed component variables."""
    if not boxlang_view.project_name or boxlang_view.project_name not in variable_mappings:
        return None
    word_region = boxlang_view.view.word(boxlang_view.position)
    word_text = boxlang_view.view.substr(word_region).lower()
    if word_text in variable_mappings[boxlang_view.project_name]:
        mapping = variable_mappings[boxlang_view.project_name][word_text]
        file_path = component_index.resolve_path(boxlang_view.project_name, boxlang_view.file_path, mapping['dot_path'])
        if file_path:
            return boxlang_view.GotoBoxlangFile(file_path, None)
    return None

def _get_component_completions(project_name, dot_path, metadata, include_accessors):
    """Get completions for a component's methods."""
    completions = []
    functions = metadata.get('functions', {})
    completion_style = utils.get_setting('boxlang_cfc_completions') or 'required'
    completion_names = utils.get_setting('boxlang_cfc_completion_names') or 'basic'
    for func_name, func_meta in functions.items():
        if func_meta.get('access') == 'private':
            continue
        args = func_meta.get('args', [])
        return_type = func_meta.get('return_type', '')
        if completion_names == 'full' and return_type:
            hint = '(): {}'.format(return_type)
        else:
            hint = 'method'
        if completion_style == 'basic':
            content = '{}($0)'.format(func_name)
        elif completion_style == 'required':
            required_args = [a for a in args if a.get('required', False)]
            snippet_args = ', '.join(['${{{}:{}}}'.format(i + 1, a.get('name', '')) for i, a in enumerate(required_args)])
            content = '{}({}$0)'.format(func_name, snippet_args)
        else:
            snippet_args = ', '.join(['${{{}:{}}}'.format(i + 1, a.get('name', '')) for i, a in enumerate(args)])
            content = '{}({}$0)'.format(func_name, snippet_args)
        completions.append(sublime.CompletionItem(func_name if completion_names == 'basic' else '{}():{}'.format(func_name, return_type) if return_type else func_name, hint, content, sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'm', dot_path.split('.')[-1]), details=func_meta.get('description', '')))
    if include_accessors:
        properties = metadata.get('properties', {})
        for prop_name, prop_meta in properties.items():
            prop_type = prop_meta.get('type', '')
            completions.append(sublime.CompletionItem('get{}'.format(prop_name.capitalize()), 'accessor: {}'.format(prop_type), 'get{}()'.format(prop_name.capitalize()), sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'g', 'getter')))
            completions.append(sublime.CompletionItem('set{}'.format(prop_name.capitalize()), 'accessor: {}'.format(prop_type), 'set{}(${{1:{}}}$0)'.format(prop_name.capitalize(), prop_name), sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 's', 'setter')))
    return completions

def _build_documentation(boxlang_view, var_name, mapping, region):
    """Build documentation popup for a component variable."""
    metadata = mapping['metadata']
    dot_path = mapping['dot_path']
    doc = {'side_color': SIDE_COLOR, 'html': {'header': 'Component: <span class="entity_name_class">{}</span>'.format(dot_path.split('.')[-1]), 'body': '<p>Dot path: <code>{}</code></p>'.format(dot_path), 'links': []}}
    if metadata.get('extends'):
        doc['html']['body'] += '<p>Extends: <code>{}</code></p>'.format(metadata['extends'])
    functions = metadata.get('functions', {})
    if functions:
        doc['html']['body'] += '<h2>Methods</h2>'
        for func_name, func_meta in sorted(functions.items()):
            if func_meta.get('access') == 'private':
                continue
            args = func_meta.get('args', [])
            return_type = func_meta.get('return_type', '')
            arg_str = ', '.join(['{}'.format(a.get('name', '')) + (': {}'.format(a.get('type', '')) if a.get('type') else '') for a in args])
            sig = '{}({})'.format(func_name, arg_str)
            if return_type:
                sig += ': {}'.format(return_type)
            doc['html']['body'] += '<p><code>{}</code></p>'.format(sig)
    doc['html']['links'] = [{'href': 'https://boxlang.ortusbooks.com/boxlang-language/reference/components/{}'.format(dot_path.split('.')[-1]), 'text': 'Open in Docs'}]
    return boxlang_view.Documentation([region], doc, None, 1)

def _file_to_dot_path(file_path, project_name, project_data):
    """Convert file path to dot path."""
    mappings = project_data.get('mappings', [])
    for mapping in mappings:
        mapping_path = utils.normalize_mapping(mapping, project_name)['path']
        mapping_prefix = mapping['mapping']
        if file_path.startswith(mapping_path):
            rel_path = file_path[len(mapping_path):].lstrip('/')
            dot_path = mapping_prefix.rstrip('/') + '/' + rel_path.replace('/', '.')
            if dot_path.endswith('.bx'):
                dot_path = dot_path[:-3]
            return dot_path
    return None

def _get_project_data(project_name):
    """Get project data."""
    for window in sublime.windows():
        if window.project_file_name():
            if utils.normalize_path(window.project_file_name()) == project_name:
                return window.project_data()
    return None

def get_completions(boxlang_view):
    """Main entry point."""
    if boxlang_view.type == 'dot':
        return get_dot_completions(boxlang_view)
    elif boxlang_view.type == 'script':
        return get_script_completions(boxlang_view)
    return None

def get_inline_documentation(boxlang_view, doc_type):
    """Get inline documentation."""
    return get_inline_documentation(boxlang_view, doc_type)

def get_goto_boxlang_file(boxlang_view):
    """Get file navigation."""
    return get_goto_boxlang_file(boxlang_view)

def _plugin_loaded():
    """Build variable mappings when plugin loads."""
    for project_name, _ in utils.get_project_list():
        build_variable_mappings(project_name)
import os