"""
BoxLang commands for Sublime Text.
"""
import os
import subprocess
import threading
import sublime
import sublime_plugin
from .src import utils

class BoxlangFormatCommand(sublime_plugin.TextCommand):
    """Format BoxLang code using boxlang format CLI."""

    def run(self, edit):
        from .boxlang_build import _get_boxlang_path
        bx_path = _get_boxlang_path()
        if not bx_path:
            from .boxlang_build import _show_path_error
            _show_path_error(self.view.window())
            return
        file_path = self.view.file_name()
        if not file_path:
            sublime.status_message('BoxLang: Save the file first to format')
            return
        self.view.run_command('save')
        config_path = self._find_format_config(file_path)
        sublime.status_message('BoxLang: Formatting...')

        def on_format(success, error):
            if success:
                self.view.run_command('revert')
                sublime.status_message('BoxLang: File formatted')
            else:
                sublime.status_message('BoxLang: Format failed - {}'.format(error))

        def _run_format():
            try:
                cmd = [bx_path, 'format']
                if config_path:
                    cmd.extend(['--config', config_path])
                cmd.append(file_path)
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                if proc.returncode == 0:
                    sublime.set_timeout(lambda: on_format(True, None))
                else:
                    error_msg = stderr.decode('utf-8').strip() or stdout.decode('utf-8').strip()
                    sublime.set_timeout(lambda e=error_msg: on_format(False, e))
            except Exception as exc:
                sublime.set_timeout(lambda e=str(exc): on_format(False, e))

        threading.Thread(target=_run_format, daemon=True).start()

    def _find_format_config(self, file_path):
        """Find .bxformat.json config starting from file directory up to project root."""
        file_dir = os.path.dirname(file_path)
        window = self.view.window()
        project_roots = [f for f in (window.folders() if window else [])]
        search_dirs = [file_dir] + project_roots
        checked = set()
        for start_dir in search_dirs:
            current = start_dir
            while current and current not in checked:
                checked.add(current)
                config = os.path.join(current, '.bxformat.json')
                if os.path.isfile(config):
                    return config
                parent = os.path.dirname(current)
                if parent == current:
                    break
                current = parent
        return None

class BoxlangControllerViewToggleCommand(sublime_plugin.TextCommand):
    """Toggle between controller and view files."""

    def run(self, edit):
        file_path = self.view.file_name()
        if not file_path:
            return
        controller_folders = utils.get_setting('boxlang_controller_folders') or ['controllers', 'handlers']
        view_folders = utils.get_setting('boxlang_view_folders') or ['views']
        current_path = utils.normalize_path(file_path)
        for ctrl_folder in controller_folders:
            if '/{}/'.format(ctrl_folder) in current_path:
                view_path = current_path.replace('/{}/'.format(ctrl_folder), '/{}/'.format(view_folders[0]))
                view_path = view_path.replace('Controller.bx', 'View.bxm')
                if os.path.isfile(view_path):
                    self.view.window().open_file(view_path)
                return
        for view_folder in view_folders:
            if '/{}/'.format(view_folder) in current_path:
                ctrl_path = current_path.replace('/{}/'.format(view_folder), '/{}/'.format(controller_folders[0]))
                ctrl_path = ctrl_path.replace('View.bxm', 'Controller.bx')
                if os.path.isfile(ctrl_path):
                    self.view.window().open_file(ctrl_path)
                return

class BoxlangInjectPropertyCommand(sublime_plugin.TextCommand):
    """Inject a property into a component."""

    def run(self, edit):
        project_name = utils.get_project_name(self.view)
        if not project_name:
            return
        from .src.component_index import get_all_indexed
        indexed = get_all_indexed(project_name)
        if not indexed:
            sublime.status_message('BoxLang: No indexed components found')
            return
        items = sorted(indexed.keys())
        self.view.window().show_quick_panel(items, lambda idx: self._insert_property(idx, items) if idx >= 0 else None)

    def _insert_property(self, index, items):
        if index < 0 or index >= len(items):
            return
        component_path = items[index]
        component_name = component_path.split('/')[-1].replace('.bx', '')
        settings = utils.get_setting('boxlang_di_property') or {}
        template = settings.get('script_template', 'property {name};')
        property_code = template.replace('{name}', component_name)
        self.view.run_command('insert', {'characters': property_code + '\n'})
        if settings.get('sort_properties', True):
            pass

class BoxlangWrapHashCommand(sublime_plugin.TextCommand):
    """Wrap selected text in #hash#."""

    def run(self, edit):
        for region in self.view.sel():
            if not region.empty():
                text = self.view.substr(region)
                self.view.replace(edit, region, '#{}#'.format(text))
