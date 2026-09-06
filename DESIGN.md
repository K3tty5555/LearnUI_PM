---
name: Learn UI PM
description: 安静、可操作的设计参考工作库
colors:
  bg: "#f7f8f5"
  bg-2: "#eef1eb"
  fill: "#e9ede5"
  fg: "#232c25"
  gray-700: "#3e4840"
  gray-600: "#526055"
  gray-500: "#627064"
  gray-400: "#687369"
  line: "#dfe5db"
  line-strong: "#bac5b6"
  blue: "#326044"
  blue-soft: "#e1edda"
  ring: "#b9d0ae"
  accent: "#d9ebbd"
  sidebar-surface: "#f0f3ec"
  white: "#ffffff"
  primary-hover: "#284e36"
typography:
  display:
    fontFamily: "Geist, -apple-system, \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", \"Noto Sans SC\", sans-serif"
    fontSize: "clamp(36px, 3.9vw, 57px)"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-.035em"
  headline:
    fontFamily: "Geist, -apple-system, \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", \"Noto Sans SC\", sans-serif"
    fontSize: "clamp(32px, 3.6vw, 48px)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-.035em"
  title:
    fontFamily: "Geist, -apple-system, \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", \"Noto Sans SC\", sans-serif"
    fontSize: "21px"
    fontWeight: 600
    letterSpacing: "-.025em"
  body:
    fontFamily: "Geist, -apple-system, \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", \"Noto Sans SC\", sans-serif"
    fontSize: "15px"
    lineHeight: 1.7
  label:
    fontFamily: "Geist, -apple-system, \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", \"Noto Sans SC\", sans-serif"
    fontSize: "12px"
  code:
    fontFamily: "Geist Mono, ui-monospace, \"SF Mono\", Menlo, monospace"
    fontSize: "12px"
    lineHeight: 1.75
  count:
    fontFamily: "Geist Mono, ui-monospace, \"SF Mono\", Menlo, monospace"
    fontSize: "11px"
rounded:
  label: "4px"
  segment: "5px"
  segment-track: "7px"
  control: "8px"
  surface: "12px"
  command: "13px"
  dialog: "16px"
spacing:
  tight: "8px"
  control: "12px"
  inset: "20px"
  panel: "24px"
  section: "42px"
  gutter: "48px"
components:
  button-primary:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    padding: "0 18px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.white}"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.fg}"
    rounded: "{rounded.control}"
    padding: "0 14px"
    height: "40px"
  input-search:
    backgroundColor: "{colors.white}"
    textColor: "{colors.fg}"
    rounded: "{rounded.control}"
    padding: "0 12px"
    height: "44px"
  nav-current:
    backgroundColor: "{colors.accent}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
  filter-active:
    backgroundColor: "{colors.white}"
    textColor: "{colors.fg}"
    rounded: "{rounded.segment}"
    padding: "0 12px"
  reference-tag:
    textColor: "{colors.gray-600}"
    rounded: "{rounded.label}"
    padding: "3px 7px"
  specimen-card:
    rounded: "{rounded.surface}"
    height: "190px"
  command-surface:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.command}"
    padding: "6px"
  project-brief:
    backgroundColor: "{colors.white}"
    textColor: "{colors.fg}"
    rounded: "{rounded.control}"
    padding: "12px"
---

# Design System: Learn UI PM

## Overview

**Creative North Star: "设计参考工作库"**

以「设计参考工作库」为视觉方向：浅纸色工作面、鼠尾草色导航、深墨文字与森林绿操作色。界面保持清晰、安静的工具密度，用可辨认的标本、准确名称和连续操作帮助用户把参考组织成设计说明。

本规范管理 Learn UI PM 的导航、目录、阅读区、搜索和参考集。品牌与视觉风格标本保留各自字体、色彩和形状；具体品牌页面规范优先于该品牌 DESIGN.md，再使用通用标本容器规则。来源中的品牌规范不改变本站外壳。实际样式以 assets/site.css 的基础规则及其后加载的 assets/workspace.css 覆盖为准。

**Key Characteristics:**

- 纸色平面与细线分组，层级清楚。
- 持续可见的导航与参考集入口。
- 标本先行，标题和说明紧随其后。
- 阅读文字使用无衬线字体，代码与技术标识保留等宽。

## Colors

色板偏向浅纸、灰绿与森林绿，正文和标本保持最强辨识度。上方 frontmatter 记录实际颜色；保留代码中的 `blue` 命名是为了对应既有变量，其现值承担森林绿功能色。

### Primary

- **森林绿（blue）**：主按钮、链接、焦点轮廓与参考集计数；主按钮悬停使用 primary-hover。
- **浅叶绿（blue-soft）**：搜索结果悬停与焦点、搜索文字标记、选中筛选背景。
- **浅黄绿（accent）**：当前导航与文本选区，帮助定位当前工作位置。
- **柔和绿环（ring）**：保留给引用该变量的控件焦点辅助色；站点通用焦点使用森林绿轮廓。

### Neutral

- **浅纸（bg）与灰绿纸（bg-2）**：页面、抽屉及辅助工作面。
- **鼠尾草导航（sidebar-surface）**：桌面侧栏与移动页眉。
- **柔灰绿（fill）**：次要控件悬停填充。
- **墨绿（fg）**：标题、正文和明确操作名称。gray-700 至 gray-400 分别承接强调说明、次级正文、辅助文字与占位提示。
- **细线（line）与强调线（line-strong）**：分区边界、输入边框与必要的结构强调。
- **白色（white）**：按钮、搜索输入、选中分段和首页命令标本。

**The Scope Rule.** 森林绿与纸色只约束站点外壳；品牌和视觉风格演示遵循自己的设计规范。

## Typography

**Display Font:** Geist，自托管可变字体；中文回退到系统中文字体栈。
**Body Font:** 同一无衬线栈，中文默认，支持英文和中英对照。
**Label/Mono Font:** Geist Mono，自托管；代码、API 符号、术语技术标识和计数使用等宽字体，常规控件标签使用 Geist。

**Character:** 用字重、紧凑标题与宽松段落建立工具和阅读层级。两种字体均使用 font-display: swap；阅读模式持久化，对照文本纵向排列。

### Hierarchy

- **Display**：首页介绍主标题，桌面使用 frontmatter 的弹性尺寸；中等宽度为（40px），手机为（38px / 1.3）。
- **Headline**：栏目标题；手机为（34px / 1.3）。详情标题使用（clamp(28px, 3.6vw, 40px) / 1.3）。
- **Title**：目录区标题；卡片标题桌面为（14px），手机为（15px）。
- **Body**：基础正文使用 frontmatter 的 body；说明段落通常为（13–14px / 1.75–1.9），详情直接段落和列表限制为（75ch）。提示词及复制说明为（13px / 1.9）。
- **Label**：常规按钮和搜索为（12px），辅助标签为（10–11px）；不把全部标签改成大写等宽文本。

**The Reading Rule.** 自然语言说明、项目目标和提示词使用正文无衬线字体；等宽字体承担代码、计数和技术标识，不成为大段阅读文本的默认字体。

## Layout

桌面采用固定左侧导航（224px）和右侧工作区，工作区宽度扣除侧栏、最大（1480px），两侧内边距（48px）。大于等于（1700px）时，工作区在剩余空间内居中。首页介绍与真实命令标本分成两列，下面是三项文字快捷入口，再进入搜索、筛选和标本网格。

目录默认三列，间距为（30px 22px）；宽度不超过（1200px）时改为两列，侧栏收至（200px），内容边距为（30px）。在（761–900px）之间侧栏为（184px），首页介绍改为上下排列，页面参考网格为单列。页面参考桌面另有（170px）筛选栏；中间宽度收至（135px）。

不超过（760px）时变为粘性双行页眉：首行依次保留标识、语言选择、搜索和参考集计数，第二行横向滚动展示全部栏目。隐藏桌面导航图标与计数，对照模式的第二行导航只显示英文标签。工作区单列、边距（20px），搜索独占一行，其余筛选和动作换行。页面参考筛选组变两列，详情内容变单列。移动锚点滚动预留（124px）页眉空间。

详情阅读区使用有限行长，区段间距（42px），常规正文区最大（900px）。目录标本默认高（190px），品牌目录为（205px），页面参考为（230px）；手机分别为（218px）、（218px）和（250px）。页面参考详情舞台桌面为（500px），手机为（440px），内部可滚动并直接操作。

## Elevation & Depth

默认靠背景明度、细边框和留白表达结构。导航是不透明工作面，明确关闭 backdrop-filter。阴影集中在少数需要离开页面平面的部件，目录卡片悬停只改变背景和边框，不抬升。

### Shadow Vocabulary

- **弹层阴影**（`0 18px 64px rgba(31,45,33,.16)`）：全局搜索和参考集抽屉。
- **命令标本阴影**（`0 14px 40px rgba(41,58,34,.10)`）：首页命令操作示例。
- **浮动入口阴影**（`0 6px 24px rgba(31,60,38,.18)`）：有已选内容时出现的参考集入口。

**The Surface Rule.** 目录标本静止时不加阴影；阴影用于命令标本、浮动参考集入口和覆盖内容的弹层。

## Shapes

圆角服务可操作性：小标签使用 label，分段内部使用 segment，按钮、输入和导航项使用 control，标本与复制块使用 surface，命令面板和全局搜索使用更大的专用圆角。常规边框为（1px），主要分组使用横向细线。抽屉贴右侧并贯穿视口高度，不画成居中卡片；手机铺满视口宽度。线性 SVG 图标沿用圆端线条，通常为（18px / 1.6px stroke），避免引入另一套装饰图形。

## Components

### Buttons

直接、安静的工具按钮。主按钮森林绿底白字，次按钮白底墨字细边框。悬停强化边框或主色，按下轻缩放（0.97）；一般颜色状态过渡（120ms），按下过渡（60ms）。禁用态透明度（.45）并使用不可操作指针。通用键盘焦点为森林绿（2px）轮廓、偏移（4px）。

### Chips

筛选与语言控件使用灰绿轨道、白色选中段；筛选按钮同步 aria-pressed。参考标签是小圆角文字标记，灰绿底、次级墨字。加入参考有独立按钮，选中时出现勾号、浅绿填充和「已加入」，同步 aria-pressed；不能只用颜色区别。

### Cards / Containers

标本舞台在上，名称、技术标识和简短说明在下，加入参考按钮独立于详情链接。目录标本使用 inert 和禁用指针事件的预览容器：内部演示按钮不进入 Tab 顺序，也不截获整卡导航。进入详情后再开放相应演示交互。品牌、风格标本保留独立外观；品牌复现说明明确区分演示内容与品牌事实。

### Inputs / Fields

目录搜索为白色细边框输入框，聚焦时边框变森林绿，无额外光晕。保留原生搜索清除按钮。项目目标是带可见标签的多行白色输入框，可纵向调整，高度上限（160px）；说明它是选填且随导出一起写入。复制成功和失败、加载与空结果通过状态文字反馈。

### Navigation

桌面左栏从标识、全局搜索到五个栏目，再到参考集；语言切换与来源链接位于底部。导航当前项浅黄绿填充、深绿文字，悬停为低对比灰绿。移动使用 Layout 所述双行结构，语言选择与搜索始终可达。跳转到内容链接在键盘聚焦时出现，当前栏目同时设置 aria-current。

### Command Search

首页命令标本包含真实栏目跳转、全局搜索和参考集入口。全局搜索用原生 dialog 展示，最大宽（600px），按 Cmd/Ctrl+K 打开或关闭，输入后跨组件、风格、品牌与页面搜索。上下箭头移动结果焦点，Enter 打开，Esc 关闭；显示结果总数，最多列出（30）条，并提示缩小范围。鼠标和触摸均可直接打开结果，遮罩外点击关闭；加载失败有明确反馈。

### Collection & Export

侧栏入口始终可用，有选择时额外显示浮动入口。参考集是最大宽（480px）、高（100dvh）的右侧原生 dialog；手机全宽。列表独立滚动，项目目标与操作区排在后面，空列表隐藏以保留空间。集合与项目目标存储在本地；跨页面保留，集合支持跨标签页同步。用户可混合加入四类参考、移除单项或清空，复制 Markdown 或下载 JSON；两种导出均包含项目目标，空集禁用导出。空态提供解释和浏览页面参考入口。

抽屉入场为（240ms），从右侧（32px）位移并淡入，采用 cubic-bezier(0.23, 1, 0.32, 1)。减少动态效果偏好下取消此动画和顺滑滚动，全局过渡及动画时长缩至（.01ms）、动画只播放一次。

### Detail Specimen States

页面参考详情用显式状态按钮切换对应面板。按钮可点击、触摸和键盘操作；桌面最小高度（36px），手机（40px），移动工具条允许换行。详情演示框恢复指针事件并支持内部滚动，目录预览继续保持 inert。此处记录外壳的交互可达性，不替换标本自己的视觉语言。

## Do's and Don'ts

### Do:

- Do 延续纸色工作面、森林绿操作和浅黄绿当前位置，保持细线与留白的分组方式。
- Do 让标本卡链接、加入参考按钮和详情状态控制各自承担明确操作，并保留键盘可达性。
- Do 让手机首行保留语言、搜索与参考集入口，第二行保留可横向滚动的全部栏目。
- Do 在减少动态效果模式下保留所有功能，同时取消抽屉入场和顺滑滚动。
- Do 将项目目标与已选参考一起导出，保留清晰的空态、加载失败与复制结果反馈。

### Don't:

- Don't 恢复站点外壳的玻璃模糊、折射背景或大面积装饰光晕。
- Don't 把本规范的颜色和字体强加给品牌、风格演示，或把品牌演示规范扩散到站点导航。
- Don't 让目录预览内部控件抢走卡片链接的点击或键盘焦点。
- Don't 用 hover 作为页面参考详情切换状态的唯一入口。
- Don't 把所有容器都做成悬浮卡片，或用等宽字堆叠自然语言说明。
