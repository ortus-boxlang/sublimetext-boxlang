"""
BoxLang Language Support for Sublime Text
"""
import sublime
from . import auto_close_tag
from . import boxlang_cli
from . import boxlang_plugins
from . import completions
from . import component_index
from . import error_panel
from . import events
from . import goto_boxlang_file
from . import inline_documentation
from . import status_bar
from . import type_resolver
from . import utils
from . import commands
from .commands import wizard
command_list = []

def plugin_loaded():
    """Called when the plugin is loaded."""
    boxlang_cli.initialize()
    # Show wizard after CLI detection finishes (runs in a background thread).
    # Calling show_wizard() immediately would always report "not found" because
    # detection hasn't completed yet.
    if not wizard.wizard_completed():
        boxlang_cli.on_detection_complete(
            lambda installed, version: sublime.set_timeout(wizard.show_wizard, 500)
        )
    for k, v in globals().items():
        try:
            if '_plugin_loaded' in v.__dict__:
                v._plugin_loaded()
        except Exception:
            pass

def plugin_unloaded():
    """Called when the plugin is unloaded."""
    pass
for k in dir():
    try:
        v = globals()[k]
        for a in dir(v):
            if a.endswith('Command'):
                command_list.append(v.__dict__[a])
    except Exception:
        pass