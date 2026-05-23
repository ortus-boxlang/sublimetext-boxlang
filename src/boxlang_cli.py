"""
BoxLang CLI wrapper for version detection, AST parsing, formatting, and compilation.
"""

import os
import subprocess
import json
import threading
import sublime

# Global state
_boxlang_installed = False
_boxlang_version = ""
_boxlang_executable = "boxlang"
_detection_complete = False
_detection_callbacks = []


def initialize():
    """Initialize and detect BoxLang installation."""
    global _boxlang_installed, _boxlang_version, _detection_complete

    # Check settings for custom executable path
    settings = sublime.load_settings("boxlang.sublime-settings")
    custom_path = settings.get("boxlang_executable_path")
    if custom_path:
        global _boxlang_executable
        _boxlang_executable = custom_path

    # Run detection in background thread
    threading.Thread(target=_detect_boxlang, daemon=True).start()


def _detect_boxlang():
    """Detect BoxLang installation by running boxlang --version."""
    global _boxlang_installed, _boxlang_version, _detection_complete

    try:
        result = subprocess.run(
            [_boxlang_executable, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            _boxlang_installed = True
            # Parse version from output like "Ortus BoxLang™ v1.13.0+54"
            version_line = result.stdout.strip().split("\n")[0]
            version_match = _parse_version(version_line)
            _boxlang_version = version_match or version_line
        else:
            _boxlang_installed = False
            _boxlang_version = ""

    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        _boxlang_installed = False
        _boxlang_version = ""

    _detection_complete = True

    # Notify callbacks
    for callback in _detection_callbacks:
        callback(_boxlang_installed, _boxlang_version)


def _parse_version(version_line):
    """Extract version string from BoxLang version output."""
    import re
    match = re.search(r'v?(\d+\.\d+\.\d+(?:\+\d+)?)', version_line)
    return match.group(1) if match else None


def on_detection_complete(callback):
    """Register a callback to be called when detection is complete."""
    if _detection_complete:
        callback(_boxlang_installed, _boxlang_version)
    else:
        _detection_callbacks.append(callback)


def is_installed():
    """Return whether BoxLang is installed and detected."""
    return _boxlang_installed


def get_version():
    """Return the detected BoxLang version string."""
    return _boxlang_version


def get_executable():
    """Return the BoxLang executable path."""
    return _boxlang_executable


def run_ast(file_path, callback=None):
    """
    Run boxlang --bx-printast on a file and return the AST.

    Args:
        file_path: Path to the .bx or .bxs file
        callback: Optional callback function(result, error)

    Returns:
        If callback is None: (ast_dict, error_string) tuple
        If callback provided: runs asynchronously
    """
    def _run():
        try:
            result = subprocess.run(
                [_boxlang_executable, "--bx-printast", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                ast = json.loads(result.stdout)
                if callback:
                    callback(ast, None)
                else:
                    return ast, None
            else:
                error = result.stderr.strip()
                if callback:
                    callback(None, error)
                else:
                    return None, error

        except subprocess.TimeoutExpired:
            error = "BoxLang AST parsing timed out"
            if callback:
                callback(None, error)
            else:
                return None, error
        except json.JSONDecodeError as e:
            error = f"Invalid JSON from BoxLang AST: {e}"
            if callback:
                callback(None, error)
            else:
                return None, error
        except Exception as e:
            error = str(e)
            if callback:
                callback(None, error)
            else:
                return None, error

    if callback:
        threading.Thread(target=_run, daemon=True).start()
    else:
        return _run()


def run_ast_code(code, callback=None):
    """
    Run boxlang --bx-printast --bx-code "code" and return the AST.

    Args:
        code: BoxLang code string to parse
        callback: Optional callback function(result, error)
    """
    def _run():
        try:
            result = subprocess.run(
                [_boxlang_executable, "--bx-printast", "--bx-code", code],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                ast = json.loads(result.stdout)
                if callback:
                    callback(ast, None)
                else:
                    return ast, None
            else:
                error = result.stderr.strip()
                if callback:
                    callback(None, error)
                else:
                    return None, error

        except subprocess.TimeoutExpired:
            error = "BoxLang AST parsing timed out"
            if callback:
                callback(None, error)
            else:
                return None, error
        except json.JSONDecodeError as e:
            error = f"Invalid JSON from BoxLang AST: {e}"
            if callback:
                callback(None, error)
            else:
                return None, error
        except Exception as e:
            error = str(e)
            if callback:
                callback(None, error)
            else:
                return None, error

    if callback:
        threading.Thread(target=_run, daemon=True).start()
    else:
        return _run()


def run_format(file_path, callback=None):
    """
    Run boxlang format on a file.

    Args:
        file_path: Path to file or directory to format
        callback: Optional callback function(success, error)
    """
    def _run():
        try:
            result = subprocess.run(
                [_boxlang_executable, "format", file_path],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                if callback:
                    callback(True, None)
                else:
                    return True, None
            else:
                error = result.stderr.strip() or result.stdout.strip()
                if callback:
                    callback(False, error)
                else:
                    return False, error

        except subprocess.TimeoutExpired:
            error = "BoxLang formatting timed out"
            if callback:
                callback(False, error)
            else:
                return False, error
        except Exception as e:
            error = str(e)
            if callback:
                callback(False, error)
            else:
                return False, error

    if callback:
        threading.Thread(target=_run, daemon=True).start()
    else:
        return _run()


def run_compile(source_path, target_path, callback=None):
    """
    Run boxlang compile.

    Args:
        source_path: Source file or directory
        target_path: Target directory
        callback: Optional callback function(success, error)
    """
    def _run():
        try:
            result = subprocess.run(
                [
                    _boxlang_executable, "compile",
                    "--source", source_path,
                    "--target", target_path
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                if callback:
                    callback(True, None)
                else:
                    return True, None
            else:
                error = result.stderr.strip() or result.stdout.strip()
                if callback:
                    callback(False, error)
                else:
                    return False, error

        except subprocess.TimeoutExpired:
            error = "BoxLang compilation timed out"
            if callback:
                callback(False, error)
            else:
                return False, error
        except Exception as e:
            error = str(e)
            if callback:
                callback(False, error)
            else:
                return False, error

    if callback:
        threading.Thread(target=_run, daemon=True).start()
    else:
        return _run()
