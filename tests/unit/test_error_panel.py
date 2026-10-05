"""
Unit tests for the Error Panel (error_panel.py).
"""

import pytest
from tests.expectations import expect
from unittest.mock import MagicMock, patch


class MockRegion:
    """Mock sublime.Region class."""
    def __init__(self, begin=0, end=0):
        self._begin = begin
        self._end = end
    def begin(self):
        return self._begin
    def end(self):
        return self._end


class TestErrorPanelShowErrors:
    """Tests for error_panel.show_errors."""

    def test_show_errors_creates_panel(self):
        """Test that show_errors creates an output panel."""
        from src import error_panel
        mock_view = MagicMock()
        mock_window = MagicMock()
        mock_panel = MagicMock()
        mock_view.window = MagicMock(return_value=mock_window)
        mock_window.create_output_panel = MagicMock(return_value=mock_panel)

        errors = [
            {"line": 10, "column": 5, "message": "Syntax error"}
        ]
        with patch.object(error_panel, "sublime", create=True) as mock_sublime:
            mock_sublime.Region = MockRegion
            error_panel.show_errors(mock_view, "/path/to/file.bx", errors)

        mock_window.create_output_panel.assert_called_once()

    def test_show_errors_highlights_regions(self):
        """Test that error regions are highlighted."""
        from src import error_panel
        mock_view = MagicMock()
        mock_window = MagicMock()
        mock_panel = MagicMock()
        mock_view.window = MagicMock(return_value=mock_window)
        mock_window.create_output_panel = MagicMock(return_value=mock_panel)
        mock_view.text_point = MagicMock(return_value=100)
        mock_view.line = MagicMock(return_value=MockRegion(100, 150))

        errors = [
            {"line": 10, "column": 5, "message": "Syntax error"}
        ]
        with patch.object(error_panel, "sublime", create=True) as mock_sublime:
            mock_sublime.Region = MockRegion
            mock_sublime.DRAW_SQUIGGLY_UNDERLINE = 1
            mock_sublime.DRAW_NO_FILL = 2
            mock_sublime.DRAW_NO_OUTLINE = 4
            error_panel.show_errors(mock_view, "/path/to/file.bx", errors)

        mock_view.add_regions.assert_called_once()

    def test_show_errors_shows_panel(self):
        """Test that the error panel is shown."""
        from src import error_panel
        mock_view = MagicMock()
        mock_window = MagicMock()
        mock_panel = MagicMock()
        mock_view.window = MagicMock(return_value=mock_window)
        mock_window.create_output_panel = MagicMock(return_value=mock_panel)
        mock_view.text_point = MagicMock(return_value=100)
        mock_view.line = MagicMock(return_value=MockRegion(100, 150))

        errors = [
            {"line": 10, "column": 5, "message": "Syntax error"}
        ]
        with patch.object(error_panel, "sublime", create=True) as mock_sublime:
            mock_sublime.Region = MockRegion
            mock_sublime.DRAW_SQUIGGLY_UNDERLINE = 1
            mock_sublime.DRAW_NO_FILL = 2
            mock_sublime.DRAW_NO_OUTLINE = 4
            error_panel.show_errors(mock_view, "/path/to/file.bx", errors)

        mock_window.run_command.assert_called_once()

    def test_show_errors_multiple_errors(self):
        """Test showing multiple errors."""
        from src import error_panel
        mock_view = MagicMock()
        mock_window = MagicMock()
        mock_panel = MagicMock()
        mock_view.window = MagicMock(return_value=mock_window)
        mock_window.create_output_panel = MagicMock(return_value=mock_panel)
        mock_view.text_point = MagicMock(return_value=100)
        mock_view.line = MagicMock(return_value=MockRegion(100, 150))

        errors = [
            {"line": 10, "column": 5, "message": "Error 1"},
            {"line": 20, "column": 3, "message": "Error 2"},
            {"line": 30, "column": 1, "message": "Error 3"},
        ]
        with patch.object(error_panel, "sublime", create=True) as mock_sublime:
            mock_sublime.Region = MockRegion
            mock_sublime.DRAW_SQUIGGLY_UNDERLINE = 1
            mock_sublime.DRAW_NO_FILL = 2
            mock_sublime.DRAW_NO_OUTLINE = 4
            error_panel.show_errors(mock_view, "/path/to/file.bx", errors)

        expect(len(error_panel._error_regions)).to_be(3)


class TestErrorPanelClearErrors:
    """Tests for error_panel.clear_errors."""

    def test_clear_errors_removes_regions(self):
        """Test that clear_errors removes regions."""
        from src import error_panel
        mock_view = MagicMock()
        error_panel._error_regions = [MagicMock()]

        error_panel.clear_errors(mock_view)

        mock_view.erase_regions.assert_called_once()
        expect(error_panel._error_regions).to_be_empty()


class TestErrorPanelNavigation:
    """Tests for error panel navigation."""

    def test_navigate_next(self):
        """Test navigating to next error."""
        from src import error_panel
        mock_view = MagicMock()
        mock_sel = MagicMock()
        mock_view.rowcol = MagicMock(return_value=(9, 4))
        mock_view.sel = MagicMock(return_value=mock_sel)
        mock_view.show_at_center = MagicMock()
        error_panel._error_regions = [MockRegion(100), MockRegion(200)]
        error_panel._current_error_index = 0

        error_panel.navigate_next(mock_view)
        expect(error_panel._current_error_index).to_be(1)

    def test_navigate_next_wraps(self):
        """Test that next navigation wraps around."""
        from src import error_panel
        mock_view = MagicMock()
        mock_sel = MagicMock()
        mock_view.rowcol = MagicMock(return_value=(9, 4))
        mock_view.sel = MagicMock(return_value=mock_sel)
        mock_view.show_at_center = MagicMock()
        error_panel._error_regions = [MockRegion(100), MockRegion(200)]
        error_panel._current_error_index = 1

        error_panel.navigate_next(mock_view)
        expect(error_panel._current_error_index).to_be(0)

    def test_navigate_prev(self):
        """Test navigating to previous error."""
        from src import error_panel
        mock_view = MagicMock()
        mock_sel = MagicMock()
        mock_view.rowcol = MagicMock(return_value=(9, 4))
        mock_view.sel = MagicMock(return_value=mock_sel)
        mock_view.show_at_center = MagicMock()
        error_panel._error_regions = [MockRegion(100), MockRegion(200)]
        error_panel._current_error_index = 1

        error_panel.navigate_prev(mock_view)
        expect(error_panel._current_error_index).to_be(0)

    def test_navigate_prev_wraps(self):
        """Test that prev navigation wraps around."""
        from src import error_panel
        mock_view = MagicMock()
        mock_sel = MagicMock()
        mock_view.rowcol = MagicMock(return_value=(9, 4))
        mock_view.sel = MagicMock(return_value=mock_sel)
        mock_view.show_at_center = MagicMock()
        error_panel._error_regions = [MockRegion(100), MockRegion(200)]
        error_panel._current_error_index = 0

        error_panel.navigate_prev(mock_view)
        expect(error_panel._current_error_index).to_be(1)

    def test_navigate_with_no_errors(self):
        """Test navigation when there are no errors."""
        from src import error_panel
        mock_view = MagicMock()
        error_panel._error_regions = []
        error_panel._current_error_index = -1

        error_panel.navigate_next(mock_view)
        expect(error_panel._current_error_index).to_be(-1)


class TestErrorAnnotations:
    """Tests for inline annotations, gutter icons and gutter hover."""

    def _show(self, errors, settings=None):
        from src import error_panel
        view = MagicMock()
        view.id.return_value = 11
        window = MagicMock()
        view.window = MagicMock(return_value=window)
        window.create_output_panel = MagicMock(return_value=MagicMock())
        view.text_point = MagicMock(return_value=100)
        view.line = MagicMock(return_value=MockRegion(100, 150))
        settings = settings or {}
        with patch.object(error_panel, "sublime", create=True) as mock_sublime, \
                patch.object(error_panel.utils, "get_setting", side_effect=lambda key: settings.get(key)):
            mock_sublime.Region = MockRegion
            error_panel.show_errors(view, "/p/a.bx", errors, show_panel=False, navigate=False)
        return view, error_panel

    def test_annotations_added_per_region(self):
        errors = [{"line": 2, "column": 1, "message": "first"}, {"line": 4, "column": 1, "message": "second"}]
        view, _ = self._show(errors)
        kwargs = view.add_regions.call_args[1]
        expect(kwargs["annotations"]).to_be(["first", "second"])
        expect(kwargs["annotation_color"]).to_be("red")

    def test_annotation_is_escaped_single_line_and_truncated(self):
        from src import error_panel
        text = error_panel._annotation_html("a <b> & c\nsecond line")
        expect(text).to_be("a &lt;b&gt; &amp; c")
        long_text = error_panel._annotation_html("x" * 500)
        expect(len(long_text)).to_be(error_panel._ANNOTATION_MAX_LENGTH)
        expect(long_text.endswith("…")).to_be_true()

    def test_inline_annotations_can_be_disabled(self):
        view, _ = self._show([{"line": 2, "column": 1, "message": "m"}], {"boxlang_error_inline_annotations": False})
        expect("annotations" in view.add_regions.call_args[1]).to_be_false()

    def test_gutter_icon_can_be_disabled(self):
        view, _ = self._show([{"line": 2, "column": 1, "message": "m"}], {"boxlang_error_gutter_icons": False})
        expect(view.add_regions.call_args[0][3]).to_be("")

    def test_gutter_icon_default_is_dot(self):
        view, _ = self._show([{"line": 2, "column": 1, "message": "m"}])
        expect(view.add_regions.call_args[0][3]).to_be("dot")

    def test_errors_for_row_uses_zero_based_rows(self):
        view, error_panel = self._show([{"line": 3, "column": 1, "message": "m1"}, {"line": 3, "column": 5, "message": "m2"}])
        expect(error_panel.errors_for_row(view, 2)).to_be(["m1", "m2"])
        expect(error_panel.errors_for_row(view, 0)).to_be_empty()

    def test_gutter_hover_shows_popup_only_on_error_lines(self):
        view, error_panel = self._show([{"line": 3, "column": 1, "message": "bad <thing>"}])
        view.rowcol = MagicMock(return_value=(2, 0))
        with patch.object(error_panel, "sublime", create=True):
            expect(error_panel.show_gutter_hover(view, 5)).to_be_true()
            view.rowcol = MagicMock(return_value=(7, 0))
            expect(error_panel.show_gutter_hover(view, 9)).to_be_false()
        expect(view.show_popup.call_args[0][0]).to_contain("bad &lt;thing&gt;")

    def test_clear_errors_forgets_rows(self):
        view, error_panel = self._show([{"line": 3, "column": 1, "message": "m"}])
        error_panel.clear_errors(view)
        expect(error_panel.errors_for_row(view, 2)).to_be_empty()
