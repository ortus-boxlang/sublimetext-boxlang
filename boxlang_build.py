"""
BoxLang build commands for Sublime Text.
Provides run, compile, debug, and audit commands that respect the boxlang_executable_path setting.
"""
import sublime
import sublime_plugin
import os
from .src import utils


def _get_project_root(window, file_path):
    """Resolve the owning project folder for a file path, if available."""
    folders = window.folders() if window else []
    normalized_file = os.path.normpath(file_path)
    for folder in folders:
        normalized_folder = os.path.normpath(folder)
        if normalized_file == normalized_folder or normalized_file.startswith(normalized_folder + os.sep):
            return folder
    return os.path.dirname(file_path)

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

    def run(self, args=None, **kwargs):
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
        self.window.run_command('exec', {'shell_cmd': '{} "{}"'.format(bx_path, file_path), 'file_regex': '(?:Error compiling.*Line: ([0-9]+) Col: ([0-9]+) - (.*))'})

class BoxlangRunWithArgsCommand(sublime_plugin.WindowCommand):
    """Run the current BoxLang file with user-provided arguments."""

    def run(self, args=None, **kwargs):
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

        def on_done(args):
            self.window.run_command('exec', {'shell_cmd': '{} "{}" {}'.format(bx_path, file_path, args), 'file_regex': '(?:Error compiling.*Line: ([0-9]+) Col: ([0-9]+) - (.*))'})
        self.window.show_input_panel('Arguments:', '', on_done, None, None)

class BoxlangCompileCommand(sublime_plugin.WindowCommand):
    """Compile the current BoxLang file or project."""

    def run(self, scope='file', args=None, **kwargs):
        if isinstance(args, dict):
            scope = args.get('scope', scope)
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
        configured_target = utils.get_setting('boxlang_compile_target') or 'bin'
        project_root = _get_project_root(self.window, file_path)

        if os.path.isabs(configured_target):
            target_root = configured_target
        else:
            target_root = os.path.normpath(os.path.join(project_root, configured_target))

        if scope == 'project':
            file_path = project_root
            target = target_root
        else:
            source_parent = os.path.dirname(file_path)
            rel_parent = os.path.relpath(source_parent, project_root)
            target_dir = target_root if rel_parent == os.curdir else os.path.join(target_root, rel_parent)
            target = os.path.join(target_dir, os.path.basename(file_path))

        target = os.path.normpath(target)
        self.window.run_command('exec', {'shell_cmd': '{} compile --source "{}" --target "{}"'.format(bx_path, file_path, target), 'file_regex': '(?:Error compiling.*Line: ([0-9]+) Col: ([0-9]+) - (.*))'})

class BoxlangDebugCommand(sublime_plugin.WindowCommand):
    """Debug the current BoxLang file."""

    def run(self, args=None, **kwargs):
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

    def run(self, args=None, **kwargs):
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