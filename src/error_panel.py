"""
Error panel for displaying AST parse errors with F4 navigation.
"""
import sublime
import sublime_plugin
from . import utils
_error_regions = []
_current_error_index = -1
_PANEL_NAME = 'boxlang_errors'

def show_errors(view, file_path, errors):
    """Show parse errors in the output panel and highlight regions."""
    global _error_regions, _current_error_index
    _error_regions = []
    _current_error_index = -1
    panel = view.window().find_output_panel(_PANEL_NAME)
    if not panel:
        view.window().create_output_panel(_PANEL_NAME)
        panel = view.window().find_output_panel(_PANEL_NAME)
    panel.set_syntax_file('Packages/Text/Plain text.tmLanguage')
    panel.settings().set('word_wrap', True)
    panel.settings().set('read_only', True)
    content = 'BoxLang Parse Errors - {}\n'.format(file_path)
    content += '=' * 60 + '\n\n'
    for i, error in enumerate(errors):
        line = error.get('line', 0)
        col = error.get('column', 0)
        message = error.get('message', str(error))
        content += 'Error {} (line {}, col {}):\n'.format(i + 1, line, col)
        content += '  {}\n\n'.format(message)
        if line > 0:
            pt = view.text_point(line - 1, max(0, col - 1))
            _error_regions.append(sublime.Region(pt, view.line(pt).end()))
    panel.run_command('append', {'characters': content})
    if _error_regions:
        view.add_regions('boxlang_parse_errors', _error_regions, 'invalid', 'dot', sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE)
    view.window().run_command('show_panel', {'panel': 'output.{}'.format(_PANEL_NAME)})
    _current_error_index = 0
    _navigate_to_error(view)

def clear_errors(view):
    """Clear all error regions and hide the panel."""
    global _error_regions, _current_error_index
    view.erase_regions('boxlang_parse_errors')
    _error_regions = []
    _current_error_index = -1

def navigate_next(view):
    """Navigate to the next error."""
    global _current_error_index
    if not _error_regions:
        return
    _current_error_index = (_current_error_index + 1) % len(_error_regions)
    _navigate_to_error(view)

def navigate_prev(view):
    """Navigate to the previous error."""
    global _current_error_index
    if not _error_regions:
        return
    _current_error_index = (_current_error_index - 1) % len(_error_regions)
    _navigate_to_error(view)

def _navigate_to_error(view):
    """Navigate the view to the current error index."""
    if _current_error_index < 0 or _current_error_index >= len(_error_regions):
        return
    region = _error_regions[_current_error_index]
    view.sel().clear()
    view.sel().add(sublime.Region(region.begin()))
    view.show_at_center(region)
    line = view.rowcol(region.begin())[0] + 1
    sublime.status_message('BoxLang error {} of {} (line {})'.format(_current_error_index + 1, len(_error_regions), line))

class BoxlangNextErrorCommand(sublime_plugin.TextCommand):
    """Navigate to the next parse error."""

    def run(self, edit):
        navigate_next(self.view)

class BoxlangPrevErrorCommand(sublime_plugin.TextCommand):
    """Navigate to the previous parse error."""

    def run(self, edit):
        navigate_prev(self.view)