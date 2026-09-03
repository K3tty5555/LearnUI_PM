#!/usr/bin/env python3
"""Learn UI PM static site builder - bilingual (EN/中文) replica of namethatui.com.
Stdlib only. Reads data/ + demos/, writes site/."""
import json, html, os, shutil, datetime, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = os.environ.get("SITE_URL", "https://K3tty5555.github.io/LearnUI_PM").rstrip("/")
SITE_NAME = "Learn UI PM"
NEW_SLUGS = {"text-scramble","spring","easing","masonry","bento-grid","hamburger-menu","lightbox","marquee"}
STYLE_NEW_SLUGS = {"frutiger-metro","anti-design","acid-graphics","risograph","zine-collage","steampunk","dieselpunk","biopunk","afrofuturism","de-stijl","constructivism","pop-art","surrealism","art-nouveau","holographic","isometric-3d","line-art","hand-drawn","fantasy-rpg","lcars"}

def load(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)

ENTRIES = load("data/entries.json")
UI = load("data/ui.json")
GUIDES = load("data/guides.json")
TABLE = load("data/translate-table.json")
ZH = {}
for i in range(1, 5):
    ZH.update(load(f"data/zh/entries-{i}.json"))
GUIDES_ZH = load("data/zh/guides.json")
TABLE_ZH = load("data/zh/translate-table-zh.json")

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
PM_REFERENCES = _nn(load_or("data/pm/references.json", []))
PM_TAXONOMY = _nn(load_or("data/pm/taxonomy.json", {}))
PM_BY_SLUG = {r["slug"]: r for r in PM_REFERENCES}
PM_LABELS = {
    group: {item["id"]: item["label"] for item in items}
    for group, items in PM_TAXONOMY.items()
}
DEMO_I18N = _nn(load_or("data/demo-i18n.json", {"global": {}, "patterns": [], "demos": {}}))
SITES_META = _nn(load_or("data/sites-manifest.json", {"items": []}))
SITES = SITES_META.get("items", [])
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

def stage(slug, detail=False):
    cls = "stage stage-detail" if detail else "stage stage-card"
    pe = "" if detail else " pe-none"
    return (f'<div class="{cls}{pe}"><div class="stage-center">'
            f'<div class="fragment" data-slug="{esc(slug)}">{demo_fragment(slug)}</div>'
            f'</div></div>')

def select_button(item_id, compact=False):
    cls = "select-toggle select-toggle-compact" if compact else "btn select-toggle"
    return (f'<button type="button" class="{cls}" data-select-id="{esc(item_id)}" '
            f'aria-pressed="false"><span data-select-label>加入参考</span></button>')

def selection_panel():
    return '''<div class="selection-dock" id="selection-dock" hidden>
 <button type="button" class="selection-dock-button" id="selection-open" aria-controls="selection-dialog">
  已选参考 <b id="selection-count">0</b>
 </button>
</div>
<dialog class="selection-dialog" id="selection-dialog" aria-labelledby="selection-title">
 <div class="selection-head">
  <div><h2 id="selection-title">参考选择集</h2><p>组合页面参考、知名网站、UI 元素和视觉风格，导出给 AI。</p></div>
  <button type="button" class="icon-button" id="selection-close" aria-label="关闭">×</button>
 </div>
 <div class="selection-list" id="selection-list"></div>
 <div class="selection-empty" id="selection-empty">还没有选择参考。</div>
 <div class="selection-actions">
  <button type="button" class="btn" id="selection-copy-md">复制 Markdown</button>
  <button type="button" class="btn" id="selection-download-json">下载 JSON</button>
  <button type="button" class="btn btn-danger" id="selection-clear">清空</button>
 </div>
 <p class="selection-status" id="selection-status" role="status"></p>
</dialog>'''

def header():
    en_all, zh_all = t("tabAll"); en_g, zh_g = t("guideCrumb"); en_st, zh_st = t("stylesCrumb")
    return f'''<header class="site-header">
 <div class="wrap header-in">
  <a class="wordmark" href="/"><img src="/assets/icons/ai-pm-client-circle-64.png" alt="" width="28" height="28">Learn UI PM</a>
  <nav class="site-nav">
   <a href="/#dictionary"><span class="lang-en">Dictionary</span><span class="lang-zh nav-zh">词典</span></a>
   <a href="/references/"><span class="lang-en">References</span><span class="lang-zh nav-zh">页面参考</span></a>
   <a href="/sites/"><span class="lang-en">Sites</span><span class="lang-zh nav-zh">知名网站</span></a>
   <a href="/styles/"><span class="lang-en">{esc(en_st)}</span><span class="lang-zh nav-zh">{esc(zh_st)}</span></a>
   <a href="/#guides"><span class="lang-en">{esc(en_g)}</span><span class="lang-zh nav-zh">{esc(zh_g)}</span></a>
   <a href="/guides/translate/"><span class="lang-en">Translation</span><span class="lang-zh nav-zh">翻译表</span></a>
  </nav>
  <div class="lang-switch" role="group" aria-label="Language">
   <button type="button" data-mode="bilingual" class="ls-btn">对照</button>
   <button type="button" data-mode="en" class="ls-btn">EN</button>
   <button type="button" data-mode="zh" class="ls-btn">中文</button>
  </div>
 </div>
</header>'''

def footer():
    return '''<div class="def-pop" id="def-pop" hidden>
 <div class="def-word" id="def-word"></div>
 <div class="def-body" id="def-body"></div>
 <div class="def-src" id="def-src"></div>
</div>'''

def page(title_en, title_zh, desc_en, desc_zh, body, path="", og_image="/assets/og/_default.png", jsonld=""):
    url = SITE_URL + "/" + path
    og_url = SITE_URL + og_image
    ld = f'<script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    return f'''<!DOCTYPE html>
<html lang="zh-CN" data-lang-mode="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LearnUI_PM</title>
<meta name="description" content="{esc(desc_zh)} {esc(desc_en)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:title" content="{esc(title_en)} · {esc(title_zh)} - {SITE_NAME}">
<meta property="og:description" content="{esc(desc_zh)} {esc(desc_en)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{esc(og_url)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{esc(og_url)}">
<meta name="theme-color" content="#e6eff2">
{ld}
<link rel="manifest" href="/manifest.webmanifest">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME} RSS" href="/feed.xml">
<link rel="icon" href="/assets/icons/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/geist-vf.woff2" as="font" type="font/woff2" crossorigin>
<script>
// 默认纯中文；用户手动切换后持久化。
(function(){{try{{
  var m=localStorage.getItem("ntui-lang-mode");
  if(m!=="bilingual"&&m!=="zh"&&m!=="en"){{
    m="zh";
  }}
  document.documentElement.setAttribute("data-lang-mode",m);
}}catch(e){{}}}})();
</script>
<link rel="stylesheet" href="/assets/site.css">
<link rel="stylesheet" href="/assets/reference-demos.css">
<link rel="stylesheet" href="/assets/glass-theme.css">
</head>
<body>
{body}
{selection_panel()}
<script src="/assets/demo-i18n.js"></script>
<script src="/assets/site.js"></script>
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
 {stage(e["slug"])}
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
    g1, g2 = GUIDES["appkit-vs-swiftui"], GUIDES["swift-vs-electron"]
    en_cnt, zh_cnt = t("entriesCount", n=len(ENTRIES))
    en_ph, zh_ph = t("searchPlaceholder")
    en_s, zh_s = t("surprise")
    en_gt, zh_gt = t("guidesTitle")
    en_vp, zh_vp = t("vibePromo")
    en_all, zh_all = t("tabAll"); en_web, zh_web = t("tabWeb"); en_mac, zh_mac = t("tabMacos")
    search_json = json.dumps(search_index, ensure_ascii=False).replace("</", "<\\/")
    body = f'''{header()}
<main class="wrap">
 <section class="hero">
  <h1 class="hero-title"><span class="lang-en">{esc(UI["heroTitle"])}</span><span class="lang-zh hero-title-zh">{esc(UI["heroTitleZh"])}</span></h1>
  {bi(UI["heroSub"], UI["heroSubZh"], "p", "hero-sub")}
  <p class="vibe-promo"><span class="tag tag-new">{esc(UI["newBadge"])}</span>
   <a class="lang-en" href="/styles/">{esc(en_vp)} →</a>
   <a class="lang-zh" href="/styles/">{esc(zh_vp)} →</a></p>
  <div class="controls">
   <div class="search-box">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
    <input id="search" type="search" autocomplete="off"
     data-ph-en="{esc(en_ph)}" data-ph-zh="{esc(zh_ph)}" placeholder="{esc(zh_ph)} / {esc(en_ph)}" aria-label="搜索 UI 元素">
    <kbd class="search-kbd">/</kbd>
   </div>
   <button type="button" id="surprise" class="btn btn-ghost">⚂ <span class="lang-en">{esc(en_s)}</span><span class="lang-zh">{esc(zh_s)}</span></button>
   <div class="tabs" role="tablist">
    <button type="button" class="tab active" data-filter="all"><span class="lang-en">{esc(en_all)}</span><span class="lang-zh">{esc(zh_all)}</span></button>
    <button type="button" class="tab" data-filter="web"><span class="lang-en">{esc(en_web)}</span><span class="lang-zh">{esc(zh_web)}</span></button>
    <button type="button" class="tab" data-filter="macos"><span class="lang-en">{esc(en_mac)}</span><span class="lang-zh">{esc(zh_mac)}</span></button>
   </div>
   <p class="count-note" id="count-note"><span class="lang-en" data-tpl="{esc(UI["entriesCount"])}">{esc(en_cnt)}</span><span class="lang-zh" data-tpl="{esc(UI["entriesCountZh"])}">{esc(zh_cnt)}</span></p>
  </div>
 </section>
 <section id="dictionary" class="grid" aria-live="polite">
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
 <section id="guides" class="guides">
  <h2 class="section-title"><span class="lang-en">{esc(en_gt)}</span><span class="lang-zh">{esc(zh_gt)}</span></h2>
  <div class="guide-grid">
   <a class="guide-card" href="/guides/appkit-vs-swiftui/">
    <span class="guide-kind">Guide</span>
    <span class="guide-title">{esc(g1["title"])}</span>
    {bi(UI["guide1Desc"], UI["guide1DescZh"], "span", "guide-desc")}
   </a>
   <a class="guide-card" href="/guides/swift-vs-electron/">
    <span class="guide-kind">Guide</span>
    <span class="guide-title">{esc(g2["title"])}</span>
    {bi(UI["guide2Desc"], UI["guide2DescZh"], "span", "guide-desc")}
   </a>
   <a class="guide-card" href="/guides/translate/">
    <span class="guide-kind">Guide</span>
    <span class="guide-title">{esc(UI["translateTitle"])}</span>
    {bi(UI["guide3Desc"], UI["guide3DescZh"], "span", "guide-desc")}
   </a>
  </div>
 </section>
</main>
{footer()}
<script id="search-index" type="application/json">{search_json}</script>'''
    return page(UI["heroTitle"], UI["heroTitleZh"], UI["heroSub"], UI["heroSubZh"], body, og_image="/assets/og/_home.png")

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
   <div class="meta-row"><dt>{esc(en_ac)}<span class="lang-zh dt-zh">{esc(zh_ac)}</span></dt>
    <dd><span class="lang-en">{esc(aka_en)}</span><span class="lang-zh zh-line">{esc(aka_zh)}</span></dd></div>
   <div class="meta-row"><dt>{esc(en_fy)}<span class="lang-zh dt-zh">{esc(zh_fy)}</span></dt>
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

def translate_page():
    en_b, zh_b = t("indexCrumb"); en_g, zh_g = t("guideCrumb")
    en_tc, zh_tc = t("thingCol")
    linkable = {"Alert": "alert", "Color well / color picker": "color-well", "Context menu": "context-menu",
                "Level indicator": "level-indicator", "Gauge / level indicator": "level-indicator",
                "Menu bar extra / status item": "menu-bar-extra", "Popover": "popover",
                "Pull-down button": "popup-pulldown-combo", "Pop-up button": "popup-pulldown-combo",
                "Save/export panel": "save-panel", "Search field": "search-field",
                "Segmented control": "segmented-control", "Sheet": "sheet", "Sidebar": "sidebar",
                "Slider": "slider", "Stepper": "stepper", "Switch": "switch-checkbox-radio",
                "Toolbar": "toolbar", "Outline / source list": "outline-view", "List": "outline-view"}
    rows = []
    for i, r in enumerate(TABLE):
        zh = TABLE_ZH[i]["thing_zh"]
        note_en = r.get("note", "")
        thing_html = esc(r["thing"])
        slug = linkable.get(r["thing"])
        if slug:
            plat = "macos"
            thing_html = f'<a class="thing-link" href="/{plat}/{slug}/">{esc(r["thing"])}</a>'
        note = f'<span class="table-note">{esc(note_en)}</span>' if note_en else ""
        rows.append(f'''<tr data-search="{esc((r["thing"] + " " + zh + " " + r["appkit"] + " " + r["swiftui"]).lower())}">
 <td class="fw">{thing_html}<span class="lang-zh zh-line">{esc(zh)}</span>{note}</td>
 <td class="mono">{esc(r["appkit"])}</td>
 <td class="mono">{esc(r["swiftui"])}</td>
</tr>''')
    en_cnt, zh_cnt = t("translateCount", n=len(TABLE), total=len(TABLE))
    body = f'''{header()}
<main class="wrap entry">
 <nav class="crumbs">
  <a href="/"><span class="lang-en">{esc(en_b)}</span><span class="lang-zh">{esc(zh_b)}</span></a>
  <span class="crumb-sep">/</span>
  <span><span class="lang-en">{esc(en_g)}</span><span class="lang-zh">{esc(zh_g)}</span></span>
  <span class="crumb-sep">/</span>
  <span class="crumb-cur"><span class="lang-en">{esc(UI["translateTitle"])}</span><span class="lang-zh">翻译对照表</span></span>
 </nav>
 <header class="entry-head">
  <h1 class="entry-title"><span class="lang-en">{esc(UI["translateTitle"])}</span><span class="lang-zh entry-title-zh">翻译对照表</span></h1>
  <p class="guide-sub mono-sm">/ {esc(UI["translateSubtitle"])} /</p>
  {bi(UI["translateLede"], UI["translateLedeZh"], "p", "entry-tag")}
 </header>
 <section class="translate-tool" aria-label="翻译对照表工具">
  <div class="translate-toolbar">
   <div class="search-box table-search">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
    <input id="table-search" type="search" autocomplete="off" placeholder="筛选术语或 API" aria-label="筛选翻译对照表">
   </div>
   <p class="translate-count"><span class="lang-en" id="table-count" data-tpl="{esc(UI["translateCount"])}">{esc(en_cnt)}</span><span class="lang-zh" id="table-count-zh" data-tpl="{esc(UI["translateCountZh"])}">{esc(zh_cnt)}</span></p>
  </div>
  <div class="table-scroll"><table class="api-table translate-table" id="translate-table">
   <thead><tr><th>{esc(en_tc)}<span class="lang-zh th-zh">{esc(zh_tc)}</span></th><th>AppKit</th><th>SwiftUI</th></tr></thead>
   <tbody>{"".join(rows)}</tbody>
  </table></div>
 </section>
</main>
{footer()}'''
    return page(UI["translateTitle"], "翻译对照表", UI["translateLede"], UI["translateLedeZh"], body, "guides/translate/")

# ---------------- product/page references ----------------

def reference_url(ref):
    return f'/references/{ref["slug"]}/'

def pm_labels(group, ids):
    labels = PM_LABELS.get(group, {})
    return [labels.get(item, item) for item in ids]

def reference_prompt(ref):
    return "\n".join([
        ref["promptHints"]["summary"],
        "适用场景：" + "、".join(ref["scenarios"]) + "。",
        "页面结构：" + "；".join(ref["structure"]) + "。",
        "视觉特征：" + "；".join(ref["visualTraits"]) + "。",
        "关键状态：" + "、".join(pm_labels("states", ref["states"])) + "。",
        "需要做到：" + "；".join(ref["promptHints"]["do"]) + "。",
        "避免：" + "；".join(ref["promptHints"]["avoid"]) + "。",
    ])

def reference_markdown(ref):
    lines = [
        f'# {ref["title"]} ({ref["titleEn"]})', "", ref["summary"], "",
        "## 分类", "",
        "- 产品类型：" + "、".join(pm_labels("productTypes", ref["productTypes"])),
        "- 页面类型：" + "、".join(pm_labels("pageTypes", ref["pageTypes"])),
        "- 布局方式：" + "、".join(pm_labels("layouts", ref["layouts"])),
        "- 视觉气质：" + "、".join(pm_labels("moods", ref["moods"])),
        "- 关键状态：" + "、".join(pm_labels("states", ref["states"])), "",
        "## 页面结构", "",
    ]
    lines += [f"- {item}" for item in ref["structure"]]
    lines += ["", "## 视觉特征", ""]
    lines += [f"- {item}" for item in ref["visualTraits"]]
    lines += ["", "## AI 风格说明", "", reference_prompt(ref), ""]
    return "\n".join(lines)

def reference_card(ref):
    chips = pm_labels("productTypes", ref["productTypes"][:1]) + pm_labels("pageTypes", ref["pageTypes"][:1]) + pm_labels("layouts", ref["layouts"][:1])
    return f'''<article class="catalog-item reference-card-item" data-reference-slug="{esc(ref["slug"])}">
 <a class="reference-card" href="{reference_url(ref)}">
  {stage(ref["demo"])}
  <div class="card-meta">
   <h3>{esc(ref["title"])} <span>{esc(ref["titleEn"])}</span></h3>
   <p>{esc(ref["summary"])}</p>
   <div class="reference-card-tags">{"".join(f"<span>{esc(label)}</span>" for label in chips)}</div>
  </div>
 </a>
 {select_button("reference:" + ref["slug"], compact=True)}
</article>'''

def reference_filter_group(key, title):
    options = []
    for item in PM_TAXONOMY.get(key, []):
        count = sum(1 for ref in PM_REFERENCES if item["id"] in ref.get(key, []))
        options.append(f'''<label><input type="checkbox" data-ref-filter="{esc(key)}" value="{esc(item["id"])}"><span>{esc(item["label"])}</span><small>{count}</small></label>''')
    return f'''<details class="reference-filter-group" open>
 <summary>{esc(title)}</summary>
 <div>{"".join(options)}</div>
</details>'''

def references_page():
    index = [{
        "slug": ref["slug"], "title": ref["title"], "titleEn": ref["titleEn"],
        "summary": ref["summary"], "scenarios": ref["scenarios"],
        "structure": ref["structure"], "visualTraits": ref["visualTraits"],
        "productTypes": ref["productTypes"], "pageTypes": ref["pageTypes"],
        "layouts": ref["layouts"], "moods": ref["moods"], "states": ref["states"]
    } for ref in PM_REFERENCES]
    filters = "".join([
        reference_filter_group("productTypes", "产品类型"),
        reference_filter_group("pageTypes", "页面类型"),
        reference_filter_group("layouts", "布局方式"),
        reference_filter_group("moods", "视觉气质"),
        reference_filter_group("states", "交互状态"),
    ])
    cards = "\n".join(reference_card(ref) for ref in PM_REFERENCES)
    index_json = json.dumps(index, ensure_ascii=False).replace("</", "<\\/")
    body = f'''{header()}
<main class="wrap references-page">
 <nav class="crumbs"><a href="/">首页</a><span class="crumb-sep">/</span><span class="crumb-cur">页面参考</span></nav>
 <header class="references-head">
  <div><h1>页面参考</h1><p>按产品、页面、布局、气质和状态筛选真实界面样例，选中后导出给 AI。</p></div>
  <a class="btn" href="/api/catalog.json">查看结构化数据</a>
 </header>
 <div class="reference-search-row">
  <div class="search-box"><input id="reference-search" type="search" autocomplete="off" data-ph-en="Search pages, scenarios, or traits" data-ph-zh="搜索页面、场景或特征" placeholder="搜索页面、场景或特征" aria-label="搜索页面参考"><kbd class="search-kbd">/</kbd></div>
  <p id="reference-count" class="count-note">{len(PM_REFERENCES)} 个参考</p>
  <button type="button" class="btn" id="reference-reset">重置筛选</button>
 </div>
 <div class="reference-browser">
  <aside class="reference-filters" aria-label="页面参考筛选">{filters}</aside>
  <section>
   <div class="reference-grid" id="reference-grid">{cards}</div>
   <div class="no-result" id="reference-no-result" hidden><b>没有符合条件的参考</b><p>减少筛选条件或换一个关键词。</p></div>
  </section>
 </div>
 <script id="reference-index" type="application/json">{index_json}</script>
</main>
{footer()}'''
    return page("Page references", "页面参考", "Filter reusable product page references.",
                "按产品类型、页面类型、布局、气质和状态筛选页面参考。", body, "references/")

def reference_page(ref):
    tags = []
    for group in ("productTypes", "pageTypes", "layouts", "moods"):
        tags += pm_labels(group, ref[group])
    states = pm_labels("states", ref["states"])
    prompt = reference_prompt(ref)
    md = reference_markdown(ref)
    structure = "".join(f"<li>{esc(item)}</li>" for item in ref["structure"])
    traits = "".join(f"<li>{esc(item)}</li>" for item in ref["visualTraits"])
    dos = "".join(f"<li>{esc(item)}</li>" for item in ref["promptHints"]["do"])
    avoids = "".join(f"<li>{esc(item)}</li>" for item in ref["promptHints"]["avoid"])
    body = f'''{header()}
<main class="wrap entry reference-detail">
 <nav class="crumbs"><a href="/references/">页面参考</a><span class="crumb-sep">/</span><span class="crumb-cur">{esc(ref["title"])}</span></nav>
 <header class="entry-head">
  <h1 class="reference-title">{esc(ref["title"])} <span>{esc(ref["titleEn"])}</span></h1>
  <p class="entry-tag">{esc(ref["summary"])}</p>
  <div class="reference-tags">{"".join(f"<span>{esc(tag)}</span>" for tag in tags)}</div>
  <div class="entry-actions">{select_button("reference:" + ref["slug"])}</div>
 </header>
 {stage(ref["demo"], detail=True)}
 <p class="stage-hint">标本可交互，可以切换不同状态。</p>
 <div class="reference-detail-grid">
  <section><h2>适用场景</h2><p>{esc("、".join(ref["scenarios"]))}</p></section>
  <section><h2>关键状态</h2><div class="reference-tags">{"".join(f"<span>{esc(state)}</span>" for state in states)}</div></section>
  <section><h2>布局结构</h2><ol>{structure}</ol></section>
  <section><h2>视觉特征</h2><ul>{traits}</ul></section>
 </div>
 <section class="sect reference-guidance">
  <h2>实现约束</h2>
  <div class="guidance-cols"><div><h3>需要做到</h3><ul>{dos}</ul></div><div><h3>避免</h3><ul>{avoids}</ul></div></div>
 </section>
 <section class="sect">
  <h2>AI 风格说明</h2>
  <div class="copy-block"><button type="button" class="btn btn-copy" data-copy="reference-prompt" data-done-zh="已复制">复制</button><div class="copy-text"><p id="reference-prompt">{esc(prompt)}</p></div></div>
 </section>
 <section class="sect reference-detail-actions">
  <button type="button" class="btn" id="copy-md" data-done-zh="已复制">复制本页 Markdown</button>
  <template id="md-source">{esc(md)}</template>
  <span>来源：{esc(ref["source"]["label"])}，{esc(ref["source"]["license"])} License</span>
 </section>
</main>
{footer()}'''
    return page(ref["titleEn"], ref["title"], ref["summary"], ref["summary"], body,
                f'references/{ref["slug"]}/')

def sources_page():
    body = f'''{header()}
<main class="wrap entry sources-page">
 <nav class="crumbs"><a href="/">首页</a><span class="crumb-sep">/</span><span class="crumb-cur">来源与许可证</span></nav>
 <header class="entry-head"><h1 class="reference-title">来源与许可证 <span>Sources &amp; License</span></h1><p class="entry-tag">原始内容与新增内容分开管理，便于识别来源和同步上游。</p></header>
 <section class="sect"><h2>上游内容</h2><p>UI 词典、指南和部分视觉风格来自 <a href="https://github.com/joeseesun/learnui" rel="noopener">joeseesun/learnui</a>。其英文源内容复刻自 <a href="https://namethatui.com/" rel="noopener">namethatui.com</a>，版权归原作者。</p></section>
 <section class="sect"><h2>本项目新增内容</h2><p><code>data/pm/</code>、<code>demos/pm/</code> 及页面参考功能为独立新增内容，不覆盖上游数据文件。</p></section>
 <section class="sect"><h2>知名网站图鉴</h2><p><code>/sites/</code> 镜像自原 LearnUI 线上页面。条目中的 DESIGN.md 来自 <a href="https://github.com/VoltAgent/awesome-design-md" rel="noopener">VoltAgent/awesome-design-md</a>（MIT License），中文解读与品牌 mock 保留原页面来源说明。</p></section>
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
  <p class="lang-en hero-sub">Browse real website previews and the DESIGN.md behind their color, type, components, and layout decisions.</p>
  <p class="lang-zh hero-sub">查看真实网站预览，以及色彩、字体、组件和布局决策背后的完整 DESIGN.md。</p>
  <div class="site-tools">
   <div class="site-filter-row">
    <div class="search-box site-search-box"><input id="site-search" type="search" autocomplete="off" data-ph-en="Search a brand or visual trait" data-ph-zh="搜索品牌或视觉特征" placeholder="搜索品牌或视觉特征" aria-label="搜索知名网站设计规范"><kbd class="search-kbd">/</kbd></div>
    <label class="site-filter-select"><span>行业</span><select id="site-category" aria-label="按行业筛选">{"".join(category_options)}</select></label>
    <label class="site-filter-select"><span>设计气质</span><select id="site-vibe" aria-label="按设计气质筛选">{"".join(vibe_options)}</select></label>
   </div>
   <p class="site-result-count" id="site-count" role="status" aria-live="polite" aria-atomic="true"><span class="lang-en" data-tpl="Showing {{shown}} of {{total}} results">Showing 12 of {len(SITES)} results</span><span class="lang-zh" data-tpl="显示 {{shown}} / {{total}} 个结果">显示 12 / {len(SITES)} 个结果</span></p>
  </div>
 </section>
 <section class="style-grid sites-grid" id="sites" aria-live="polite">{cards}</section>
 <div class="site-more-row"><button type="button" class="btn site-more" id="site-more"><span class="lang-en">Load more</span><span class="lang-zh">加载更多</span><b id="site-more-count"></b></button></div>
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
    body = f'''{header()}
{detail}
{footer()}'''
    return page(site["nameEn"], site["nameZh"], site["summaryEn"], site["summaryZh"],
                body, f'sites/{site["slug"]}/', og_image=f'/assets/og/site-{site["slug"]}.png')

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
    en_cnt, zh_cnt = t("stylesCount", n=len(STYLES))
    en_ph, zh_ph = t("searchStylesPlaceholder")
    en_gv, zh_gv = t("governedTitle"); en_rs, zh_rs = t("researchingLabel")
    cards = "\n".join(style_card(s) for s in STYLES)
    chips = "".join(f"<span>{esc(n)}</span>" for n in STYLES_META.get("researching", []))
    body = f'''{header()}
<main class="wrap">
 <nav class="crumbs">
  <a href="/"><span class="lang-en">{esc(en_b)}</span><span class="lang-zh">{esc(zh_b)}</span></a>
  <span class="crumb-sep">/</span>
  <span class="crumb-cur"><span class="lang-en">{esc(en_sc)}</span><span class="lang-zh">{esc(zh_sc)}</span></span>
 </nav>
 <section class="hero" style="padding-top:32px">
  <h1 class="hero-title" style="font-size:clamp(32px,4.6vw,48px)"><span class="lang-en">{esc(UI["stylesTitle"])}</span><span class="lang-zh hero-title-zh">{esc(UI["stylesTitleZh"])}</span></h1>
  {paras(STYLES_META.get("hubTagline", ""), STYLES_META_ZH.get("hubTagline_zh", ""), "hero-sub")}
  <div class="atlas-note">
   <h2><span class="lang-en">{esc(en_gv)}</span> <span class="lang-zh" style="font-weight:400;font-size:12.5px">{esc(zh_gv)}</span></h2>
   {paras(STYLES_META.get("governedNote", ""), STYLES_META_ZH.get("governedNote_zh", ""), "")}
   <div class="research-chips">{chips}</div>
  </div>
  <div class="controls">
   <div class="search-box">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
    <input id="style-search" type="search" autocomplete="off"
     data-ph-en="{esc(en_ph)}" data-ph-zh="{esc(zh_ph)}" placeholder="{esc(zh_ph)} / {esc(en_ph)}" aria-label="Search styles">
    <kbd class="search-kbd">/</kbd>
   </div>
   <p class="count-note" id="style-count"><span class="lang-en" data-tpl="{esc(UI["stylesCount"])}">{esc(en_cnt)}</span><span class="lang-zh" data-tpl="{esc(UI["stylesCountZh"])}">{esc(zh_cnt)}</span></p>
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
                ent = next((x for x in ENTRIES if x["slug"] == ref), None)
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
    for ref in PM_REFERENCES:
        items.append({
            "id": "reference:" + ref["slug"], "type": "page-reference", "slug": ref["slug"],
            "name": ref["titleEn"], "nameZh": ref["title"], "url": reference_url(ref),
            "summary": ref["summary"],
            "tags": {key: ref[key] for key in ("productTypes", "pageTypes", "layouts", "moods", "states")},
            "scenarios": ref["scenarios"], "structure": ref["structure"],
            "visualTraits": ref["visualTraits"], "prompt": reference_prompt(ref),
            "source": ref["source"]
        })
    for site in SITES:
        items.append({
            "id": "site:" + site["slug"], "type": "site-reference", "slug": site["slug"],
            "name": site["nameEn"], "nameZh": site["nameZh"],
            "url": f'/sites/{site["slug"]}/', "summary": site["summaryZh"],
            "tags": {"category": [site["category"]]}, "prompt": site["summaryZh"],
            "source": {"kind": "external", "label": "awesome-design-md", "license": "MIT"}
        })
    return {
        "schemaVersion": 1,
        "language": "zh-CN",
        "description": "供 AI 和选择导出功能读取的 LearnUI 结构化目录。",
        "taxonomy": PM_TAXONOMY,
        "items": items
    }

def catalog_readme():
    return '''# LearnUI AI 数据入口

优先读取 `catalog.json`。它包含页面参考、知名网站设计规范、UI 元素和视觉风格的统一字段，不需要扫描整个仓库。

- `type=page-reference`：页面级结构、使用场景、状态和视觉说明。
- `type=ui-element`：现有 UI 词典条目和实现 Prompt。
- `type=visual-style`：现有视觉风格和 Style Brief。
- `type=site-reference`：知名网站的设计系统、分类和中文风格解读。
- `taxonomy.json`：页面参考筛选所使用的稳定分类 ID。
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
    write("references/index.html", references_page())
    for ref in PM_REFERENCES:
        write(f'references/{ref["slug"]}/index.html', reference_page(ref))
    write("sources/index.html", sources_page())
    if SITES:
        write("sites/index.html", sites_hub_page())
        for site in SITES:
            write(f'sites/{site["slug"]}/index.html', site_detail_page(site))
    for e in ENTRIES:
        write(f'{e["platform"]}/{e["slug"]}/index.html', entry_page(e))
    for slug in GUIDES:
        write(f"guides/{slug}/index.html", guide_page(slug))
    write("guides/translate/index.html", translate_page())
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
  <p class="hero-desc"><span class="lang-en">This page doesn't exist. Try the dictionary, page references, or the styles atlas.</span>
  <span class="lang-zh">页面不存在。去词典、页面参考或风格图鉴看看。</span></p>
  <p class="hero-desc"><a href="/">Dictionary</a> · <a href="/references/">References</a> · <a href="/styles/">Styles</a></p>
 </section>
</main>
{footer()}''', "404.html"))
    # static assets
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    shutil.copyfile(os.path.join(ROOT, "manifest.webmanifest"), os.path.join(OUT, "manifest.webmanifest"))
    shutil.copyfile(os.path.join(ROOT, "LICENSE"), os.path.join(OUT, "LICENSE.txt"))
    write("assets/demo-i18n.js", "window.DEMO_I18N=" + json.dumps(DEMO_I18N, ensure_ascii=False) + ";")
    write("api/catalog.json", json.dumps(catalog_data(), ensure_ascii=False, indent=2))
    write("api/taxonomy.json", json.dumps(PM_TAXONOMY, ensure_ascii=False, indent=2))
    write("api/demo-i18n.json", json.dumps(DEMO_I18N, ensure_ascii=False, indent=2))
    write("api/README.md", catalog_readme())
    with open(os.path.join(ROOT, "sw.js"), encoding="utf-8") as f:
        sw = f.read()
    version = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    offline_pages = ["/", "/references/", "/sources/", "/styles/"] + \
        [reference_url(ref) for ref in PM_REFERENCES] + \
        (["/sites/"] + [f'/sites/{site["slug"]}/' for site in SITES] +
         [f'/assets/site-thumbs/site-{site["slug"]}.webp' for site in SITES] if SITES else []) + \
        [entry_url(e) for e in ENTRIES] + \
        [style_url(s) for s in STYLES] + \
        [f"/guides/{slug}/" for slug in GUIDES] + ["/guides/translate/"] + \
        [vs_url(a, b) for a, b in vs_pairs()]
    sw = sw.replace("__SW_VERSION__", version)
    sw = sw.replace("__PRECACHE_PAGES__", json.dumps(sorted(set(offline_pages)), ensure_ascii=False))
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
<title>Learn UI PM</title>
<link>{SITE_URL}/</link>
<description>{esc(UI["tagline"])} - bilingual UI dictionary</description>
{"".join(items)}
</channel></rss>''')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    urls = ["/", "/references/", "/sources/"] + \
           [reference_url(ref) for ref in PM_REFERENCES] + \
           (["/sites/"] + [f'/sites/{site["slug"]}/' for site in SITES] if SITES else []) + \
           [f'/{e["platform"]}/{e["slug"]}/' for e in ENTRIES] + \
           [f"/guides/{s}/" for s in GUIDES] + ["/guides/translate/"]
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
