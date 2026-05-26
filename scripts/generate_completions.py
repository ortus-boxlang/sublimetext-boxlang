#!/usr/bin/env python3
"""
Generate BoxLang completion JSON files from the boxlang-docs repository.

Usage:
    python3 scripts/generate_completions.py
    python3 scripts/generate_completions.py --docs-path /path/to/boxlang-docs
    python3 scripts/generate_completions.py --update    # git pull docs repo first

Outputs (written to src/plugins_/basecompletions/json/):
    boxlang_functions.json         - BIF name → [description, [req_snippet, full_snippet]]
    boxlang_tags.json              - tag name → {attributes: [[req], [opt]], attribute_values: {}}
    boxlang_member_functions.json  - type → {name → [description, [req_snippet, full_snippet]]}
    boxlang_function_params.json   - BIF name → {description, params: [{name,type,required,description,default}]}

Covers:
    - Core BIFs and components (boxlang-language/reference/)
    - Module BIFs and components (boxlang-framework/modularity/ and boxlang-framework/boxlang-plus/modules/)
"""

import argparse
import html
import json
import os
import re
import subprocess
import sys

DOCS_REPO_URL = "https://github.com/ortus-boxlang/boxlang-docs"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
JSON_DIR = os.path.join(REPO_ROOT, "src", "plugins_", "basecompletions", "json")

BIF_ROOT = "boxlang-language/reference/built-in-functions"
COMPONENT_ROOT = "boxlang-language/reference/components"
TYPES_ROOT = "boxlang-language/reference/types"

# Directories to scan for module BIFs and components
MODULE_ROOTS = [
    "boxlang-framework/modularity",
    "boxlang-framework/boxlang-plus/modules",
]

# Member function type files → boxlang type name
MEMBER_TYPE_FILES = {
    "array.md": "array",
    "string.md": "string",
    "struct.md": "struct",
    "query.md": "query",
    "date.md": "date",
    "datetime.md": "datetime",
    "list.md": "list",
    "numeric.md": "numeric",
    "xml.md": "xml",
}


# ---------------------------------------------------------------------------
# Markdown parsing helpers
# ---------------------------------------------------------------------------

def strip_html(text):
    """Remove HTML tags and decode entities, collapsing whitespace."""
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_default(raw):
    """Extract the default value from a table cell like '`false`' or ''."""
    raw = raw.strip()
    if not raw:
        return None
    m = re.match(r"^`([^`]*)`$", raw)
    return m.group(1) if m else raw


def parse_table_rows(lines, start):
    """
    Parse a markdown pipe table starting at or after `start` index.
    Skips blank lines before the table begins.
    Returns list of dicts keyed by lowercased column header.
    Stops at first non-table line after the table has started.
    """
    headers = []
    rows = []
    i = start
    table_started = False
    while i < len(lines):
        line = lines[i].strip()
        if not table_started:
            if not line:
                i += 1
                continue  # skip blank lines before table
            if not line.startswith("|"):
                break  # no table found
        if not line.startswith("|"):
            break  # end of table
        table_started = True
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not headers:
            headers = [c.lower().strip("`* ") for c in cells]
        elif re.match(r"^[-| :]+$", line):
            pass  # separator row
        else:
            row = {}
            for j, h in enumerate(headers):
                row[h] = cells[j] if j < len(cells) else ""
            rows.append(row)
        i += 1
    return rows


def parse_bif_file(path):
    """
    Parse a BIF markdown file. Handles two formats:
      1. Core format:   # Function: `Name`  with  ### Arguments
      2. Module format: # Name               with  ## Arguments  (column: Name or Argument)
    Returns: {name, description, params: [{name, type, required, description, default}]}
    or None on failure.
    """
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None

    lines = content.splitlines()

    # Name: try "# Function: `Name`" first, fall back to plain H1 heading
    name_match = re.search(r"^#\s+Function:\s+`([^`]+)`", content, re.MULTILINE)
    if name_match:
        name = name_match.group(1)
        name_prefix = "Function:"
    else:
        # Plain H1: "# SomeName" or "# Name1 / Name2" (aliases — take first)
        # Allows lower or uppercase start (e.g. createDate, couchbaseGetBucket)
        name_match = re.search(r"^#\s+([A-Za-z][A-Za-z0-9_]+)", content, re.MULTILINE)
        if not name_match:
            return None
        name = name_match.group(1)
        name_prefix = None

    # Description: first non-comment, non-empty, non-heading line after the name heading
    description = ""
    past_name = False
    for line in lines:
        if name_prefix and re.match(r"^#\s+Function:", line):
            past_name = True
            continue
        elif not name_prefix and re.match(r"^#\s+" + re.escape(name), line):
            past_name = True
            continue
        if past_name:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("[comment]") \
                    and not stripped.startswith("{%") and not stripped.startswith("```"):
                description = strip_html(stripped)
                break

    # Arguments table — try ### Arguments first, then ## Arguments
    params = []
    for i, line in enumerate(lines):
        if re.match(r"^#{2,3}\s+Arguments", line.strip()):
            rows = parse_table_rows(lines, i + 1)
            for row in rows:
                arg_name = row.get("argument", row.get("name", row.get("atrribute", row.get("attribute", ""))))
                arg_name = re.sub(r"[`*]", "", arg_name).strip()
                if not arg_name:
                    continue
                required_val = row.get("required", "false").strip().strip("`").lower()
                params.append({
                    "name": arg_name,
                    "type": re.sub(r"[`*]", "", row.get("type", "any")).strip(),
                    "required": required_val in ("true", "yes"),
                    "description": strip_html(row.get("description", "")),
                    "default": parse_default(row.get("default", "")),
                })
            break

    return {"name": name, "description": description, "params": params}


def parse_component_file(path):
    """
    Parse a component/tag markdown file. Handles multiple formats:
      1. Standard:  # Component: `Name`  with  ### Attributes
      2. bx: prefix:  # bx:name  with  ## Attributes (and optional subsections)
      3. Plain name:  # Name  with  ## Attributes
    Returns: {name, description, attributes: [{name, type, required, description, default}]}
    or None.
    """
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None

    lines = content.splitlines()

    # Name: try several heading patterns in order
    name = None
    name_heading_line = None

    # 1. "# Component: `Name`"
    m = re.search(r"^#\s+Component:\s+`([^`]+)`", content, re.MULTILINE)
    if m:
        name = m.group(1)
        name_heading_line = m.group(0)
    else:
        # 2. "# bx:name" — strip bx: prefix
        m = re.search(r"^#\s+bx:([a-zA-Z][a-zA-Z0-9_-]*)\s*$", content, re.MULTILINE)
        if m:
            # Convert kebab-case to PascalCase for the tag name stored in JSON
            raw = m.group(1)
            name = "".join(w.capitalize() for w in raw.replace("-", " ").split())
            name_heading_line = m.group(0)
        else:
            # 3. "# SomeName" or "# SomeName Component" — plain H1
            m = re.search(r"^#\s+([A-Z][A-Za-z0-9_]+)(?:\s+Component)?\s*$", content, re.MULTILINE)
            if m:
                name = m.group(1)
                name_heading_line = m.group(0)

    if not name:
        return None

    description = ""
    past_name = False
    for line in lines:
        stripped_line = line.strip()
        if name_heading_line and stripped_line == name_heading_line.strip():
            past_name = True
            continue
        if past_name:
            stripped = stripped_line
            if stripped and not stripped.startswith("#") and not stripped.startswith("{%") \
                    and not stripped.startswith("```") and not stripped.startswith("##"):
                description = strip_html(stripped)
                break

    # Attributes: collect all rows from all attribute table sections (## or ### level)
    # This handles charts which has multiple subsections under ## Attributes
    attributes = []
    seen_names = set()
    for i, line in enumerate(lines):
        if re.match(r"^#{2,3}\s+(?:Core\s+|Responsive\s+|Styling\s+|Data\s+|Advanced\s+)?Attributes", line.strip()):
            rows = parse_table_rows(lines, i + 1)
            for row in rows:
                attr_name = row.get("atrribute", row.get("attribute", row.get("name", row.get("argument", ""))))
                attr_name = re.sub(r"[`*]", "", attr_name).strip()
                if not attr_name or attr_name.lower() in seen_names:
                    continue
                seen_names.add(attr_name.lower())
                required_val = row.get("required", "false").strip().strip("`").lower()
                attributes.append({
                    "name": attr_name,
                    "type": re.sub(r"[`*]", "", row.get("type", "any")).strip(),
                    "required": required_val in ("true", "yes"),
                    "description": strip_html(row.get("description", "")),
                    "default": parse_default(row.get("default", "")),
                })

    return {"name": name, "description": description, "attributes": attributes}


def parse_member_type_file(path, type_name):
    """
    Parse a type reference file (array.md, string.md, etc.).
    Returns list of {name, description, params} dicts.
    """
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return []

    methods = []
    # Split on <details> blocks
    detail_blocks = re.split(r"<details>", content, flags=re.IGNORECASE)
    for block in detail_blocks[1:]:  # skip text before first <details>
        # Extract signature from <summary><code>...</code></summary>
        sig_match = re.search(r"<summary><code>(.*?)</code></summary>", block, re.DOTALL | re.IGNORECASE)
        if not sig_match:
            continue
        signature = sig_match.group(1).strip()

        # method name is before the first `(`
        method_name_match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", signature)
        if not method_name_match:
            continue
        method_name = method_name_match.group(1)

        # Description: first non-empty text after </summary>
        after_summary = re.sub(r".*?</summary>", "", block, flags=re.DOTALL | re.IGNORECASE, count=1)
        description = ""
        for line in after_summary.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("|") and not stripped.startswith("Arguments") \
                    and not stripped.startswith("<") and not stripped.startswith("#"):
                description = strip_html(stripped)
                break

        # Arguments table (may not exist for no-arg methods)
        params = []
        lines = after_summary.splitlines()
        for i, line in enumerate(lines):
            if re.match(r"^\|\s*(Argument|argument)", line):
                rows = parse_table_rows(lines, i)
                for row in rows:
                    arg_name = row.get("argument", "")
                    arg_name = re.sub(r"[`*]", "", arg_name).strip()
                    if not arg_name:
                        continue
                    params.append({
                        "name": arg_name,
                        "type": re.sub(r"[`*]", "", row.get("type", "any")).strip(),
                        "required": row.get("required", "false").strip().strip("`") == "true",
                        "description": "",
                        "default": parse_default(row.get("default", "")),
                    })
                break

        methods.append({"name": method_name, "description": description, "params": params})

    return methods


# ---------------------------------------------------------------------------
# Snippet builders
# ---------------------------------------------------------------------------

def build_snippets(params):
    """
    Build (required_snippet, full_snippet) tuple from a params list.
    Required snippet: only required params.
    Full snippet: all params.
    """
    required = [p for p in params if p["required"]]
    all_params = params

    def make_snippet(param_list):
        if not param_list:
            return "($0)"
        parts = []
        for i, p in enumerate(param_list, 1):
            parts.append("${" + str(i) + ":" + p["name"] + "}")
        return "(" + ", ".join(parts) + "$0)"

    return (make_snippet(required), make_snippet(all_params))


# ---------------------------------------------------------------------------
# Module directory discovery
# ---------------------------------------------------------------------------

def find_module_reference_dirs(docs_path, ref_type):
    """
    Find all `reference/<ref_type>` directories under MODULE_ROOTS.
    ref_type is 'built-in-functions' or 'components'.
    Returns list of (module_name, dir_path) tuples.
    """
    found = []
    for module_root in MODULE_ROOTS:
        root_path = os.path.join(docs_path, module_root)
        if not os.path.isdir(root_path):
            continue
        for module_name in sorted(os.listdir(root_path)):
            module_path = os.path.join(root_path, module_name)
            if not os.path.isdir(module_path):
                continue
            ref_path = os.path.join(module_path, "reference", ref_type)
            if os.path.isdir(ref_path):
                found.append((module_name, ref_path))
    return found


def walk_md_files(directory):
    """Yield all .md files (excluding README.md) under directory, recursively."""
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        for fname in sorted(files):
            if fname.endswith(".md") and fname != "README.md":
                yield os.path.join(root, fname)


# ---------------------------------------------------------------------------
# Main generators
# ---------------------------------------------------------------------------

def generate_bif_data(docs_path):
    """Walk all BIF markdown files (core + modules) and return parsed data."""
    results = {}
    missing = []

    # Core BIFs: organized in category subdirectories
    bif_dir = os.path.join(docs_path, BIF_ROOT)
    for fpath in walk_md_files(bif_dir):
        data = parse_bif_file(fpath)
        if data:
            rel = os.path.relpath(fpath, docs_path).replace(os.sep, '/').lower()
            data['url_path'] = rel[:-3] if rel.endswith('.md') else rel
            data['category'] = os.path.basename(os.path.dirname(fpath))
            results[data["name"]] = data
        else:
            missing.append(fpath)

    core_count = len(results)

    # Module BIFs: flat files or category subdirectories
    module_dirs = find_module_reference_dirs(docs_path, "built-in-functions")
    for module_name, ref_dir in module_dirs:
        before = len(results)
        for fpath in walk_md_files(ref_dir):
            data = parse_bif_file(fpath)
            if data:
                rel = os.path.relpath(fpath, docs_path).replace(os.sep, '/').lower()
                data['url_path'] = rel[:-3] if rel.endswith('.md') else rel
                data['category'] = module_name
                results[data["name"]] = data
            else:
                missing.append(fpath)
        added = len(results) - before
        if added:
            print(f"    {module_name}: +{added} BIFs")

    if missing:
        print(f"  [warn] Could not parse {len(missing)} BIF files", file=sys.stderr)

    return results, core_count


def generate_component_data(docs_path):
    """Walk all component markdown files (core + modules) and return parsed data."""
    results = {}

    # Core components
    comp_dir = os.path.join(docs_path, COMPONENT_ROOT)
    for fpath in walk_md_files(comp_dir):
        data = parse_component_file(fpath)
        if data:
            results[data["name"]] = data

    core_count = len(results)

    # Module components
    module_dirs = find_module_reference_dirs(docs_path, "components")
    for module_name, ref_dir in module_dirs:
        before = len(results)
        for fpath in walk_md_files(ref_dir):
            data = parse_component_file(fpath)
            if data:
                results[data["name"]] = data
        added = len(results) - before
        if added:
            print(f"    {module_name}: +{added} components")

    return results, core_count


def generate_member_data(docs_path):
    """Parse all type member function files."""
    types_dir = os.path.join(docs_path, TYPES_ROOT)
    results = {}

    for fname, type_name in MEMBER_TYPE_FILES.items():
        fpath = os.path.join(types_dir, fname)
        if not os.path.exists(fpath):
            print(f"  [warn] Missing type file: {fpath}", file=sys.stderr)
            continue
        methods = parse_member_type_file(fpath, type_name)
        if methods:
            results[type_name] = {m["name"]: m for m in methods}

    return results


# ---------------------------------------------------------------------------
# JSON serializers (match existing format expected by basecompletions/__init__.py)
# ---------------------------------------------------------------------------

def build_functions_json(bif_data):
    """
    {FuncName: [description, [required_snippet, full_snippet]]}
    """
    out = {}
    for name, data in sorted(bif_data.items()):
        req_snip, full_snip = build_snippets(data["params"])
        out[name] = [data["description"], [req_snip, full_snip]]
    return out


def build_tags_json(component_data):
    """
    {tagName: {attributes: [[required_names], [optional_names]], attribute_values: {}}}
    """
    out = {}
    for name, data in sorted(component_data.items()):
        required = [a["name"] for a in data["attributes"] if a["required"]]
        optional = [a["name"] for a in data["attributes"] if not a["required"]]
        out[name] = {"attributes": [required, optional], "attribute_values": {}}
    return out


def build_member_functions_json(member_data):
    """
    {typeName: {funcName: [description, [required_snippet, full_snippet]]}}

    Merges with any existing JSON so that types under-documented in the docs
    repo (e.g. string has only 3 detail blocks) retain their prior entries.
    """
    # Load existing data to use as fallback
    existing = {}
    existing_path = os.path.join(JSON_DIR, "boxlang_member_functions.json")
    if os.path.exists(existing_path):
        try:
            with open(existing_path, encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    out = {}
    all_types = set(member_data.keys()) | set(existing.keys())
    for type_name in sorted(all_types):
        docs_methods = member_data.get(type_name, {})
        existing_methods = existing.get(type_name, {})

        # Start from existing, then overlay with fresh docs data
        merged = dict(existing_methods)
        for func_name, data in docs_methods.items():
            req_snip, full_snip = build_snippets(data["params"])
            merged[func_name] = [data["description"], [req_snip, full_snip]]

        if merged:
            out[type_name] = {k: merged[k] for k in sorted(merged)}

    return out


def build_function_params_json(bif_data):
    """
    Full parameter data for the documentation popup.
    {FuncName: {description, params: [{name, type, required, description, default}], url_path, category}}
    """
    out = {}
    for name, data in sorted(bif_data.items()):
        out[name] = {
            "description": data["description"],
            "params": data["params"],
            "url_path": data.get("url_path", ""),
            "category": data.get("category", ""),
        }
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate BoxLang completion JSON from boxlang-docs")
    parser.add_argument(
        "--docs-path",
        default=os.path.join(os.path.dirname(REPO_ROOT), "boxlang-docs"),
        help="Path to the boxlang-docs repo (default: ../boxlang-docs)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Run 'git pull' in the docs repo before generating",
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help="Clone the docs repo to --docs-path if it doesn't exist",
    )
    args = parser.parse_args()

    docs_path = os.path.abspath(args.docs_path)

    # Clone if requested and missing
    if not os.path.isdir(docs_path):
        if args.clone:
            print(f"Cloning {DOCS_REPO_URL} → {docs_path}")
            subprocess.run(["git", "clone", "--depth=1", DOCS_REPO_URL, docs_path], check=True)
        else:
            print(f"Error: docs path not found: {docs_path}", file=sys.stderr)
            print("Use --clone to clone it automatically, or --docs-path to specify a custom path.", file=sys.stderr)
            sys.exit(1)
    elif args.update:
        print(f"Updating {docs_path}...")
        subprocess.run(["git", "-C", docs_path, "pull", "--ff-only"], check=True)

    print(f"Reading docs from: {docs_path}")

    # Parse
    print("Parsing BIF files...")
    bif_data, core_bif_count = generate_bif_data(docs_path)
    print(f"  Found {len(bif_data)} BIFs total ({core_bif_count} core + {len(bif_data) - core_bif_count} module)")

    print("Parsing component files...")
    component_data, core_comp_count = generate_component_data(docs_path)
    print(f"  Found {len(component_data)} components total ({core_comp_count} core + {len(component_data) - core_comp_count} module)")

    print("Parsing member function files...")
    member_data = generate_member_data(docs_path)
    total_members = sum(len(v) for v in member_data.values())
    print(f"  Found {total_members} member functions across {len(member_data)} types")

    # Build JSON payloads
    functions_json = build_functions_json(bif_data)
    tags_json = build_tags_json(component_data)
    member_json = build_member_functions_json(member_data)
    params_json = build_function_params_json(bif_data)

    # Write
    os.makedirs(JSON_DIR, exist_ok=True)
    outputs = [
        ("boxlang_functions.json", functions_json),
        ("boxlang_tags.json", tags_json),
        ("boxlang_member_functions.json", member_json),
        ("boxlang_function_params.json", params_json),
    ]
    for fname, data in outputs:
        fpath = os.path.join(JSON_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {fpath}  ({len(data)} entries)")

    print("\nDone. JSON files updated.")


if __name__ == "__main__":
    main()
