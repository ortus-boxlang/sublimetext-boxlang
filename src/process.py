"""
Subprocess helpers for running CLI tools without flashing consoles on Windows.
"""
import subprocess
import sys


def get_startupinfo():
    """Return Windows startupinfo that hides console windows."""
    if sys.platform != 'win32':
        return None

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo


def get_creationflags():
    """Return Windows creation flags that suppress console windows."""
    if sys.platform != 'win32':
        return 0
    return getattr(subprocess, 'CREATE_NO_WINDOW', 0)
