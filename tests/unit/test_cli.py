"""
Unit tests for the CLI wrapper (boxlang_cli.py).
"""

import pytest
from tests.expectations import expect
from unittest.mock import MagicMock, patch
import subprocess


class TestBoxlangCLIDetection:
    """Tests for BoxLang CLI detection."""

    def test_detection_complete_callback(self, mocker):
        """Test that detection callbacks are called."""
        from src import boxlang_cli
        callback = MagicMock()
        boxlang_cli.on_detection_complete(callback)
        # Since detection runs async, we test the callback mechanism directly
        boxlang_cli._detection_complete = True
        boxlang_cli._boxlang_installed = True
        boxlang_cli._boxlang_version = "1.13.0+54"
        boxlang_cli.on_detection_complete(callback)
        callback.assert_called_once()

    def test_is_installed(self, mocker):
        """Test is_installed returns correct state."""
        from src import boxlang_cli
        boxlang_cli._boxlang_installed = True
        expect(boxlang_cli.is_installed()).to_be_true()
        boxlang_cli._boxlang_installed = False
        expect(boxlang_cli.is_installed()).to_be_false()

    def test_get_version(self, mocker):
        """Test get_version returns correct version."""
        from src import boxlang_cli
        boxlang_cli._boxlang_version = "1.13.0+54"
        expect(boxlang_cli.get_version()).to_be("1.13.0+54")

    def test_get_executable(self, mocker):
        """Test get_executable returns default."""
        from src import boxlang_cli
        expect(boxlang_cli.get_executable()).to_be("boxlang")


class TestBoxlangCLIParseVersion:
    """Tests for version parsing."""

    def test_parse_version_standard(self):
        """Test parsing standard version string."""
        from src.boxlang_cli import _parse_version
        result = _parse_version("Ortus BoxLang v1.13.0+54")
        expect(result).to_be("1.13.0+54")

    def test_parse_version_without_v(self):
        """Test parsing version without v prefix."""
        from src.boxlang_cli import _parse_version
        result = _parse_version("Ortus BoxLang 1.13.0+54")
        expect(result).to_be("1.13.0+54")

    def test_parse_version_only(self):
        """Test parsing version-only string."""
        from src.boxlang_cli import _parse_version
        result = _parse_version("1.13.0+54")
        expect(result).to_be("1.13.0+54")

    def test_parse_version_no_match(self):
        """Test parsing when no version found."""
        from src.boxlang_cli import _parse_version
        result = _parse_version("BoxLang not found")
        expect(result).to_be_none()


class TestBoxlangCLIRunAST:
    """Tests for run_ast function."""

    def test_run_ast_success(self, mocker):
        """Test successful AST parsing."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(0, '{"statements": []}', ""))

        from src import boxlang_cli
        ast, error = boxlang_cli.run_ast("/path/to/file.bx")
        expect(ast).to_be_a(dict)
        expect(ast).to_have_key("statements")
        expect(error).to_be_none()

    def test_run_ast_cli_error(self, mocker):
        """Test CLI error handling."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(1, "", "File not found"))

        from src import boxlang_cli
        ast, error = boxlang_cli.run_ast("/path/to/nonexistent.bx")
        expect(ast).to_be_none()
        expect(error).to_be("File not found")

    def test_run_ast_timeout(self, mocker):
        """Test timeout handling."""
        mocker.patch("src.boxlang_cli._run_command", side_effect=subprocess.TimeoutExpired("cmd", 30))

        from src import boxlang_cli
        ast, error = boxlang_cli.run_ast("/path/to/file.bx")
        expect(ast).to_be_none()
        expect(error).to_be("BoxLang AST parsing timed out")

    def test_run_ast_invalid_json(self, mocker):
        """Test invalid JSON handling."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(0, "not valid json", ""))

        from src import boxlang_cli
        ast, error = boxlang_cli.run_ast("/path/to/file.bx")
        expect(ast).to_be_none()
        expect(error).to_start_with("Invalid JSON from BoxLang AST")

    def test_run_ast_callback(self, mocker):
        """Test async callback execution."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(0, '{"statements": []}', ""))

        from src import boxlang_cli
        callback = MagicMock()
        boxlang_cli.run_ast("/path/to/file.bx", callback=callback)

        # Wait for thread to complete
        import time
        time.sleep(0.5)
        callback.assert_called_once()


class TestBoxlangCLIRunASTCode:
    """Tests for run_ast_code function."""

    def test_run_ast_code_success(self, mocker):
        """Test successful AST parsing from code string."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(0, '{"statements": []}', ""))

        from src import boxlang_cli
        ast, error = boxlang_cli.run_ast_code("class Test {}")
        expect(ast).to_be_a(dict)
        expect(error).to_be_none()

    def test_run_ast_code_error(self, mocker):
        """Test error handling for code string."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(1, "", "Syntax error"))

        from src import boxlang_cli
        ast, error = boxlang_cli.run_ast_code("invalid code")
        expect(ast).to_be_none()
        expect(error).to_be("Syntax error")


class TestBoxlangCLIRunFormat:
    """Tests for run_format function."""

    def test_run_format_success(self, mocker):
        """Test successful formatting."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(0, "", ""))

        from src import boxlang_cli
        success, error = boxlang_cli.run_format("/path/to/file.bx")
        expect(success).to_be_true()
        expect(error).to_be_none()

    def test_run_format_error(self, mocker):
        """Test format error handling."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(1, "", "Format error"))

        from src import boxlang_cli
        success, error = boxlang_cli.run_format("/path/to/file.bx")
        expect(success).to_be_false()
        expect(error).to_be("Format error")


class TestBoxlangCLIRunCompile:
    """Tests for run_compile function."""

    def test_run_compile_success(self, mocker):
        """Test successful compilation."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(0, "", ""))

        from src import boxlang_cli
        success, error = boxlang_cli.run_compile("/src", "/bin")
        expect(success).to_be_true()
        expect(error).to_be_none()

    def test_run_compile_error(self, mocker):
        """Test compile error handling."""
        mocker.patch("src.boxlang_cli._run_command", return_value=(1, "", "Compile error"))

        from src import boxlang_cli
        success, error = boxlang_cli.run_compile("/src", "/bin")
        expect(success).to_be_false()
        expect(error).to_be("Compile error")
