"""
Show which BoxLang the package is using, globally and in the current project.

Works for every install type: BVM, the quick installer (user or system), Homebrew, the
Windows installer, a custom path, or whatever is on PATH. BVM-only details (the global
`bvm current`, a project `.bvmrc`, installed versions) appear only when BVM is present.
"""
import os
import re
import threading
import sublime
import sublime_plugin
from . import boxlang_cli
from . import utils

_PANEL_NAME = 'boxlang_version_info'
_SOURCE_LABELS = {
    'bvm': 'BVM',
    'homebrew': 'Homebrew',
    'quick-user': 'Quick installer (user)',
    'quick-system': 'Quick installer (system)',
    'windows': 'Windows installer',
    'path': 'PATH',
    'other': 'Custom location',
}
_UPGRADE_HINTS = {
    'bvm': 'bvm list-remote, then bvm install latest && bvm use latest',
    'homebrew': 'brew upgrade ortus-boxlang/boxlang/boxlang',
    'quick-user': 'install-boxlang --check-update',
    'quick-system': 'install-boxlang --check-update (use sudo install-boxlang --system to update)',
    'windows': 'install-boxlang --check-update',
}


# ── install detection ─────────────────────────────────────────────────────────

def bvm_home(env=None):
    """Return the BVM home directory when BVM is installed, otherwise None."""
    env = os.environ if env is None else env
    candidate = env.get('BVM_HOME') or os.path.expanduser('~/.bvm')
    return candidate if os.path.isdir(candidate) else None


def classify_install(executable, source, env=None):
    """
    Work out how BoxLang was installed from its executable path.

    Returns (key, label). key is one of bvm, homebrew, quick-user, quick-system,
    windows, path or other.
    """
    env = os.environ if env is None else env
    path = executable.replace('\\', '/')
    real = os.path.realpath(executable).replace('\\', '/') if os.path.exists(executable) else path
    bvm = (env.get('BVM_HOME') or os.path.expanduser('~/.bvm')).replace('\\', '/')
    home = os.path.expanduser('~').replace('\\', '/')
    lowered = path.lower()
    if '/.bvm/' in path or path.startswith(bvm + '/') or real.startswith(bvm + '/'):
        key = 'bvm'
    elif lowered.startswith('/opt/homebrew/') or '/cellar/' in real.lower() or '/homebrew/' in real.lower():
        key = 'homebrew'
    elif re.match(r'^[a-z]:/boxlang', lowered):
        key = 'windows'
    elif path.startswith(home + '/.local/'):
        key = 'quick-user'
    elif path.startswith('/usr/local/'):
        key = 'quick-system'
    elif source == 'path':
        key = 'path'
    else:
        key = 'other'
    return (key, _SOURCE_LABELS[key])


def describe_source(source, key, label):
    """Describe how the executable was chosen, for the report."""
    if source == 'setting':
        return 'boxlang_executable_path setting ({})'.format(label)
    if source == 'path':
        return 'found on PATH ({})'.format(label)
    return label


# ── BVM details (only when BVM exists) ────────────────────────────────────────

def read_bvmrc(start_dir):
    """
    Find the nearest .bvmrc walking up from start_dir.

    Returns (version, path) or None. Comment and empty lines are ignored.
    """
    current = start_dir
    while current:
        candidate = os.path.join(current, '.bvmrc')
        if os.path.isfile(candidate):
            try:
                with open(candidate, encoding='utf-8') as handle:
                    for line in handle:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            return (line, candidate)
            except OSError:
                return None
            return None
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def bvm_current(home):
    """The version `bvm use` activated, read from the `current` link. None when unknown."""
    link = os.path.join(home, 'current')
    if not os.path.exists(link):
        return None
    name = os.path.basename(os.path.realpath(link).rstrip('/\\'))
    return name if re.search(r'\d+\.\d+\.\d+', name) else None


def bvm_installed(home):
    """Installed BVM versions (real directories under versions/), sorted oldest to newest."""
    versions = os.path.join(home, 'versions')
    if not os.path.isdir(versions):
        return []
    names = [name for name in os.listdir(versions) if os.path.isdir(os.path.join(versions, name)) and not os.path.islink(os.path.join(versions, name))]
    return sorted(names, key=lambda name: (boxlang_cli.version_tuple(name) or (0, 0, 0), name))


def bvmrc_mismatch(active_version, bvmrc_version):
    """
    True when a concrete .bvmrc version differs from the active BoxLang version.

    Aliases such as `latest` and `snapshot` cannot be compared, so they never count as a mismatch.
    """
    wanted = boxlang_cli.version_tuple(bvmrc_version)
    active = boxlang_cli.version_tuple(active_version)
    if not wanted or not active:
        return False
    return wanted != active


def status_suffix(file_path, active_version):
    """Short status bar suffix such as ' (.bvmrc 1.17.6)' when a BVM project file differs."""
    try:
        if not file_path or not active_version or not bvm_home():
            return ''
        found = read_bvmrc(os.path.dirname(file_path))
        if found and bvmrc_mismatch(active_version, found[0]):
            return ' (.bvmrc {})'.format(found[0])
    except (OSError, TypeError, AttributeError):
        pass
    return ''


# ── other signals ─────────────────────────────────────────────────────────────

def boxlang_home(env=None):
    """Return (path, source) for BOXLANG_HOME, where source is 'env' or 'default'."""
    env = os.environ if env is None else env
    value = env.get('BOXLANG_HOME')
    if value:
        return (value, 'env')
    return (os.path.expanduser('~/.boxlang'), 'default')


def project_root_for(window, view):
    """Best project folder for the active view or window."""
    file_path = view.file_name() if view else None
    folders = window.folders() if window else []
    if file_path:
        normalized = os.path.normpath(file_path)
        for folder in folders:
            base = os.path.normpath(folder)
            if normalized == base or normalized.startswith(base + os.sep):
                return folder
        return os.path.dirname(file_path)
    return folders[0] if folders else None


# ── report ────────────────────────────────────────────────────────────────────

def collect(project_root=None, env=None):
    """Gather everything the report shows. Runs detection, so call it off the UI thread."""
    installed, version, executable, source = boxlang_cli.redetect()
    key, label = classify_install(executable, source, env)
    info = {
        'installed': installed,
        'version': version,
        'executable': executable,
        'source': source,
        'kind': key,
        'kind_label': label,
        'project_root': project_root,
        'boxlang_home': boxlang_home(env),
        'tried': boxlang_cli.executable_candidates(),
        'project_config': bool(project_root and os.path.isfile(os.path.join(project_root, '.boxlang.json'))),
        'bvm': None,
    }
    home = bvm_home(env)
    if home:
        bvmrc = read_bvmrc(project_root) if project_root else None
        info['bvm'] = {
            'home': home,
            'current': bvm_current(home),
            'installed': bvm_installed(home),
            'bvmrc': bvmrc,
            'mismatch': bool(bvmrc and bvmrc_mismatch(version, bvmrc[0])),
        }
    return info


def format_report(info):
    """Render the collected info as plain text."""
    lines = ['BoxLang Version Info', '=' * 60]
    if not info['installed']:
        lines.append('BoxLang was NOT found or could not run.')
        lines.append('Tried: {}'.format(info['executable']))
        lines.append('')
        lines.append('Standard locations checked:')
        lines.extend('  {}'.format(path) for path in info['tried'])
        lines.append('')
        lines.append('Install BoxLang (https://boxlang.ortusbooks.com/getting-started/installation),')
        lines.append('or set "boxlang_executable_path" in Preferences: BoxLang Settings.')
        lines.append("Sublime Text's PATH can differ from your Terminal's, so a path is the most reliable fix.")
        return '\n'.join(lines)

    supports = boxlang_cli.supports_check()
    lines.append('Version      : {}'.format(info['version'] or 'unknown'))
    lines.append('Executable   : {}'.format(info['executable']))
    lines.append('Source       : {}'.format(describe_source(info['source'], info['kind'], info['kind_label'])))
    lines.append('Features     : syntax check {}'.format('available' if supports else 'unavailable (needs BoxLang 1.17+)'))
    home_path, home_source = info['boxlang_home']
    lines.append('BOXLANG_HOME : {} ({})'.format(home_path, 'from the environment' if home_source == 'env' else 'default, variable not set'))
    lines.append('')
    lines.append('Project      : {}'.format(info['project_root'] or '(no project folder open)'))
    if info['project_root']:
        lines.append('  .boxlang.json : {}'.format('found' if info['project_config'] else 'not found'))
    bvm = info['bvm']
    if bvm:
        lines.append('')
        lines.append('BVM          : {}'.format(bvm['home']))
        lines.append('  Global (bvm current) : {}'.format(bvm['current'] or 'unknown'))
        if bvm['bvmrc']:
            version, path = bvm['bvmrc']
            note = '   <-- differs from the active version, run `bvm use` in the project' if bvm['mismatch'] else ''
            lines.append('  Project (.bvmrc)     : {} ({}){}'.format(version, path, note))
        elif info['project_root']:
            lines.append('  Project (.bvmrc)     : none')
        lines.append('  Installed            : {}'.format(', '.join(bvm['installed']) or 'none found'))
    lines.append('')
    hint = _UPGRADE_HINTS.get(info['kind'])
    if hint:
        lines.append('Upgrade      : {}'.format(hint))
    lines.append("Note         : Sublime Text can have a different PATH than your Terminal. Set")
    lines.append('               "boxlang_executable_path" to pin the exact BoxLang it should use.')
    return '\n'.join(lines)


# ── command ───────────────────────────────────────────────────────────────────

def _show(window, text):
    panel = window.create_output_panel(_PANEL_NAME)
    panel.settings().set('word_wrap', False)
    panel.run_command('append', {'characters': text, 'force': True})
    panel.settings().set('read_only', True)
    window.run_command('show_panel', {'panel': 'output.{}'.format(_PANEL_NAME)})


class BoxlangShowVersionInfoCommand(sublime_plugin.WindowCommand):
    """Show the BoxLang version, executable, install type and project details."""

    def run(self):
        root = project_root_for(self.window, self.window.active_view())
        window = self.window
        sublime.status_message('BoxLang: detecting version...')

        def work():
            try:
                info = collect(root)
                text = format_report(info)
            except Exception as exc:
                info, text = None, 'Could not collect version info: {}'.format(exc)

            def finish():
                _show(window, text)
                if info:
                    from . import status_bar
                    status_bar._update_all_status_bars()
                    sublime.status_message('BoxLang: {}'.format('v' + info['version'] if info['installed'] else 'not found'))

            sublime.set_timeout(finish)

        threading.Thread(target=work, daemon=True).start()
