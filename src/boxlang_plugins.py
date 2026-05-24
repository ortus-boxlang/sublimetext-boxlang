"""
BoxLang plugin loader.
"""
import importlib
from .plugins_.plugin import BoxlangPlugin

directory = ['basecompletions', 'boxdocs', 'cfcs', 'dotpaths', 'typecompletions', 'applicationbx', 'in_file_completions']
plugins = []

_package = __name__.rsplit('.', 1)[0]


class ModulePluginAdapter(BoxlangPlugin):
    """Adapter for legacy module-style plugins."""

    def __init__(self, module):
        self._module = module

    def _call(self, name, *args):
        func = getattr(self._module, name, None)
        if callable(func):
            return func(*args)
        return None

    def get_completion_docs(self, boxlang_view):
        return self._call('get_completion_docs', boxlang_view)

    def get_completions(self, boxlang_view):
        return self._call('get_completions', boxlang_view)

    def get_goto_boxlang_file(self, boxlang_view):
        return self._call('get_goto_boxlang_file', boxlang_view)

    def get_inline_documentation(self, boxlang_view, doc_type):
        return self._call('get_inline_documentation', boxlang_view, doc_type)

    def get_method_preview(self, boxlang_view):
        return self._call('get_method_preview', boxlang_view)


for p in directory:
    try:
        m = importlib.import_module('.plugins_.' + p, _package)
        globals()[p] = m
        module_has_hooks = False
        for a in dir(m):
            v = m.__dict__[a]
            if a.endswith('Command'):
                globals()[a] = v
            elif a == 'BoxlangPlugin':
                try:
                    if v.__bases__ and issubclass(v, BoxlangPlugin):
                        plugins.append(v())
                        module_has_hooks = True
                except AttributeError:
                    pass
        if not module_has_hooks and any(callable(getattr(m, name, None)) for name in (
            'get_completions',
            'get_completion_docs',
            'get_inline_documentation',
            'get_goto_boxlang_file',
            'get_method_preview'
        )):
            plugins.append(ModulePluginAdapter(m))
    except ImportError:
        pass

def _plugin_loaded():
    """Called after all plugins are loaded."""
    for p in directory:
        m = globals().get(p)
        if m and '_plugin_loaded' in m.__dict__:
            m._plugin_loaded()