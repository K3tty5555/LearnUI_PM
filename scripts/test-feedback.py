#!/usr/bin/env python3
"""Browser regression: copy and "add to reference" buttons give feedback and always recover.

- A copy button shows its "copied" state and returns to its own label afterwards, even when
  clicked twice in a row (the second click used to remember "Copied" as the label).
- A copy that fails says so in the page language and recovers; it must not wipe the bilingual
  label (it used to replace the whole button with a Chinese-only sentence).
- Copy buttons without separate language spans (graphic and logo pages) also recover.
- "Add to reference" speaks the page language, visibly and to screen readers, and announces the
  new total.
- "New" badges disappear on their own once their end date has passed.
- The platform tabs (All / Web / macOS) filter on the very first click.
- Search explains a match in plain words ("you said X — this is the one"), in the page language.

Usage: python3 scripts/test-feedback.py site [--base /UIUX] [--engines chromium,webkit]
"""
import argparse
import importlib.util
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("logo_layout", ROOT / "scripts/test-logo-layout.py")
logo_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logo_layout)

# Replace the clipboard so the test controls success or failure in every engine.
CLIPBOARD = """ok => {
  const fake = { writeText: () => ok ? Promise.resolve() : Promise.reject(new Error('denied')) };
  Object.defineProperty(navigator, 'clipboard', { configurable: true, get: () => fake });
  document.execCommand = () => ok;
}"""
LABEL = "el => el.innerText.replace(/\\s+/g, ' ').trim()"


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

            # 1. Entry page prompt copy: twice in a row, then it must come back.
            page.goto(base + "/web/tilt-card/")
            page.evaluate(CLIPBOARD, True)
            btn = page.locator("[data-copy]").first
            before = btn.evaluate(LABEL)
            btn.click(); page.wait_for_timeout(200); btn.click()
            if btn.evaluate(LABEL) == before:
                failures.append(where("copy: no 'copied' feedback"))
            page.wait_for_timeout(2200)
            if btn.evaluate(LABEL) != before:
                failures.append(where(f"copy: stuck as {btn.evaluate(LABEL)!r} after a double click (was {before!r})"))

            # 2. Failure keeps both language spans and recovers, in English mode too.
            page.locator('.ls-btn[data-mode="en"]:visible').click()
            page.evaluate(CLIPBOARD, False)
            before = btn.evaluate(LABEL)
            btn.click(); page.wait_for_timeout(200)
            shown = btn.evaluate(LABEL)
            if shown == before:
                failures.append(where("copy failure: no feedback"))
            if any("一" <= ch <= "鿿" for ch in shown):
                failures.append(where(f"copy failure: Chinese text {shown!r} in English mode"))
            if btn.locator(".lang-en").count() != 1 or btn.locator(".lang-zh").count() != 1:
                failures.append(where("copy failure: bilingual label wiped"))
            page.wait_for_timeout(2600)
            if btn.evaluate(LABEL) != before:
                failures.append(where(f"copy failure: did not recover ({btn.evaluate(LABEL)!r})"))

            # 3. "Add to reference" in English mode.
            add = page.locator("[data-select-id]").first
            add.click(); page.wait_for_timeout(200)
            text = add.evaluate("b => getComputedStyle(b.querySelector('[data-select-label]'), '::after').content")
            aria = add.get_attribute("aria-label") or ""
            for value, what in ((text, "label"), (aria, "aria-label")):
                if any("一" <= ch <= "鿿" for ch in value):
                    failures.append(where(f"add to reference: Chinese {what} {value!r} in English mode"))
            # Screen readers hear what happened and how many are collected now.
            said = page.locator("#selection-announce").inner_text() if page.locator("#selection-announce").count() else ""
            if "1" not in said or any("一" <= ch <= "鿿" for ch in said):
                failures.append(where(f"add to reference: no English announcement with the total ({said!r})"))
            add.click()  # leave the collection empty
            page.locator('.ls-btn[data-mode="zh"]:visible').click()

            # 4. Page-level Markdown copy on graphic and logo pages recovers.
            for path in ("/graphics/worlds-2022/", "/logos/reicon/"):
                page.goto(base + path)
                page.evaluate(CLIPBOARD, True)
                md = page.locator("#copy-md")
                if not md.count():
                    continue
                before = md.evaluate(LABEL)
                md.click(); page.wait_for_timeout(2200)
                if md.evaluate(LABEL) != before:
                    failures.append(where(f"{path} copy-md: stuck as {md.evaluate(LABEL)!r}"))
            # 7. Platform tabs filter on the first click, before the search box was ever used
            #    (they did nothing until the search index happened to load, 2026-11-21).
            page.goto(base + "/")
            page.locator('.tab[data-filter="macos"]').click()
            page.wait_for_timeout(1500)
            shown = page.locator(".catalog-item[data-platform]:visible").evaluate_all("els => els.map(e => e.dataset.platform)")
            if not shown or set(shown) != {"macos"}:
                failures.append(where(f"platform tab did not filter on first click: {sorted(set(shown))}"))
            if not page.locator('.tab[data-filter="macos"].active').count():
                failures.append(where("platform tab not marked active after click"))

            # 6. Search says why a card matched in plain words, in the page language.
            page.goto(base + "/")
            page.locator("#search").fill("三个点")
            page.wait_for_timeout(400)
            reasons = page.locator(".card-match:not([hidden])").all_inner_texts()
            if not reasons or any(r.startswith(("aka", "fuzzy", "symbol")) for r in reasons):
                failures.append(where(f"search match reasons not in plain words: {reasons[:3]}"))
            page.locator('.ls-btn[data-mode="en"]:visible').click(); page.wait_for_timeout(200)
            reasons = page.locator(".card-match:not([hidden])").all_inner_texts()
            # The quoted phrase is what matched (here Chinese, as typed); only the wording around it must switch.
            import re as _re
            if any(any("一" <= ch <= "鿿" for ch in _re.sub(r"“[^”]*”|「[^」]*」", "", r)) for r in reasons):
                failures.append(where(f"search match reasons not English in English mode: {reasons[:3]}"))
            page.locator('.ls-btn[data-mode="zh"]:visible').click()

            # 5. "New" badges: shown while fresh, hidden by the page itself once their date passes.
            fresh = browser.new_page()
            fresh.goto(base + "/")
            dates = fresh.locator("[data-new-until]").evaluate_all("els => els.map(e => e.getAttribute('data-new-until'))")
            fresh.close()
            if dates:
                late = browser.new_page()
                late.clock.set_fixed_time(max(dates) + "T12:00:00")
                late.goto(base + "/")
                if late.locator("[data-new-until]").count():
                    failures.append(where("expired 'new' badges still shown"))
                late.close()
            browser.close()
    server.shutdown()
    if failures:
        print("\n".join(failures))
        raise SystemExit(f"{len(failures)} feedback checks failed")
    print("Copy and add-to-reference feedback appears and recovers.")


if __name__ == "__main__":
    main()
