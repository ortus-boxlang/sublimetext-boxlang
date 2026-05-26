# BoxLang Language Support for Sublime Text

Thank you for installing **BoxLang** — comprehensive language support for the BoxLang programming language on Sublime Text 4.

## Quick Start

BoxLang syntax highlighting works immediately. For the full feature set (code formatting, AST parsing, compilation), ensure the BoxLang CLI is installed:

```bash
boxlang --version
```

If not installed, visit [boxlang.ortusbooks.com](https://boxlang.ortusbooks.com) for installation instructions.

## Features

- **Syntax Highlighting** for `.bx`, `.bxs`, `.bxm` files
- **825+ Built-in Function Completions** with parameter hints
- **81+ BoxLang Tag Completions** with attribute support
- **Type-Aware Member Method Completions**
- **Code Formatting** via `boxlang format`
- **Build System** — run, compile, debug, and audit
- **Go to Definition** — Command Palette navigation
- **Inline Documentation** — F1 for full docs, hover for quick info
- **Project Component Indexing** with inheritance resolution

## File Icons

- Native fallback icons are included and work without any additional package.

Restart Sublime Text if icons do not appear immediately after installation.

## First Run

On first launch, the setup wizard will guide you through detecting BoxLang and configuring optional CFML fallback support.

Re-run anytime via Command Palette: `BoxLang: Run Setup Wizard`

## Key Bindings

| Action | Shortcut |
| ------ | -------- |
| Show inline documentation | `F1` |
| Go to definition | `BoxLang: Go to Definition` |
| Format code | `Shift+Alt+F` |
| Next/previous parse error | `F4` / `Shift+F4` |

## Getting Started

Open any `.bx`, `.bxs`, or `.bxm` file and start typing. Completions, syntax highlighting, and documentation will be available immediately.

For detailed documentation, visit [boxlang.ortusbooks.com](https://boxlang.ortusbooks.com).
