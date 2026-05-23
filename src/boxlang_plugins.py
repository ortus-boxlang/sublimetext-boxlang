"""
BoxLang plugin loader.
"""

import importlib
from .plugins_.plugin import BoxlangPlugin

directory = [
    "basecompletions",
    "boxdocs",
    "cfcs",
    "dotpaths",
    "typecompletions",
    "applicationbx",
    "in_file_completions",
]

plugins = []


for p in directory:
    try:
        m = importlib.import_module(".plugins_." + p, __package__)
        globals()[p] = m
        for a in dir(m):
            v = m.__dict__[a]
            if a.endswith("Command"):
                globals()[a] = v
            elif a == "BoxlangPlugin":
                try:
                    if v.__bases__ and issubclass(v, BoxlangPlugin):
                        plugins.append(v())
                except AttributeError:
                    pass
    except ImportError:
        pass


def _plugin_loaded():
    """Called after all plugins are loaded."""
    for p in directory:
        m = globals().get(p)
        if m and "_plugin_loaded" in m.__dict__:
            m._plugin_loaded()
