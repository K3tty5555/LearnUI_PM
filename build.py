#!/usr/bin/env python3
"""Learn UIUX static site builder - bilingual (EN/中文) replica of namethatui.com.
Stdlib only. Reads data/ + demos/, writes site/."""
import json, html, os, shutil, datetime, subprocess, sys, hashlib, base64, re
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = os.environ.get("SITE_URL", "https://www.kettywu.art/UIUX").rstrip("/")
SITE_NAME = "Learn UIUX"
NEW_SLUGS = {"text-scramble","spring","easing","masonry","bento-grid","hamburger-menu","lightbox","marquee","container-morph","otp-input","duration-picker","animated-counter","scroll-progress-indicator","code-block","destructive-action","ai-status-orb","agent-processing-state","streaming-response","agent-approval-card","diff-viewer","agent-input-composer","inline-citations","agent-task-list","scroll-triggered","scroll-linked","parallax","scroll-snap","horizontal-scroll","liquid-glass-material","typography-details","scroll-zoom-out","arc-carousel","tilt-card","hover-fan-out","particle-repel","file-upload","loading-choreography","interaction-details","carousel","number-input","timeline","pagination","border-beam","card-swap","tick-slider","hold-to-record","context-meter"}
STYLE_NEW_SLUGS = {"frutiger-metro","anti-design","acid-graphics","risograph","zine-collage","steampunk","dieselpunk","biopunk","afrofuturism","de-stijl","constructivism","pop-art","surrealism","art-nouveau","holographic","isometric-3d","line-art","hand-drawn","fantasy-rpg","lcars","mono-color-editorial-print"}

def load(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)

ENTRIES = load("data/entries.json")
UI = load("data/ui.json")
GUIDES = load("data/guides.json")
ZH = {}
for i in range(1, 5):
    ZH.update(load(f"data/zh/entries-{i}.json"))
GUIDES_ZH = load("data/zh/guides.json")

def load_or(p, default):
    full = os.path.join(ROOT, p)
    if not os.path.exists(full):
        return default
    return load(p)

def _nn(obj):
    """Recursively convert None to "" so partial/WIP data stays renderable."""
    if obj is None:
        return ""
    if isinstance(obj, dict):
        return {k: _nn(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_nn(v) for v in obj]
    return obj

STYLES = _nn(load_or("data/styles.json", []))
STYLES_META = _nn(load_or("data/styles-meta.json", {"hubTagline": "", "governedNote": "", "researching": []}))
STYLES_ZH = _nn(load_or("data/zh/styles.json", {}))
STYLES_META_ZH = _nn(load_or("data/zh/styles-meta-zh.json", {"hubTagline_zh": "", "governedNote_zh": ""}))
STYLE_BY_SLUG = {s["slug"]: s for s in STYLES}
DEMO_I18N = _nn(load_or("data/demo-i18n.json", {"global": {}, "patterns": [], "demos": {}}))
SITES_META = _nn(load_or("data/sites-manifest.json", {"items": []}))
SITES = SITES_META.get("items", [])
LOGOS_META = _nn(load_or("data/logos.json", {"issues": [], "types": [], "uses": [], "logos": []}))
LOGO_ISSUES = {i["id"]: i for i in LOGOS_META["issues"]}
LOGOS = LOGOS_META["logos"]
LOGO_TYPES = {t["id"]: t for t in LOGOS_META["types"]}
LOGO_USES = {u["id"]: u for u in LOGOS_META["uses"]}
GRAPHICS_META = _nn(load_or("data/graphics.json", {"issues": [], "types": [], "styleTags": [], "techniques": [], "cases": []}))
GRAPHICS = GRAPHICS_META["cases"]
GRAPHIC_ISSUES = {i["id"]: i for i in GRAPHICS_META["issues"]}
GRAPHIC_TYPES = {t["id"]: t for t in GRAPHICS_META["types"]}
GRAPHIC_STYLES = {t["id"]: t for t in GRAPHICS_META["styleTags"]}
GRAPHIC_TECHS = {t["id"]: t for t in GRAPHICS_META["techniques"]}
SITE_CATEGORY_ZH = {
    "AI & LLM Platforms": "AI 与大模型平台",
    "Developer Tools & IDEs": "开发者工具与 IDE",
    "Backend, Database & DevOps": "后端、数据库与 DevOps",
    "Productivity & SaaS": "生产力与 SaaS",
    "Design & Creative Tools": "设计与创意工具",
    "Fintech & Crypto": "金融科技与加密货币",
    "E-commerce & Retail": "电商与零售",
    "Media & Consumer Tech": "媒体与消费科技",
    "Automotive": "汽车",
    "Retro Web": "复古网页",
}
SITE_VIBE_RULES = [
    ("minimal", "Minimal & restrained", "极简克制", ["minimal", "restraint", "restrained", "austere", "subtraction", "monochrome", "克制", "极简", "禁欲", "黑白"]),
    ("dark", "Dark & immersive", "暗色沉浸", ["dark", "near-black", "black canvas", "night", "深色", "近黑", "暗色", "夜间", "纯黑"]),
    ("editorial", "Editorial typography", "编辑排版", ["editorial", "magazine", "publication", "serif", "编辑", "杂志", "衬线", "印刷"]),
    ("bold", "Bold & high contrast", "鲜明高对比", ["high-contrast", "saturated", "colossal", "electric", "高对比", "高饱和", "巨型", "电光"]),
    ("playful", "Playful & illustrative", "趣味插画", ["playful", "friendly", "hand-drawn", "illustration", "pastel", "sticker", "手绘", "插画", "粉彩", "友好"]),
    ("technical", "Technical & product-led", "技术产品感", ["developer", "engineering", "terminal", "code", "database", "documentation", "技术", "工程", "终端", "代码", "数据库", "文档"]),
    ("cinematic", "Cinematic & photography-led", "沉浸影像", ["cinematic", "photography", "full-bleed", "immersive", "video", "电影", "摄影", "全幅", "沉浸", "影像"]),
    ("retro", "Retro web", "复古网页", ["1996", "2001", "retro", "y2k", "复古", "千禧", "目录时代"]),
]

def static_asset_version():
    digest = hashlib.sha256()
    for path in ("assets/site.css", "assets/workspace.css", "assets/site.js", "assets/live-demos.js"):
        with open(os.path.join(ROOT, path), "rb") as handle:
            digest.update(handle.read())
    digest.update(json.dumps(DEMO_I18N, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()[:12]

ASSET_VERSION = static_asset_version()

OUT = os.path.join(ROOT, "site")

def esc(s):
    return html.escape(str(s), quote=True)

def t(key, **kw):
    """UI copy: returns (en, zh) with optional format params."""
    en, zh = UI[key], UI.get(key + "Zh", "")
    for k, v in kw.items():
        en = en.replace("{" + k + "}", str(v))
        zh = zh.replace("{" + k + "}", str(v))
    return en, zh

def bi(en, zh, tag="p", cls="", clsen="", clszh=""):
    """Bilingual block: EN line + ZH line."""
    if not zh:
        return f'<{tag} class="lang-en {cls} {clsen}">{esc(en)}</{tag}>'
    return (f'<{tag} class="lang-en {cls} {clsen}">{esc(en)}</{tag}>'
            f'<{tag} class="lang-zh {cls} {clszh}">{esc(zh)}</{tag}>')

def bi_raw(en_html, zh_html, tag="p", cls="", clsen="", clszh=""):
    """Bilingual block with pre-rendered HTML (already escaped)."""
    if not zh_html:
        return f'<{tag} class="lang-en {cls} {clsen}">{en_html}</{tag}>'
    return (f'<{tag} class="lang-en {cls} {clsen}">{en_html}</{tag}>'
            f'<{tag} class="lang-zh {cls} {clszh}">{zh_html}</{tag}>')

def paras(text_en, text_zh, cls):
    """Multi-paragraph bilingual text (split on blank lines)."""
    out = []
    ens = [p.strip() for p in (text_en or "").split("\n\n") if p.strip()]
    zhs = [p.strip() for p in (text_zh or "").split("\n\n") if p.strip()]
    for i, p in enumerate(ens):
        z = zhs[i] if i < len(zhs) else ""
        out.append(bi(p, z, "p", cls))
    return "".join(out)

def demo_fragment(slug):
    path = os.path.join(ROOT, "demos", slug + ".html")
    if not os.path.exists(path):
        return f'<div class="demo demo-missing" style="color:#a3a3a3;font:12px monospace">specimen pending: {esc(slug)}</div>'
    with open(path, encoding="utf-8") as f:
        return f.read()

def stage(slug, detail=False, eager=False):
    if not detail:
        thumbnail = esc(slug.replace("/", "-"))
        preview_zh = f"/assets/demo-thumbs/{thumbnail}-zh.webp"
        preview_en = f"/assets/demo-thumbs/{thumbnail}-en.webp"
        if eager:
            def inline_preview(language):
                with open(os.path.join(ROOT, "assets/demo-thumbs", thumbnail + "-" + language + ".webp"), "rb") as asset:
                    return "data:image/webp;base64," + base64.b64encode(asset.read()).decode("ascii")
            preview_zh, preview_en = inline_preview("zh"), inline_preview("en")
        state = "" if eager else " preview-pending"
        source_attr = f'srcset="{preview_en}" data-preview-en' if eager else f'data-preview-en="{preview_en}"'
        image_attr = f'src="{preview_zh}"' if eager else f'data-src="{preview_zh}"'
        return (f'<div class="stage stage-card pe-none{state}" inert>'
                f'<picture data-preview><source media="(max-width: 0px)" {source_attr}>'
                f'<img class="stage-preview" {image_attr} width="600" height="360" alt="" decoding="async"></picture>'
                '<span class="preview-loading"><span class="lang-zh">预览加载中…</span><span class="lang-en">Loading preview…</span></span>'
                '<span class="stage-preview-error" hidden>打开详情查看标本</span>'
                f'<noscript><img class="stage-preview" src="/assets/demo-thumbs/{thumbnail}-zh.webp" width="600" height="360" loading="lazy" alt=""><style>.preview-loading{{display:none}}</style></noscript></div>')
    safe_slug = re.sub(r"[^a-z0-9_-]", "-", slug.lower())
    return (f'<div class="stage stage-detail stage-detail-{safe_slug}"><div class="stage-center">'
            f'<div class="fragment" data-slug="{esc(slug)}">{demo_fragment(slug)}</div>'
            f'</div></div>')

def specimen_payload(entry):
    return {"slug": entry["slug"], "html": demo_fragment(entry["slug"])}


def live_stage(entry):
    payload = specimen_payload(entry)
    revision = hashlib.sha256(payload["html"].encode("utf-8")).hexdigest()[:12]
    first_row = entry in ENTRIES[:3]
    # The first row paints actual HTML immediately. Scripts execute only inside
    # visible isolated frames, never in all 78 catalog cards at once.
    still = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", payload["html"], flags=re.I) if first_row else ""
    initial = f'<div class="stage-center live-demo-still">{still}</div>' if first_row else ''
    return (f'<div class="stage stage-card pe-none" data-live-demo="{esc(entry["slug"])}"'
            f' data-live-name="{esc(entry["name"])}" data-live-state="idle"'
            f' data-live-source="/api/specimens/{esc(entry["slug"])}.json?v={revision}" inert>'
            + initial +
            ('<span class="live-demo-loading"><span class="lang-zh">动效加载中…</span><span class="lang-en">Loading animation…</span></span>' if not first_row else '') +
            '<span class="live-demo-error"><span class="lang-zh">动效加载失败，点开详情查看</span><span class="lang-en">Animation unavailable. Open the detail to retry.</span></span>'
            f'<noscript><img class="stage-preview" src="/assets/demo-thumbs/{esc(entry["slug"])}-zh.webp" width="600" height="360" loading="lazy" alt=""><style>.live-demo-loading{{display:none}}</style></noscript></div>')


def select_button(item_id, compact=False):
    cls = "select-toggle select-toggle-compact" if compact else "btn select-toggle"
    return (f'<button type="button" class="{cls}" data-select-id="{esc(item_id)}" '
            f'aria-pressed="false"><span data-select-label>加入参考</span></button>')

def selection_panel():
    return f'''<div class="selection-dock" id="selection-dock" hidden>
 <button type="button" class="selection-dock-button" id="selection-open" aria-controls="selection-dialog">
  已选参考 <b id="selection-count">0</b>
 </button>
</div>
<dialog class="selection-dialog" id="selection-dialog" aria-labelledby="selection-title">
 <div class="selection-head">
  <div><h2 id="selection-title">我的参考集</h2><p>组合知名网站、UI 元素、视觉风格和平面设计案例，导出给 AI。</p></div>
  <button type="button" class="icon-button" id="selection-close" aria-label="关闭">{icon("close")}</button>
 </div>
 <div class="selection-list" id="selection-list"></div>
 <div class="selection-empty" id="selection-empty"><strong>你的下一份设计，从这里开始。</strong><p>在任意案例旁点击「加入参考」，就能把品牌、组件、风格和平面设计案例组合成一份 AI 设计说明。</p></div>
 <label class="collection-brief" for="collection-brief">这次想做什么？<textarea id="collection-brief" rows="3" placeholder="例如：为项目管理工具设计一个清晰、轻量的任务看板。"></textarea><span>选填，会一起写入导出的设计说明。</span></label>
 <div class="selection-actions">
  <button type="button" class="btn" id="selection-copy-md">复制 Markdown</button>
  <button type="button" class="btn" id="selection-download-json">下载 JSON</button>
  <button type="button" class="btn btn-danger" id="selection-clear">清空</button>
 </div>
 <p class="selection-status" id="selection-status" role="status"></p>
</dialog>'''

def global_search_panel():
    return f'''<dialog class="global-search-dialog" id="global-search-dialog" aria-labelledby="global-search-title">
 <div class="global-search-head"><h2 id="global-search-title"><span class="lang-zh">搜索参考库</span><span class="lang-en">Search the library</span></h2><button type="button" class="icon-button" id="global-search-close" aria-label="关闭搜索">{icon("close")}</button></div>
 <label class="global-search-field">{icon("search",20)}<input type="search" id="global-search-input" placeholder="搜索组件、风格、品牌或页面…" data-ph-zh="搜索组件、风格、品牌或页面…" data-ph-en="Search components, styles, brands, or pages…" autocomplete="off" aria-label="搜索整个参考库"></label>
 <p class="global-search-status" id="global-search-status" role="status">输入关键词，搜索所有参考。</p><div class="global-search-results" id="global-search-results"></div>
 <div class="global-search-footer"><span>↑ ↓ 选择 · Enter 打开</span><span>Esc 关闭</span></div>
</dialog>'''


def icon(name, size=18):
    paths = {
        "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
        "page": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 9v11"/>',
        "globe": '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
        "style": '<circle cx="9" cy="9" r="6"/><rect x="9" y="9" width="12" height="12" rx="2"/>',
        "book": '<path d="M12 5v16M12 5C8 2 4 3 2 4v15c4-2 7-1 10 2 3-3 6-4 10-2V4c-2-1-6-2-10 1Z"/>',
        "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
        "bookmark": '<path d="M6 4h12v17l-6-4-6 4V4Z"/>',
        "arrow": '<path d="M4 12h16m-6-6 6 6-6 6"/>',
        "shuffle": '<path d="m18 3 3 3-3 3m0 6 3 3-3 3M3 6h3c5 0 7 12 12 12h3M3 18h3c2 0 4-3 6-6s4-6 6-6h3"/>',
        "close": '<path d="m6 6 12 12M6 18 18 6"/>',
        "mark": '<path d="M12 3 4 7.5v9L12 21l8-4.5v-9L12 3Z"/><path d="M12 8v8M8.5 10l7 4M15.5 10l-7 4"/>',
        "poster": '<rect x="5" y="3" width="14" height="18" rx="1.5"/><path d="M8 7h8M8 10h5M5 15l4-3 4 3 3-2 3 2"/>',
        "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths.get(name, paths["grid"])}</svg>'


def nav_links():
    """Site sections shown in the sidebar (also drawn on the home share image by scripts/gen-og.py)."""
    return [("/#top", "grid", "UI elements", "UI 元素", len(ENTRIES)),
            ("/sites/", "globe", "Website systems", "知名网站", len(SITES)),
            ("/logos/", "mark", "Logo atlas", "Logo 图鉴", len(LOGOS)),
            ("/graphics/", "poster", "Graphic design", "平面设计", len(GRAPHICS)),
            ("/styles/", "style", "Visual styles", "视觉风格", len(STYLES))]


def header():
    links = nav_links()
    nav = "".join(f'<a href="{url}">{icon(glyph)}<span class="nav-label"><span class="lang-en">{en}</span><span class="lang-zh nav-zh">{zh}</span></span><span class="nav-count">{count}</span></a>' for url, glyph, en, zh, count in links)
    return f'''<a class="skip-link" href="#main-content">跳转到内容</a>
<header class="site-header">
 <div class="wrap header-in">
  <a class="wordmark" href="/"><img src="/assets/icons/ai-pm-client-circle-64.png" alt="" width="32" height="32"><span>Learn UIUX</span></a>
  <p class="sidebar-caption"><span class="lang-zh">寻之于目，识美于此。</span><span class="lang-en">Seek with your eyes. Know beauty here.</span></p>
  <button class="global-search-open" type="button" data-global-search>{icon("search")}<span class="lang-zh">搜索所有参考</span><span class="lang-en">Search library</span><kbd>⌘ K</kbd></button>
  <div class="lang-switch mobile-language" role="group" aria-label="阅读语言"><button type="button" data-mode="zh" class="ls-btn">中文</button><button type="button" data-mode="en" class="ls-btn">EN</button></div>
  <nav class="site-nav" aria-label="主导航">{nav}</nav>
  <button class="sidebar-selection" type="button" data-open-selection>{icon("bookmark")}<span class="lang-zh">我的参考集</span><span class="lang-en">My collection</span><b data-selection-total>0</b></button>
  <div class="sidebar-bottom">
   <p><span class="lang-zh">于辞汇间，邂逅良美</span><span class="lang-en">Meet good design among the words.</span></p>
   <div class="lang-switch" role="group" aria-label="阅读语言">
    <button type="button" data-mode="zh" class="ls-btn">中文</button><button type="button" data-mode="en" class="ls-btn">EN</button>
   </div>
   <a class="source-link" href="/sources/"><span class="lang-zh">来源与许可证</span><span class="lang-en">Sources &amp; license</span>{icon("arrow", 14)}</a>
  </div>
 </div>
</header>'''

def footer():
    return '''<footer class="library-footer"><span>Learn UIUX <span class="lang-zh">· 让灵感有据可依</span><span class="lang-en">· A shared language for design</span></span><div><a href="/sources/"><span class="lang-zh">来源与许可证</span><span class="lang-en">Sources &amp; license</span></a><a href="#top"><span class="lang-zh">回到顶部</span><span class="lang-en">Back to top</span></a></div></footer><div class="def-pop" id="def-pop" hidden>
 <div class="def-word" id="def-word"></div>
 <div class="def-body" id="def-body"></div>
 <div class="def-src" id="def-src"></div>
</div>'''

def page(title_en, title_zh, desc_en, desc_zh, body, path="", og_image="/assets/og/_default.png", jsonld=""):
    body = body.replace('<main ', '<main id="main-content" tabindex="-1" ', 1)
    chrome_css = "\n".join(open(os.path.join(ROOT, "assets", name), encoding="utf-8").read() for name in ("site.css", "workspace.css"))
    chrome_js = open(os.path.join(ROOT, "assets/site.js"), encoding="utf-8").read()
    if 'data-live-demo=' in body:
        live_data = {"translations": DEMO_I18N, "items": {entry["slug"]: specimen_payload(entry) for entry in ENTRIES[:3]}}
        safe_json = json.dumps(live_data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        body += '<script id="live-demo-data" type="application/json">' + safe_json + '</script>'
        chrome_js += "\n" + open(os.path.join(ROOT, "assets/live-demos.js"), encoding="utf-8").read()
    if 'data-gd-detail' in body:
        chrome_js += "\n" + open(os.path.join(ROOT, "assets/graphics.js"), encoding="utf-8").read()
    demo_assets = ''
    demo_js = ('<script>window.DEMO_I18N=' + json.dumps(DEMO_I18N, ensure_ascii=False).replace('</', '<\\/') + ';</script>') if 'class="fragment" data-slug=' in body else ''
    url = SITE_URL + "/" + path
    og_url = SITE_URL + og_image
    ld = f'<script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    return f'''<!DOCTYPE html>
<html lang="zh-CN" data-lang-mode="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title_zh) + " · " if title_zh else ""}Learn UIUX</title>
<meta name="description" content="{esc(desc_zh)} {esc(desc_en)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:title" content="{esc(title_en) + " · " + esc(title_zh) + " - " if title_zh else ""}{SITE_NAME}">
<meta property="og:description" content="{esc(desc_zh)} {esc(desc_en)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{esc(og_url)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{esc(og_url)}">
<meta name="theme-color" content="#f7f7f8">
{ld}
<link rel="manifest" href="/manifest.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME} RSS" href="/feed.xml">
<link rel="icon" href="/assets/icons/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<script>
// 默认纯中文；用户手动切换后持久化。旧的「对照」偏好归一到中文。
(function(){{try{{
  var m=localStorage.getItem("ntui-lang-mode");
  if(m!=="zh"&&m!=="en"){{
    m="zh";
  }}
  document.documentElement.setAttribute("data-lang-mode",m);
}}catch(e){{}}}})();
</script>
<style data-site-theme="monochrome-glass">{chrome_css}</style>
{demo_assets}
</head>
<body id="top">
{body}
{selection_panel()}
{global_search_panel()}
{demo_js}
<script data-site-runtime="{ASSET_VERSION}">{chrome_js}</script>
</body>
</html>'''

def ld_graph(*nodes):
    return json.dumps({"@context": "https://schema.org", "@graph": [n for n in nodes if n]}, ensure_ascii=False)

def ld_breadcrumb(items):
    """items: [(name, url_path), ...]"""
    return {"@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE_URL + u}
                                 for i, (n, u) in enumerate(items)]}

def ld_defined_term(name, desc, path):
    return {"@type": "DefinedTerm", "name": name, "description": desc,
            "url": SITE_URL + path,
            "inDefinedTermSet": {"@type": "DefinedTermSet", "name": SITE_NAME, "url": SITE_URL}}

def entry_url(e):
    return f'/{e["platform"]}/{e["slug"]}/'

def card(e):
    z = ZH[e["slug"]]
    new = f'<span class="tag tag-new">{esc(UI["newBadge"])}</span>' if e["slug"] in NEW_SLUGS else ""
    sym = e["api"][0]["symbol"]
    return f'''<article class="catalog-item" data-platform="{e["platform"]}" data-slug="{e["slug"]}">
<a class="card" href="{entry_url(e)}">
 {live_stage(e)}
 <div class="card-meta">
  <h3 class="card-name">
   <span class="lang-en">{esc(e["name"])}{new}</span>
   <span class="lang-zh card-name-zh">{esc(z["name_zh"])}</span>
   <span class="tag tag-platform">{esc(e["platform"])}</span>
  </h3>
  <p class="card-symbol">{esc(sym)}</p>
  {bi(e["tagline"], z["tagline_zh"], "p", "card-tag")}
 </div>
</a>
{select_button("entry:" + e["slug"], compact=True)}
</article>'''

def homepage():
    search_index = []
    for e in ENTRIES:
        z = ZH[e["slug"]]
        search_index.append({
            "slug": e["slug"], "platform": e["platform"], "url": entry_url(e),
            "name": e["name"], "name_zh": z["name_zh"], "tagline": e["tagline"],
            "tagline_zh": z["tagline_zh"], "symbol": e["api"][0]["symbol"],
            "aka": e["aka"], "aka_zh": z["aka_zh"],
            "fuzzy": e["fuzzy"], "fuzzy_zh": z["fuzzy_zh"],
        })
    cards = "\n".join(card(e) for e in ENTRIES)
    en_ph, zh_ph = t("searchPlaceholder")
    en_s, zh_s = t("surprise")
    en_vp, zh_vp = t("vibePromo")
    en_all, zh_all = t("tabAll"); en_web, zh_web = t("tabWeb"); en_mac, zh_mac = t("tabMacos")
    search_json = json.dumps(search_index, ensure_ascii=False).replace("</", "<\\/")
    body = f'''{header()}
<main class="wrap home-page">
 <section class="home-intro">
  <div class="home-intro-copy">
   <h1><span class="lang-zh">寻之于目，<br>识美于此</span><span class="lang-en">Seek with your eyes.<br>Know beauty here.</span></h1>
   <p class="home-description"><span class="lang-zh">察有形之美，汇万象之观</span><span class="lang-en">Behold beauty in form. Gather views of everything.</span></p>
  </div>
  <div class="hero-specimen">
   <div class="hero-command">
    <button type="button" class="hero-command-search" data-global-search>{icon("search")}<span class="lang-zh">你想做什么？</span><span class="lang-en">What would you like to do?</span><kbd>⌘ K</kbd></button>
    <a href="/graphics/">{icon("poster")}<span class="lang-zh">看平面设计案例</span><span class="lang-en">Explore graphic design</span>{icon("arrow",15)}</a>
    <a href="/styles/">{icon("style")}<span class="lang-zh">探索一种视觉风格</span><span class="lang-en">Explore a visual style</span>{icon("arrow",15)}</a>
    <button type="button" data-open-selection>{icon("bookmark")}<span class="lang-zh">打开我的参考集</span><span class="lang-en">Open my collection</span>{icon("arrow",15)}</button>
   </div>
  </div>
 </section>
 <div class="collection-shortcuts"><a href="/graphics/"><span class="lang-zh">想看案例</span><span class="lang-en">See real work</span><strong>{len(GRAPHICS)} <span class="lang-zh">个平面设计案例</span><span class="lang-en">cases</span></strong>{icon("arrow",16)}</a><a href="/sites/"><span class="lang-zh">想找灵感</span><span class="lang-en">Find inspiration</span><strong>{len(SITES)} <span class="lang-zh">个品牌规范</span><span class="lang-en">websites</span></strong>{icon("arrow",16)}</a><a href="/styles/"><span class="lang-zh">想定风格</span><span class="lang-en">Set the style</span><strong>{len(STYLES)} <span class="lang-zh">种视觉风格</span><span class="lang-en">visual styles</span></strong>{icon("arrow",16)}</a></div>
 <section class="hero library-head" id="library">
  <div class="library-title"><h2><span class="lang-zh">UI 元素词典</span><span class="lang-en">UI dictionary</span></h2><span class="library-help"><span class="lang-zh">点开案例，了解它的名字与用法</span><span class="lang-en">Open a case to learn its name and use</span></span></div>
  <div class="controls">
   <div class="search-box">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
    <input id="search" type="search" autocomplete="off"
     data-ph-en="{esc(en_ph)}" data-ph-zh="{esc(zh_ph)}" placeholder="{esc(zh_ph)} / {esc(en_ph)}" aria-label="搜索 UI 元素">
    <kbd class="search-kbd">/</kbd>
   </div>
   <button type="button" id="surprise" class="btn btn-ghost">{icon("shuffle",16)} <span class="lang-en">{esc(en_s)}</span><span class="lang-zh">{esc(zh_s)}</span></button>
   <div class="tabs" role="group" aria-label="平台筛选">
    <button type="button" class="tab active" data-filter="all"><span class="lang-en">{esc(en_all)}</span><span class="lang-zh">{esc(zh_all)}</span></button>
    <button type="button" class="tab" data-filter="web"><span class="lang-en">{esc(en_web)}</span><span class="lang-zh">{esc(zh_web)}</span></button>
    <button type="button" class="tab" data-filter="macos"><span class="lang-en">{esc(en_mac)}</span><span class="lang-zh">{esc(zh_mac)}</span></button>
   </div>
  </div>
 </section>
 <section id="dictionary" class="grid" aria-label="UI 元素标本">
{cards}
 </section>
 <div id="no-result" class="no-result" hidden>
  <p><span class="lang-en">{esc(UI["searchNoResult"])}</span><span class="lang-zh">{esc(UI["searchNoResultZh"])}</span></p>
  <div class="no-result-examples">
   <button type="button" data-q="the dots menu">“the dots menu”</button>
   <button type="button" data-q="mac window buttons">“mac window buttons”</button>
   <button type="button" data-q="红绿灯">「红绿灯」</button>
   <button type="button" data-q="角落里弹出来的小消息">「角落里弹出来的小消息」</button>
  </div>
 </div>
</main>
{footer()}
<script id="search-index" type="application/json" data-src="/api/search-index.json"></script>'''
    return page("", "", UI["heroSub"], UI["heroSubZh"], body, og_image="/assets/og/_home.png")

def api_table(e, z):
    en_f, zh_f = t("framework"); en_s, zh_s = t("symbol"); en_n, zh_n = t("note")
    rows = []
    for i, a in enumerate(e["api"]):
        note_en = a.get("note", "")
        note_zh = z["api_notes_zh"][i] if i < len(z["api_notes_zh"]) else None
        note = ""
        if note_en:
            note = f'<span class="lang-en">{esc(note_en)}</span><span class="lang-zh zh-line">{esc(note_zh or "")}</span>'
        rows.append(f'''<tr>
 <td class="mono fw">{esc(a["framework"])}</td>
 <td class="mono sym">{esc(a["symbol"])}</td>
 <td class="note">{note}</td>
</tr>''')
    return f'''<div class="table-scroll"><table class="api-table">
<thead><tr><th>{esc(en_f)}<span class="lang-zh th-zh">{esc(zh_f)}</span></th><th>{esc(en_s)}<span class="lang-zh th-zh">{esc(zh_s)}</span></th><th>{esc(en_n)}<span class="lang-zh th-zh">{esc(zh_n)}</span></th></tr></thead>
<tbody>{"".join(rows)}</tbody>
</table></div>'''

def copy_block(text_en, text_zh, block_id):
    en_c, zh_c = t("copy"); en_cd, zh_cd = t("copied")
    return f'''<div class="copy-block" data-copy-target="{block_id}">
 <button type="button" class="btn btn-copy" data-copy="{block_id}" data-label-en="{esc(en_c)}" data-label-zh="{esc(zh_c)}" data-done-en="{esc(en_cd)}" data-done-zh="{esc(zh_cd)}"><span class="lang-en">{esc(en_c)}</span><span class="lang-zh">{esc(zh_c)}</span></button>
 <div class="copy-text">
  <p class="lang-en" id="{block_id}">{esc(text_en)}</p>
  <p class="lang-zh zh-copy">{esc(text_zh)}</p>
 </div>
</div>'''

def entry_page(e):
    z = ZH[e["slug"]]
    en_b, zh_b = t("indexCrumb")
    plat_label = "Web" if e["platform"] == "web" else "macOS"
    new = f'<span class="tag tag-new">{esc(UI["newBadge"])}</span>' if e["slug"] in NEW_SLUGS else ""
    aka_en = ", ".join(e["aka"]); aka_zh = "、".join(z["aka_zh"])
    fuzzy_rows = "".join(
        f'<li><span class="lang-en">“{esc(f)}”</span><span class="lang-zh zh-line">「{esc(z["fuzzy_zh"][i])}」</span></li>'
        for i, f in enumerate(e["fuzzy"]))
    parts = []
    en_pf, zh_pf = t("promptFragment")
    for i, p in enumerate(e.get("parts", [])):
        pz = z["parts_zh"].get(p["id"], {})
        parts.append(f'''<li class="part">
 <div class="part-head">
  <span class="part-num">{i+1}</span>
  <span class="part-name"><span class="lang-en">{esc(p["name"])}</span><span class="lang-zh part-name-zh">{esc(pz.get("name_zh",""))}</span></span>
  <code class="part-api">{esc(p["api"])}</code>
 </div>
 {bi(p["description"], pz.get("description_zh",""), "p", "part-desc")}
 <div class="part-prompt">
  <span class="part-prompt-label"><span class="lang-en">{esc(en_pf)}</span><span class="lang-zh">{esc(zh_pf)}</span></span>
  <p class="lang-en mono-sm">{esc(p["prompt"])}</p>
  <p class="lang-zh mono-sm">{esc(pz.get("prompt_zh",""))}</p>
 </div>
</li>''')
    anatomy = ""
    if parts:
        en_a, zh_a = t("anatomy")
        anatomy = f'''<section class="sect">
 <h2 class="section-title"><span class="lang-en">{esc(en_a)}</span><span class="lang-zh">{esc(zh_a)}</span></h2>
 <ol class="parts">{"".join(parts)}</ol>
</section>'''
    related = []
    by_slug = {x["slug"]: x for x in ENTRIES}
    for r in e.get("related", []):
        if r in by_slug:
            re_ = by_slug[r]
            rz = ZH[r]
            related.append(f'''<a class="rel-card" href="{entry_url(re_)}">
 <span class="rel-name"><span class="lang-en">{esc(re_["name"])}</span><span class="lang-zh rel-name-zh">{esc(rz["name_zh"])}</span></span>
 <span class="rel-sym">{esc(re_["api"][0]["symbol"])}</span>
</a>''')
    see_also = ""
    if related:
        en_sa, zh_sa = t("seeAlso")
        see_also = f'''<section class="sect">
 <h2 class="section-title"><span class="lang-en">{esc(en_sa)}</span><span class="lang-zh">{esc(zh_sa)}</span></h2>
 <div class="rel-grid">{"".join(related)}</div>
</section>'''
    en_p, zh_p = t("promptSection"); en_d, zh_d = t("debugSection")
    en_ic, zh_ic = t("inCode"); en_ac, zh_ac = t("alsoCalled"); en_fy, zh_fy = t("ifYouCalledIt")
    en_cp, zh_cp = t("copyPage"); en_cd, zh_cd = t("copied")
    md = entry_markdown(e, z)
    body = f'''{header()}
<main class="wrap entry">
 <nav class="crumbs">
  <a href="/"><span class="lang-en">{esc(en_b)}</span><span class="lang-zh">{esc(zh_b)}</span></a>
  <span class="crumb-sep">/</span>
  <a href="/?platform={e["platform"]}#dictionary">{plat_label}</a>
  <span class="crumb-sep">/</span>
  <span class="crumb-cur"><span class="lang-en">{esc(e["name"])}</span><span class="lang-zh">{esc(z["name_zh"])}</span></span>
 </nav>
 <header class="entry-head">
  <h1 class="entry-title">
   <span class="lang-en">{esc(e["name"])} {new}</span>
   <span class="lang-zh entry-title-zh">{esc(z["name_zh"])}</span>
   <span class="tag tag-platform">{esc(e["platform"])}</span>
  </h1>
  {bi(e["tagline"], z["tagline_zh"], "p", "entry-tag")}
  <dl class="entry-meta">
   <div class="meta-row"><dt><span class="lang-en">{esc(en_ac)}</span><span class="lang-zh dt-zh">{esc(zh_ac)}</span></dt>
    <dd><span class="lang-en">{esc(aka_en)}</span><span class="lang-zh zh-line">{esc(aka_zh)}</span></dd></div>
   <div class="meta-row"><dt><span class="lang-en">{esc(en_fy)}</span><span class="lang-zh dt-zh">{esc(zh_fy)}</span></dt>
   <dd><ul class="fuzzy-list">{fuzzy_rows}</ul></dd></div>
  </dl>
  <div class="entry-actions">{select_button("entry:" + e["slug"])}</div>
 </header>
 {stage(e["slug"], detail=True)}
 <p class="stage-hint lang-zh">标本可交互，可以直接操作。</p>
 {anatomy}
 <section class="sect">
  <h2 class="section-title"><span class="lang-en">{esc(en_p)}</span><span class="lang-zh">{esc(zh_p)}</span></h2>
  {copy_block(e["prompt"], z["prompt_zh"], "prompt-main")}
 </section>
 <section class="sect">
  <h2 class="section-title"><span class="lang-en">{esc(en_d)}</span><span class="lang-zh">{esc(zh_d)}</span></h2>
  {copy_block(e["debugPrompt"], z["debugPrompt_zh"], "prompt-debug")}
 </section>
 <section class="sect">
  <h2 class="section-title"><span class="lang-en">{esc(en_ic)}</span><span class="lang-zh">{esc(zh_ic)}</span></h2>
  {api_table(e, z)}
 </section>
 {see_also}
 <section class="sect">
  <button type="button" class="btn btn-ghost" id="copy-md" data-done-en="{esc(en_cd)}" data-done-zh="{esc(zh_cd)}">⧉ <span class="lang-en">{esc(en_cp)}</span><span class="lang-zh">{esc(zh_cp)}</span></button>
  <template id="md-source">{esc(md)}</template>
 </section>
</main>
{footer()}'''
    en_b, zh_b = t("indexCrumb")
    path = f'{e["platform"]}/{e["slug"]}/'
    ld = ld_graph(
        ld_defined_term(f'{e["name"]} · {z["name_zh"]}', e["tagline"], "/" + path),
        ld_breadcrumb([(f"{en_b} · {zh_b}", "/"), (e["name"], "/" + path)]))
    return page(e["name"], z["name_zh"], e["tagline"], z["tagline_zh"], body, path,
                og_image=f'/assets/og/{e["slug"]}.png', jsonld=ld)

def entry_markdown(e, z):
    lines = [f"# {e['name']} · {z['name_zh']}", "",
        f"UI reference — {SITE_URL}/{e['platform']}/{e['slug']}/", "",
        f"**{e['tagline']}**", z["tagline_zh"], "",
        f"**Also called / 也叫:** {', '.join(e['aka'])} / {'、'.join(z['aka_zh'])}", ""]
    if e.get("parts"):
        lines += ["## Anatomy — every part, named / 解剖", ""]
        for i, p in enumerate(e["parts"]):
            pz = z["parts_zh"].get(p["id"], {})
            lines += [f"{i+1}. **{p['name']} · {pz.get('name_zh','')}** (`{p['api']}`)",
                      f"   {p['description']}", f"   {pz.get('description_zh','')}",
                      f"   Prompt fragment: {p['prompt']}", ""]
    lines += ["## Prompt / 提示词", "", e["prompt"], "", z["prompt_zh"], "",
              "## Debug prompt / 调试提示词", "", e["debugPrompt"], "", z["debugPrompt_zh"], "",
              "## In code / 代码里叫什么", ""]
    for i, a in enumerate(e["api"]):
        note = a.get("note", "")
        nz = z["api_notes_zh"][i] or "" if i < len(z["api_notes_zh"]) else ""
        line = f"- **{a['framework']}** `{a['symbol']}`"
        if note:
            line += f" — {note} / {nz}"
        lines.append(line)
    return "\n".join(lines)

def guide_page(slug):
    g = GUIDES[slug]
    gz = GUIDES_ZH[slug]
    en_b, zh_b = t("indexCrumb"); en_g, zh_g = t("guideCrumb")
    inner = []
    if slug == "appkit-vs-swiftui":
        eq = g["equation"]
        inner.append(f'''<div class="equation">
 <span class="eq-side"><code>{esc(eq["left"])}</code><span class="eq-tag">{esc(eq["leftTag"])}</span></span>
 <span class="eq-op">=</span>
 <span class="eq-side"><code>{esc(eq["right"])}</code><span class="eq-tag">{esc(eq["rightTag"])}</span></span>
</div>''')
    for i, para in enumerate(g["intro"]):
        inner.append(bi(para, gz["intro_zh"][i], "p", "guide-para"))
    if "rules" in g:
        rows = "".join(f'''<li class="rule"><span class="rule-num">{i+1}</span>
 <div>{bi(r["title"], gz["rules_zh"][i]["title_zh"], "p", "rule-title")}{bi(r["body"], gz["rules_zh"][i]["body_zh"], "p", "rule-body")}</div>
</li>''' for i, r in enumerate(g["rules"]))
        inner.append(f'''<section class="sect"><h2 class="section-title"><span class="lang-en">{esc(g["rulesTitle"])}</span><span class="lang-zh">{esc(gz["rulesTitle_zh"])}</span></h2>
<ol class="rules">{rows}</ol></section>''')
    if "table" in g:
        rows = "".join(f'''<tr><td class="fw"><span class="lang-en">{esc(r["aspect"])}</span><span class="lang-zh zh-line">{esc(gz["table_zh"][i]["aspect_zh"])}</span></td>
<td><span class="lang-en">{esc(r["swift"])}</span><span class="lang-zh zh-line">{esc(gz["table_zh"][i]["swift_zh"])}</span></td>
<td><span class="lang-en">{esc(r["electron"])}</span><span class="lang-zh zh-line">{esc(gz["table_zh"][i]["electron_zh"])}</span></td></tr>''' for i, r in enumerate(g["table"]))
        inner.append(f'''<section class="sect"><h2 class="section-title"><span class="lang-en">{esc(g["tableTitle"])}</span><span class="lang-zh">{esc(gz["tableTitle_zh"])}</span></h2>
<table class="api-table vs-table"><thead><tr><th></th><th>Swift (native)</th><th>Electron (web shell)</th></tr></thead><tbody>{rows}</tbody></table></section>''')
    if "rule" in g:
        inner.append(f'''<section class="sect"><h2 class="section-title"><span class="lang-en">{esc(g["ruleTitle"])}</span><span class="lang-zh">{esc(gz["ruleTitle_zh"])}</span></h2>
{bi(g["rule"], gz["rule_zh"], "p", "guide-para")}</section>''')
    if "promptsIntro" in g:
        inner.append(bi(g["promptsIntro"], gz["promptsIntro_zh"], "p", "guide-para"))
    prompts = []
    for i, p in enumerate(g["prompts"]):
        pz = gz["prompts_zh"][i]
        note = f'<span class="prompt-note">· {esc(p.get("note",""))}<span class="lang-zh"> · {esc(pz.get("note_zh",""))}</span></span>' if p.get("note") else ""
        prompts.append(f'''<div class="guide-prompt">
 <p class="prompt-label"><span class="lang-en">{esc(p["label"])}</span><span class="lang-zh">{esc(pz["label_zh"])}</span>{note}</p>
 {copy_block(p["text"], pz["text_zh"], f"g-{slug}-{i}")}
</div>''')
    inner.append(f'''<section class="sect"><h2 class="section-title"><span class="lang-en">{esc(g["promptsTitle"])}</span><span class="lang-zh">{esc(gz["promptsTitle_zh"])}</span></h2>
{"".join(prompts)}</section>''')
    conf = "".join(f'''<li class="confuse"><span class="confuse-term"><span class="lang-en">{esc(c["term"])}</span><span class="lang-zh zh-line">{esc(gz["confuse_zh"][i]["term_zh"])}</span></span>
{bi(c["body"], gz["confuse_zh"][i]["body_zh"], "p", "confuse-body")}</li>''' for i, c in enumerate(g["confuse"]))
    inner.append(f'''<section class="sect"><h2 class="section-title"><span class="lang-en">{esc(g["confuseTitle"])}</span><span class="lang-zh">{esc(gz["confuseTitle_zh"])}</span></h2>
<ul class="confuse-list">{conf}</ul></section>''')
    if "faq" in g:
        faq = "".join(f'''<details class="faq">
 <summary><span class="lang-en">{esc(q["q"])}</span><span class="lang-zh zh-line">{esc(gz["faq_zh"][i]["q_zh"])}</span></summary>
 {bi(q["a"], gz["faq_zh"][i]["a_zh"], "p", "faq-a")}
</details>''' for i, q in enumerate(g["faq"]))
        inner.append(f'''<section class="sect"><h2 class="section-title"><span class="lang-en">{esc(g["faqTitle"])}</span><span class="lang-zh">{esc(gz["faqTitle_zh"])}</span></h2>
{faq}</section>''')
    inner.append(bi(g["outro"], gz["outro_zh"], "p", "guide-outro"))
    body = f'''{header()}
<main class="wrap entry guide">
 <nav class="crumbs">
  <a href="/"><span class="lang-en">{esc(en_b)}</span><span class="lang-zh">{esc(zh_b)}</span></a>
  <span class="crumb-sep">/</span>
  <span><span class="lang-en">{esc(en_g)}</span><span class="lang-zh">{esc(zh_g)}</span></span>
  <span class="crumb-sep">/</span>
  <span class="crumb-cur"><span class="lang-en">{esc(g["title"])}</span><span class="lang-zh">{esc(gz["title_zh"])}</span></span>
 </nav>
 <header class="entry-head">
  <h1 class="entry-title"><span class="lang-en">{esc(g["title"])}</span><span class="lang-zh entry-title-zh">{esc(gz["title_zh"])}</span></h1>
  <p class="guide-sub mono-sm">/ {esc(g["subtitle"])} /</p>
  {bi(g["lede"], gz["lede_zh"], "p", "entry-tag")}
 </header>
 {"".join(inner)}
</main>
{footer()}'''
    return page(g["title"], gz["title_zh"], g["lede"], gz["lede_zh"], body, f"guides/{slug}/")

def sources_page():
    body = f'''{header()}
<main class="wrap entry sources-page">
 <nav class="crumbs"><a href="/">首页</a><span class="crumb-sep">/</span><span class="crumb-cur">来源与许可证</span></nav>
 <header class="entry-head"><h1 class="reference-title">来源与许可证 <span>Sources &amp; License</span></h1><p class="entry-tag">原始内容与新增内容分开管理，便于识别来源和同步上游。</p></header>
 <section class="sect"><h2>上游内容</h2><p>UI 词典、指南和部分视觉风格来自 <a href="https://github.com/joeseesun/learnui" rel="noopener">joeseesun/learnui</a>。其英文源内容复刻自 <a href="https://namethatui.com/" rel="noopener">namethatui.com</a>，版权归原作者。</p></section>
 <section class="sect"><h2>已移除的栏目</h2><p>「页面参考」和「术语对照」已于 2026-11-18 移除（用户拍板）：前者是虚构模板页，与全站「看真实作品学设计」的定位不符；后者是上游遗留的 Mac 开发者 API 对照表，与本站无关。历史数据保留在 git 历史中。</p></section>
 <section class="sect"><h2>知名网站图鉴</h2><p><code>/sites/</code> 镜像自原 LearnUI 线上页面。条目中的 DESIGN.md 来自 <a href="https://github.com/VoltAgent/awesome-design-md" rel="noopener">VoltAgent/awesome-design-md</a>（MIT License），中文解读与品牌 mock 保留原页面来源说明。</p></section>
 <section class="sect"><h2>Logo 图鉴</h2><p><code>/logos/</code> 样本取自小红书视频介绍的网站：第 1 期《好用的设计网站之LOGO/图标》（李李说设计（大学陪跑）），第 2 期《2026 年的图标库，根本不是人用的》（默默然）。logo 图片取自各网站公开发布的图标文件，商标归各自所有者，仅用于识别与学习；每个详情页标明原始文件地址。</p></section>
 <section class="sect"><h2>平面设计</h2><p><code>/graphics/</code> 的案例收录自小红书笔记。详情页的原作图片截取自收录笔记中的原作画面，注明原作设计方、年份和图源；代码标本是对原作版式、字体和配色的学习性还原。原作版权归原权利人，本站不盈利、仅用于学习交流；权利人如要求删除，请通过 GitHub 仓库联系，我们会立即删除。</p></section>
 <section class="sect"><h2>许可证</h2><p>代码与本地新增示例按仓库中的 <a href="/LICENSE.txt">MIT License</a> 使用。原始内容的版权边界以 README 和上游说明为准。</p></section>
</main>
{footer()}'''
    return page("Sources and license", "来源与许可证", "Content sources and licenses.",
                "项目内容来源、上游关系和许可证说明。", body, "sources/")

def vendor_site_fragment(name):
    path = os.path.join(ROOT, "vendor", "sites", name)
    if not os.path.isfile(path):
        return '<main class="wrap"><p class="no-result">Site mirror is missing. Run scripts/sync-sites.py.</p></main>'
    with open(path, encoding="utf-8") as f:
        return f.read()

def site_vibes(site):
    hay = " ".join([site["summaryEn"], site["summaryZh"]]).lower()
    return [vibe_id for vibe_id, _, _, keywords in SITE_VIBE_RULES
            if any(keyword.lower() in hay for keyword in keywords)]

def site_hub_card(site):
    category = site["category"]
    category_zh = SITE_CATEGORY_ZH.get(category, category)
    vibes = site_vibes(site)
    hay = " ".join([
        site["nameEn"], site["nameZh"], site["summaryEn"], site["summaryZh"],
        category, category_zh,
    ]).lower()
    return f'''<article class="catalog-item site-reference-item" data-search="{esc(hay)}" data-cat="{esc(category)}" data-vibes="{esc(" ".join(vibes))}">
 <a class="style-card sites-card" href="/sites/{esc(site["slug"])}/">
  <div class="stage stage-card pe-none stage-lazy" data-slug="site-{esc(site["slug"])}"><div class="stage-center"><img class="stage-fallback" src="/assets/site-thumbs/site-{esc(site["slug"])}.webp" alt="" loading="lazy" decoding="async"></div></div>
  <div class="card-meta">
   <h3 class="card-name"><span class="lang-en">{esc(site["nameEn"])}</span><span class="lang-zh card-name-zh">{esc(site["nameZh"])}</span><span class="tag tag-platform">{esc(category)}</span></h3>
   {bi(site["summaryEn"], site["summaryZh"], "p", "card-tag")}
  </div>
 </a>
 {select_button("site:" + site["slug"], compact=True)}
</article>'''

def sites_hub_page():
    categories = []
    for site in SITES:
        if site["category"] not in categories:
            categories.append(site["category"])
    category_options = ['''<option value="">全部行业</option>'''] + [
        f'''<option value="{esc(category)}">{esc(SITE_CATEGORY_ZH.get(category, category))}</option>'''
        for category in categories
    ]
    vibe_options = ['''<option value="">全部设计气质</option>''']
    for vibe_id, _, label_zh, _ in SITE_VIBE_RULES:
        count = sum(1 for site in SITES if vibe_id in site_vibes(site))
        vibe_options.append(f'''<option value="{esc(vibe_id)}">{esc(label_zh)}（{count}）</option>''')
    cards = "\n".join(site_hub_card(site) for site in SITES)
    body = f'''{header()}
<main class="wrap sites-hub-page">
 <nav class="crumbs"><a href="/"><span class="lang-en">Index</span><span class="lang-zh">首页</span></a><span class="crumb-sep">/</span><span class="crumb-cur"><span class="lang-en">Sites</span><span class="lang-zh">知名网站</span></span></nav>
 <section class="hero sites-hero">
  <h1 class="hero-title"><span class="lang-en">Design systems of famous websites</span><span class="lang-zh hero-title-zh">知名网站设计规范</span></h1>
  <p class="lang-en hero-sub">Carry the known, open the new view.</p>
  <p class="lang-zh hero-sub">承旧识，开新观</p>
  <div class="site-tools">
   <div class="site-filter-row">
    <div class="search-box site-search-box"><input id="site-search" type="search" autocomplete="off" data-ph-en="Search a brand or visual trait" data-ph-zh="搜索品牌或视觉特征" placeholder="搜索品牌或视觉特征" aria-label="搜索知名网站设计规范"><kbd class="search-kbd">/</kbd></div>
    <label class="site-filter-select"><span>行业</span><select id="site-category" aria-label="按行业筛选">{"".join(category_options)}</select></label>
    <label class="site-filter-select"><span>设计气质</span><select id="site-vibe" aria-label="按设计气质筛选">{"".join(vibe_options)}</select></label>
   </div>
   <div class="site-filter-meta">
    <p class="site-result-count" id="site-count" role="status" aria-live="polite" aria-atomic="true"><span class="lang-en" data-tpl="Showing {{shown}} of {{total}} results">Showing 12 of {len(SITES)} results</span><span class="lang-zh" data-tpl="显示 {{shown}} / {{total}} 个结果">显示 12 / {len(SITES)} 个结果</span></p>
    <button type="button" class="site-reset" id="site-reset" hidden><span class="lang-en">Reset filters</span><span class="lang-zh">重置筛选</span></button>
   </div>
  </div>
 </section>
 <section class="style-grid sites-grid" id="sites" aria-live="polite">{cards}</section>
 <div class="site-more-row" id="site-more-row"><button type="button" class="btn site-more" id="site-more"><span class="lang-en">Load more</span><span class="lang-zh">加载更多</span><b id="site-more-count"></b></button><p class="site-auto-note" id="site-auto-note" role="status" aria-live="polite"><span class="lang-zh">向下滚动，自动加载更多</span><span class="lang-en">Scroll to load more automatically</span></p></div>
 <div class="no-result" id="site-no-result" hidden><b>没有符合条件的网站</b><p>换一个品牌、行业或设计气质。</p></div>
</main>
{footer()}'''
    return page("Design systems of famous websites", "知名网站设计规范",
                "Browse design systems extracted from famous websites.",
                "浏览 74 个知名网站的设计系统、视觉解读和 DESIGN.md。",
                body, "sites/", og_image="/assets/og/site-claude.png")

def site_detail_page(site):
    detail = vendor_site_fragment(site["slug"] + ".html")
    detail = detail.replace('</header>', f'''<div class="entry-actions site-reference-actions">{select_button("site:" + site["slug"])}</div></header>''', 1)
    detail = detail.replace('<div class="brand-mock-frame">', '<p class="brand-preview-note"><span class="lang-zh">品牌风格复现 · 以下文案与数据为演示内容，非官网截图或品牌事实。样例按钮用于展示外观。</span><span class="lang-en">Brand-style reconstruction. Sample copy and metrics are illustrative, not an official website capture or brand claims. Buttons demonstrate appearance.</span></p><div class="brand-mock-frame">', 1)
    body = f'''{header()}
{detail}
{footer()}'''
    return page(site["nameEn"], site["nameZh"], site["summaryEn"], site["summaryZh"],
                body, f'sites/{site["slug"]}/', og_image=f'/assets/og/site-{site["slug"]}.png')

# ---------------- logo atlas ----------------
def logo_url(logo):
    return f'/logos/{logo["slug"]}/'

def logo_name_zh(logo):
    return logo.get("nameZh") or logo["name"]

def logo_type_tag(type_id):
    t_ = LOGO_TYPES[type_id]
    return f'<span class="tag logo-type-tag"><span class="lang-zh">{esc(t_["nameZh"])}</span><span class="lang-en">{esc(t_["name"])}</span></span>'

def logo_use_tag(use_id):
    u = LOGO_USES[use_id]
    return f'<span class="tag"><span class="lang-zh">{esc(u["nameZh"])}</span><span class="lang-en">{esc(u["name"])}</span></span>'

def logo_image(logo, cls="logo-art", lazy=True):
    loading = ' loading="lazy" decoding="async"' if lazy else ''
    return f'<img class="{cls}" src="/assets/logos/{esc(logo["image"])}.webp" alt="{esc(logo["name"])} logo"{loading}>'

def logo_card(logo):
    t_ = LOGO_TYPES[logo["type"]]; u = LOGO_USES[logo["use"]]
    hay = " ".join([logo["name"], logo_name_zh(logo), logo["maker"], logo["makerZh"], t_["name"], t_["nameZh"],
                    u["name"], u["nameZh"], logo["aboutZh"], logo["about"]]).lower()
    return f'''<article class="catalog-item logo-item" data-search="{esc(hay)}" data-type="{esc(logo["type"])}" data-use="{esc(logo["use"])}">
 <a class="style-card logo-card" href="{logo_url(logo)}">
  <div class="stage stage-card logo-stage">{logo_image(logo)}</div>
  <div class="card-meta">
   <h3 class="card-name"><span class="lang-en">{esc(logo["name"])}</span><span class="lang-zh card-name-zh">{esc(logo_name_zh(logo))}</span></h3>
   <div class="logo-card-tags">{logo_type_tag(logo["type"])}{logo_use_tag(logo["use"])}</div>
   {bi(logo["about"], logo["aboutZh"], "p", "card-tag")}
  </div>
 </a>
 {select_button("logo:" + logo["slug"], compact=True)}
</article>'''

def logos_hub_page():
    counts = {tid: sum(1 for l in LOGOS if l["type"] == tid) for tid in LOGO_TYPES}
    type_chips = ['<button type="button" class="logo-type-chip" data-logo-type="" aria-pressed="true"><span class="lang-zh">全部类型</span><span class="lang-en">All types</span><b>' + str(len(LOGOS)) + '</b></button>']
    for tid, t_ in LOGO_TYPES.items():
        disabled = ' disabled' if not counts[tid] else ''
        type_chips.append(f'<button type="button" class="logo-type-chip" data-logo-type="{esc(tid)}" aria-pressed="false"{disabled} title="{esc(t_["definitionZh"])}"><span class="lang-zh">{esc(t_["nameZh"])}</span><span class="lang-en">{esc(t_["name"])}</span><b>{counts[tid]}</b></button>')
    empty_note = '<em><span class="lang-zh">暂无样本</span><span class="lang-en">No sample yet</span></em>'
    glossary = "".join(f'<div class="logo-glossary-item"><dt><span class="lang-zh">{esc(t_["nameZh"])} <small>{esc(t_["name"])}</small></span><span class="lang-en">{esc(t_["name"])}</span></dt><dd><span class="lang-zh">{esc(t_["definitionZh"])}</span><span class="lang-en">{esc(t_["definition"])}</span>{"" if counts[tid] else empty_note}</dd></div>' for tid, t_ in LOGO_TYPES.items())
    use_options = ['<option value="">全部用途</option>'] + [f'<option value="{esc(uid)}">{esc(u["nameZh"])}</option>' for uid, u in LOGO_USES.items()]
    cards = "\n".join(logo_card(l) for l in LOGOS)
    body = f'''{header()}
<main class="wrap logos-hub-page">
 <nav class="crumbs"><a href="/"><span class="lang-en">Index</span><span class="lang-zh">首页</span></a><span class="crumb-sep">/</span><span class="crumb-cur"><span class="lang-en">Logo atlas</span><span class="lang-zh">Logo 图鉴</span></span></nav>
 <section class="hero logos-hero">
  <h1 class="hero-title"><span class="lang-en">Logo atlas</span><span class="lang-zh hero-title-zh">Logo 图鉴</span></h1>
  <p class="lang-zh hero-sub">览徽标万象，撷形意之美</p>
  <p class="lang-en hero-sub">Survey a world of marks; gather the beauty of form and meaning.</p>
  <div class="logo-tools">
   <div class="logo-type-chips" role="group" aria-label="按 logo 类型筛选">{"".join(type_chips)}</div>
   <div class="site-filter-row">
    <div class="search-box site-search-box"><input id="logo-search" type="search" autocomplete="off" data-ph-en="Search a site, type or use" data-ph-zh="搜索网站、类型或用途" placeholder="搜索网站、类型或用途" aria-label="搜索 logo 图鉴"><kbd class="search-kbd">/</kbd></div>
    <label class="site-filter-select"><span>用途</span><select id="logo-use" aria-label="按用途筛选">{"".join(use_options)}</select></label>
    <button type="button" class="site-reset" id="logo-reset" hidden><span class="lang-en">Reset filters</span><span class="lang-zh">重置筛选</span></button>
   </div>
   <p class="site-result-count" id="logo-count" role="status" aria-live="polite" aria-atomic="true"><span class="lang-en" data-tpl="Showing {{shown}} of {{total}}">Showing {len(LOGOS)} of {len(LOGOS)}</span><span class="lang-zh" data-tpl="显示 {{shown}} / {{total}} 个">显示 {len(LOGOS)} / {len(LOGOS)} 个</span></p>
  </div>
 </section>
 <section class="style-grid logos-grid" id="logos" aria-live="polite">{cards}</section>
 <div class="no-result" id="logo-no-result" hidden><b>没有符合条件的 logo</b><p>换一个类型、用途或关键词。</p></div>
 <section class="sect logo-glossary-sect">
  <h2 class="section-title"><span class="lang-zh">7 种 logo 类型</span><span class="lang-en">Seven kinds of logo</span></h2>
  <dl class="logo-glossary">{glossary}</dl>
  <p class="logo-legal"><span class="lang-zh">logo 均为各自所有者的商标，取自各网站公开发布的图标文件，仅用于识别与学习。</span><span class="lang-en">All logos are trademarks of their owners, taken from each site's published icon files, and shown for identification and study only.</span></p>
 </section>
</main>
{footer()}'''
    return page("Logo atlas", "Logo 图鉴",
                "Learn logo types through real marks, with the design sites they come from.",
                f"通过 {len(LOGOS)} 个真实 logo 认识 logo 类型与构成，并收录好用的 logo / 图标网站。",
                body, "logos/")

def logo_markdown(logo):
    t_ = LOGO_TYPES[logo["type"]]
    lines = [f'# {logo_name_zh(logo)}', '', f'- 类型：{t_["nameZh"]}（{t_["name"]}）— {t_["definitionZh"]}',
             f'- 网站：{logo["url"]}', f'- 用途：{LOGO_USES[logo["use"]]["nameZh"]}；{logo["aboutZh"]}',
             f'- 适合：{logo["audienceZh"]}', f'- 授权：{logo["licenseZh"]}', '', '## 构成', '', logo["readZh"], '']
    lines += [f'- {p_["nameZh"]}：{p_["descZh"]}' for p_ in logo["parts"]]
    lines += ['', '## 给 AI 的 prompt', '', logo["promptZh"], '']
    if logo.get("noteZh"):
        lines += ['## 说明', '', logo["noteZh"], '']
    return "\n".join(lines)

def logo_page(logo):
    t_ = LOGO_TYPES[logo["type"]]
    parts = "".join(f'<div class="logo-part"><h3><span class="lang-zh">{esc(p_["nameZh"])}</span><span class="lang-en">{esc(p_["name"])}</span></h3><p><span class="lang-zh">{esc(p_["descZh"])}</span><span class="lang-en">{esc(p_["desc"])}</span></p></div>' for p_ in logo["parts"])
    sizes = "".join(f'<figure><div class="logo-size-box" style="--logo-size:{n}px">{logo_image(logo, "logo-size-img", lazy=False)}</div><figcaption>{n}px</figcaption></figure>' for n in (16, 32, 64))
    same = [l for l in LOGOS if l["type"] == logo["type"] and l["slug"] != logo["slug"]]
    others = same + [l for l in LOGOS if l["use"] == logo["use"] and l["slug"] != logo["slug"] and l not in same]
    related = "".join(f'<a class="rel-card logo-rel" href="{logo_url(l)}">{logo_image(l, "logo-rel-img")}<span class="rel-name"><span class="lang-en">{esc(l["name"])}</span><span class="lang-zh rel-name-zh">{esc(logo_name_zh(l))}</span></span><span class="rel-sym"><span class="lang-zh">{esc(LOGO_TYPES[l["type"]]["nameZh"])}</span><span class="lang-en">{esc(LOGO_TYPES[l["type"]]["name"])}</span></span></a>' for l in others[:4])
    related_sect = (f'<section class="sect"><h2 class="section-title"><span class="lang-zh">同类与同用途</span><span class="lang-en">Related</span></h2><div class="rel-grid">{related}</div></section>' if related else '')
    note = (f'<p class="logo-note"><span class="lang-zh">{esc(logo["noteZh"])}</span><span class="lang-en">{esc(logo["note"])}</span></p>' if logo.get("note") else "")
    body = f'''{header()}
<main class="wrap entry logo-detail">
 <nav class="crumbs"><a href="/logos/"><span class="lang-zh">Logo 图鉴</span><span class="lang-en">Logo atlas</span></a><span class="crumb-sep">/</span><span class="crumb-cur"><span class="lang-zh">{esc(logo_name_zh(logo))}</span><span class="lang-en">{esc(logo["name"])}</span></span></nav>
 <header class="entry-head">
  <h1 class="logo-title"><span class="lang-zh">{esc(logo_name_zh(logo))}</span><span class="lang-en">{esc(logo["name"])}</span></h1>
  <p class="entry-tag"><span class="lang-zh">{esc(logo["aboutZh"])}</span><span class="lang-en">{esc(logo["about"])}</span></p>
  <div class="logo-card-tags">{logo_type_tag(logo["type"])}{logo_use_tag(logo["use"])}</div>
  <div class="entry-actions">{select_button("logo:" + logo["slug"])}<a class="btn" href="{esc(logo["url"])}" rel="noopener" target="_blank"><span class="lang-zh">访问网站</span><span class="lang-en">Visit site</span>{icon("external", 15)}</a></div>
 </header>
 <div class="logo-showcase">
  <div class="logo-plate logo-plate-light">{logo_image(logo, "logo-art", lazy=False)}</div>
  <div class="logo-plate logo-plate-dark">{logo_image(logo, "logo-art", lazy=False)}</div>
 </div>
 <div class="logo-sizes"><span class="logo-sizes-label"><span class="lang-zh">小尺寸测试</span><span class="lang-en">Small sizes</span></span>{sizes}</div>
 {note}
 <section class="sect">
  <h2 class="section-title"><span class="lang-zh">它是哪种 logo</span><span class="lang-en">What kind of logo</span></h2>
  <p class="logo-type-line"><b><span class="lang-zh">{esc(t_["nameZh"])}</span><span class="lang-en">{esc(t_["name"])}</span></b><span class="lang-zh">{esc(t_["definitionZh"])}</span><span class="lang-en">{esc(t_["definition"])}</span></p>
  <p class="logo-read"><span class="lang-zh">{esc(logo["readZh"])}</span><span class="lang-en">{esc(logo["read"])}</span></p>
 </section>
 <section class="sect">
  <h2 class="section-title"><span class="lang-zh">拆解</span><span class="lang-en">Anatomy</span></h2>
  <div class="logo-parts">{parts}</div>
 </section>
 <section class="sect">
  <h2 class="section-title"><span class="lang-zh">网站档案</span><span class="lang-en">About the site</span></h2>
  <dl class="logo-facts">
   <div><dt><span class="lang-zh">网址</span><span class="lang-en">URL</span></dt><dd><a href="{esc(logo["url"])}" rel="noopener" target="_blank">{esc(logo["url"])}</a></dd></div>
   <div><dt><span class="lang-zh">出品</span><span class="lang-en">Made by</span></dt><dd><span class="lang-zh">{esc(logo["makerZh"])}</span><span class="lang-en">{esc(logo["maker"])}</span></dd></div>
   <div><dt><span class="lang-zh">适合谁</span><span class="lang-en">Good for</span></dt><dd><span class="lang-zh">{esc(logo["audienceZh"])}</span><span class="lang-en">{esc(logo["audience"])}</span></dd></div>
   <div><dt><span class="lang-zh">费用与授权</span><span class="lang-en">Cost &amp; license</span></dt><dd><span class="lang-zh">{esc(logo["licenseZh"])}</span><span class="lang-en">{esc(logo["license"])}</span></dd></div>
  </dl>
 </section>
 <section class="sect">
  <h2 class="section-title"><span class="lang-zh">给 AI 的 prompt</span><span class="lang-en">Prompt for your AI</span></h2>
  {copy_block(logo["prompt"], logo["promptZh"], "logo-prompt")}
 </section>
 {related_sect}
 <section class="sect reference-detail-actions">
  <button type="button" class="btn" id="copy-md" data-done-zh="已复制">复制本页 Markdown</button>
  <template id="md-source">{esc(logo_markdown(logo))}</template>
  <span><span class="lang-zh">logo 为 {esc(logo["makerZh"])} 的商标，取自<a href="{esc(logo["imageSource"])}" rel="noopener">官方图标文件</a>，仅用于识别与学习。</span><span class="lang-en">The logo is a trademark of {esc(logo["maker"])}, taken from its <a href="{esc(logo["imageSource"])}" rel="noopener">published icon file</a>, for identification and study only.</span></span>
 </section>
</main>
{footer()}'''
    return page(logo["name"], logo_name_zh(logo), logo["about"], logo["aboutZh"], body, logo_url(logo).lstrip("/"))

# ---------------- graphic design ----------------
def graphic_url(case):
    return f'/graphics/{case["slug"]}/'

def graphic_title_zh(case):
    return f'{case.get("gameZh") or case["game"]} · {case["project"]}'

def graphic_title_en(case):
    return f'{case["game"]} · {case["project"]}'

def graphic_srcset(im, enough=None):
    """Original-size file for 1x screens; the 2x file (AI-upscaled or official) for high-density screens.
    `enough`: if the 1x file is already this wide (e.g. a cover card), skip the 2x file altogether."""
    hd = im.get("hd")
    if not hd or (enough and im["w"] >= enough):
        return ""
    return f' srcset="/assets/graphics/{esc(im["file"])} 1x, /assets/graphics/{esc(hd)} 2x"'

def graphic_year(case, sep=" · "):
    return f'{sep}{case["year"]}' if case.get("year") else ""

def graphic_tech_tags(case):
    # Detail page only: plain spans with a hover definition (the hub no longer has a technique filter or glossary).
    out = []
    for tid in case["techniques"]:
        t_ = GRAPHIC_TECHS[tid]
        inner = f'<span class="lang-zh">{esc(t_["nameZh"])}</span><span class="lang-en">{esc(t_["name"])}</span>'
        out.append(f'<span class="tag gd-tech" title="{esc(t_["definitionZh"])}\n\n{esc(t_["definition"])}">{inner}</span>')
    return "".join(out)

def graphic_style_tags(case):
    return "".join(f'<span class="tag gd-style"><span class="lang-zh">{esc(GRAPHIC_STYLES[s]["nameZh"])}</span><span class="lang-en">{esc(GRAPHIC_STYLES[s]["name"])}</span></span>' for s in case["styleTags"])

COVER_1X, COVER_2X = 450, 1000  # cover thumbnail widths; mirrored in scripts/graphics/make_covers.py

def graphic_cover(case):
    """List-page cover. A card renders at most ~440 CSS px wide, so ship a thumbnail sized to that
    (and twice it for dense screens) instead of the full original; the picture is identical, the
    bytes are a fraction. Detail-page images and click-to-enlarge files keep their full size."""
    im = case["images"][0]
    w, h = im["w"], im["h"]
    shown_w = w if w <= COVER_1X else COVER_1X
    shown_h = h if w <= COVER_1X else round(h * COVER_1X / w)
    base = f'/assets/graphics/{esc(case["slug"])}-cover'
    return (f'<div class="gd-cover" style="aspect-ratio:{w}/{h}">'
            f'<img src="{base}.webp" srcset="{base}.webp 1x, {base}@2x.webp 2x" '
            f'width="{shown_w}" height="{shown_h}" alt="" loading="lazy" decoding="async"></div>')

def graphic_card(case):
    ty = GRAPHIC_TYPES[case["type"]]
    hay = " ".join([case["game"], case.get("gameZh", ""), case["project"], case["credits"], ty["name"], ty["nameZh"], case["summary"], case["summaryZh"]]
                   + [GRAPHIC_STYLES[s]["name"] + " " + GRAPHIC_STYLES[s]["nameZh"] for s in case["styleTags"]]).lower()
    return f'''<article class="catalog-item graphic-item" data-search="{esc(hay)}" data-type="{esc(case["type"])}" data-styles="{esc(" ".join(case["styleTags"]))}">
 <a class="style-card graphic-card" href="{graphic_url(case)}">
  {graphic_cover(case)}
  <div class="card-meta">
   <h3 class="card-name"><span class="lang-zh card-name-zh">{esc(graphic_title_zh(case))}</span><span class="lang-en">{esc(graphic_title_en(case))}</span></h3>
   <p class="gd-credit">{esc(case["credits"])}{graphic_year(case)}</p>
   <div class="gd-card-tags">{graphic_style_tags(case)}</div>
  </div>
 </a>
 {select_button("graphic:" + case["slug"], compact=True)}
</article>'''

def graphics_hub_page():
    type_counts = {tid: sum(1 for c in GRAPHICS if c["type"] == tid) for tid in GRAPHIC_TYPES}
    type_chips = ['<button type="button" class="logo-type-chip" data-gd-type="" aria-pressed="true"><span class="lang-zh">全部类型</span><span class="lang-en">All types</span><b>' + str(len(GRAPHICS)) + '</b></button>']
    for tid, ty in GRAPHIC_TYPES.items():
        dis = '' if type_counts[tid] else ' disabled'
        type_chips.append(f'<button type="button" class="logo-type-chip" data-gd-type="{esc(tid)}" aria-pressed="false"{dis}><span class="lang-zh">{esc(ty["nameZh"])}</span><span class="lang-en">{esc(ty["name"])}</span><b>{type_counts[tid]}</b></button>')
    used_styles = [sid for sid in GRAPHIC_STYLES if any(sid in c["styleTags"] for c in GRAPHICS)]
    style_options = ['<option value="">全部风格</option>'] + [f'<option value="{esc(s)}">{esc(GRAPHIC_STYLES[s]["nameZh"])}（{sum(1 for c in GRAPHICS if s in c["styleTags"])}）</option>' for s in used_styles]
    cards = "\n".join(graphic_card(c) for c in GRAPHICS)
    body = f'''{header()}
<main class="wrap graphics-hub-page">
 <nav class="crumbs"><a href="/"><span class="lang-en">Index</span><span class="lang-zh">首页</span></a><span class="crumb-sep">/</span><span class="crumb-cur"><span class="lang-en">Graphic design</span><span class="lang-zh">平面设计</span></span></nav>
 <section class="hero logos-hero">
  <h1 class="hero-title"><span class="lang-en">Graphic design</span><span class="lang-zh hero-title-zh">平面设计</span></h1>
  <p class="lang-zh hero-sub">裁纸为境，构形传意</p>
  <p class="lang-en hero-sub">Paper becomes the stage; form carries the meaning.</p>
  <div class="logo-tools">
   <div class="logo-type-chips" role="group" aria-label="按类型筛选">{"".join(type_chips)}</div>
   <div class="site-filter-row">
    <div class="search-box site-search-box"><input id="graphic-search" type="search" autocomplete="off" data-ph-en="Search a game, studio or style" data-ph-zh="搜索游戏、设计方或风格" placeholder="搜索游戏、设计方或风格" aria-label="搜索平面设计案例"><kbd class="search-kbd">/</kbd></div>
    <label class="site-filter-select"><span>风格</span><select id="graphic-style" aria-label="按风格筛选">{"".join(style_options)}</select></label>
    <button type="button" class="site-reset" id="graphic-reset" hidden><span class="lang-en">Reset filters</span><span class="lang-zh">重置筛选</span></button>
   </div>
   <p class="site-result-count" id="graphic-count" role="status" aria-live="polite" aria-atomic="true"><span class="lang-en" data-tpl="Showing {{shown}} of {{total}}">Showing {len(GRAPHICS)} of {len(GRAPHICS)}</span><span class="lang-zh" data-tpl="显示 {{shown}} / {{total}} 个">显示 {len(GRAPHICS)} / {len(GRAPHICS)} 个</span></p>
  </div>
 </section>
 <section class="style-grid graphics-grid" id="graphics" aria-live="polite">{cards}</section>
 <div class="no-result" id="graphic-no-result" hidden><b>没有符合条件的案例</b><p>换一个类型、风格或关键词。</p></div>
</main>
{footer()}'''
    return page("Graphic design", "平面设计", "Graphic design cases browsed by style, techniques taken apart in each case.",
                f"按风格浏览 {len(GRAPHICS)} 个真实平面设计案例，详情页逐层拆解版式、字体和配色手法。", body, "graphics/")

def graphic_markdown(case):
    ty = GRAPHIC_TYPES[case["type"]]
    lines = [f'# {graphic_title_zh(case)}', '', f'- 类型：{ty["nameZh"]}', f'- 设计方：{case["credits"]}{graphic_year(case, "，")}', f'- 图源：{case["sourceLabel"]}' + "".join(f" <{u}>" for u in case.get("sourceUrls", [])),
             f'- 风格：' + '、'.join(GRAPHIC_STYLES[s]["nameZh"] for s in case["styleTags"]),
             f'- 手法：' + '、'.join(GRAPHIC_TECHS[t]["nameZh"] for t in case["techniques"]), '', case["summaryZh"], '', '## 为什么好看', '', case["readZh"], '', '## 拆解', '']
    lines += [f'- {name}：{case["layers"][key + "Zh"]}' for key, name in (("grid", "网格"), ("type", "字体层级"), ("focus", "视觉焦点"), ("space", "留白"))]
    lines += ['', '## 配色', ''] + [f'- {c["nameZh"]} {c["hex"]}' for c in case["palette"]]
    lines += ['', '## 原作图片', ''] + [f'- {im["captionZh"]}：{SITE_URL}/assets/graphics/{im["file"]}' for im in case["images"]]
    lines += ['', '## 生图提示词', '', case["imagePromptZh"], '', '## 代码提示词', '', case["codePromptZh"], '']
    return "\n".join(lines)

def graphic_page(case):
    ty = GRAPHIC_TYPES[case["type"]]
    iss = GRAPHIC_ISSUES[case["issue"]]
    styles = graphic_style_tags(case)
    layer_btns = "".join(f'<button type="button" class="gd-layer-btn" data-gd-layer="{k}" aria-pressed="false"><span class="lang-zh">{zh}</span><span class="lang-en">{en}</span></button>'
                         for k, zh, en in (("grid", "网格", "Grid"), ("type", "字体层级", "Type"), ("palette", "配色", "Palette"), ("focus", "视觉焦点", "Focus"), ("space", "留白", "Space"), ("all", "全部", "All")))
    notes = "".join(f'<p class="gd-note" data-gd-note="{k}" hidden><b><span class="lang-zh">{zh}</span><span class="lang-en">{en}</span></b><span class="lang-zh">{esc(case["layers"][k + "Zh"])}</span><span class="lang-en">{esc(case["layers"][k])}</span></p>'
                    for k, zh, en in (("grid", "网格", "Grid"), ("type", "字体层级", "Type"), ("focus", "视觉焦点", "Focus"), ("space", "留白", "Space")))
    notes += '<p class="gd-note" data-gd-note="palette" hidden><b><span class="lang-zh">配色</span><span class="lang-en">Palette</span></b>' + " · ".join(f'<span class="lang-zh">{esc(c["nameZh"])}</span><span class="lang-en">{esc(c["name"])}</span> {esc(c["hex"])}' for c in case["palette"]) + '</p>'
    swatches = "".join(f'<button type="button" class="gd-swatch" data-copy-text="{esc(c["hex"])}" title="复制 {esc(c["hex"])}"><i style="background:{esc(c["hex"])}"></i><b>{esc(c["hex"])}</b><span class="lang-zh">{esc(c["nameZh"])}</span><span class="lang-en">{esc(c["name"])}</span></button>' for c in case["palette"])
    palette_json = json.dumps([{"hex": c["hex"]} for c in case["palette"]])
    # Originals keep their own aspect ratio. A portrait lead image sits beside the rest;
    # a landscape lead image spans the row and the rest line up below at equal height.
    def orig_badge(im):
        labels = {"official": ("官方原图", "Official file"), "note": ("截自收录笔记", "Cropped from the note"),
                  "enhanced": ("截自收录笔记 · AI 放大 2 倍", "From the note · 2× AI upscale"),
                  "official-enhanced": ("官方原图 · AI 放大 2 倍", "Official file · 2× AI upscale"),
                  "author": ("作者原图", "Designer's own file"), "author-enhanced": ("作者原图 · AI 放大 2 倍", "Designer's own file · 2× AI upscale")}
        zh, en = labels.get(im.get("origin", "note"), labels["note"])
        return f'<em class="gd-orig-src"><span class="lang-zh">{zh}</span><span class="lang-en">{en}</span></em>'
    def orig_figure(im, i, style=""):
        return (f'<figure class="gd-orig"{style}><a href="/assets/graphics/{esc(im.get("hd") or im["file"])}" target="_blank" rel="noopener">'
                f'<img src="/assets/graphics/{esc(im["file"])}"{graphic_srcset(im)} width="{im["w"]}" height="{im["h"]}" alt="{esc(im["captionZh"])}" loading="{"eager" if i == 0 else "lazy"}" decoding="async"></a>'
                f'<figcaption><span class="lang-zh">{esc(im["captionZh"])}</span><span class="lang-en">{esc(im["caption"])}</span>{orig_badge(im)}</figcaption></figure>')
    has_ai = any(im.get("origin", "").endswith("enhanced") for im in case["images"])
    ai_zh = "标有「AI 放大 2 倍」的图在高清屏上显示 AI 清晰度增强版（Real-ESRGAN），细节可能与原作有细微差异；" if has_ai else ""
    ai_en = "Images marked “2× AI upscale” use a Real-ESRGAN enhanced version on high-density screens; fine detail may differ slightly. " if has_ai else ""
    hosts = [urlsplit(u).netloc.removeprefix("www.") for u in case.get("sourceUrls", [])]
    source_links = "".join(f' · <a href="{esc(u)}" target="_blank" rel="noopener">{esc(h)}{f" ({hosts[:i].count(h) + 1})" if hosts.count(h) > 1 else ""}</a>'
                           for i, (u, h) in enumerate(zip(case.get("sourceUrls", []), hosts)))
    lead, rest = case["images"][0], case["images"][1:]
    if lead["h"] > lead["w"] * 1.05:
        gallery = (f'<div class="gd-orig-split"><div class="gd-orig-lead" style="--ar:{lead["w"]}/{lead["h"]}">{orig_figure(lead, 0)}</div>'
                   f'<div class="gd-orig-rest">{"".join(orig_figure(im, i + 1) for i, im in enumerate(rest))}</div></div>')
    else:
        row = "".join(orig_figure(im, i + 1, f' style="flex:{im["w"] / im["h"]:.3f} 1 0"') for i, im in enumerate(rest))
        gallery = (f'<div class="gd-orig-stack"><div class="gd-orig-lead gd-orig-wide" style="--ar:{lead["w"]}/{lead["h"]}">{orig_figure(lead, 0)}</div>'
                   f'<div class="gd-orig-row">{row}</div></div>')
    others = [c for c in GRAPHICS if c["slug"] != case["slug"] and set(c["techniques"]) & set(case["techniques"])][:4]
    related = "".join(f'<a class="rel-card" href="{graphic_url(c)}"><span class="rel-name"><span class="lang-zh rel-name-zh">{esc(graphic_title_zh(c))}</span><span class="lang-en">{esc(graphic_title_en(c))}</span></span><span class="rel-sym">{esc(" · ".join(GRAPHIC_TECHS[t]["nameZh"] for t in c["techniques"] if t in case["techniques"]))}</span></a>' for c in others)
    related_sect = f'<section class="sect"><h2 class="section-title"><span class="lang-zh">用了相同手法</span><span class="lang-en">Same techniques</span></h2><div class="rel-grid">{related}</div></section>' if related else ''
    body = f'''{header()}
<main class="wrap entry graphic-detail" data-gd-detail data-gd-palette="{esc(palette_json)}">
 <nav class="crumbs"><a href="/graphics/"><span class="lang-zh">平面设计</span><span class="lang-en">Graphic design</span></a><span class="crumb-sep">/</span><span class="crumb-cur"><span class="lang-zh">{esc(graphic_title_zh(case))}</span><span class="lang-en">{esc(graphic_title_en(case))}</span></span></nav>
 <header class="entry-head">
  <h1 class="logo-title"><span class="lang-zh">{esc(graphic_title_zh(case))}</span><span class="lang-en">{esc(graphic_title_en(case))}</span></h1>
  <p class="entry-tag"><span class="lang-zh">{esc(case["summaryZh"])}</span><span class="lang-en">{esc(case["summary"])}</span></p>
  <div class="logo-card-tags"><span class="tag logo-type-tag"><span class="lang-zh">{esc(ty["nameZh"])}</span><span class="lang-en">{esc(ty["name"])}</span></span>{graphic_tech_tags(case)}{styles}</div>
  <div class="entry-actions">{select_button("graphic:" + case["slug"])}</div>
 </header>
 <section class="gd-originals">
  <h2 class="section-title"><span class="lang-zh">原作</span><span class="lang-en">Original</span></h2>
  {gallery}
  <p class="gd-orig-credit"><span class="lang-zh">原作：{esc(case["credits"])}{graphic_year(case, "，")}。图源：{esc(case["sourceLabel"])}{source_links}。版权归原权利人，仅用于学习交流，权利人要求即删除。{ai_zh}点图片可看大图。</span><span class="lang-en">Original: {esc(case["credits"])}{graphic_year(case, ", ")}. Source: {esc(case["sourceLabel"])}{source_links}. Rights belong to the original owners; shown for study and removed on request. {ai_en}Click an image to open it full size.</span></p>
 </section>
 <section class="gd-recreate">
  <h2 class="section-title"><span class="lang-zh">代码还原与拆解</span><span class="lang-en">Coded reconstruction and breakdown</span></h2>
  <p class="gd-recreate-note"><span class="lang-zh">用代码还原原作的版式、字体和配色，再逐层打开拆解。插画、摄影和角色画面不重画，用简化的形状代替，请对照上方原图。</span><span class="lang-en">Layout, type and colour rebuilt in code so each layer can be opened. Illustration, photography and characters are simplified shapes; compare with the originals above.</span></p>
 </section>
 {stage("graphic/" + case["slug"], detail=True)}
 <div class="gd-layer-bar" role="group" aria-label="拆解图层"><span class="gd-layer-label"><span class="lang-zh">拆解</span><span class="lang-en">Break down</span></span>{layer_btns}</div>
 <div class="gd-notes">{notes}</div>
 <section class="sect">
  <h2 class="section-title"><span class="lang-zh">为什么好看</span><span class="lang-en">Why it works</span></h2>
  <p class="logo-read"><span class="lang-zh">{esc(case["readZh"])}</span><span class="lang-en">{esc(case["read"])}</span></p>
 </section>
 <section class="sect">
  <h2 class="section-title"><span class="lang-zh">配色</span><span class="lang-en">Palette</span></h2>
  <div class="gd-swatches">{swatches}</div>
 </section>
 <section class="sect">
  <h2 class="section-title"><span class="lang-zh">生图提示词</span><span class="lang-en">Image prompt</span></h2>
  {copy_block(case["imagePrompt"], case["imagePromptZh"], "gd-image-prompt")}
 </section>
 <section class="sect">
  <h2 class="section-title"><span class="lang-zh">代码提示词</span><span class="lang-en">Code prompt</span></h2>
  {copy_block(case["codePrompt"], case["codePromptZh"], "gd-code-prompt")}
 </section>
 {related_sect}
 <section class="sect reference-detail-actions">
  <button type="button" class="btn" id="copy-md" data-done-zh="已复制">复制本页 Markdown</button>
  <template id="md-source">{esc(graphic_markdown(case))}</template>
  <span><span class="lang-zh">收录自小红书「{esc(iss["author"])}」的笔记《{esc(iss["title"])}》，<a href="{esc(iss["url"])}" rel="noopener" target="_blank">查看原笔记</a>。</span><span class="lang-en">Collected from the Xiaohongshu note "{esc(iss["title"])}" by {esc(iss["author"])}; <a href="{esc(iss["url"])}" rel="noopener" target="_blank">view the note</a>.</span></span>
 </section>
</main>
{footer()}'''
    return page(graphic_title_en(case), graphic_title_zh(case), case["summary"], case["summaryZh"], body, graphic_url(case).lstrip("/"))

# ---------------- styles atlas (Name That Vibe) ----------------

def style_url(s):
    return f'/styles/{s["slug"]}/'

def style_zh(s):
    return STYLES_ZH.get(s["slug"], {})

def first_para(text):
    return (text or "").split("\n\n")[0].strip()

def style_card(s):
    z = style_zh(s)
    hay = " ".join([s.get("name") or "", z.get("name_zh") or "", s.get("tagline") or "", z.get("tagline_zh") or ""] +
                   (s.get("aliases") or []) + (z.get("aliases_zh") or [])).lower()
    new = f'<span class="tag tag-new">{esc(UI["newBadge"])}</span>' if s["slug"] in STYLE_NEW_SLUGS else ""
    return f'''<article class="catalog-item style-catalog-item" data-search="{esc(hay)}" data-slug="{s["slug"]}">
<a class="style-card" href="{style_url(s)}">
 {stage("style-" + s["slug"])}
 <div class="card-meta">
  <h3 class="card-name">
   <span class="lang-en">{esc(s["name"])}{new}</span>
   <span class="lang-zh card-name-zh">{esc(z.get("name_zh", ""))}</span>
  </h3>
  {bi(first_para(s.get("tagline", "")), first_para(z.get("tagline_zh", "")), "p", "card-tag")}
 </div>
</a>
{select_button("style:" + s["slug"], compact=True)}
</article>'''

def styles_hub_page():
    en_b, zh_b = t("indexCrumb"); en_sc, zh_sc = t("stylesCrumb")
    en_ph, zh_ph = t("searchStylesPlaceholder")
    cards = "\n".join(style_card(s) for s in STYLES)
    body = f'''{header()}
<main class="wrap">
 <nav class="crumbs">
  <a href="/"><span class="lang-en">{esc(en_b)}</span><span class="lang-zh">{esc(zh_b)}</span></a>
  <span class="crumb-sep">/</span>
  <span class="crumb-cur"><span class="lang-en">{esc(en_sc)}</span><span class="lang-zh">{esc(zh_sc)}</span></span>
 </nav>
 <section class="hero" style="padding-top:32px">
  <h1 class="hero-title"><span class="lang-en">{esc(UI["stylesTitle"])}</span><span class="lang-zh hero-title-zh">{esc(UI["stylesTitleZh"])}</span></h1>
  {paras(STYLES_META.get("hubTagline", ""), STYLES_META_ZH.get("hubTagline_zh", ""), "hero-sub")}
  <div class="controls">
   <div class="search-box">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
    <input id="style-search" type="search" autocomplete="off"
     data-ph-en="{esc(en_ph)}" data-ph-zh="{esc(zh_ph)}" placeholder="{esc(zh_ph)} / {esc(en_ph)}" aria-label="Search styles">
    <kbd class="search-kbd">/</kbd>
   </div>
  </div>
 </section>
 <section class="style-grid" id="styles" aria-live="polite">
{cards}
 </section>
 <p id="style-no-result" class="no-result" hidden><span class="lang-en">{esc(UI["searchNoResult"])}</span><span class="lang-zh">{esc(UI["searchNoResultZh"])}</span></p>
</main>
{footer()}'''
    return page(UI["stylesTitle"], UI["stylesTitleZh"], STYLES_META.get("hubTagline", "")[:150],
                STYLES_META_ZH.get("hubTagline_zh", "")[:80], body, "styles/", og_image="/assets/og/_styles.png")

def style_page(s):
    z = style_zh(s)
    en_b, zh_b = t("indexCrumb"); en_sc, zh_sc = t("stylesCrumb")
    en_fy, zh_fy = t("ifYouCalledIt")
    en_dna, zh_dna = t("dnaTitle"); en_cf, zh_cf = t("confusedTitle")
    en_ic, zh_ic = t("styleCodeTitle"); en_br, zh_br = t("briefTitle")
    en_a11y, zh_a11y = t("a11yTitle"); en_or, zh_or = t("originTitle")
    en_sa, zh_sa = t("seeAlso"); en_cp, zh_cp = t("copyPage"); en_cd, zh_cd = t("copied")

    aliases = ""
    if s.get("aliases"):
        chips = []
        for i, a in enumerate(s["aliases"]):
            az = z.get("aliases_zh", [])
            ztxt = az[i] if i < len(az) else ""
            chips.append(f'''<span class="alias-chip"><span class="lang-en">“{esc(a)}”</span><span class="lang-zh">「{esc(ztxt)}」</span></span>''')
        aliases = f'''<section class="sect">
 <h2 class="section-title"><span class="lang-en">{esc(en_fy)}</span><span class="lang-zh">{esc(zh_fy)}</span></h2>
 <div class="alias-chips">{"".join(chips)}</div>
</section>'''

    dna = ""
    if s.get("signals"):
        items = []
        role_keys = {"defining": ("roleDefining",), "supporting": ("roleSupporting",),
                     "variable": ("roleVariable",), "avoid": ("roleAvoid",)}
        for sig in s["signals"]:
            sz = z.get("signals_zh", {}).get(sig["id"], {})
            rk = role_keys.get(sig["role"], ("roleSupporting",))[0]
            en_r, zh_r = t(rk)
            items.append(f'''<li class="dna-item">
 <div class="dna-head">
  <span class="dna-name"><span class="lang-en">{esc(sig["name"])}</span><span class="lang-zh dna-name-zh">{esc(sz.get("name_zh", ""))}</span></span>
  <span class="dna-facet">{esc(sig["facet"])}</span>
  <span class="dna-role dna-role-{esc(sig["role"])}"><span class="lang-en">{esc(en_r)}</span><span class="lang-zh">{esc(zh_r)}</span></span>
 </div>
 {bi(sig["description"], sz.get("description_zh", ""), "p", "dna-desc")}
</li>''')
        dna = f'''<section class="sect" style="max-width:none">
 <h2 class="section-title"><span class="lang-en">{esc(en_dna)}</span><span class="lang-zh">{esc(zh_dna)}</span></h2>
 <ol class="dna">{"".join(items)}</ol>
</section>'''

    confused = ""
    cw = s.get("confusedWith")
    if cw and cw.get("slug") in STYLE_BY_SLUG:
        other = STYLE_BY_SLUG[cw["slug"]]
        oz = style_zh(other)
        other_demo = "style-" + other["slug"]
        pair = ""
        if os.path.exists(os.path.join(ROOT, "demos", other_demo + ".html")):
            pair = f'''<div class="vs-pair">
 <div class="vs-cell">{stage("style-" + s["slug"])}<p class="vs-cell-label"><span class="lang-en">{esc(s["name"])}</span><span class="lang-zh">{esc(z.get("name_zh", ""))}</span></p></div>
 <div class="vs-cell">{stage(other_demo)}<p class="vs-cell-label"><span class="lang-en">{esc(other["name"])}</span><span class="lang-zh">{esc(oz.get("name_zh", ""))}</span></p></div>
</div>'''
        czw = z.get("confused_zh", {})
        en_vb, zh_vb = t("vsCrumb")
        confused = f'''<section class="sect" style="max-width:none">
 <h2 class="section-title"><span class="lang-en">{esc(en_cf)}: {esc(cw["name"])}</span><span class="lang-zh">{esc(zh_cf)}：{esc(oz.get("name_zh", cw["name"]))}</span></h2>
 {pair}
 <div class="vs-why">
  <div class="vs-why-card">{bi(cw.get("because", ""), czw.get("because_zh", ""), "p")}</div>
  <div class="vs-why-card">{bi(cw.get("wouldBecomeIf", ""), czw.get("wouldBecomeIf_zh", ""), "p")}</div>
 </div>
 <p class="vs-more"><a href="{vs_url(s["slug"], other["slug"])}"><span class="lang-en">{esc(en_vb)}: {esc(s["name"])} vs {esc(other["name"])} →</span><span class="lang-zh">{esc(zh_vb)}页 →</span></a></p>
</section>'''

    code_sect = ""
    if s.get("code"):
        blocks = []
        for i, c in enumerate(s["code"]):
            title = f'<p class="code-title">{esc(c["title"])}</p>' if c.get("title") else ""
            blocks.append(f'''<div class="code-block">
 <button type="button" class="btn btn-copy" data-copy="code-{s["slug"]}-{i}" data-done-en="{esc(en_cd)}" data-done-zh="{esc(zh_cd)}"><span class="lang-en">{esc(t("copy")[0])}</span><span class="lang-zh">{esc(t("copy")[1])}</span></button>
 {title}
 <pre><code id="code-{s["slug"]}-{i}">{esc(c["code"])}</code></pre>
</div>''')
        code_sect = f'''<section class="sect">
 <h2 class="section-title"><span class="lang-en">{esc(en_ic)}</span><span class="lang-zh">{esc(zh_ic)}</span></h2>
 {"".join(blocks)}
</section>'''

    brief = ""
    if s.get("brief"):
        brief = f'''<section class="sect">
 <h2 class="section-title"><span class="lang-en">{esc(en_br)}</span><span class="lang-zh">{esc(zh_br)}</span></h2>
 {copy_block(s["brief"], z.get("brief_zh", ""), "brief-" + s["slug"])}
</section>'''

    a11y = ""
    if s.get("accessibility"):
        a11y = f'''<section class="sect">
 <h2 class="section-title"><span class="lang-en">{esc(en_a11y)}</span><span class="lang-zh">{esc(zh_a11y)}</span></h2>
 {paras(s["accessibility"], z.get("accessibility_zh", ""), "guide-para")}
</section>'''

    origin = ""
    if s.get("origin"):
        origin = f'''<section class="sect">
 <h2 class="section-title"><span class="lang-en">{esc(en_or)}</span><span class="lang-zh">{esc(zh_or)}</span></h2>
 {paras(s["origin"], z.get("origin_zh", ""), "guide-para")}
</section>'''

    see_also = ""
    if s.get("seeAlso"):
        cards = []
        for sa in s["seeAlso"]:
            ref = (sa.get("slug") or "")
            if ref.startswith("styles/"):
                ref = ref[len("styles/"):]
            if ref in STYLE_BY_SLUG:
                so = STYLE_BY_SLUG[ref]
                soz = style_zh(so)
                cards.append(f'''<a class="rel-card" href="{style_url(so)}">
 <span class="rel-name"><span class="lang-en">{esc(so["name"])}</span><span class="lang-zh rel-name-zh">{esc(soz.get("name_zh", ""))}</span></span>
</a>''')
            else:
                # Dictionary references carry their platform, e.g. "macos/vibrancy".
                ent = next((x for x in ENTRIES if ref in (x["slug"], f'{x["platform"]}/{x["slug"]}')), None)
                if ent:
                    ez = ZH[ent["slug"]]
                    cards.append(f'''<a class="rel-card" href="{entry_url(ent)}">
 <span class="rel-name"><span class="lang-en">{esc(ent["name"])}</span><span class="lang-zh rel-name-zh">{esc(ez["name_zh"])}</span></span>
 <span class="rel-sym">{esc(ent["api"][0]["symbol"])}</span>
</a>''')
        if cards:
            see_also = f'''<section class="sect">
 <h2 class="section-title"><span class="lang-en">{esc(en_sa)}</span><span class="lang-zh">{esc(zh_sa)}</span></h2>
 <div class="rel-grid">{"".join(cards)}</div>
</section>'''

    scope = ""
    if s.get("scope"):
        scope = paras(s["scope"], z.get("scope_zh", ""), "guide-para")

    md = style_markdown(s, z)
    body = f'''{header()}
<main class="wrap entry">
 <nav class="crumbs">
  <a href="/"><span class="lang-en">{esc(en_b)}</span><span class="lang-zh">{esc(zh_b)}</span></a>
  <span class="crumb-sep">/</span>
  <a href="/styles/"><span class="lang-en">{esc(en_sc)}</span><span class="lang-zh">{esc(zh_sc)}</span></a>
  <span class="crumb-sep">/</span>
  <span class="crumb-cur"><span class="lang-en">{esc(s["name"])}</span><span class="lang-zh">{esc(z.get("name_zh", s["name"]))}</span></span>
 </nav>
 <header class="entry-head">
  <h1 class="entry-title">
   <span class="lang-en">{esc(s["name"])}</span>
   <span class="lang-zh entry-title-zh">{esc(z.get("name_zh", ""))}</span>
  </h1>
  {paras(s.get("tagline", ""), z.get("tagline_zh", ""), "entry-tag")}
  {scope}
  <div class="entry-actions">{select_button("style:" + s["slug"])}</div>
 </header>
 {stage("style-" + s["slug"], detail=True)}
 <p class="stage-hint lang-zh">标本可交互，可以直接操作。</p>
 {aliases}
 {dna}
 {confused}
 {code_sect}
 {brief}
 {a11y}
 {origin}
 {see_also}
 <section class="sect">
  <button type="button" class="btn btn-ghost" id="copy-md" data-done-en="{esc(en_cd)}" data-done-zh="{esc(zh_cd)}">⧉ <span class="lang-en">{esc(en_cp)}</span><span class="lang-zh">{esc(zh_cp)}</span></button>
  <template id="md-source">{esc(md)}</template>
 </section>
</main>
{footer()}'''
    en_b, zh_b = t("indexCrumb"); en_sc, zh_sc = t("stylesCrumb")
    path = f'styles/{s["slug"]}/'
    ld = ld_graph(
        ld_defined_term(f'{s["name"]} · {z.get("name_zh", s["name"])}', (s.get("tagline") or "")[:200], "/" + path),
        ld_breadcrumb([(f"{en_b} · {zh_b}", "/"), (f"{en_sc} · {zh_sc}", "/styles/"), (s["name"], "/" + path)]))
    return page(s["name"], z.get("name_zh", s["name"]), (s.get("tagline") or "")[:150],
                (z.get("tagline_zh") or "")[:80], body, path,
                og_image=f'/assets/og/style-{s["slug"]}.png', jsonld=ld)

def style_markdown(s, z):
    lines = [f"# {s['name']} · {z.get('name_zh','')}", "",
             f"Style reference — {SITE_URL}/styles/{s['slug']}/", ""]
    if s.get("tagline"):
        lines += [s["tagline"], z.get("tagline_zh", ""), ""]
    if s.get("aliases"):
        lines += ["## If you called it… / 如果你管它叫……", ""]
        for i, a in enumerate(s["aliases"]):
            az = z.get("aliases_zh", [])
            lines.append(f"- “{a}” / 「{az[i] if i < len(az) else ''}」")
        lines.append("")
    if s.get("signals"):
        lines += ["## Full style DNA / 完整风格 DNA", ""]
        for sig in s["signals"]:
            sz = z.get("signals_zh", {}).get(sig["id"], {})
            lines += [f"- **[{sig['role']}] {sig['name']} · {sz.get('name_zh','')}** ({sig['facet']})",
                      f"  {sig['description']}", f"  {sz.get('description_zh','')}"]
        lines.append("")
    if s.get("brief"):
        lines += ["## Style brief / 风格 Brief", "", s["brief"], "", z.get("brief_zh", ""), ""]
    if s.get("origin"):
        lines += ["## Origin / 起源", "", s["origin"], "", z.get("origin_zh", "")]
    return "\n".join(lines)

def vs_pairs():
    """Unique unordered confused-with pairs across styles."""
    seen, pairs = set(), []
    for s in STYLES:
        c = (s.get("confusedWith") or {}).get("slug", "")
        if not c or c not in STYLE_BY_SLUG:
            continue
        key = tuple(sorted([s["slug"], c]))
        if key in seen:
            continue
        seen.add(key)
        pairs.append((s["slug"], c))
    return pairs

def vs_url(a, b):
    x, y = sorted([a, b])
    return f'/styles/vs/{x}-vs-{y}/'

def vs_page(a_slug, b_slug):
    a, b = STYLE_BY_SLUG[a_slug], STYLE_BY_SLUG[b_slug]
    az, bz = style_zh(a), style_zh(b)
    en_b, zh_b = t("indexCrumb"); en_sc, zh_sc = t("stylesCrumb")
    en_v, zh_v = t("vsCrumb"); en_d, zh_d = t("vsDesc"); en_vb, zh_vb = t("vsViewBoth")
    title_en = f'{a["name"]} vs {b["name"]}'
    title_zh = f'{az.get("name_zh", a["name"])} 对比 {bz.get("name_zh", b["name"])}'

    pair = f'''<div class="vs-pair">
 <div class="vs-cell">{stage("style-" + a["slug"])}<p class="vs-cell-label"><span class="lang-en">{esc(a["name"])}</span><span class="lang-zh">{esc(az.get("name_zh", ""))}</span></p></div>
 <div class="vs-cell">{stage("style-" + b["slug"])}<p class="vs-cell-label"><span class="lang-en">{esc(b["name"])}</span><span class="lang-zh">{esc(bz.get("name_zh", ""))}</span></p></div>
</div>'''

    # directional text blocks (whichever directions exist in the data)
    blocks, faq = [], []
    for x, y, xz, yz in [(a, b, az, bz), (b, a, bz, az)]:
        cw = x.get("confusedWith") or {}
        if cw.get("slug") != y["slug"]:
            continue
        czw = xz.get("confused_zh", {})
        en_ti, zh_ti = t("vsThisIs", a=x["name"]); en_wb, zh_wb = t("vsWouldBecome", b=y["name"])
        blocks.append(f'''<div class="vs-why">
  <div class="vs-why-card"><p class="vs-why-head"><span class="lang-en">{esc(en_ti)}</span><span class="lang-zh">{esc(zh_ti)}</span></p>{bi(cw.get("because", ""), czw.get("because_zh", ""), "p")}</div>
  <div class="vs-why-card"><p class="vs-why-head"><span class="lang-en">{esc(en_wb)}</span><span class="lang-zh">{esc(zh_wb)}</span></p>{bi(cw.get("wouldBecomeIf", ""), czw.get("wouldBecomeIf_zh", ""), "p")}</div>
</div>''')
        faq.append({"@type": "Question", "name": f'How to tell {x["name"]} from {y["name"]}?',
                    "acceptedAnswer": {"@type": "Answer", "text": (cw.get("because", "") + " " + cw.get("wouldBecomeIf", "")).strip()}})

    links = f'''<p class="vs-links"><span class="lang-en">{esc(en_vb)}:</span><span class="lang-zh">{esc(zh_vb)}：</span>
 <a href="{style_url(a)}">{esc(a["name"])}</a> · <a href="{style_url(b)}">{esc(b["name"])}</a></p>'''

    path = vs_url(a_slug, b_slug).lstrip("/")
    ld = ld_graph(
        {"@type": "FAQPage", "mainEntity": faq} if faq else None,
        ld_breadcrumb([(f"{en_b} · {zh_b}", "/"), (f"{en_sc} · {zh_sc}", "/styles/"),
                       (f"{en_v} · {zh_v}", "/styles/vs/"), (title_en, "/" + path)]))
    body = f'''{header()}
<main class="wrap">
 <nav class="crumbs" aria-label="Breadcrumb">
  <a href="/"><span class="lang-en">{esc(en_b)}</span><span class="lang-zh">{esc(zh_b)}</span></a>
  <span class="crumb-sep">/</span>
  <a href="/styles/"><span class="lang-en">{esc(en_sc)}</span><span class="lang-zh">{esc(zh_sc)}</span></a>
  <span class="crumb-sep">/</span>
  <span class="crumb-cur"><span class="lang-en">{esc(title_en)}</span><span class="lang-zh">{esc(title_zh)}</span></span>
 </nav>
 <section class="hero">
  <h1><span class="lang-en">{esc(title_en)}</span><span class="lang-zh">{esc(title_zh)}</span></h1>
  <p class="hero-desc"><span class="lang-en">{esc(en_d)}</span> <span class="lang-zh">{esc(zh_d)}</span></p>
 </section>
 {pair}
 {"".join(blocks)}
 {links}
</main>
{footer()}'''
    x, y = sorted([a_slug, b_slug])
    return page(title_en, title_zh, en_d[:150], zh_d[:80], body, path,
                og_image=f"/assets/og/vs-{x}-vs-{y}.png", jsonld=ld)

def search_index_data():
    items = []
    for e in ENTRIES:
        z = ZH[e["slug"]]
        items.append({
            "slug": e["slug"], "platform": e["platform"], "url": entry_url(e),
            "name": e["name"], "name_zh": z["name_zh"], "tagline": e["tagline"],
            "tagline_zh": z["tagline_zh"], "symbol": e["api"][0]["symbol"],
            "aka": e["aka"], "aka_zh": z["aka_zh"],
            "fuzzy": e["fuzzy"], "fuzzy_zh": z["fuzzy_zh"],
        })
    return items

def catalog_data():
    items = []
    for e in ENTRIES:
        z = ZH[e["slug"]]
        items.append({
            "id": "entry:" + e["slug"], "type": "ui-element", "slug": e["slug"],
            "name": e["name"], "nameZh": z["name_zh"], "url": entry_url(e),
            "summary": z["tagline_zh"], "tags": {"platform": [e["platform"]]},
            "prompt": z["prompt_zh"],
            "source": {"kind": "upstream", "label": "joeseesun/learnui"}
        })
    for s in STYLES:
        z = style_zh(s)
        items.append({
            "id": "style:" + s["slug"], "type": "visual-style", "slug": s["slug"],
            "name": s["name"], "nameZh": z.get("name_zh", s["name"]), "url": style_url(s),
            "summary": first_para(z.get("tagline_zh", s.get("tagline", ""))),
            "tags": {}, "prompt": z.get("brief_zh", s.get("brief", "")),
            "source": {"kind": "upstream", "label": "joeseesun/learnui"}
        })
    for site in SITES:
        items.append({
            "id": "site:" + site["slug"], "type": "site-reference", "slug": site["slug"],
            "name": site["nameEn"], "nameZh": site["nameZh"],
            "url": f'/sites/{site["slug"]}/', "summary": site["summaryZh"],
            "tags": {"category": [site["category"]]}, "prompt": site["summaryZh"],
            "source": {"kind": "external", "label": "awesome-design-md", "license": "MIT"}
        })
    for case in GRAPHICS:
        items.append({
            "id": "graphic:" + case["slug"], "type": "graphic-reference", "slug": case["slug"],
            "name": graphic_title_en(case), "nameZh": graphic_title_zh(case), "url": graphic_url(case),
            "summary": case["summaryZh"], "tags": {"graphicType": [case["type"]], "styles": case["styleTags"], "techniques": case["techniques"]},
            "styles": [GRAPHIC_STYLES[s]["nameZh"] for s in case["styleTags"]],
            "techniques": [GRAPHIC_TECHS[t]["nameZh"] for t in case["techniques"]], "palette": [c["hex"] for c in case["palette"]],
            "credits": case["credits"], "year": case.get("year") or None, "images": [f'/assets/graphics/{im["file"]}' for im in case["images"]], "imagePrompt": case["imagePromptZh"], "prompt": case["codePromptZh"],
            "source": {"kind": "external", "label": GRAPHIC_ISSUES[case["issue"]]["author"], "url": GRAPHIC_ISSUES[case["issue"]]["url"], "original": case["sourceLabel"]}
        })
    for logo in LOGOS:
        items.append({
            "id": "logo:" + logo["slug"], "type": "logo-reference", "slug": logo["slug"],
            "name": logo["name"], "nameZh": logo_name_zh(logo), "url": logo_url(logo),
            "summary": logo["aboutZh"],
            "tags": {"logoType": [logo["type"]], "use": [logo["use"]]},
            "logoType": LOGO_TYPES[logo["type"]]["nameZh"], "construction": logo["readZh"],
            "website": logo["url"], "license": logo["licenseZh"], "prompt": logo["promptZh"],
            "source": {"kind": "external", "label": LOGO_ISSUES[logo["issue"]]["author"], "url": LOGO_ISSUES[logo["issue"]]["url"]}
        })
    return {
        "schemaVersion": 1,
        "language": "zh-CN",
        "description": "供 AI 和选择导出功能读取的 LearnUI 结构化目录。",
        "items": items
    }

def catalog_readme():
    return '''# LearnUI AI 数据入口

优先读取 `catalog.json`。它包含知名网站设计规范、UI 元素、视觉风格、Logo 和平面设计案例的统一字段，不需要扫描整个仓库。

- `type=ui-element`：现有 UI 词典条目和实现 Prompt。
- `type=visual-style`：现有视觉风格和 Style Brief。
- `type=site-reference`：知名网站的设计系统、分类和中文风格解读。
- `type=logo-reference`：Logo 图鉴，含 logo 类型、构成拆解、网站用途与授权、生成 Prompt。
- `type=graphic-reference`：平面设计案例，含风格与手法、配色、生图与代码两种 Prompt、原作设计方与图源。
'''

def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

def build():
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "validate-data.py")], check=True)
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    write("index.html", homepage())
    write("sources/index.html", sources_page())
    if SITES:
        write("sites/index.html", sites_hub_page())
        for site in SITES:
            write(f'sites/{site["slug"]}/index.html', site_detail_page(site))
    if GRAPHICS:
        write("graphics/index.html", graphics_hub_page())
        for case in GRAPHICS:
            write(f'graphics/{case["slug"]}/index.html', graphic_page(case))
    if LOGOS:
        write("logos/index.html", logos_hub_page())
        for logo in LOGOS:
            write(f'logos/{logo["slug"]}/index.html', logo_page(logo))
    for e in ENTRIES:
        write(f'{e["platform"]}/{e["slug"]}/index.html', entry_page(e))
        write(f'api/specimens/{e["slug"]}.json', json.dumps(specimen_payload(e), ensure_ascii=False, separators=(",", ":")))
    for slug in GUIDES:
        write(f"guides/{slug}/index.html", guide_page(slug))
    if STYLES:
        write("styles/index.html", styles_hub_page())
        for s in STYLES:
            write(f'styles/{s["slug"]}/index.html', style_page(s))
    # style look-alike comparison pages ("X vs Y")
    for a, b in vs_pairs():
        write(vs_url(a, b).lstrip("/") + "index.html", vs_page(a, b))
    # 404
    write("404.html", page("404", "页面不存在", "Page not found.", "页面不存在。",
                           f'''{header()}
<main class="wrap">
 <section class="hero">
  <h1>404</h1>
  <p class="hero-desc"><span class="lang-en">This page doesn't exist. Try the dictionary, the styles atlas, or graphic design.</span>
  <span class="lang-zh">页面不存在。去词典、风格图鉴或平面设计看看。</span></p>
  <p class="hero-desc"><a href="/">Dictionary</a> · <a href="/styles/">Styles</a> · <a href="/graphics/">Graphic design</a></p>
 </section>
</main>
{footer()}''', "404.html"))
    # static assets
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    shutil.copyfile(os.path.join(ROOT, "manifest.webmanifest"), os.path.join(OUT, "manifest.webmanifest"))
    shutil.copyfile(os.path.join(ROOT, "offline.html"), os.path.join(OUT, "offline.html"))
    shutil.copyfile(os.path.join(ROOT, "LICENSE"), os.path.join(OUT, "LICENSE.txt"))
    write("assets/demo-i18n.js", "window.DEMO_I18N=" + json.dumps(DEMO_I18N, ensure_ascii=False) + ";")
    write("api/catalog.json", json.dumps(catalog_data(), ensure_ascii=False, separators=(",", ":")))
    write("api/search-index.json", json.dumps(search_index_data(), ensure_ascii=False, separators=(",", ":")))
    write("api/demo-i18n.json", json.dumps(DEMO_I18N, ensure_ascii=False, indent=2))
    write("api/README.md", catalog_readme())
    with open(os.path.join(ROOT, "sw.js"), encoding="utf-8") as f:
        sw = f.read()
    version = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    sw = sw.replace("__SW_VERSION__", version)
    sw = sw.replace("__ASSET_VERSION__", ASSET_VERSION)
    write("sw.js", sw)
    # feed
    items = []
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    for e in ENTRIES:
        z = ZH[e["slug"]]
        items.append(f'''<item><title>{esc(e["name"])} · {esc(z["name_zh"])}</title>
<link>{SITE_URL}/{e["platform"]}/{e["slug"]}/</link>
<guid>{SITE_URL}/{e["platform"]}/{e["slug"]}/</guid>
<pubDate>{date}</pubDate>
<description>{esc(e["tagline"])} / {esc(z["tagline_zh"])}</description></item>''')
    for s in STYLES:
        z = style_zh(s)
        items.append(f'''<item><title>{esc(s["name"])} · {esc(z.get("name_zh",""))}</title>
<link>{SITE_URL}/styles/{s["slug"]}/</link>
<guid>{SITE_URL}/styles/{s["slug"]}/</guid>
<pubDate>{date}</pubDate>
<description>{esc((s.get("tagline") or "")[:200])}</description></item>''')
    write("feed.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>Learn UIUX</title>
<link>{SITE_URL}/</link>
<description>{esc(UI["tagline"])} - bilingual UI dictionary</description>
{"".join(items)}
</channel></rss>''')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    urls = ["/", "/sources/"] + \
           (["/sites/"] + [f'/sites/{site["slug"]}/' for site in SITES] if SITES else []) + \
           (["/logos/"] + [logo_url(logo) for logo in LOGOS] if LOGOS else []) + \
           (["/graphics/"] + [graphic_url(c) for c in GRAPHICS] if GRAPHICS else []) + \
           [f'/{e["platform"]}/{e["slug"]}/' for e in ENTRIES] + \
           [f"/guides/{s}/" for s in GUIDES]
    if STYLES:
        urls += ["/styles/"] + [f'/styles/{s["slug"]}/' for s in STYLES] + \
                [vs_url(a, b) for a, b in vs_pairs()]
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    write("sitemap.xml", f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"".join(f"<url><loc>{SITE_URL}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)}
</urlset>''')
    print(f"Built {len(urls)} pages into site/")

if __name__ == "__main__":
    build()
