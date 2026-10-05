# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

* * *

## [Unreleased]

## [1.2.0] - 2026-10-05

Targets **BoxLang 1.17.0+** (verified through 1.18.0).

### Added

- Syntax checking powered by `boxlang check` (BoxLang 1.17+): runs on save, with an opt-in debounced check while typing
- `BoxLang: Check Syntax` Command Palette command and build variant (clickable errors)
- New settings: `boxlang_check_on_save`, `boxlang_check_show_panel`, `boxlang_check_on_type`, `boxlang_check_on_type_delay_ms`
- Completions refreshed for BoxLang 1.14 to 1.18: sets (`setNew`, `boxSet*`), `dateSet*`, `stringStartsWith`/`stringEndsWith`, `schedulerNew`, `getModuleTree`, `dataNavigate`, `generatesecret`-era module BIFs, and the latest module BIFs and components (942 BIFs, 86 tags, 371 member functions)
- Built-in function highlighting now covers 80 newly documented core BIFs
- New snippets: `bxlocalclass`, `bxabstract`, `bxset`, `bxrange`, `bxclassmap`, `bxtransformer`, `bxscheduler`, `bxtask`, `bxclassintercept`
- `scripts/generate_syntax_bifs.py` to refresh the highlighted BIF list from the docs repo

### Changed

- Minimum supported BoxLang version is now 1.17.0
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
