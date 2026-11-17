# 002 Logo 图鉴栏目

## 目标

用户 2026-11-17 给出小红书视频《好用的设计网站之LOGO/图标》（作者「李李说设计（大学陪跑）」，2026-11-13 发布，52 秒），要求「加一个 logo 的栏目，首期 logo 从这拿」。

视频逐个介绍 9 个网站：IconPark、Logopond、Iconfinder、iOS Icon Gallery、Reeoo App Icon Gallery、Remix Icon、iconfont、Logobook、Icônes。网站名来自画面字幕，用途与「适合谁」来自口播转写。

「栏目做成什么」有三种理解，问了用户。用户选择「Logo 图鉴 + 资源站」（用户拍板 2026-11-17），定位写入 [docs/logos.md](../docs/logos.md)。

## 改动

在 001（a1158fc）之后单独提交。

- `data/logos.json`：7 种 logo 类型（文字标、字母标、具象图形标、抽象图形标、吉祥物标、组合标、徽章标）、4 种用途、9 个样本。每个样本有中英双语的构成解读、三条拆解、网站用途、适合谁、费用与授权、给 AI 的 prompt；与视频不一致处有 `note`。
- `assets/logos/*.webp`：9 个 logo，每个 3–29 KB。
- `build.py`：
  - 新页面 `/logos/`（类型按钮筛选 + 用途下拉 + 搜索 + 类型词汇表）和 9 个详情页（浅/深底展示、16/32/64px 小尺寸测试、类型说明、拆解、网站档案、prompt、同类推荐、复制 Markdown、图片来源）。
  - 侧栏导航加「Logo 图鉴」。
  - 新类型 `logo-reference` 写入 `api/catalog.json`，因此 ⌘K 全库搜索、「加入参考」和参考集导出自动支持 logo。
  - 加入 sitemap，「来源与许可证」页加 Logo 图鉴一节。
- `assets/site.js`：logo 筛选（支持 `?type=&use=&q=` 深链）、导航高亮、`/` 聚焦搜索、参考集与全库搜索里的类型名称；参考集中、英文名相同时不再显示成「Remix Icon / Remix Icon」。
- `assets/workspace.css`：栏目样式与 760px 以下手机布局。
- `scripts/validate-data.py`：新增 logo 数据校验（类型/用途 ID、双语字段成对、至少两条拆解、图片文件存在、slug 唯一）。
- `docs/logos.md`（新）、`README.md`、`PRODUCT.md`：栏目说明与数量，静态页 264 → 274。

## 关键决策与踩坑

- **视频里有三处与现状不符，以现状为准并在卡片上说明。**
  - Iconfinder：curl 访问 iconfinder.com 返回 301 到 freepik.com/icons。查证后确认：Freepik 2022 年收购 Iconfinder，2026-04-28 更名为 Magnific（[Wikipedia](https://en.wikipedia.org/wiki/Magnific)）。视频里给 Iconfinder 配的「M」是 Magnific 的新标志。卡片标题写「Iconfinder（现并入 Magnific）」，并说明了来龙去脉。
  - Logobook：视频里的皇冠「b」在 logobook.com 首页 HTML 中是 `object/crowns/` 分类的缩略图 `crowns.svg`，属于档案里别人的商标。改用该站页头的官方 `logomark.svg`（书本 + 地球 + L）。
  - Remix Icon：视频说「免费可商用」。npm 元数据写 Apache-2.0，但包内 `License` 文件已是「Remix Icon License v1.0，2026 年 1 月」，明确禁止用作 logo、商标、App 图标，禁止当图标包单独售卖。这个限制和 logo 栏目直接相关，写进了卡片。
- **logo 图片的来源与处理。** 每个都取自网站自己发布的文件：favicon、apple-touch-icon、页头 logo、logomark。
  - 下载放在独立临时目录，SVG 先确认不含 script，再用无网络的浏览器页面渲染成 PNG，最后转 WebP 入库。页面不直接引用第三方 SVG。
  - 详情页底部链接原始文件地址，并声明商标归属。
- **取图时遇到的问题：**
  - Logopond 的 logo 是 CSS 背景图，从 `overrides.css` 里找到 `logo-head-new.png`。只有 191px 宽，没有 2x 版本，所以卡片上略软。
  - iOS Icon Gallery 的 `favicon.ico` 第一次下载被截断（PIL 报 truncated），连接多次返回 000；重试 `assets/images/favicon-ios.ico` 后拿到含 256px 的完整文件。
  - Icônes 的 `favicon.svg` 是白色（给深色模式用），改用 `favicon-dark.svg`。
  - Playwright 打开 logopond.com 超时（curl 正常），改为从 HTML/CSS 找文件地址直接下载。
- **数字只写能核实的。** IconPark、Remix Icon 的图标总数没有拿到可靠来源，不写数字。Icônes 的视频原话是「几十个图标库」，但 Iconify 的 npm 描述是「Hundreds of open source icon sets」，按后者写「上百个」。
- **样式踩坑：** 详情页沿用 `.reference-title` 后标题变得很小——那条规则把内部所有 span 缩到 0.42em，而标题全部包在语言 span 里；改用自己的 `.logo-title`。类型标签放在 `.reference-tags` 里同样被内层 span 样式覆盖，出现白底白字，改用 `.logo-card-tags` 容器。两处都是截图发现的。
- 首期样本里没有「文字标」，筛选按钮保留并置灰，词汇表标「首期暂无样本」。

## 验证

本机自动化，均实际运行：

- `python3 scripts/validate-data.py`：通过。故意把一个类型改成 `wordmarkx`、一张图改成不存在的文件，校验报出这两处错误并以 1 退出；恢复后通过。
- `python3 build.py`：274 页。`verify-site.py site`：276 个 HTML、224 个目录入口通过。`verify-performance.py site`：预算通过。
- CI 等价流程（`prepare-pages.py --base /LearnUI_PM` → `verify-site.py --base` → `test-live-demos.py`）：通过，84 个标本、无 JS 错误。
- Playwright 专项（Chromium）：
  - 按类型筛选（字母标 → 2 个）、叠加用途、重置、中文搜索「阿里」、深链 `?type=mascot` 均正确。
  - 详情页「加入参考」后计数为 1，参考集列表显示「Logo 图鉴」类型；⌘K 搜「logobook」第一条命中。
  - 390px 手机端栏目页与详情页无横向溢出。
  - 在 `/LearnUI_PM/` 前缀下导航高亮、筛选、9 张图片加载均正常。
- 截图核对了桌面栏目页、两个详情页、手机栏目页与详情页。

证据边界：网站现状（跳转、授权文件）是 2026-11-17 的抓取结果，日后可能变化；Safari 未测。

## 下一步

- 待用户：确认 Iconfinder、Logobook 两处与视频不同的处理是否接受。
- 后续期次可补「文字标」样本。新样本按 `docs/logos.md` 的规则取图、核实授权。
- 2026-11-17 用户要求提交并推送到 main，由 GitHub Pages 工作流自动发布。
