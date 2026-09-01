#!/usr/bin/env python3
"""Mirror the live /sites/ atlas into local, buildable source files."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://learnui.qiaomu.ai"
VENDOR = ROOT / "vendor" / "sites"
OG_DIR = ROOT / "assets" / "og"
USER_AGENT = "LearnUI-PM sites mirror/1.0"
MAIN_RE = re.compile(r"<main\b[^>]*>.*?</main>", re.S | re.I)
CARD_RE = re.compile(r'<a class="style-card sites-card".*?</a>', re.S)


def fetch(path):
    request = Request(BASE + path, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=45) as response:
        return response.read()


def main_fragment(raw, source):
    text = raw.decode("utf-8")
    match = MAIN_RE.search(text)
    if not match:
        raise RuntimeError(f"missing <main> in {source}")
    return match.group(0)


class CardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.item = {}
        self.capture = ""
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        classes = set(values.get("class", "").split())
        if tag == "a" and "sites-card" in classes:
            self.item["slug"] = values["href"].strip("/").split("/")[-1]
            self.item["category"] = values.get("data-cat", "")
        if tag == "span" and "card-name-zh" in classes:
            self.capture = "nameZh"
            self.buffer = []
        elif tag == "span" and "lang-en" in classes and "card-name-zh" not in classes:
            self.capture = "nameEn"
            self.buffer = []
        elif tag == "p" and "card-tag" in classes and "lang-en" in classes:
            self.capture = "summaryEn"
            self.buffer = []
        elif tag == "p" and "card-tag" in classes and "lang-zh" in classes:
            self.capture = "summaryZh"
            self.buffer = []

    def handle_data(self, data):
        if self.capture:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if self.capture and tag in ("span", "p"):
            self.item[self.capture] = " ".join("".join(self.buffer).split())
            self.capture = ""
            self.buffer = []


def parse_manifest(hub):
    items = []
    for block in CARD_RE.findall(hub.decode("utf-8")):
        parser = CardParser()
        parser.feed(block)
        required = {"slug", "category", "nameEn", "nameZh", "summaryEn", "summaryZh"}
        if required - parser.item.keys():
            raise RuntimeError(f"incomplete site card: {parser.item}")
        parser.item["sourceUrl"] = f'{BASE}/sites/{parser.item["slug"]}/'
        items.append(parser.item)
    if len(items) != 74:
        raise RuntimeError(f"expected 74 sites, found {len(items)}")
    return items


def fetch_site(item):
    slug = item["slug"]
    html = fetch(f"/sites/{slug}/")
    image = fetch(f"/assets/og/site-{slug}.png")
    return slug, main_fragment(html, slug), image


def main():
    VENDOR.mkdir(parents=True, exist_ok=True)
    OG_DIR.mkdir(parents=True, exist_ok=True)
    hub = fetch("/sites/")
    items = parse_manifest(hub)
    (VENDOR / "index.html").write_text(main_fragment(hub, "sites hub"), encoding="utf-8")

    completed = 0
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(fetch_site, item) for item in items]
        for future in as_completed(futures):
            slug, fragment, image = future.result()
            (VENDOR / f"{slug}.html").write_text(fragment, encoding="utf-8")
            (OG_DIR / f"site-{slug}.png").write_bytes(image)
            completed += 1
            if completed % 10 == 0:
                print(f"  {completed}/{len(items)}")

    manifest = {
        "source": "https://learnui.qiaomu.ai/sites/",
        "contentSource": "https://github.com/VoltAgent/awesome-design-md",
        "license": "MIT",
        "syncedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items,
    }
    (ROOT / "data" / "sites-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Mirrored {len(items)} site pages and previews.")


if __name__ == "__main__":
    main()
