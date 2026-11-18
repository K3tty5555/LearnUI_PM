#!/usr/bin/env python3
"""Export original images for a graphic case and record them in data/graphics.json.

    python3 scripts/graphics/export_originals.py <slug> <source> [<source> ...] [--origin note|official|author]
                                                  [--no-enhance] [--start 1]

Each source (PNG/JPG/WebP crop, or an official file) becomes assets/graphics/<slug>-<n>.webp at
quality 94, plus <slug>-<n>@2x.webp for high-density screens (served through srcset), by size:

- long side up to 1400 px (note crops): kept as is; the @2x file is made with Real-ESRGAN
  (realesrgan-x4plus: 4x up, then Lanczos down to exactly 2x) unless --no-enhance is given;
- long side 1401-1819 px: kept as is, no @2x file (it is already sharp enough);
- long side 1820 px or more (official files): the 1x file is scaled to a 1400 px long side and the
  @2x file is the original's own pixels, scaled to at most twice that. No AI involved.

The case's "images" entries are updated in place: file, w, h, hd and origin are written; captions
already present are kept, new entries get placeholder captions that validate-data.py will reject
until they are filled in. Real-ESRGAN location: $REALESRGAN_DIR or
~/.local/share/codex-tools/realesrgan-ncnn-vulkan (binary + models/).
"""
import argparse
import json
import os
import subprocess
import tempfile
from collections import OrderedDict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/graphics.json"
ASSETS = ROOT / "assets/graphics"
LONG_1X = 1400       # long side of the standard file
REAL_HD_MIN = 1820   # sources at least this long get a real-pixel @2x file instead of an AI one
ESRGAN = Path(os.environ.get("REALESRGAN_DIR", "~/.local/share/codex-tools/realesrgan-ncnn-vulkan")).expanduser()


def enhance(src: Image.Image, dest: Path):
    """Real-ESRGAN 4x, then a clean Lanczos downscale to exactly 2x the source."""
    binary = ESRGAN / "realesrgan-ncnn-vulkan"
    if not binary.exists():
        raise SystemExit(f"Real-ESRGAN not found at {binary}; install it or pass --no-enhance")
    with tempfile.TemporaryDirectory() as tmp:
        i, o = Path(tmp) / "in.png", Path(tmp) / "out.png"
        src.save(i)
        subprocess.run([str(binary), "-i", str(i), "-o", str(o), "-n", "realesrgan-x4plus", "-m", str(ESRGAN / "models")],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Image.open(o).convert("RGB").resize((src.width * 2, src.height * 2), Image.LANCZOS).save(dest, "WEBP", quality=88, method=6)


def scaled(im: Image.Image, long: int) -> Image.Image:
    """Lanczos downscale so the longer side is at most `long` pixels (never upscales)."""
    factor = long / max(im.size)
    if factor >= 1:
        return im
    return im.resize((round(im.width * factor), round(im.height * factor)), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("sources", nargs="+", type=Path)
    ap.add_argument("--origin", choices=["note", "official", "author"], default="note",
                    help="note: cropped from a compiler's note; official: publisher or studio file; author: posted by the designer")
    ap.add_argument("--no-enhance", action="store_true")
    ap.add_argument("--start", type=int, default=1, help="number of the first image (to replace or append)")
    args = ap.parse_args()
    data = json.loads(DATA.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
    case = next((c for c in data["cases"] if c["slug"] == args.slug), None)
    if case is None:
        raise SystemExit(f"Add the case '{args.slug}' to data/graphics.json first.")
    images = case.setdefault("images", [])
    ASSETS.mkdir(parents=True, exist_ok=True)
    for offset, source in enumerate(args.sources):
        n = args.start + offset
        name = f"{args.slug}-{n}.webp"
        src = Image.open(source).convert("RGB")
        long = max(src.size)
        hd_name = name.replace(".webp", "@2x.webp")
        hd = None
        if long >= REAL_HD_MIN:
            pic = scaled(src, LONG_1X)
            hd = scaled(src, 2 * LONG_1X)
        else:
            pic = src
        pic.save(ASSETS / name, "WEBP", quality=94, method=6)
        entry = next((im for im in images if im["file"] == name), None)
        if entry is None:
            entry = OrderedDict(file=name, caption="TODO", captionZh="TODO")
            images.append(entry)
        entry["w"], entry["h"] = pic.size
        if hd is not None:
            hd.save(ASSETS / hd_name, "WEBP", quality=88, method=6)
            entry["hd"] = hd_name
            entry["origin"] = args.origin
        elif args.no_enhance or long > LONG_1X:
            entry.pop("hd", None)
            (ASSETS / hd_name).unlink(missing_ok=True)
            entry["origin"] = args.origin
        else:
            enhance(pic, ASSETS / hd_name)
            entry["hd"] = hd_name
            entry["origin"] = "enhanced" if args.origin == "note" else args.origin + "-enhanced"
        print(f"{name}: {pic.width}x{pic.height}{' + ' + hd_name if 'hd' in entry else ''} ({entry['origin']})")
    images.sort(key=lambda im: int(im["file"].rsplit("-", 1)[1].split(".")[0].split("@")[0]))
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
