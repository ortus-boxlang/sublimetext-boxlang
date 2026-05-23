"""
BoxLang Language Support for Sublime Text
"""

import sublime
from . import boxlang_cli
from . import completions
from . import component_index
from . import events
from . import goto_boxlang_file
from . import inline_documentation
from . import utils
from . import commands
from .commands import wizard

command_list = []


def plugin_loaded():
    """Called when the plugin is loaded."""
    # Initialize BoxLang CLI detection
    boxlang_cli.initialize()

    # Run wizard if first time
    if not wizard.wizard_completed():
        wizard.show_wizard()

    # Notify all modules
    for k, v in globals().items():
        try:
            if "_plugin_loaded" in v.__dict__:
                v._plugin_loaded()
        except Exception:
            pass


def plugin_unloaded():
    """Called when the plugin is unloaded."""
    pass


# Load commands
for k in dir():
    try:
        v = globals()[k]
        for a in dir(v):
            if a.endswith("Command"):
                command_list.append(v.__dict__[a])
    except Exception:
        pass
