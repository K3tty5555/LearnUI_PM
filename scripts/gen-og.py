#!/usr/bin/env python3
"""Generate 1200x630 og images for every page into assets/og/. Usage: python3 scripts/gen-og.py"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build as B  # reuse data + demo_fragment + esc

OUT = os.path.join(ROOT, "assets", "og")
TMP = os.path.join(ROOT, "site", "_ogtmp")
os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

FONT_CSS = f"""
@font-face {{ font-family: "Geist"; src: url("file://{ROOT}/assets/fonts/geist-vf.woff2") format("woff2"); font-weight: 100 900; }}
"""

SHELL = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="file://ROOTDIR/assets/site.css">
<style>FONTCSS
html,body{margin:0;width:1200px;height:630px;overflow:hidden;background:#fff;
  font-family:"Geist",-apple-system,"PingFang SC",sans-serif}
.og{display:flex;width:1200px;height:630px;border:1px solid #eaeaea}
.og-stage{width:560px;flex:none;border-right:1px solid #eaeaea;background:#fafafa;position:relative}
.og-text{flex:1;padding:64px 56px;display:flex;flex-direction:column;justify-content:center}
.og-kind{font:500 13px "Geist",monospace;letter-spacing:.12em;text-transform:uppercase;color:#a3a3a3;margin-bottom:18px}
.og-name{font-size:46px;font-weight:600;letter-spacing:-0.03em;line-height:1.12;color:#0a0a0a;margin:0 0 14px}
.og-zh{font-size:25px;font-weight:500;color:#525252;margin:0 0 28px}
.og-tag{font-size:15px;line-height:1.55;color:#737373;margin:0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.og-foot{position:absolute;left:56px;bottom:40px;display:flex;align-items:baseline;gap:10px}
.og-mark{font-size:17px;font-weight:600;letter-spacing:-0.01em;color:#0a0a0a}
.og-mark span{color:#a3a3a3;font-weight:400}
.og-url{font:13px "Geist",monospace;color:#a3a3a3}
.og-vsline{display:flex;align-items:center;gap:14px;margin-bottom:14px}
.og-vsline .og-name{font-size:34px;margin:0}
.og-vs{font:600 18px "Geist",monospace;color:#a3a3a3}
.og-halves{display:flex;width:560px;height:630px}
.og-half{flex:1;position:relative;background:#fafafa}
.og-half + .og-half{border-left:1px solid #eaeaea}
.stage-center{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:24px}
.fragment{display:flex;align-items:center;justify-content:center;width:100%;height:100%}
</style></head><body>BODYHTML</body></html>"""


def shell(body):
    return (SHELL.replace("ROOTDIR", ROOT).replace("FONTCSS", FONT_CSS).replace("BODYHTML", body))


def frag(demo_slug):
    return (f'<div class="stage-center"><div class="fragment">{B.demo_fragment(demo_slug)}</div></div>')


def text_block(kind, name, zh, tag):
    return f'''<div class="og-text">
 <p class="og-kind">{B.esc(kind)}</p>
 <h1 class="og-name">{B.esc(name)}</h1>
 <p class="og-zh">{B.esc(zh)}</p>
 <p class="og-tag">{B.esc(tag)}</p>
<div class="og-foot"><span class="og-mark">{B.SITE_NAME}</span><span class="og-url">{B.SITE_URL.split("://", 1)[-1]}</span></div>
</div>'''


def page_single(key, kind, name, zh, tag, demo_slug):
    body = f'<div class="og"><div class="og-stage">{frag(demo_slug)}</div>{text_block(kind, name, zh, tag)}</div>'
    return key, shell(body)


def page_vs(key, a, az, b, bz):
    demo_a = frag("style-" + a["slug"])
    demo_b = frag("style-" + b["slug"])
    body = f'''<div class="og">
 <div class="og-halves"><div class="og-half">{demo_a}</div><div class="og-half">{demo_b}</div></div>
 <div class="og-text">
  <p class="og-kind">Compare · 对比</p>
  <div class="og-vsline"><h1 class="og-name">{B.esc(a["name"])}</h1><span class="og-vs">vs</span><h1 class="og-name">{B.esc(b["name"])}</h1></div>
  <p class="og-zh">{B.esc(az.get("name_zh", ""))} 对比 {B.esc(bz.get("name_zh", ""))}</p>
  <div class="og-foot"><span class="og-mark">{B.SITE_NAME}</span><span class="og-url">{B.SITE_URL.split("://", 1)[-1]}</span></div>
 </div>
</div>'''
    return key, shell(body)


def page_generic(key, kind, name, zh, tag):
    body = f'<div class="og"><div class="og-stage" style="display:flex;align-items:center;justify-content:center"><span style="font-size:120px;font-weight:700;letter-spacing:-0.05em;color:#0a0a0a">?</span></div>{text_block(kind, name, zh, tag)}</div>'
    return key, shell(body)


def page_home():
    """Home share image: the site's current sections with live counts, plus the motto."""
    rows = "".join(f'<li><span>{B.icon(glyph, 22)}{B.esc(zh)}</span><b>{count}</b></li>' for _url, glyph, _en, zh, count in B.nav_links())
    stage = f'''<div class="og-stage" style="display:flex;align-items:center;justify-content:center">
<ul style="list-style:none;margin:0;padding:0;width:360px;display:flex;flex-direction:column;gap:6px">{rows}</ul>
<style>.og-stage li{{display:flex;align-items:center;justify-content:space-between;height:58px;padding:0 20px;border-radius:12px;background:#fff;border:1px solid #ececef;font-size:20px;font-weight:500;color:#242428}}
.og-stage li span{{display:flex;align-items:center;gap:14px}}.og-stage li svg{{color:#737373}}.og-stage li b{{font:500 16px "Geist",monospace;color:#a3a3a3}}</style></div>'''
    sections = " · ".join(zh for _u, _g, _e, zh, _c in B.nav_links())
    body = f'<div class="og">{stage}{text_block(B.SITE_NAME, "寻之于目，识美于此", B.UI["heroSub"], "察有形之美，汇万象之观。" + sections)}</div>'
    return "_home", shell(body)


def jobs():
    js = []
    for e in B.ENTRIES:
        z = B.ZH[e["slug"]]
        js.append(page_single(e["slug"], f'UI Dictionary · {e["platform"]}', e["name"], z["name_zh"], e["tagline"], e["slug"]))
    for s in B.STYLES:
        z = B.style_zh(s)
        js.append(page_single("style-" + s["slug"], "Visual Style · 视觉风格", s["name"],
                              z.get("name_zh", s["name"]), B.first_para(s.get("tagline", "")), "style-" + s["slug"]))
    for a, b in B.vs_pairs():
        A, Bb = B.STYLE_BY_SLUG[a], B.STYLE_BY_SLUG[b]
        x, y = sorted([a, b])
        js.append(page_vs(f"vs-{x}-vs-{y}", A, B.style_zh(A), Bb, B.style_zh(Bb)))
    js.append(page_home())
    js.append(page_generic("_styles", "Styles Atlas · 风格图鉴", B.UI["stylesTitle"], B.UI["stylesTitleZh"], B.STYLES_META.get("hubTagline", "")))
    js.append(("_default", page_home()[1]))
    return js


def main():
    from playwright.sync_api import sync_playwright
    todo = jobs()
    force = "--force" in sys.argv
    if not force:
        todo = [(k, h) for k, h in todo if not os.path.exists(os.path.join(OUT, k + ".png"))]
    if not todo:
        print("all og images exist, nothing to do")
        return
    print(f"generating {len(todo)} og images…")
    with sync_playwright() as p:
        chrome_path = os.environ.get("PLAYWRIGHT_CHROME_PATH")
        b = p.chromium.launch(executable_path=chrome_path) if chrome_path else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        for i, (key, html) in enumerate(todo, 1):
            f = os.path.join(TMP, key + ".html")
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(html)
            pg.goto("file://" + f)
            pg.wait_for_timeout(280)
            pg.screenshot(path=os.path.join(OUT, key + ".png"))
            if i % 20 == 0:
                print(f"  {i}/{len(todo)}")
        b.close()
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"done → assets/og/ ({len(todo)} images)")


if __name__ == "__main__":
    main()
