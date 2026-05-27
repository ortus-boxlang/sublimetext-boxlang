"""
In-file completions for BoxLang.
Provides completions for symbols defined in the current file (functions, variables, properties).
"""
import re
import sublime
from ..plugin import BoxlangPlugin
SIDE_COLOR = 'color(#4C9BB0 blend(var(--background) 60%))'

def parse_file_symbols(view):
    """Parse the current view for function and variable definitions."""
    symbols = {'functions': [], 'variables': [], 'properties': []}
    full_text = view.substr(sublime.Region(0, view.size()))
    lines = full_text.split('\n')
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        func_match = re.match('^(?:public|private|remote|package)\\s+(?:any|void|string|numeric|boolean|array|struct|query|component|[\\w.]+)\\s+(\\w+)\\s*\\(', stripped)
        if not func_match:
            func_match = re.match('^function\\s+(\\w+)\\s*\\(', stripped)
        if func_match:
            func_name = func_match.group(1)
            args_match = re.search('\\(([^)]*)\\)', stripped)
            args = []
            if args_match:
                arg_str = args_match.group(1)
                args = [a.strip().split(':')[0].split('=')[0].strip() for a in arg_str.split(',') if a.strip()]
            return_type = 'any'
            rt_match = re.match('^(?:public|private|remote|package)\\s+(\\w+)', stripped)
            if rt_match:
                return_type = rt_match.group(1)
            symbols['functions'].append({'name': func_name, 'args': args, 'return_type': return_type, 'line': line_num})
            continue
        prop_match = re.match('^(?:public|private|package)\\s+(?:any|void|string|numeric|boolean|array|struct|query|component|[\\w.]+)\\s+(\\w+)\\s*[;=]', stripped)
        if prop_match:
            prop_name = prop_match.group(1)
            prop_type = re.match('^(?:public|private|package)\\s+(\\w+)', stripped).group(1)
            symbols['properties'].append({'name': prop_name, 'type': prop_type, 'line': line_num})
            continue
        prop_decl_match = re.match('^property\\s+(?:(public|private|package)\\s+)?(?:(any|void|string|numeric|boolean|array|struct|query|component|[\\w.]+)\\s+)?(\\w+)\\b', stripped)
        if prop_decl_match:
            prop_type = prop_decl_match.group(2) or 'any'
            symbols['properties'].append({'name': prop_decl_match.group(3), 'type': prop_type, 'line': line_num})
            continue
        var_match = re.match('^var\\s+(\\w+)\\s*=', stripped)
        if not var_match:
            var_match = re.match('^(\\w+)\\s*=\\s*', stripped)
        if var_match and (not stripped.startswith('if')) and (not stripped.startswith('for')) and (not stripped.startswith('while')):
            var_name = var_match.group(1)
            if var_name not in ['true', 'false', 'null', 'undefined']:
                symbols['variables'].append({'name': var_name, 'line': line_num})
    return symbols

class BoxlangPlugin(BoxlangPlugin):
    """Plugin for in-file symbol completions."""

    def get_completions(self, boxlang_view):
        """Get completions for symbols in the current file."""
        symbols = parse_file_symbols(boxlang_view.view)
        completions = []
        if boxlang_view.type == 'dot':
            if len(boxlang_view.dot_context) == 1 and boxlang_view.dot_context[0].name == 'this':
                for func in symbols['functions']:
                    args = func['args']
                    snippet_args = ', '.join(['${{{}:{}}}'.format(i + 1, a) for i, a in enumerate(args)])
                    content = '{}({})'.format(func['name'], snippet_args) if args else '{}()'.format(func['name'])
                    completions.append(sublime.CompletionItem(func['name'], 'method: {}'.format(func['return_type']), content, sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'f', 'this'), details='Line {}'.format(func['line'])))
                for prop in symbols['properties']:
                    completions.append(sublime.CompletionItem(prop['name'], 'property: {}'.format(prop['type']), prop['name'], sublime.COMPLETION_FORMAT_TEXT, kind=(sublime.KIND_ID_VARIABLE, 'p', 'property'), details='Line {}'.format(prop['line'])))
        elif boxlang_view.type == 'script':
            for func in symbols['functions']:
                args = func['args']
                snippet_args = ', '.join(['${{{}:{}}}'.format(i + 1, a) for i, a in enumerate(args)])
                content = '{}({})'.format(func['name'], snippet_args) if args else '{}()'.format(func['name'])
                completions.append(sublime.CompletionItem(func['name'], 'function: {}'.format(func['return_type']), content, sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'f', 'function'), details='Line {}'.format(func['line'])))
            for var in symbols['variables']:
                completions.append(sublime.CompletionItem(var['name'], 'variable', var['name'], sublime.COMPLETION_FORMAT_TEXT, kind=(sublime.KIND_ID_VARIABLE, 'v', 'variable'), details='Line {}'.format(var['line'])))
        return boxlang_view.CompletionList(completions, 0, False) if completions else None

    def get_inline_documentation(self, boxlang_view, doc_type):
        """Get inline documentation for in-file symbols."""
        symbols = parse_file_symbols(boxlang_view.view)
        word_region = boxlang_view.view.word(boxlang_view.position)
        word_text = boxlang_view.view.substr(word_region)
        for func in symbols['functions']:
            if func['name'] == word_text:
                args = func['args']
                arg_str = ', '.join(args)
                signature = '{}({}): {}'.format(func['name'], arg_str, func['return_type'])
                doc = {'side_color': SIDE_COLOR, 'html': {'header': 'Function: <span class="entity_name_function">{}</span>'.format(word_text), 'body': '<p><code>{}</code></p>'.format(signature)}}
                if args:
                    doc['html']['body'] += '<h2>Arguments</h2>'
                    for a in args:
                        doc['html']['body'] += '<p><code>{}</code></p>'.format(a)
                doc['html']['body'] += '<p>Defined at line {}</p>'.format(func['line'])
                return boxlang_view.Documentation([word_region], doc, None, 1)
        for prop in symbols['properties']:
            if prop['name'] == word_text:
                doc = {'side_color': SIDE_COLOR, 'html': {'header': 'Property: <span class="variable">{}</span>'.format(word_text), 'body': '<p>Type: <code>{}</code></p>'.format(prop['type'])}}
                doc['html']['body'] += '<p>Defined at line {}</p>'.format(prop['line'])
                return boxlang_view.Documentation([word_region], doc, None, 1)
        return None

    def get_goto_boxlang_file(self, boxlang_view):
        """Go to symbol definition in current file."""
        symbols = parse_file_symbols(boxlang_view.view)
        word_region = boxlang_view.view.word(boxlang_view.position)
        word_text = boxlang_view.view.substr(word_region)
        for func in symbols['functions']:
            if func['name'] == word_text:
                point = boxlang_view.view.text_point(func['line'] - 1, 0)
                return boxlang_view.GotoBoxlangFile(boxlang_view.file_path, point)
        for prop in symbols['properties']:
            if prop['name'] == word_text:
                point = boxlang_view.view.text_point(prop['line'] - 1, 0)
                return boxlang_view.GotoBoxlangFile(boxlang_view.file_path, point)
        return None