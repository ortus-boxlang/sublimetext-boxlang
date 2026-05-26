# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

* * *

## [Unreleased]

## [0.1.0] - 2026-05-26

### Added

- Syntax highlighting for `.bx` (script classes), `.bxs` (script-only), and `.bxm` (module templates)
- 825+ BIF completions (563 core + 262 module) with parameter hints and snippet insertion
- 81+ BoxLang tag completions (49 core + 32 module) with attribute completions
- 229 member function completions for native types (string, array, struct, query, numeric, datetime, list, xml)
- Dot-path completions for `import`, `new`, and `createObject()` statements
- Type-aware completions based on medium-depth type inference
- Component indexing with inheritance resolution for project-wide completions
- Inline documentation system (F1 popup, hover docs, completion docs)
- Code formatting via `boxlang format` CLI
- Build system with 6 variants (run, compile, debug, audit)
- Error panel with parse error display and F4/Shift+F4 navigation
- Status bar integration (version, indexing progress, error counts)
- Go-to-definition via Ctrl/Cmd+Click
- 10 code snippets for common BoxLang patterns
- Application.bx lifecycle method completions (`applicationbx` plugin)
- In-file symbol completions (`in_file_completions` plugin)
- Plugin-based architecture (7 plugins) for completions and documentation
- First-run setup wizard for BoxLang CLI detection and CFML fallback configuration
- 236 tests (191 unit + 45 integration) with TestBox-style expectations
- File icons (native fallback + optional `A File Icon` support)