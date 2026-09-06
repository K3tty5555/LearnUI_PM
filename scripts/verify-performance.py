#!/usr/bin/env python3
"""Keep static catalogs light and prevent whole-library offline prefetch regressions."""
import gzip
import sys
from html.parser import HTMLParser
from pathlib import Path


class Catalog(HTMLParser):
    scripts = 0
    live_fragments = 0
    render_blocking_links = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.scripts += 1
        if 'fragment' in attrs.get('class', '').split():
            self.live_fragments += 1
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.render_blocking_links += 1


def verify(root):
    for name in ('index.html', 'styles/index.html', 'references/index.html'):
        data = (root / name).read_bytes()
        parsed = Catalog()
        parsed.feed(data.decode('utf-8'))
        assert parsed.scripts <= 4, f'{name}: catalog scripts grew to {parsed.scripts}'
        assert parsed.live_fragments == 0, f'{name}: live specimen code returned to a catalog'
        assert parsed.render_blocking_links == 0, f'{name}: blocking CSS round trips returned'
        assert len(data) < 380_000, f'{name}: HTML exceeds 380 KB budget'
        assert len(gzip.compress(data)) < 85_000, f'{name}: compressed HTML exceeds 85 KB budget'
        print(f'{name}: {len(data)} bytes, {len(gzip.compress(data))} gzip bytes, {parsed.scripts} scripts')
    worker = (root / 'sw.js').read_text()
    assert 'GENERATED_PAGES' not in worker and '.addAll(' not in worker, 'Whole-library prefetch must not return'
    assert (root / 'offline.html').stat().st_size < 4096, 'Offline install shell grew beyond 4 KB'
    assert len(list((root / 'assets/demo-thumbs').glob('*.webp'))) == 236, 'Bilingual previews incomplete'
    print('Catalog, preview and offline-install budgets passed.')


if __name__ == '__main__':
    verify(Path(sys.argv[1] if len(sys.argv) > 1 else 'site'))
