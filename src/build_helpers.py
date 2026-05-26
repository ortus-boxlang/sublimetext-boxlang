"""
Shared helpers for BoxLang build and command modules.
"""
import os
import sublime
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
    """Get the configured BoxLang executable path, checking common locations."""
    path = utils.get_setting('boxlang_executable_path')
    if path:
        return path
    candidates = [
        os.path.expanduser('~/.bvm/current/bin/boxlang'),
        '/usr/local/bin/boxlang',
        os.path.expanduser('~/.local/bin/boxlang'),
        '/usr/local/boxlang/bin/boxlang',
        os.path.expanduser('~/.local/boxlang/bin/boxlang'),
        'c:\\boxlang\\bin\\boxlang.bat',
        os.path.expandvars('${USERPROFILE}\\.local\\bin\\boxlang.bat')
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def show_path_error(window):
    """Show error dialog when BoxLang executable is not found."""
    window.run_command('hide_panel', {'panel': 'output.exec'})
    sublime.error_message('BoxLang executable not found.\n\nPlease configure the path in your user settings:\n  Preferences: BoxLang Settings\n\nAdd this setting with your BoxLang path:\n  "boxlang_executable_path": "/path/to/boxlang"\n\nCommon locations:\n  ~/.bvm/current/bin/boxlang\n  /usr/local/bin/boxlang\n  ~/.local/bin/boxlang\n  c:\\boxlang\\bin\\boxlang.bat')
