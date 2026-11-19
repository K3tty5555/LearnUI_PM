# 008 平面设计关键词分层：列表页挂宏观风格词

## 目标

用户看列表页「手法词汇」后提出疑问：这些词好像不全是设计类术语。讨论后理清两层模型——**宏观层**是主义/流派/风格词（用户举例：国际主义、解构主义、包豪斯），**微观层**是单张画面的手法（斜线分区、图文穿插）——并拍板（2026-11-18）：

1. 列表页关键词改展示宏观层风格词，详情页继续拆微观层手法（现状保留）。
2. 删掉列表页「手法词汇」版块。
3. 列表页瀑布流：发现 CSS 里本就是多列瀑布流（`workspace.css` `.graphics-grid`），无需开发。
4. 与风格图谱解耦：图谱针对网站/UI 风格，平面设计五花八门；风格词自由维护。

决策细节（含为什么解耦）写在 `docs/graphic-design.md`「关键词分层」一节。

## 改动

- **数据 `data/graphics.json`**：新增顶层 `styleTags` 词汇表（15 词，`{id, name, nameZh}`）；案例的 `styles`（图谱 slug）字段删除，换成 `styleTags: [id...]`；`techniques` 全保留。
- **词汇表经 web 检索核实**：各家工作室（Buck、Worship、Tendril）自述只用「透视网格」「粗几何」「可延展系统」这类描述词，没人自称某主义 → 电竞主视觉没有教科书风格名，自由文本描述词是对的主线。真风格名只在呼应属实/社区也这么归类时用：构成主义（Valorant 社区归类）、Y2K（FNCS 铬片反光+倾斜是教科书式 Y2K 回潮）、瑞士风格+酸性图形（reionization 原作者自己拆的）。弃用原拟「未来主义」（查证无人这么叫，VCT 改挂「粗几何海报」）；「工业硬朗」按社区通用词改成「战术工业风」（tactical）。
- **`build.py`**：`GRAPHIC_STYLES` 字典；卡片 `data-techs`→`data-styles`、hay 吃风格词、卡片标签渲染风格词（纯文本）；hub 手法下拉→风格下拉（`?style=`）、删手法词汇版块、hero/搜索占位/无结果文案改口径；详情页图谱链接删除、手法标签去链接加 `title` 悬停解释（词汇表删除后的学习入口）；复制 Markdown 加「风格」行；⌘K 目录条目加 `styles`（tags 与可搜索字段都吃）。
- **`assets/site.js`**：hub 筛选读 `#graphic-style` + `data-styles`，URL 参数 `tech`→`style`（旧参数不兼容，个人站无外部深链）；⌘K 搜索 hay 并入 `styles`/`techniques`。
- **`assets/workspace.css`**：`.gd-style` 标签样式（底色区分）、详情页 `.gd-tech` 光标改 help。
- **`scripts/validate-data.py`**：删图谱 ID 校验，新增 styleTags 校验（词汇表条目 id/name/nameZh 齐全、案例 styleTags 非空且 id 都在词汇表）。
- 文档与流程：`docs/graphic-design.md` 新增「关键词分层」节、「和现有栏目的关系」改解耦、收录流程第 4 步加风格词；`README.md` 两处措辞；`.claude/skills/add-graphic-case` 同步两条规矩。

## 关键决策与踩坑

- **词表不是一次写死的**：第一版拟了「未来主义」，检索后弃用。教训：给真实作品挂风格名，先查官方/工作室怎么自述、社区怎么归类，别从艺术史倒推。
- **`?tech=` 深链直接废弃**：dev-log 006 曾用 `?tech=` 验证筛选，本次改为 `?style=` 后旧链接自然失效，属预期。
- 编辑 build.py 大块 HTML 模板时一次 Edit 失配（`{esc(iss["author"])}` 抄错一处），拆成小块逐段替换解决；后续改模板先重读再编辑。

## 验证

- `python3 scripts/validate-data.py` 通过；反例（故意写 `not-a-real-style`）报 `styleTags missing or unknown` 并退出 1，恢复后通过。
- `python3 build.py`（305 页）+ `python3 scripts/verify-site.py site`（307 页 254 目标）通过。
- `python3 scripts/test-graphics-layout.py site`：219 项布局检查全过（三宽度无横向溢出、图片比例、2 倍图加载）。
- Playwright 截图 + DOM 对账：列表页瀑布流、卡片挂风格词；选「构成主义」→ 显示 1/11、唯一可见卡片是 VCT 2023（DOM 标签 `构成主义Constructivism粗几何海报Bold geometric`，截图一致）；搜「Y2K」→ 1/11 FNCS；详情页 VCT 标签行 = 类型 + 构成主义/粗几何海报 + 3 个手法标签（`title` 属性带定义，grep 确认）；390px 单列正常；⌘K 目录 11 条 graphic 条目都带 `styles`，按构成主义能命中 VCT。
- 中途一次截图描述误判（把滤镜后唯一卡片认成 THE FINALS），DOM 调试 + 重拍对账确认是误读，行为本身正确。

## 下一步

- 案例多了以后观察 `styleTags` 词汇表是否会失控（目前 15 词），必要时在 docs 里补「何时合并近义词」的规矩。
- 包装类型还没有案例，`packaging` 类型按钮置灰，等第 3 期收录。

## 追加（用户看预览后反馈：筛选下拉没做视觉优化）

原生 `<select>` 的弹出菜单没法用 CSS 定制，箭头和菜单都是浏览器默认样式，和站里的玻璃质感不搭。改法：`site.js` 末尾新增通用增强——把 `.site-filter-select select` 换成「按钮 + 玻璃弹出菜单」的自定义下拉（原生 select 隐藏但保留，选中后写回 value 并派发 `change`，三个栏目的既有筛选逻辑零改动），支持键盘（方向键 / 回车 / Esc / Home / End）和 ARIA（listbox / option / aria-expanded）。同一控件在三个栏目共用：平面设计「风格」、Logo「用途」、知名网站「行业 + 设计气质」，一处修好四下场生效。

连带改动：三个栏目的「重置筛选」按钮原来直接清 select value 不派发事件，会和新下拉的字面不同步，已补 `dispatchEvent(new Event("change"))`。

验证：构建 + 307 页链接核验 + 性能预算 + 219 项布局检查 + 动效标本测试全过；Playwright 实测——图形页选「大字排版」计数变 3/11 且按钮字面跟着变、重置后回到「全部风格」、Logo 和网站页两个下拉正常、390px 打开菜单无横向溢出；键盘方向键+回车可选中。
