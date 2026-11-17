#!/usr/bin/env python3
"""Every logo must sit centred and fully inside its stage, at desktop, wide and phone widths.

Usage: python3 scripts/test-logo-layout.py site [--base /LearnUI_PM] [--engines chromium,webkit]
Requires Playwright. Serves the built site locally; no network access.
"""
import argparse
import functools
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 2  # px between image centre and stage centre
VIEWPORTS = [(1440, 1000), (2000, 1100), (390, 844)]
# (container selector, image selector) pairs that must hold a centred, contained logo.
BOXES = {
    "hub": [(".logo-stage", ".logo-art")],
    "detail": [(".logo-plate", ".logo-art"), (".logo-size-box", ".logo-size-img")],
}

MEASURE = """(pairs) => pairs.flatMap(([box, img]) => [...document.querySelectorAll(box)].map((el, i) => {
  const a = el.getBoundingClientRect(), image = el.querySelector(img);
  if (!image) return {box, i, error: 'missing image'};
  const b = image.getBoundingClientRect();
  return {box, i, dx: (b.left + b.width / 2) - (a.left + a.width / 2), dy: (b.top + b.height / 2) - (a.top + a.height / 2),
          inside: b.left >= a.left - 0.5 && b.right <= a.right + 0.5 && b.top >= a.top - 0.5 && b.bottom <= a.bottom + 0.5,
          loaded: image.complete && image.naturalWidth > 0, w: Math.round(b.width), h: Math.round(b.height)};
}))"""


def serve(site, base):
    root = Path(site).resolve()
    prefix = "/" + base.strip("/") if base.strip("/") else ""

    class Handler(SimpleHTTPRequestHandler):
        def translate_path(self, path):
            if prefix and path.startswith(prefix):
                path = path[len(prefix):] or "/"
            return super().translate_path(path)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}{prefix}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site")
    parser.add_argument("--base", default="")
    parser.add_argument("--engines", default="chromium")
    args = parser.parse_args()
    slugs = [logo["slug"] for logo in json.loads((ROOT / "data/logos.json").read_text(encoding="utf-8"))["logos"]]
    server, base = serve(args.site, args.base)
    failures, checked = [], 0
    with sync_playwright() as p:
        for engine in args.engines.split(","):
            browser = getattr(p, engine).launch()
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                pages = [("hub", "/logos/")] + [("detail", f"/logos/{slug}/") for slug in slugs]
                for kind, path in pages:
                    page.goto(base + path)
                    # Lazy images below the fold never start loading on their own; load them all, but never wait forever.
                    page.evaluate("""() => Promise.race([
                      Promise.all([...document.images].map(i => { i.loading = 'eager'; return i.decode().catch(() => {}); })),
                      new Promise(r => setTimeout(r, 5000))])""")
                    for r in page.evaluate(MEASURE, BOXES[kind]):
                        checked += 1
                        where = f"{engine} {width}px {path} {r['box']}[{r['i']}]"
                        if r.get("error"):
                            failures.append(f"{where}: {r['error']}")
                        elif not r["loaded"]:
                            failures.append(f"{where}: image not loaded")
                        elif abs(r["dx"]) > TOLERANCE or abs(r["dy"]) > TOLERANCE or not r["inside"]:
                            failures.append(f"{where}: off-centre dx={r['dx']:.0f} dy={r['dy']:.0f} size={r['w']}x{r['h']} inside={r['inside']}")
                    if kind == "hub":
                        checked += 1
                        rows = page.evaluate("""() => { const g = document.querySelector('.logo-glossary').getBoundingClientRect(), rows = {};
                          document.querySelectorAll('.logo-glossary-item').forEach(el => { const r = el.getBoundingClientRect();
                            (rows[Math.round(r.top)] = rows[Math.round(r.top)] || []).push(r.width / g.width); });
                          return Object.values(rows); }""")
                        # A lone card on a row is fine only when it spans the row (single column, or the spanning last card).
                        stranded = [row for row in rows if len(row) == 1 and row[0] < 0.95]
                        if stranded:
                            failures.append(f"{engine} {width}px /logos/ glossary: stranded card, rows={[len(r) for r in rows]}")
                page.close()
            browser.close()
    server.shutdown()
    if failures:
        print("\n".join(failures[:40]))
        raise SystemExit(f"{len(failures)} of {checked} logo placements failed")
    print(f"All {checked} logo placements are centred and contained.")


if __name__ == "__main__":
    main()
