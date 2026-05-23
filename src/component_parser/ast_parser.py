"""
AST-based parser for .bx and .bxs files using boxlang --bx-printast.
"""

import json
import re
from .. import boxlang_cli


class ASTParser:
    """Parser that uses BoxLang AST output to extract component metadata."""

    @staticmethod
    def parse(file_path):
        """Parse a .bx or .bxs file and return component metadata."""
        ast, error = boxlang_cli.run_ast(file_path)

        if error:
            return {
                "name": None,
                "extends": None,
                "implements": [],
                "functions": {},
                "properties": {},
                "annotations": [],
                "parse_errors": [error]
            }

        return ASTParser._extract_metadata(ast)

    @staticmethod
    def parse_string(content):
        """Parse BoxLang code from a string and return component metadata."""
        ast, error = boxlang_cli.run_ast_code(content)

        if error:
            return {
                "name": None,
                "extends": None,
                "implements": [],
                "functions": {},
                "properties": {},
                "annotations": [],
                "parse_errors": [error]
            }

        return ASTParser._extract_metadata(ast)

    @staticmethod
    def _extract_metadata(ast):
        """Extract component metadata from the AST JSON."""
        metadata = {
            "name": None,
            "extends": None,
            "implements": [],
            "functions": {},
            "properties": {},
            "annotations": [],
            "parse_errors": []
        }

        statements = ast.get("statements", [])

        # Look for class declaration pattern:
        # BoxIdentifier("class") -> BoxAssignment("extends", ...) -> BoxAssignment("implements", ...) -> BoxStatementBlock
        class_info = ASTParser._find_class_info(statements)
        metadata.update(class_info)

        # Extract functions and properties from the class body
        for stmt in statements:
            if stmt.get("ASTType") == "BoxStatementBlock":
                body = stmt.get("body", [])
                for item in body:
                    if item.get("ASTType") == "BoxFunctionDeclaration":
                        func_meta = ASTParser._extract_function(item)
                        metadata["functions"][func_meta["name"]] = func_meta
                    elif item.get("ASTType") == "BoxPropertyDeclaration":
                        prop_meta = ASTParser._extract_property(item)
                        metadata["properties"][prop_meta["name"]] = prop_meta

        return metadata

    @staticmethod
    def _find_class_info(statements):
        """
        Find class declaration info from sequential statements.

        Pattern: BoxIdentifier("class") -> optional BoxAssignment("extends", ...)
                 -> optional BoxAssignment("implements", ...) -> BoxStatementBlock
        """
        info = {
            "name": None,
            "extends": None,
            "implements": [],
            "annotations": []
        }

        i = 0
        while i < len(statements):
            stmt = statements[i]

            # Look for BoxIdentifier with name "class"
            if stmt.get("ASTType") == "BoxExpressionStatement":
                expr = stmt.get("expression", {})
                if expr.get("ASTType") == "BoxIdentifier" and expr.get("name") == "class":
                    # Found class keyword, next statement(s) may have class info
                    i += 1

                    # Check for class name (BoxIdentifier after "class")
                    while i < len(statements):
                        next_stmt = statements[i]

                        if next_stmt.get("ASTType") == "BoxExpressionStatement":
                            next_expr = next_stmt.get("expression", {})

                            if next_expr.get("ASTType") == "BoxIdentifier":
                                name = next_expr.get("name")
                                if name and name not in ["extends", "implements"]:
                                    # This is the class name
                                    if not info["name"]:
                                        info["name"] = name
                                    i += 1
                                    continue

                            elif next_expr.get("ASTType") == "BoxAssignment":
                                left = next_expr.get("left", {})
                                right = next_expr.get("right", {})

                                if left.get("name") == "extends":
                                    # Extract extends value
                                    if right.get("ASTType") == "BoxStringLiteral":
                                        info["extends"] = right.get("value")
                                    elif right.get("ASTType") == "BoxIdentifier":
                                        info["extends"] = right.get("name")
                                    i += 1
                                    continue

                                elif left.get("name") == "implements":
                                    # Extract implements value (may be comma-separated)
                                    if right.get("ASTType") == "BoxStringLiteral":
                                        value = right.get("value", "")
                                        info["implements"] = [
                                            impl.strip() for impl in value.split(",") if impl.strip()
                                        ]
                                    elif right.get("ASTType") == "BoxIdentifier":
                                        info["implements"] = [right.get("name")]
                                    i += 1
                                    continue

                        elif next_stmt.get("ASTType") == "BoxStatementBlock":
                            # Found the class body
                            break

                        i += 1

                    break

            i += 1

        # Extract annotations from comments
        for stmt in statements:
            comments = stmt.get("comments", [])
            for comment in comments:
                if comment.get("ASTType") == "BoxDocComment":
                    annotations = comment.get("annotations", [])
                    for ann in annotations:
                        if ann.get("ASTType") == "BoxDocumentationAnnotation":
                            key = ann.get("key", {})
                            value = ann.get("value", {})
                            info["annotations"].append({
                                "key": key.get("value", ""),
                                "value": value.get("value", "")
                            })

        return info

    @staticmethod
    def _extract_function(func_node):
        """Extract function metadata from a BoxFunctionDeclaration node."""
        name = func_node.get("name", "unknown")

        # Extract return type
        type_node = func_node.get("type", {})
        return_type = None
        if type_node:
            inner_type = type_node.get("type", {})
            if inner_type:
                return_type = inner_type.get("sourceText")
            elif type_node.get("sourceText"):
                return_type = type_node.get("sourceText")

        # Extract access modifier
        access_mod = func_node.get("accessModifier", {})
        access = None
        if access_mod:
            access = access_mod.get("sourceText", "").lower()

        # Extract arguments
        args = []
        for arg in func_node.get("args", []):
            arg_info = {
                "name": arg.get("name", ""),
                "type": arg.get("type"),
                "required": arg.get("required", False),
                "default": arg.get("value")
            }
            args.append(arg_info)

        # Extract annotations
        annotations = []
        for ann in func_node.get("annotations", []):
            if ann.get("ASTType") == "BoxAnnotation":
                annotations.append(ann.get("name", ""))

        return {
            "name": name,
            "return_type": return_type,
            "access": access,
            "args": args,
            "annotations": annotations,
            "line": func_node.get("position", {}).get("start", {}).get("line", 0)
        }

    @staticmethod
    def _extract_property(prop_node):
        """Extract property metadata from a BoxPropertyDeclaration node."""
        name = prop_node.get("name", "unknown")

        return {
            "name": name,
            "type": prop_node.get("type"),
            "access": prop_node.get("accessModifier", {}).get("sourceText", "").lower(),
            "default": prop_node.get("value"),
            "line": prop_node.get("position", {}).get("start", {}).get("line", 0)
        }
