"""
Unit tests for the Tag parser (component_parser/tag_parser.py).
"""

import pytest
from tests.expectations import expect


class TestTagParserExtractTags:
    """Tests for TagParser._extract_tags."""

    def test_extract_self_closing_tag(self):
        """Test extraction of known self-closing tags."""
        from src.component_parser.tag_parser import TagParser
        content = "<bx:abort />"
        tags = TagParser._extract_tags(content)
        expect(tags).to_have_length(1)
        expect(tags[0]["name"]).to_be("abort")
        expect(tags[0]["body"]).to_be_none()

    def test_extract_self_closing_no_slash(self):
        """Test self-closing tag without explicit />."""
        from src.component_parser.tag_parser import TagParser
        content = "<bx:abort>"
        tags = TagParser._extract_tags(content)
        expect(tags).to_have_length(1)
        expect(tags[0]["name"]).to_be("abort")
        expect(tags[0]["body"]).to_be_none()

    def test_extract_tag_with_body(self):
        """Test extraction of tag with body."""
        from src.component_parser.tag_parser import TagParser
        content = "<bx:output>Hello World</bx:output>"
        tags = TagParser._extract_tags(content)
        expect(tags).to_have_length(1)
        expect(tags[0]["name"]).to_be("output")
        expect(tags[0]["body"]).to_be("Hello World")

    def test_extract_tag_with_attributes(self):
        """Test extraction of tag with attributes."""
        from src.component_parser.tag_parser import TagParser
        content = '<bx:param name="id" type="numeric" />'
        tags = TagParser._extract_tags(content)
        expect(tags).to_have_length(1)
        expect(tags[0]["name"]).to_be("param")
        expect(tags[0]["attributes"]["name"]).to_be("id")
        expect(tags[0]["attributes"]["type"]).to_be("numeric")

    def test_extract_multiple_tags(self):
        """Test extraction of multiple tags."""
        from src.component_parser.tag_parser import TagParser
        content = "<bx:abort /><bx:dump /><bx:throw />"
        tags = TagParser._extract_tags(content)
        expect(tags).to_have_length(3)
        expect(tags[0]["name"]).to_be("abort")
        expect(tags[1]["name"]).to_be("dump")
        expect(tags[2]["name"]).to_be("throw")

    def test_extract_tag_line_number(self):
        """Test that line numbers are calculated."""
        from src.component_parser.tag_parser import TagParser
        content = "line1\nline2\n<bx:abort />"
        tags = TagParser._extract_tags(content)
        expect(tags[0]["line"]).to_be(3)

    def test_extract_tag_case_insensitive(self):
        """Test tag name extraction is case insensitive."""
        from src.component_parser.tag_parser import TagParser
        content = "<bx:ABORT />"
        tags = TagParser._extract_tags(content)
        expect(tags[0]["name"]).to_be("abort")

    def test_extract_script_tag_with_body(self):
        """Test extraction of bx:script tag with body."""
        from src.component_parser.tag_parser import TagParser
        content = "<bx:script>\nfunction test() {}\n</bx:script>"
        tags = TagParser._extract_tags(content)
        expect(tags).to_have_length(1)
        expect(tags[0]["name"]).to_be("script")
        expect(tags[0]["body"]).to_contain("function test()")

    def test_no_tags(self):
        """Test content with no bx: tags."""
        from src.component_parser.tag_parser import TagParser
        content = "Just plain HTML here"
        tags = TagParser._extract_tags(content)
        expect(tags).to_be_empty()

    def test_non_bx_tags_ignored(self):
        """Test that non-bx: tags are ignored."""
        from src.component_parser.tag_parser import TagParser
        content = "<div>Hello</div><bx:abort />"
        tags = TagParser._extract_tags(content)
        expect(tags).to_have_length(1)
        expect(tags[0]["name"]).to_be("abort")


class TestTagParserParseAttributes:
    """Tests for TagParser._parse_attributes."""

    def test_double_quoted_attributes(self):
        """Test parsing double-quoted attributes."""
        from src.component_parser.tag_parser import TagParser
        attrs = TagParser._parse_attributes('name="test" type="string"')
        expect(attrs["name"]).to_be("test")
        expect(attrs["type"]).to_be("string")

    def test_single_quoted_attributes(self):
        """Test parsing single-quoted attributes."""
        from src.component_parser.tag_parser import TagParser
        attrs = TagParser._parse_attributes("name='test' type='string'")
        expect(attrs["name"]).to_be("test")
        expect(attrs["type"]).to_be("string")

    def test_unquoted_attributes(self):
        """Test parsing unquoted attributes."""
        from src.component_parser.tag_parser import TagParser
        attrs = TagParser._parse_attributes("required=true")
        expect(attrs["required"]).to_be("true")

    def test_mixed_quoting(self):
        """Test parsing mixed quoting styles."""
        from src.component_parser.tag_parser import TagParser
        attrs = TagParser._parse_attributes('name="test" type=\'string\' required=true')
        expect(attrs["name"]).to_be("test")
        expect(attrs["type"]).to_be("string")
        expect(attrs["required"]).to_be("true")

    def test_empty_attributes(self):
        """Test parsing empty attribute string."""
        from src.component_parser.tag_parser import TagParser
        attrs = TagParser._parse_attributes("")
        expect(attrs).to_be_empty()

    def test_attribute_names_lowercased(self):
        """Test that attribute names are lowercased."""
        from src.component_parser.tag_parser import TagParser
        attrs = TagParser._parse_attributes('NAME="test" TYPE="string"')
        expect(attrs).to_have_key("name")
        expect(attrs).to_have_key("type")


class TestTagParserParseString:
    """Tests for TagParser.parse_string."""

    def test_parse_function_tag(self):
        """Test parsing bx:function tag."""
        from src.component_parser.tag_parser import TagParser
        content = '<bx:function name="render" returntype="string" access="public" />'
        metadata = TagParser.parse_string(content)
        expect(metadata["functions"]).to_have_key("render")
        expect(metadata["functions"]["render"]["return_type"]).to_be("string")
        expect(metadata["functions"]["render"]["access"]).to_be("public")

    def test_parse_property_tag(self):
        """Test parsing bx:property tag."""
        from src.component_parser.tag_parser import TagParser
        content = '<bx:property name="title" type="string" default="Hello" />'
        metadata = TagParser.parse_string(content)
        expect(metadata["properties"]).to_have_key("title")
        expect(metadata["properties"]["title"]["type"]).to_be("string")
        expect(metadata["properties"]["title"]["default"]).to_be("Hello")

    def test_parse_multiple_functions(self):
        """Test parsing multiple function tags."""
        from src.component_parser.tag_parser import TagParser
        content = """
            <bx:function name="init" returntype="void" />
            <bx:function name="render" returntype="string" />
        """
        metadata = TagParser.parse_string(content)
        expect(metadata["functions"]).to_have_length(2)
        expect(metadata["functions"]).to_have_key("init")
        expect(metadata["functions"]).to_have_key("render")

    def test_parse_function_without_name(self):
        """Test that function without name is skipped."""
        from src.component_parser.tag_parser import TagParser
        content = '<bx:function returntype="string" />'
        metadata = TagParser.parse_string(content)
        expect(metadata["functions"]).to_be_empty()

    def test_parse_property_without_name(self):
        """Test that property without name is skipped."""
        from src.component_parser.tag_parser import TagParser
        content = '<bx:property type="string" />'
        metadata = TagParser.parse_string(content)
        expect(metadata["properties"]).to_be_empty()

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        from src.component_parser.tag_parser import TagParser
        metadata = TagParser.parse_string("")
        expect(metadata["functions"]).to_be_empty()
        expect(metadata["properties"]).to_be_empty()
        expect(metadata["parse_errors"]).to_be_empty()

    def test_parse_script_block_error(self, mocker):
        """Test that script block parse errors are handled gracefully."""
        mocker.patch("src.component_parser.tag_parser.boxlang_cli.run_ast_code",
                     return_value=(None, "parse error"))
        from src.component_parser.tag_parser import TagParser
        content = "<bx:script>invalid code</bx:script>"
        metadata = TagParser.parse_string(content)
        # Should not crash, just return empty functions
        expect(metadata["functions"]).to_be_empty()


class TestTagParserParseFile:
    """Tests for TagParser.parse (file-based)."""

    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing a file that doesn't exist."""
        from src.component_parser.tag_parser import TagParser
        result = TagParser.parse(str(tmp_path / "nonexistent.bxm"))
        expect(result["parse_errors"]).not_to_be_empty()

    def test_parse_valid_file(self, tmp_path):
        """Test parsing a valid .bxm file."""
        from src.component_parser.tag_parser import TagParser
        test_file = tmp_path / "test.bxm"
        test_file.write_text('<bx:function name="test" returntype="void" />')
        result = TagParser.parse(str(test_file))
        expect(result["functions"]).to_have_key("test")
        expect(result["parse_errors"]).to_be_empty()
