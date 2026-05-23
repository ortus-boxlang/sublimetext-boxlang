"""
Unit tests for the Documentation Helpers (documentation_helpers.py).
"""

import pytest
from tests.expectations import expect


class TestSpanWrap:
    """Tests for documentation_helpers.span_wrap."""

    def test_basic_span_wrap(self):
        """Test basic span wrapping."""
        from src.documentation_helpers import span_wrap
        result = span_wrap("functionName", "entity.name.function")
        expect(result).to_be('<span class="entity.name.function">functionName</span>')

    def test_span_wrap_with_spaces(self):
        """Test span wrapping with spaces in class."""
        from src.documentation_helpers import span_wrap
        result = span_wrap("param", "variable.parameter.function")
        expect(result).to_be('<span class="variable.parameter.function">param</span>')


class TestParamHeader:
    """Tests for documentation_helpers.param_header."""

    def test_required_param(self):
        """Test required parameter header."""
        from src.documentation_helpers import param_header
        param = {"name": "criteria", "type": "struct", "required": True}
        result = param_header(param)
        expect(result).to_contain_string("criteria")
        expect(result).not_to_start_with("[")

    def test_optional_param(self):
        """Test optional parameter header."""
        from src.documentation_helpers import param_header
        param = {"name": "maxRows", "type": "numeric", "required": False}
        result = param_header(param)
        expect(result).to_start_with("[")
        expect(result).to_end_with("]")

    def test_param_without_type(self):
        """Test parameter without type."""
        from src.documentation_helpers import param_header
        param = {"name": "data"}
        result = param_header(param)
        expect(result).to_contain_string("data")
        expect(result).not_to_contain_string("storage.type")


class TestCard:
    """Tests for documentation_helpers.card."""

    def test_card_with_header_and_body(self):
        """Test card with both header and body."""
        from src.documentation_helpers import card
        result = card("Header", "Body content")
        expect(result).to_contain_string("card-header")
        expect(result).to_contain_string("Header")
        expect(result).to_contain_string("card-body")
        expect(result).to_contain_string("Body content")

    def test_card_with_header_only(self):
        """Test card with header only."""
        from src.documentation_helpers import card
        result = card(header="Header Only")
        expect(result).to_contain_string("card-header")
        expect(result).not_to_contain_string("card-body")

    def test_card_with_body_only(self):
        """Test card with body only."""
        from src.documentation_helpers import card
        result = card(body="Body Only")
        expect(result).to_contain_string("card-body")
        expect(result).not_to_contain_string("card-header")

    def test_card_empty(self):
        """Test empty card."""
        from src.documentation_helpers import card
        result = card()
        expect(result).to_be('<div class="card"></div>')


class TestCleanHTML:
    """Tests for documentation_helpers.clean_html."""

    def test_clean_html_escapes_ampersand(self):
        """Test that ampersands are escaped."""
        from src.documentation_helpers import clean_html
        result = clean_html("a & b")
        expect(result).to_contain_string("&amp;")
        expect(result).not_to_contain_string("a & b")

    def test_clean_html_escapes_lt_gt(self):
        """Test that < and > are escaped."""
        from src.documentation_helpers import clean_html
        result = clean_html("<div>")
        expect(result).to_contain_string("&lt;")
        expect(result).to_contain_string("&gt;")

    def test_clean_html_code_blocks(self):
        """Test that backtick code is converted to <code>."""
        from src.documentation_helpers import clean_html
        result = clean_html("Use `functionName` here")
        expect(result).to_contain_string("<code>functionName</code>")

    def test_clean_html_newlines(self):
        """Test that newlines are converted to <br>."""
        from src.documentation_helpers import clean_html
        result = clean_html("line1\nline2")
        expect(result).to_contain_string("<br>")

    def test_clean_html_none(self):
        """Test that None returns empty string."""
        from src.documentation_helpers import clean_html
        result = clean_html(None)
        expect(result).to_be("")

    def test_clean_html_empty(self):
        """Test that empty string returns empty string."""
        from src.documentation_helpers import clean_html
        result = clean_html("")
        expect(result).to_be("")


class TestBuildSignature:
    """Tests for documentation_helpers.build_signature."""

    def test_signature_without_return_type(self):
        """Test signature without return type."""
        from src.documentation_helpers import build_signature
        params = [
            {"name": "criteria", "type": "struct", "required": True},
            {"name": "maxRows", "type": "numeric", "required": False}
        ]
        result = build_signature("find", params)
        expect(result).to_contain_string("find")
        expect(result).to_contain_string("criteria")
        expect(result).to_contain_string("maxRows")

    def test_signature_with_return_type(self):
        """Test signature with return type."""
        from src.documentation_helpers import build_signature
        params = [{"name": "id", "type": "numeric", "required": True}]
        result = build_signature("getById", params, "query")
        expect(result).to_contain_string("query")

    def test_signature_no_params(self):
        """Test signature with no parameters."""
        from src.documentation_helpers import build_signature
        result = build_signature("init", [])
        expect(result).to_contain_string("init")
        expect(result).to_contain_string("()")
