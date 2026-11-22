#!/usr/bin/env python3
"""Browser regression: the shell's motion happens, and stops for people who ask it to.

Normal motion (Chromium; the view-transition checks need its cross-document support):
- following a link cross-fades old and new page on exactly the same timing (otherwise the
  additive cross-fade washes out to a white flash), with the sidebar kept as its own still layer;
- a graphic cover flies into its case page (gd-hero) and back to its card; a logo flies into
  its detail page (logo-hero);
- the platform tabs' pill slides; the command search dialog animates in;
- hover prefetch is set to "moderate".
Reduced motion (Chromium and WebKit):
- no view transition on navigation, and no running animation after opening the command search,
  switching a tab or adding to the collection.

Usage: python3 scripts/test-motion.py site [--base /UIUX] [--engines chromium,webkit]
"""
import argparse
import importlib.util
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("logo_layout", ROOT / "scripts/test-logo-layout.py")
logo_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logo_layout)

# Record, on every page, whether it arrived with a view transition and which layers it animated.
REVEAL = """window.__vt = 'pending';
addEventListener('pagereveal', e => {
  if (!e.viewTransition) { window.__vt = 'none'; return; }
  e.viewTransition.ready.then(() => {
    const anims = document.getAnimations();
    window.__vt = [...new Set(anims.map(a => a.effect && a.effect.pseudoElement).filter(Boolean))];
    // Timing of every animation on the old / new root image (fade + blend-mode helpers).
    window.__pair = ['old', 'new'].map(k => anims.filter(a => a.effect && a.effect.pseudoElement === '::view-transition-' + k + '(root)')
      .map(a => { const t = a.effect.getComputedTiming(); return t.duration + ' ' + t.easing; }).sort().join(' | '));
  }, () => { window.__vt = 'skipped'; });
});"""
RUNNING = """() => document.getAnimations().filter(a => a.playState === 'running'
  && (a.effect.getComputedTiming().duration || 0) > 5).map(a => (a.effect.target && a.effect.target.className || '') + ' ' + (a.animationName || a.transitionProperty || ''))"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site")
    parser.add_argument("--base", default="")
    parser.add_argument("--engines", default="chromium")
    args = parser.parse_args()
    server, base = logo_layout.serve(args.site, args.base)
    server.handle_error = lambda *a: None
    failures = []
    with sync_playwright() as p:
        for engine in args.engines.split(","):
            browser = getattr(p, engine).launch()
            where = lambda what: f"{engine} {what}"

            if engine == "chromium":
                ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="no-preference")
                ctx.add_init_script(REVEAL)
                page = ctx.new_page()
                page.goto(base + "/graphics/")
                page.wait_for_timeout(1200)
                page.locator("a.graphic-card").nth(1).click()
                page.wait_for_timeout(900)
                layers = page.evaluate("window.__vt")
                if not isinstance(layers, list) or not any("root" in l for l in layers):
                    failures.append(where(f"no page cross-fade on navigation ({layers})"))
                else:
                    # The cross-fade adds the two images, so it only stays at normal brightness when the
                    # old page fades out exactly as the new fades in: same duration, same curve.
                    # Mismatched timing (140 ms vs 200 ms, two curves) washed pages out to white (2026-11-22).
                    old, new = page.evaluate("window.__pair")
                    if not old or old != new:
                        failures.append(where(f"old and new page fade on different timing, the cross-fade flashes: old [{old}] new [{new}]"))
                    if not any("site-header" in l for l in layers):
                        failures.append(where("the sidebar is not kept as its own layer during navigation"))
                    if not any("gd-hero" in l for l in layers):
                        failures.append(where("graphic cover did not fly into the case page"))
                page.go_back()
                page.wait_for_timeout(900)
                layers = page.evaluate("window.__vt")
                if not isinstance(layers, list) or not any("gd-hero" in l for l in layers):
                    failures.append(where(f"cover did not fly back to its card ({layers})"))

                page.goto(base + "/logos/")
                page.wait_for_timeout(1000)
                page.locator("a.logo-card").nth(1).click()
                page.wait_for_timeout(900)
                layers = page.evaluate("window.__vt")
                if not isinstance(layers, list) or not any("logo-hero" in l for l in layers):
                    failures.append(where(f"logo did not fly into its detail page ({layers})"))

                page.goto(base + "/")
                page.wait_for_timeout(800)
                page.locator('.tab[data-filter="web"]').click()
                page.wait_for_timeout(40)
                if not page.evaluate("document.getAnimations().some(a => a.effect && a.effect.pseudoElement === '::before' && a.effect.target.classList.contains('tabs'))"):
                    failures.append(where("platform tab pill did not slide"))
                page.keyboard.press("Control+k")
                page.wait_for_timeout(40)
                if not page.evaluate("document.querySelector('#global-search-dialog').getAnimations().length"):
                    failures.append(where("command search dialog did not animate in"))
                page.keyboard.press("Escape")
                rules = page.evaluate("[...document.querySelectorAll('script[type=speculationrules]')].map(s => s.textContent).join('')")
                if '"moderate"' not in rules:
                    failures.append(where(f"hover prefetch missing or not moderate: {rules[:80]!r}"))
                ctx.close()

            # Reduced motion: nothing moves.
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
            ctx.add_init_script(REVEAL)
            page = ctx.new_page()
            page.goto(base + "/graphics/")
            page.wait_for_timeout(800)
            page.locator("a.graphic-card").nth(1).click()
            page.wait_for_timeout(600)
            if isinstance(page.evaluate("window.__vt"), list):
                failures.append(where("reduced motion: navigation still runs a view transition"))
            page.goto(base + "/")
            page.wait_for_timeout(800)
            page.locator('.tab[data-filter="macos"]').click()
            page.keyboard.press("Control+k" if engine == "chromium" else "Meta+k")
            page.wait_for_timeout(30)
            moving = page.evaluate(RUNNING)
            if moving:
                failures.append(where(f"reduced motion: still animating {moving[:3]}"))
            ctx.close()
            browser.close()
    server.shutdown()
    if failures:
        print("\n".join(failures))
        raise SystemExit(f"{len(failures)} motion checks failed")
    print("Motion runs where it should and stays still under reduced motion.")


if __name__ == "__main__":
    main()
