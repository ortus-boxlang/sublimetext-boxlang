"""
Application.bx lifecycle method completions and documentation for BoxLang.
Provides completions for onApplicationStart, onRequest, onSessionStart, etc.
"""
import sublime
from .plugin import BoxlangPlugin
APPLICATION_METHODS = {'onApplicationStart': {'signature': 'onApplicationStart()', 'return_type': 'boolean', 'description': 'Called once when the application starts. Return true to allow processing to continue.', 'args': []}, 'onApplicationEnd': {'signature': 'onApplicationEnd(applicationScope)', 'return_type': 'void', 'description': 'Called when the application ends.', 'args': [{'name': 'applicationScope', 'type': 'struct', 'description': 'The application scope'}]}, 'onSessionStart': {'signature': 'onSessionStart()', 'return_type': 'void', 'description': 'Called when a new session starts.', 'args': []}, 'onSessionEnd': {'signature': 'onSessionEnd(sessionScope, applicationScope)', 'return_type': 'void', 'description': 'Called when a session ends.', 'args': [{'name': 'sessionScope', 'type': 'struct', 'description': 'The session scope'}, {'name': 'applicationScope', 'type': 'struct', 'description': 'The application scope'}]}, 'onRequestStart': {'signature': 'onRequestStart(targetPage)', 'return_type': 'boolean', 'description': 'Called at the start of each request. Return true to allow processing to continue.', 'args': [{'name': 'targetPage', 'type': 'string', 'description': 'The target page being requested'}]}, 'onRequest': {'signature': 'onRequest(targetPage)', 'return_type': 'void', 'description': 'Called to process the request. If defined, you must include the target page manually.', 'args': [{'name': 'targetPage', 'type': 'string', 'description': 'The target page being requested'}]}, 'onRequestEnd': {'signature': 'onRequestEnd()', 'return_type': 'void', 'description': 'Called at the end of each request.', 'args': []}, 'onError': {'signature': 'onError(exception, eventName)', 'return_type': 'void', 'description': 'Called when an unhandled exception occurs.', 'args': [{'name': 'exception', 'type': 'any', 'description': 'The exception object'}, {'name': 'eventName', 'type': 'string', 'description': 'The event that caused the error'}]}, 'onMissingTemplate': {'signature': 'onMissingTemplate(targetPage)', 'return_type': 'boolean', 'description': 'Called when a requested template is not found. Return true to suppress default error.', 'args': [{'name': 'targetPage', 'type': 'string', 'description': 'The missing template path'}]}}
SIDE_COLOR = 'color(#4C9BB0 blend(var(--background) 60%))'

class BoxlangPlugin(BoxlangPlugin):
    """Plugin for Application.bx lifecycle method completions."""

    def get_completions(self, boxlang_view):
        """Get Application.bx lifecycle method completions."""
        if not boxlang_view.file_path:
            return None
        file_name = boxlang_view.file_path.split('/')[-1].lower()
        if 'application' not in file_name:
            return None
        completions = []
        for method_name, meta in APPLICATION_METHODS.items():
            args = meta['args']
            snippet_args = ', '.join(['${{{}:{}}}'.format(i + 1, a['name']) for i, a in enumerate(args)])
            content = '{}({})'.format(method_name, snippet_args) if args else '{}()'.format(method_name)
            completions.append(sublime.CompletionItem(method_name, 'lifecycle: {}'.format(meta['return_type']), content, sublime.COMPLETION_FORMAT_SNIPPET, kind=(sublime.KIND_ID_FUNCTION, 'A', 'Application'), details=meta['description']))
        return boxlang_view.CompletionList(completions, 0, False) if completions else None

    def get_inline_documentation(self, boxlang_view, doc_type):
        """Get inline documentation for Application.bx lifecycle methods."""
        if not boxlang_view.file_path:
            return None
        file_name = boxlang_view.file_path.split('/')[-1].lower()
        if 'application' not in file_name:
            return None
        word_region = boxlang_view.view.word(boxlang_view.position)
        word_text = boxlang_view.view.substr(word_region)
        if word_text in APPLICATION_METHODS:
            meta = APPLICATION_METHODS[word_text]
            args = meta['args']
            arg_str = ', '.join(['{}: {}'.format(a['name'], a['type']) for a in args])
            signature = '{}({})'.format(word_text, arg_str)
            doc = {'side_color': SIDE_COLOR, 'html': {'header': 'Lifecycle: <span class="entity_name_function">{}</span>'.format(word_text), 'body': '<p><code>{}</code></p>'.format(signature)}}
            if args:
                doc['html']['body'] += '<h2>Arguments</h2>'
                for a in args:
                    doc['html']['body'] += '<p><code>{}</code>: {} - {}</p>'.format(a['name'], a['type'], a.get('description', ''))
            doc['html']['body'] += '<p>{}</p>'.format(meta['description'])
            doc['html']['body'] += '<p>Return type: <code>{}</code></p>'.format(meta['return_type'])
            return boxlang_view.Documentation([word_region], doc, None, 1)
        return None