"""
Shared helpers for BoxLang build and command modules.
"""
import os
import sublime
from . import boxlang_cli
from . import utils


def get_project_root(window, file_path):
    """Resolve the owning project folder for a file path, if available."""
    folders = window.folders() if window else []
    normalized_file = os.path.normpath(file_path)
    for folder in folders:
        normalized_folder = os.path.normpath(folder)
        if normalized_file == normalized_folder or normalized_file.startswith(normalized_folder + os.sep):
            return folder
    return os.path.dirname(file_path)


def get_boxlang_path():
    """Get the BoxLang executable path (setting, standard install locations, then PATH), or None."""
    path, source = boxlang_cli.resolve_executable()
    return None if source == 'missing' else path


def show_path_error(window):
    """Show error dialog when BoxLang executable is not found."""
    window.run_command('hide_panel', {'panel': 'output.exec'})
    sublime.error_message('BoxLang executable not found.\n\nPlease configure the path in your user settings:\n  Preferences: BoxLang Settings\n\nAdd this setting with your BoxLang path:\n  "boxlang_executable_path": "/path/to/boxlang"\n\nCommon locations:\n  ~/.bvm/current/bin/boxlang\n  /opt/homebrew/bin/boxlang\n  /usr/local/bin/boxlang\n  ~/.local/bin/boxlang\n  c:\\boxlang\\bin\\boxlang.bat')
