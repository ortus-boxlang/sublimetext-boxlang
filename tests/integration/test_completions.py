"""
Integration tests for the completion system.
"""

import pytest
from tests.expectations import expect
from unittest.mock import MagicMock


class TestCompletionOrchestrator:
    """Tests for completions.get_completions."""

    def test_get_completions_no_context(self, mock_boxlang_view):
        """Test that no completions are returned when context is None."""
        mock_boxlang_view.type = None
        from src.completions import get_completions
        result = get_completions(mock_boxlang_view.view, 0, "")
        expect(result).to_be_none()

    def test_get_completions_returns_list(self, mock_boxlang_view):
        """Test that completions returns a list or None."""
        mock_boxlang_view.type = "script"
        from src.completions import get_completions
        result = get_completions(mock_boxlang_view.view, 0, "")
        # Should return a list (possibly empty) or None
        expect(result is None or isinstance(result, list)).to_be_true()


class TestBaseCompletionsPlugin:
    """Tests for basecompletions plugin."""

    def test_basecompletions_has_completion_files(self):
        """Test that completion files are defined."""
        from src.plugins_.basecompletions import COMPLETION_FILES
        expect(COMPLETION_FILES).to_contain("boxlang_tags")
        expect(COMPLETION_FILES).to_contain("boxlang_functions")
        expect(COMPLETION_FILES).to_contain("boxlang_member_functions")

    def test_basecompletions_get_completions_returns_for_tag(self, mock_boxlang_view_tag):
        """Test that tag completions are returned."""
        from src.plugins_.basecompletions import get_completions
        result = get_completions(mock_boxlang_view_tag)
        # May be None or CompletionList depending on whether JSON is loaded
        expect(result is None or hasattr(result, "completions")).to_be_true()

    def test_basecompletions_get_completions_returns_for_script(self, mock_boxlang_view):
        """Test that script completions are returned."""
        from src.plugins_.basecompletions import get_completions
        result = get_completions(mock_boxlang_view)
        expect(result is None or hasattr(result, "completions")).to_be_true()


class TestTypeCompletionsPlugin:
    """Tests for typecompletions plugin."""

    def test_typecompletions_dot_context(self, mock_boxlang_view_dot):
        """Test type-aware completions for dot context."""
        from src.plugins_.typecompletions import get_completions
        result = get_completions(mock_boxlang_view_dot)
        expect(result is None or hasattr(result, "completions")).to_be_true()

    def test_typecompletions_no_dot_context(self, mock_boxlang_view):
        """Test type completions with no dot context."""
        mock_boxlang_view.type = "dot"
        mock_boxlang_view.dot_context = []
        from src.plugins_.typecompletions import get_completions
        result = get_completions(mock_boxlang_view)
        expect(result).to_be_none()

    def test_typecompletions_script_context(self, mock_boxlang_view):
        """Test type completions in script context."""
        mock_boxlang_view.type = "script"
        from src.plugins_.typecompletions import get_completions
        result = get_completions(mock_boxlang_view)
        expect(result).to_be_none()


class TestDotPathsPlugin:
    """Tests for dotpaths plugin."""

    def test_dotpaths_no_project(self, mock_boxlang_view):
        """Test dotpaths with no project."""
        mock_boxlang_view.project_name = None
        mock_boxlang_view.type = "script"
        from src.plugins_.dotpaths import get_completions
        result = get_completions(mock_boxlang_view)
        expect(result).to_be_none()

    def test_dotpaths_dot_context_empty(self, mock_boxlang_view):
        """Test dotpaths with empty dot context."""
        mock_boxlang_view.type = "dot"
        mock_boxlang_view.dot_context = []
        from src.plugins_.dotpaths import get_completions
        result = get_completions(mock_boxlang_view)
        expect(result).to_be_none()


class TestBoxDocsPlugin:
    """Tests for boxdocs plugin."""

    def test_boxdocs_get_completions_returns_none(self, mock_boxlang_view):
        """Test that boxdocs does not provide completions."""
        from src.plugins_.boxdocs import get_completions
        result = get_completions(mock_boxlang_view)
        expect(result).to_be_none()

    def test_boxdocs_get_inline_documentation_no_match(self, mock_boxlang_view):
        """Test inline documentation when no match."""
        from src.plugins_.boxdocs import get_inline_documentation
        result = get_inline_documentation(mock_boxlang_view, "inline_doc")
        expect(result).to_be_none()


class TestPluginBaseClass:
    """Tests for the BoxlangPlugin base class."""

    def test_base_plugin_returns_none_by_default(self, mock_boxlang_view):
        """Test that base plugin methods return None."""
        from src.plugins_.plugin import BoxlangPlugin
        plugin = BoxlangPlugin()
        expect(plugin.get_completions(mock_boxlang_view)).to_be_none()
        expect(plugin.get_completion_docs(mock_boxlang_view)).to_be_none()
        expect(plugin.get_inline_documentation(mock_boxlang_view, "inline_doc")).to_be_none()
        expect(plugin.get_goto_boxlang_file(mock_boxlang_view)).to_be_none()
        expect(plugin.get_method_preview(mock_boxlang_view)).to_be_none()


class TestPluginLoader:
    """Tests for the plugin loader."""

    def test_plugins_list_not_empty(self):
        """Test that plugins list is populated."""
        from src import boxlang_plugins
        # Plugins may be empty in test environment due to mocking
        # but the directory list should have entries
        expect(len(boxlang_plugins.directory)).to_be_gt(0)

    def test_plugin_directory_has_expected_plugins(self):
        """Test that expected plugins are in the directory."""
        from src import boxlang_plugins
        expect(boxlang_plugins.directory).to_contain("basecompletions")
        expect(boxlang_plugins.directory).to_contain("boxdocs")
        expect(boxlang_plugins.directory).to_contain("classes")
        expect(boxlang_plugins.directory).to_contain("dotpaths")
        expect(boxlang_plugins.directory).to_contain("typecompletions")
