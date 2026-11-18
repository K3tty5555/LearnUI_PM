#!/usr/bin/env python3
"""Find and crop the original artworks on compilation pages (one note page → several images).

    python3 scripts/graphics/crop_originals.py <download-dir> <out-dir> [--top 0.155] [--bottom 0.81] [--skip 1]

Each page's background colour is sampled from its side edges; everything that differs is
split recursively along empty gutters (XY-cut) until only solid blocks remain. Blocks inside
the [top, bottom] band of the page are kept, which drops the compiler's title and captions.

Writes <out-dir>/p<page>-<n>.png crops, blocks.json and contact-sheet.jpg. Always open the
contact sheet before using a crop: confirm it contains only the original work, then map
crops to case images with export_originals.py.
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def split(mask, y0, y1, x0, x1, depth=0, out=None):
    out = [] if out is None else out
    sub = mask[y0:y1, x0:x1]
    if sub.size == 0 or sub.mean() < 0.02:
        return out
    rows, cols = np.where(sub.mean(1) > 0.02)[0], np.where(sub.mean(0) > 0.02)[0]
    if not len(rows) or not len(cols):
        return out
    y0, y1, x0, x1 = y0 + rows[0], y0 + rows[-1] + 1, x0 + cols[0], x0 + cols[-1] + 1
    sub = mask[y0:y1, x0:x1]
    for axis in (0, 1):
        profile = sub.mean(1) if axis == 0 else sub.mean(0)
        best, run = None, 0
        for i, empty in enumerate(profile < 0.01):
            run = run + 1 if empty else 0
            if run >= 10 and (best is None or run > best[1]):
                best = (i - run + 1, run)
        if best and depth < 6:
            cut = best[0] + best[1] // 2
            if axis == 0:
                split(mask, y0, y0 + cut, x0, x1, depth + 1, out); split(mask, y0 + cut, y1, x0, x1, depth + 1, out)
            else:
                split(mask, y0, y1, x0, x0 + cut, depth + 1, out); split(mask, y0, y1, x0 + cut, x1, depth + 1, out)
            return out
    out.append((int(x0), int(y0), int(x1), int(y1)))
    return out


def page_number(path):
    m = re.search(r"_(\d+)\.png$", path.name)
    return int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("download_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--top", type=float, default=0.155, help="ignore everything above this fraction of the page")
    ap.add_argument("--bottom", type=float, default=0.81, help="ignore everything below this fraction of the page")
    ap.add_argument("--skip", type=int, nargs="*", default=[1], help="page numbers to skip (cover pages)")
    ap.add_argument("--min-area", type=float, default=0.025, help="minimum block area as a fraction of the page")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    blocks, tiles = {}, []
    for page in sorted(args.download_dir.glob("*.png"), key=page_number):
        n = page_number(page)
        if n in args.skip:
            continue
        im = Image.open(page).convert("RGB")
        a = np.asarray(im).astype(int)
        bg = np.median(np.concatenate([a[:, 8].reshape(-1, 3), a[:, -8].reshape(-1, 3)]), axis=0)
        mask = np.abs(a - bg).sum(2) > 40
        h, w = mask.shape
        found = [b for b in split(mask, int(h * args.top), int(h * args.bottom), 0, w)
                 if (b[2] - b[0]) * (b[3] - b[1]) > w * h * args.min_area]
        blocks[n] = found
        for k, box in enumerate(found, 1):
            crop = im.crop(box)
            crop.save(args.out_dir / f"p{n}-{k}.png")
            tile = crop.copy(); tile.thumbnail((300, 300))
            card = Image.new("RGB", (310, 330), "white"); card.paste(tile, (5, 5))
            ImageDraw.Draw(card).text((6, 312), f"p{n}-{k}  {crop.width}x{crop.height}", fill=(0, 0, 0))
            tiles.append(card)
    (args.out_dir / "blocks.json").write_text(json.dumps(blocks, indent=1))
    if tiles:
        cols = 8; rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (310 * cols, 330 * rows), (230, 230, 230))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % cols) * 310, (i // cols) * 330))
        sheet.save(args.out_dir / "contact-sheet.jpg", quality=82)
    print(f"{len(tiles)} crops from {len(blocks)} pages → {args.out_dir} (check contact-sheet.jpg)")


if __name__ == "__main__":
    main()
