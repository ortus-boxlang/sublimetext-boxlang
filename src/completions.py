"""
Completion orchestrator for the BoxLang package.
"""

import sublime_plugin
from . import inline_documentation
from . import utils
from . import boxlang_plugins
from .boxlang_view import BoxlangView


def get_completions(view, position, prefix):
    """Get completions for the given position."""
    boxlang_view = BoxlangView(view, position, prefix)
    if not boxlang_view.type:
        return None

    completion_lists = []
    minimum_priority = 0
    docs = []

    for p in boxlang_plugins.plugins:
        completionlist = p.get_completions(boxlang_view)
        if completionlist:
            completion_lists.append(completionlist)
            if completionlist.exclude_lower_priority:
                minimum_priority = completionlist.priority

    if utils.get_setting("boxlang_completion_docs"):
        for p in boxlang_plugins.plugins:
            inline_doc = p.get_completion_docs(boxlang_view)
            if inline_doc:
                docs.append(inline_doc)

    full_completion_list = []
    for completionlist in completion_lists:
        full_completion_list.extend(completionlist.completions)

    if len(docs) > 0:
        inline_documentation.display_documentation(view, docs, "completion_doc", 0)
    return full_completion_list


class BoxlangUpdateCompletionDocCommand(sublime_plugin.TextCommand):
    """Update completion documentation when a new parameter is entered."""

    def run(self, edit):
        self.view.run_command("insert_snippet", {"contents": ","})
        if inline_documentation.doc_window == "completion_doc":
            position = self.view.sel()[0].begin()
            boxlang_view = BoxlangView(self.view, position)
            docs = []
            for p in boxlang_plugins.plugins:
                inline_doc = p.get_completion_docs(boxlang_view)
                if inline_doc:
                    docs.append(inline_doc)

            if len(docs) > 0:
                inline_documentation.display_documentation(
                    self.view, docs, "completion_doc", 0
                )
            else:
                self.view.hide_popup()
