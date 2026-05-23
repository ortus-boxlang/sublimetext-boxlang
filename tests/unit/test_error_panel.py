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
        mock_window.find_output_panel = MagicMock(return_value=None)
        mock_window.create_output_panel = MagicMock()
        mock_window.find_output_panel = MagicMock(side_effect=[None, mock_panel])

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
        mock_window.find_output_panel = MagicMock(side_effect=[None, mock_panel])
        mock_window.create_output_panel = MagicMock()
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
        mock_window.find_output_panel = MagicMock(side_effect=[None, mock_panel])
        mock_window.create_output_panel = MagicMock()
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
        mock_window.find_output_panel = MagicMock(side_effect=[None, mock_panel])
        mock_window.create_output_panel = MagicMock()
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
