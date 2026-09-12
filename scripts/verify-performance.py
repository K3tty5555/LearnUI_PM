#!/usr/bin/env python3
"""Keep catalog startup bounded without removing live UI specimens."""
import gzip
import json
import sys
from html.parser import HTMLParser
from pathlib import Path


class Catalog(HTMLParser):
    scripts = 0
    live_fragments = 0
    render_blocking_links = 0

    def __init__(self):
        super().__init__()
        self.live_slots = []
        self.inline_iframes = 0
        self.in_live_data = False
        self.live_data = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.scripts += 1
            self.in_live_data = attrs.get('id') == 'live-demo-data'
        if 'data-live-demo' in attrs:
            self.live_slots.append(attrs['data-live-demo'])
        if tag == 'iframe':
            self.inline_iframes += 1
        if 'fragment' in attrs.get('class', '').split():
            self.live_fragments += 1
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.render_blocking_links += 1

    def handle_data(self, data):
        if self.in_live_data:
            self.live_data += data

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_live_data = False


def verify(root):
    for name in ('index.html', 'styles/index.html', 'references/index.html'):
        data = (root / name).read_bytes()
        parsed = Catalog()
        parsed.feed(data.decode('utf-8'))
        assert parsed.scripts <= 4, f'{name}: catalog scripts grew to {parsed.scripts}'
        assert parsed.live_fragments == 0, f'{name}: unbounded live fragments returned to the main document'
        assert parsed.inline_iframes == 0, f'{name}: frames must only mount near the viewport'
        if name == 'index.html':
            entries = [item for item in json.loads((root / 'api/catalog.json').read_text())['items'] if item['type'] == 'ui-element']
            assert set(parsed.live_slots) == {item['slug'] for item in entries}, 'UI dictionary must retain all live specimens'
            initial = json.loads(parsed.live_data)
            assert set(initial['items']) == {item['slug'] for item in entries[:3]}, 'First-row demos must be available without another request'
            for entry in entries:
                payload = json.loads((root / 'api/specimens' / (entry['slug'] + '.json')).read_text())
                assert '<div class="demo ' in payload['html'], entry['slug']
        assert parsed.render_blocking_links == 0, f'{name}: blocking CSS round trips returned'
        assert len(data) < 380_000, f'{name}: HTML exceeds 380 KB budget'
        assert len(gzip.compress(data)) < 85_000, f'{name}: compressed HTML exceeds 85 KB budget'
        print(f'{name}: {len(data)} bytes, {len(gzip.compress(data))} gzip bytes, {parsed.scripts} scripts')
    worker = (root / 'sw.js').read_text()
    assert 'GENERATED_PAGES' not in worker and '.addAll(' not in worker, 'Whole-library prefetch must not return'
    assert (root / 'offline.html').stat().st_size < 4096, 'Offline install shell grew beyond 4 KB'
    catalog_items = json.loads((root / 'api/catalog.json').read_text())['items']
    expected_previews = 2 * sum(item['type'] in {'ui-element', 'visual-style', 'page-reference'} for item in catalog_items)
    assert len(list((root / 'assets/demo-thumbs').glob('*.webp'))) == expected_previews, 'Bilingual previews incomplete'
    print('Catalog, preview and offline-install budgets passed.')


if __name__ == '__main__':
    verify(Path(sys.argv[1] if len(sys.argv) > 1 else 'site'))
