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
        project_dir = os.path.dirname(file_path)
        cfformat_path = os.path.join(project_dir, '.cfformat.json')
        bxformat_path = os.path.join(project_dir, '.bxformat.json')
        if os.path.isfile(cfformat_path) and (not os.path.isfile(bxformat_path)):
            result = sublime.yes_no_cancel_dialog('Found legacy .cfformat.json configuration file.\n\nBoxLang uses .bxformat.json for formatting settings.\n\nWould you like to convert .cfformat.json to .bxformat.json?', 'Convert', 'Ignore')
            if result == sublime.DIALOG_YES:
                try:
                    import shutil
                    shutil.copy(cfformat_path, bxformat_path)
                    sublime.status_message('BoxLang: Created .bxformat.json from .cfformat.json')
                except Exception:
                    sublime.status_message('BoxLang: Failed to create .bxformat.json')
        sublime.status_message('BoxLang: Formatting...')

        def on_format(success, error):
            if success:
                self.view.run_command('revert')
                sublime.status_message('BoxLang: File formatted')
            else:
                sublime.status_message('BoxLang: Format failed - {}'.format(error))

        def _run_format():
            try:
                proc = subprocess.Popen([bx_path, 'format', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                if proc.returncode == 0:
                    sublime.set_timeout(lambda: on_format(True, None))
                else:
                    error_msg = stderr.decode('utf-8').strip() or stdout.decode('utf-8').strip()
                    sublime.set_timeout(lambda e=error_msg: on_format(False, e))
            except Exception as exc:
                sublime.set_timeout(lambda e=str(exc): on_format(False, e))

        threading.Thread(target=_run_format, daemon=True).start()

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
