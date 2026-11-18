#!/usr/bin/env python3
"""Graphic design pages must show originals undistorted and sharp, and the breakdown layers must land on the work.

For the hub and every case page, at desktop, wide and phone widths:
- every cover and original image loads, is drawn at its own aspect ratio (no squashing, no cropping
  of mixed portrait/landscape work), and the box reserved before loading matches the file;
- on a 2x screen, images that have an @2x file actually load it;
- the page never scrolls sideways;
- every specimen marks type, focus and space somewhere (a view may carry no lettering), the default
  view draws focus and space marks, and every drawn mark's centre sits inside the specimen canvas;
- on phones the specimen stage hugs the specimen and keeps one height across formats;
- headings share one left edge and size, prompt text fills its box, no stray language divider;
- poster text is never translated when the site switches language (it is part of the artwork).

Usage: python3 scripts/test-graphics-layout.py site [--base /LearnUI_PM] [--engines chromium,webkit]
Requires Playwright. Serves the built site locally; no network access.
"""
import argparse
import importlib.util
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("logo_layout", ROOT / "scripts/test-logo-layout.py")
logo_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logo_layout)
serve = logo_layout.serve

VIEWPORTS = [(1440, 1000), (2000, 1100), (390, 844)]
RATIO_TOLERANCE = 0.015  # 1.5 % between drawn and natural aspect ratio

LOAD_ALL = """() => Promise.race([
  Promise.all([...document.images].map(i => { i.loading = 'eager'; return i.decode().catch(() => {}); })),
  new Promise(r => setTimeout(r, 8000))])"""

IMAGES = """() => [...document.querySelectorAll('.gd-cover img, .gd-orig img')].map(img => {
  const r = img.getBoundingClientRect(), frame = img.closest('.gd-cover, a').getBoundingClientRect();
  const src = img.currentSrc || img.src;
  return {file: src.split('/').pop(), loaded: img.complete && img.naturalWidth > 0,
          natural: img.naturalWidth / (img.naturalHeight || 1), drawn: r.width / (r.height || 1),
          frame: frame.width / (frame.height || 1), w: Math.round(r.width), h: Math.round(r.height),
          wantsHd: /@2x\\.webp/.test(img.getAttribute('srcset') || ''), hd: /@2x\\.webp$/.test(src)};
})"""

OVERFLOW = "() => document.scrollingElement.scrollWidth - window.innerWidth"

LAYERS = """async () => {
  const all = document.querySelector('[data-gd-layer="all"]');
  if (!all) return {error: 'no "all layers" button'};
  all.click();
  await new Promise(r => setTimeout(r, 700));
  const host = document.querySelector('.gd-ov-layer').parentElement.getBoundingClientRect();
  const marks = [...document.querySelectorAll('.gd-ov')].map(el => {
    const r = el.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    return {kind: el.className.replace('gd-ov ', ''), label: el.textContent,
            inside: cx >= host.left && cx <= host.right && cy >= host.top && cy <= host.bottom};
  });
  all.click();
  // A view may legitimately carry no lettering (e.g. a key visual without text); the mark then lives in another view.
  const defined = ['type', 'focus', 'space'].filter(k => document.querySelector('.gd-specimen [data-ov-' + k + ']'));
  return {marks, defined,
          host: [Math.round(host.width), Math.round(host.height)]};
}"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site")
    parser.add_argument("--base", default="")
    parser.add_argument("--engines", default="chromium")
    args = parser.parse_args()
    cases = json.loads((ROOT / "data/graphics.json").read_text(encoding="utf-8"))["cases"]
    paths = ["/graphics/"] + [f"/graphics/{c['slug']}/" for c in cases]
    server, base = serve(args.site, args.base)
    failures, checked = [], 0
    with sync_playwright() as p:
        for engine in args.engines.split(","):
            browser = getattr(p, engine).launch()
            for width, height in VIEWPORTS:
                context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=2,
                                              reduced_motion="reduce")
                page = context.new_page()
                for path in paths:
                    page.goto(base + path)
                    page.evaluate(LOAD_ALL)
                    where = f"{engine} {width}px {path}"
                    for im in page.evaluate(IMAGES):
                        checked += 1
                        if not im["loaded"]:
                            failures.append(f"{where} {im['file']}: not loaded")
                            continue
                        if abs(im["drawn"] / im["natural"] - 1) > RATIO_TOLERANCE:
                            failures.append(f"{where} {im['file']}: distorted, drawn {im['w']}x{im['h']} vs natural ratio {im['natural']:.3f}")
                        if abs(im["frame"] / im["natural"] - 1) > RATIO_TOLERANCE:
                            failures.append(f"{where} {im['file']}: frame ratio {im['frame']:.3f} crops the {im['natural']:.3f} image")
                        if im["wantsHd"] and not im["hd"]:
                            failures.append(f"{where} {im['file']}: 2x screen did not load the @2x file")
                    checked += 1
                    overflow = page.evaluate(OVERFLOW)
                    if overflow > 1:
                        failures.append(f"{where}: page scrolls sideways by {overflow}px")
                    if path != "/graphics/":
                        checked += 1
                        result = page.evaluate(LAYERS)
                        if result.get("error"):
                            failures.append(f"{where}: {result['error']}")
                            continue
                        kinds = {m["kind"] for m in result["marks"]}
                        for need in ("type", "focus", "space"):
                            if need not in result["defined"]:
                                failures.append(f"{where}: specimen marks no data-ov-{need} element")
                        if not {"gd-ov-focus", "gd-ov-space"} <= kinds:
                            failures.append(f"{where}: default view draws no focus or space mark ({sorted(kinds)})")
                        if width <= 760:
                            # Phones: the stage hugs the specimen, and switching formats never changes its height.
                            fit = page.evaluate("""async () => {
                              const st = document.querySelector('[class*="stage-detail-graphic-"]'), sp = st.querySelector('.gd-specimen');
                              const hs = [], gaps = [];
                              const btns = [...sp.querySelectorAll('[data-format-btn]')];
                              for (const b of (btns.length ? btns : [null])) {
                                if (b) { b.click(); await new Promise(r => setTimeout(r, 650)); }
                                hs.push(Math.round(st.getBoundingClientRect().height));
                                gaps.push(Math.round(st.getBoundingClientRect().height - sp.getBoundingClientRect().height));
                              }
                              return {hs, gaps}; }""")
                            if max(fit["gaps"]) > 60:
                                failures.append(f"{where}: phone stage leaves {max(fit['gaps'])}px of blank around the specimen")
                            if len(set(fit["hs"])) > 1:
                                failures.append(f"{where}: phone stage height jumps between formats {fit['hs']}")
                        # Text layout: headings share one left edge and style, prompt text fills its box,
                        # and the English/Chinese divider only appears when both languages are shown.
                        tx = page.evaluate("""() => {
                          const vis = h => [...h.children].find(c => getComputedStyle(c).display !== 'none') || h;
                          const hs = [...document.querySelectorAll('main h2.section-title')];
                          const lefts = hs.map(h => Math.round(vis(h).getBoundingClientRect().left));
                          const sizes = hs.map(h => getComputedStyle(h).fontSize);
                          const gaps = [...document.querySelectorAll('.copy-block')].map(b => {
                            const p = [...b.querySelectorAll('.copy-text p')].find(x => getComputedStyle(x).display !== 'none');
                            return Math.round(b.getBoundingClientRect().right - p.getBoundingClientRect().right); });
                          const rules = [...document.querySelectorAll('.copy-text .zh-copy')].map(p => getComputedStyle(p).borderTopStyle);
                          return {lefts, sizes, gaps, rules}; }""")
                        if len(set(tx["lefts"])) > 1:
                            failures.append(f"{where}: section headings start at different x {sorted(set(tx['lefts']))}")
                        if len(set(tx["sizes"])) > 1:
                            failures.append(f"{where}: section headings use different sizes {sorted(set(tx['sizes']))}")
                        if any(g > 110 for g in tx["gaps"]):
                            failures.append(f"{where}: prompt text stops {max(tx['gaps'])}px short of its box")
                        if any(r != "none" for r in tx["rules"]):
                            failures.append(f"{where}: dashed language divider shown in Chinese-only mode")
                        # Poster text is part of the artwork: the site's demo translator must leave it alone.
                        texts = page.evaluate("""() => {
                          const read = () => [...document.querySelectorAll('[data-gd-canvas]')].map(c => c.textContent.replace(/\\s+/g, ' ').trim()).join('|');
                          const zh = read(); document.querySelector('.ls-btn[data-mode="en"]').click();
                          const en = read(); document.querySelector('.ls-btn[data-mode="zh"]').click();
                          return [zh, en]; }""")
                        if texts[0] != texts[1]:
                            failures.append(f"{where}: poster text changes with the site language (translated artwork)")
                        for m in result["marks"]:
                            if not m["inside"]:
                                failures.append(f"{where}: {m['kind']} '{m['label']}' lies outside the canvas {result['host']}")
                page.close()
                context.close()
            browser.close()
    server.shutdown()
    if failures:
        print("\n".join(failures[:60]))
        raise SystemExit(f"{len(failures)} graphic layout checks failed (of {checked})")
    print(f"All {checked} graphic layout checks passed.")


if __name__ == "__main__":
    main()
