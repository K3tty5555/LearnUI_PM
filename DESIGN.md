---
name: Learn UI PM
description: 雾白与墨黑的玻璃拟态设计参考工作库
colors:
  bg: "#f7f7f8"
  bg-2: "#ededf0"
  fill: "#e9e9ed"
  fg: "#242428"
  gray-700: "#414148"
  gray-600: "#575760"
  gray-500: "#666670"
  gray-400: "#696973"
  line: "#dddde3"
  line-strong: "#bcbcc5"
  blue: "#242428"
  blue-soft: "#e5e5eb"
  ring: "#bcbcc8"
  accent: "#e1e1e7"
  sidebar-surface: "#efeff3"
  white: "#ffffff"
  glass-navigation: "rgba(249,249,252,.58)"
  glass-command: "rgba(255,255,255,.46)"
  glass-dialog: "rgba(248,248,252,.91)"
  glass-edge: "rgba(255,255,255,.95)"
  primary-hover: "#3b3b43"
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

用户明确选择「雾白、墨黑、玻璃拟态」。保持已有资料库的信息结构，以中性银灰背景、透明表面、边缘高光和柔和阴影建立玻璃质感。站点外壳不使用绿色。品牌、视觉风格和组件标本是被展示的对象，其内部色彩不受外壳配色限制。

唯一实现来源为 assets/site.css 与后加载的 assets/workspace.css；构建时内联共享 CSS 与站点脚本，以减少高延迟网络中的阻塞请求。页面参考详情按需加入 reference-demos.css。

## Colors

背景使用 {colors.bg}，标题、主按钮与主要操作使用 {colors.fg} / {colors.blue}。`blue` 是兼容旧组件的变量名，当前值为墨黑。次级文字使用中性灰；透明白表面从下方的银灰底景获得层次。选中态以明暗、字重、图标和 aria 状态共同表达。

## Typography

Geist 用于拉丁文字，中文使用系统中文无衬线字体。Geist Mono 仅用于代码、数量和技术标识；说明文字与提示词使用无衬线。首页标题 36–57px，移动端 38px；栏目标题 32–48px，移动端 34px。正文 13–15px，正文行高 1.7–1.9，阅读段落不超过 75ch。10–12px 用于辅助签、计数和简短说明，交互控件不依赖微小文字说明其用途。

## Layout

桌面保留 224px 导航分区。侧栏距窗口边缘 14px，实际宽度为分区宽度减 14px，四角 20px。内容水平内边距 48px，最大 1480px。1200px 以下收紧导航和页边距；760px 以下切换为顶部两行导航，内容边距 20px，目录单列。详情页的状态切换在小屏仍然可见，按钮至少 40px 高。

目录使用 118 组中英双语 WebP 预览，真实交互保留在详情页。首页前三张预览内嵌以随 HTML 直接呈现；其它预览在进入视口附近 240px 时加载。图片保留 600×360 的固有尺寸和固定舞台，避免布局跳动。无 JavaScript 时有原生懒加载回退。

## Elevation & Depth

玻璃是一套明确的材料选择：透明白表面、白色细边、内高光、带偏移的软阴影，下方是静止的银灰光照背景。不要使用绿色或彩色背景光。

仅大面积主要玻璃层使用 backdrop-filter：桌面导航 18px、首页命令面板 16px、对话框 20px；移动导航 12px，移动端命令面板取消实时模糊。目录卡片不用实时模糊，页面参考标本不逐个给按钮和卡片叠加 backdrop-filter。背景不做持续动画。

不支持模糊或偏好减少透明效果时，退回不透明的雾白表面。减少动态效果偏好禁用抽屉入场动画和非必要过渡。

## Shapes

按钮和输入框 8px 圆角，标本舞台 12px，命令面板 18px，搜索对话框 16px。微小分段控件使用 5–7px 圆角。外壳图标使用同一套线性 SVG，保持一致的线宽。

## Components

- **导航**：半透明浮动侧栏；当前栏目以更明亮的玻璃表面和深色图标标记。手机端保留语言、搜索和参考集入口。
- **命令面板**：真实导航操作和全库搜索入口；透明表面与下方灰色光照形成可见层次。支持键盘操作。
- **目录**：静态预览、名称、简短说明与加入参考按钮。缩略图本身 inert，避免抢占键盘焦点。加载中有文字反馈，图片失败仍可点击卡片打开详情。
- **搜索**：`/` 聚焦当前栏目；Cmd/Ctrl+K 打开全库搜索，方向键和 Enter 导航，Escape 关闭。全库数据首次使用才获取；失败可关闭再打开重试。
- **参考集**：选择立即保存在本地，首次打开时加载完整资料；项目说明可随 Markdown/JSON 导出。空集禁用导出，读取与失败反馈通过状态区展示。对话框使用原生焦点管理。
- **离线访问**：Service Worker 只安装一个小型离线说明页；仅缓存实际访问的页面、预览和目录数据。已访问页面优先返回缓存并在后台更新。最多保存 160 个响应。未缓存的页面显示明确的离线说明，不伪装成首页。

## Do's and Don'ts

- 保留用户选定的雾白、墨黑与玻璃材质；不要退回绿色主题。
- 用真实透明层和边缘高光形成材料感；保持文字对比和稳定的操作区域。
- 目录保持轻量，交互演示留在详情；不要在目录重新启动几十个动画和观察器。
- 不预下载整站，不用无限缓存掩盖网络问题。
- 区分本地弱网测量与公网连接延迟；不能把实验室毫秒数当作所有用户的实际加载时间。
