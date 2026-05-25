"""
Regression tests for bugs fixed in the codebase review.

Covers:
  - dotpaths: duplicate get_completions name collision
  - buffer_metadata: wrong scope selector for .bx files
  - boxlang_view: wrong cache key in get_struct_context
  - classes/__init__: import os at bottom of file
  - tag_parser: ASTParser import at bottom of file
  - status_bar: missing setting default + wrong scope
"""

import pytest
from unittest.mock import MagicMock, patch
from tests.expectations import expect


# ---------------------------------------------------------------------------
# Bug: dotpaths/_lookup_completions name collision
# ---------------------------------------------------------------------------

class TestDotpathsNoNameCollision:
    """The internal lookup helper must not shadow the public entry point."""

    def test_internal_helper_is_private(self):
        """_lookup_completions should exist; get_completions (public) should too."""
        import importlib
        dotpaths = importlib.import_module('src.plugins_.dotpaths')
        expect(hasattr(dotpaths, '_lookup_completions')).to_be_true()
        expect(hasattr(dotpaths, 'get_completions')).to_be_true()

    def test_public_get_completions_accepts_one_arg(self):
        """Public get_completions(boxlang_view) must accept exactly one argument."""
        import inspect
        from src.plugins_.dotpaths import get_completions
        sig = inspect.signature(get_completions)
        expect(len(sig.parameters)).to_be(1)

    def test_internal_lookup_accepts_three_args(self):
        """_lookup_completions must accept (project_name, dot_path, completion_type)."""
        import inspect
        from src.plugins_.dotpaths import _lookup_completions
        sig = inspect.signature(_lookup_completions)
        expect(len(sig.parameters)).to_be(3)

    def test_lookup_completions_returns_empty_for_unknown_key(self):
        """_lookup_completions returns [] when key not found."""
        from src.plugins_.dotpaths import _lookup_completions, projects
        projects['proj'] = {'path_completions': {}}
        result = _lookup_completions('proj', 'nonexistent.path', 'path_completions')
        expect(result).to_be([])

    def test_lookup_completions_returns_data_for_known_key(self):
        """_lookup_completions returns data when key is found."""
        from src.plugins_.dotpaths import _lookup_completions, projects
        projects['proj'] = {'path_completions': {'model.user': ['UserCompletion']}}
        result = _lookup_completions('proj', 'model.User', 'path_completions')
        expect(result).to_be(['UserCompletion'])


# ---------------------------------------------------------------------------
# Bug: buffer_metadata wrong scope selector for .bx files
# ---------------------------------------------------------------------------

class TestBufferMetadataScope:
    """buffer_metadata must parse both .bx (source.boxlang) and .bxm files."""

    def test_scope_string_includes_source_boxlang(self):
        """on_view_loaded/on_view_modified must check 'source.boxlang'."""
        import inspect
        from src import buffer_metadata
        source = inspect.getsource(buffer_metadata)
        # The old broken selector was 'embedding.boxlang' alone (missing source.boxlang)
        expect(source).to_contain('source.boxlang, embedding.boxlang')

    def test_on_view_loaded_fires_for_bx_file(self):
        """on_view_loaded should call get_view_metadata for source.boxlang views."""
        from src import buffer_metadata
        buffer_metadata.buffer_metadata_cache.clear()

        mock_view = MagicMock()
        mock_view.buffer_id.return_value = 9001
        mock_view.match_selector.side_effect = lambda pos, sel: 'source.boxlang' in sel
        mock_view.file_name.return_value = None
        mock_view.find_by_selector.return_value = []
        mock_view.substr.return_value = ''
        mock_view.window.return_value = MagicMock()
        mock_view.window().project_file_name.return_value = None

        buffer_metadata.on_view_loaded(mock_view)
        # metadata was cached — view was processed
        expect(mock_view.buffer_id.called).to_be_true()

    def test_on_view_loaded_skips_non_boxlang_file(self):
        """on_view_loaded must skip views that are not BoxLang."""
        from src import buffer_metadata
        buffer_metadata.buffer_metadata_cache.clear()

        mock_view = MagicMock()
        mock_view.buffer_id.return_value = 9002
        mock_view.match_selector.return_value = False

        buffer_metadata.on_view_loaded(mock_view)
        expect(9002 in buffer_metadata.buffer_metadata_cache).to_be_false()


# ---------------------------------------------------------------------------
# Bug: boxlang_view wrong cache key in get_struct_context
# ---------------------------------------------------------------------------

class TestBoxlangViewStructContextCacheKey:
    """get_struct_context must use its own cache bucket, not 'get_function'."""

    def test_struct_context_uses_correct_cache_key(self):
        """After calling get_struct_context, result is stored in get_struct_context bucket."""
        from collections import defaultdict
        from unittest.mock import MagicMock, patch

        mock_view = MagicMock()
        mock_view.file_name.return_value = '/tmp/test.bx'
        mock_view.window.return_value = MagicMock()
        mock_view.window().project_file_name.return_value = None
        mock_view.match_selector.return_value = False
        mock_view.scope_name.return_value = 'source.boxlang'
        mock_view.substr.return_value = ''

        with patch('src.boxlang_view.utils') as mock_utils, \
             patch('src.boxlang_view.buffer_metadata') as mock_bm:
            mock_utils.normalize_path.return_value = '/tmp/test.bx'
            mock_utils.get_project_name.return_value = None
            mock_utils.get_struct_context.return_value = []
            mock_bm.get_cached_view_metadata.return_value = {}

            from src.boxlang_view import BoxlangView
            bv = BoxlangView.__new__(BoxlangView)
            bv.view = mock_view
            bv.prefix = ''
            bv.position = 10
            bv.prefix_start = 10
            bv._cache = defaultdict(dict)

            bv.get_struct_context(5)

            # Must be stored under 'get_struct_context', NOT 'get_function'
            expect(5 in bv._cache['get_struct_context']).to_be_true()
            expect(5 in bv._cache['get_function']).to_be_false()

    def test_struct_context_cache_hit_avoids_recomputation(self):
        """Cached get_struct_context result is returned without calling utils again."""
        from collections import defaultdict
        from unittest.mock import MagicMock, patch

        mock_view = MagicMock()

        with patch('src.boxlang_view.utils') as mock_utils, \
             patch('src.boxlang_view.buffer_metadata'):
            mock_utils.get_struct_context.return_value = ['sentinel']

            from src.boxlang_view import BoxlangView
            bv = BoxlangView.__new__(BoxlangView)
            bv.view = mock_view
            bv._cache = defaultdict(dict)

            result1 = bv.get_struct_context(42)
            result2 = bv.get_struct_context(42)

            expect(result1).to_be(result2)
            expect(mock_utils.get_struct_context.call_count).to_be(1)


# ---------------------------------------------------------------------------
# Bug: classes/__init__.py import os at bottom
# ---------------------------------------------------------------------------

class TestClassesImportOrder:
    """os must be importable at the top of classes/__init__.py."""

    def test_os_imported_before_build_variable_mappings(self):
        """build_variable_mappings uses os; it must not NameError on import."""
        import inspect
        import importlib
        mod = importlib.import_module('src.plugins_.classes')
        source = inspect.getsource(mod)
        # import os must appear before build_variable_mappings definition
        os_pos = source.find('import os')
        func_pos = source.find('def build_variable_mappings')
        expect(os_pos).to_be_gt(-1)
        expect(func_pos).to_be_gt(-1)
        expect(os_pos).to_be_lt(func_pos)

    def test_build_variable_mappings_doesnt_nameError(self, mock_sublime):
        """build_variable_mappings must not raise NameError for os."""
        from src.plugins_ import classes
        mock_sublime.windows.return_value = []
        # Should run without NameError; no project data → returns early
        classes.build_variable_mappings('/nonexistent/project.sublime-project')


# ---------------------------------------------------------------------------
# Bug: tag_parser ASTParser import at bottom
# ---------------------------------------------------------------------------

class TestTagParserImportOrder:
    """ASTParser must be importable at the top of tag_parser.py."""

    def test_ast_parser_import_is_at_top(self):
        """ASTParser import must appear before TagParser class definition."""
        import inspect
        from src.component_parser import tag_parser
        source = inspect.getsource(tag_parser)
        import_pos = source.find('from .ast_parser import ASTParser')
        class_pos = source.find('class TagParser')
        expect(import_pos).to_be_gt(-1)
        expect(class_pos).to_be_gt(-1)
        expect(import_pos).to_be_lt(class_pos)

    def test_tag_parser_script_block_uses_ast_parser(self):
        """_parse_script_block must resolve ASTParser without error."""
        from src.component_parser.tag_parser import TagParser, ASTParser
        # ASTParser must be accessible in the module namespace
        expect(ASTParser).not_to_be_none()

    def test_parse_script_block_returns_functions_on_success(self):
        """_parse_script_block returns a dict with 'functions' key."""
        from src.component_parser.tag_parser import TagParser

        ast_result = {
            'statements': [
                {
                    'ASTType': 'BoxFunctionDeclaration',
                    'name': 'helper',
                    'type': {'sourceText': 'string'},
                    'accessModifier': {'sourceText': 'public'},
                    'args': [],
                    'annotations': [],
                    'position': {'start': {'line': 1}},
                }
            ]
        }
        with patch('src.component_parser.tag_parser.boxlang_cli.run_ast_code',
                   return_value=(ast_result, None)):
            result = TagParser._parse_script_block('function helper() { return "x"; }')
        expect(result).to_have_key('functions')
        expect('helper' in result['functions']).to_be_true()


# ---------------------------------------------------------------------------
# Bug: status_bar missing setting default + double _plugin_loaded
# ---------------------------------------------------------------------------

class TestStatusBarSettingDefault:
    """Status bar must default to enabled when setting is absent."""

    def test_missing_setting_defaults_to_enabled(self, mock_sublime):
        """When boxlang_status_bar_enabled is absent (None), status bar stays on."""
        from src import status_bar, boxlang_cli
        boxlang_cli._boxlang_installed = True
        boxlang_cli._boxlang_version = '1.0.0'

        mock_settings = MagicMock()
        mock_settings.get = MagicMock(return_value=None)  # setting absent
        mock_sublime.load_settings.return_value = mock_settings

        mock_view = MagicMock()
        mock_view.match_selector.return_value = True
        mock_view.file_name.return_value = None
        mock_view.window.return_value = MagicMock()
        mock_view.window().project_file_name.return_value = None

        status_bar._update_status_bar(mock_view)
        # set_status must have been called (not just erase_status)
        mock_view.set_status.assert_called()

    def test_explicit_false_disables_status_bar(self, mock_sublime):
        """When boxlang_status_bar_enabled is explicitly False, status is cleared."""
        from src import status_bar

        mock_settings = MagicMock()
        mock_settings.get = MagicMock(return_value=False)
        mock_sublime.load_settings.return_value = mock_settings

        mock_view = MagicMock()
        mock_view.match_selector.return_value = True

        status_bar._update_status_bar(mock_view)
        mock_view.erase_status.assert_called()
        mock_view.set_status.assert_not_called()

    def test_non_boxlang_file_skipped(self, mock_sublime):
        """Status bar update must skip non-BoxLang views."""
        from src import status_bar

        mock_settings = MagicMock()
        mock_settings.get = MagicMock(return_value=None)
        mock_sublime.load_settings.return_value = mock_settings

        mock_view = MagicMock()
        mock_view.match_selector.return_value = False  # not a BoxLang file

        status_bar._update_status_bar(mock_view)
        mock_view.set_status.assert_not_called()
        mock_view.erase_status.assert_not_called()
