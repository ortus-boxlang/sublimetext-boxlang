"""
Auto-close tag support for BoxLang markup files.
Inserts the corresponding closing tag when typing ">" after a bx: opening tag.
"""
import re
import sublime
import sublime_plugin
from . import utils


def should_auto_close(view):
    settings = sublime.load_settings("boxlang.sublime-settings")
    if not settings.get("boxlang_auto_insert_closing_tag", False):
        return False

    sel = view.sel()
    if len(sel) != 1:
        return False

    pos = sel[0].begin()
    if not view.match_selector(pos - 1, "embedding.boxlang.markup"):
        return False

    search_start = max(0, pos - 500)
    text_before = view.substr(sublime.Region(search_start, pos))

    match = re.search(r"<bx:(\w+)(?:\s[^>]*)?$", text_before, re.DOTALL)
    if not match:
        return False

    tag_name = match.group(1).lower()
    non_closing_tags = [t.lower() for t in settings.get("boxlang_non_closing_tags", [])]
    if tag_name in non_closing_tags:
        return False

    if text_before.rstrip().endswith("/"):
        return False

    return tag_name


def insert_closing_tag(view, tag_name, insert_pos):
    closing = "</bx:{}>".format(tag_name)
    view.run_command("insert", {"characters": closing})
    view.sel().clear()
    view.sel().add(sublime.Region(insert_pos, insert_pos))


class BoxlangAutoCloseTagCommand(sublime_plugin.TextCommand):
    """Insert '>' and auto-close the enclosing bx: tag when enabled."""

    def run(self, edit):
        sel = self.view.sel()
        if not sel:
            return

        # Check eligibility BEFORE modifying the buffer so the regex can see the open tag
        tag_name = should_auto_close(self.view) if len(sel) == 1 else False

        # Insert '>' at all cursor positions (reverse order preserves offsets)
        for region in reversed(list(sel)):
            if region.empty():
                self.view.insert(edit, region.begin(), ">")
            else:
                self.view.replace(edit, region, ">")

        if tag_name:
            # After inserting '>', get the updated cursor position
            cursor_pos = self.view.sel()[0].begin()
            closing = "</bx:{}>".format(tag_name)
            self.view.insert(edit, cursor_pos, closing)
            # Place cursor between opening '>' and closing tag
            self.view.sel().clear()
            self.view.sel().add(sublime.Region(cursor_pos, cursor_pos))

        # Dismiss any completion popup that was open before > was typed,
        # otherwise its commit action can replace the freshly inserted >.
        view = self.view
        sublime.set_timeout(lambda: view.run_command("hide_auto_complete"), 0)
