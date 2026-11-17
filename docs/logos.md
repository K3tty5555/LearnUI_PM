# Logo 图鉴栏目

## 定位（用户拍板 2026-11-17）

新增「Logo 图鉴」栏目，形式为「Logo 图鉴 + 资源站」：

- 每个 logo 一张卡：标出它属于哪种 logo（文字标、字母标、具象图形标、抽象图形标、吉祥物标、组合标、徽章标），拆解它的构成，并给出一段可交给 AI 的 prompt。
- 同一张卡兼作资源站档案：链接到网站，写明用途、适合谁、费用与授权。
- 首期 9 个样本取自小红书视频《好用的设计网站之LOGO/图标》（作者「李李说设计（大学陪跑）」，2026-11-13 发布）中介绍的 9 个网站，样本就是这些网站自己的 logo。

用户在三个方案中选择了本方案；另两个是「只做资源导航」和「Logo 作品赏析（从这些站挑别人的作品）」。

## 内容规则

- logo 图片取自各网站官方发布的图标文件（favicon、logomark、页头 logo），由脚本统一渲染成 WebP，不在页面中执行原始 SVG。商标归各自所有者，页面仅用于识别与学习，在栏目页和「来源与许可证」页注明。
- 授权写法以核实过的一手来源为准（npm 包、仓库 LICENSE、网站自述），核实不了的不写数字。
- 视频与现状不一致时以现状为准，并在卡片上说明。首期的三处：
  - Iconfinder 已被 Freepik 收购（2022），现访问会跳到 freepik.com/icons；Freepik 于 2026-04-28 更名为 Magnific，视频中展示的「M」就是 Magnific 的新标志。
  - Logobook 的官方标志是「书本 + 地球 + L」，视频中的皇冠「b」是该站「Crowns」分类的缩略图（别人的商标），未采用。
  - Remix Icon 自 2026 年 1 月起改用 Remix Icon License v1.0：可商用，但不得用作 logo、商标或 App 图标，不得作为图标包单独售卖。npm 元数据仍写 Apache-2.0，以包内 License 文件为准。
- prompt 只讲构成方法，要求「不要复制原 logo」。

## 第 2 期（2026-11-17）

- 样本 Reicon，来自小红书视频《2026 年的图标库，根本不是人用的》（默默然，2026-09-03）。用户要求加入；放进 Logo 图鉴而不是新栏目，因为它和首期的 IconPark、Remix Icon 同属图标库。
- 已核对：官网 reicon.dev、npm 包 `reicon` / `reicon-mcp` 均标 MIT；官网 llms-full.txt 自述「Base elements from Solar Icons (CC BY 4.0) by 480 Design and Zappicon」，同一文件又写「no attribution required」，授权链条需要使用方自己核验。
- 未能核对：原视频说仓库 README 已写 3,900+ 个图标（GitHub 当时无法访问），卡片上注明「据原视频」。

数据在 `data/logos.json`，图片在 `assets/logos/`，落地过程见 [dev-log/002](../dev-log/002-logo-atlas.md)。
