"""
BoxLang commands module.
"""

import sublime
import sublime_plugin
import os
import tempfile
from .. import boxlang_cli
from .. import utils


class BoxlangFormatCommand(sublime_plugin.TextCommand):
    """Format BoxLang code using boxlang format CLI."""

    def run(self, edit):
        if not boxlang_cli.is_installed():
            sublime.error_message(
                "BoxLang formatting requires BoxLang to be installed.\n\n"
                "Install BoxLang: https://boxlang.ortusbooks.com/getting-started/installation/"
            )
            return

        file_path = self.view.file_name()
        if not file_path:
            sublime.status_message("BoxLang: Save the file first to format")
            return

        # Check for .cfformat.json and suggest conversion
        project_dir = os.path.dirname(file_path)
        cfformat_path = os.path.join(project_dir, ".cfformat.json")
        bxformat_path = os.path.join(project_dir, ".bxformat.json")

        if os.path.isfile(cfformat_path) and not os.path.isfile(bxformat_path):
            result = sublime.yes_no_cancel_dialog(
                "Found legacy .cfformat.json configuration file.\n\n"
                "BoxLang uses .bxformat.json for formatting settings.\n\n"
                "Would you like to convert .cfformat.json to .bxformat.json?",
                "Convert",
                "Ignore"
            )
            if result == sublime.DIALOG_YES:
                try:
                    import shutil
                    shutil.copy(cfformat_path, bxformat_path)
                    sublime.status_message("BoxLang: Created .bxformat.json from .cfformat.json")
                except Exception:
                    sublime.status_message("BoxLang: Failed to create .bxformat.json")

        sublime.status_message("BoxLang: Formatting...")

        def on_format(success, error):
            if success:
                # Reload the file
                self.view.run_command("revert")
                sublime.status_message("BoxLang: File formatted")
            else:
                sublime.status_message(f"BoxLang: Format failed - {error}")

        boxlang_cli.run_format(file_path, callback=on_format)


class BoxlangControllerViewToggleCommand(sublime_plugin.TextCommand):
    """Toggle between controller and view files."""

    def run(self, edit):
        file_path = self.view.file_name()
        if not file_path:
            return

        controller_folders = utils.get_setting("boxlang_controller_folders") or ["controllers", "handlers"]
        view_folders = utils.get_setting("boxlang_view_folders") or ["views"]

        current_path = utils.normalize_path(file_path)

        # Check if we're in a controller folder
        for ctrl_folder in controller_folders:
            if f"/{ctrl_folder}/" in current_path:
                # Switch to view
                view_path = current_path.replace(f"/{ctrl_folder}/", f"/{view_folders[0]}/")
                # Remove controller suffix and add view extension
                view_path = view_path.replace("Controller.bx", "View.bxm")
                if os.path.isfile(view_path):
                    self.view.window().open_file(view_path)
                return

        # Check if we're in a view folder
        for view_folder in view_folders:
            if f"/{view_folder}/" in current_path:
                # Switch to controller
                ctrl_path = current_path.replace(f"/{view_folder}/", f"/{controller_folders[0]}/")
                ctrl_path = ctrl_path.replace("View.bxm", "Controller.bx")
                if os.path.isfile(ctrl_path):
                    self.view.window().open_file(ctrl_path)
                return


class BoxlangInjectPropertyCommand(sublime_plugin.TextCommand):
    """Inject a property into a component."""

    def run(self, edit):
        # Get all indexed components for the project
        project_name = utils.get_project_name(self.view)
        if not project_name:
            return

        from ..component_index import get_all_indexed
        indexed = get_all_indexed(project_name)

        if not indexed:
            sublime.status_message("BoxLang: No indexed components found")
            return

        # Show quick panel to select component
        items = sorted(indexed.keys())
        self.view.window().show_quick_panel(
            items,
            lambda idx: self._insert_property(idx, items) if idx >= 0 else None
        )

    def _insert_property(self, index, items):
        if index < 0 or index >= len(items):
            return

        component_path = items[index]
        component_name = component_path.split("/")[-1].replace(".bx", "")

        settings = utils.get_setting("boxlang_di_property") or {}
        template = settings.get("script_template", "property {name};")
        property_code = template.replace("{name}", component_name)

        # Find the class body and insert property
        self.view.run_command("insert", {"characters": property_code + "\n"})

        if settings.get("sort_properties", True):
            # Sort properties (simplified - just insert at top)
            pass


class BoxlangWrapHashCommand(sublime_plugin.TextCommand):
    """Wrap selected text in #hash#."""

    def run(self, edit):
        for region in self.view.sel():
            if not region.empty():
                text = self.view.substr(region)
                self.view.replace(edit, region, f"#{text}#")
