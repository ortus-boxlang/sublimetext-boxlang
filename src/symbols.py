"""
Quick-panel navigation for symbols the grammar cannot list on its own:
TestBox specs and suites (describe/it names) and property declarations.

The parsing helpers are pure functions over buffer text so they can be unit tested.
"""
import re
import sublime
import sublime_plugin
from . import testbox_runner

_SCRIPT_PROPERTY = re.compile(r'^[ \t]*property\b([^;{]*);', re.MULTILINE)
_TAG_PROPERTY = re.compile(r'<bx:property\b([^>]*)>', re.IGNORECASE)
_NAME_ATTRIBUTE = re.compile(r'\bname\s*=\s*(["\'])(.*?)\1', re.IGNORECASE)
_ATTRIBUTE_PAIR = re.compile(r'\b\w+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s;]+)')
_PLAIN_IDENTIFIER = re.compile(r'^[A-Za-z_$][\w$]*$')


def find_specs(text):
    """
    List the TestBox suites and specs in a buffer.

    Returns a list of (kind, name, offset) tuples sorted by position, where kind is
    'suite' or 'spec'.
    """
    found = []
    for match in testbox_runner.CALL_PATTERN.finditer(text):
        kind = 'spec' if match.group(1) in testbox_runner.SPEC_FUNCTIONS else 'suite'
        found.append((kind, match.group(3), match.start()))
    for match in testbox_runner.XUNIT_PATTERN.finditer(text):
        found.append(('spec', match.group(1), match.start()))
    return sorted(found, key=lambda item: item[2])


def _property_name(attributes):
    """Extract a property name from the text between `property` and `;` (or the tag attributes)."""
    named = _NAME_ATTRIBUTE.search(attributes)
    if named:
        return named.group(2)
    remaining = _ATTRIBUTE_PAIR.sub(' ', attributes).split()
    for token in reversed(remaining):
        if _PLAIN_IDENTIFIER.match(token):
            return token
    return None


def find_properties(text):
    """
    List property declarations in a buffer, in script (`property string name;`,
    `property name="x" type="string";`) and tag (`<bx:property name="x">`) form.

    Returns a list of (name, offset) tuples sorted by position.
    """
    found = []
    for match in _SCRIPT_PROPERTY.finditer(text):
        name = _property_name(match.group(1))
        if name:
            found.append((name, match.start() + match.group(0).index('property')))
    for match in _TAG_PROPERTY.finditer(text):
        name = _property_name(match.group(1))
        if name:
            found.append((name, match.start()))
    return sorted(found, key=lambda item: item[1])


class BoxlangGotoSymbolCommand(sublime_plugin.TextCommand):
    """Show a quick panel of specs, suites or properties and jump to the selection. kind: spec or property."""

    def run(self, edit, kind='spec'):
        text = self.view.substr(sublime.Region(0, self.view.size()))
        if kind == 'property':
            entries = [(name, offset, 'property') for name, offset in find_properties(text)]
            empty_message = 'BoxLang: no properties found in this file'
        else:
            entries = [(name, offset, label) for label, name, offset in find_specs(text)]
            empty_message = 'BoxLang: no TestBox specs or suites found in this file'
        if not entries:
            sublime.status_message(empty_message)
            return
        items = [[name, '{} (line {})'.format(label, self.view.rowcol(offset)[0] + 1)] for name, offset, label in entries]
        start_selection = [sublime.Region(r.a, r.b) for r in self.view.sel()]

        def reveal(index):
            self.view.show_at_center(entries[index][1])

        def on_done(index):
            if index < 0:
                self.view.sel().clear()
                self.view.sel().add_all(start_selection)
                return
            offset = entries[index][1]
            self.view.sel().clear()
            self.view.sel().add(sublime.Region(offset))
            self.view.show_at_center(offset)

        self.view.window().show_quick_panel(items, on_done, on_highlight=reveal)

    def is_enabled(self):
        return self.view.match_selector(0, 'source.boxlang, embedding.boxlang.markup')
