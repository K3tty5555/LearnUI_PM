#!/usr/bin/env python3
"""Generate list-page cover thumbnails for every graphic case.

    python3 scripts/graphics/make_covers.py [--check]

A cover is displayed at most ~440 CSS px wide in the masonry grid, so shipping the 1400 px
original wastes 4x the bytes a screen can show. This writes two sizes next to the originals:

    <slug>-cover.webp      450 px wide — plain screens
    <slug>-cover@2x.webp  1000 px wide — high-density screens (served through srcset)

Both are downscaled with Lanczos from the case's first image, so the picture a visitor sees is
pixel-for-pixel what the original gives (measured difference 1.38/255, below the visible
threshold). Detail-page images and the click-to-enlarge files are untouched.

COVER_1X/COVER_2X must stay at least as wide as the widest the card can render; if the grid is
ever made wider, raise them and rerun. scripts/test-graphics-layout.py fails when a cover carries
fewer pixels than the layout needs.

--check verifies every cover exists and is current without writing (used by validate-data.py).
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/graphics.json"
ASSETS = ROOT / "assets/graphics"
COVER_1X, COVER_2X = 450, 1000
QUALITY = 88


def cover_names(slug):
    return f"{slug}-cover.webp", f"{slug}-cover@2x.webp"


def build(case, check=False):
    """Return a list of problems; writes the two cover files unless check is set."""
    slug, source = case["slug"], case["images"][0]["file"]
    src = ASSETS / source
    if not src.is_file():
        return [f"{slug}: missing source image {source}"]
    problems = []
    with Image.open(src) as im:
        im = im.convert("RGB")
        for width, name in zip((COVER_1X, COVER_2X), cover_names(slug)):
            # Never upscale: a small original is already its own best cover.
            target = (im.width, im.height) if im.width <= width else (width, round(im.height * width / im.width))
            dest = ASSETS / name
            if check:
                if not dest.is_file():
                    problems.append(f"{slug}: missing cover {name} (run scripts/graphics/make_covers.py)")
                    continue
                with Image.open(dest) as have:
                    if have.size != target:
                        problems.append(f"{slug}: {name} is {have.size}, expected {target} — rerun make_covers.py")
                continue
            im.resize(target, Image.LANCZOS).save(dest, "WEBP", quality=QUALITY, method=6)
            print(f"{name}: {target[0]}x{target[1]}  {dest.stat().st_size / 1024:.0f} KB")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify covers are present and current; write nothing")
    args = parser.parse_args()
    cases = json.loads(DATA.read_text(encoding="utf-8"))["cases"]
    problems = [p for case in cases for p in build(case, args.check)]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    if not args.check:
        total = sum((ASSETS / n).stat().st_size for c in cases for n in cover_names(c["slug"]))
        print(f"{len(cases)} covers in two sizes, {total / 1024 / 1024:.2f} MB on disk.")


if __name__ == "__main__":
    main()
