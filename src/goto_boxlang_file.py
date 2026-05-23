"""
Go to BoxLang file navigation.
"""

import sublime
import sublime_plugin
import os
import webbrowser
from . import utils
from . import component_index
from .boxlang_view import BoxlangView


def get_goto_boxlang_file(boxlang_view):
    """Get file navigation info for the current position."""
    # Check for function call
    if boxlang_view.view.match_selector(
        boxlang_view.position, "meta.function-call.support.boxlang"
    ):
        func_name, func_region, args_region = boxlang_view.get_function_call(
            boxlang_view.position, True
        )
        # Link to BoxLang docs
        return boxlang_view.GotoBoxlangFile(
            f"https://boxlang.ortusbooks.com/boxlang-language/reference/built-in-functions/{func_name}",
            None
        )

    # Check for tag
    if boxlang_view.view.match_selector(
        boxlang_view.position, "meta.tag.boxlang,meta.tag.script.boxlang"
    ):
        tag_name = utils.get_tag_name(boxlang_view.view, boxlang_view.position)
        if tag_name:
            return boxlang_view.GotoBoxlangFile(
                f"https://boxlang.ortusbooks.com/boxlang-language/reference/components/{tag_name}",
                None
            )

    # Check for dot path in string (new, createObject, import)
    if boxlang_view.view.match_selector(
        boxlang_view.position, "string.quoted"
    ):
        word = boxlang_view.view.word(boxlang_view.position)
        dot_path = boxlang_view.view.substr(word)
        if "." in dot_path:
            file_path = component_index.resolve_path(
                boxlang_view.project_name, boxlang_view.file_path, dot_path
            )
            if file_path and os.path.isfile(file_path):
                return boxlang_view.GotoBoxlangFile(file_path, None)

    return None


class BoxlangGotoFileCommand(sublime_plugin.TextCommand):
    """Go to BoxLang file or documentation."""

    def run(self, edit):
        position = self.view.sel()[0].begin()
        boxlang_view = BoxlangView(self.view, position)
        goto_info = get_goto_boxlang_file(boxlang_view)

        if goto_info:
            if goto_info.file_path.startswith("http"):
                webbrowser.open_new_tab(goto_info.file_path)
            elif os.path.isfile(goto_info.file_path):
                self.view.window().open_file(goto_info.file_path)
            elif goto_info.symbol:
                self.view.window().run_command(
                    "show_overlay",
                    {"overlay": "goto", "text": goto_info.symbol}
                )
