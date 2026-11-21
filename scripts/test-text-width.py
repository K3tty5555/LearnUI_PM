#!/usr/bin/env python3
"""Text follows the window width: no paragraph, list, prompt box or table is held to a fixed measure.

User decision (2026-11-18): on wide screens, text blocks fill the content column instead of stopping
at a fixed line length. For one page of every kind, at 1440 and 2000 px, every text block in <main>
(and each of its ancestors up to <main>) must not be narrowed by a max-width: if a max-width applies,
the element must still be as wide as the space its parent offers. Card grids and media are free to
size themselves; only text blocks are checked.

Section headings must also start on the content's left edge in the shown language, and sit
clearly closer to the content below them than to the block above.

Usage: python3 scripts/test-text-width.py site [--base /LearnUI_PM] [--engines chromium,webkit]
"""
import argparse
import importlib.util
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("logo_layout", ROOT / "scripts/test-logo-layout.py")
logo_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logo_layout)

PAGES = ["/", "/web/tilt-card/", "/web/card-swap/", "/macos/sidebar/", "/styles/", "/styles/aqua/",
         "/sites/", "/sites/claude/", "/logos/", "/logos/reicon/", "/graphics/", "/graphics/worlds-2022/",
         "/graphics/reionization/", "/guides/appkit-vs-swiftui/", "/guides/swift-vs-electron/", "/sources/"]
VIEWPORTS = [(1440, 1000), (2000, 1100)]

SCAN = """() => {
  const main = document.querySelector('main'); if (!main) return [];
  const blocks = main.querySelectorAll('p, ul, ol, dl, table, pre, .copy-block, .code-block, .parts, .sect, .entry-tag');
  const out = new Set();
  const name = el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + [...el.classList].slice(0, 2).map(c => '.' + c).join('');
  for (const el of blocks) {
    if (!el.offsetParent || !el.textContent.trim()) continue;
    // Text inside cards, chips, tables cells or flex/grid rows is laid out by its card, not capped.
    if (el.closest('a, button, td, th, figure, .rel-card, .card, .graphic-card, .logo-card, [role="dialog"], dialog, .demo, .fragment, .pm-chat')) continue;
    for (let n = el; n && n !== main; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.maxWidth === 'none' || cs.maxWidth === '100%') continue;
      const p = n.parentElement, ps = getComputedStyle(p);
      if (ps.display.includes('flex') && ps.flexDirection.startsWith('row')) break;
      if (ps.display.includes('grid') && ps.gridTemplateColumns.split(' ').length > 1) break;
      const room = p.clientWidth - parseFloat(ps.paddingLeft) - parseFloat(ps.paddingRight);
      const w = n.getBoundingClientRect().width + parseFloat(cs.marginLeft) + parseFloat(cs.marginRight);
      if (w < room - 4) { out.add(name(n) + ' max-width:' + cs.maxWidth + ' (' + Math.round(w) + ' of ' + Math.round(room) + 'px)'); break; }
    }
  }
  return [...out];
}"""


# Section headings start on the same left edge as the text under them (user decision 2026-11-18).
# In Chinese mode the English half is hidden, so a margin meant to separate the two halves must
# not push the Chinese title inward (it did by 10px until 2026-11-21).
ALIGN = """() => [...document.querySelectorAll('main h2.section-title')].map(h => {
  const shown = [...h.children].find(c => getComputedStyle(c).display !== 'none' && c.textContent.trim());
  if (!shown) return null;
  const left = h.getBoundingClientRect().left + parseFloat(getComputedStyle(h).paddingLeft);
  const off = Math.round(shown.getBoundingClientRect().left - left);
  return off > 1 ? (h.textContent.trim().slice(0, 12) + ' indented ' + off + 'px') : null;
}).filter(Boolean)"""

# A section heading belongs to the content under it: clearly more space above it than below it.
# (Until 2026-11-21 a broken selector list zeroed every section's top margin, so headings sat
# glued to the block above and read as its last line.)
RHYTHM = """() => {
  const out = [];
  for (const h of document.querySelectorAll('main h2.section-title')) {
    if (!h.offsetParent) continue;
    let prev = null;
    for (let n = h; n && n.tagName !== 'MAIN' && !prev; n = n.parentElement) {
      for (let s = n.previousElementSibling; s; s = s.previousElementSibling) {
        if (s.getBoundingClientRect().height > 0 && getComputedStyle(s).position !== 'absolute') { prev = s; break; }
      }
    }
    const next = h.nextElementSibling;
    if (!prev || !next) continue;
    const r = h.getBoundingClientRect();
    const above = Math.round(r.top - prev.getBoundingClientRect().bottom);
    const below = Math.round(next.getBoundingClientRect().top - r.bottom);
    if (above < 28 || above < below * 1.5) out.push(h.innerText.trim().slice(0, 12) + ': ' + above + 'px above, ' + below + 'px below');
  }
  return out;
}"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site")
    parser.add_argument("--base", default="")
    parser.add_argument("--engines", default="chromium")
    args = parser.parse_args()
    server, base = logo_layout.serve(args.site, args.base)
    server.handle_error = lambda *a: None  # pages navigate away mid-download; broken pipes are expected
    failures, checked = [], 0
    with sync_playwright() as p:
        for engine in args.engines.split(","):
            browser = getattr(p, engine).launch()
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                for path in PAGES:
                    page.goto(base + path)
                    checked += 1
                    for hit in page.evaluate(SCAN):
                        failures.append(f"{engine} {width}px {path}: {hit}")
                    for hit in page.evaluate(ALIGN):
                        failures.append(f"{engine} {width}px {path}: heading {hit}")
                    for hit in page.evaluate(RHYTHM):
                        failures.append(f"{engine} {width}px {path}: heading spacing {hit}")
                page.close()
            browser.close()
    server.shutdown()
    if failures:
        print("\n".join(failures[:80]))
        raise SystemExit(f"{len(failures)} capped text blocks on {checked} page views")
    print(f"Text fills the content width on all {checked} page views.")


if __name__ == "__main__":
    main()
