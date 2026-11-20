# 010 站名从 Learn UI PM 改为 Learn UIUX

## 目标

页面参考移除后，「PM」后缀失去所指；用户 2026-11-18 拍板：去掉 PM，站名改为 **Learn UIUX**（更贴合「UI/UX 学习」的实际内容）。

## 改动

- **站内品牌全量替换**（Learn UI PM → Learn UIUX）：`build.py` 的 SITE_NAME、页头 wordmark（`Learn UI` + 徽标式 `UX`，类名 `wordmark-pm` → `wordmark-ux`）、页脚、`<title>` 后缀、RSS 标题、离线页标题、manifest 的 name/short_name、`site.css`/`workspace.css`/`site.js` 头部注释、README 两处标题、DEPLOY 标题。
- **不动的东西（有意）**：
  - `SITE_URL`（build.py:8）仍指向 `https://K3tty5555.github.io/LearnUI_PM/`——这是真实部署地址，仓库没改名前改它会让 canonical/OG/sitemap 指向不存在的 URL；
  - GitHub 仓库名 `LearnUI_PM` 与本地目录名——仓库改名是对外动作（旧链接靠 GitHub 重定向兜底），等用户决定后一并改 SITE_URL、README 链接和 `--base /LearnUI_PM` 测试参数；
  - 图标 `ai-pm-client-circle-64.png`——渐变圆环图，无 PM 字样，仅文件名带 pm，对访客不可见。

## 验证

- 重建（291 页）+ 链接核验通过；构建产物 grep 无 "Learn UI PM" 残留；Playwright 确认页面标题为「… · Learn UIUX」、wordmark 徽标显示 UX。

## 下一步

- **线上地址迁移（用户拍板 2026-11-18）**：站点后续将从 `K3tty5555.github.io/LearnUI_PM/` 迁移到用户自己的公网域名，由另一个任务负责；在那之前不改 `SITE_URL` 和仓库名。迁移时需同步：`build.py` 的 `SITE_URL`、README/DEPLOY 里的链接、`scripts/test-live-demos.py` 的 `--base` 默认值、robots/sitemap 中的绝对地址。（2026-11-20 核对：已完成，见 012 追加）

## 修订（2026-11-19）

用户看页头后拍板：改名后「UX」不再单独用框圈起来。页头 wordmark 改为纯文字 `Learn UIUX`（与原字号字重一致），删除 `workspace.css` 的 `.wordmark-ux` 规则。重建 291 页，Playwright 截图确认一行显示、无框、不溢出。

用户同日拍板：定位已变，首页浏览器标题去掉「这个控件叫什么？」。首页 `<title>` 与 og:title 改为只显示 `Learn UIUX`（`page()` 在标题为空时省略前缀），其他页面仍为「页面名 · Learn UIUX」。

用户同日再拍板：(1) 分享预览图按网站现状重做；(2) 首页简介就用「寻之于目，识美于此」。

- 简介：`data/ui.json` 的 heroSub / heroSubZh 改为「Seek with your eyes. Know beauty here.」/「寻之于目，识美于此。」（英文沿用侧栏已有译法）；不再使用的 heroTitle / heroTitleZh 删除，siteName 同步改为 Learn UIUX。
- 首页分享图 `_home.png`：左侧画当前五个栏目及数量（取 `build.nav_links()`，与侧栏同源，栏目增减或数量变化后重跑 `scripts/gen-og.py --force` 即同步），右侧为站名、「寻之于目，识美于此」、英文与「察有形之美，汇万象之观」。通用图 `_default.png` 用同一版，去掉旧定位的大问号。
- 所有分享图底部站名改为 Learn UIUX（取 `build.SITE_NAME`），重出 191 张；知名网站的 43 张是网站截图、无站名，不受影响。
- 验证：数据检查、重建 291 页、全站链接检查（293 页）通过；构建产物中无「Learn UI PM」「这个控件叫什么」残留；人工看过首页图、通用图和抽查的词条图。
