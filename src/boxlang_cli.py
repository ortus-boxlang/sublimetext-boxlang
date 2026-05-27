"""
BoxLang CLI wrapper for version detection, AST parsing, formatting, and compilation.
"""
import os
import subprocess
import json
import threading
import locale
from . import process
from . import utils
_boxlang_installed = False
_boxlang_version = ''
_boxlang_executable = 'boxlang'
_detection_complete = False
_detection_callbacks = []
JSON_DECODE_ERROR = getattr(json, 'JSONDecodeError', ValueError)


def _decode_output(output):
    """Decode subprocess output across UTF-8 and platform-local encodings."""
    encodings = ['utf-8']
    preferred_encoding = locale.getpreferredencoding(False)
    if preferred_encoding and preferred_encoding.lower() not in encodings:
        encodings.append(preferred_encoding)
    for encoding in ('cp1252', 'latin-1'):
        if encoding not in encodings:
            encodings.append(encoding)
    for encoding in encodings:
        try:
            return output.decode(encoding)
        except UnicodeDecodeError:
            continue
    return output.decode('utf-8', 'replace')

def _find_boxlang_executable():
    """Find BoxLang executable in common locations."""
    custom_path = utils.get_setting('boxlang_executable_path')
    if custom_path:
        return custom_path
    candidates = [os.path.expanduser('~/.bvm/current/bin/boxlang'), '/usr/local/bin/boxlang', os.path.expanduser('~/.local/bin/boxlang'), '/usr/local/boxlang/bin/boxlang', os.path.expanduser('~/.local/boxlang/bin/boxlang'), 'c:\\boxlang\\bin\\boxlang.bat', os.path.expandvars('${USERPROFILE}\\.local\\bin\\boxlang.bat')]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return 'boxlang'

def initialize():
    """Initialize and detect BoxLang installation."""
    global _boxlang_installed, _boxlang_version, _boxlang_executable, _detection_complete
    _boxlang_executable = _find_boxlang_executable()
    threading.Thread(target=_detect_boxlang, daemon=True).start()

def _run_command(args, timeout=30):
    """Run a subprocess command compatible with Python 3.3."""
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=process.get_startupinfo(),
        creationflags=process.get_creationflags()
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return proc.returncode, _decode_output(stdout), _decode_output(stderr)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        raise

def _detect_boxlang():
    """Detect BoxLang installation by running boxlang --version."""
    global _boxlang_installed, _boxlang_version, _detection_complete
    try:
        returncode, stdout, stderr = _run_command([_boxlang_executable, '--version'], timeout=10)
        if returncode == 0 and stdout.strip():
            _boxlang_installed = True
            version_line = stdout.strip().split('\n')[0]
            version_match = _parse_version(version_line)
            _boxlang_version = version_match or version_line
        else:
            _boxlang_installed = False
            _boxlang_version = ''
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        _boxlang_installed = False
        _boxlang_version = ''
    _detection_complete = True
    for callback in _detection_callbacks:
        callback(_boxlang_installed, _boxlang_version)

def _parse_version(version_line):
    """Extract version string from BoxLang version output."""
    import re
    match = re.search('v?(\\d+\\.\\d+\\.\\d+(?:\\+\\d+)?)', version_line)
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
            returncode, stdout, stderr = _run_command([_boxlang_executable, '--bx-printast', file_path], timeout=30)
            if returncode == 0:
                ast = json.loads(stdout)
                if callback:
                    callback(ast, None)
                else:
                    return (ast, None)
            else:
                error = stderr.strip()
                if callback:
                    callback(None, error)
                else:
                    return (None, error)
        except subprocess.TimeoutExpired:
            error = 'BoxLang AST parsing timed out'
            if callback:
                callback(None, error)
            else:
                return (None, error)
        except JSON_DECODE_ERROR as e:
            error = 'Invalid JSON from BoxLang AST: {}'.format(e)
            if callback:
                callback(None, error)
            else:
                return (None, error)
        except Exception as e:
            error = str(e)
            if callback:
                callback(None, error)
            else:
                return (None, error)
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
            returncode, stdout, stderr = _run_command([_boxlang_executable, '--bx-printast', '--bx-code', code], timeout=30)
            if returncode == 0:
                ast = json.loads(stdout)
                if callback:
                    callback(ast, None)
                else:
                    return (ast, None)
            else:
                error = stderr.strip()
                if callback:
                    callback(None, error)
                else:
                    return (None, error)
        except subprocess.TimeoutExpired:
            error = 'BoxLang AST parsing timed out'
            if callback:
                callback(None, error)
            else:
                return (None, error)
        except JSON_DECODE_ERROR as e:
            error = 'Invalid JSON from BoxLang AST: {}'.format(e)
            if callback:
                callback(None, error)
            else:
                return (None, error)
        except Exception as e:
            error = str(e)
            if callback:
                callback(None, error)
            else:
                return (None, error)
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
            returncode, stdout, stderr = _run_command([_boxlang_executable, 'format', file_path], timeout=60)
            if returncode == 0:
                if callback:
                    callback(True, None)
                else:
                    return (True, None)
            else:
                error = stderr.strip() or stdout.strip()
                if callback:
                    callback(False, error)
                else:
                    return (False, error)
        except subprocess.TimeoutExpired:
            error = 'BoxLang formatting timed out'
            if callback:
                callback(False, error)
            else:
                return (False, error)
        except Exception as e:
            error = str(e)
            if callback:
                callback(False, error)
            else:
                return (False, error)
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
            returncode, stdout, stderr = _run_command([_boxlang_executable, 'compile', '--source', source_path, '--target', target_path], timeout=120)
            if returncode == 0:
                if callback:
                    callback(True, None)
                else:
                    return (True, None)
            else:
                error = stderr.strip() or stdout.strip()
                if callback:
                    callback(False, error)
                else:
                    return (False, error)
        except subprocess.TimeoutExpired:
            error = 'BoxLang compilation timed out'
            if callback:
                callback(False, error)
            else:
                return (False, error)
        except Exception as e:
            error = str(e)
            if callback:
                callback(False, error)
            else:
                return (False, error)
    if callback:
        threading.Thread(target=_run, daemon=True).start()
    else:
        return _run()
