#!/usr/bin/env python3
"""Validate local content contracts without third-party dependencies."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return json.load(handle)


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def main():
    refs = load("data/pm/references.json")
    taxonomy = load("data/pm/taxonomy.json")
    required = {
        "slug", "title", "titleEn", "summary", "productTypes", "pageTypes",
        "layouts", "moods", "states", "scenarios", "structure", "visualTraits",
        "promptHints", "demo", "source"
    }
    allowed = {key: {item["id"] for item in values} for key, values in taxonomy.items()}
    seen = set()
    errors = 0

    for ref in refs:
        slug = ref.get("slug", "<missing>")
        missing = required - set(ref)
        if missing:
            errors += fail(f"{slug}: missing fields {sorted(missing)}")
        if slug in seen:
            errors += fail(f"duplicate reference slug: {slug}")
        seen.add(slug)
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            errors += fail(f"{slug}: invalid slug")
        for key in ("productTypes", "pageTypes", "layouts", "moods", "states"):
            unknown = set(ref.get(key, [])) - allowed[key]
            if unknown:
                errors += fail(f"{slug}: unknown {key}: {sorted(unknown)}")
        if len(ref.get("states", [])) < 3:
            errors += fail(f"{slug}: at least three states are required")
        demo = os.path.join(ROOT, "demos", ref.get("demo", "") + ".html")
        if not os.path.isfile(demo):
            errors += fail(f"{slug}: missing demo {ref.get('demo')}")

    if errors:
        return 1
    print(f"Validated {len(refs)} page references and {sum(len(v) for v in taxonomy.values())} taxonomy values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
