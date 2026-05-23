"""
Integration tests for the component indexing system.
"""

import pytest
from tests.expectations import expect
from unittest.mock import MagicMock, patch


class TestComponentIndex:
    """Tests for component_index module."""

    def test_get_indexed_metadata_no_project(self):
        """Test getting metadata for non-existent project."""
        from src.component_index import get_indexed_metadata
        result = get_indexed_metadata("nonexistent", "some.path")
        expect(result).to_be_none()

    def test_get_all_indexed_no_project(self):
        """Test getting all indexed for non-existent project."""
        from src.component_index import get_all_indexed
        result = get_all_indexed("nonexistent")
        expect(result).to_be_empty()

    def test_get_dot_paths_no_project(self):
        """Test getting dot paths for non-existent project."""
        from src.component_index import get_dot_paths
        result = get_dot_paths("nonexistent")
        expect(result).to_be_empty()

    def test_get_completions_by_dot_path_no_project(self):
        """Test getting completions for non-existent project."""
        from src.component_index import get_completions_by_dot_path
        result = get_completions_by_dot_path("nonexistent", "some.path")
        expect(result).to_be_none()

    def test_get_completions_by_file_path_no_project(self):
        """Test getting completions by file path for non-existent project."""
        from src.component_index import get_completions_by_file_path
        result = get_completions_by_file_path("nonexistent", "/path/to/file.bx")
        expect(result).to_be_empty()


class TestComponentIndexResolvePath:
    """Tests for component_index.resolve_path."""

    def test_resolve_path_no_project_data(self):
        """Test resolve_path with no project data."""
        from src.component_index import resolve_path
        result = resolve_path("nonexistent", None, "model.UserService")
        expect(result).to_be_none()

    def test_resolve_path_no_mappings(self, mock_sublime):
        """Test resolve_path with no mappings."""
        from src.component_index import resolve_path
        mock_window = MagicMock()
        mock_window.project_file_name = MagicMock(return_value="test.sublime-project")
        mock_window.project_data = MagicMock(return_value={"folders": []})
        mock_sublime.windows = MagicMock(return_value=[mock_window])

        result = resolve_path("/path/to/test.sublime-project", None, "model.UserService")
        expect(result).to_be_none()


class TestComponentIndexExtendMetadata:
    """Tests for component index metadata extension."""

    def test_extend_metadata_no_extends(self):
        """Test extending metadata without extends."""
        from src.component_index import _extend_metadata
        metadata = {
            "name": "UserService",
            "functions": {"find": {"name": "find"}},
            "properties": {}
        }
        result = _extend_metadata(metadata, "test_project")
        expect(result["functions"]).to_have_key("find")

    def test_extend_metadata_with_extends(self, mock_sublime):
        """Test extending metadata with parent class."""
        from src.component_index import _extend_metadata, project_indexes

        # Set up parent in index
        project_indexes["test_project"] = {
            "model.BaseService": {
                "name": "BaseService",
                "functions": {"baseMethod": {"name": "baseMethod"}},
                "properties": {}
            }
        }

        mock_window = MagicMock()
        mock_window.project_file_name = MagicMock(return_value="test.sublime-project")
        mock_window.project_data = MagicMock(return_value={
            "mappings": [{"path": "/project", "mapping": "/"}]
        })
        mock_sublime.windows = MagicMock(return_value=[mock_window])

        metadata = {
            "name": "UserService",
            "extends": "model.BaseService",
            "functions": {"find": {"name": "find"}},
            "properties": {}
        }
        result = _extend_metadata(metadata, "test_project")
        # Child functions should be present
        expect(result["functions"]).to_have_key("find")


class TestComponentIndexBuildCompletions:
    """Tests for _build_completions."""

    def test_build_completions_with_functions(self):
        """Test building completions from functions."""
        from src.component_index import _build_completions
        metadata = {
            "functions": {
                "find": {
                    "name": "find",
                    "args": [
                        {"name": "criteria", "required": True},
                        {"name": "maxRows", "required": False}
                    ],
                    "return_type": "query",
                    "access": "public"
                }
            }
        }
        result = _build_completions(metadata, "model.UserService")
        expect(result["functions"]).to_have_length(1)
        expect(result["functions"][0]["key"]).to_be("find")
        expect(result["dot_path"]).to_be("model.UserService")

    def test_build_completions_with_init(self):
        """Test building constructor completion from init function."""
        from src.component_index import _build_completions
        metadata = {
            "functions": {
                "init": {
                    "name": "init",
                    "args": [{"name": "config", "required": True}],
                    "return_type": "void",
                    "access": "public"
                }
            }
        }
        result = _build_completions(metadata, "model.Config")
        expect(result["constructor"]).not_to_be_none()

    def test_build_completions_empty(self):
        """Test building completions from empty metadata."""
        from src.component_index import _build_completions
        metadata = {"functions": {}, "properties": {}}
        result = _build_completions(metadata, "Empty")
        expect(result["functions"]).to_be_empty()
        expect(result["constructor"]).to_be_none()


class TestComponentIndexCommand:
    """Tests for BoxlangIndexProjectCommand."""

    def test_index_command_no_project(self, mock_sublime):
        """Test index command with no project."""
        from src.component_index import BoxlangIndexProjectCommand
        mock_window = MagicMock()
        mock_window.project_file_name = MagicMock(return_value=None)
        cmd = BoxlangIndexProjectCommand()
        cmd.window = mock_window
        # Should not crash
        cmd.run()
