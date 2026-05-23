"""
Unit tests for utility functions (utils.py).
"""

import pytest
from unittest.mock import MagicMock
from tests.expectations import expect


class TestNormalizePath:
    """Tests for utils.normalize_path."""

    def test_none_path(self):
        """Test that None returns None."""
        from src.utils import normalize_path
        expect(normalize_path(None)).to_be_none()

    def test_forward_slashes_unchanged(self):
        """Test that forward slashes are unchanged."""
        from src.utils import normalize_path
        result = normalize_path("/path/to/file.bx")
        expect(result).to_be("/path/to/file.bx")

    def test_backslashes_converted(self):
        """Test that backslashes are converted to forward slashes."""
        from src.utils import normalize_path
        result = normalize_path("C:\\path\\to\\file.bx")
        expect(result).to_contain_string("/")
        expect(result).not_to_contain("\\")

    def test_trailing_slash_removed(self):
        """Test that trailing slash is removed."""
        from src.utils import normalize_path
        result = normalize_path("/path/to/dir/")
        expect(result).to_end_with("dir")
        expect(result).not_to_end_with("/")


class TestNormalizeMapping:
    """Tests for utils.normalize_mapping."""

    def test_normalize_mapping_path(self):
        """Test mapping path normalization."""
        from src.utils import normalize_mapping
        mapping = {"path": "/some/path", "mapping": "/model"}
        result = normalize_mapping(mapping, "/project")
        expect(result["path"]).to_be("/some/path")
        expect(result["mapping"]).to_be("/model")

    def test_normalize_mapping_adds_leading_slash(self):
        """Test that mapping without leading slash gets one."""
        from src.utils import normalize_mapping
        mapping = {"path": "/some/path", "mapping": "model"}
        result = normalize_mapping(mapping, "/project")
        expect(result["mapping"]).to_start_with("/")


class TestGetPreviousCharacter:
    """Tests for utils.get_previous_character."""

    def test_previous_character_position(self):
        """Test getting previous character position."""
        from src.utils import get_previous_character
        mock_view = MagicMock()
        mock_view.substr = MagicMock(return_value=" ")  # whitespace triggers find_by_class
        mock_view.find_by_class = MagicMock(return_value=5)

        result = get_previous_character(mock_view, 10)
        # whitespace triggers find_by_class which returns 5, then we subtract 1
        expect(result).to_be(4)


class TestGetScopeRegionContainingPoint:
    """Tests for utils.get_scope_region_containing_point."""

    def test_scope_not_found(self):
        """Test when scope is not found."""
        from src.utils import get_scope_region_containing_point
        mock_view = MagicMock()
        mock_view.scope_name = MagicMock(return_value="source.boxlang.script")
        mock_view.find_by_selector = MagicMock(return_value=[])

        result = get_scope_region_containing_point(mock_view, 0, "entity.name.function")
        expect(result).to_be_none()


class TestGetDotContext:
    """Tests for utils.get_dot_context."""

    def test_empty_context_when_not_dot(self):
        """Test empty context when position is not on a dot."""
        from src.utils import get_dot_context
        mock_view = MagicMock()
        mock_view.substr = MagicMock(return_value="x")

        result = get_dot_context(mock_view, 0)
        expect(result).to_be_empty()

    def test_context_on_dot(self):
        """Test context extraction on a dot."""
        from src.utils import get_dot_context
        mock_view = MagicMock()
        mock_view.substr = MagicMock(side_effect=lambda pos: "." if pos == 0 else "x")
        mock_view.scope_name = MagicMock(return_value="source.boxlang.script")
        mock_view.match_selector = MagicMock(return_value=False)

        result = get_dot_context(mock_view, 0)
        expect(result).to_be_a(list)


class TestGetTagAttribute:
    """Tests for tag-related utilities."""

    def test_get_tag_attribute_name(self):
        """Test tag attribute name extraction."""
        from src.utils import get_tag_attribute_name
        mock_view = MagicMock()
        mock_view.match_selector = MagicMock(return_value=True)
        mock_view.word = MagicMock()
        mock_view.word.return_value = MagicMock()
        mock_view.substr = MagicMock(return_value="name")

        result = get_tag_attribute_name(mock_view, 0)
        expect(result).to_be("name")


class TestGetFunction:
    """Tests for function-related utilities."""

    def test_get_function_not_in_function(self):
        """Test when not inside a function."""
        from src.utils import get_function
        mock_view = MagicMock()
        mock_view.match_selector = MagicMock(return_value=False)
        mock_view.scope_name = MagicMock(return_value="source.boxlang.script")

        result = get_function(mock_view, 0)
        expect(result).to_be_none()


class TestFindVariableAssignment:
    """Tests for utils.find_variable_assignment."""

    def test_no_assignment_found(self):
        """Test when no assignment is found."""
        from src.utils import find_variable_assignment
        mock_view = MagicMock()
        mock_view.find_all = MagicMock(return_value=[])

        result = find_variable_assignment(mock_view, 100, "myVar")
        expect(result).to_be_none()


class TestGetVerifiedPath:
    """Tests for utils.get_verified_path."""

    def test_nonexistent_root(self):
        """Test with nonexistent root path."""
        from src.utils import get_verified_path
        rel_path, exists = get_verified_path("/nonexistent/root", "some/path")
        expect(exists).to_be_false()


class TestGetSetting:
    """Tests for utils.get_setting."""

    def test_get_setting(self, mock_sublime_settings):
        """Test getting a setting."""
        mock_sublime_settings["boxlang_bif_completions"] = "full"
        from src.utils import get_setting
        result = get_setting("boxlang_bif_completions")
        expect(result).to_be("full")

    def test_get_setting_missing(self, mock_sublime_settings):
        """Test getting a missing setting."""
        from src.utils import get_setting
        result = get_setting("nonexistent_setting")
        expect(result).to_be_none()
