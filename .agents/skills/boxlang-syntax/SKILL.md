---
name: boxlang-syntax
description: "Work with BoxLang Sublime Text syntax definitions (.sublime-syntax files). Use when editing syntax highlighting, scope naming, or grammar rules for .bx, .bxs, and .bxm files."
---

# BoxLang Syntax Definition Skill

Use this skill when working with Sublime Text syntax definitions for BoxLang files.

## Syntax Files

| File | Scope | Extensions | Purpose |
|------|-------|------------|---------|
| `syntaxes/BoxLang.sublime-syntax` | `source.boxlang` | `.bx`, `.bxs` | Script syntax for classes and scripts |
| `syntaxes/BoxLangMarkup.sublime-syntax` | `embedding.boxlang.markup` | `.bxm` | Markup syntax for templates |

## Key Syntax Rules

### Reserved Words
```yaml
reserved_word: |-
  (?x:
    break|case|catch|continue|default|do|else|finally|for|function|if|import|in|new|return|
    super|switch|this|try|var|void|while|null|true|false|class|interface|extends|implements|
    attempt|retry|transaction|lock|abort|throw|rethrow|include|property|component|abstract|
    final|static|public|private|package|remote|annotation
  )\b
```

### Storage Types
```yaml
storage_types: \b(?:any|array|binary|boolean|component|date|guid|numeric|query|string|struct|xml|uuid|void)\b
```

### Access Modifiers
```yaml
access_modifier: \b(private|package|public|remote)\b
```

### Storage Modifiers
```yaml
storage_modifier: \b(static|final|abstract)\b
```

## Scope Naming Conventions

| Element | Scope |
|---------|-------|
| Tags | `entity.name.tag.boxlang` |
| Tag attributes | `entity.other.attribute-name.boxlang` |
| Functions | `entity.name.function.boxlang` |
| Classes | `entity.name.class.boxlang` |
| Variables | `variable.other.readwrite.boxlang` |
| Parameters | `variable.parameter.function.boxlang` |
| Properties | `variable.other.property.boxlang` |
| Strings | `string.quoted.double.boxlang`, `string.quoted.single.boxlang` |
| Numbers | `constant.numeric.boxlang` |
| Keywords | `keyword.control.*.boxlang`, `keyword.operator.*.boxlang` |
| Comments | `comment.block.documentation.boxlang`, `comment.block.boxlang`, `comment.line.double-slash.boxlang` |
| Imports | `variable.other.import.boxlang` |
| Hash escapes | `constant.character.escape.hash.boxlang` |

## Tag Syntax Rules

The main syntax (`BoxLang.sublime-syntax`) handles these tag patterns:

- **Generic bx: tags:** `<bx:tagname attr="value">` → `meta.tag.boxlang`
- **bx:function:** `<bx:function name="...">` → `meta.tag.function.boxlang` with `source.boxlang.script` body
- **bx:output:** `<bx:output>` → `meta.tag.output.boxlang` with HTML body
- **bx:script:** `<bx:script>` → `meta.tag.script.boxlang` with `source.boxlang.script` body

## Self-Closing Tags

These tags should NOT have closing tags (derived from `@BoxComponent` annotations):
```
abort, associate, break, continue, dump, exit, flush, httpparam, include,
invokeargument, log, param, procparam, procresult, queryparam, rethrow,
return, schedule, setting, sleep, throw, trace, zipparam
```

## Adding New Syntax Features

1. **New reserved word:** Add to `reserved_word` variable in both syntax files
2. **New storage type:** Add to `storage_types` variable
3. **New tag:** Add context in `BoxLangMarkup.sublime-syntax` under `tags:` include
4. **New operator:** Add to `operators` context in `BoxLang.sublime-syntax`
5. **New scope style:** Update `boxlang.sublime-settings` with style entry

## Testing Syntax Changes

1. Open a `.bx`/`.bxs`/`.bxm` file in Sublime Text
2. Place cursor on element to check
3. Use `Tools > Developer > Show Scope Name` (Ctrl+Alt+Shift+P)
4. Verify scope matches expected naming convention

## Common Patterns

### Function Declaration
```yaml
function-declaration:
  - match: '{{function_declaration_lookahead}}'
    scope: meta.function.declaration.boxlang
    push:
      - match: \bfunction\b
        scope: keyword.declaration.function.boxlang storage.type.function.boxlang
      - match: '{{identifier}}'
        scope: entity.name.function.boxlang
      - match: \(
        scope: punctuation.section.group.begin.boxlang
        push: function-params
      - match: ':'
        scope: punctuation.separator.type.boxlang
        push: return-type
```

### Class Declaration
```yaml
class-declaration:
  - match: \b(class)\b
    scope: keyword.declaration.class.boxlang storage.type.class.boxlang
    push:
      - match: \{
        scope: punctuation.section.block.begin.boxlang
        set: class-body
      - match: \b(extends)\b
        scope: keyword.declaration.extends.boxlang
      - match: \b(implements)\b
        scope: keyword.declaration.implements.boxlang
      - match: '{{identifier}}'
        scope: entity.name.class.boxlang
```
