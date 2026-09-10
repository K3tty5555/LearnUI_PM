#!/usr/bin/env python3
"""Browser regression: visible UI specimens animate; hidden specimens stop.

Build and prepare the site first. Requires Playwright and its Chromium browser.
PLAYWRIGHT_CHROME_PATH can select a locally installed Chrome executable.
"""
import argparse
import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright


def run(site, base):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(site.resolve()), **kwargs)

        def translate_path(self, path):
            if base and path.startswith(base + '/'):
                path = path[len(base):]
            return super().translate_path(path)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}{base}/'
    report = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('PLAYWRIGHT_CHROME_PATH'))
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='no-preference')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            page.wait_for_selector('[data-live-demo="text-scramble"][data-live-state="running"]')

            def moving(slug, selector, expression, count=9):
                target = page.frame_locator(f'[data-live-demo="{slug}"] iframe').locator(selector).first
                values = []
                for _ in range(count):
                    values.append(target.evaluate(expression))
                    page.wait_for_timeout(160)
                assert len(set(values)) > 1, f'{slug}: specimen stopped animating: {values}'
                return len(set(values))

            report['text_scramble_states'] = moving('text-scramble', '.scr-churn', '(el)=>el.textContent', 24)
            report['spring_positions'] = moving('spring', '.spr-ball-spring', '(el)=>getComputedStyle(el).transform')
            report['easing_positions'] = moving('easing', '.eas-ball', '(el)=>getComputedStyle(el).transform', 14)
            catalog = json.loads((site / 'api/catalog.json').read_text())
            expected_ui_elements = sum(item['type'] == 'ui-element' for item in catalog['items'])
            assert page.locator('[data-live-demo]').count() == expected_ui_elements
            report['initial_active'] = page.locator('.live-specimen-frame').count()
            assert report['initial_active'] <= 12
            assert not any('/api/specimens/text-scramble.json' in request['name'] for request in page.evaluate("performance.getEntriesByType('resource').map(r=>({name:r.name}))")), 'First-row animation must not need a network request'

            page.locator('[data-live-demo="progress-indicators"]').scroll_into_view_if_needed()
            page.wait_for_selector('[data-live-demo="progress-indicators"][data-live-state="running"]')
            report['progress_values'] = moving('progress-indicators', '.pct', '(el)=>el.textContent')
            assert page.locator('[data-live-demo="spring"] iframe').count() == 0, 'Offscreen frame still running'

            page.locator('#search').fill('文本乱序')
            page.locator('#search').scroll_into_view_if_needed()
            page.wait_for_timeout(250)
            assert page.locator('.live-specimen-frame').count() == 1, 'Filtered cards still run'
            page.locator('.ls-btn[data-mode="en"]').click()
            page.wait_for_selector('[data-live-demo="text-scramble"][data-live-state="running"]')
            assert page.frame_locator('[data-live-demo="text-scramble"] iframe').locator('html').get_attribute('data-lang-mode') == 'en'
            page.locator('.ls-btn[data-mode="zh"]').click()

            page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))")
            assert page.locator('.live-specimen-frame').count() == 0, 'Hidden tab retains running specimens'
            page.evaluate("delete document.hidden;document.dispatchEvent(new Event('visibilitychange'))")
            page.wait_for_selector('[data-live-state="running"]')

            page.locator('#search').fill('')
            page.wait_for_timeout(250)
            page.emulate_media(reduced_motion='reduce')
            page.wait_for_selector('[data-live-demo="spring"][data-live-state="running"]')
            ball = page.frame_locator('[data-live-demo="spring"] iframe').locator('.spr-ball-spring')
            first = ball.evaluate('(el)=>getComputedStyle(el).transform')
            page.wait_for_timeout(350)
            assert ball.evaluate('(el)=>getComputedStyle(el).transform') == first, 'Reduced motion ignored'
            page.emulate_media(reduced_motion='no-preference')
            page.set_viewport_size({'width': 390, 'height': 844})
            page.locator('[data-live-demo="spring"]').scroll_into_view_if_needed()
            page.wait_for_selector('[data-live-demo="spring"][data-live-state="running"]')
            report['mobile_spring_positions'] = moving('spring', '.spr-ball-spring', '(el)=>getComputedStyle(el).transform')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile overflow'

            # Mount each original specimen, checking that its actual DOM loads
            # without exceptions, rather than accepting an image or a spinner.
            slugs = page.locator('[data-live-demo]').evaluate_all('(els)=>els.map(el=>el.dataset.liveDemo)')
            for slug in slugs:
                page.locator(f'[data-live-demo="{slug}"]').scroll_into_view_if_needed()
                page.wait_for_selector(f'[data-live-demo="{slug}"][data-live-state="running"]')
                assert page.frame_locator(f'[data-live-demo="{slug}"] iframe').locator('.demo').count() == 1, slug
            report['mounted_specimens'] = len(slugs)

            # A failed lazy fetch is explicit and retryable after connectivity returns.
            retry_page = context.new_page()
            retry_page.on('pageerror', lambda error: errors.append(str(error)))
            retry_page.route('**/api/specimens/accordion.json*', lambda route: route.abort())
            retry_page.goto(url)
            retry_page.locator('#search').fill('accordion')
            retry_page.locator('[data-live-demo="accordion"]').scroll_into_view_if_needed()
            retry_page.wait_for_selector('[data-live-demo="accordion"][data-live-state="error"]')
            retry_page.unroute('**/api/specimens/accordion.json*')
            retry_page.evaluate("dispatchEvent(new Event('online'))")
            retry_page.wait_for_selector('[data-live-demo="accordion"][data-live-state="running"]')
            report['retry_recovers'] = True
            assert not errors, '\n'.join(errors)
            report['errors'] = errors
            context.close()
            browser.close()
    finally:
        server.shutdown()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('site', type=Path, nargs='?', default=Path('site'))
    parser.add_argument('--base', default='/LearnUI_PM')
    args = parser.parse_args()
    run(args.site, args.base.rstrip('/'))
