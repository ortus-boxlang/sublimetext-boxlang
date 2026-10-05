"""
Unit tests for `boxlang check` integration (boxlang_cli.run_check and syntax_check.py).
"""

import json
import re
from unittest.mock import MagicMock, patch

from tests.expectations import expect

SAMPLE_INVALID = json.dumps([{
    "file": "/path/bad.bxs",
    "valid": False,
    "issues": [{"message": "Unclosed parenthesis [(] on line 1", "line": 1, "column": 3}],
}])
SAMPLE_VALID = json.dumps([{"file": "/path/good.bxs", "valid": True, "issues": []}])


class TestVersionHelpers:
    def test_version_tuple(self):
        from src import boxlang_cli
        expect(boxlang_cli.version_tuple("1.18.0+12")).to_be((1, 18, 0))
        expect(boxlang_cli.version_tuple("")).to_be_none()

    def test_supports_check_true_for_117_and_newer(self):
        from src import boxlang_cli
        for version in ("1.17.0", "1.17.6+3", "1.18.0", "2.0.0"):
            boxlang_cli._boxlang_version = version
            expect(boxlang_cli.supports_check()).to_be_true()

    def test_supports_check_false_for_older_or_unknown(self):
        from src import boxlang_cli
        for version in ("1.16.9", "1.13.0+54", ""):
            boxlang_cli._boxlang_version = version
            expect(boxlang_cli.supports_check()).to_be_false()

    def test_is_checkable_file(self):
        from src import boxlang_cli
        for name in ("a.bx", "a.bxs", "a.bxm", "a.cfc", "a.cfm", "a.cfs", "A.BX"):
            expect(boxlang_cli.is_checkable_file("/x/" + name)).to_be_true()
        expect(boxlang_cli.is_checkable_file("/x/a.txt")).to_be_false()
        expect(boxlang_cli.is_checkable_file(None)).to_be_false()


class TestParseCheckOutput:
    def test_parses_invalid_file(self):
        from src import boxlang_cli
        records = boxlang_cli.parse_check_output(SAMPLE_INVALID)
        expect(len(records)).to_be(1)
        expect(records[0]["issues"][0]["line"]).to_be(1)

    def test_parses_valid_file(self):
        from src import boxlang_cli
        records = boxlang_cli.parse_check_output(SAMPLE_VALID)
        expect(records[0]["issues"]).to_be_empty()

    def test_returns_none_for_garbage(self):
        from src import boxlang_cli
        expect(boxlang_cli.parse_check_output("not json")).to_be_none()
        expect(boxlang_cli.parse_check_output("")).to_be_none()
        expect(boxlang_cli.parse_check_output("42")).to_be_none()


class TestRunCheck:
    def test_exit_code_one_with_json_is_not_an_error(self):
        from src import boxlang_cli
        with patch.object(boxlang_cli, "_run_command", return_value=(1, SAMPLE_INVALID, "")) as run:
            issues, error = boxlang_cli.run_check("/path/bad.bxs")
        expect(error).to_be_none()
        expect(len(issues)).to_be(1)
        args = run.call_args[0][0]
        expect(args[1:]).to_be(["check", "--format", "json", "/path/bad.bxs"])

    def test_valid_file_returns_no_issues(self):
        from src import boxlang_cli
        with patch.object(boxlang_cli, "_run_command", return_value=(0, SAMPLE_VALID, "")):
            issues, error = boxlang_cli.run_check("/path/good.bxs")
        expect(error).to_be_none()
        expect(issues).to_be_empty()

    def test_non_json_output_is_an_error(self):
        from src import boxlang_cli
        with patch.object(boxlang_cli, "_run_command", return_value=(2, "", "Unknown action check")):
            issues, error = boxlang_cli.run_check("/path/a.bx")
        expect(issues).to_be_none()
        expect(error).to_contain("Unknown action check")

    def test_timeout_is_reported(self):
        import subprocess
        from src import boxlang_cli
        with patch.object(boxlang_cli, "_run_command", side_effect=subprocess.TimeoutExpired("boxlang", 30)):
            issues, error = boxlang_cli.run_check("/path/a.bx")
        expect(issues).to_be_none()
        expect(error).to_contain("timed out")


class TestBuildFileRegex:
    def test_regex_matches_text_output(self):
        pattern = re.compile(r"^\s*(.+?): Line: ([0-9]+) Col: ([0-9]+) - (.*)$")
        line = "   bad.bxs: Line: 1 Col: 3 - Unclosed parenthesis [(] on line 1"
        match = pattern.match(line)
        expect(match.group(1)).to_be("bad.bxs")
        expect(match.group(2)).to_be("1")
        expect(match.group(3)).to_be("3")


class TestSyntaxCheckModule:
    def _view(self, path="/p/a.bx", scope_ok=True, dirty=False):
        view = MagicMock()
        view.file_name.return_value = path
        view.match_selector.return_value = scope_ok
        view.id.return_value = 7
        view.is_dirty.return_value = dirty
        return view

    def test_should_check_requires_extension_and_scope(self):
        from src import syntax_check
        expect(syntax_check.should_check(self._view())).to_be_true()
        expect(syntax_check.should_check(self._view(path="/p/a.txt"))).to_be_false()
        expect(syntax_check.should_check(self._view(scope_ok=False))).to_be_false()

    def test_apply_results_shows_errors(self):
        from src import syntax_check
        view = self._view()
        issues = [{"line": 1, "column": 3, "message": "bad"}]
        with patch.object(syntax_check, "status_bar") as bar, patch.object(syntax_check, "error_panel") as panel:
            syntax_check.apply_results(view, "/p/a.bx", issues)
        bar.set_error_count.assert_called_once_with(view, 1)
        panel.show_errors.assert_called_once_with(view, "/p/a.bx", issues, show_panel=True, navigate=False)

    def test_apply_results_clears_when_valid(self):
        from src import syntax_check
        view = self._view()
        with patch.object(syntax_check, "status_bar") as bar, patch.object(syntax_check, "error_panel") as panel:
            syntax_check.apply_results(view, "/p/a.bx", [])
        bar.set_error_count.assert_called_once_with(view, 0)
        panel.clear_errors.assert_called_once_with(view)
        panel.hide_panel.assert_called_once_with(view)

    def test_check_view_skips_old_boxlang(self):
        from src import syntax_check, boxlang_cli
        boxlang_cli._boxlang_installed = True
        boxlang_cli._boxlang_version = "1.16.0"
        syntax_check._version_warning_shown = False
        with patch.object(boxlang_cli, "run_check") as run:
            syntax_check.check_view(self._view())
        run.assert_not_called()

    def test_check_view_runs_on_supported_boxlang(self):
        from src import syntax_check, boxlang_cli
        boxlang_cli._boxlang_installed = True
        boxlang_cli._boxlang_version = "1.18.0"
        with patch.object(boxlang_cli, "run_check") as run:
            syntax_check.check_view(self._view())
        run.assert_called_once()
        expect(run.call_args[0][0]).to_be("/p/a.bx")

    def test_on_save_respects_setting(self, mock_sublime_settings):
        from src import syntax_check
        mock_sublime_settings["boxlang_check_on_save"] = False
        with patch.object(syntax_check, "check_view") as check:
            syntax_check.on_post_save_async(self._view())
        check.assert_not_called()

    def test_on_type_is_off_by_default(self, mock_sublime_settings):
        from src import syntax_check
        with patch.object(syntax_check, "sublime") as sub:
            syntax_check.on_modified_async(self._view())
        sub.set_timeout_async.assert_not_called()

    def test_on_type_schedules_debounced_check(self, mock_sublime_settings):
        from src import syntax_check
        mock_sublime_settings["boxlang_check_on_type"] = True
        mock_sublime_settings["boxlang_check_on_type_delay_ms"] = 400
        with patch.object(syntax_check, "sublime") as sub:
            syntax_check.on_modified_async(self._view())
        delay = sub.set_timeout_async.call_args[0][1]
        expect(delay).to_be(400)

    def test_only_latest_keystroke_runs_check(self, mock_sublime_settings):
        from src import syntax_check
        mock_sublime_settings["boxlang_check_on_type"] = True
        view = self._view()
        with patch.object(syntax_check, "sublime") as sub, patch.object(syntax_check, "check_view") as check:
            syntax_check.on_modified_async(view)
            syntax_check.on_modified_async(view)
            first, second = [c[0][0] for c in sub.set_timeout_async.call_args_list]
            first()
            check.assert_not_called()
            second()
        check.assert_called_once()
