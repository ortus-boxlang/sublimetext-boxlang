# BoxLang Language Support for Sublime Text

Comprehensive BoxLang language support for Sublime Text 4.

## Features

- **Syntax Highlighting** for `.bx`, `.bxs`, and `.bxm` files
- **Built-in Function Completions** with parameter hints
- **Tag Completions** for `bx:` tags in `.bxm` templates
- **Component Indexing** using BoxLang AST (`boxlang --bx-printast`)
- **Inline Documentation** (F1) linking to [boxlang.ortusbooks.com](https://boxlang.ortusbooks.com)
- **Code Formatting** via `boxlang format` CLI
- **Build System** for running, compiling, and debugging BoxLang files
- **Go to Definition** for classes and functions
- **Type-Aware Completions** based on explicit and inferred types

## Requirements

- Sublime Text 4
- BoxLang installed and available in PATH (for full functionality)

## Installation

### Via Package Control

1. Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Select `Package Control: Install Package`
3. Search for `BoxLang`

### Manual Installation

1. Clone this repository into your Sublime Text Packages folder:
   ```bash
   git clone https://github.com/ortus-boxlang/sublimetext-boxlang.git ~/Library/Application\ Support/Sublime\ Text/Packages/BoxLang
   ```
2. Restart Sublime Text

## First Run

On first launch, the package will:
1. Check for BoxLang installation
2. Guide you through configuration options
3. Ask about CFML file support (optional)

## Key Bindings

| Shortcut | Action |
|----------|--------|
| `F1` | Show inline documentation |
| `Shift+Alt+F` | Format code |
| `Ctrl+B` | Build & run |
| `Ctrl+Alt+D` | Insert `writeDump()` |
| `Ctrl+Shift+O` | Insert `writeOutput()` |
| `Ctrl+Alt+A` | Insert `abort;` |
| `Ctrl+Alt+Click` | Go to definition |

## Settings

Open settings via Command Palette: `BoxLang: Settings`

Key settings:
- `boxlang_executable_path` - Custom BoxLang executable path
- `boxlang_enable_cfml_fallback` - Enable `.cfc`/`.cfm`/`.cfs` support
- `boxlang_bif_completions` - Completion style: `basic`, `required`, `full`
- `boxlang_auto_compile_on_save` - Auto-compile to `./bin` on save
- `boxlang_format_on_save` - Auto-format on save

## Build System

The package includes a build system with variants:
- **Run** - Execute current file
- **Run with Arguments** - Execute with CLI arguments
- **Compile File** - Compile to `./bin`
- **Compile Project** - Compile entire project
- **Debug** - Run with debug output
- **Feature Audit** - Audit CFML→BoxLang compatibility

## Documentation

Full documentation: [boxlang.ortusbooks.com](https://boxlang.ortusbooks.com)

## License

MIT License
