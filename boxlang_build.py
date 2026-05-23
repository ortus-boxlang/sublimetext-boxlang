"""
BoxLang build commands for Sublime Text.
Provides run, compile, debug, and audit commands that respect the boxlang_executable_path setting.
"""
import sublime
import sublime_plugin
import os
from .src import utils

def _get_boxlang_path():
    """Get the configured BoxLang executable path, checking common locations."""
    path = utils.get_setting('boxlang_executable_path')
    if path:
        return path
    candidates = [os.path.expanduser('~/.bvm/current/bin/boxlang'), '/usr/local/bin/boxlang', os.path.expanduser('~/.local/bin/boxlang'), '/usr/local/boxlang/bin/boxlang', os.path.expanduser('~/.local/boxlang/bin/boxlang'), 'c:\\boxlang\\bin\\boxlang.bat', os.path.expandvars('${USERPROFILE}\\.local\\bin\\boxlang.bat')]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None

def _show_path_error(window):
    """Show error dialog when BoxLang executable is not found."""
    window.run_command('hide_panel', {'panel': 'output.exec'})
    sublime.error_message('BoxLang executable not found.\n\nPlease configure the path in your user settings:\n  Preferences: BoxLang Settings\n\nAdd this setting with your BoxLang path:\n  "boxlang_executable_path": "/path/to/boxlang"\n\nCommon locations:\n  ~/.bvm/current/bin/boxlang\n  /usr/local/bin/boxlang\n  ~/.local/bin/boxlang\n  c:\\boxlang\\bin\\boxlang.bat')

class BoxlangRunCommand(sublime_plugin.WindowCommand):
    """Run the current BoxLang file."""

    def run(self, with_args=False):
        view = self.window.active_view()
        if not view:
            return
        file_path = view.file_name()
        if not file_path:
            sublime.status_message('BoxLang: Save the file first to run')
            return
        bx_path = _get_boxlang_path()
        if not bx_path:
            _show_path_error(self.window)
            return
        if with_args:

            def on_done(args):
                self.window.run_command('exec', {'shell_cmd': '{} "{}" {}'.format(bx_path, file_path, args), 'file_regex': '(?:Error compiling.*Line: ([0-9]+) Col: ([0-9]+) - (.*))'})
            self.window.show_input_panel('Arguments:', '', on_done, None, None)
        else:
            self.window.run_command('exec', {'shell_cmd': '{} "{}"'.format(bx_path, file_path), 'file_regex': '(?:Error compiling.*Line: ([0-9]+) Col: ([0-9]+) - (.*))'})

class BoxlangCompileCommand(sublime_plugin.WindowCommand):
    """Compile the current BoxLang file or project."""

    def run(self, scope='file'):
        view = self.window.active_view()
        if not view:
            return
        file_path = view.file_name()
        if not file_path:
            sublime.status_message('BoxLang: Save the file first to compile')
            return
        bx_path = _get_boxlang_path()
        if not bx_path:
            _show_path_error(self.window)
            return
        target = utils.get_setting('boxlang_compile_target') or './bin'
        if scope == 'project':
            file_path = os.path.dirname(file_path)
        self.window.run_command('exec', {'shell_cmd': '{} compile --source "{}" --target "{}"'.format(bx_path, file_path, target), 'file_regex': '(?:Error compiling.*Line: ([0-9]+) Col: ([0-9]+) - (.*))'})

class BoxlangDebugCommand(sublime_plugin.WindowCommand):
    """Debug the current BoxLang file."""

    def run(self):
        view = self.window.active_view()
        if not view:
            return
        file_path = view.file_name()
        if not file_path:
            sublime.status_message('BoxLang: Save the file first to debug')
            return
        bx_path = _get_boxlang_path()
        if not bx_path:
            _show_path_error(self.window)
            return
        self.window.run_command('exec', {'shell_cmd': '{} --bx-debug "{}"'.format(bx_path, file_path), 'file_regex': '(?:Error compiling.*Line: ([0-9]+) Col: ([0-9]+) - (.*))'})

class BoxlangAuditCommand(sublime_plugin.WindowCommand):
    """Run feature audit on the current BoxLang file."""

    def run(self):
        view = self.window.active_view()
        if not view:
            return
        file_path = view.file_name()
        if not file_path:
            sublime.status_message('BoxLang: Save the file first to audit')
            return
        bx_path = _get_boxlang_path()
        if not bx_path:
            _show_path_error(self.window)
            return
        self.window.run_command('exec', {'shell_cmd': '{} featureaudit --source "{}"'.format(bx_path, file_path)})