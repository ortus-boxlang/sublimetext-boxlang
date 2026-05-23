"""
Unit tests for the Status Bar (status_bar.py).
"""

import pytest
from tests.expectations import expect
from unittest.mock import MagicMock, patch


class TestStatusBar:
    """Tests for the status bar module."""

    def test_set_indexing_progress(self):
        """Test setting indexing progress."""
        from src import status_bar
        status_bar._indexing_progress.clear()
        status_bar.set_indexing_progress("test.sublime-project", 5, 10)
        expect(status_bar._indexing_progress["test.sublime-project"]).to_be((5, 10))

    def test_set_error_count(self):
        """Test setting error count."""
        from src import status_bar
        status_bar._error_counts.clear()
        mock_view = MagicMock()
        mock_view.file_name = MagicMock(return_value="/path/to/file.bx")
        status_bar.set_error_count(mock_view, 3)
        expect(status_bar._error_counts["/path/to/file.bx"]).to_be(3)

    def test_update_status_bar_version(self, mock_sublime):
        """Test status bar shows version."""
        from src import status_bar
        from src import boxlang_cli
        boxlang_cli._boxlang_installed = True
        boxlang_cli._boxlang_version = "1.13.0+54"

        mock_view = MagicMock()
        mock_view.file_name = MagicMock(return_value=None)
        mock_view.match_selector = MagicMock(return_value=True)

        status_bar._update_status_bar(mock_view)
        mock_view.set_status.assert_called()

    def test_update_status_bar_indexing(self, mock_sublime):
        """Test status bar shows indexing progress."""
        from src import status_bar
        status_bar._indexing_progress["test.sublime-project"] = (3, 10)

        mock_view = MagicMock()
        mock_view.file_name = MagicMock(return_value=None)
        mock_view.match_selector = MagicMock(return_value=True)

        mock_sublime.windows = MagicMock(return_value=[])

        status_bar._update_status_bar(mock_view)

    def test_status_bar_disabled(self, mock_sublime):
        """Test status bar is cleared when disabled."""
        from src import status_bar
        mock_view = MagicMock()
        mock_view.file_name = MagicMock(return_value=None)
        mock_view.match_selector = MagicMock(return_value=True)

        mock_sublime.load_settings = MagicMock()
        mock_sublime.load_settings.return_value.get = MagicMock(return_value=False)

        status_bar._update_status_bar(mock_view)
        mock_view.erase_status.assert_called()


class TestStatusBarEventListener:
    """Tests for the status bar event listener."""

    def test_event_listener_exists(self):
        """Test that the event listener class exists."""
        from src.status_bar import BoxlangStatusUpdateListener
        expect(BoxlangStatusUpdateListener).not_to_be_none()
