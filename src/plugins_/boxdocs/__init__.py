"""
BoxLang documentation plugin.
Provides inline documentation linking to boxlang.ortusbooks.com.
"""
import re
import webbrowser
from ... import utils
from ... import documentation_helpers
SIDE_COLOR = '#158CBA'
BIF_URL_MAP = {}
COMPONENT_URL_MAP = {}


def _ensure_docs_data_loaded():
    """Lazy-load completion payloads and URL maps for hover/docs lookups."""
    from ..basecompletions import ensure_loaded
    ensure_loaded()
    if not BIF_URL_MAP and not COMPONENT_URL_MAP:
        build_url_maps()

def build_url_maps():
    """Build URL mapping from completion data."""
    global BIF_URL_MAP, COMPONENT_URL_MAP
    try:
        from ..basecompletions import completions
        params_data = completions.get('boxlang_function_params', {})
        for func_name, entry in params_data.items():
            if not isinstance(entry, dict):
                continue
            url_path = entry.get('url_path', '')
            if url_path:
                BIF_URL_MAP[func_name.lower()] = url_path
        tags_data = completions.get('boxlang_tags_data', {})
        for tag_name, tag_info in tags_data.items():
            if not isinstance(tag_info, dict):
                continue
            url_path = tag_info.get('url_path', '')
            if url_path:
                lookup = tag_name.lower()
                if lookup.startswith('<bx:') and lookup.endswith('>'):
                    lookup = lookup[4:-1]
                elif lookup.startswith('bx:'):
                    lookup = lookup[3:]
                COMPONENT_URL_MAP[lookup] = url_path
    except Exception:
        pass

def get_inline_documentation(boxlang_view, doc_type):
    """Get inline documentation for BIFs, tags, and script constructs."""
    doc_name = None
    doc_attr_or_arg = None
    doc_regions = None
    doc_priority = 0
    if boxlang_view.tag_name:
        doc_name = boxlang_view.tag_name
        doc_attr_or_arg = boxlang_view.tag_attribute_name
        if doc_type == 'hover_doc' and doc_name in ['bx:component', 'bx:interface', 'bx:function'] and boxlang_view.view.match_selector(boxlang_view.position, 'source.boxlang'):
            return None
    elif boxlang_view.view.match_selector(boxlang_view.position, 'support.function.boxlang'):
        word_region = boxlang_view.view.word(boxlang_view.position)
        doc_name = boxlang_view.view.substr(word_region).lower()
        doc_regions = [boxlang_view.view.full_line(word_region.begin())]
    elif boxlang_view.view.match_selector(boxlang_view.position, 'meta.function-call.support.boxlang'):
        result = boxlang_view.get_function_call(boxlang_view.position, True)
        if result:
            doc_name, function_name_region, _ = result
            doc_regions = [boxlang_view.view.full_line(function_name_region.begin())]
    elif boxlang_view.view.match_selector(boxlang_view.position, 'keyword.boxlang, variable.language.boxlang'):
        # Script constructs: try/catch/finally, thread, lock, transaction, loop, query, etc.
        # thread/lock/transaction are scoped as variable.language since they double as scope names
        word_region = boxlang_view.view.word(boxlang_view.position)
        word = boxlang_view.view.substr(word_region).lower()
        if word:
            doc_name = word
            doc_regions = [boxlang_view.view.full_line(word_region.begin())]
    if doc_name:
        lookup_name = doc_name
        if lookup_name.startswith('bx:'):
            lookup_name = lookup_name[3:]
        data = _get_boxdoc(lookup_name)
        if data:
            return boxlang_view.Documentation(doc_regions, build_boxdoc(doc_name, doc_attr_or_arg, data), None, doc_priority)
    return None

def get_completion_docs(boxlang_view):
    """Get documentation shown during completion."""
    if boxlang_view.tag_name and boxlang_view.tag_attribute_name and (boxlang_view.tag_location == 'tag_attributes'):
        lookup_name = boxlang_view.tag_name
        if lookup_name.startswith('bx:'):
            lookup_name = lookup_name[3:]
        data = _get_boxdoc(lookup_name)
        if data:
            for param in data.get('params', []):
                if param.get('name', '').lower() == boxlang_view.tag_attribute_name.lower():
                    return boxlang_view.CompletionDoc(None, build_tag_completion_doc(data, param), None)
        return None
    if boxlang_view.function_call_params and boxlang_view.function_call_params.support and (not boxlang_view.function_call_params.method):
        data = _get_boxdoc(boxlang_view.function_call_params.function_name)
        if data:
            return boxlang_view.CompletionDoc(None, build_function_completion_doc(boxlang_view.function_call_params, data), None)
    return None

def get_goto_boxlang_file(boxlang_view):
    """Get URL for documentation navigation."""
    if boxlang_view.view.match_selector(boxlang_view.position, 'support.function.boxlang'):
        doc_name = boxlang_view.view.substr(boxlang_view.view.word(boxlang_view.position)).lower()
        if doc_name:
            url = _get_bif_url(doc_name)
            if url:
                return boxlang_view.GotoBoxlangFile(url, None)
    elif boxlang_view.view.match_selector(boxlang_view.position, 'meta.function-call.support.boxlang'):
        result = boxlang_view.get_function_call(boxlang_view.position, True)
        if result:
            doc_name, _, _ = result
            if doc_name:
                url = _get_bif_url(doc_name)
                if url:
                    return boxlang_view.GotoBoxlangFile(url, None)
    elif boxlang_view.view.match_selector(boxlang_view.position, 'meta.tag.boxlang,meta.tag.script.boxlang,meta.tag.script.bx.boxlang'):
        doc_name = utils.get_tag_name(boxlang_view.view, boxlang_view.position)
        if doc_name:
            if doc_name.startswith('bx:'):
                doc_name = doc_name[3:]
            url = _get_component_url(doc_name)
            if url:
                return boxlang_view.GotoBoxlangFile(url, None)
    return None

def _get_boxdoc(name):
    """Get documentation for a function, tag, or script construct."""
    try:
        _ensure_docs_data_loaded()
        from ..basecompletions import completions
        # 1. Rich params data (generated from boxlang-docs) — covers all BIFs + module functions
        params_data = completions.get('boxlang_function_params', {})
        lower_params_map = {k.lower(): k for k in params_data}
        canonical_name = lower_params_map.get(name.lower())
        if canonical_name:
            entry = params_data[canonical_name]
            return {
                'type': 'function',
                'name': canonical_name,
                'description': entry.get('description', ''),
                'params': entry.get('params', []),
                'returns': entry.get('returns', ''),
                'category': entry.get('category', ''),
                'url_path': entry.get('url_path', ''),
            }
        # 2. Raw functions data (snippet-based, fallback for any BIFs not in params)
        functions_data = completions.get('boxlang_functions_data', {})
        lower_func_map = {k.lower(): k for k in functions_data}
        canonical_func = lower_func_map.get(name.lower())
        if canonical_func:
            func_data = functions_data[canonical_func]
            if func_data:
                return {
                    'type': 'function',
                    'name': canonical_func,
                    'description': func_data[0] if len(func_data) > 0 else '',
                    'params': _extract_params(func_data),
                    'returns': '',
                }
        # 3. Tags/components (bx: tags, script constructs like thread/lock/loop/query)
        tags_data = completions.get('boxlang_tags_data', {})
        lower_tag_map = {}
        for key in tags_data:
            normalized_key = key.lower()
            lower_tag_map[normalized_key] = key
            lower_tag_map['bx:' + normalized_key] = key
            if normalized_key.startswith('<bx:') and normalized_key.endswith('>'):
                lower_tag_map[normalized_key[4:-1]] = key
                lower_tag_map['bx:' + normalized_key[4:-1]] = key
            elif normalized_key.startswith('bx:'):
                lower_tag_map[normalized_key[3:]] = key
        canonical_tag = lower_tag_map.get(name.lower())
        if canonical_tag:
            tag_info = tags_data[canonical_tag]
            attrs = tag_info.get('attributes', [[], []]) if isinstance(tag_info, dict) else [[], []]
            required = attrs[0] if len(attrs) > 0 else []
            optional = attrs[1] if len(attrs) > 1 else []
            params = [{'name': a, 'required': True, 'type': 'any'} for a in required]
            params.extend([{'name': a, 'required': False, 'type': 'any'} for a in optional])
            return {
                'type': 'tag',
                'name': canonical_tag,
                'description': 'BoxLang component: {}'.format(canonical_tag),
                'params': params,
            }
    except Exception:
        pass
    return None

def _extract_params(func_data):
    """Extract params from function completion data."""
    if len(func_data) < 2:
        return []
    snippet = func_data[1][0] if len(func_data[1]) > 0 else ''
    params = re.findall('\\$\\{(\\d+):(\\w+)\\}', snippet)
    return [{'name': p[1], 'required': True, 'type': 'any'} for p in params]

BASE_URL = 'https://boxlang.ortusbooks.com'

def _get_bif_url(name):
    """Get documentation URL for a built-in function."""
    _ensure_docs_data_loaded()
    stored = BIF_URL_MAP.get(name.lower(), '')
    if not stored:
        return None
    if stored.startswith('http'):
        return stored
    return '{}/{}'.format(BASE_URL, stored)

def _get_component_url(name):
    """Get documentation URL for a component."""
    _ensure_docs_data_loaded()
    lookup = name.lower()
    stored = COMPONENT_URL_MAP.get(lookup, '')
    if not stored:
        return None
    return '{}/{}'.format(BASE_URL, stored)

def build_boxdoc(name, attr_or_arg, data):
    """Build documentation HTML."""
    doc = {'side_color': SIDE_COLOR, 'html': {}}
    if data['type'] == 'function':
        url = _get_bif_url(name)
        if url:
            doc['html']['links'] = [{'href': url, 'text': 'boxlang.ortusbooks.com/.../{}'.format(name.lower())}]
    else:
        url = _get_component_url(name)
        if url:
            doc['html']['links'] = [{'href': url, 'text': 'boxlang.ortusbooks.com/.../{}'.format(name.lower())}]
    doc['html']['header'] = _build_header(data, attr_or_arg)
    doc['html']['body'] = ''
    category = data.get('category', '')
    if category and not attr_or_arg:
        doc['html']['body'] += '<p><span class="category-badge">{}</span></p>'.format(_format_category(category))
    if attr_or_arg:
        for param in data.get('params', []):
            if param.get('name', '').lower() == attr_or_arg.lower():
                header, body = _build_attr_doc(param)
                doc['html']['body'] += documentation_helpers.card(header, body)
                break
    else:
        if data.get('description'):
            doc['html']['body'] += documentation_helpers.card(body=documentation_helpers.clean_html(data['description']))
        if data.get('params'):
            header_text = 'ARGUMENT REFERENCE' if data['type'] == 'function' else 'ATTRIBUTE REFERENCE'
            doc['html']['body'] += '<h2>{}</h2>'.format(header_text)
            for param in data['params']:
                header, body = _build_attr_doc(param)
                doc['html']['body'] += documentation_helpers.card(header, body)
    doc['html']['body'] = re.sub('`([^`\\n<>]+)`', '<span class="code">\\1</span>', doc['html']['body'])
    return doc


def _format_category(category):
    """Format a category slug for display (e.g. 'image-manipulation' → 'Image Manipulation')."""
    return category.replace('-', ' ').replace('_', ' ').title()

def _build_header(data, attr_or_arg=None, include_params=True):
    """Build signature header."""
    if data['type'] != 'function':
        header = '&lt;bx:{}'.format(documentation_helpers.span_wrap(data['name'], 'entity.name.tag.boxlang'))
        for param in data.get('params', []):
            if attr_or_arg:
                if attr_or_arg.lower() != param.get('name', '').lower():
                    continue
            elif not include_params or not param.get('required', False):
                continue
            header += ' {}=""'.format(documentation_helpers.span_wrap(param['name'], 'entity.other.attribute-name'))
        header += '&gt;'
        return header
    header = documentation_helpers.span_wrap(data['name'], 'entity.name.function')
    header += '('
    param_base = ''
    if include_params:
        for param in data.get('params', []):
            span_html = param_base + documentation_helpers.span_wrap(param['name'], 'variable.parameter.function')
            if not param.get('required', True):
                span_html = '[' + span_html + ']'
            param_base = ', '
            header += span_html
    else:
        params = data.get('params', [])
        header += '...' if len(params) > 0 else ''
    header += ')'
    if data.get('returns'):
        header += ': ' + documentation_helpers.span_wrap(data['returns'], 'storage.type')
    return header

def _build_attr_doc(param):
    """Build attribute/argument documentation."""
    header = documentation_helpers.param_header(param)
    body = ''
    if 'default' in param and param['default']:
        body += '<p><em>Default:</em> <span class="code">{}</span></p>'.format(param['default'])
    description = param.get('description', '').replace('\n ', '<br>').replace('\n', '<br>').strip()
    if description:
        body += '<p>{}</p>'.format(description)
    if 'values' in param and param['values']:
        body += '<p><em>values:</em> {}</p>'.format(', '.join([str(v) for v in param['values']]))
    return (header, body)

def build_tag_completion_doc(data, param):
    """Build tag completion documentation."""
    doc = {'side_color': SIDE_COLOR, 'html': {}}
    doc['html']['header'] = _build_header(data, include_params=False)
    _, body = _build_attr_doc(param)
    doc['html']['body'] = body
    doc['html']['arguments'] = documentation_helpers.param_header(param)
    return doc

def build_function_completion_doc(function_call_params, data):
    """Build function completion documentation."""
    doc = {'side_color': SIDE_COLOR, 'html': {}}
    doc['html']['header'] = _build_header(data, include_params=False)
    doc['html']['body'] = ''
    description_params = []
    params = data.get('params', [])
    if params:
        for index, param in enumerate(params):
            if function_call_params.named_params:
                active_name = function_call_params.params[function_call_params.current_index][0] or ''
                is_active = active_name.lower() == param.get('name', '').lower()
            else:
                is_active = index == function_call_params.current_index
            if is_active:
                param_variables = {'name': param.get('name', ''), 'description': param.get('description', '').replace('\n', '<br>'), 'values': ''}
                if 'type' in param and param['type']:
                    param_variables['name'] += ': ' + param['type']
                if 'values' in param and param['values']:
                    param_variables['values'] = '<em>values:</em> ' + ', '.join([str(v) for v in param['values']])
                if param_variables['description'] or param_variables['values']:
                    doc['html']['body'] = '<p>{}</p><p>{}</p>'.format(param_variables['description'], param_variables['values'])
                description_params.append('<span class="active">{}</span>'.format(param['name']))
            elif param.get('required', True):
                description_params.append('<span class="required">{}</span>'.format(param['name']))
            else:
                description_params.append('<span class="optional">{}</span>'.format(param['name']))
        doc['html']['arguments'] = '(' + ', '.join(description_params) + ')'
    return doc

def get_completions(boxlang_view):
    """No completions from this plugin."""
    return None

def _plugin_loaded():
    """Build URL maps when plugin loads."""
    build_url_maps()