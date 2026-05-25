"""
Flexible tag parser for .bxm template files.
Handles self-closing tags, paired tags, and <bx:script> blocks.
"""
import re
import json
from .. import boxlang_cli
from .ast_parser import ASTParser
SELF_CLOSING_TAGS = {'abort', 'associate', 'break', 'continue', 'dump', 'exit', 'flush', 'httpparam', 'include', 'invokeargument', 'log', 'param', 'procparam', 'procresult', 'queryparam', 'rethrow', 'return', 'schedule', 'setting', 'sleep', 'throw', 'trace', 'zipparam'}
OPTIONAL_BODY_TAGS = {'cache', 'execute', 'http', 'invoke', 'invokeargument', 'object', 'processingdirective', 'thread', 'transaction', 'zip'}
REQUIRED_BODY_TAGS = {'lock', 'loop', 'output', 'query', 'savecontent', 'silent', 'storedproc', 'timer', 'xml'}

class TagParser:
    """Parser for .bxm template files using flexible tag tokenization."""

    @staticmethod
    def parse(file_path):
        """Parse a .bxm file and return component metadata."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'name': None, 'functions': {}, 'properties': {}, 'parse_errors': [str(e)]}
        return TagParser.parse_string(content)

    @staticmethod
    def parse_string(content):
        """Parse .bxm content string and return component metadata."""
        metadata = {'name': None, 'functions': {}, 'properties': {}, 'parse_errors': []}
        tags = TagParser._extract_tags(content)
        for tag in tags:
            tag_name = tag.get('name', '').lower()
            if tag_name == 'function':
                func_meta = TagParser._extract_function_from_tag(tag)
                if func_meta:
                    metadata['functions'][func_meta['name']] = func_meta
            elif tag_name == 'property':
                prop_meta = TagParser._extract_property_from_tag(tag)
                if prop_meta:
                    metadata['properties'][prop_meta['name']] = prop_meta
            elif tag_name == 'script':
                script_content = tag.get('body', '')
                if script_content.strip():
                    script_meta = TagParser._parse_script_block(script_content)
                    if script_meta:
                        for func_name, func_meta in script_meta.get('functions', {}).items():
                            metadata['functions'][func_name] = func_meta
        return metadata

    @staticmethod
    def _extract_tags(content):
        """
        Extract all bx: tags from content.

        Returns a list of dicts with:
        - name: tag name
        - attributes: dict of attribute name -> value
        - body: tag body content (if any)
        - line: line number
        """
        tags = []
        tag_pattern = re.compile('<bx:(\\w+)(\\s[^>]*)?/?>', re.IGNORECASE | re.DOTALL)
        pos = 0
        while pos < len(content):
            match = tag_pattern.search(content, pos)
            if not match:
                break
            tag_name = match.group(1).lower()
            attrs_str = match.group(2) or ''
            is_self_closing = match.group(0).endswith('/>')
            attributes = TagParser._parse_attributes(attrs_str)
            line_num = content[:match.start()].count('\n') + 1
            tag_info = {'name': tag_name, 'attributes': attributes, 'body': None, 'line': line_num}
            if is_self_closing:
                tags.append(tag_info)
                pos = match.end()
            elif tag_name in SELF_CLOSING_TAGS:
                tags.append(tag_info)
                pos = match.end()
            else:
                closing_pattern = re.compile('</bx:{}\\s*>'.format(tag_name), re.IGNORECASE)
                closing_match = closing_pattern.search(content, match.end())
                if closing_match:
                    tag_info['body'] = content[match.end():closing_match.start()]
                    pos = closing_match.end()
                else:
                    pos = match.end()
                tags.append(tag_info)
        return tags

    @staticmethod
    def _parse_attributes(attrs_str):
        """Parse attribute string into a dictionary."""
        attributes = {}
        attr_pattern = re.compile('(\\w[\\w\\-]*)\\s*=\\s*(?:"([^"]*)"|\\\'([^\\\']*)\\\'|(\\S+))', re.IGNORECASE)
        for match in attr_pattern.finditer(attrs_str):
            name = match.group(1).lower()
            value = match.group(2) or match.group(3) or match.group(4) or ''
            attributes[name] = value
        return attributes

    @staticmethod
    def _extract_function_from_tag(tag):
        """Extract function metadata from a bx:function tag."""
        name = tag['attributes'].get('name')
        if not name:
            return None
        return {'name': name, 'return_type': tag['attributes'].get('returntype'), 'access': tag['attributes'].get('access'), 'args': [], 'annotations': [], 'line': tag['line']}

    @staticmethod
    def _extract_property_from_tag(tag):
        """Extract property metadata from a bx:property tag."""
        name = tag['attributes'].get('name')
        if not name:
            return None
        return {'name': name, 'type': tag['attributes'].get('type'), 'access': tag['attributes'].get('access'), 'default': tag['attributes'].get('default'), 'line': tag['line']}

    @staticmethod
    def _parse_script_block(content):
        """Parse a <bx:script> block using the BoxLang AST parser."""
        ast, error = boxlang_cli.run_ast_code(content)
        if error:
            return {'functions': {}}
        functions = {}
        statements = ast.get('statements', [])
        for stmt in statements:
            if stmt.get('ASTType') == 'BoxFunctionDeclaration':
                func_meta = ASTParser._extract_function(stmt)
                functions[func_meta['name']] = func_meta
        return {'functions': functions}