"""
Unit tests for the Parser Router (component_parser/__init__.py).
"""

import pytest
from tests.expectations import expect


class TestParserRouter:
    """Tests for parse_file routing."""

    def test_routes_bx_to_ast_parser(self, mocker):
        """Test that .bx files route to AST parser."""
        mock_parse = mocker.patch("src.component_parser.ast_parser.ASTParser.parse",
                                  return_value={"name": "Test"})
        from src.component_parser import parse_file
        parse_file("/path/to/file.bx")
        mock_parse.assert_called_once_with("/path/to/file.bx")

    def test_routes_bxs_to_ast_parser(self, mocker):
        """Test that .bxs files route to AST parser."""
        mock_parse = mocker.patch("src.component_parser.ast_parser.ASTParser.parse",
                                  return_value={"name": "Test"})
        from src.component_parser import parse_file
        parse_file("/path/to/file.bxs")
        mock_parse.assert_called_once_with("/path/to/file.bxs")

    def test_routes_bxm_to_tag_parser(self, mocker):
        """Test that .bxm files route to Tag parser."""
        mock_parse = mocker.patch("src.component_parser.tag_parser.TagParser.parse",
                                  return_value={"name": "Test"})
        from src.component_parser import parse_file
        parse_file("/path/to/file.bxm")
        mock_parse.assert_called_once_with("/path/to/file.bxm")

    def test_unsupported_extension(self):
        """Test that unsupported extensions return error."""
        from src.component_parser import parse_file
        result = parse_file("/path/to/file.cfc")
        expect(result["parse_errors"]).not_to_be_empty()
        expect(result["parse_errors"][0]).to_contain_string("Unsupported file extension")

    def test_case_insensitive_extension(self, mocker):
        """Test that extension matching is case insensitive."""
        mock_parse = mocker.patch("src.component_parser.ast_parser.ASTParser.parse",
                                  return_value={"name": "Test"})
        from src.component_parser import parse_file
        parse_file("/path/to/file.BX")
        mock_parse.assert_called_once()


class TestParserRouterParseString:
    """Tests for parse_string routing."""

    def test_parse_string_bx_type(self, mocker):
        """Test parse_string with bx type routes to AST parser."""
        mock_parse = mocker.patch("src.component_parser.ast_parser.ASTParser.parse_string",
                                  return_value={"name": "Test"})
        from src.component_parser import parse_string
        parse_string("class Test {}", "bx")
        mock_parse.assert_called_once_with("class Test {}")

    def test_parse_string_bxs_type(self, mocker):
        """Test parse_string with bxs type routes to AST parser."""
        mock_parse = mocker.patch("src.component_parser.ast_parser.ASTParser.parse_string",
                                  return_value={"name": "Test"})
        from src.component_parser import parse_string
        parse_string("class Test {}", "bxs")
        mock_parse.assert_called_once_with("class Test {}")

    def test_parse_string_bxm_type(self, mocker):
        """Test parse_string with bxm type routes to Tag parser."""
        mock_parse = mocker.patch("src.component_parser.tag_parser.TagParser.parse_string",
                                  return_value={"name": "Test"})
        from src.component_parser import parse_string
        parse_string("<bx:function name='test' />", "bxm")
        mock_parse.assert_called_once_with("<bx:function name='test' />")

    def test_parse_string_unsupported_type(self):
        """Test parse_string with unsupported type."""
        from src.component_parser import parse_string
        result = parse_string("test", "cfc")
        expect(result["parse_errors"]).not_to_be_empty()
        expect(result["parse_errors"][0]).to_contain_string("Unsupported file type")
