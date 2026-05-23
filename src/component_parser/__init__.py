"""
Component parser for BoxLang files.
Routes to AST parser for .bx/.bxs and tag parser for .bxm files.
"""

import os
from .ast_parser import ASTParser
from .tag_parser import TagParser


def parse_file(file_path):
    """
    Parse a BoxLang file and return component metadata.

    Args:
        file_path: Path to the .bx, .bxs, or .bxm file

    Returns:
        Dictionary with component metadata:
        {
            "name": class name,
            "extends": parent class,
            "implements": list of interfaces,
            "functions": {name: metadata},
            "properties": {name: metadata},
            "annotations": [...],
            "parse_errors": [...]
        }
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".bx", ".bxs"]:
        return ASTParser.parse(file_path)
    elif ext == ".bxm":
        return TagParser.parse(file_path)
    else:
        return {"parse_errors": [f"Unsupported file extension: {ext}"]}


def parse_string(content, file_type="bxs"):
    """
    Parse BoxLang code from a string.

    Args:
        content: BoxLang code string
        file_type: "bx", "bxs", or "bxm"

    Returns:
        Dictionary with component metadata
    """
    if file_type in ["bx", "bxs"]:
        return ASTParser.parse_string(content)
    elif file_type == "bxm":
        return TagParser.parse_string(content)
    else:
        return {"parse_errors": [f"Unsupported file type: {file_type}"]}
