#!/usr/bin/env python3
"""
Local smoke test for the BoxLang Sublime Text package.

Runs the package's own CLI integration against a REAL BoxLang (and optionally TestBox)
install, so you can confirm everything works before trying it inside Sublime Text.

Usage:
    python3 scripts/local_smoke_test.py
    python3 scripts/local_smoke_test.py --boxlang ~/.bvm/current/bin/boxlang
    python3 scripts/local_smoke_test.py --testbox /path/to/testbox
    python3 scripts/local_smoke_test.py --http-url http://localhost:8080/tests/runner.bxm
    python3 scripts/local_smoke_test.py --install     # symlink the package into Sublime Text

What it checks:
    1. Static files: JSON, snippet XML, Python compiles, the unit test suite
    2. BoxLang is installed and is 1.17+
    3. `boxlang check` JSON output is parsed correctly (valid and invalid files)
    4. The build-variant file_regex matches real `boxlang check` text output
    5. The TestBox BoxLang runner produces a JSON report the package can parse
       (needs TestBox 7+: pass --testbox or run from a project that has ./testbox)
    6. (optional) A web runner returns JSON the package can parse

Exit code is 1 when any step fails. Skipped steps do not fail the run.
"""

import argparse
import ast
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import xml.dom.minidom
from unittest.mock import MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = {'pass': 0, 'fail': 0, 'skip': 0}

GOOD_SOURCE = 'x = 1\nwriteOutput( x )\n'
BAD_SOURCE = 'if ( true {\n    x = 1\n}\n'
SPEC_SOURCE = '''class extends="testbox.system.BaseSpec" {

	function run() {
		describe( "Smoke", () => {
			it( "passes", () => {
				expect( 1 + 1 ).toBe( 2 )
			} )
			it( "fails", () => {
				expect( 1 + 1 ).toBe( 3 )
			} )
		} )
	}

}
'''


# ── output helpers ────────────────────────────────────────────────────────────

def report(status, name, detail=''):
    RESULTS[status] += 1
    label = {'pass': 'PASS', 'fail': 'FAIL', 'skip': 'SKIP'}[status]
    print('[{}] {}'.format(label, name))
    if detail:
        for line in str(detail).strip().splitlines():
            print('       {}'.format(line))


def check(name, condition, detail=''):
    report('pass' if condition else 'fail', name, '' if condition else detail)
    return bool(condition)


def section(title):
    print('\n== {} =='.format(title))


# ── stub the sublime module so the package's CLI code can be imported ─────────

class FakeSettings(object):
    def __init__(self, values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)


def install_sublime_stubs(settings):
    sublime = MagicMock()
    sublime.load_settings = lambda name: FakeSettings(settings)
    sublime.status_message = lambda message: None
    sublime_plugin = types.ModuleType('sublime_plugin')
    for name in ('EventListener', 'TextCommand', 'WindowCommand', 'ApplicationCommand', 'ViewEventListener'):
        setattr(sublime_plugin, name, object)
    sys.modules['sublime'] = sublime
    sys.modules['sublime_plugin'] = sublime_plugin


# ── step 1: static checks ─────────────────────────────────────────────────────

def static_checks():
    section('1. Static files and unit tests')
    bad = []
    for path in glob.glob(os.path.join(ROOT, '**', '*.py'), recursive=True):
        if os.sep + '.git' + os.sep in path or '__pycache__' in path:
            continue
        try:
            with open(path, encoding='utf-8') as handle:
                compile(handle.read(), path, 'exec')
        except SyntaxError as exc:
            bad.append('{}: {}'.format(path, exc))
    check('All Python files compile', not bad, '\n'.join(bad))

    bad = []
    for path in glob.glob(os.path.join(ROOT, 'snippets', '*.sublime-snippet')) + glob.glob(os.path.join(ROOT, 'skeletons', '*.sublime-snippet')):
        try:
            xml.dom.minidom.parse(path)
        except Exception as exc:
            bad.append('{}: {}'.format(os.path.basename(path), exc))
    check('All snippet XML files parse', not bad, '\n'.join(bad))

    bad = []
    json_files = [os.path.join(ROOT, name) for name in ('messages.json', 'version.json')]
    json_files += glob.glob(os.path.join(ROOT, 'commands', '*.sublime-commands'))
    json_files += glob.glob(os.path.join(ROOT, 'src', 'plugins_', 'basecompletions', 'json', '*.json'))
    for path in json_files:
        try:
            with open(path, encoding='utf-8') as handle:
                json.load(handle)
        except Exception as exc:
            bad.append('{}: {}'.format(os.path.basename(path), exc))
    for name in ('BoxLang.sublime-settings', 'BoxLang.sublime-build'):
        try:
            with open(os.path.join(ROOT, name), encoding='utf-8') as handle:
                json.loads(re.sub(r'(?m)^\s*//.*$', '', handle.read()))
        except Exception as exc:
            bad.append('{}: {}'.format(name, exc))
    check('JSON, settings and command files parse', not bad, '\n'.join(bad))

    try:
        import yaml
        with open(os.path.join(ROOT, 'syntaxes', 'BoxLang.sublime-syntax'), encoding='utf-8') as handle:
            yaml.safe_load(handle)
        check('Syntax definition parses as YAML', True)
    except ImportError:
        report('skip', 'Syntax definition YAML check', 'PyYAML not installed (pip install pyyaml)')
    except Exception as exc:
        check('Syntax definition parses as YAML', False, exc)

    try:
        import pytest  # noqa: F401
    except ImportError:
        report('skip', 'Unit test suite', 'pytest not installed (pip install pytest pytest-mock)')
        return
    proc = subprocess.run([sys.executable, '-m', 'pytest', 'tests', '-q'], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    tail = '\n'.join(proc.stdout.strip().splitlines()[-5:])
    check('Unit test suite passes', proc.returncode == 0, tail)


# ── step 2: BoxLang install ───────────────────────────────────────────────────

def find_boxlang(explicit):
    if explicit:
        return explicit
    on_path = shutil.which('boxlang')
    if on_path:
        return on_path
    for candidate in (os.path.expanduser('~/.bvm/current/bin/boxlang'), '/usr/local/bin/boxlang', os.path.expanduser('~/.local/bin/boxlang')):
        if os.path.isfile(candidate):
            return candidate
    return None


def boxlang_checks(boxlang_cli, executable):
    section('2. BoxLang install')
    if not executable:
        report('fail', 'BoxLang executable found', 'Not on PATH. Install with `bvm install latest && bvm use latest` or pass --boxlang PATH')
        return False
    boxlang_cli._boxlang_executable = executable
    try:
        raw = subprocess.run([executable, '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        raw = ''
    noise = [line for line in raw.splitlines() if re.match(r'^\s*\[\d+(?:\.\d+)?s\]\[', line)]
    if noise:
        report('skip', 'JVM printed warnings before the BoxLang version (the package skips them)', '\n'.join(noise) + '\nThis usually means BoxLang is starting on a different JDK than it was built for. Check JAVA_HOME and `java -version`.')
    boxlang_cli._detect_boxlang()
    version = boxlang_cli.get_version()
    check('BoxLang runs (`boxlang --version`)', boxlang_cli.is_installed(), 'Could not run {}'.format(executable))
    print('       using {} (version {})'.format(executable, version or 'unknown'))
    try:
        from src import version_info
        print('       --- what `BoxLang: Show Version Info` will show ---')
        print(version_info.format_report(version_info.collect(os.getcwd())).replace('\n', '\n       '))
    except Exception as exc:
        report('fail', 'Version info report', exc)
    return check('BoxLang is 1.17.0 or newer (required for `boxlang check`)', boxlang_cli.supports_check(), 'Found {}. Upgrade the BoxLang you use (bvm install latest, or install-boxlang --force)'.format(version))


# ── steps 3 and 4: boxlang check ──────────────────────────────────────────────

def build_file_regex():
    """Read the file_regex constant from boxlang_build.py without importing it."""
    with open(os.path.join(ROOT, 'boxlang_build.py'), encoding='utf-8') as handle:
        tree = ast.parse(handle.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', '') == '_CHECK_FILE_REGEX' for t in node.targets):
            return ast.literal_eval(node.value)
    return None


def run_text(executable, args, cwd=None):
    proc = subprocess.run([executable] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=120)
    return proc.returncode, proc.stdout


def check_command_tests(boxlang_cli, executable):
    section('3. `boxlang check` JSON integration')
    workdir = tempfile.mkdtemp(prefix='boxlang_smoke_')
    try:
        good = os.path.join(workdir, 'good.bxs')
        bad = os.path.join(workdir, 'bad.bxs')
        with open(good, 'w') as handle:
            handle.write(GOOD_SOURCE)
        with open(bad, 'w') as handle:
            handle.write(BAD_SOURCE)

        issues, error = boxlang_cli.run_check(good)
        check('Valid file reports no issues', error is None and issues == [], 'issues={!r} error={!r}'.format(issues, error))

        issues, error = boxlang_cli.run_check(bad)
        check('Invalid file reports at least one issue', error is None and bool(issues), 'issues={!r} error={!r}'.format(issues, error))
        if issues:
            first = issues[0]
            check('Issue has message, line and column', all(key in first for key in ('message', 'line', 'column')), json.dumps(first))
            print('       first issue: line {} col {}: {}'.format(first.get('line'), first.get('column'), str(first.get('message', '')).splitlines()[0]))

        section('4. Build variant file_regex against real text output')
        pattern = build_file_regex()
        check('file_regex constant found in boxlang_build.py', bool(pattern))
        if pattern:
            code, output = run_text(executable, ['check', bad])
            matches = [m for line in output.splitlines() for m in [re.match(pattern, line)] if m]
            check('`boxlang check` exits 1 for a bad file', code == 1, 'exit code {}'.format(code))
            check('file_regex matches the error line (file, line, col, message)', bool(matches), output)
            code, output = run_text(executable, ['check', '--source', workdir])
            matches = [re.match(pattern, line) for line in output.splitlines()]
            check('Project check (--source) output also matches', any(matches), output)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ── step 5: TestBox ───────────────────────────────────────────────────────────

def find_testbox(explicit):
    candidates = [explicit] if explicit else []
    candidates += [os.path.join(os.getcwd(), 'testbox'), os.path.expanduser('~/testbox')]
    for candidate in candidates:
        if candidate and os.path.isfile(os.path.join(candidate, 'system', 'runners', 'BoxLangRunner.bx')):
            return os.path.abspath(candidate)
    return None


def testbox_checks(boxlang_cli, testbox_runner, testbox_path):
    section('5. TestBox BoxLang runner')
    if not testbox_path:
        report('skip', 'TestBox runner', 'TestBox 7+ not found. Pass --testbox /path/to/testbox (box install testbox, or git clone ortus-solutions/testbox)')
        return
    runner = os.path.join(testbox_path, 'system', 'runners', 'BoxLangRunner.bx')
    print('       using {}'.format(runner))
    project = tempfile.mkdtemp(prefix='boxlang_smoke_project_')
    try:
        specs = os.path.join(project, 'tests', 'specs')
        os.makedirs(specs)
        spec_file = os.path.join(specs, 'SmokeTest.bx')
        with open(spec_file, 'w') as handle:
            handle.write(SPEC_SOURCE)
        bundle = testbox_runner.bundle_dot_path(spec_file, project)
        check('Bundle dot path is derived from the file path', bundle == 'tests.specs.SmokeTest', bundle)

        offset = SPEC_SOURCE.index('expect( 1 + 1 ).toBe( 3 )')
        check('Spec at cursor is found', testbox_runner.find_target_at(SPEC_SOURCE, offset) == ('spec', 'fails'))

        settings = testbox_runner.get_testbox_settings()
        exe = boxlang_cli.get_executable()

        def run(target):
            report_dir = tempfile.mkdtemp(prefix='boxlang_smoke_report_')
            try:
                args = testbox_runner.build_cli_args(runner, report_dir, settings, bundle=bundle, target=target)
                return testbox_runner.run_cli(exe, args, project, 180, report_dir)
            finally:
                shutil.rmtree(report_dir, ignore_errors=True)

        memento, output, error = run(None)
        if not check('Runner wrote a parsable JSON report (--write-json-report)', memento is not None and error is None, '{}\n{}'.format(error, (output or '')[-1500:])):
            print('       If the report is missing, your TestBox may predate --write-json-report. Upgrade TestBox.')
            return
        results = testbox_runner.parse_results(memento, project)
        totals = results['totals']
        check('Totals: 1 passed, 1 failed', totals['pass'] == 1 and totals['fail'] == 1, json.dumps(totals))
        check('One failure is reported for the "fails" spec', len(results['failures']) == 1 and 'fails' in results['failures'][0]['spec'], json.dumps(results['failures']))
        if results['failures']:
            failure = results['failures'][0]
            print('       failure: {}:{} {}'.format(failure['file'] or '(no origin)', failure['line'], failure['message']))
            if failure['file']:
                check('Failure origin points at the spec file', os.path.basename(failure['file']) == 'SmokeTest.bx', failure['file'])
            else:
                report('skip', 'Failure origin file', 'TestBox gave no failOrigin for this engine; inline annotation would be skipped')
        print(testbox_runner.format_report(results, bundle).replace('\n', '\n       '))

        memento, output, error = run(('spec', 'passes'))
        if check('Single spec run (--filter-specs) works', memento is not None, '{}\n{}'.format(error, (output or '')[-800:])):
            totals = testbox_runner.parse_results(memento, project)['totals']
            check('Only the "passes" spec ran', totals['pass'] == 1 and totals['fail'] == 0, json.dumps(totals))
    finally:
        shutil.rmtree(project, ignore_errors=True)


# ── step 6: web runner ────────────────────────────────────────────────────────

def http_checks(testbox_runner, url):
    section('6. Web runner')
    if not url:
        report('skip', 'Web runner', 'Pass --http-url http://localhost:8080/tests/runner.bxm to test one (the server must be running)')
        return
    full_url = testbox_runner.build_http_url(url, testbox_runner.get_testbox_settings())
    print('       GET {}'.format(full_url))
    try:
        memento, error = testbox_runner.run_http(full_url, 300)
    except Exception as exc:
        report('fail', 'Web runner request', exc)
        return
    if check('Web runner returned JSON', memento is not None, error):
        results = testbox_runner.parse_results(memento)
        print('       {}'.format(json.dumps(results['totals'])))
        check('Result parsed into totals', results['totals']['specs'] > 0, 'No specs ran. Check the directory setting and runner URL.')


# ── optional: install into Sublime Text ───────────────────────────────────────

def sublime_packages_dir():
    if sys.platform == 'darwin':
        return os.path.expanduser('~/Library/Application Support/Sublime Text/Packages')
    if sys.platform.startswith('win'):
        return os.path.join(os.environ.get('APPDATA', ''), 'Sublime Text', 'Packages')
    return os.path.expanduser('~/.config/sublime-text/Packages')


def install_package():
    section('Install into Sublime Text')
    packages = sublime_packages_dir()
    target = os.path.join(packages, 'BoxLang')
    if not os.path.isdir(packages):
        report('fail', 'Sublime Text Packages folder', 'Not found at {}. Open Sublime Text once, or use Preferences > Browse Packages.'.format(packages))
        return
    if os.path.lexists(target):
        report('skip', 'Install', '{} already exists. Remove it first if you want to relink.'.format(target))
        return
    try:
        os.symlink(ROOT, target, target_is_directory=True)
        report('pass', 'Linked package', '{} -> {}'.format(target, ROOT))
    except OSError as exc:
        report('fail', 'Link package', '{}\nCopy the folder manually to {}'.format(exc, target))


MANUAL_CHECKLIST = '''
== Manual checks in Sublime Text 4 ==
Open a BoxLang project, then:
  1. Save a .bxs file containing `if ( true {`
       -> squiggle, red dot in the gutter, inline message at the end of the line,
          error panel, "BoxLang: 1 error(s)" in the status bar. F4 / Shift+F4 jump between errors.
          Hover the gutter dot for the full message.
  2. Fix the file and save   -> everything clears and the panel closes.
  3. Command Palette: "BoxLang: Check Syntax", then "BoxLang: Check Project"
  4. Tools > Build With > "BoxLang: Check Syntax" / "BoxLang: Check Project"; click an error line.
  5. Settings: set "boxlang_check_on_type": true, type a syntax error, wait one second
       -> underline appears without the panel opening.
  6. In a TestBox spec: "BoxLang: TestBox Run Spec at Cursor", "Run Bundle", "Run All Tests", "Run Last"
       -> output panel with clickable file:line failures, plus an inline message on the failing line.
  7. Per-project web runner: in your .sublime-project add
       "settings": { "boxlang_testbox": { "http_runner_url": "http://localhost:8080/tests/runner.bxm" } }
       and run any TestBox command again -> it should now run over HTTP.
  8. "BoxLang: Go to TestBox Spec or Suite" and "BoxLang: Go to Property" in a spec / class file.
  9. Type `setNew(`, `dateSetYear(`, `schedulerNew(` -> completions and built-in highlighting.
 10. Snippets: bxset, bxrange, bxlocalclass, bxscheduler, bxtask (Tab to expand).
Sublime console (View > Show Console) should show no tracebacks mentioning the BoxLang package.
'''


def main():
    parser = argparse.ArgumentParser(description='Local smoke test for the BoxLang Sublime Text package')
    parser.add_argument('--boxlang', help='Path to the boxlang executable (default: PATH, then ~/.bvm)')
    parser.add_argument('--testbox', help='Path to a TestBox 7+ checkout or install (the folder containing system/)')
    parser.add_argument('--http-url', help='URL of a TestBox web runner to try, e.g. http://localhost:8080/tests/runner.bxm')
    parser.add_argument('--install', action='store_true', help='Symlink this package into the Sublime Text Packages folder')
    args = parser.parse_args()

    static_checks()

    executable = find_boxlang(args.boxlang)
    install_sublime_stubs({'boxlang_executable_path': executable})
    sys.path.insert(0, ROOT)
    from src import boxlang_cli, testbox_runner

    if boxlang_checks(boxlang_cli, executable):
        check_command_tests(boxlang_cli, executable)
        testbox_checks(boxlang_cli, testbox_runner, find_testbox(args.testbox))
    else:
        for step in ('3. `boxlang check`', '4. file_regex', '5. TestBox runner'):
            report('skip', step, 'Needs BoxLang 1.17+')
    http_checks(testbox_runner, args.http_url)

    if args.install:
        install_package()

    print('\n== Summary ==')
    print('{pass} passed, {fail} failed, {skip} skipped'.format(**RESULTS))
    print(MANUAL_CHECKLIST)
    return 1 if RESULTS['fail'] else 0


if __name__ == '__main__':
    sys.exit(main())
