"""
First-run install wizard for BoxLang package.
"""

import sublime
import sublime_plugin
import os
from .. import boxlang_cli
from .. import utils

WIZARD_FLAG_KEY = "boxlang_wizard_completed"


def wizard_completed():
    """Check if the wizard has been completed."""
    return sublime.load_settings("boxlang.sublime-settings").get(WIZARD_FLAG_KEY, False)


def mark_wizard_completed():
    """Mark the wizard as completed."""
    settings = sublime.load_settings("boxlang.sublime-settings")
    settings.set(WIZARD_FLAG_KEY, True)
    sublime.save_settings("boxlang.sublime-settings")


def show_wizard():
    """Show the first-run wizard panel."""
    window = sublime.active_window()
    if not window:
        return

    # Step 1: Welcome & Detection
    _show_step_welcome(window)


def _show_step_welcome(window):
    """Step 1: Welcome screen with BoxLang detection status."""
    installed = boxlang_cli.is_installed()
    version = boxlang_cli.get_version()

    if installed:
        message = (
            f"Welcome to BoxLang for Sublime Text!\n\n"
            f"BoxLang detected: {version}\n\n"
            f"This package provides syntax highlighting, completions, "
            f"inline documentation, formatting, and more for BoxLang files.\n\n"
            f"Click Next to configure your preferences."
        )
        result = sublime.yes_no_cancel_dialog(
            message,
            "Next",
            "Skip Setup"
        )
        if result == sublime.DIALOG_YES:
            _show_step_cfml(window)
        elif result == sublime.DIALOG_NO:
            mark_wizard_completed()
    else:
        message = (
            "Welcome to BoxLang for Sublime Text!\n\n"
            "BoxLang was NOT found in your PATH.\n\n"
            "Some features require BoxLang to be installed:\n"
            "  - Component parsing and indexing\n"
            "  - Code formatting\n"
            "  - Build & run\n"
            "  - Compile to bytecode\n\n"
            "Install BoxLang:\n"
            "https://boxlang.ortusbooks.com/getting-started/installation/\n\n"
            "You can still use syntax highlighting without BoxLang."
        )
        result = sublime.yes_no_cancel_dialog(
            message,
            "Open Install Page",
            "Continue Anyway"
        )
        if result == sublime.DIALOG_YES:
            sublime.run_command("open_url", {"url": "https://boxlang.ortusbooks.com/getting-started/installation/"})
            # Still show next step after they return
            _show_step_cfml(window)
        elif result == sublime.DIALOG_NO:
            _show_step_cfml(window)


def _show_step_cfml(window):
    """Step 2: CFML file support option."""
    # Check if CFML package is installed
    cfml_installed = _is_cfml_package_installed()

    if cfml_installed:
        message = (
            "CFML File Support\n\n"
            "The CFML package is already installed.\n\n"
            "BoxLang can natively parse CFML files (.cfm, .cfc, .cfs), "
            "but enabling support here may conflict with the CFML package.\n\n"
            "Do you want to enable CFML file support in this package?"
        )
    else:
        message = (
            "CFML File Support\n\n"
            "BoxLang can natively parse CFML files (.cfm, .cfc, .cfs) "
            "using its AST parser.\n\n"
            "Do you want this package to also handle CFML files?\n\n"
            "You can always change this later in settings:\n"
            "  boxlang_enable_cfml_fallback: true"
        )

    result = sublime.yes_no_cancel_dialog(
        message,
        "Enable CFML Support",
        "BoxLang Only"
    )

    if result == sublime.DIALOG_YES:
        _set_cfml_fallback(True)
    elif result == sublime.DIALOG_NO:
        _set_cfml_fallback(False)

    _show_step_done(window)


def _show_step_done(window):
    """Step 3: Done screen with quick tips."""
    message = (
        "You're all set!\n\n"
        "Quick tips:\n"
        "  F1           - Show inline documentation\n"
        "  Shift+Alt+F  - Format code\n"
        "  Ctrl+B       - Build & run\n"
        "  Ctrl+Alt+D   - Insert writeDump()\n\n"
        "Open Settings to customize your experience."
    )
    result = sublime.yes_no_cancel_dialog(
        message,
        "Open Settings",
        "Close"
    )

    if result == sublime.DIALOG_YES:
        window.run_command("edit_settings", {
            "base_file": "${packages}/BoxLang/settings/boxlang.sublime-settings",
            "default": "{\n\t$0\n}\n"
        })

    mark_wizard_completed()


def _is_cfml_package_installed():
    """Check if the CFML package is installed."""
    try:
        # Try to find CFML package resources
        sublime.load_resource("Packages/CFML/src/__init__.py")
        return True
    except Exception:
        return False


def _set_cfml_fallback(enabled):
    """Enable or disable CFML file fallback in settings."""
    settings = sublime.load_settings("boxlang.sublime-settings")
    settings.set("boxlang_enable_cfml_fallback", enabled)
    sublime.save_settings("boxlang.sublime-settings")


class BoxlangRunWizardCommand(sublime_plugin.ApplicationCommand):
    """Re-run the first-time setup wizard."""

    def run(self):
        show_wizard()
