"""
Integration tests for the plugin system.
"""

import pytest
from tests.expectations import expect
from unittest.mock import MagicMock


class TestPluginSystem:
    """Tests for the overall plugin system."""

    def test_plugin_base_class_exists(self):
        """Test that the BoxlangPlugin base class exists."""
        from src.plugins_.plugin import BoxlangPlugin
        expect(BoxlangPlugin).not_to_be_none()

    def test_plugin_base_class_has_required_methods(self):
        """Test that base class has all required methods."""
        from src.plugins_.plugin import BoxlangPlugin
        plugin = BoxlangPlugin()
        expect(hasattr(plugin, "get_completions")).to_be_true()
        expect(hasattr(plugin, "get_completion_docs")).to_be_true()
        expect(hasattr(plugin, "get_inline_documentation")).to_be_true()
        expect(hasattr(plugin, "get_goto_boxlang_file")).to_be_true()
        expect(hasattr(plugin, "get_method_preview")).to_be_true()

    def test_plugin_loader_directory_defined(self):
        """Test that plugin loader has directory defined."""
        from src import boxlang_plugins
        expect(boxlang_plugins.directory).to_be_a(list)
        expect(len(boxlang_plugins.directory)).to_be_gt(0)

    def test_plugin_loader_plugins_list_exists(self):
        """Test that plugins list exists."""
        from src import boxlang_plugins
        expect(boxlang_plugins.plugins).to_be_a(list)


class TestPluginModuleImports:
    """Tests that all plugin modules can be imported."""

    def test_import_basecompletions(self, mock_sublime):
        """Test that basecompletions module can be imported."""
        from src.plugins_ import basecompletions
        expect(basecompletions).not_to_be_none()

    def test_import_boxdocs(self, mock_sublime):
        """Test that boxdocs module can be imported."""
        from src.plugins_ import boxdocs
        expect(boxdocs).not_to_be_none()

    def test_import_classes(self, mock_sublime):
        """Test that classes module can be imported."""
        from src.plugins_ import classes
        expect(classes).not_to_be_none()

    def test_import_dotpaths(self, mock_sublime):
        """Test that dotpaths module can be imported."""
        from src.plugins_ import dotpaths
        expect(dotpaths).not_to_be_none()

    def test_import_typecompletions(self, mock_sublime):
        """Test that typecompletions module can be imported."""
        from src.plugins_ import typecompletions
        expect(typecompletions).not_to_be_none()

    def test_in_file_completions_parses_property_declaration(self, mock_sublime):
        """Test that BoxLang property declarations are recognized as properties."""
        from src.plugins_.in_file_completions import parse_file_symbols

        class MockView:
            def substr(self, region):
                return 'property string title;\n'

            def size(self):
                return len('property string title;\n')

        symbols = parse_file_symbols(MockView())

        expect(symbols['properties']).to_have_length(1)
        expect(symbols['properties'][0]['name']).to_be('title')
        expect(symbols['properties'][0]['type']).to_be('string')


class TestPluginContextTypes:
    """Tests for plugin behavior across different context types."""

    def test_plugin_handles_tag_context(self, mock_boxlang_view_tag):
        """Test that plugins handle tag context."""
        from src.plugins_.basecompletions import get_completions
        result = get_completions(mock_boxlang_view_tag)
        expect(result is None or hasattr(result, "completions")).to_be_true()

    def test_plugin_handles_dot_context(self, mock_boxlang_view_dot):
        """Test that plugins handle dot context."""
        from src.plugins_.typecompletions import get_completions
        result = get_completions(mock_boxlang_view_dot)
        expect(result is None or hasattr(result, "completions")).to_be_true()

    def test_plugin_handles_script_context(self, mock_boxlang_view):
        """Test that plugins handle script context."""
        from src.plugins_.basecompletions import get_completions
        result = get_completions(mock_boxlang_view)
        expect(result is None or hasattr(result, "completions")).to_be_true()


class TestBoxlangViewContext:
    """Tests for BoxlangView context detection."""

    def test_boxlang_view_named_tuples(self, mock_sublime):
        """Test that BoxlangView has named tuple factories."""
        from src.boxlang_view import BoxlangView, CompletionList, Documentation, MethodPreview, CompletionDoc, GotoBoxlangFile
        expect(CompletionList).not_to_be_none()
        expect(Documentation).not_to_be_none()
        expect(MethodPreview).not_to_be_none()
        expect(CompletionDoc).not_to_be_none()
        expect(GotoBoxlangFile).not_to_be_none()

    def test_completion_list_named_tuple(self):
        """Test CompletionList named tuple structure."""
        from src.boxlang_view import CompletionList
        cl = CompletionList(["item1", "item2"], 0, False)
        expect(cl.completions).to_have_length(2)
        expect(cl.priority).to_be(0)
        expect(cl.exclude_lower_priority).to_be_false()

    def test_documentation_named_tuple(self):
        """Test Documentation named tuple structure."""
        from src.boxlang_view import Documentation
        doc = Documentation([], {"side_color": "#fff", "html": {}}, None, 0)
        expect(doc.doc_regions).to_be_a(list)
        expect(doc.doc_html_variables).to_have_key("side_color")
        expect(doc.priority).to_be(0)

    def test_boxlang_view_tolerates_metadata_failure(self, mock_sublime, monkeypatch):
        """Inline-doc contexts should still initialize when metadata lookup fails."""
        from src.boxlang_view import BoxlangView
        from src import buffer_metadata

        class MockView:
            def match_selector(self, point, selector):
                return selector == 'source.boxlang'

            def file_name(self):
                return '/path/to/project/model/User.bx'

            def window(self):
                return None

            def substr(self, point):
                return ''

        monkeypatch.setattr(buffer_metadata, 'get_cached_view_metadata', lambda view: (_ for _ in ()).throw(RuntimeError('boom')))

        boxlang_view = BoxlangView(MockView(), 1)

        expect(boxlang_view.type).to_be('script')
        expect(boxlang_view.view_metadata).to_be_a(dict)


class TestInlineDocumentationHelpers:
    """Tests for hover-doc helper behavior."""

    def test_hover_docs_use_previous_character_when_hover_is_on_token_boundary(self):
        """Hover points just after a token should still resolve docs against the token."""
        from src.inline_documentation import get_documentation_position

        class MockView:
            def match_selector(self, point, selector):
                return point == 4

        expect(get_documentation_position(MockView(), 5)).to_be(4)
        expect(get_documentation_position(MockView(), 4)).to_be(4)


class TestGotoBoxlangFile:
    """Tests for go-to-definition functionality."""

    def test_goto_file_module_exists(self):
        """Test that goto_boxlang_file module exists."""
        from src import goto_boxlang_file
        expect(goto_boxlang_file).not_to_be_none()

    def test_goto_file_has_command(self):
        """Test that goto file command class exists."""
        from src.goto_boxlang_file import BoxlangGotoFileCommand
        expect(BoxlangGotoFileCommand).not_to_be_none()
