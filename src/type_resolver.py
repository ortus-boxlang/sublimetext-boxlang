"""
Medium-depth type inference engine for BoxLang.
Resolves types from literals, new expressions, variable assignments, and function returns.
"""

import re
import sublime
from . import utils
from . import buffer_metadata
from .component_parser import ast_parser
from . import component_index

KNOWN_TYPES = {
    "string", "numeric", "number", "boolean", "array", "struct", "map",
    "query", "date", "datetime", "void", "any", "xml", "binary",
    "function", "closure", "lambda", "java", "uicomponent",
}

BIF_RETURN_TYPES = {
    "arrayNew": "array",
    "arrayLen": "numeric",
    "structNew": "struct",
    "mapNew": "map",
    "queryNew": "query",
    "now": "datetime",
    "createDate": "date",
    "createDateTime": "datetime",
    "isDefined": "boolean",
    "isNull": "boolean",
    "isStruct": "boolean",
    "isArray": "boolean",
    "isQuery": "boolean",
    "isDate": "boolean",
    "isNumeric": "boolean",
    "isBoolean": "boolean",
    "isClosure": "boolean",
    "isCustomFunction": "boolean",
    "toString": "string",
    "toNumeric": "numeric",
    "toBoolean": "boolean",
    "toScript": "string",
    "getMetaData": "struct",
    "getFunctionCalledName": "string",
    "getBaseTemplatePath": "string",
    "getCurrentTemplatePath": "string",
    "getDirectoryFromPath": "string",
    "getFileFromPath": "string",
    "trim": "string",
    "len": "numeric",
    "left": "string",
    "right": "string",
    "mid": "string",
    "lCase": "string",
    "uCase": "string",
    "dateFormat": "string",
    "timeFormat": "string",
    "encodeForHTML": "string",
    "decodeFromHTML": "string",
    "hash": "string",
    "rand": "numeric",
    "randRange": "numeric",
    "abs": "numeric",
    "ceiling": "numeric",
    "floor": "numeric",
    "round": "numeric",
    "max": "numeric",
    "min": "numeric",
    "pi": "numeric",
    "inputBaseN": "numeric",
    "formatBaseN": "string",
}


class TypeResolver:
    """Resolves types for variables, expressions, and function calls."""

    def __init__(self, view, position):
        self.view = view
        self.position = position
        self._cache = {}

    def resolve_type_at_position(self):
        """Resolve the type at the current cursor position."""
        pt = self.position

        if self.view.match_selector(pt, "variable.other.readwrite.boxlang"):
            word = self.view.substr(self.view.word(pt)).lower()
            return self.resolve_variable_type(word, pt)

        if self.view.match_selector(pt, "meta.function-call.support.boxlang"):
            func_name = self.view.substr(self.view.word(pt)).lower()
            return BIF_RETURN_TYPES.get(func_name, "any")

        return "any"

    def resolve_variable_type(self, var_name, position):
        """Resolve the type of a variable by looking at its assignment."""
        cache_key = ("var", var_name, position)
        if cache_key in self._cache:
            return self._cache[cache_key]

        assignment = utils.find_variable_assignment(self.view, position, var_name)
        if not assignment:
            result = "any"
            self._cache[cache_key] = result
            return result

        result = self._resolve_from_assignment(assignment, var_name)
        self._cache[cache_key] = result
        return result

    def _resolve_from_assignment(self, assignment, var_name):
        """Resolve type from a variable assignment region."""
        end_pt = min(assignment.end() + 200, self.view.size())
        assign_text = self.view.substr(sublime.Region(assignment.begin(), end_pt))

        type_result = self._infer_type_from_text(assign_text)
        return type_result

    def _infer_type_from_text(self, code):
        """Infer type from a code snippet."""
        code = code.strip()

        if "=" not in code:
            return "any"

        rhs = code.split("=", 1)[1].strip()

        type_result = self._infer_from_expression(rhs)
        return type_result

    def _infer_from_expression(self, expr):
        """Infer type from an expression."""
        expr = expr.strip()

        if not expr:
            return "any"

        result = self._check_new_expression(expr)
        if result:
            return result

        result = self._check_literal(expr)
        if result:
            return result

        result = self._check_function_call(expr)
        if result:
            return result

        result = self._check_create_object(expr)
        if result:
            return result

        return "any"

    def _check_new_expression(self, expr):
        """Check for `new ComponentName()` pattern."""
        match = re.match(r'new\s+([\w.]+)', expr)
        if match:
            component_path = match.group(1)
            return f"component:{component_path}"
        return None

    def _check_literal(self, expr):
        """Check for literal values."""
        if expr.startswith('"') or expr.startswith("'"):
            return "string"

        if expr.startswith("["):
            if ":" in expr.split("]")[0]:
                return "struct"
            return "array"

        if expr.startswith("{"):
            return "struct"

        if expr.startswith("queryNew") or expr.startswith("QueryNew"):
            return "query"

        numeric_pattern = re.compile(r'^-?\d+(\.\d+)?$')
        if numeric_pattern.match(expr):
            return "numeric"

        if expr.lower() in ("true", "false"):
            return "boolean"

        return None

    def _check_function_call(self, expr):
        """Check for known BIF calls."""
        match = re.match(r'(\w+)\s*\(', expr)
        if match:
            func_name = match.group(1)
            if func_name in BIF_RETURN_TYPES:
                return BIF_RETURN_TYPES[func_name]
        return None

    def _check_create_object(self, expr):
        """Check for createObject() pattern."""
        match = re.match(r'createObject\s*\(\s*["\']component["\']\s*,\s*["\']([^"\']+)["\']', expr)
        if match:
            component_path = match.group(1)
            return f"component:{component_path}"
        return None

    def resolve_function_return_type(self, component_path, function_name):
        """Resolve the return type of a function from a component."""
        if not component_path:
            return "any"

        metadata = component_index.get_indexed_metadata_by_dotpath(component_path)
        if not metadata:
            return "any"

        functions = metadata.get("functions", {})
        func_meta = functions.get(function_name)
        if func_meta:
            return_type = func_meta.get("return_type")
            if return_type:
                return return_type

        if metadata.get("extends"):
            return self.resolve_function_return_type(metadata["extends"], function_name)

        return "any"

    def resolve_dot_chain_type(self, dot_context):
        """Resolve the type at the end of a dot chain."""
        if not dot_context:
            return "any"

        current_type = self._resolve_first_element(dot_context[0])

        for symbol in dot_context[1:]:
            if current_type.startswith("component:"):
                component_path = current_type[len("component:"):]
                current_type = self._resolve_member_type(component_path, symbol.name)
            else:
                current_type = self._get_member_type_for_known_type(current_type, symbol.name)

        return current_type

    def _resolve_first_element(self, symbol):
        """Resolve the type of the first element in a dot chain."""
        name = symbol.name.lower()

        if symbol.is_function:
            return "any"

        var_type = self.resolve_variable_type(name, self.position)
        if var_type != "any":
            return var_type

        if name[0:1].isupper():
            return f"component:{name}"

        return "any"

    def _resolve_member_type(self, component_path, member_name):
        """Resolve the type of a member on a component."""
        metadata = component_index.get_indexed_metadata_by_dotpath(component_path)
        if not metadata:
            return "any"

        functions = metadata.get("functions", {})
        func_meta = functions.get(member_name)
        if func_meta:
            return func_meta.get("return_type", "any")

        properties = metadata.get("properties", {})
        prop_meta = properties.get(member_name)
        if prop_meta:
            return prop_meta.get("type", "any")

        if metadata.get("extends"):
            return self._resolve_member_type(metadata["extends"], member_name)

        return "any"

    def _get_member_type_for_known_type(self, type_name, member_name):
        """Get the return type of a member method on a known type."""
        member_methods = {
            "string": {
                "len": "numeric", "length": "numeric", "left": "string",
                "right": "string", "mid": "string", "trim": "string",
                "lCase": "string", "uCase": "string", "replace": "string",
                "find": "numeric", "split": "array", "substring": "string",
                "toNumeric": "numeric", "toBoolean": "boolean",
            },
            "array": {
                "len": "numeric", "length": "numeric", "append": "void",
                "prepend": "void", "delete": "void", "sort": "array",
                "reverse": "array", "slice": "array", "find": "numeric",
                "contains": "boolean", "isEmpty": "boolean",
            },
            "struct": {
                "len": "numeric", "length": "numeric", "keyArray": "array",
                "valueArray": "array", "delete": "void", "clear": "void",
                "isEmpty": "boolean", "keyExists": "boolean",
            },
            "query": {
                "len": "numeric", "length": "numeric", "columnArray": "array",
                "addColumn": "void", "deleteRow": "void",
            },
            "numeric": {
                "abs": "numeric", "ceiling": "numeric", "floor": "numeric",
                "round": "numeric", "toString": "string",
            },
        }

        type_methods = type_methods if (type_methods := member_methods.get(type_name)) else {}
        return type_methods.get(member_name, "any")
