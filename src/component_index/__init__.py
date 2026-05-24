"""
Component index for BoxLang files.
Indexes all .bx files in configured project folders.
"""
import os
import time
import threading
import sqlite3
import hashlib
import json
import sublime
import sublime_plugin
from .. import utils
from ..component_parser import parse_file
from .. import boxlang_cli
project_indexes = {}
indexing_in_progress = {}

def get_indexed_metadata(project_name, dot_path):
    """Get metadata for an indexed component by dot path."""
    if project_name not in project_indexes:
        return None
    return project_indexes[project_name].get(dot_path)

def get_indexed_metadata_by_dotpath(dot_path):
    """Get metadata for an indexed component by dot path, searching all projects."""
    for project_name, index in project_indexes.items():
        metadata = index.get(dot_path)
        if metadata:
            return metadata
        for key, value in index.items():
            if key.lower() == dot_path.lower():
                return value
    return None

def get_all_indexed(project_name):
    """Get all indexed components for a project."""
    if project_name not in project_indexes:
        return {}
    return project_indexes[project_name]

def resolve_path(project_name, current_file_path, dot_path):
    """
    Resolve a dotted path to a file path using project mappings.

    Args:
        project_name: The project file path
        current_file_path: The current file's path
        dot_path: The dotted path to resolve (e.g., "model.UserService")

    Returns:
        Resolved file path or None
    """
    project_data = _get_project_data(project_name)
    if not project_data:
        return None
    mappings = project_data.get('mappings', [])
    if not mappings:
        return None
    file_path = dot_path.replace('.', '/') + '.bx'
    for mapping in mappings:
        mapping_path = utils.normalize_mapping(mapping, project_name)['path']
        mapping_prefix = mapping['mapping']
        if file_path.startswith(mapping_prefix.lstrip('/')):
            rel_path = file_path[len(mapping_prefix.lstrip('/')):]
            full_path = utils.normalize_path(mapping_path + rel_path)
            if os.path.isfile(full_path):
                return full_path
    return None

def index_project(project_name, callback=None):
    """
    Index all .bx files in a project.

    Args:
        project_name: The project file path
        callback: Optional callback(indexed_count, total_count) for progress
    """
    if indexing_in_progress.get(project_name, False):
        return
    indexing_in_progress[project_name] = True
    project_indexes[project_name] = {}
    project_data = _get_project_data(project_name)
    if not project_data:
        indexing_in_progress[project_name] = False
        return
    class_folders = project_data.get('boxlang_class_folders', [])
    if not class_folders:
        class_folders = utils.get_setting('boxlang_class_folders') or []
    files_to_index = []
    for folder_config in class_folders:
        folder_path = utils.normalize_path(folder_config['path'], project_name)
        if os.path.isdir(folder_path):
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    if f.endswith(('.bx', '.bxs')):
                        files_to_index.append(os.path.join(root, f))
    total = len(files_to_index)
    indexed = 0

    def _index_files():
        nonlocal indexed
        for file_path in files_to_index:
            if not indexing_in_progress.get(project_name, False):
                break
            metadata = parse_file(file_path)
            dot_path = _file_to_dot_path(file_path, project_name, project_data)
            if dot_path:
                project_indexes[project_name][dot_path] = metadata
            indexed += 1
            if callback:
                callback(indexed, total)
            try:
                from .. import status_bar
                status_bar.set_indexing_progress(project_name, indexed, total)
            except Exception:
                pass
        indexing_in_progress[project_name] = False
    threading.Thread(target=_index_files, daemon=True).start()

def _file_to_dot_path(file_path, project_name, project_data):
    """Convert a file path to a dotted path using project mappings."""
    mappings = project_data.get('mappings', [])
    for mapping in mappings:
        mapping_path = utils.normalize_mapping(mapping, project_name)['path']
        mapping_prefix = mapping['mapping']
        if file_path.startswith(mapping_path):
            rel_path = file_path[len(mapping_path):].lstrip('/')
            dot_path = mapping_prefix.rstrip('/') + '/' + rel_path.replace('/', '.')
            if dot_path.endswith('.bx'):
                dot_path = dot_path[:-3]
            elif dot_path.endswith('.bxs'):
                dot_path = dot_path[:-4]
            return dot_path
    return None

def get_dot_paths(project_name):
    """Get all dot paths for a project."""
    if project_name not in project_indexes:
        return {}
    result = {}
    for dot_path, metadata in project_indexes[project_name].items():
        result[dot_path.lower()] = {'dot_path': dot_path, 'file_path': _dot_path_to_file(project_name, dot_path), 'metadata': metadata}
    return result

def get_completions_by_file_path(project_name, file_path):
    """Get completions for a component by file path."""
    if project_name not in project_indexes:
        return {}
    for dot_path, metadata in project_indexes[project_name].items():
        file_from_path = _dot_path_to_file(project_name, dot_path)
        if file_from_path == file_path:
            return _build_completions(metadata, dot_path)
    return {}

def get_completions_by_dot_path(project_name, dot_path):
    """Get completions for a component by dot path."""
    if project_name not in project_indexes:
        return None
    metadata = project_indexes[project_name].get(dot_path)
    if metadata:
        return _build_completions(metadata, dot_path)
    return None

def get_extended_metadata_by_file_path(project_name, file_path):
    """Get extended metadata (with inherited functions) for a file path."""
    if project_name not in project_indexes:
        return None
    for dot_path, metadata in project_indexes[project_name].items():
        file_from_path = _dot_path_to_file(project_name, dot_path)
        if file_from_path == file_path:
            return _extend_metadata(metadata, project_name)
    return None

def _dot_path_to_file(project_name, dot_path):
    """Convert a dot path to a file path."""
    project_data = _get_project_data(project_name)
    if not project_data:
        return None
    mappings = project_data.get('mappings', [])
    for mapping in mappings:
        mapping_path = utils.normalize_mapping(mapping, project_name)['path']
        mapping_prefix = mapping['mapping']
        if dot_path.startswith(mapping_prefix.lstrip('/')):
            rel_path = dot_path[len(mapping_prefix.lstrip('/')):]
            return utils.normalize_path(mapping_path + '/' + rel_path.replace('.', '/') + '.bx')
    return None

def _build_completions(metadata, dot_path):
    """Build completion items from component metadata."""
    completions = {'functions': [], 'constructor': None, 'dot_path': dot_path}
    functions = metadata.get('functions', {})
    for func_name, func_meta in functions.items():
        args = func_meta.get('args', [])
        arg_str = ', '.join([a.get('name', '') for a in args])
        return_type = func_meta.get('return_type', '')
        hint = '({})'.format(arg_str) + (': {}'.format(return_type) if return_type else '')
        snippet_args = ', '.join(['${{{}:{}}}'.format(i + 1, a.get('name', '')) for i, a in enumerate(args)])
        content = '{}({})$0'.format(func_name, snippet_args)
        completions['functions'].append({'key': func_name, 'hint': hint, 'content': content, 'private': func_meta.get('access') == 'private', 'return_type': return_type, 'args': args})
    init_func = functions.get('init') or functions.get('new')
    if init_func:
        args = init_func.get('args', [])
        snippet_args = ', '.join(['${{{}:{}}}'.format(i + 1, a.get('name', '')) for i, a in enumerate(args)])
        completions['constructor'] = type('obj', (object,), {'content': '({})$0'.format(snippet_args)})()
    return completions

def _extend_metadata(metadata, project_name):
    """Extend metadata with inherited functions from parent class."""
    extended = dict(metadata)
    extends = metadata.get('extends')
    if extends:
        parent_file = resolve_path(project_name, None, extends)
        if parent_file:
            parent_meta = get_extended_metadata_by_file_path(project_name, parent_file)
            if parent_meta:
                parent_functions = parent_meta.get('functions', {})
                child_functions = extended.get('functions', {})
                merged = dict(parent_functions)
                merged.update(child_functions)
                extended['functions'] = merged
    return extended

def _get_project_data(project_name):
    """Get project data from the project file."""
    for window in sublime.windows():
        if window.project_file_name():
            if utils.normalize_path(window.project_file_name()) == project_name:
                return window.project_data()
    return None

class BoxlangIndexProjectCommand(sublime_plugin.WindowCommand):
    """Command to index the active project."""

    def run(self):
        project_name = utils.get_project_name_from_window(self.window)
        if not project_name:
            sublime.status_message('BoxLang: No project file found')
            return
        sublime.status_message('BoxLang: Indexing project...')

        def progress_callback(indexed, total):
            sublime.status_message('BoxLang: Indexing {}/{} files'.format(indexed, total))
            if indexed == total:
                sublime.status_message('BoxLang: Indexing complete ({} files)'.format(total))
        index_project(project_name, callback=progress_callback)