"""
Unit tests for the Type Resolver (type_resolver.py).
"""

import pytest
from tests.expectations import expect


class TestTypeResolverInferFromExpression:
    """Tests for TypeResolver._infer_from_expression."""

    def test_string_literal_double_quotes(self):
        """Test double-quoted string literal."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression('"hello world"')
        expect(result).to_be("string")

    def test_string_literal_single_quotes(self):
        """Test single-quoted string literal."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("'hello world'")
        expect(result).to_be("string")

    def test_array_literal(self):
        """Test array literal."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("[1, 2, 3]")
        expect(result).to_be("array")

    def test_struct_literal(self):
        """Test struct literal with key-value pairs."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression('{"key": "value"}')
        expect(result).to_be("struct")

    def test_numeric_literal_integer(self):
        """Test integer literal."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("42")
        expect(result).to_be("numeric")

    def test_numeric_literal_decimal(self):
        """Test decimal literal."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("3.14")
        expect(result).to_be("numeric")

    def test_numeric_literal_negative(self):
        """Test negative numeric literal."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("-100")
        expect(result).to_be("numeric")

    def test_boolean_true(self):
        """Test boolean true literal."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("true")
        expect(result).to_be("boolean")

    def test_boolean_false(self):
        """Test boolean false literal."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("false")
        expect(result).to_be("boolean")

    def test_new_expression(self):
        """Test new expression."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("new UserService()")
        expect(result).to_be("component:UserService")

    def test_new_expression_with_args(self):
        """Test new expression with constructor args."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("new UserService(arg1, arg2)")
        expect(result).to_be("component:UserService")

    def test_new_expression_dotted_path(self):
        """Test new expression with dotted path."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("new model.UserService()")
        expect(result).to_be("component:model.UserService")

    def test_create_object_component(self):
        """Test createObject with component type."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression('createObject("component", "model.UserService")')
        expect(result).to_be("component:model.UserService")

    def test_create_object_single_quotes(self):
        """Test createObject with single quotes."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("createObject('component', 'model.UserService')")
        expect(result).to_be("component:model.UserService")

    def test_bif_array_new(self):
        """Test arrayNew BIF return type."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("arrayNew()")
        expect(result).to_be("array")

    def test_bif_struct_new(self):
        """Test structNew BIF return type."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("structNew()")
        expect(result).to_be("struct")

    def test_bif_now(self):
        """Test now() BIF return type."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("now()")
        expect(result).to_be("datetime")

    def test_bif_is_defined(self):
        """Test isDefined() BIF return type."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("isDefined('x')")
        expect(result).to_be("boolean")

    def test_bif_to_string(self):
        """Test toString() BIF return type."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("toString(x)")
        expect(result).to_be("string")

    def test_bif_trim(self):
        """Test trim() BIF return type."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("trim(x)")
        expect(result).to_be("string")

    def test_unknown_function(self):
        """Test unknown function returns any."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("unknownFunc()")
        expect(result).to_be("any")

    def test_empty_expression(self):
        """Test empty expression returns any."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("")
        expect(result).to_be("any")

    def test_variable_reference(self):
        """Test plain variable reference returns any."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._infer_from_expression("someVar")
        expect(result).to_be("any")


class TestTypeResolverBIFReturnTypes:
    """Tests for known BIF return type mappings."""

    def test_bif_return_types_mapping(self):
        """Test that BIF_RETURN_TYPES has expected entries."""
        from src.type_resolver import BIF_RETURN_TYPES
        expect(BIF_RETURN_TYPES).to_have_key("arrayNew")
        expect(BIF_RETURN_TYPES).to_have_key("structNew")
        expect(BIF_RETURN_TYPES).to_have_key("now")
        expect(BIF_RETURN_TYPES).to_have_key("isDefined")
        expect(BIF_RETURN_TYPES).to_have_key("toString")
        expect(BIF_RETURN_TYPES["arrayNew"]).to_be("array")
        expect(BIF_RETURN_TYPES["structNew"]).to_be("struct")
        expect(BIF_RETURN_TYPES["now"]).to_be("datetime")
        expect(BIF_RETURN_TYPES["isDefined"]).to_be("boolean")
        expect(BIF_RETURN_TYPES["toString"]).to_be("string")

    def test_bif_return_types_count(self):
        """Test that we have a reasonable number of BIF return types."""
        from src.type_resolver import BIF_RETURN_TYPES
        expect(len(BIF_RETURN_TYPES)).to_be_gt(30)


class TestTypeResolverGetMemberTypeForKnownType:
    """Tests for _get_member_type_for_known_type."""

    def test_string_len(self):
        """Test string.len returns numeric."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._get_member_type_for_known_type("string", "len")
        expect(result).to_be("numeric")

    def test_string_left(self):
        """Test string.left returns string."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._get_member_type_for_known_type("string", "left")
        expect(result).to_be("string")

    def test_string_split(self):
        """Test string.split returns array."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._get_member_type_for_known_type("string", "split")
        expect(result).to_be("array")

    def test_array_sort(self):
        """Test array.sort returns array."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._get_member_type_for_known_type("array", "sort")
        expect(result).to_be("array")

    def test_array_contains(self):
        """Test array.contains returns boolean."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._get_member_type_for_known_type("array", "contains")
        expect(result).to_be("boolean")

    def test_struct_key_exists(self):
        """Test struct.keyExists returns boolean."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._get_member_type_for_known_type("struct", "keyExists")
        expect(result).to_be("boolean")

    def test_struct_key_array(self):
        """Test struct.keyArray returns array."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._get_member_type_for_known_type("struct", "keyArray")
        expect(result).to_be("array")

    def test_unknown_type_member(self):
        """Test unknown type member returns any."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._get_member_type_for_known_type("unknown_type", "someMethod")
        expect(result).to_be("any")

    def test_known_type_unknown_member(self):
        """Test known type with unknown member returns any."""
        from src.type_resolver import TypeResolver
        resolver = TypeResolver(None, 0)
        result = resolver._get_member_type_for_known_type("string", "unknownMethod")
        expect(result).to_be("any")
