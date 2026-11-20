#!/usr/bin/env python3
"""Browser regression: no catalog specimen gets cut off, in any state.

A specimen cycles through states on its own (steps, open menus, expanded
cards, tabs). A screenshot of the first frame says nothing about the tallest
state, which is where clipping hides (dev-log 003: the typography card's last
step was cut by its own stage). This check plays every catalog card through a
full cycle at desktop and phone widths and samples what is on screen.

An element counts as cut when part of it is visible and part of it lies beyond
the card, or beyond an ancestor inside the specimen that clips (overflow
hidden/clip). Rules (dev-log 014):
- Content is a visible element that paints: text, image, canvas, svg, form
  control, background or border. An ancestor at opacity 0 hides it.
- Entirely clipped away counts as hidden, not cut (off-canvas drawers).
- A scroll area (overflow auto/scroll) clips on purpose: content scrolled out
  of it is not cut, and clips outside it no longer apply.
- A cut must last OVERFLOW_HOLD_MS: things sliding in or out cross edges.
- Elements that are cut on purpose (a marquee track, a parallax layer, a card
  being thrown off the stage) carry data-clip-ok; they and their descendants
  are skipped. Put it on the narrowest element that moves, never on a stage.

All cards run at once: the viewport is made as tall as the catalog (in windows
for the phone layout), so the catalog's own lazy loader starts them all.

Usage: python3 scripts/test-catalog-states.py site [--base /UIUX]
       [--engines chromium,webkit] [--seconds 55] [--shots DIR]
"""
import argparse
import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

TOLERANCE_PX = 2
OVERFLOW_HOLD_MS = 700
SAMPLE_MS = 100
VIEWPORTS = {"desktop": 1440, "mobile": 390}

# Installed into every specimen frame; records the worst sustained overflow.
SAMPLER = """([tolerance, holdMs, sampleMs]) => {
  if (window.__stateProbe) return;
  const probe = window.__stateProbe = {worst: 0, element: '', since: null, runWorst: 0, runElement: ''};
  const paints = (el, cs) => {
    if (['IMG', 'CANVAS', 'VIDEO', 'INPUT', 'BUTTON', 'TEXTAREA', 'SELECT'].includes(el.tagName)) return true;
    if (el instanceof SVGSVGElement) return true;
    if (cs.backgroundImage !== 'none') return true;
    if (cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent') return true;
    if (parseFloat(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none') return true;
    for (const node of el.childNodes) if (node.nodeType === 3 && node.nodeValue.trim()) return true;
    return false;
  };
  // A fully transparent ancestor (a closed menu fading out) hides the element.
  const transparent = (el) => {
    for (let a = el; a && a !== document.body; a = a.parentElement) {
      if (parseFloat(getComputedStyle(a).opacity) === 0) return true;
    }
    return false;
  };
  const label = (el) => {
    const cls = typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '';
    return (el.tagName.toLowerCase() + (cls ? '.' + cls.trim().split(/\\s+/).join('.') : '')).slice(0, 60);
  };
  // Two boxes per element: `seen` is what any clipping ancestor lets
  // through; `room` is what hidden/clip ancestors and the card allow. A scroll
  // area clips on purpose (content beyond it is scrolled away, not cut), so
  // ancestors outside a scroll area no longer limit `room` on that axis.
  const boxes = (el) => {
    const r = el.getBoundingClientRect();
    const seen = [Math.max(r.left, 0), Math.max(r.top, 0), Math.min(r.right, innerWidth), Math.min(r.bottom, innerHeight)];
    const room = [-Infinity, -Infinity, Infinity, Infinity];
    const by = ['card', 'card', 'card', 'card'];  // which box set each edge of `room`
    let openX = true, openY = true;
    const scrolls = (v) => v === 'auto' || v === 'scroll';
    for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
      const q = a.getBoundingClientRect();
      if (cs.overflowX !== 'visible') {
        seen[0] = Math.max(seen[0], q.left); seen[2] = Math.min(seen[2], q.right);
        if (scrolls(cs.overflowX)) openX = false;
        if (openX) {
          if (q.left > room[0]) { room[0] = q.left; by[0] = label(a); }
          if (q.right < room[2]) { room[2] = q.right; by[2] = label(a); }
        }
      }
      if (cs.overflowY !== 'visible') {
        seen[1] = Math.max(seen[1], q.top); seen[3] = Math.min(seen[3], q.bottom);
        if (scrolls(cs.overflowY)) openY = false;
        if (openY) {
          if (q.top > room[1]) { room[1] = q.top; by[1] = label(a); }
          if (q.bottom < room[3]) { room[3] = q.bottom; by[3] = label(a); }
        }
      }
    }
    // The card itself is the outermost clip, unless a scroll area intervened.
    if (openX) {
      if (room[0] < 0) { room[0] = 0; by[0] = 'card'; }
      if (room[2] > innerWidth) { room[2] = innerWidth; by[2] = 'card'; }
    }
    if (openY) {
      if (room[1] < 0) { room[1] = 0; by[1] = 'card'; }
      if (room[3] > innerHeight) { room[3] = innerHeight; by[3] = 'card'; }
    }
    return [r, seen, room, by];
  };
  const sample = () => {
    const W = innerWidth, H = innerHeight;
    const root = document.querySelector('.fragment');
    if (!root) return;
    let over = 0, who = '';
    for (const el of root.querySelectorAll('*')) {
      if (el.closest('[data-clip-ok]')) continue;
      if (el instanceof SVGElement && !(el instanceof SVGSVGElement)) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility !== 'visible') continue;
      if (!paints(el, cs) || transparent(el)) continue;
      const [r, seen, room, by] = boxes(el);
      if (seen[2] - seen[0] < 1 || seen[3] - seen[1] < 1) continue;  // entirely clipped away: hidden
      const sides = [room[0] - r.left, room[1] - r.top, r.right - room[2], r.bottom - room[3]];
      const amount = Math.max(...sides);
      if (amount > over) { over = amount; who = label(el) + ' cut by ' + by[sides.indexOf(amount)]; probe.culprit = el; }
    }
    const now = performance.now();
    probe.current = over > tolerance && probe.since !== null && now - probe.since >= holdMs;
    if (over > tolerance) {
      if (probe.since === null) { probe.since = now; probe.runWorst = 0; }
      if (over > probe.runWorst) { probe.runWorst = over; probe.runElement = who; }
      if (now - probe.since >= holdMs && probe.runWorst > probe.worst) {
        probe.worst = probe.runWorst; probe.element = probe.runElement;
      }
    } else {
      probe.since = null;
    }
  };
  setInterval(sample, sampleMs);
}"""


def serve(site, base):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(site.resolve()), **kwargs)

        def translate_path(self, path):
            if base and path.startswith(base + "/"):
                path = path[len(base):]
            return super().translate_path(path)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


MAX_VIEWPORT = 30000


def check(browser, url, width, seconds, shots, tag):
    page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="no-preference")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url)
    page.wait_for_selector("[data-live-demo]")
    height = page.evaluate("Math.ceil(document.documentElement.scrollHeight)")
    window = min(height + 200, MAX_VIEWPORT)
    page.set_viewport_size({"width": width, "height": window})
    every = page.locator("[data-live-demo]").evaluate_all("els => els.map(el => el.dataset.liveDemo)")
    seen, failures, offset = set(), {}, 0
    # A phone-width catalog is taller than any browser viewport: play it in windows.
    while offset < height:
        page.evaluate("y => scrollTo({top: y, behavior: 'instant'})", offset)
        page.wait_for_timeout(300)
        slugs = page.locator("[data-live-demo]").evaluate_all(
            "els => els.filter(el => { const r = el.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; })"
            ".map(el => el.dataset.liveDemo)")
        slugs = [slug for slug in slugs if slug not in seen]
        if slugs:
            run_window(page, slugs, seconds, shots, tag, failures)
        seen.update(slugs)
        offset += window - 400  # overlap so no card straddles every window
    page.close()
    missed = sorted(set(every) - seen)
    if missed:
        raise SystemExit(f"Cards never fully on screen: {missed}")
    return len(seen), failures, errors


def run_window(page, slugs, seconds, shots, tag, failures):
    selector = ",".join(f'[data-live-demo="{slug}"]' for slug in slugs)
    running = "sel => [...document.querySelectorAll(sel)].every(el => el.dataset.liveState === 'running')"
    for attempt in range(5):
        try:
            page.wait_for_function(running, arg=selector, timeout=15000)
            break
        except Exception:
            # A hundred lazy fetches at once can drop a few on the local test
            # server; the catalog retries failed specimens on "online".
            page.evaluate("dispatchEvent(new Event('online'))")
    else:
        stuck = page.locator(selector).evaluate_all(
            "els => els.filter(el => el.dataset.liveState !== 'running').map(el => el.dataset.liveDemo + ':' + el.dataset.liveState)")
        raise SystemExit(f"Specimens never started: {stuck}")
    for slug in slugs:
        frame = page.locator(f'[data-live-demo="{slug}"] iframe').element_handle().content_frame()
        frame.evaluate(SAMPLER, [TOLERANCE_PX, OVERFLOW_HOLD_MS, SAMPLE_MS])
    page.wait_for_timeout(seconds * 1000)
    for slug in slugs:
        slot = page.locator(f'[data-live-demo="{slug}"]')
        frame = slot.locator("iframe").element_handle().content_frame()
        probe = frame.evaluate("({...window.__stateProbe, W: innerWidth, H: innerHeight})")
        if probe["worst"] > TOLERANCE_PX:
            failures[slug] = {
                "overflow_px": round(probe["worst"], 1),
                "element": probe["element"],
                "card": f'{probe["W"]}x{probe["H"]}',
            }
            if shots:
                slot.screenshot(path=str(Path(shots) / f"{tag}-{slug}.png"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site", type=Path, nargs="?", default=Path("site"))
    parser.add_argument("--base", default="/UIUX")
    parser.add_argument("--engines", default="chromium")
    parser.add_argument("--seconds", type=int, default=55, help="how long each card plays; must cover the longest cycle (interaction-details, ~47 s)")
    parser.add_argument("--shots", help="directory for screenshots of failing cards")
    args = parser.parse_args()
    base = args.base.rstrip("/")
    if args.shots:
        Path(args.shots).mkdir(parents=True, exist_ok=True)
    server = serve(args.site, base)
    url = f"http://127.0.0.1:{server.server_port}{base}/"
    report, failed = {}, False
    try:
        with sync_playwright() as p:
            for engine in args.engines.split(","):
                launch = {"executable_path": os.environ.get("PLAYWRIGHT_CHROME_PATH")} if engine == "chromium" else {}
                browser = getattr(p, engine).launch(**launch)
                for name, width in VIEWPORTS.items():
                    count, failures, errors = check(browser, url, width, args.seconds, args.shots, f"{engine}-{name}")
                    report[f"{engine}/{name}"] = {"cards": count, "clipped": failures, "errors": errors}
                    failed = failed or bool(failures) or bool(errors)
                browser.close()
    finally:
        server.shutdown()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit("Catalog specimens clipped by their card (see 'clipped' above).")


if __name__ == "__main__":
    main()
