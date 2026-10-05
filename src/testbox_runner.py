"""
TestBox integration: run bundles, specs or whole suites and show the results in the editor.

By default tests run through TestBox's BoxLang CLI runner (testbox/system/runners/BoxLangRunner.bx).
A project can opt into a web runner instead by setting `http_runner_url` in its
`boxlang_testbox` project setting. That runs over HTTP with `reporter=json`.

Results are shown in an output panel (clickable `file:line` failures) and as inline
annotations on the failing lines of any open file.
"""
import html
import json
import os
import re
import shutil
import tempfile
import threading
from urllib.parse import urlencode
from urllib.request import urlopen
import sublime
import sublime_plugin
from . import boxlang_cli
from . import utils

_PANEL_NAME = 'boxlang_testbox'
_REGION_KEY = 'boxlang_testbox_failures'
_RUNNER_RELATIVE = os.path.join('testbox', 'system', 'runners', 'BoxLangRunner.bx')
SPEC_FUNCTIONS = ('it', 'fit', 'xit', 'test', 'ftest', 'xtest', 'then', 'fthen', 'xthen')
SUITE_FUNCTIONS = ('describe', 'fdescribe', 'xdescribe', 'feature', 'ffeature', 'xfeature', 'story', 'fstory', 'xstory', 'given', 'fgiven', 'xgiven', 'when', 'fwhen', 'xwhen', 'scenario', 'fscenario', 'xscenario')
CALL_PATTERN = re.compile(r'\b(' + '|'.join(SPEC_FUNCTIONS + SUITE_FUNCTIONS) + r')\s*\(\s*(["\'])((?:(?!\2).)*)\2')
XUNIT_PATTERN = re.compile(r'\bfunction\s+(test\w*)\s*\(', re.IGNORECASE)
DEFAULTS = {
    'runner_path': '',
    'http_runner_url': '',
    'directory': 'tests.specs',
    'extra_args': [],
    'timeout': 300,
}
_last_run = {}


# ── settings ──────────────────────────────────────────────────────────────────

def get_testbox_settings(view=None):
    """Merge defaults, package settings and the project-level `boxlang_testbox` setting."""
    merged = dict(DEFAULTS)
    package_value = utils.get_setting('boxlang_testbox')
    if isinstance(package_value, dict):
        merged.update(package_value)
    if view is not None:
        project_value = view.settings().get('boxlang_testbox')
        if isinstance(project_value, dict):
            merged.update(project_value)
    return merged


# ── path helpers ──────────────────────────────────────────────────────────────

def find_runner(start_dir, project_root=None, configured=''):
    """Locate BoxLangRunner.bx: a configured path, the project root, or any parent of start_dir."""
    if configured:
        candidate = configured if os.path.isabs(configured) or not project_root else os.path.join(project_root, configured)
        return candidate if os.path.isfile(candidate) else None
    seen = []
    if project_root:
        seen.append(project_root)
    current = start_dir
    while current and current not in seen:
        seen.append(current)
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    for directory in seen:
        candidate = os.path.join(directory, _RUNNER_RELATIVE)
        if os.path.isfile(candidate):
            return candidate
    return None


def bundle_dot_path(file_path, project_root):
    """Convert tests/specs/FooTest.bx into the bundle dot path tests.specs.FooTest."""
    relative = os.path.relpath(file_path, project_root)
    without_ext = os.path.splitext(relative)[0]
    return '.'.join(part for part in re.split(r'[\\/]+', without_ext) if part)


# ── cursor targeting ──────────────────────────────────────────────────────────

def find_target_at(text, offset):
    """
    Find the spec or suite the cursor is in.

    Returns ('spec', name), ('suite', name) or None. The nearest spec call
    (it, test, then, ...) or xUnit `function testXxx()` above the cursor wins; when
    none exists the nearest suite call (describe, feature, ...) is used.
    """
    before = text[:offset]
    spec = None
    suite = None
    for match in CALL_PATTERN.finditer(before):
        kind = 'spec' if match.group(1) in SPEC_FUNCTIONS else 'suite'
        if kind == 'spec':
            spec = (match.start(), match.group(3))
        else:
            suite = (match.start(), match.group(3))
    for match in XUNIT_PATTERN.finditer(before):
        if spec is None or match.start() > spec[0]:
            spec = (match.start(), match.group(1))
    if spec:
        return ('spec', spec[1])
    if suite:
        return ('suite', suite[1])
    return None


# ── building runs ─────────────────────────────────────────────────────────────

def build_cli_args(runner_path, report_dir, settings, bundle=None, target=None):
    """Build the argument list for the TestBox BoxLang runner."""
    args = [runner_path, '--reporter=text', '--write-json-report=true', '--properties-summary=false', '--reportpath={}'.format(report_dir)]
    if bundle:
        args.append('--bundles={}'.format(bundle))
    else:
        args.append('--directory={}'.format(settings.get('directory') or DEFAULTS['directory']))
    if target:
        flag = '--filter-specs' if target[0] == 'spec' else '--filter-suites'
        args.append('{}={}'.format(flag, target[1]))
    args.extend(str(extra) for extra in (settings.get('extra_args') or []))
    return args


def build_http_url(base_url, settings, bundle=None, target=None):
    """Build the web runner URL with reporter=json."""
    params = [('reporter', 'json')]
    if bundle:
        params.append(('bundles', bundle))
    else:
        params.extend([('directory', settings.get('directory') or DEFAULTS['directory']), ('recurse', 'true')])
    if target:
        params.append(('testSpecs' if target[0] == 'spec' else 'testSuites', target[1]))
    separator = '&' if '?' in base_url else '?'
    return base_url + separator + urlencode(params)


# ── parsing results ───────────────────────────────────────────────────────────

def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _origin(spec_stats, project_root):
    """Pick the best file and line for a failing spec from its failOrigin or error tag context."""
    candidates = []
    origin = spec_stats.get('failOrigin')
    if isinstance(origin, list):
        candidates.extend(origin)
    elif isinstance(origin, dict) and origin:
        candidates.append(origin)
    error = spec_stats.get('error')
    if isinstance(error, dict) and isinstance(error.get('tagContext'), list):
        candidates.extend(error['tagContext'])
    fallback = None
    for entry in candidates:
        if not isinstance(entry, dict):
            continue
        template = entry.get('template') or entry.get('file') or ''
        line = _int(entry.get('line'))
        if not template or not line:
            continue
        if fallback is None:
            fallback = (template, line)
        normalized = template.replace('\\', '/')
        if '/testbox/system/' not in normalized and '/testbox/' not in normalized:
            return (template, line)
    return fallback or ('', 0)


def _walk_suites(suites, bundle_name, path, project_root, failures):
    for suite in suites or []:
        suite_path = path + [suite.get('name', '')]
        for spec in suite.get('specStats') or []:
            status = str(spec.get('status', '')).lower()
            if status in ('failed', 'error'):
                file_name, line = _origin(spec, project_root)
                failures.append({
                    'bundle': bundle_name,
                    'spec': ' > '.join(part for part in suite_path + [spec.get('name', '')] if part),
                    'status': status,
                    'message': spec.get('failMessage') or (spec.get('error') or {}).get('message', '') or '',
                    'detail': spec.get('failDetail') or '',
                    'file': file_name,
                    'line': line,
                })
        _walk_suites(suite.get('suiteStats'), bundle_name, suite_path, project_root, failures)


def parse_results(memento, project_root=''):
    """Normalize a TestBox result memento (JSON reporter output) into totals and failures."""
    totals = {
        'pass': _int(memento.get('totalPass')),
        'fail': _int(memento.get('totalFail')),
        'error': _int(memento.get('totalError')),
        'skipped': _int(memento.get('totalSkipped')),
        'specs': _int(memento.get('totalSpecs')),
        'bundles': _int(memento.get('totalBundles')),
        'ms': _int(memento.get('totalDuration')),
    }
    failures = []
    for bundle in memento.get('bundleStats') or []:
        exception = bundle.get('globalException')
        if exception:
            message = exception.get('message', '') if isinstance(exception, dict) else str(exception)
            file_name, line = _origin({'error': exception if isinstance(exception, dict) else {}}, project_root)
            failures.append({
                'bundle': bundle.get('path') or bundle.get('name', ''),
                'spec': '(bundle failed to run)',
                'status': 'error',
                'message': message,
                'detail': '',
                'file': file_name,
                'line': line,
            })
        _walk_suites(bundle.get('suiteStats'), bundle.get('path') or bundle.get('name', ''), [], project_root, failures)
    return {'ok': totals['fail'] == 0 and totals['error'] == 0 and not failures, 'totals': totals, 'failures': failures}


def format_report(results, title):
    """Render results as plain text. Failure lines start with `file:line:` so the panel is clickable."""
    totals = results['totals']
    lines = ['TestBox - {}'.format(title), '=' * 60]
    lines.append('{} passed, {} failed, {} errors, {} skipped ({} specs, {} ms)'.format(totals['pass'], totals['fail'], totals['error'], totals['skipped'], totals['specs'], totals['ms']))
    lines.append('')
    if results['ok']:
        lines.append('All specs passed.')
    for failure in results['failures']:
        location = '{}:{}'.format(failure['file'], failure['line']) if failure['file'] else failure['bundle']
        lines.append('{}: [{}] {}'.format(location, failure['status'].upper(), failure['spec']))
        if failure['message']:
            lines.append('    {}'.format(failure['message']))
        if failure['detail']:
            lines.append('    {}'.format(failure['detail']))
        lines.append('')
    return '\n'.join(lines)


# ── running ───────────────────────────────────────────────────────────────────

def run_cli(bx_path, args, project_root, timeout, report_dir):
    """Run the BoxLang runner. Returns (memento, output_text, error)."""
    returncode, stdout, stderr = boxlang_cli._run_command([bx_path] + args, timeout=timeout, cwd=project_root)
    report_file = os.path.join(report_dir, 'report.json')
    if os.path.isfile(report_file):
        try:
            with open(report_file, encoding='utf-8') as handle:
                return (json.load(handle), stdout, None)
        except (OSError, ValueError) as exc:
            return (None, stdout, 'Could not read the TestBox JSON report: {}'.format(exc))
    detail = (stderr.strip() or stdout.strip() or 'no output')
    return (None, stdout, 'TestBox did not produce a JSON report (exit {}). {}'.format(returncode, detail[:2000]))


def run_http(url, timeout):
    """Run through a web runner with reporter=json. Returns (memento, error)."""
    with urlopen(url, timeout=timeout) as response:
        body = response.read().decode('utf-8', errors='replace')
    try:
        return (json.loads(body), None)
    except ValueError:
        return (None, 'The web runner did not return JSON: {}'.format(body[:500].strip()))


# ── presentation ──────────────────────────────────────────────────────────────

def _show_panel(window, text, project_root):
    panel = window.create_output_panel(_PANEL_NAME)
    panel.settings().set('result_file_regex', r'^(.+?):([0-9]+): ')
    panel.settings().set('result_base_dir', project_root or '')
    panel.settings().set('word_wrap', False)
    panel.run_command('append', {'characters': text, 'force': True})
    panel.settings().set('read_only', True)
    window.run_command('show_panel', {'panel': 'output.{}'.format(_PANEL_NAME)})


def apply_failure_annotations(window, failures):
    """Mark failing lines in any open file with a squiggle, gutter icon and inline message."""
    by_file = {}
    for failure in failures:
        if failure['file'] and failure['line']:
            by_file.setdefault(os.path.normcase(os.path.normpath(failure['file'])), []).append(failure)
    inline = utils.get_setting('boxlang_error_inline_annotations') is not False
    for view in window.views():
        view.erase_regions(_REGION_KEY)
        file_name = view.file_name()
        if not file_name:
            continue
        matches = by_file.get(os.path.normcase(os.path.normpath(file_name)))
        if not matches:
            continue
        regions = [view.line(view.text_point(item['line'] - 1, 0)) for item in matches]
        kwargs = {}
        if inline:
            kwargs = {'annotations': [html.escape((item['message'] or item['status']).split('\n')[0][:120]) for item in matches], 'annotation_color': 'red'}
        view.add_regions(_REGION_KEY, regions, 'invalid', 'cross', sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE, **kwargs)


def _finish(window, results, title, project_root, output_text, error):
    if error:
        _show_panel(window, 'TestBox - {}\n{}\n\n{}\n\n{}'.format(title, '=' * 60, error, output_text or ''), project_root)
        sublime.status_message('TestBox: run failed')
        return
    _show_panel(window, format_report(results, title), project_root)
    apply_failure_annotations(window, results['failures'])
    totals = results['totals']
    sublime.status_message('TestBox: {} passed, {} failed, {} errors'.format(totals['pass'], totals['fail'], totals['error']))


def start_run(window, view, scope='file', last=None):
    """Resolve what to run, then run it in the background and present the results."""
    file_path = view.file_name() if view else None
    project_root = None
    if file_path:
        from . import build_helpers
        project_root = build_helpers.get_project_root(window, file_path)
    elif window.folders():
        project_root = window.folders()[0]
    if not project_root:
        sublime.status_message('TestBox: open a project folder first')
        return
    settings = get_testbox_settings(view)
    bundle = None
    target = None
    title = 'all tests'
    if last:
        bundle, target, title = last['bundle'], last['target'], last['title']
    elif scope in ('file', 'spec'):
        if not file_path:
            sublime.status_message('TestBox: save the file first')
            return
        bundle = bundle_dot_path(file_path, project_root)
        title = bundle
        if scope == 'spec':
            target = find_target_at(view.substr(sublime.Region(0, view.size())), view.sel()[0].begin())
            if not target:
                sublime.status_message('TestBox: no spec found above the cursor, running the whole bundle')
            else:
                title = '{} > {}'.format(bundle, target[1])
    _last_run['args'] = {'bundle': bundle, 'target': target, 'title': title}
    timeout = settings.get('timeout') if isinstance(settings.get('timeout'), int) else DEFAULTS['timeout']
    http_url = (settings.get('http_runner_url') or '').strip()
    bx_path = None
    runner_path = None
    if not http_url:
        if not boxlang_cli.is_installed():
            sublime.status_message('TestBox: BoxLang executable not found')
            return
        runner_path = find_runner(os.path.dirname(file_path) if file_path else project_root, project_root, settings.get('runner_path'))
        if not runner_path:
            sublime.error_message('TestBox BoxLang runner not found.\n\nInstall TestBox 7+ in your project (box install testbox) or set "runner_path" in the "boxlang_testbox" setting.\n\nTo use a web runner instead, set "http_runner_url" in your project settings.')
            return
        bx_path = boxlang_cli.get_executable()
    sublime.status_message('TestBox: running {}...'.format(title))

    def work():
        report_dir = None
        output_text = ''
        try:
            if http_url:
                memento, error = run_http(build_http_url(http_url, settings, bundle, target), timeout)
            else:
                report_dir = tempfile.mkdtemp(prefix='boxlang_testbox_')
                args = build_cli_args(runner_path, report_dir, settings, bundle, target)
                memento, output_text, error = run_cli(bx_path, args, project_root, timeout, report_dir)
            results = parse_results(memento, project_root) if memento else None
        except Exception as exc:
            results, error = None, str(exc)
        finally:
            if report_dir:
                shutil.rmtree(report_dir, ignore_errors=True)
        sublime.set_timeout(lambda: _finish(window, results, title, project_root, output_text, error))

    threading.Thread(target=work, daemon=True).start()


class BoxlangTestboxRunCommand(sublime_plugin.WindowCommand):
    """Run TestBox tests. scope: file, spec, all or last."""

    def run(self, scope='file'):
        view = self.window.active_view()
        if scope == 'last':
            last = _last_run.get('args')
            if not last:
                sublime.status_message('TestBox: nothing has been run yet')
                return
            start_run(self.window, view, last=last)
            return
        start_run(self.window, view, scope=scope)

    def is_enabled(self):
        return utils.get_setting('boxlang_testbox_enabled') is not False
