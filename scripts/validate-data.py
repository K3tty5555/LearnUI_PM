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
    errors = validate_logos()
    errors += validate_graphics()
    if errors:
        return 1
    print("Validated logos and graphic design data.")
    return 0

    errors += validate_logos()
    errors += validate_graphics()
    if errors:
        return 1
    print(f"Validated {len(refs)} page references and {sum(len(v) for v in taxonomy.values())} taxonomy values.")
    return 0


def validate_logos():
    """Logo atlas: known type/use ids, bilingual text pairs, and a shipped image per logo."""
    if not os.path.exists(os.path.join(ROOT, "data/logos.json")):
        return 0
    data = load("data/logos.json")
    types = {t["id"] for t in data["types"]}
    issues = {i["id"] for i in data.get("issues", [])}
    uses = {u["id"] for u in data["uses"]}
    errors, seen = 0, set()
    pairs = (("name", None), ("about", "aboutZh"), ("audience", "audienceZh"), ("license", "licenseZh"),
             ("read", "readZh"), ("prompt", "promptZh"), ("maker", "makerZh"), ("url", None), ("imageSource", None))
    for logo in data["logos"]:
        slug = logo.get("slug", "")
        if not re.fullmatch(r"[a-z0-9-]+", slug) or slug in seen:
            errors += fail(f"logo {slug!r}: slug must be unique kebab-case")
        seen.add(slug)
        for en_key, zh_key in pairs:
            if not logo.get(en_key) or (zh_key and not logo.get(zh_key)):
                errors += fail(f"logo {slug}: {en_key}{'/' + zh_key if zh_key else ''} required")
        if bool(logo.get("note")) != bool(logo.get("noteZh")):
            errors += fail(f"logo {slug}: note and noteZh must come together")
        if logo.get("type") not in types:
            errors += fail(f"logo {slug}: unknown type {logo.get('type')!r}")
        if logo.get("issue") not in issues:
            errors += fail(f"logo {slug}: unknown issue {logo.get('issue')!r}")
        if logo.get("use") not in uses:
            errors += fail(f"logo {slug}: unknown use {logo.get('use')!r}")
        parts = logo.get("parts", [])
        if len(parts) < 2 or any(not all(p.get(k) for k in ("name", "nameZh", "desc", "descZh")) for p in parts):
            errors += fail(f"logo {slug}: at least two bilingual parts are required")
        if not os.path.isfile(os.path.join(ROOT, "assets/logos", logo.get("image", "") + ".webp")):
            errors += fail(f"logo {slug}: missing assets/logos/{logo.get('image')}.webp")
    return errors


def webp_size(path):
    """Width and height from a WebP header (VP8, VP8L or VP8X), standard library only."""
    with open(path, "rb") as handle:
        head = handle.read(30)
    if head[:4] != b"RIFF" or head[8:12] != b"WEBP":
        return None
    chunk = head[12:16]
    if chunk == b"VP8X":
        return 1 + int.from_bytes(head[24:27], "little"), 1 + int.from_bytes(head[27:30], "little")
    if chunk == b"VP8 ":
        return int.from_bytes(head[26:28], "little") & 0x3FFF, int.from_bytes(head[28:30], "little") & 0x3FFF
    if chunk == b"VP8L":
        bits = int.from_bytes(head[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    return None


def validate_covers(cases):
    """List-page covers must exist and match the current source images (scripts/graphics/make_covers.py)."""
    sys.path.insert(0, os.path.join(ROOT, "scripts/graphics"))
    try:
        import make_covers
    except ImportError:  # Pillow missing: the layout test still catches a stale or absent cover.
        return 0
    errors = 0
    for case in cases:
        for problem in make_covers.build(case, check=True):
            errors += fail(f"graphic {problem}")
    return errors


def validate_graphics():
    """Graphic design cases: known ids, a specimen file, bilingual text pairs, all five layer notes, valid colours."""
    if not os.path.exists(os.path.join(ROOT, "data/graphics.json")):
        return 0
    data = load("data/graphics.json")
    types = {t["id"] for t in data["types"]}
    techs = {t["id"] for t in data["techniques"]}
    issues = {i["id"] for i in data["issues"]}
    style_tags = {}
    errors = 0
    for st in data.get("styleTags", []):
        if not st.get("id") or not st.get("name") or not st.get("nameZh"):
            errors += fail(f"styleTag {st.get('id')!r}: id, name and nameZh required")
        else:
            style_tags[st["id"]] = st
    seen = set()
    for case in data["cases"]:
        slug = case.get("slug", "")
        if not re.fullmatch(r"[a-z0-9-]+", slug) or slug in seen:
            errors += fail(f"graphic {slug!r}: slug must be unique kebab-case")
        seen.add(slug)
        if case.get("type") not in types:
            errors += fail(f"graphic {slug}: unknown type {case.get('type')!r}")
        if case.get("issue") not in issues:
            errors += fail(f"graphic {slug}: unknown issue {case.get('issue')!r}")
        unknown = set(case.get("techniques", [])) - techs
        if unknown or not case.get("techniques"):
            errors += fail(f"graphic {slug}: techniques missing or unknown {sorted(unknown)}")
        if case.get("specimen", "reconstruction") not in ("reconstruction", "style-demo"):
            errors += fail(f"graphic {slug}: specimen must be 'reconstruction' or 'style-demo'")
        unknown_styles = set(case.get("styleTags", [])) - set(style_tags)
        if unknown_styles or not case.get("styleTags"):
            errors += fail(f"graphic {slug}: styleTags missing or unknown {sorted(unknown_styles)}")
        for en_key in ("summary", "read", "imagePrompt", "codePrompt"):
            if not case.get(en_key) or not case.get(en_key + "Zh"):
                errors += fail(f"graphic {slug}: {en_key}/{en_key}Zh required")
        for key in ("grid", "type", "focus", "space"):
            if not case.get("layers", {}).get(key) or not case.get("layers", {}).get(key + "Zh"):
                errors += fail(f"graphic {slug}: layers.{key} and {key}Zh required")
        if not case.get("palette") or any(not re.fullmatch(r"#[0-9A-Fa-f]{6}", c.get("hex", "")) for c in case["palette"]):
            errors += fail(f"graphic {slug}: palette needs #RRGGBB colours")
        if not case.get("credits") or not case.get("sourceLabel"):
            errors += fail(f"graphic {slug}: credits and sourceLabel required")
        for url in case.get("sourceUrls", []):
            if not str(url).startswith("https://"):
                errors += fail(f"graphic {slug}: sourceUrls entry must be an https link: {url}")
        if any(im.get("origin", "").startswith(("official", "author")) for im in case.get("images", [])) and not case.get("sourceUrls"):
            errors += fail(f"graphic {slug}: official images need sourceUrls (the pages they were taken from)")
        images = case.get("images", [])
        if not images:
            errors += fail(f"graphic {slug}: at least one original image required")
        for im in images:
            if not im.get("caption") or not im.get("captionZh"):
                errors += fail(f"graphic {slug}: image {im.get('file')} needs caption and captionZh")
            if im.get("hd") and not os.path.isfile(os.path.join(ROOT, "assets/graphics", im["hd"])):
                errors += fail(f"graphic {slug}: missing assets/graphics/{im['hd']}")
            if im.get("origin") not in ("note", "official", "enhanced", "official-enhanced", "author", "author-enhanced"):
                errors += fail(f"graphic {slug}: {im.get('file')} has unknown origin {im.get('origin')!r}")
            path = os.path.join(ROOT, "assets/graphics", im.get("file", ""))
            if os.path.isfile(path) and webp_size(path) != (im.get("w"), im.get("h")):
                errors += fail(f"graphic {slug}: {im['file']} is {webp_size(path)}, data says {(im.get('w'), im.get('h'))}")
            if im.get("hd") and os.path.isfile(os.path.join(ROOT, "assets/graphics", im["hd"])):
                hd = webp_size(os.path.join(ROOT, "assets/graphics", im["hd"])) or (0, 0)
                w, h = im.get("w") or 1, im.get("h") or 1
                # AI copies are exactly 2x; copies cut from a large official file are 1.3-2x. Same shape either way.
                if not (1.3 <= hd[0] / w <= 2.0 and abs((hd[0] / hd[1]) / (w / h) - 1) < 0.01) or (
                        im.get("origin", "").endswith("enhanced") and hd != (w * 2, h * 2)):
                    errors += fail(f"graphic {slug}: {im['hd']} is {hd}, not a same-shape 1.3-2x copy of {(w, h)}")
            if not os.path.isfile(os.path.join(ROOT, "assets/graphics", im.get("file", ""))):
                errors += fail(f"graphic {slug}: missing assets/graphics/{im.get('file')}")
        if not os.path.isfile(os.path.join(ROOT, "demos/graphic", slug + ".html")):
            errors += fail(f"graphic {slug}: missing demos/graphic/{slug}.html")
    errors += validate_covers(data["cases"])
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
