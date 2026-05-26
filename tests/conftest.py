"""
Pytest configuration and shared fixtures for BoxLang tests.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_sublime():
    """Auto-mock the sublime and sublime_plugin modules for all tests."""
    sublime_mock = MagicMock()
    sublime_mock.CompletionItem = MagicMock
    sublime_mock.COMPLETION_FORMAT_SNIPPET = 1
    sublime_mock.COMPLETION_FORMAT_TEXT = 0
    sublime_mock.KIND_ID_FUNCTION = 1
    sublime_mock.KIND_ID_VARIABLE = 2
    sublime_mock.KIND_ID_MARKUP = 3
    sublime_mock.KIND_ID_KEYWORD = 4
    sublime_mock.KIND_ID_TYPE = 5
    sublime_mock.KIND_ID_AMBIGUOUS = 6
    sublime_mock.KIND_ID_NAVIGATION = 7
    sublime_mock.DRAW_SQUIGGLY_UNDERLINE = 1
    sublime_mock.DRAW_NO_FILL = 2
    sublime_mock.DRAW_NO_OUTLINE = 4
    sublime_mock.HIDE_ON_MOUSE_MOVE_AWAY = 8
    sublime_mock.COOPERATE_WITH_AUTO_COMPLETE = 16
    sublime_mock.CLASS_WORD_END = 1
    sublime_mock.CLASS_PUNCTUATION_END = 2
    sublime_mock.CLASS_WORD_START = 4
    sublime_mock.CLASS_PUNCTUATION_START = 8
    sublime_mock.DIALOG_YES = 1
    sublime_mock.DIALOG_NO = 0
    sublime_mock.DIALOG_CANCEL = 2
    sublime_mock.load_settings = MagicMock(return_value=MagicMock())
    sublime_mock.save_settings = MagicMock()
    sublime_mock.load_resource = MagicMock(return_value="")
    sublime_mock.active_window = MagicMock(return_value=None)
    sublime_mock.windows = MagicMock(return_value=[])
    sublime_mock.status_message = MagicMock()
    sublime_mock.run_command = MagicMock()

    sublime_plugin_mock = MagicMock()
    sublime_plugin_mock.EventListener = object
    sublime_plugin_mock.TextCommand = object
    sublime_plugin_mock.WindowCommand = object
    sublime_plugin_mock.ApplicationCommand = object

    with patch.dict("sys.modules", {
        "sublime": sublime_mock,
        "sublime_plugin": sublime_plugin_mock,
    }):
        yield sublime_mock


@pytest.fixture
def mock_sublime_settings(mock_sublime):
    """Fixture for settings with configurable values."""
    settings_store = {}

    def load_settings(name):
        mock = MagicMock()
        mock.get = lambda key, default=None: settings_store.get(key, default)
        mock.set = lambda key, value: settings_store.__setitem__(key, value)
        return mock

    mock_sublime.load_settings = load_settings
    return settings_store


@pytest.fixture
def sample_class_ast():
    """Sample AST output for a class declaration."""
    return {
        "statements": [
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "class"}
            },
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "UserService"}
            },
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {
                    "ASTType": "BoxAssignment",
                    "left": {"name": "extends"},
                    "right": {"ASTType": "BoxStringLiteral", "value": "BaseService"}
                }
            },
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {
                    "ASTType": "BoxAssignment",
                    "left": {"name": "implements"},
                    "right": {"ASTType": "BoxStringLiteral", "value": "IUserService"}
                }
            },
            {
                "ASTType": "BoxStatementBlock",
                "body": [
                    {
                        "ASTType": "BoxFunctionDeclaration",
                        "name": "init",
                        "type": {"sourceText": "void"},
                        "accessModifier": {"sourceText": "public"},
                        "args": [],
                        "annotations": [],
                        "position": {"start": {"line": 3}}
                    },
                    {
                        "ASTType": "BoxFunctionDeclaration",
                        "name": "find",
                        "type": {"sourceText": "query"},
                        "accessModifier": {"sourceText": "public"},
                        "args": [
                            {
                                "name": "criteria",
                                "type": {"sourceText": "struct"},
                                "required": True,
                                "value": None
                            },
                            {
                                "name": "maxRows",
                                "type": {"sourceText": "numeric"},
                                "required": False,
                                "value": {"ASTType": "BoxNumericLiteral", "value": 100}
                            }
                        ],
                        "annotations": [{"ASTType": "BoxAnnotation", "name": "cached"}],
                        "position": {"start": {"line": 7}}
                    },
                    {
                        "ASTType": "BoxFunctionDeclaration",
                        "name": "_privateMethod",
                        "type": {"sourceText": "string"},
                        "accessModifier": {"sourceText": "private"},
                        "args": [],
                        "annotations": [],
                        "position": {"start": {"line": 15}}
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_class_ast_no_extends():
    """Sample AST for a class without extends/implements."""
    return {
        "statements": [
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "class"}
            },
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "SimpleClass"}
            },
            {
                "ASTType": "BoxStatementBlock",
                "body": []
            }
        ]
    }


@pytest.fixture
def sample_class_ast_with_properties():
    """Sample AST for a class with properties."""
    return {
        "statements": [
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "class"}
            },
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "Config"}
            },
            {
                "ASTType": "BoxStatementBlock",
                "body": [
                    {
                        "ASTType": "BoxPropertyDeclaration",
                        "name": "name",
                        "type": {"sourceText": "string"},
                        "accessModifier": {"sourceText": "public"},
                        "value": {"ASTType": "BoxStringLiteral", "value": "default"},
                        "position": {"start": {"line": 2}}
                    },
                    {
                        "ASTType": "BoxPropertyDeclaration",
                        "name": "timeout",
                        "type": {"sourceText": "numeric"},
                        "accessModifier": {"sourceText": "public"},
                        "value": {"ASTType": "BoxNumericLiteral", "value": 30},
                        "position": {"start": {"line": 3}}
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_function_ast():
    """Sample AST with a single function."""
    return {
        "statements": [
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "class"}
            },
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "Test"}
            },
            {
                "ASTType": "BoxStatementBlock",
                "body": [
                    {
                        "ASTType": "BoxFunctionDeclaration",
                        "name": "find",
                        "type": {"sourceText": "query"},
                        "accessModifier": {"sourceText": "public"},
                        "args": [
                            {
                                "name": "criteria",
                                "type": {"sourceText": "struct"},
                                "required": True,
                                "value": None
                            }
                        ],
                        "annotations": [],
                        "position": {"start": {"line": 5}}
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_ast_with_annotations():
    """Sample AST with doc comment annotations."""
    return {
        "statements": [
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "class"},
                "comments": [
                    {
                        "ASTType": "BoxDocComment",
                        "annotations": [
                            {
                                "ASTType": "BoxDocumentationAnnotation",
                                "key": {"value": "displayName"},
                                "value": {"value": "User Service"}
                            },
                            {
                                "ASTType": "BoxDocumentationAnnotation",
                                "key": {"value": "singleton"},
                                "value": {"value": "true"}
                            }
                        ]
                    }
                ]
            },
            {
                "ASTType": "BoxExpressionStatement",
                "expression": {"ASTType": "BoxIdentifier", "name": "UserService"}
            },
            {
                "ASTType": "BoxStatementBlock",
                "body": []
            }
        ]
    }


@pytest.fixture
def sample_bxm_content():
    """Sample .bxm file content."""
    return """<bx:component>
    <bx:property name="title" type="string" />
    <bx:property name="count" type="numeric" default="0" />

    <bx:function name="render" returntype="string" access="public">
        return "<h1>#title#</h1>";
    </bx:function>

    <bx:abort />
    <bx:dump var="#title#" />
    <bx:output>#title#</bx:output>

    <bx:script>
        function helper() {
            return "helper";
        }
    </bx:script>
</bx:component>"""


@pytest.fixture
def sample_bxm_content_self_closing():
    """Sample .bxm content with only self-closing tags."""
    return """<bx:param name="id" type="numeric" required="true" />
<bx:abort />
<bx:return value="#result#" />
<bx:throw type="ValidationError" message="Invalid" />"""


@pytest.fixture
def mock_boxlang_view():
    """Create a mock BoxlangView for testing plugins."""
    from unittest.mock import MagicMock

    view = MagicMock()
    view.type = "script"
    view.position = 0
    view.prefix = ""
    view.project_name = "/path/to/project.sublime-project"
    view.file_path = "/path/to/project/model/User.bx"
    view.dot_context = []
    view.tag_name = None
    view.tag_attribute_name = None
    view.tag_location = None
    view.function_call_params = None
    view.view_metadata = {}
    view.previous_char = ""

    # Named tuple factories
    from collections import namedtuple
    CompletionList = namedtuple("CompletionList", "completions priority exclude_lower_priority")
    Documentation = namedtuple("Documentation", "doc_regions doc_html_variables on_navigate priority")

    view.CompletionList = CompletionList
    view.Documentation = Documentation

    # Mock view methods
    mock_view = MagicMock()
    mock_view.match_selector = MagicMock(return_value=False)
    mock_view.substr = MagicMock(return_value="")
    mock_view.word = MagicMock(return_value=MagicMock(begin=0, end=5))
    mock_view.file_name = MagicMock(return_value="/path/to/project/model/User.bx")
    mock_view.size = MagicMock(return_value=1000)
    mock_view.text_point = MagicMock(return_value=0)
    mock_view.rowcol = MagicMock(return_value=(0, 0))
    mock_view.sel = MagicMock(return_value=[MagicMock(begin=0)])
    mock_view.scope_name = MagicMock(return_value="source.boxlang")
    view.view = mock_view

    return view


@pytest.fixture
def mock_boxlang_view_tag(mock_boxlang_view):
    """Mock BoxlangView in tag context."""
    mock_boxlang_view.type = "tag"
    mock_boxlang_view.tag_name = "bx:query"
    mock_boxlang_view.tag_location = "tag_name"
    mock_boxlang_view.view.match_selector = MagicMock(return_value=True)
    return mock_boxlang_view


@pytest.fixture
def mock_boxlang_view_dot(mock_boxlang_view):
    """Mock BoxlangView in dot context."""
    mock_boxlang_view.type = "dot"
    from collections import namedtuple
    Symbol = namedtuple("Symbol", "name is_function function_region args_region name_region")
    mock_boxlang_view.dot_context = [Symbol("userService", False, None, None, None)]
    return mock_boxlang_view


@pytest.fixture
def fixture_path():
    """Return the path to the fixtures directory."""
    return os.path.join(PROJECT_ROOT, "tests", "fixtures")
