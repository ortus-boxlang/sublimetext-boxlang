"""
Unit tests for the AST parser (component_parser/ast_parser.py).
"""

import pytest
from tests.expectations import expect


class TestASTParserExtractMetadata:
    """Tests for ASTParser._extract_metadata."""

    def test_extract_class_name(self, sample_class_ast):
        """Test that class name is extracted correctly."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata(sample_class_ast)
        expect(metadata["name"]).to_be("UserService")

    def test_extract_extends(self, sample_class_ast):
        """Test that extends clause is extracted."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata(sample_class_ast)
        expect(metadata["extends"]).to_be("BaseService")

    def test_extract_implements(self, sample_class_ast):
        """Test that implements clause is extracted."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata(sample_class_ast)
        expect(metadata["implements"]).to_contain("IUserService")

    def test_extract_multiple_implements(self):
        """Test comma-separated implements are split."""
        from src.component_parser.ast_parser import ASTParser
        ast = {
            "statements": [
                {"ASTType": "BoxExpressionStatement", "expression": {"ASTType": "BoxIdentifier", "name": "class"}},
                {"ASTType": "BoxExpressionStatement", "expression": {"ASTType": "BoxIdentifier", "name": "MyClass"}},
                {
                    "ASTType": "BoxExpressionStatement",
                    "expression": {
                        "ASTType": "BoxAssignment",
                        "left": {"name": "implements"},
                        "right": {"ASTType": "BoxStringLiteral", "value": "IFoo,IBar,IBaz"}
                    }
                },
                {"ASTType": "BoxStatementBlock", "body": []}
            ]
        }
        metadata = ASTParser._extract_metadata(ast)
        expect(metadata["implements"]).to_have_length(3)
        expect(metadata["implements"]).to_contain("IFoo")
        expect(metadata["implements"]).to_contain("IBar")
        expect(metadata["implements"]).to_contain("IBaz")

    def test_no_extends(self, sample_class_ast_no_extends):
        """Test class without extends returns None."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata(sample_class_ast_no_extends)
        expect(metadata["extends"]).to_be_none()
        expect(metadata["implements"]).to_be_empty()

    def test_extract_functions(self, sample_class_ast):
        """Test that functions are extracted from class body."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata(sample_class_ast)
        expect(metadata["functions"]).to_have_length(3)
        expect(metadata["functions"]).to_have_key("init")
        expect(metadata["functions"]).to_have_key("find")
        expect(metadata["functions"]).to_have_key("_privateMethod")

    def test_extract_function_details(self, sample_class_ast):
        """Test function metadata extraction."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata(sample_class_ast)
        func = metadata["functions"]["find"]

        expect(func["name"]).to_be("find")
        expect(func["return_type"]).to_be("query")
        expect(func["access"]).to_be("public")
        expect(func["args"]).to_have_length(2)
        expect(func["args"][0]["name"]).to_be("criteria")
        expect(func["args"][0]["required"]).to_be_true()
        expect(func["args"][1]["name"]).to_be("maxRows")
        expect(func["args"][1]["required"]).to_be_false()
        expect(func["annotations"]).to_contain("cached")
        expect(func["line"]).to_be(7)

    def test_extract_properties(self, sample_class_ast_with_properties):
        """Test that properties are extracted."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata(sample_class_ast_with_properties)
        expect(metadata["properties"]).to_have_length(2)
        expect(metadata["properties"]).to_have_key("name")
        expect(metadata["properties"]).to_have_key("timeout")

    def test_extract_property_details(self, sample_class_ast_with_properties):
        """Test property metadata extraction."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata(sample_class_ast_with_properties)
        prop = metadata["properties"]["name"]

        expect(prop["name"]).to_be("name")
        expect(prop["type"]["sourceText"]).to_be("string")
        expect(prop["access"]).to_be("public")
        expect(prop["line"]).to_be(2)

    def test_extract_annotations(self, sample_ast_with_annotations):
        """Test that doc comment annotations are extracted."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata(sample_ast_with_annotations)
        expect(metadata["annotations"]).to_have_length(2)
        expect(metadata["annotations"][0]["key"]).to_be("displayName")
        expect(metadata["annotations"][0]["value"]).to_be("User Service")
        expect(metadata["annotations"][1]["key"]).to_be("singleton")
        expect(metadata["annotations"][1]["value"]).to_be("true")

    def test_empty_statements(self):
        """Test handling of empty statements list."""
        from src.component_parser.ast_parser import ASTParser
        metadata = ASTParser._extract_metadata({"statements": []})
        expect(metadata["name"]).to_be_none()
        expect(metadata["functions"]).to_be_empty()
        expect(metadata["properties"]).to_be_empty()

    def test_no_class_declaration(self):
        """Test AST without class declaration."""
        from src.component_parser.ast_parser import ASTParser
        ast = {
            "statements": [
                {
                    "ASTType": "BoxFunctionDeclaration",
                    "name": "standalone",
                    "type": {},
                    "accessModifier": {},
                    "args": [],
                    "annotations": [],
                    "position": {"start": {"line": 1}}
                }
            ]
        }
        metadata = ASTParser._extract_metadata(ast)
        expect(metadata["name"]).to_be_none()
        expect(metadata["functions"]).to_be_empty()


class TestASTParserExtractFunction:
    """Tests for ASTParser._extract_function."""

    def test_function_with_no_args(self):
        """Test function with empty args."""
        from src.component_parser.ast_parser import ASTParser
        node = {
            "name": "init",
            "type": {"sourceText": "void"},
            "accessModifier": {"sourceText": "public"},
            "args": [],
            "annotations": [],
            "position": {"start": {"line": 1}}
        }
        result = ASTParser._extract_function(node)
        expect(result["name"]).to_be("init")
        expect(result["args"]).to_be_empty()
        expect(result["return_type"]).to_be("void")

    def test_function_with_nested_type(self):
        """Test function with nested type node."""
        from src.component_parser.ast_parser import ASTParser
        node = {
            "name": "get",
            "type": {"type": {"sourceText": "array"}},
            "accessModifier": {"sourceText": "remote"},
            "args": [],
            "annotations": [],
            "position": {"start": {"line": 5}}
        }
        result = ASTParser._extract_function(node)
        expect(result["return_type"]).to_be("array")

    def test_function_access_modifier_case(self):
        """Test access modifier is lowercased."""
        from src.component_parser.ast_parser import ASTParser
        node = {
            "name": "test",
            "type": {},
            "accessModifier": {"sourceText": "REMOTE"},
            "args": [],
            "annotations": [],
            "position": {"start": {"line": 1}}
        }
        result = ASTParser._extract_function(node)
        expect(result["access"]).to_be("remote")

    def test_function_unknown_name(self):
        """Test function with missing name defaults to 'unknown'."""
        from src.component_parser.ast_parser import ASTParser
        node = {
            "type": {},
            "accessModifier": {},
            "args": [],
            "annotations": [],
            "position": {"start": {"line": 1}}
        }
        result = ASTParser._extract_function(node)
        expect(result["name"]).to_be("unknown")


class TestASTParserExtractProperty:
    """Tests for ASTParser._extract_property."""

    def test_property_basic(self):
        """Test basic property extraction."""
        from src.component_parser.ast_parser import ASTParser
        node = {
            "name": "title",
            "type": {"sourceText": "string"},
            "accessModifier": {"sourceText": "public"},
            "value": {"ASTType": "BoxStringLiteral", "value": "Hello"},
            "position": {"start": {"line": 3}}
        }
        result = ASTParser._extract_property(node)
        expect(result["name"]).to_be("title")
        expect(result["access"]).to_be("public")
        expect(result["line"]).to_be(3)

    def test_property_unknown_name(self):
        """Test property with missing name defaults to 'unknown'."""
        from src.component_parser.ast_parser import ASTParser
        node = {
            "type": {},
            "accessModifier": {},
            "value": None,
            "position": {"start": {"line": 1}}
        }
        result = ASTParser._extract_property(node)
        expect(result["name"]).to_be("unknown")


class TestASTParserParseString:
    """Tests for ASTParser.parse_string (requires CLI mocking)."""

    def test_parse_string_error(self, mocker):
        """Test parse_string handles CLI errors."""
        mocker.patch("src.component_parser.ast_parser.boxlang_cli.run_ast_code",
                     return_value=(None, "AST parse error"))
        from src.component_parser.ast_parser import ASTParser
        result = ASTParser.parse_string("invalid code")
        expect(result["parse_errors"]).to_contain("AST parse error")
        expect(result["name"]).to_be_none()
