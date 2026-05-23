"""
Base completions for BoxLang built-in functions and tags.
"""
import sublime
import json
from ... import utils
COMPLETION_FILES = ['boxlang_tags', 'boxlang_functions', 'boxlang_member_functions', 'boxlang_function_params']
SIDE_COLOR = 'color(#4C9BB0 blend(var(--background) 60%))'
completions = {}
function_names = []

def get_tags(boxlang_view):
    """Get tag completions."""
    return boxlang_view.CompletionList(completions.get('boxlang_tags', []), 0, False)

def get_tag_attributes(boxlang_view):
    """Get tag attribute completions."""
    if not boxlang_view.tag_name:
        return None
    tag_name = boxlang_view.tag_name
    if tag_name.startswith('bx:'):
        tag_name = tag_name[3:]
    if boxlang_view.tag_attribute_name is None or boxlang_view.tag_location == 'tag_attribute_name':
        completion_list = completions.get('boxlang_tag_attributes', {}).get(tag_name, None)
        if completion_list:
            return boxlang_view.CompletionList(completion_list, 0, False)
    elif tag_name in completions.get('boxlang_tag_attribute_values', {}) and boxlang_view.tag_attribute_name in completions['boxlang_tag_attribute_values'].get(tag_name, {}):
        completion_list = completions['boxlang_tag_attribute_values'][tag_name][boxlang_view.tag_attribute_name]
        return boxlang_view.CompletionList(completion_list, 0, False)
    return None

def get_script_completions(boxlang_view):
    """Get script completions."""
    completion_list = []
    if boxlang_view.view.match_selector(boxlang_view.position, 'meta.function-call.arguments.boxlang,meta.function-call.arguments.method.boxlang'):
        completion_list.append(sublime.CompletionItem('argumentCollection', 'parameter struct', 'argumentCollection = ${1:parameters}', sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_VARIABLE, 'v', 'BoxLang')))
    completion_list.extend(completions.get('boxlang_functions', {}).get(utils.get_setting('boxlang_bif_completions'), []))
    completion_list.extend(completions.get('boxlang_tags_in_script', []))
    return boxlang_view.CompletionList(completion_list, 0, False)

def get_dot_completions(boxlang_view):
    """Get dot (member function) completions."""
    completion_list = completions.get('boxlang_member_functions', {}).get(utils.get_setting('boxlang_bif_completions'), [])
    return boxlang_view.CompletionList(completion_list, 0, False)

def get_inline_documentation(boxlang_view, doc_type):
    """Get inline documentation for BIFs."""
    return None

def get_completions(boxlang_view):
    """Main completions entry point."""
    if boxlang_view.type == 'tag':
        if boxlang_view.tag_location == 'tag_name':
            return get_tags(boxlang_view)
        else:
            return get_tag_attributes(boxlang_view)
    elif boxlang_view.type == 'dot':
        return get_dot_completions(boxlang_view)
    elif boxlang_view.type == 'script':
        return get_script_completions(boxlang_view)
    elif boxlang_view.type == 'tag_attributes':
        return get_tag_attributes(boxlang_view)
    return None

def load_completions():
    """Load completion data from JSON files."""
    global completions, function_names
    completions_data = {}
    for filename in COMPLETION_FILES:
        try:
            completions_data[filename] = load_json_data(filename)
        except Exception:
            completions_data[filename] = {}
    completions['boxlang_tags'] = []
    completions['boxlang_tags_in_script'] = []
    completions['boxlang_tag_attributes'] = {}
    completions['boxlang_tag_attribute_values'] = {}
    tags_data = completions_data.get('boxlang_tags', {})
    for tag_name in sorted(tags_data.keys()):
        tag_info = tags_data[tag_name]
        if isinstance(tag_info, list):
            tag_info = {'attributes': [tag_info, []], 'attribute_values': {}}
        tag_attributes = tag_info.get('attributes', [[], []])
        required_attrs = tag_attributes[0] if len(tag_attributes) > 0 else []
        optional_attrs = tag_attributes[1] if len(tag_attributes) > 1 else []
        completions['boxlang_tags'].append(make_tag_completion(tag_name, required_attrs))
        completions['boxlang_tags_in_script'].append(make_tag_completion(tag_name, required_attrs))
        completions['boxlang_tag_attributes'][tag_name] = [sublime.CompletionItem(a, 'required', a + '="$1"', sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_MARKUP, 'a', tag_name)) for a in required_attrs]
        completions['boxlang_tag_attributes'][tag_name].extend([sublime.CompletionItem(a, 'optional', a + '="$1"', sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_MARKUP, 'a', tag_name)) for a in optional_attrs])
        tag_attribute_values = tag_info.get('attribute_values', {})
        completions['boxlang_tag_attribute_values'][tag_name] = {}
        for attribute_name in sorted(tag_attribute_values.keys()):
            completions['boxlang_tag_attribute_values'][tag_name][attribute_name] = [sublime.CompletionItem(v, attribute_name, v, sublime.COMPLETION_FORMAT_TEXT, kind=(sublime.KIND_ID_AMBIGUOUS, 'v', tag_name)) for v in tag_attribute_values[attribute_name]]
    completions['boxlang_functions'] = {'basic': [], 'required': [], 'full': []}
    function_names = []
    functions_data = completions_data.get('boxlang_functions', {})
    for funct in sorted(functions_data.keys()):
        func_info = functions_data[funct]
        description = func_info[0] if len(func_info) > 0 else ''
        required_snippet = func_info[1][0] if len(func_info) > 1 and len(func_info[1]) > 0 else '($0)'
        full_snippet = func_info[1][1] if len(func_info) > 1 and len(func_info[1]) > 1 else '($0)'
        completions['boxlang_functions']['basic'].append(sublime.CompletionItem(funct, 'boxlang.fn', funct + '($0)', sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'f', 'function'), details=description))
        completions['boxlang_functions']['required'].append(sublime.CompletionItem(funct, 'boxlang.fn', funct + required_snippet, sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'f', 'function'), details=description))
        completions['boxlang_functions']['full'].append(sublime.CompletionItem(funct, 'boxlang.fn', funct + full_snippet, sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'f', 'function'), details=description))
        function_names.append(funct)
    completions['boxlang_member_functions'] = {'basic': [], 'required': [], 'full': []}
    member_data = completions_data.get('boxlang_member_functions', {})
    for member_type in sorted(member_data.keys()):
        for funct in sorted(member_data[member_type].keys()):
            func_info = member_data[member_type][funct]
            description = func_info[0] if len(func_info) > 0 else ''
            required_snippet = func_info[1][0] if len(func_info) > 1 and len(func_info[1]) > 0 else '($0)'
            full_snippet = func_info[1][1] if len(func_info) > 1 and len(func_info[1]) > 1 else '($0)'
            completions['boxlang_member_functions']['basic'].append(sublime.CompletionItem(funct, member_type + '.fn', funct + '($0)', sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'm', 'method'), details=description))
            completions['boxlang_member_functions']['required'].append(sublime.CompletionItem(funct, member_type + '.fn', funct + required_snippet, sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'm', 'method'), details=description))
            completions['boxlang_member_functions']['full'].append(sublime.CompletionItem(funct, member_type + '.fn', funct + full_snippet, sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'm', 'method'), details=description))

def load_json_data(filename):
    """Load JSON data from package resources."""
    json_data = sublime.load_resource('Packages/' + utils.get_plugin_name() + '/src/plugins_/basecompletions/json/' + filename + '.json')
    return json.loads(json_data)

def make_tag_completion(tag, required_attrs):
    """Create a tag completion item."""
    attrs = ''
    for index, attr in enumerate(required_attrs, 1):
        attrs += ' ' + attr + '="$' + str(index) + '"'
    return sublime.CompletionItem(tag, 'tag (boxlang)', tag + attrs, sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_MARKUP, 't', 'BoxLang'))

def _plugin_loaded():
    """Load completions when plugin is loaded."""
    load_completions()