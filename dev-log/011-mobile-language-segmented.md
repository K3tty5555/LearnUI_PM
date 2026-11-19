# 011 手机端语言切换改为分段控件

## 目标

用户 2026-11-19 反馈：手机宽度下，页头的「中文 / EN」切换弹出的是系统原生下拉菜单，没有遵循网站设计规范。

## 原因

页头在 760px 以下用的是原生 `<select id="mobile-language">`，弹出层由系统绘制，样式无法跟随网站。DESIGN.md 规定语言切换是「微小分段控件，5–7px 圆角」（桌面侧栏底部的 `.lang-switch` 就是这样做的），并要求「手机端保留语言入口」。

## 改动

- `build.py` 页头：原生 select 换成与侧栏同款的分段控件 `<div class="lang-switch mobile-language" role="group">` + 两个 `.ls-btn`。
- `assets/workspace.css`：手机端分段控件放在页头第一行第 2 列，按钮高 28px、字号 12px；桌面端仍隐藏。
- `assets/site.js`：删掉 select 的同步与 change 监听。两组 `.ls-btn` 共用原有点击逻辑，切换时两组的高亮一起更新。
- `scripts/test-live-demos.py`：页面上现在有两组语言按钮，点击改为只点当前可见的那组（`:visible`），否则 Playwright 严格模式会因匹配到两个元素报错。

## 验证

- 先写回归测试 `scripts/test-mobile-language.py`：375 / 390 / 760 宽 × 首页、平面设计、词条页，检查页头无原生 select、只有一组分段控件、按钮顺序和圆角、默认中文高亮、点 EN 后切换并移动高亮、不与站名/搜索/参考集重叠、不出屏；1440 宽只显示侧栏那一组。
  - 修改前：18 项失败（手机宽度下全部是原生 select、没有分段控件）。
  - 修改后：Chromium + WebKit 全部通过。
- `validate-data`、`build`（291 页）、`verify-site`（293 页）、`test-logo-layout`（183 项）、`test-graphics-layout`（219 项）、`test-live-demos`（`errors: []`）通过。
- WebKit 390 宽截图看过中文、EN 两种状态，样式与桌面侧栏一致。

## 备注

- 本轮进行时另一个会话在同时修 `test-text-width.py`（去掉已删除栏目的页面）并在 `workspace.css` 末尾加了文字宽度规则；那部分不属于本轮，提交时只取本轮的那一处改动。
- 本轮改动尚未提交。
