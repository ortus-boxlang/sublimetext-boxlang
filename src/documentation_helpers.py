"""
Documentation HTML generation helpers.
"""
import re

def span_wrap(text, scope_class):
    """Wrap text in a span with the given scope class."""
    return '<span class="{}">{}</span>'.format(scope_class, text)

def param_header(param):
    """Generate a parameter header HTML string."""
    header = span_wrap(param.get('name', ''), 'variable.parameter.function')
    if param.get('type'):
        header += ': ' + span_wrap(param['type'], 'storage.type')
    if not param.get('required', True):
        header = '[' + header + ']'
    return header

def card(header=None, body=None):
    """Generate a card HTML element."""
    html = '<div class="card">'
    if header:
        html += '<div class="card-header">{}</div>'.format(header)
    if body:
        html += '<div class="card-body">{}</div>'.format(body)
    html += '</div>'
    return html

def clean_html(text):
    """Clean HTML text for safe display."""
    if not text:
        return ''
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = re.sub('`([^`]+)`', '<code>\\1</code>', text)
    text = text.replace('\n', '<br>')
    return text

def build_signature(name, params, return_type=None):
    """Build a function signature HTML string."""
    sig = span_wrap(name, 'entity.name.function')
    sig += '('
    param_parts = []
    for param in params:
        part = span_wrap(param.get('name', ''), 'variable.parameter.function')
        if param.get('type'):
            part += ': ' + span_wrap(param['type'], 'storage.type')
        if not param.get('required', True):
            part = '[' + part + ']'
        param_parts.append(part)
    sig += ', '.join(param_parts)
    sig += ')'
    if return_type:
        sig += ': ' + span_wrap(return_type, 'storage.type')
    return sig