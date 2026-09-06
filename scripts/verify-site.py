#!/usr/bin/env python3
"""Check generated page links, assets and catalog destinations before publishing."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


def verify(root, base):
    failures = set()
    prefix = '/' + base.strip('/') if base.strip('/') else ''

    def check(url, source):
        if not url or not url.startswith('/') or url.startswith('//'):
            return
        path = unquote(urlsplit(url).path)
        if prefix:
            if not path.startswith(prefix + '/'):
                failures.add(f'{source}: URL escapes project base: {url}')
                return
            path = path[len(prefix):]
        target = root / path.lstrip('/')
        if path.endswith('/'):
            target = target / 'index.html'
        if not target.is_file():
            failures.add(f'{source}: missing destination: {url}')

    class PageLinks(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for name, value in attrs:
                if name in ('href', 'src', 'data-src', 'data-preview-en', 'data-live-source'):
                    check(value, self.source)

    pages = list(root.rglob('*.html'))
    if not pages:
        raise SystemExit('No generated HTML pages found.')
    for page in pages:
        parser = PageLinks()
        parser.source = page.relative_to(root)
        parser.feed(page.read_text(encoding='utf-8'))
    items = json.loads((root / 'api/catalog.json').read_text(encoding='utf-8'))['items']
    for item in items:
        check(item['url'], item['id'])
    if failures:
        raise SystemExit('\n'.join(sorted(failures)))
    print(f'Verified {len(pages)} HTML pages and {len(items)} catalog destinations.')


if __name__ == '__main__':
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument('site', type=Path)
    arguments.add_argument('--base', default='')
    args = arguments.parse_args()
    verify(args.site, args.base)
