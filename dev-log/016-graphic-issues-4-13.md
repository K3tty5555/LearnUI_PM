# 016 平面设计第 4–13 期：16 个案例，蒙太奇标本修复

## 目标

用户 2026-11-20 发来 11 条小红书笔记，说「这些案例加一下」。其中 1 条（26 个交互动效）进 UI 词典，见 [015](015-hover-effects-26.md)；其余 10 条进平面设计。7 条是视频，下载脚本会跳过，询问后用户拍板：

- 2027 趋势两条视频：**每种风格做一个案例**（共 8 个）。
- 4 条视频教程（霓虹发光、故障风、离解复合 PV、《沉沦在世界树之下》）：先看成品帧再定，看过后**四条全收**。

## 改动

| 期 | 笔记 | 案例 |
|---|---|---|
| 4 | 3-Brushes · 霓虹发光氛围感海报（视频） | `neon-dreamcore`（4 张：MUTTON / COUPLE / CLOUDS / GOOSE） |
| 5 | LiKE品牌设计 · 2027 趋势 0.2（视频） | `trend-neo-fauvism`、`trend-dust-fusion`、`trend-swiss-punk`、`trend-retro-futurism` |
| 6 | 蟹黄糕Design · 2027 趋势前瞻（视频） | `trend-expressive-type`、`trend-neo-folk`、`trend-tactile-material`、`trend-neo-brutalism` |
| 7 | 屿野_YeDesign · 黑白与红 | `red-accent-type`（4 张，首图署名 KAERU） |
| 8 | 章章晴子 · 故障风海报（视频） | `glitch-posters`（明月祈愿 / 城市电脉 / Short Circuit） |
| 9 | 因为 · blue 审美积累 | `blue-bitmap-collage`（3 张） |
| 10 | RICO · TOICO Works｜BISON ENERGY | `bison-energy`（新类型 `brand`；设计方本人发的 3544px 原稿，标 `author`） |
| 11 | 珍妮弗兰克 · 高亮黄大字报 | `street-yellow-type`（3 张笔记图 + Pen 杂志官方封面） |
| 12 | IMageDev · 离解复合 PV 风格化平面（视频） | `arknights-gate-future`（调色后 / 调色前两帧） |
| 13 | 浮白 · 沉沦在世界树之下（视频） | `beneath-the-world-tree`（标本 7 步还原 PS 搭建顺序） |

- 平面设计从 12 个案例、3 期增加到 28 个、13 期。新风格词 9 个，新手法 36 个（合并重复后），新类型 `brand`。
- 新来源类型 `video`（截自设计师本人的视频），图注「截自作者视频」；4 个教程案例改用它（原先写「截自收录笔记」不准确）。`build.py`、`validate-data.py`、`export_originals.py` 同步支持。
- 趋势案例加 `"specimen": "style-demo"`：详情页标本小标题改为「风格示范与拆解」，说明标题自拟、不是看板原作。
- 期次标题去掉了分配表里的「（视频）」备注。
- **蒙太奇标本修复**（上一轮遗留，已上线的缺陷）：标本高 633px，桌面详情页标本区固定 520px，顶部红块和分步按钮被切掉；照片区是整块黑（近黑底上画黑点、点大小跟亮度走反了）。宽度收到 320px；底色改纸色、点按暗度变大。
- `test-graphics-layout.py` 新增：桌面宽度下标本（每个切换视图）必须完整落在 520px 标本区内。修复前对蒙太奇失败（溢出 57px），修复后通过。
- 文档：`docs/graphic-design.md` 新增「第 4–13 期与新规矩」；`add-graphic-case` skill 补视频笔记流程、520px 限制，去掉过时的 `NEW_SLUGS` 一步；README / PRODUCT 数量。`.gitignore` 加 `.claude/worktrees/`。

## 关键决策与踩坑

- **并行做法**：16 个案例 + 11 个 UI 词条分给 7 个助手，各在独立 git worktree 里做（构建脚本固定输出到 `site/`，同一目录并行构建会互相覆盖），主会话写合并脚本 `/tmp/gd-batch/merge.py` 把新增的期次、类型、风格词、手法、案例和文件合回主仓库。
- **第一轮 7 个助手全部中途失败**：2 个是接口并发上限（429），5 个是服务端 502。有进度的从断点续跑；没动手的副本已被自动清理，重新开。之后限制同时最多 3 个，再没出错。
- **分配表的备注被原样写进数据**：我给助手的期次表在标题后写了「（视频）」，助手照抄进了 title。合并时清掉。以后给助手的表格，备注要和字段分开写。
- **合并去重**：三对同义手法合并（手绘定制字→手写字标题、材质颗粒→颗粒噪点、切片错位字→横切错位）；「网格外露」等几个被两个助手各定义了一遍，保留先合入的那份。
- **蒙太奇的问题是助手顺带发现的**：现有平面设计测试只查图片比例和标注落点，不查标本是否超出固定高的标本区，所以 013 上线时没被拦住。
- 霓虹那组的手写字（Dream core 等）用系统手写体近似，Linux 上会换成别的手写字体。

## 验证

- `validate-data`；`build` 319 页；`verify-site` 321 页 / 270 目录项；`verify-performance`：通过。
- `test-graphics-layout`（Chromium + WebKit）：972 项全部通过（含新的 520px 检查）。
- `test-live-demos`：113 个标本挂载、无 JS 错误；`test-catalog-states`、`test-logo-layout`、`test-text-width`、`test-mobile-language`：通过。
- 16 个新案例逐个截「原图 vs 标本」对照图人工核对（`/tmp/lstate/rev*.png`）；蒙太奇修复前后截图核对。
- 各助手自己的 2000 / 1440 / 390 截图在 `/tmp/gd-batch/shots/`。

## 下一步

- 待用户拍板的几处（见本轮汇报）：Pen 杂志封面是否留在第 11 期案例里；第 9 期 RM 曲目表是否单独收；第 12 期 AI 2 倍图会把信号干扰纹抹成波纹，要不要去掉 2 倍图；第 12 期是否加第 3 张「平面构成完成」帧；`glitch-posters` 是否保留「酸性图形」风格词；BISON 的风格词偏勉强。
- 本轮已在本地提交，推送等用户同意。
