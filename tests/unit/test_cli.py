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


class TestBoxlangCLIDecodeOutput:
    """Tests for subprocess output decoding."""

    def test_decode_output_falls_back_to_windows_encoding(self):
        """Test decoding output containing CP-1252 bytes."""
        from src.boxlang_cli import _decode_output
        result = _decode_output(b"Ortus\x99 BoxLang v1.13.0+54")
        expect(result).to_be("Ortus\u2122 BoxLang v1.13.0+54")


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


CDS_WARNING = "[0.001s][warning][cds] The shared archive file version 0x12 does not match the required version 0x13."


class TestJvmNoiseTolerance:
    """The JVM can print warnings ahead of BoxLang's own output."""

    def test_version_ignores_jvm_warning_line(self):
        from src import boxlang_cli
        output = CDS_WARNING + "\nBoxLang 1.18.0+1 (Build: 20261002)\n"
        expect(boxlang_cli._find_version(output)).to_be("1.18.0+1")

    def test_version_with_warning_after_version_line(self):
        from src import boxlang_cli
        expect(boxlang_cli._find_version("BoxLang v1.17.6+3\n" + CDS_WARNING)).to_be("1.17.6+3")

    def test_version_falls_back_to_first_real_line(self):
        from src import boxlang_cli
        expect(boxlang_cli._find_version(CDS_WARNING + "\nsomething unexpected\n")).to_be("something unexpected")

    def test_version_empty_output(self):
        from src import boxlang_cli
        expect(boxlang_cli._find_version("")).to_be("")
        expect(boxlang_cli._find_version(CDS_WARNING)).to_be("")

    def test_detection_survives_warning(self):
        from src import boxlang_cli
        with patch.object(boxlang_cli, "_run_command", return_value=(0, CDS_WARNING + "\nBoxLang 1.18.0+1\n", "")):
            boxlang_cli._detect_boxlang()
        expect(boxlang_cli.get_version()).to_be("1.18.0+1")
        expect(boxlang_cli.supports_check()).to_be_true()

    def test_extract_json_skips_leading_bracket_noise(self):
        from src import boxlang_cli
        text = CDS_WARNING + '\n[ {\n  "file" : "a.bx",\n  "valid" : true,\n  "issues" : [ ]\n} ]\n'
        data = boxlang_cli.extract_json(text)
        expect(data[0]["file"]).to_be("a.bx")

    def test_extract_json_object_and_none(self):
        from src import boxlang_cli
        expect(boxlang_cli.extract_json("warning line\n{\"a\": 1}")).to_be({"a": 1})
        expect(boxlang_cli.extract_json(CDS_WARNING)).to_be_none()
        expect(boxlang_cli.extract_json("")).to_be_none()

    def test_check_output_with_warning_prefix(self):
        from src import boxlang_cli
        text = CDS_WARNING + '\n[{"file": "bad.bxs", "valid": false, "issues": [{"message": "m", "line": 1, "column": 3}]}]'
        records = boxlang_cli.parse_check_output(text)
        expect(records[0]["issues"][0]["line"]).to_be(1)

    def test_run_check_with_warning_prefix(self):
        from src import boxlang_cli
        out = CDS_WARNING + '\n[{"file": "bad.bxs", "valid": false, "issues": [{"message": "m", "line": 2, "column": 1}]}]'
        with patch.object(boxlang_cli, "_run_command", return_value=(1, out, "")):
            issues, error = boxlang_cli.run_check("/p/bad.bxs")
        expect(error).to_be_none()
        expect(issues[0]["line"]).to_be(2)

    def test_run_ast_with_warning_prefix(self):
        from src import boxlang_cli
        out = CDS_WARNING + '\n{"statements": []}'
        with patch.object(boxlang_cli, "_run_command", return_value=(0, out, "")):
            ast, error = boxlang_cli.run_ast("/p/a.bx")
        expect(error).to_be_none()
        expect(ast).to_be({"statements": []})

    def test_run_ast_without_json_is_an_error(self):
        from src import boxlang_cli
        with patch.object(boxlang_cli, "_run_command", return_value=(0, CDS_WARNING, "")):
            ast, error = boxlang_cli.run_ast("/p/a.bx")
        expect(ast).to_be_none()
        expect(error).to_contain("Invalid JSON")
