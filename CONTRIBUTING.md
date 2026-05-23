# Contributing Guide

Thanks for helping improve BoxLang language support for Sublime Text.

This repository is a Sublime Text package, not the BoxLang runtime. Contributions here should focus on editor integrations such as syntax, completions, docs, commands, and project indexing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Support](#support)
- [Reporting Bugs](#reporting-bugs)
- [Submitting Changes](#submitting-changes)
- [Development Setup](#development-setup)
- [Project Layout](#project-layout)
- [Coding Guidelines](#coding-guidelines)
- [Manual Validation Checklist](#manual-validation-checklist)
- [Security](#security)
- [Release Notes](#release-notes)

## Code of Conduct

Please follow the guidelines in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Support

Use community channels for usage questions and discussion:

- Ortus Community: https://community.ortussolutions.com
- Box Team Slack: http://boxteam.ortussolutions.com/
- Professional Support: https://www.ortussolutions.com/services/support

Use GitHub issues for actionable bugs and feature requests specific to this repository.

## Reporting Bugs

Please open a GitHub issue in this repository:

- https://github.com/ortus-boxlang/sublimetext-boxlang/issues

When possible, include:

- Sublime Text version and OS
- BoxLang CLI version (`boxlang --version`)
- Steps to reproduce
- Expected behavior vs actual behavior
- Relevant sample file(s), settings, and console output
- Whether CFML fallback is enabled (`boxlang_enable_cfml_fallback`)

## Submitting Changes

1. Fork and create a feature branch from the default branch.
2. Keep PRs focused (one feature/fix per PR when possible).
3. Update docs/settings/comments when behavior changes.
4. Add or update snippets/completions/templates when relevant.
5. Include clear manual test steps in the PR description.

PR checklist:

- [ ] The change is scoped and documented.
- [ ] I manually validated the feature in Sublime Text.
- [ ] I updated [README.md](README.md) and/or settings docs when needed.
- [ ] I updated [changelog.md](changelog.md) under `Unreleased`.

## Development Setup

Requirements:

- Sublime Text 4
- BoxLang installed and available on PATH (recommended)
- Git

Clone into the Sublime Text Packages directory.

macOS example:

```bash
git clone https://github.com/ortus-boxlang/sublimetext-boxlang.git \
   "$HOME/Library/Application Support/Sublime Text/Packages/BoxLang"
```

Typical local iteration loop:

1. Open Sublime Text console (`View -> Show Console`) for runtime errors.
2. Edit package files.
3. Reload plugin host if needed (`Tools -> Developer -> Reload Plugin`).
4. Test against `.bx`, `.bxs`, and `.bxm` files.

## Project Layout

- `src/` Python plugin modules and commands
- `src/plugins_/` completion and documentation providers
- `syntaxes/` syntax grammars
- `snippets/` editor snippets
- `settings/` package settings defaults
- `inputmaps/` key bindings
- `commands/` command palette entries
- `templates/` HTML templates used by inline/completion docs

## Coding Guidelines

- Follow existing style in surrounding files.
- Keep compatibility with Sublime Text 4's Python runtime.
- Favor small, composable functions for command and event code.
- Avoid broad exception swallowing unless there is a clear user-facing fallback.
- Keep command names and setting names consistent with the `boxlang_` prefix.
- Do not commit local machine artifacts (`.sublime-workspace`, `.DS_Store`, caches).

For plugin-facing settings and behavior, keep [README.md](README.md) and [settings/boxlang.sublime-settings](settings/boxlang.sublime-settings) aligned.

## Manual Validation Checklist

Before opening a PR, validate the paths touched by your change.

Syntax and editing:

- [ ] `.bx`, `.bxs`, and `.bxm` syntax scopes look correct.
- [ ] Completions appear in expected contexts.
- [ ] Snippets expand as expected.

Commands and docs:

- [ ] Command palette entries under `BoxLang:` work.
- [ ] Inline docs (`F1`) and hover/completion docs render correctly.
- [ ] Go to definition works for the scenarios you changed.

CLI-related features (if changed):

- [ ] Formatting via BoxLang CLI behaves as expected.
- [ ] Compile/build variants still run from [BoxLang.sublime-build](BoxLang.sublime-build).
- [ ] Setup wizard still completes and persists settings.

## Security

If you discover a security issue, please email:

- security@ortussolutions.com

Please avoid opening a public issue for sensitive security reports.

## Release Notes

Add a brief item to [changelog.md](changelog.md) under `Unreleased` describing user-visible changes.

Use concise entries such as:

- `Fixed: completions in bx:component attribute context`
- `Added: setting for custom BoxLang executable path fallback`
