"""
Syntax checking powered by `boxlang check` (BoxLang 1.17+).

Runs on save by default, can optionally run while typing (debounced), and
feeds the error panel, squiggly underlines and the status bar error count.
"""
import os
import tempfile
import sublime
import sublime_plugin
from . import boxlang_cli
from . import error_panel
from . import events
from . import status_bar
from . import utils

_BOXLANG_SCOPE = 'source.boxlang, embedding.boxlang.markup'
_generation = {}
_version_warning_shown = False


def should_check(view):
    """Return True when the view holds a file that `boxlang check` can validate."""
    file_path = view.file_name()
    if not boxlang_cli.is_checkable_file(file_path):
        return False
    return view.match_selector(0, _BOXLANG_SCOPE)


def _check_available():
    """Return True when the CLI supports `check`, warning once when it does not."""
    global _version_warning_shown
    if not boxlang_cli.is_installed():
        return False
    if boxlang_cli.supports_check():
        return True
    if not _version_warning_shown:
        _version_warning_shown = True
        sublime.status_message('BoxLang: syntax check needs BoxLang 1.17+ (found {})'.format(boxlang_cli.get_version() or 'unknown'))
    return False


def _write_buffer(view):
    """Write the unsaved buffer to a temp file with the same extension and return its path."""
    ext = os.path.splitext(view.file_name())[1]
    fd, path = tempfile.mkstemp(suffix=ext, prefix='boxlang_check_')
    with os.fdopen(fd, 'w', encoding='utf-8') as handle:
        handle.write(view.substr(sublime.Region(0, view.size())))
    return path


def apply_results(view, file_path, issues, show_panel=True):
    """Display check results for a view. Must run on the UI thread."""
    status_bar.set_error_count(view, len(issues))
    if issues:
        error_panel.show_errors(view, file_path, issues, show_panel=show_panel, navigate=False)
    else:
        error_panel.clear_errors(view)
        if show_panel:
            error_panel.hide_panel(view)


def check_view(view, show_panel=True, use_buffer=False):
    """
    Check a view asynchronously and display the results.

    Args:
        view: The view to check
        show_panel: Open the error panel when errors are found
        use_buffer: Check the unsaved buffer contents instead of the file on disk
    """
    if not should_check(view) or not _check_available():
        return
    view_id = view.id()
    generation = _generation.get(view_id, 0) + 1
    _generation[view_id] = generation
    file_path = view.file_name()
    temp_path = _write_buffer(view) if use_buffer else None

    def on_done(issues, error):
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass

        def update():
            # A newer check started while this one ran, so drop the stale result
            if _generation.get(view_id) != generation:
                return
            if error:
                sublime.status_message('BoxLang: syntax check failed - {}'.format(error.splitlines()[0] if error else ''))
                return
            apply_results(view, file_path, issues, show_panel=show_panel)

        sublime.set_timeout(update)

    boxlang_cli.run_check(temp_path or file_path, callback=on_done)


def on_post_save_async(view):
    """Check on save."""
    if utils.get_setting('boxlang_check_on_save') is False:
        return
    check_view(view, show_panel=utils.get_setting('boxlang_check_show_panel') is not False)


def on_modified_async(view):
    """Check while typing, debounced. Off by default."""
    if not utils.get_setting('boxlang_check_on_type'):
        return
    if not should_check(view):
        return
    delay = utils.get_setting('boxlang_check_on_type_delay_ms')
    if not isinstance(delay, int) or delay < 100:
        delay = 1000
    view_id = view.id()
    token = _generation.get(view_id, 0) + 1
    _generation[view_id] = token

    def fire():
        # Only the latest keystroke's timer actually runs the check
        if _generation.get(view_id) == token:
            check_view(view, show_panel=False, use_buffer=True)

    sublime.set_timeout_async(fire, delay)


def on_close(view):
    """Forget per-view state."""
    _generation.pop(view.id(), None)


class BoxlangCheckSyntaxCommand(sublime_plugin.TextCommand):
    """Run `boxlang check` on the current file and show any syntax errors."""

    def run(self, edit):
        if not self.view.file_name():
            sublime.status_message('BoxLang: Save the file first to check syntax')
            return
        if not boxlang_cli.is_installed():
            sublime.status_message('BoxLang: executable not found')
            return
        if not _check_available():
            return
        sublime.status_message('BoxLang: Checking syntax...')
        check_view(self.view, show_panel=True, use_buffer=self.view.is_dirty())

    def is_enabled(self):
        return should_check(self.view)


events.subscribe('on_post_save_async', on_post_save_async)
events.subscribe('on_modified_async', on_modified_async)
events.subscribe('on_close', on_close)
