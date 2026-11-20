# 009 移除术语对照与页面参考两个栏目

## 目标

用户 2026-11-18 拍板：

1. **术语对照（/guides/translate/）去掉**：63 行 AppKit/SwiftUI 映射表是上游 LearnUI 的遗留内容，服务 Mac 开发者，与本站「看真实作品学设计」无关。
2. **页面参考（/references/）去掉**：用户判断「定位有点尴尬」——12 个虚构模板页夹在「学词汇」（词条、风格）和「看真东西」（网站、Logo、平面设计）之间两头不靠。
3. 首页原来指向页面参考的入口**换成平面设计**（用户明确：平面设计会经常补充案例）。

## 改动

- **build.py**：删 `TABLE`/`PM_*` 数据载入、`translate_page()`（约 58 行）与整个 references 段（`reference_url`/`pm_labels*`/`reference_prompt*`/`reference_markdown`/`reference_card`/`references_page`/`reference_page`，约 178 行）；导航从 7 项减到 5 项；首页 hero 主按钮和命令面板入口改指 `/graphics/`（文案「看平面设计案例」）、快捷卡「想搭页面」改「想看案例（平面设计）」；参考集空态 CTA 与文案改口径；catalog 删 `page-reference` 条目和 `taxonomy` 字段、不再写 `api/taxonomy.json`；sitemap/sw 预缓存/404 页/manifest 描述同步；来源页新增「已移除的栏目」一节记录本次拍板与理由。
- **assets/site.js**：删页面参考筛选、PM 标本状态切换、术语表筛选三段；`/` 快捷键输入框清单和导航高亮去掉两个页面的 id；导出与 ⌘K 的类型标签去掉 page-reference。
- **assets/site.css / workspace.css**：删 `.translate-*`、`.reference-browser/-filters/-grid/-card/-detail-grid` 等规则；保留共用类（`.api-table`、`.table-scroll`、`.reference-title` 来源页在用、`.reference-detail-actions` Logo/平面设计详情在用）。
- **数据与文件删除**：`data/pm/`、`demos/pm/`、`data/translate-table.json`、`data/zh/translate-table-zh.json`、`assets/reference-demos.css`、`assets/demo-thumbs/pm-*.webp`（24 张）、`docs/assets/translate-table.png`。git 历史可找回。
- **脚本**：`validate-data.py` 的 main() 不再校验 pm 数据；`verify-performance.py` 预算页换 `graphics/index.html`、预览计数去掉 page-reference。
- **文档**：README（定位段重写、目录树、构建数 305→291、特性表截图换成平面设计栏目截图）、PRODUCT.md、DESIGN.md、manifest 描述。

## 关键决策与踩坑

- **保留共用 CSS 类**：`.reference-title`、`.reference-detail-actions` 名字里带 reference 但被来源页、Logo 和平面设计详情页共用，不能顺手删——删前逐类 grep build.py 确认。
- **性能脚本的隐式依赖**：`verify-performance.py` 把 `references/index.html` 写死在预算清单里、预览计数含 page-reference，删栏目后两处都要改，否则误报。
- ⌘K 目录数据在 `file://` 下 fetch 不出来（Chromium 限制），验收要走本地 HTTP 服务，不然会误判「搜索失效」。

## 验证

- `python3 build.py`（291 页，较此前少 14 页 = 13 个 references 页 + 1 个 translate 页）+ `verify-site.py`（293 页 242 目录条目）+ `verify-performance.py` + `test-graphics-layout.py`（219 项）+ `test-live-demos.py` 全过；`node --check` site.js 语法通过。
- Playwright（本地 HTTP）：导航 5 项（UI 元素 102 / 知名网站 74 / Logo 10 / 平面设计 11 / 视觉风格 45）；⌘K 搜「页面参考」0 结果、「构成主义」2 个、「Y2K」2 个；`site/references/` 目录已不存在（file 404）；首页截图确认主按钮、命令面板、快捷卡都指向平面设计。
- 全站 grep 无残留 `/references/`、`/guides/translate` 链接（来源页「已移除的栏目」说明文字除外，属有意保留）。

## 追加（用户拍板：移除中英「对照」阅读模式）

对照模式下中英并排显示，所有双语文案都要兼顾并排排版，美化压力大。用户决定只留中/英一键切换（2026-11-18）。改动：页眉切换器和手机下拉去掉「对照」项；`site.js` 的 `mode()` 把历史遗留的 `bilingual` 偏好归一到中文；`<head>` 内联探测脚本同步；搜索框占位符不再拼双语；`ui.json` 删 `bilingual` 键；README 阅读模式说明改两种。页面里的双语数据结构（lang-zh/lang-en）不动，只是不再并排显示。验证：构建 + 链接核验 + 动效标本 + 布局 + 性能全过；Playwright 实测切换器只剩中文/EN 两项、存量为 bilingual 的偏好回落中文、中英切换显示隐藏正常。

## 下一步（已并入上文各节）
- 仓库名 LearnUI_PM 的「PM」已成历史含义，是否改名由用户以后决定。（用户 2026-11-20 拍板：不改名，没有必要）
- 平面设计是用户会持续补充的栏目，首页入口已就位；第 3 期收录时走 `.claude/skills/add-graphic-case`。

## 追加（用户看预览后：平面设计首页删期数来源文案）

栏目页 hero 里那三条「第 N 期 · N 个案例，来自小红书……」和版权说明列表整体删除：期数是收录台账，不该占学习页版面；版权与删除说明在「来源与许可证」页和每个详情页的署名行都有，不损失法律声明。`graphics.json` 的 `issues` 数据保留（详情页署名还要用），Logo 图鉴的同款列表 2026-11-19 也按同理由移除（期数行 + 「logo 都是各网站自己的标志」说明，`.logo-issue` CSS 清理，数据保留）。随后用户又把 hero 介绍压缩成一句「寻找视觉之美」（英文 In search of visual beauty）。同期首页文案改版：主标题改「寻之于目，识美于此」（EN: Seek with your eyes. Know beauty here.），副文案改用户自拟的「察有形之美，汇万象之观」（EN: Behold beauty in form. Gather views of everything.），知名网站副文案改「承旧识，开新观」，首页词条区「点开标本」改「点开案例」、元素条数说明行删除。另应用户反馈处理列表卡上的「加入参考」按钮：我先误删了首页与平面设计两处，用户澄清红框指的是首页且要求**两个列表都加回来**——已全部恢复（首页 102、平面设计 11，DOM 验证）。另应用户反馈处理首页 hero：先按「占位文字去掉」把右侧 command palette 演示块整个删了并改为居中封面——用户澄清要删的只是**装饰文案**（试试看 / 一个熟悉的界面…… / Command palette 词条说明 / 两个介绍按钮 / 双语小字），**命令面板本身**（你想做什么搜索 + 看平面设计案例 / 探索一种视觉风格 / 打开我的参考集）要保留。已恢复两栏布局与面板（玻璃质感 CSS 一并恢复），左侧只留标题与副文案。期间还发现用户浏览器反复看到旧版本是缓存所致（本地 http.server 无 no-cache 头），已建议无痕窗口或带参 URL 验证；后续可考虑 no-cache 预览脚本。验证：重建 + 链接核验通过；DOM 确认面板 4 项俱在、装饰文案 0 残留；桌面与 390px 截图确认两栏/单栏布局正常。
