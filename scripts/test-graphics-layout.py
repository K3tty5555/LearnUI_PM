#!/usr/bin/env python3
"""Graphic design pages must show originals undistorted and sharp, and the breakdown layers must land on the work.

For the hub and every case page, at desktop, wide and phone widths:
- every cover and original image loads, is drawn at its own aspect ratio (no squashing, no cropping
  of mixed portrait/landscape work), and the box reserved before loading matches the file;
- every image carries enough pixels for the screen it is drawn on, and a list-page cover carries no
  more than the screen can show (a full-size original used as a thumbnail fails here);
- on a 2x screen, images that have an @2x file actually load it;
- the page never scrolls sideways;
- every specimen marks type, focus and space somewhere (a view may carry no lettering), the default
  view draws focus and space marks, and every drawn mark's centre sits inside the specimen canvas;
- the breakdown's "fog clears" motion: none at all under reduced motion; otherwise the marks start
  clear, never move, are fully opaque within 1s of "All" and gone 250ms after closing;
- on desktop the whole specimen fits inside its fixed 520px stage in every format;
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

# (width, height, device pixel ratio). A plain-density desktop is where oversized images show up;
# the dense ones prove the 2x files are picked and that phone layouts hold.
VIEWPORTS = [(1440, 1000, 1), (2000, 1100, 2), (390, 844, 2)]
PIXELS_SHORT = 0.9  # below this many of the pixels the screen needs, the image renders soft
PIXELS_WASTED = 2.2  # above this, bytes are being shipped that no screen can show
RATIO_TOLERANCE = 0.015  # 1.5 % between drawn and natural aspect ratio

# Wait until every image has really loaded. A single decode() is not enough: if the page swaps
# an image's source while it loads, that decode() rejects early and the check would run on a
# half-loaded image (flaky "not loaded" on the 28-cover hub, 2026-11-21). An image that truly
# fails to load is still pending at the deadline and gets reported.
LOAD_ALL = """async () => {
  [...document.images].forEach(i => { i.loading = 'eager'; });
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    const pending = [...document.images].filter(i => !(i.complete && i.naturalWidth > 0));
    if (!pending.length) return;
    await Promise.race([Promise.all(pending.map(i => i.decode().catch(() => {}))), new Promise(r => setTimeout(r, 400))]);
  }
}"""

IMAGES = """async () => {
  const out = [];
  for (const img of document.querySelectorAll('.gd-cover img, .gd-orig img')) {
    const r = img.getBoundingClientRect(), frame = img.closest('.gd-cover, a').getBoundingClientRect();
    const src = img.currentSrc || img.src;
    // img.naturalWidth is divided by the srcset density descriptor, so load the chosen file on its
    // own to learn how many pixels it really carries.
    let pixels = img.naturalWidth;
    try { const probe = new Image(); probe.src = src; await probe.decode(); pixels = probe.naturalWidth; } catch (e) {}
    out.push({file: src.split('/').pop(), loaded: img.complete && img.naturalWidth > 0,
              natural: img.naturalWidth / (img.naturalHeight || 1), drawn: r.width / (r.height || 1),
              pixels, needed: r.width * devicePixelRatio, cover: !!img.closest('.gd-cover'),
              frame: frame.width / (frame.height || 1), w: Math.round(r.width), h: Math.round(r.height),
              wantsHd: /@2x\\.webp/.test(img.getAttribute('srcset') || ''), hd: /@2x\\.webp$/.test(src)});
  }
  return out;
}"""

OVERFLOW = "() => document.scrollingElement.scrollWidth - window.innerWidth"

LAYERS = """async () => {
  const all = document.querySelector('[data-gd-layer="all"]');
  if (!all) return {error: 'no "all layers" button'};
  // This runs with reduced motion: the breakdown marks and the grid must appear and leave with no animation.
  const frame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const moving = () => document.getAnimations().filter(a => {
    const t = a.effect && a.effect.target;
    return t && t.closest && t.closest('.gd-ov-layer, .gd-grid') && (a.effect.getComputedTiming().duration || 0) > 0;
  }).length;
  all.click();
  await frame();
  const movingOpen = moving();
  await new Promise(r => setTimeout(r, 700));
  const host = document.querySelector('.gd-ov-layer').parentElement.getBoundingClientRect();
  const marks = [...document.querySelectorAll('.gd-ov')].map(el => {
    const r = el.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    return {kind: [...el.classList].find(c => c.startsWith('gd-ov-')), label: el.textContent,
            inside: cx >= host.left && cx <= host.right && cy >= host.top && cy <= host.bottom};
  });
  all.click();
  await frame();
  const movingClose = moving(), lingering = document.querySelectorAll('.gd-ov').length;
  // A view may legitimately carry no lettering (e.g. a key visual without text); the mark then lives in another view.
  const defined = ['type', 'focus', 'space'].filter(k => document.querySelector('.gd-specimen [data-ov-' + k + ']'));
  return {marks, defined, movingOpen, movingClose, lingering,
          host: [Math.round(host.width), Math.round(host.height)]};
}"""

# Normal motion: "All" lifts the marks with the fog-clears motion (docs/polish-plan.md). On the first
# frame the marks are still clear (the motion exists), they never move, every one is fully opaque
# within 1 second, and after closing nothing is left behind 250ms later.
FOG = """async () => {
  const all = document.querySelector('[data-gd-layer="all"]');
  const marks = () => [...document.querySelectorAll('.gd-ov-layer:not(.gd-ov-leaving) > *')];
  const t0 = performance.now();
  all.click();
  await new Promise(r => requestAnimationFrame(r));
  const early = marks().map(m => +getComputedStyle(m).opacity);
  const moved = marks().filter(m => getComputedStyle(m).transform !== 'none').length;
  let full = null;
  while (performance.now() - t0 < 1000) {
    const now = marks();
    if (now.length && now.every(m => +getComputedStyle(m).opacity >= 0.999)) { full = Math.round(performance.now() - t0); break; }
    await new Promise(r => setTimeout(r, 20));
  }
  const count = marks().length;
  all.click();
  await new Promise(r => setTimeout(r, 250));
  return {count, early: early.length ? Math.max(...early) : null, moved, full,
          left: document.querySelectorAll('.gd-ov-leaving > *').length, open: marks().length};
}"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site")
    parser.add_argument("--base", default="")
    parser.add_argument("--engines", default="chromium")
    args = parser.parse_args()
    cases = json.loads((ROOT / "data/graphics.json").read_text(encoding="utf-8"))["cases"]
    paths = ["/graphics/"] + [f"/graphics/{c['slug']}/" for c in cases]
    # The most pixels each file could possibly carry: a cover cannot beat its source, an original
    # cannot beat its 2x copy. Nothing is faulted for being smaller than that.
    ceiling = {}
    for case in cases:
        for im in case["images"]:
            ceiling[im["file"]] = im["w"]
            if im.get("hd"):
                ceiling[im["hd"]] = im["w"] * 2
        ceiling[f'{case["slug"]}-cover.webp'] = case["images"][0]["w"]
        ceiling[f'{case["slug"]}-cover@2x.webp'] = case["images"][0]["w"]
    server, base = serve(args.site, args.base)
    failures, checked = [], 0
    with sync_playwright() as p:
        for engine in args.engines.split(","):
            browser = getattr(p, engine).launch()
            for width, height, dpr in VIEWPORTS:
                context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=dpr,
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
                        if dpr == 2 and im["wantsHd"] and not im["hd"]:
                            failures.append(f"{where} {im['file']}: 2x screen did not load the @2x file")
                        # Enough pixels for this screen, and not far more than it can show.
                        want = min(im["needed"], ceiling.get(im["file"], im["pixels"]))
                        ratio = im["pixels"] / max(im["needed"], 1)
                        if im["pixels"] < want * PIXELS_SHORT:
                            failures.append(f"{where} {im['file']}: only {im['pixels']}px for a {round(im['needed'])}px slot — renders soft")
                        elif im["cover"] and ratio > PIXELS_WASTED:
                            failures.append(f"{where} {im['file']}: {im['pixels']}px for a {round(im['needed'])}px slot — {ratio:.1f}x more than the screen shows")
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
                        if result["movingOpen"] or result["movingClose"]:
                            failures.append(f"{where}: breakdown animates under reduced motion ({result['movingOpen']} on open, {result['movingClose']} on close)")
                        if result["lingering"]:
                            failures.append(f"{where}: {result['lingering']} breakdown marks linger after closing under reduced motion")
                        kinds = {m["kind"] for m in result["marks"]}
                        for need in ("type", "focus", "space"):
                            if need not in result["defined"]:
                                failures.append(f"{where}: specimen marks no data-ov-{need} element")
                        if not {"gd-ov-focus", "gd-ov-space"} <= kinds:
                            failures.append(f"{where}: default view draws no focus or space mark ({sorted(kinds)})")
                        if width > 760:
                            # Desktop: the stage is a fixed 520px box that clips, so the whole specimen
                            # (step buttons included) must fit inside it in every format (dev-log 016:
                            # montage-red-black was 633px tall and lost its top and its buttons).
                            fit = page.evaluate("""async () => {
                              const st = document.querySelector('[class*="stage-detail-graphic-"]'), sp = st.querySelector('.gd-specimen');
                              const out = [];
                              const btns = [...sp.querySelectorAll('[data-format-btn]')];
                              for (const b of (btns.length ? btns : [null])) {
                                if (b) { b.click(); await new Promise(r => setTimeout(r, 650)); }
                                const s = st.getBoundingClientRect(), q = sp.getBoundingClientRect();
                                out.push(Math.round(Math.max(s.top - q.top, q.bottom - s.bottom, s.left - q.left, q.right - s.right)));
                              }
                              return out; }""")
                            if max(fit) > 2:
                                failures.append(f"{where}: specimen spills {max(fit)}px out of the 520px stage and is cut off")
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
            # The breakdown's own motion, with animation allowed (desktop, every case).
            context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="no-preference")
            page = context.new_page()
            for path in paths[1:]:
                page.goto(base + path)
                where = f"{engine} motion {path}"
                checked += 1
                fog = page.evaluate(FOG)
                if not fog["count"]:
                    failures.append(f"{where}: 'All' drew no marks")
                    continue
                if fog["full"] is None:
                    failures.append(f"{where}: breakdown marks not fully opaque within 1s of 'All'")
                if fog["early"] is not None and fog["early"] >= 0.9:
                    failures.append(f"{where}: breakdown marks appear at once (opacity {fog['early']:.2f} on the first frame), no fog-clears motion")
                if fog["moved"]:
                    failures.append(f"{where}: {fog['moved']} breakdown marks are transformed while appearing (fog clears in place)")
                if fog["left"] or fog["open"]:
                    failures.append(f"{where}: {fog['left'] + fog['open']} breakdown marks still on screen 250ms after closing")
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
