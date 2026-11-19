#!/usr/bin/env python3
"""The mobile header's language control follows the site's segmented-control design.

User report (2026-11-19): on phone widths the header used a native <select>, whose system popup
menu ignores DESIGN.md (language switching is a small segmented control, 5-7px radius, like the
desktop sidebar). At phone widths the header must show one segmented 中文 | EN control with no
native select; tapping EN switches the page language and moves the active state; the control must
not overlap the wordmark, search or collection buttons. On desktop only the sidebar control shows.

Usage: python3 scripts/test-mobile-language.py site [--base /LearnUI_PM] [--engines chromium,webkit]
"""
import argparse
import importlib.util
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("logo_layout", ROOT / "scripts/test-logo-layout.py")
logo_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logo_layout)

PAGES = ["/", "/graphics/", "/web/tilt-card/"]
PHONES = [(375, 812), (390, 844), (760, 900)]

SCAN = """() => {
  const visible = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const header = document.querySelector('.site-header');
  const box = el => { const r = el.getBoundingClientRect(); return {l: r.left, r: r.right, t: r.top, b: r.bottom, h: r.height}; };
  const switches = [...header.querySelectorAll('.lang-switch')].filter(visible);
  return {
    selects: [...header.querySelectorAll('select')].filter(visible).length,
    switches: switches.map(s => ({box: box(s), radius: parseFloat(getComputedStyle(s).borderTopLeftRadius),
      buttons: [...s.querySelectorAll('.ls-btn')].filter(visible).map(b => ({mode: b.dataset.mode, active: b.classList.contains('active'), box: box(b)}))})),
    others: ['.wordmark', '.global-search-open', '.sidebar-selection'].map(sel => header.querySelector(sel)).filter(el => el && visible(el)).map(el => ({sel: el.className, box: box(el)})),
    mode: document.documentElement.dataset.langMode,
  };
}"""


def overlap(a, b):
    return a["l"] < b["r"] - 0.5 and b["l"] < a["r"] - 0.5 and a["t"] < b["b"] - 0.5 and b["t"] < a["b"] - 0.5


def check_phone(page, url, label):
    errors = []
    page.goto(url)
    page.evaluate("() => localStorage.clear()")
    page.reload()
    page.wait_for_timeout(200)
    s = page.evaluate(SCAN)
    if s["selects"]:
        errors.append(f"{label}: header shows a native <select> ({s['selects']})")
    if len(s["switches"]) != 1:
        return errors + [f"{label}: expected 1 visible segmented language control in header, found {len(s['switches'])}"]
    sw = s["switches"][0]
    if [b["mode"] for b in sw["buttons"]] != ["zh", "en"]:
        errors.append(f"{label}: segmented buttons are {[b['mode'] for b in sw['buttons']]}, expected zh, en")
    if not 5 <= sw["radius"] <= 7:
        errors.append(f"{label}: segmented control radius {sw['radius']}px, DESIGN.md asks 5-7px")
    if [b["active"] for b in sw["buttons"]] != [True, False]:
        errors.append(f"{label}: default active state should be 中文")
    for b in sw["buttons"]:
        if b["box"]["h"] < 28:
            errors.append(f"{label}: {b['mode']} button only {b['box']['h']:.0f}px tall")
    for o in s["others"]:
        if overlap(sw["box"], o["box"]):
            errors.append(f"{label}: language control overlaps {o['sel']}")
    if sw["box"]["r"] > page.viewport_size["width"]:
        errors.append(f"{label}: language control runs off screen")
    page.locator('.site-header .lang-switch:visible .ls-btn[data-mode="en"]').click()
    after = page.evaluate(SCAN)
    if after["mode"] != "en":
        errors.append(f"{label}: tapping EN left page mode {after['mode']}")
    elif [b["active"] for b in after["switches"][0]["buttons"]] != [False, True]:
        errors.append(f"{label}: after tapping EN the active state did not move")
    return errors


def check_desktop(page, url, label):
    page.goto(url)
    page.wait_for_timeout(150)
    s = page.evaluate(SCAN)
    errors = []
    if s["selects"]:
        errors.append(f"{label}: desktop header shows a <select>")
    if len(s["switches"]) != 1:
        errors.append(f"{label}: desktop should show exactly the sidebar language control, found {len(s['switches'])}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site")
    parser.add_argument("--base", default="")
    parser.add_argument("--engines", default="chromium")
    args = parser.parse_args()
    server, origin = logo_layout.serve(args.site, args.base)
    errors = []
    try:
        with sync_playwright() as p:
            for engine in args.engines.split(","):
                browser = getattr(p, engine).launch()
                for w, h in PHONES:
                    page = browser.new_page(viewport={"width": w, "height": h})
                    for path in PAGES:
                        errors += check_phone(page, origin + path, f"{engine} {w}px {path}")
                    page.close()
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                for path in PAGES:
                    errors += check_desktop(page, origin + path, f"{engine} 1440px {path}")
                browser.close()
    finally:
        server.shutdown()
    if errors:
        print("\n".join(errors))
        raise SystemExit(f"{len(errors)} mobile language problem(s)")
    print(f"Mobile language control follows the segmented design on {len(PAGES)} pages.")


if __name__ == "__main__":
    main()
