#!/usr/bin/env python3
"""
Refresh the `bif_names` list in syntaxes/BoxLang.sublime-syntax from the boxlang-docs repository.

Usage:
    python3 scripts/generate_syntax_bifs.py --docs-path /path/to/boxlang-docs

Existing names are kept, and every core built-in function documented under
boxlang-language/reference/built-in-functions is added. The list is rewritten sorted.
"""

import argparse
import glob
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SYNTAX_FILE = os.path.join(os.path.dirname(SCRIPT_DIR), "syntaxes", "BoxLang.sublime-syntax")
BIF_ROOT = "boxlang-language/reference/built-in-functions"
PER_ROW = 8


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-path", required=True, help="Path to a local boxlang-docs checkout")
    args = parser.parse_args()

    root = os.path.join(args.docs_path, BIF_ROOT)
    if not os.path.isdir(root):
        sys.exit("BIF docs directory not found: {}".format(root))

    with open(SYNTAX_FILE, encoding="utf-8") as handle:
        lines = handle.read().split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith("  bif_names:"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "    )")

    names = {}
    for entry in " ".join(lines[start + 2:end]).split("|"):
        entry = entry.strip()
        if entry:
            names[entry.lower()] = entry
    for path in glob.glob(os.path.join(root, "**", "*.md"), recursive=True):
        name = os.path.basename(path)[:-3]
        if name.lower() not in ("readme", "summary"):
            names.setdefault(name.lower(), name)

    ordered = sorted(names.values(), key=str.lower)
    rows = ["      " + " | ".join(ordered[i:i + PER_ROW]) for i in range(0, len(ordered), PER_ROW)]
    lines[start + 2:end] = [row + (" |" if idx < len(rows) - 1 else "") for idx, row in enumerate(rows)]

    with open(SYNTAX_FILE, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    print("Wrote {} BIF names to {}".format(len(ordered), SYNTAX_FILE))


if __name__ == "__main__":
    main()
