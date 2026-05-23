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
from .. import utils
from ..component_parser import parse_file
from .. import boxlang_cli

# Global index state
project_indexes = {}
indexing_in_progress = {}


def get_indexed_metadata(project_name, dot_path):
    """Get metadata for an indexed component by dot path."""
    if project_name not in project_indexes:
        return None
    return project_indexes[project_name].get(dot_path)


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

    mappings = project_data.get("mappings", [])
    if not mappings:
        return None

    # Convert dot path to file path
    file_path = dot_path.replace(".", "/") + ".bx"

    # Try each mapping
    for mapping in mappings:
        mapping_path = utils.normalize_mapping(mapping, project_name)["path"]
        mapping_prefix = mapping["mapping"]

        if file_path.startswith(mapping_prefix.lstrip("/")):
            rel_path = file_path[len(mapping_prefix.lstrip("/")):]
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

    # Get project data
    project_data = _get_project_data(project_name)
    if not project_data:
        indexing_in_progress[project_name] = False
        return

    # Get configured folders
    cfc_folders = project_data.get("boxlang_cfc_folders", [])
    if not cfc_folders:
        # Try to get from settings
        cfc_folders = utils.get_setting("boxlang_cfc_folders") or []

    # Collect all files to index
    files_to_index = []
    for folder_config in cfc_folders:
        folder_path = utils.normalize_path(folder_config["path"], project_name)
        if os.path.isdir(folder_path):
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    if f.endswith((".bx", ".bxs")):
                        files_to_index.append(os.path.join(root, f))

    total = len(files_to_index)
    indexed = 0

    def _index_files():
        nonlocal indexed

        for file_path in files_to_index:
            if not indexing_in_progress.get(project_name, False):
                break

            metadata = parse_file(file_path)

            # Calculate dot path
            dot_path = _file_to_dot_path(file_path, project_name, project_data)
            if dot_path:
                project_indexes[project_name][dot_path] = metadata

            indexed += 1
            if callback:
                callback(indexed, total)

        indexing_in_progress[project_name] = False

    threading.Thread(target=_index_files, daemon=True).start()


def _file_to_dot_path(file_path, project_name, project_data):
    """Convert a file path to a dotted path using project mappings."""
    mappings = project_data.get("mappings", [])

    for mapping in mappings:
        mapping_path = utils.normalize_mapping(mapping, project_name)["path"]
        mapping_prefix = mapping["mapping"]

        if file_path.startswith(mapping_path):
            rel_path = file_path[len(mapping_path):].lstrip("/")
            dot_path = mapping_prefix.rstrip("/") + "/" + rel_path.replace("/", ".")
            # Remove extension
            if dot_path.endswith(".bx"):
                dot_path = dot_path[:-3]
            elif dot_path.endswith(".bxs"):
                dot_path = dot_path[:-4]
            return dot_path

    return None


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
            sublime.status_message("BoxLang: No project file found")
            return

        sublime.status_message("BoxLang: Indexing project...")

        def progress_callback(indexed, total):
            sublime.status_message(f"BoxLang: Indexing {indexed}/{total} files")
            if indexed == total:
                sublime.status_message(f"BoxLang: Indexing complete ({total} files)")

        index_project(project_name, callback=progress_callback)
