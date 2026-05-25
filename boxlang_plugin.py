"""
BoxLang Language Support for Sublime Text — root plugin entry point.
Mirrors the cfml_plugin.py pattern: EventListeners and plugin_loaded MUST live
in a top-level package file so Sublime Text registers them correctly.
"""
import sublime
import sublime_plugin
from .src import completions, events, utils
from .src import plugin_loaded as _src_plugin_loaded

# Re-export sub-package commands at root level so ST4 discovers and registers them.
from .src.commands.wizard import BoxlangRunWizardCommand
from .src.component_index import BoxlangIndexProjectCommand
from .src.inline_documentation import BoxlangInlineDocumentationCommand
from .src.goto_boxlang_file import BoxlangGotoFileCommand
from .src.error_panel import BoxlangNextErrorCommand, BoxlangPrevErrorCommand
from .src.completions import BoxlangUpdateCompletionDocCommand


def plugin_loaded():
    _src_plugin_loaded()


class BoxlangEventListener(sublime_plugin.EventListener):

    # ── buffer-metadata / component-index lifecycle ──────────────────────────

    def on_load_async(self, view):
        events.trigger("on_load_async", view)

    def on_close(self, view):
        events.trigger("on_close", view)

    def on_modified_async(self, view):
        events.trigger("on_modified_async", view)

    def on_post_save_async(self, view):
        if not view.file_name():
            return
        events.trigger("on_post_save_async", view)

    # ── completions ───────────────────────────────────────────────────────────

    def on_query_completions(self, view, prefix, locations):
        if not locations:
            return None
        position = locations[0]
        if not view.match_selector(
            max(0, position - 1),
            "source.boxlang, embedding.boxlang.markup",
        ):
            return None
        completion_list = completions.get_completions(view, position, prefix)
        if not completion_list:
            return None
        return (completion_list, sublime.INHIBIT_WORD_COMPLETIONS)

    # ── hover documentation ───────────────────────────────────────────────────

    def on_hover(self, view, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT:
            return
        if not view.match_selector(
            point, "source.boxlang, embedding.boxlang.markup"
        ):
            return
        view.run_command(
            "boxlang_inline_documentation",
            {"pt": point, "doc_type": "hover_doc"},
        )

    # ── re-trigger completions after commit ───────────────────────────────────

    def on_post_text_command(self, view, command_name, args):
        if command_name != "commit_completion":
            return
        pos = view.sel()[0].begin()
        # Re-open completions after a dot accessor
        if view.substr(pos - 1) == "." and view.match_selector(
            pos - 1, "source.boxlang punctuation.accessor.boxlang"
        ):
            view.run_command("auto_complete", {"api_completions_only": True})
