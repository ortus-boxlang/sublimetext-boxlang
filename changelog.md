# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

* * *

## [Unreleased]

### Added

- `BoxLang: Open Documentation Website`, `BoxLang: Get Support` and `TestBox: Open Documentation Website` Command Palette commands

### Fixed

- Inline documentation plugins now receive file and project context even when the cursor is outside a recognized syntax context

## [1.3.0] - 2026-10-06

### Added

- `BoxLang: Show Version Info` command: re-detects BoxLang and shows the version, executable, where it came from (BVM, Homebrew, quick installer user or system, Windows installer, custom setting or PATH), `BOXLANG_HOME`, project signals and an upgrade hint for that install type
- BVM details (global `bvm current`, project `.bvmrc`, installed versions, mismatch warning) when BVM is present. Nothing BVM-specific is shown for other install types
- The status bar adds `(.bvmrc X)` after the version when a BVM project file differs from the active version
- Homebrew's `/opt/homebrew/bin/boxlang` is now a standard detection location, and `BVM_HOME` is honored

### Changed

- Build variants and the version detection now share one executable lookup (`boxlang_executable_path`, standard locations, then `PATH`). Build commands now also find BoxLang on `PATH`

## [1.2.1] - 2026-10-06

### Fixed

- The status bar showed a JVM warning (`[0.001s][warning][cds] The shared archive file version ...`) instead of the BoxLang version when the JVM printed it before the real output. The version, `boxlang check` and AST JSON are now read after skipping JVM warning lines, so syntax checking and indexing keep working
- README troubleshooting for finding which BoxLang and Java the package is using

## [1.2.0] - 2026-10-05

Targets **BoxLang 1.17.0+** (verified through 1.18.0).

### Added

- Syntax checking powered by `boxlang check` (BoxLang 1.17+): runs on save, with an opt-in debounced check while typing
- `BoxLang: Check Syntax` Command Palette command and build variant (clickable errors)
- Inline error annotations (the first line of each message at the end of the line), a configurable gutter icon, and a gutter hover popup for syntax errors
- `BoxLang: Check Project` command and build variant (`boxlang check --source`)
- TestBox runner: `TestBox Run Bundle`, `Run Spec at Cursor`, `Run All Tests` and `Run Last` commands using TestBox's BoxLang runner, with results in a clickable output panel and inline failure annotations. A per-project web runner can be configured with `http_runner_url` (runs over HTTP with `reporter=json`)
- `BoxLang: Go to TestBox Spec or Suite` and `BoxLang: Go to Property` quick panels
- `scripts/local_smoke_test.py` to verify the package against a real BoxLang and TestBox install
- New settings: `boxlang_error_gutter_icons`, `boxlang_error_inline_annotations`, a rewritten `boxlang_testbox` block, `boxlang_check_on_save`, `boxlang_check_show_panel`, `boxlang_check_on_type`, `boxlang_check_on_type_delay_ms`
- Completions refreshed for BoxLang 1.14 to 1.18: sets (`setNew`, `boxSet*`), `dateSet*`, `stringStartsWith`/`stringEndsWith`, `schedulerNew`, `getModuleTree`, `dataNavigate`, `generatesecret`-era module BIFs, and the latest module BIFs and components (942 BIFs, 86 tags, 371 member functions)
- Built-in function highlighting now covers 80 newly documented core BIFs
- New snippets: `bxlocalclass`, `bxabstract`, `bxset`, `bxrange`, `bxclassmap`, `bxtransformer`, `bxscheduler`, `bxtask`, `bxclassintercept`
- `scripts/generate_syntax_bifs.py` to refresh the highlighted BIF list from the docs repo

### Changed

- Minimum supported BoxLang version is now 1.17.0
- The `boxlang_testbox` setting block was replaced (the old keys were unused); see the README for the new keys
- The error panel now starts fresh on every run and can show errors without opening the panel or moving the cursor
- Syntax highlighting fixture covers 1.14 to 1.18 constructs


### Added

- Syntax highlighting for range operators (`..`, `..<`, `>..`, `>..<`)
- Syntax highlighting for the `assert` statement, including the optional `: message` clause
- Syntax highlighting for `set{...}` and `sb{...}`/`stringbuilder{...}` literals
- Syntax highlighting for two-variable `for (item, index in arr)` / `for (key, value in struct)` loops

### Chores

- Remove legacy settings file support
- Update README to remove legacy settings file support
- Remove unused colors
- Remove unused icons

## [1.0.3] - 2026-05-27

- More fixes

## [1.0.2] - 2026-05-27

- More fixes

## [1.0.1] - 2026-05-27

- Tons of fixes

## [1.0.0] - 2026-05-26

- First release
