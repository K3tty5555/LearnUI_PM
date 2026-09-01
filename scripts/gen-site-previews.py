#!/usr/bin/env python3
"""Render local famous-site brand mocks into 1200x630 preview images."""
from pathlib import Path
import os
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build

BASE = os.environ.get("LEARNUI_PREVIEW_URL", "http://127.0.0.1:8000")
CHROME = os.environ.get("PLAYWRIGHT_CHROME_PATH")
OUT = ROOT / "assets" / "og"
THUMBS = ROOT / "assets" / "site-thumbs"

PREVIEW_CSS = """
.brand-mock-frame {
  width: 1200px !important;
  height: 630px !important;
  margin: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: #e8f0f2 !important;
  box-shadow: none !important;
}
.brand-mock-frame .demo {
  zoom: 1.32 !important;
  transform: none !important;
}
"""


def write_thumbnail(full_path, slug):
    with Image.open(full_path) as image:
        image.resize((600, 315), Image.Resampling.LANCZOS).save(
            THUMBS / f"site-{slug}.webp", "WEBP", quality=82, method=6
        )


def main():
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    THUMBS.mkdir(parents=True, exist_ok=True)
    if "--thumbs-only" in sys.argv:
        for site in build.SITES:
            full_path = OUT / f'site-{site["slug"]}.png'
            if not full_path.is_file():
                raise RuntimeError(f"missing full preview: {full_path}")
            write_thumbnail(full_path, site["slug"])
        print(f"Generated {len(build.SITES)} WebP thumbnails.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000}, device_scale_factor=1,
            service_workers="block"
        )
        page = context.new_page()
        for index, site in enumerate(build.SITES, 1):
            page.goto(f'{BASE}/sites/{site["slug"]}/', wait_until="domcontentloaded")
            page.add_style_tag(content=PREVIEW_CSS)
            frame = page.locator(".brand-mock-frame")
            frame.wait_for(state="visible")
            box = frame.bounding_box()
            if not box:
                raise RuntimeError(f'preview frame missing for {site["slug"]}')
            full_path = OUT / f'site-{site["slug"]}.png'
            page.screenshot(
                path=str(full_path),
                clip={"x": box["x"], "y": box["y"], "width": 1200, "height": 630},
            )
            write_thumbnail(full_path, site["slug"])
            if index % 10 == 0:
                print(f"  {index}/{len(build.SITES)}")
        context.close()
        browser.close()
    print(f"Rendered {len(build.SITES)} local site previews.")


if __name__ == "__main__":
    main()
