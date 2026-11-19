---
name: add-graphic-case
description: 把用户发来的平面设计案例（小红书笔记链接或图片：海报、游戏平面设计、包装）收录进 LearnUI PM 的「平面设计」栏目：下载原图、裁出原作、找官方大图、写案例数据、导出原图与 AI 2 倍图、写还原标本、跑检查和截图。用户发来平面设计 / 海报 / 游戏视觉 / 包装案例并说「加一下」「收录」「放进平面设计」时使用。
---

# 收录平面设计案例

完整说明和决策背景在 `docs/graphic-design.md`（「策略调整」「命名规则」「收录流程」三节），动手前先读。下面是执行清单。

## 先确认的规矩（用户拍板 2026-11-18）

- **尽量还原原作**：原名、原字标、原构图；详情页先放原图，再放代码还原。署名原作设计方、年份、图源，链接收录笔记；页面已有「权利人要求即删除」说明。
- **横竖混排**：不要把竖图裁成横图。第一张图决定详情页版式（竖图左右分栏，横图上下排列）。
- **手法名用平实中文**，不用「出血」这类行业黑话；新手法先查 `data/graphics.json` 的 `techniques` 里有没有能复用的。
- **风格关键词是宏观层词**（构成主义、Y2K、瑞士风格这类，2026-11-18 拍板，见 docs「关键词分层」）：从 `styleTags` 词汇表选，没有合适的再加新词（中英双语）；与风格图谱无关，不挂图谱链接。真风格名只在呼应属实、社区也这么归类时用，其余用大白话描述词。
- 第三方原图存仓库外（`~/.local/share/codex-data/xhs-graphic/<批次>/`），只有裁好、署名的图进 `assets/graphics/`。

## 步骤

1. 下载：`~/.local/share/codex-tools/XHS-Downloader/.venv/bin/python scripts/graphics/fetch_xhs_note.py "<链接>" ~/.local/share/codex-data/xhs-graphic/<批次>`。失败就请用户给一条新的完整分享链接。
2. 裁图：`python3 scripts/graphics/crop_originals.py <批次>/download /tmp/<批次>-crops`，**用 Read 打开 contact-sheet.jpg 逐张核对**，把裁片对应到案例。
3. 官方大图：Steam 用 `cdn.cloudflare.steamstatic.com/steam/apps/<appid>/library_600x900_2x.jpg` / `library_hero.jpg`（其他 Steam 域名常超时）；其余搜官方新闻稿和设计方作品集。下载的文件放单独空目录。
4. 数据：在 `data/graphics.json` 加期次（新笔记）和案例，字段照已有案例写全（中英文、`styleTags` 风格关键词、手法、四层拆解、配色、两组提示词、credits、sourceLabel）。
5. 原图：`python3 scripts/graphics/export_originals.py <slug> <图...> [--origin official|author] [--start N]`（`author` = 设计师本人发的原稿），再把 `TODO` 图注补成中英文。官方大图会自动缩出标准版和真实像素的 2 倍图；用了官方 / 设计方的图要填案例的 `sourceUrls`。换图前把现有图和候选图拼成对照图，用 Read 逐张确认是同一张作品、版式一致。
6. 标本：`demos/graphic/<slug>.html`，参考已有标本（如 `the-finals.html` 的多尺寸切换、`capcom-cup-12.html` 的多物料切换）。标记 `data-ov-type` / `data-ov-focus` / `data-ov-space` 和 `.gd-grid`；字号随画面尺寸缩放（ResizeObserver），切换视图时派发 `gd:layout`；支持 `prefers-reduced-motion`；目录卡里的小尺寸用 `@media (max-height:260px)` 处理。能用一个 SVG 按原图坐标（viewBox 等于原图比例）画的就用 SVG，缩放不用写 JS；会切换横竖版的，在 `@media (max-width:760px) and (min-height:261px)` 里给根元素预留最高版式的高度。海报文字放在 `[data-gd-canvas]` 里，网站不会翻译它。
7. 新案例的 slug 加进 `build.py` 的 `NEW_SLUGS`；README / PRODUCT 里的数量跟着改。

## 检查（全部自己跑，不留给用户）

```bash
python3 scripts/validate-data.py
python3 build.py && python3 scripts/verify-site.py site && python3 scripts/verify-performance.py site
python3 scripts/test-graphics-layout.py site --engines chromium,webkit
python3 scripts/test-live-demos.py site
```

- 再用 Playwright 截 2000 / 1440 / 390 宽度的列表页和详情页，Read 图片，**对照原图**看还原度，打开「全部图层」看标注是否落在对的位置。
- 预览：本机 `python3 -m http.server 8000 --directory <仓库绝对路径>/site`，让用户打开 http://localhost:8000/graphics/。
- 写开发日志（`dev-log/`），提交只用显式路径；推送到公网要用户当次明确同意。
