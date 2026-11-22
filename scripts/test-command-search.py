#!/usr/bin/env python3
"""Browser regression: the ⌘K library search helps you find a name.

- Results show a small thumbnail per entry, and every thumbnail really loads (no broken images).
- The typed words are highlighted with <mark> in the results.
- The first result is selected as soon as results appear (visibly, and announced to screen
  readers); ↓ moves the selection, Enter opens the selected page.
- Hovering one result and having another selected never shows two highlights.
- No results: a plain-words hint and clickable example words that do find something,
  in the page language.

Usage: python3 scripts/test-command-search.py site [--base /UIUX] [--engines chromium,webkit]
"""
import argparse
import importlib.util
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("logo_layout", ROOT / "scripts/test-logo-layout.py")
logo_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logo_layout)

RESULTS = "#global-search-results .global-search-result"
SELECTED = "#global-search-results .global-search-result[aria-selected=true]"
EMPTY = "#global-search-results .global-search-empty"
# The selected result as a screen reader sees it: focused itself, or named by aria-activedescendant.
ANNOUNCED = """() => {
  const input = document.getElementById('global-search-input');
  const id = input.getAttribute('aria-activedescendant');
  return id ? document.getElementById(id) : (document.activeElement.closest('.global-search-result') || null);
}"""
# How many results paint a highlight background right now.
HIGHLIGHTED = """els => els.filter(e => {
  const bg = getComputedStyle(e).backgroundColor;
  return bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
}).length"""
CJK = lambda text: any("一" <= ch <= "鿿" for ch in text)


def open_search(page, query):
    page.keyboard.press("ControlOrMeta+k")
    page.wait_for_selector("#global-search-dialog[open]")
    page.locator("#global-search-input").fill(query)
    page.wait_for_timeout(400)


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
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            where = lambda what: f"{engine} {what}"

            page.goto(base + "/")
            open_search(page, "按钮")
            results = page.locator(RESULTS)
            if not results.count():
                failures.append(where("「按钮」: no results"))
                browser.close()
                continue

            # Selected from the start: exactly one, the first, announced, and visibly highlighted.
            selected = page.locator(SELECTED)
            if selected.count() != 1 or results.first.get_attribute("aria-selected") != "true":
                failures.append(where(f"first result not selected on typing ({selected.count()} selected)"))
            announced = page.evaluate_handle(ANNOUNCED)
            if not announced.evaluate("(el, first) => el === first", results.first.element_handle()):
                failures.append(where("selected result is not announced (no focus, no aria-activedescendant)"))
            page.wait_for_timeout(300)
            if results.evaluate_all(HIGHLIGHTED) != 1:
                failures.append(where(f"{results.evaluate_all(HIGHLIGHTED)} results highlighted, expected the selected one"))

            # Thumbnails: one per result, each loads.
            thumbs = page.locator(RESULTS + " img")
            if thumbs.count() != results.count():
                failures.append(where(f"{thumbs.count()} thumbnails for {results.count()} results"))
            broken = []
            for i in range(thumbs.count()):
                img = thumbs.nth(i)
                img.scroll_into_view_if_needed()
                try:
                    page.wait_for_function("img => img.complete", arg=img.element_handle(), timeout=5000)
                except Exception:
                    pass
                if not img.evaluate("img => img.complete && img.naturalWidth > 0"):
                    broken.append(img.get_attribute("src"))
            if broken:
                failures.append(where(f"thumbnails did not load: {broken[:3]}"))
            page.locator("#global-search-results").evaluate("el => { el.scrollTop = 0; }")

            # Highlighted query words.
            marks = page.locator("#global-search-results mark").all_inner_texts()
            if not marks or any(m.lower() != "按钮" for m in marks):
                failures.append(where(f"query not highlighted with <mark>: {marks[:3]}"))

            # Hover another result: still a single highlight.
            if results.count() > 2:
                results.nth(2).hover()
                page.wait_for_timeout(300)
                if results.evaluate_all(HIGHLIGHTED) != 1:
                    failures.append(where(f"hover + selection show {results.evaluate_all(HIGHLIGHTED)} highlights"))
                page.mouse.move(5, 5)
                page.locator("#global-search-input").fill("按钮")
                page.wait_for_timeout(400)

            # ↓ moves the selection; Enter opens it.
            page.keyboard.press("ArrowDown")
            if results.count() > 1:
                second = results.nth(1)
                if second.get_attribute("aria-selected") != "true" or page.locator(SELECTED).count() != 1:
                    failures.append(where("ArrowDown did not move the selection to the second result"))
                if not page.evaluate_handle(ANNOUNCED).evaluate("(el, s) => el === s", second.element_handle()):
                    failures.append(where("new selection after ArrowDown is not announced"))
                href = second.evaluate("a => a.href")
                page.keyboard.press("Enter")
                try:
                    page.wait_for_url(href, timeout=5000)
                except Exception:
                    failures.append(where(f"Enter opened {page.url}, expected {href}"))

            # Nothing found: hint plus example words that find something.
            page.goto(base + "/")
            open_search(page, "qzxvj乱码乱码")
            empty = page.locator(EMPTY)
            if not empty.count() or not empty.is_visible():
                failures.append(where("no hint shown when nothing matches"))
            else:
                examples = empty.locator("button")
                if not 2 <= examples.count() <= 3:
                    failures.append(where(f"{examples.count()} example words, expected 2-3"))
                else:
                    examples.first.click()
                    page.wait_for_timeout(400)
                    if not page.locator(RESULTS).count():
                        failures.append(where("example word finds nothing"))
            page.keyboard.press("Escape")

            # English mode: the hint is English.
            page.locator('.ls-btn[data-mode="en"]:visible').click()
            open_search(page, "qzxvj乱码乱码")
            hint = page.locator(EMPTY).inner_text() if page.locator(EMPTY).count() else ""
            status = page.locator("#global-search-status").inner_text()
            if not hint or CJK(hint) or CJK(status):
                failures.append(where(f"English mode hint not English: {hint!r} / {status!r}"))
            page.keyboard.press("Escape")
            page.locator('.ls-btn[data-mode="zh"]:visible').click()
            browser.close()
    server.shutdown()
    if failures:
        print("\n".join(failures))
        raise SystemExit(f"{len(failures)} command search checks failed")
    print("⌘K search: thumbnails load, matches highlighted, first result selected, helpful when empty.")


if __name__ == "__main__":
    main()
