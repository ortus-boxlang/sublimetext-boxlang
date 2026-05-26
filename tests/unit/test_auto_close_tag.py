"""
Unit tests for auto-close tag feature in src/auto_close_tag.py.
"""

import pytest
from unittest.mock import MagicMock, patch
from tests.expectations import expect


class FakeRegion:
    """A simple object that behaves like sublime.Region for testing."""
    def __init__(self, begin, end):
        self._begin = begin
        self._end = end
    def begin(self):
        return self._begin
    def end(self):
        return self._end


def _make_view(text_before_cursor, scope="embedding.boxlang.markup"):
    """Create a mock sublime.View for testing auto-close tag logic."""
    cursor_pos = len(text_before_cursor)

    view = MagicMock()

    selection = MagicMock()
    selection.begin.return_value = cursor_pos

    sel_mock = MagicMock()
    sel_mock.__len__.return_value = 1
    sel_mock.__getitem__.return_value = selection
    view.sel.return_value = sel_mock

    def substr_side_effect(region):
        if region.begin() == max(0, cursor_pos - 500) and region.end() == cursor_pos:
            return text_before_cursor
        return ""

    view.substr.side_effect = substr_side_effect

    def match_selector(pos, selector_str):
        if "embedding.boxlang.markup" in selector_str:
            return scope == "embedding.boxlang.markup"
        if "source.boxlang" in selector_str and "embedding.boxlang.markup" not in selector_str:
            return scope == "source.boxlang"
        return False

    view.match_selector.side_effect = match_selector
    view.run_command = MagicMock()

    return view, cursor_pos


class TestAutoCloseTag:
    """Tests for the auto_close_tag.should_auto_close function."""

    def test_settings_disabled_returns_false(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = False
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view("<bx:output>")
        expect(should_auto_close(view)).to_be_false()

    def test_not_in_markup_scope_returns_false(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view("<bx:output>", scope="source.boxlang")
        expect(should_auto_close(view)).to_be_false()

    def test_auto_closes_simple_tag(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view("<bx:output>")
        expect(should_auto_close(view)).to_be("output")

    def test_auto_closes_tag_with_attributes(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view('<bx:query name="users" datasource="main">')
        expect(should_auto_close(view)).to_be("query")

    def test_does_not_close_self_closing_tag_with_slash(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view('<bx:param name="id" />')
        expect(should_auto_close(view)).to_be_false()

    def test_does_not_close_non_closing_tag(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = ["abort", "dump", "param"]

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view("<bx:abort>")
        expect(should_auto_close(view)).to_be_false()

    def test_does_not_close_dump_tag(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = ["abort", "dump", "param"]

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view('<bx:dump var="#user#">')
        expect(should_auto_close(view)).to_be_false()

    def test_auto_closes_script_tag(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view("<bx:script>")
        expect(should_auto_close(view)).to_be("script")

    def test_auto_closes_function_tag(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view('<bx:function name="init">')
        expect(should_auto_close(view)).to_be("function")


class TestInsertClosingTag:
    """Tests for the auto_close_tag.insert_closing_tag function."""

    def test_insert_closing_tag(self):
        from src.auto_close_tag import insert_closing_tag

        import sublime
        sublime.Region = FakeRegion

        view = MagicMock()
        view.run_command = MagicMock()

        sel_mock = MagicMock()
        view.sel.return_value = sel_mock

        insert_closing_tag(view, "output", 10)

        view.run_command.assert_called_once_with(
            "insert", {"characters": "</bx:output>"}
        )
        sel_mock.clear.assert_called_once()
        sel_mock.add.assert_called_once()


class TestAutoCloseTagEdgeCases:
    """Edge case tests for auto-close tag."""

    def test_no_bx_tag_returns_false(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view("some text >")
        expect(should_auto_close(view)).to_be_false()

    def test_multiple_selections_returns_false(self, mock_sublime_settings):
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close
        view = MagicMock()
        sel_mock = MagicMock()
        sel_mock.__len__.return_value = 2
        view.sel.return_value = sel_mock

        expect(should_auto_close(view)).to_be_false()

    def test_tag_name_case_normalized(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view("<bx:Output>")
        expect(should_auto_close(view)).to_be("output")

    def test_non_closing_tags_case_insensitive(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = ["Abort", "DUMP"]

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion

        view, cursor_pos = _make_view("<bx:abort>")
        expect(should_auto_close(view)).to_be_false()

        view2, cursor_pos2 = _make_view("<bx:DUMP>")
        expect(should_auto_close(view2)).to_be_false()

    def test_multi_line_tag(self, mock_sublime_settings, mock_sublime):
        mock_sublime.Region = FakeRegion
        mock_sublime_settings["boxlang_auto_insert_closing_tag"] = True
        mock_sublime_settings["boxlang_non_closing_tags"] = []

        from src.auto_close_tag import should_auto_close, sublime
        sublime.Region = FakeRegion
        view, cursor_pos = _make_view('<bx:output\n  key="value"\n  attr="test">')
        expect(should_auto_close(view)).to_be("output")
