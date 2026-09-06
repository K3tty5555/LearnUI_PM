#!/usr/bin/env python3
"""Render lightweight bilingual WebP previews from the real local specimens.

Run after changing a specimen. Requires Playwright and Pillow for asset generation;
normal site builds remain Python-standard-library only.
"""
import io
import os
import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build

OUT = ROOT / 'assets/demo-thumbs'
SLUGS = [e['slug'] for e in build.ENTRIES] + ['style-' + s['slug'] for s in build.STYLES] + [r['demo'] for r in build.PM_REFERENCES]
source = (ROOT / 'assets/site.js').read_text()
translation = source[source.index('  var MODE_KEY'):source.index('  /* ---------- keyboard:')]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass

    def do_GET(self):
        url = urlsplit(self.path)
        if not url.path.startswith('/_specimen/'):
            return super().do_GET()
        slug = url.path.removeprefix('/_specimen/')
        if slug not in SLUGS:
            return self.send_error(404)
        lang = 'en' if parse_qs(url.query).get('lang') == ['en'] else 'zh'
        fragment = build.demo_fragment(slug)
        html = f'''<!doctype html><html data-lang-mode="{lang}"><head><meta charset="utf-8">
<link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/reference-demos.css">
<style>html,body{{margin:0;background:transparent}}.stage{{width:400px;height:240px;border:0;border-radius:0;background:transparent;box-shadow:none}}.stage-center{{padding:22px}}.pm-demo{{box-shadow:none}}.scr-churn{{animation:none}}</style>
<script>localStorage.setItem('ntui-lang-mode','{lang}')</script></head><body>
<div class="stage stage-card"><div class="stage-center"><div class="fragment" data-slug="{slug}">{fragment}</div></div></div>
<script>window.DEMO_I18N={json.dumps(build.DEMO_I18N,ensure_ascii=False)};(function(){{{translation}}})()</script></body></html>'''
        content = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    selected = [arg for arg in sys.argv[1:] if arg != "--resume"] or SLUGS
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get("PLAYWRIGHT_CHROME_PATH"))
        context = browser.new_context(viewport={'width': 400, 'height': 240}, device_scale_factor=1.5, reduced_motion='reduce', service_workers='block')
        page = context.new_page()
        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
        for i, slug in enumerate(selected, 1):
            if '--resume' in sys.argv and all((OUT / (slug.replace('/', '-') + f'-{lang}.webp')).exists() for lang in ['zh', 'en']):
                continue
            for lang in ['zh', 'en']:
                page.goto(f'{base}/_specimen/{slug}?lang={lang}', wait_until='domcontentloaded')
                page.evaluate("document.fonts.ready")
                raw = page.screenshot(omit_background=True)
                with Image.open(io.BytesIO(raw)) as image:
                    image.save(OUT / (slug.replace('/', '-') + f'-{lang}.webp'), 'WEBP', quality=82, method=4)
            if i % 15 == 0 or i == len(selected):
                print(f'Rendered {i}/{len(selected)} bilingual specimen previews', flush=True)
        browser.close()
    server.shutdown()
    manifest = {'origin': 'Rendered from repository demos using scripts/gen-demo-previews.py; sample content is illustrative.', 'size': [600, 360], 'languages': ['zh', 'en'], 'slugs': SLUGS}
    (OUT / 'SOURCE.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
