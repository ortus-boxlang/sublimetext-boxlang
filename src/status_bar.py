"""
Status bar integration for BoxLang.
Displays version, indexing progress, and error counts.
"""
import sublime
import sublime_plugin
from . import boxlang_cli
from . import component_index
from . import utils
_STATUS_KEY_VERSION = 'boxlang_version'
_STATUS_KEY_INDEXING = 'boxlang_indexing'
_STATUS_KEY_ERRORS = 'boxlang_errors'
_indexing_progress = {}
_error_counts = {}

def set_indexing_progress(project_name, indexed, total):
    """Update indexing progress for a project."""
    _indexing_progress[project_name] = (indexed, total)
    _update_all_status_bars()

def set_error_count(view, count):
    """Update error count for a view."""
    file_path = view.file_name()
    if file_path:
        _error_counts[file_path] = count
        _update_status_bar(view)

def _update_all_status_bars():
    """Update status bars for all open windows."""
    for window in sublime.windows():
        for view in window.views():
            _update_status_bar(view)

_BOXLANG_SCOPE = 'source.boxlang, embedding.boxlang.markup'

def _update_status_bar(view):
    """Update status bar for a single view."""
    if utils.get_setting('boxlang_status_bar_enabled') is False:
        view.erase_status(_STATUS_KEY_VERSION)
        view.erase_status(_STATUS_KEY_INDEXING)
        view.erase_status(_STATUS_KEY_ERRORS)
        return
    if not view.match_selector(0, _BOXLANG_SCOPE):
        return
    version = boxlang_cli.get_version()
    if version:
        view.set_status(_STATUS_KEY_VERSION, 'BoxLang v{}'.format(version))
    elif boxlang_cli.is_installed():
        view.set_status(_STATUS_KEY_VERSION, 'BoxLang: detecting...')
    else:
        view.set_status(_STATUS_KEY_VERSION, 'BoxLang: not found')
    file_path = view.file_name()
    project_name = utils.get_project_name(view)
    if project_name and project_name in _indexing_progress:
        indexed, total = _indexing_progress[project_name]
        if indexed < total:
            pct = int(indexed / total * 100) if total > 0 else 0
            view.set_status(_STATUS_KEY_INDEXING, 'Indexing: {}/{} ({}%)'.format(indexed, total, pct))
        else:
            view.erase_status(_STATUS_KEY_INDEXING)
    else:
        view.erase_status(_STATUS_KEY_INDEXING)
    if file_path and file_path in _error_counts:
        count = _error_counts[file_path]
        if count > 0:
            view.set_status(_STATUS_KEY_ERRORS, 'BoxLang: {} error(s)'.format(count))
        else:
            view.erase_status(_STATUS_KEY_ERRORS)
    else:
        view.erase_status(_STATUS_KEY_ERRORS)

class BoxlangStatusUpdateListener(sublime_plugin.EventListener):
    """Update status bar on activation and loading."""

    def on_activated_async(self, view):
        if view.match_selector(0, _BOXLANG_SCOPE):
            _update_status_bar(view)

    def on_load_async(self, view):
        if view.match_selector(0, _BOXLANG_SCOPE):
            _update_status_bar(view)

    def on_post_save_async(self, view):
        if view.match_selector(0, _BOXLANG_SCOPE):
            _update_status_bar(view)

def _plugin_loaded():
    """Initialize status bar when plugin loads."""
    boxlang_cli.on_detection_complete(lambda installed, version: _update_all_status_bars())