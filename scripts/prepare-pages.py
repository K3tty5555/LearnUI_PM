#!/usr/bin/env python3
"""Prepare a generated static site for a GitHub Pages project URL."""

import argparse
import re
from pathlib import Path


TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".webmanifest", ".xml", ".txt"}


def prefix_root_urls(text: str, base: str) -> str:
    base = "/" + base.strip("/") if base.strip("/") else ""
    if not base:
        return text
    # Every generated root-relative URL is quoted. Keep protocol URLs and already
    # prefixed paths untouched so the script remains safe to run twice.
    pattern = re.compile(r'(["\'])/(?!/)(?!' + re.escape(base.lstrip("/")) + r'(?:/|["\']))')
    return pattern.sub(lambda match: match.group(1) + base + "/", text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    parser.add_argument("--base", required=True, help="Project path, e.g. /LearnUI_PM")
    args = parser.parse_args()
    changed = 0
    for path in args.site.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        original = path.read_text(encoding="utf-8")
        updated = prefix_root_urls(original, args.base)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    (args.site / ".nojekyll").touch()
    print(f"Prepared {changed} files for GitHub Pages base path {args.base}")


if __name__ == "__main__":
    main()
