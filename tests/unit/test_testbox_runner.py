"""
Unit tests for the TestBox integration (testbox_runner.py).
"""

import json
import os
from unittest.mock import MagicMock, patch

from tests.expectations import expect

MEMENTO = {
    "totalPass": 3, "totalFail": 1, "totalError": 1, "totalSkipped": 1,
    "totalSpecs": 6, "totalBundles": 1, "totalDuration": 120,
    "bundleStats": [{
        "name": "FooTest", "path": "tests.specs.FooTest",
        "suiteStats": [{
            "name": "Foo",
            "specStats": [
                {"name": "adds", "status": "Passed"},
                {"name": "subtracts", "status": "Failed", "failMessage": "Expected [3] to be [4]", "failDetail": "",
                 "failOrigin": [{"template": "/testbox/system/Assertion.cfc", "line": 5},
                                {"template": "/proj/tests/specs/FooTest.bx", "line": 42}]},
                {"name": "explodes", "status": "Error", "failMessage": "boom",
                 "error": {"message": "boom", "tagContext": [{"template": "/proj/models/Foo.bx", "line": 9}]}},
                {"name": "later", "status": "Skipped"},
            ],
            "suiteStats": [{"name": "nested", "specStats": [{"name": "deep", "status": "Failed", "failMessage": "no origin"}]}],
        }],
    }],
}


class TestSettings:
    def test_defaults_when_nothing_configured(self, mock_sublime_settings):
        from src import testbox_runner
        settings = testbox_runner.get_testbox_settings()
        expect(settings["directory"]).to_be("tests.specs")
        expect(settings["http_runner_url"]).to_be("")

    def test_project_setting_overrides_package_setting(self, mock_sublime_settings):
        from src import testbox_runner
        mock_sublime_settings["boxlang_testbox"] = {"directory": "tests.unit", "timeout": 60}
        view = MagicMock()
        view.settings.return_value.get.return_value = {"http_runner_url": "http://localhost:8080/tests/runner.bxm"}
        settings = testbox_runner.get_testbox_settings(view)
        expect(settings["directory"]).to_be("tests.unit")
        expect(settings["timeout"]).to_be(60)
        expect(settings["http_runner_url"]).to_be("http://localhost:8080/tests/runner.bxm")

    def test_save_project_testbox_setting_preserves_existing_settings(self):
        from src import testbox_runner
        window = MagicMock()
        window.project_file_name.return_value = "/proj/project.sublime-project"
        window.project_data.return_value = {
            "settings": {"other": True, "boxlang_testbox": {"directory": "tests.unit"}}
        }

        saved = testbox_runner.save_project_testbox_setting(
            window, "runner_path", "lib/testbox/system/runners/BoxLangRunner.bx"
        )

        expect(saved).to_be_true()
        project_data = window.set_project_data.call_args[0][0]
        expect(project_data["settings"]["other"]).to_be_true()
        expect(project_data["settings"]["boxlang_testbox"]["directory"]).to_be("tests.unit")
        expect(project_data["settings"]["boxlang_testbox"]["runner_path"]).to_be(
            "lib/testbox/system/runners/BoxLangRunner.bx"
        )

    def test_missing_runner_prompt_offers_local_and_http_options(self):
        from src import testbox_runner
        window = MagicMock()

        testbox_runner.prompt_for_runner(window, MagicMock(), "/proj")

        choices, on_choice = window.show_quick_panel.call_args[0]
        expect(choices).to_be([
            "Set a local BoxLangRunner.bx path",
            "Use an HTTP runner",
        ])
        on_choice(0)
        expect(window.show_input_panel.call_args[0][0]).to_contain("Runner path")

        window.show_input_panel.reset_mock()
        on_choice(1)
        expect(window.show_input_panel.call_args[0][0]).to_contain("HTTP runner URL")


class TestPaths:
    def test_bundle_dot_path(self):
        from src import testbox_runner
        root = os.path.join(os.sep, "proj")
        path = os.path.join(root, "tests", "specs", "FooTest.bx")
        expect(testbox_runner.bundle_dot_path(path, root)).to_be("tests.specs.FooTest")

    def test_find_runner_walks_up_and_prefers_project_root(self, tmp_path):
        from src import testbox_runner
        runner = tmp_path / "testbox" / "system" / "runners" / "BoxLangRunner.bx"
        runner.parent.mkdir(parents=True)
        runner.write_text("class {}")
        nested = tmp_path / "tests" / "specs"
        nested.mkdir(parents=True)
        expect(testbox_runner.find_runner(str(nested), str(tmp_path))).to_be(str(runner))
        expect(testbox_runner.find_runner(str(nested), None)).to_be(str(runner))

    def test_find_runner_supports_lib_testbox_install(self, tmp_path):
        from src import testbox_runner
        runner = tmp_path / "lib" / "testbox" / "system" / "runners" / "BoxLangRunner.bx"
        runner.parent.mkdir(parents=True)
        runner.write_text("class {}")

        expect(testbox_runner.find_runner(str(tmp_path), str(tmp_path))).to_be(str(runner))

    def test_find_runner_supports_testbox_source_checkout(self, tmp_path):
        from src import testbox_runner
        runner = tmp_path / "system" / "runners" / "BoxLangRunner.bx"
        runner.parent.mkdir(parents=True)
        runner.write_text("class {}")

        expect(testbox_runner.find_runner(str(tmp_path), str(tmp_path))).to_be(str(runner))

    def test_find_runner_returns_none_when_missing(self, tmp_path):
        from src import testbox_runner
        expect(testbox_runner.find_runner(str(tmp_path), str(tmp_path))).to_be_none()

    def test_find_runner_uses_configured_path(self, tmp_path):
        from src import testbox_runner
        custom = tmp_path / "custom.bx"
        custom.write_text("x")
        expect(testbox_runner.find_runner(str(tmp_path), str(tmp_path), "custom.bx")).to_be(str(custom))
        expect(testbox_runner.find_runner(str(tmp_path), str(tmp_path), "nope.bx")).to_be_none()


class TestFindTargetAtCursor:
    SOURCE = (
        'class extends="testbox.system.BaseSpec" {\n'
        '  function run() {\n'
        '    describe( "Math", () => {\n'
        '      it( "adds", () => {\n'
        '        expect( 1 + 1 ).toBe( 2 )\n'
        '      } )\n'
        '      it( \'subtracts\', () => {\n'
        '        expect( 2 - 1 ).toBe( 1 )\n'
        '      } )\n'
        '    } )\n'
        '  }\n'
        '}\n'
    )

    def test_cursor_inside_spec_finds_that_spec(self):
        from src import testbox_runner
        offset = self.SOURCE.index("expect( 1 + 1 )")
        expect(testbox_runner.find_target_at(self.SOURCE, offset)).to_be(("spec", "adds"))

    def test_single_quoted_spec(self):
        from src import testbox_runner
        offset = self.SOURCE.index("expect( 2 - 1 )")
        expect(testbox_runner.find_target_at(self.SOURCE, offset)).to_be(("spec", "subtracts"))

    def test_cursor_in_suite_before_any_spec_finds_suite(self):
        from src import testbox_runner
        offset = self.SOURCE.index("it( \"adds\"")
        expect(testbox_runner.find_target_at(self.SOURCE, offset)).to_be(("suite", "Math"))

    def test_xunit_function(self):
        from src import testbox_runner
        source = "component {\n function testAddsNumbers() {\n  assertEquals( 2, 1 + 1 )\n }\n}"
        expect(testbox_runner.find_target_at(source, source.index("assertEquals"))).to_be(("spec", "testAddsNumbers"))

    def test_no_target(self):
        from src import testbox_runner
        expect(testbox_runner.find_target_at("class {}", 3)).to_be_none()


class TestBuilders:
    def test_cli_args_for_bundle_and_spec(self):
        from src import testbox_runner
        args = testbox_runner.build_cli_args("/p/testbox/.../BoxLangRunner.bx", "/tmp/r", {"extra_args": ["--labels=unit"]}, bundle="tests.specs.FooTest", target=("spec", "adds"))
        expect(args[0]).to_be("/p/testbox/.../BoxLangRunner.bx")
        expect(args).to_contain("--bundles=tests.specs.FooTest")
        expect(args).to_contain("--filter-specs=adds")
        expect(args).to_contain("--write-json-report=true")
        expect(args).to_contain("--reportpath=/tmp/r")
        expect(args).to_contain("--labels=unit")
        expect("--directory=tests.specs" in args).to_be_false()

    def test_cli_args_for_all_use_directory_and_suite_filter(self):
        from src import testbox_runner
        args = testbox_runner.build_cli_args("r.bx", "/tmp/r", {"directory": "tests.unit"}, target=("suite", "Math"))
        expect(args).to_contain("--directory=tests.unit")
        expect(args).to_contain("--filter-suites=Math")

    def test_http_url_adds_json_reporter(self):
        from src import testbox_runner
        url = testbox_runner.build_http_url("http://localhost:8080/tests/runner.bxm", {}, bundle="tests.specs.FooTest", target=("spec", "adds a b"))
        expect(url).to_start_with("http://localhost:8080/tests/runner.bxm?")
        expect(url).to_contain("reporter=json")
        expect(url).to_contain("bundles=tests.specs.FooTest")
        expect(url).to_contain("testSpecs=adds+a+b")

    def test_http_url_for_all_and_existing_query(self):
        from src import testbox_runner
        url = testbox_runner.build_http_url("http://h/runner.bxm?token=1", {"directory": "tests.unit"})
        expect(url).to_contain("runner.bxm?token=1&reporter=json")
        expect(url).to_contain("directory=tests.unit")
        expect(url).to_contain("recurse=true")


class TestParseResults:
    def test_totals_and_ok_flag(self):
        from src import testbox_runner
        results = testbox_runner.parse_results(MEMENTO)
        expect(results["totals"]["pass"]).to_be(3)
        expect(results["totals"]["error"]).to_be(1)
        expect(results["ok"]).to_be_false()

    def test_failures_include_nested_suites_and_skip_passes(self):
        from src import testbox_runner
        failures = testbox_runner.parse_results(MEMENTO)["failures"]
        names = [f["spec"] for f in failures]
        expect(names).to_be(["Foo > subtracts", "Foo > explodes", "Foo > nested > deep"])

    def test_origin_skips_testbox_frames(self):
        from src import testbox_runner
        failures = testbox_runner.parse_results(MEMENTO)["failures"]
        expect(failures[0]["file"]).to_be("/proj/tests/specs/FooTest.bx")
        expect(failures[0]["line"]).to_be(42)
        expect(failures[1]["file"]).to_be("/proj/models/Foo.bx")
        expect(failures[2]["file"]).to_be("")

    def test_all_passing_is_ok(self):
        from src import testbox_runner
        results = testbox_runner.parse_results({"totalPass": 2, "totalSpecs": 2, "bundleStats": []})
        expect(results["ok"]).to_be_true()

    def test_bundle_global_exception_is_reported(self):
        from src import testbox_runner
        memento = {"bundleStats": [{"name": "Bad", "path": "tests.Bad", "globalException": {"message": "cannot load"}, "suiteStats": []}]}
        results = testbox_runner.parse_results(memento)
        expect(results["ok"]).to_be_false()
        expect(results["failures"][0]["message"]).to_be("cannot load")


class TestFormatReport:
    def test_failure_lines_are_clickable(self):
        from src import testbox_runner
        text = testbox_runner.format_report(testbox_runner.parse_results(MEMENTO), "tests.specs.FooTest")
        expect(text).to_contain("3 passed, 1 failed, 1 errors, 1 skipped")
        expect(text).to_contain("/proj/tests/specs/FooTest.bx:42: [FAILED] Foo > subtracts")
        expect(text).to_contain("    Expected [3] to be [4]")

    def test_all_passed_message(self):
        from src import testbox_runner
        text = testbox_runner.format_report(testbox_runner.parse_results({"totalPass": 1, "bundleStats": []}), "all tests")
        expect(text).to_contain("All specs passed.")


class TestRunners:
    def test_run_cli_reads_json_report(self, tmp_path):
        from src import testbox_runner, boxlang_cli
        (tmp_path / "report.json").write_text(json.dumps(MEMENTO))
        with patch.object(boxlang_cli, "_run_command", return_value=(1, "text out", "")) as run:
            memento, out, error = testbox_runner.run_cli("boxlang", ["runner.bx"], "/proj", 30, str(tmp_path))
        expect(error).to_be_none()
        expect(memento["totalPass"]).to_be(3)
        expect(out).to_be("text out")
        expect(run.call_args[1]["cwd"]).to_be("/proj")

    def test_run_cli_reports_missing_report(self, tmp_path):
        from src import testbox_runner, boxlang_cli
        with patch.object(boxlang_cli, "_run_command", return_value=(2, "", "no such bundle")):
            memento, out, error = testbox_runner.run_cli("boxlang", ["runner.bx"], "/proj", 30, str(tmp_path))
        expect(memento).to_be_none()
        expect(error).to_contain("no such bundle")

    def test_run_http_parses_json(self):
        from src import testbox_runner
        response = MagicMock()
        response.read.return_value = json.dumps(MEMENTO).encode()
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *a: False
        with patch.object(testbox_runner, "urlopen", return_value=response) as opened:
            memento, error = testbox_runner.run_http("http://h/runner.bxm?reporter=json", 5)
        expect(error).to_be_none()
        expect(memento["totalFail"]).to_be(1)
        expect(opened.call_args[1]["timeout"]).to_be(5)

    def test_run_http_non_json_is_an_error(self):
        from src import testbox_runner
        response = MagicMock()
        response.read.return_value = b"<html>login</html>"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *a: False
        with patch.object(testbox_runner, "urlopen", return_value=response):
            memento, error = testbox_runner.run_http("http://h/", 5)
        expect(memento).to_be_none()
        expect(error).to_contain("did not return JSON")


class TestAnnotations:
    def test_failure_annotations_target_matching_open_files(self):
        from src import testbox_runner
        view = MagicMock()
        view.file_name.return_value = "/proj/tests/specs/FooTest.bx"
        view.text_point.return_value = 10
        view.line.return_value = "REGION"
        other = MagicMock()
        other.file_name.return_value = "/proj/other.bx"
        window = MagicMock()
        window.views.return_value = [view, other]
        failures = testbox_runner.parse_results(MEMENTO)["failures"]
        with patch.object(testbox_runner.utils, "get_setting", return_value=None):
            testbox_runner.apply_failure_annotations(window, failures)
        view.add_regions.assert_called_once()
        expect(view.add_regions.call_args[1]["annotations"]).to_be(["Expected [3] to be [4]"])
        other.add_regions.assert_not_called()
        other.erase_regions.assert_called_once()
