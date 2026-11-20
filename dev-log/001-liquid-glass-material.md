# 001 液态玻璃材质词条

## 目标

用户 2026-11-17 给出小红书笔记《我复刻了真正的液态玻璃！（附使用教程）》（作者「枯白啃设计」，系列《999 个小技巧》第 010 期，视频 39 秒、无旁白），要求把这个案例放进 Learn UI PM。

笔记正文给出了六层做法和推荐参数，视频画面给出了分层拆解、浅/深色切换和随背景亮度切换文字色的演示。

## 改动

提交 a1158fc。

- `demos/liquid-glass-material.html`：新标本。播放器卡片在壁纸上缓慢漂移，按「无材质 → 投影 → 模糊提亮 → 边缘折射 → 着色 → 边缘光 → 文字着色 → 深色玻璃」逐层叠加；详情页可单独开关六层、拖动卡片、切换浅/深色，下方实时显示背后亮度、文字色和着色浓度。目录卡片（高度 ≤260px）只保留壁纸、卡片和步骤标签。
- `data/entries.json`、`data/zh/entries-4.json`：新增 Web 词条 `liquid-glass-material`（中文名「液态玻璃材质（网页做法）」），六个解剖部件对应六层，Prompt 写入笔记的推荐参数，描述中注明来源。
- `data/styles.json`：Liquid Glass 风格的「另见」加入该词条。
- `build.py`：新词条加入 `NEW_SLUGS`；修复风格页「另见」查不到词条（见下）。
- `scripts/verify-site.py`：新增检查，风格数据里每条「另见」都必须在页面上渲染成卡片。
- `assets/demo-thumbs/liquid-glass-material-{zh,en}.webp`、`SOURCE.json`：由 `scripts/gen-demo-previews.py liquid-glass-material` 生成。
- `README.md`、`PRODUCT.md`、`DESIGN.md`、`docs/live-specimens.md`：数量 83 → 84、Web 52 → 53、静态页 263 → 264。

## 关键决策与踩坑

- **放在 UI 词典，不放风格页。** 上一个外部案例（空间卡片布局）先放风格页、再挪到页面参考、最后定为 UI 元素（提交 49c583d → 68f905e → db219c6）。本次沿用最终位置，并从已有的 Liquid Glass 风格页链过来。项目文档里没有找到用户关于案例归属的明文决定，这是按先例推断，用户若有别的意图可再挪。
- **折射用「壁纸副本 + CSS filter」，不用 `backdrop-filter: url()`。** 后者只有 Chromium 支持。标本把同一张画布复制进卡片，随卡片位置反向平移，再套 SVG 位移滤镜，WebKit 和 Chromium 都能看到折射。词条 Prompt 仍按真实项目写法给出 `backdrop-filter: url(#lens)` 加只模糊的退回方案。
- **文字色按平均亮度切换，卡片骑在明暗交界上时会失效。** 第一版壁纸右侧是硬边深色波浪，卡片跨在交界上时平均亮度约 0.41，文字切成白色，而卡片左半是亮的，「Low Tide」「0:48」几乎看不见（截图核对）。改为左亮右深的渐变壁纸、波浪改成半透明，保留细白线供折射显形；文字色切换加 0.35s 过渡和 0.48/0.52 回差。这是这种做法本身的局限，详情说明里没有回避。
- **卡片贴近壁纸边缘时出现深色竖条。** 位移会采样卡片外最多约 56px，超出壁纸的地方是透明。先改为把边缘像素拉伸出去，结果 WebKit 在右上角把一条白线拉成彩虹条纹；最终改为镜像填充四周。
- **WebKit 下卡片内部有横竖接缝。** 原位移贴图只覆盖卡片、用 `feImage` 的 x/y 偏移定位，WebKit 与 Chromium 对该偏移的解释不同。改为贴图覆盖整个采样区域（卡片外一圈填中性灰 128），不再设偏移，两边一致。
- **顺带修复：风格页「另见」从来不显示词条链接。** 数据写的是 `macos/vibrancy`、`web/form-field`，`build.py` 拿它直接比对不带平台前缀的 slug，12 条链接被静默丢弃（liquid-glass、neobrutalism、web-brutalism 等页）。先在 `verify-site.py` 加检查，确认它报出 12 条缺失，再修 `build.py`，检查通过。
- **减少动态效果时直接显示完成态。** 预览图在 reduced-motion 下截取，原来会截到第 0 步「无材质」。
- 视频无人声，转写只得到 Whisper 的幻觉字幕；方法与参数全部来自笔记正文和画面。

## 验证

本机自动化，均实际运行：

- `python3 scripts/validate-data.py`、`python3 build.py`：通过，264 页。
- `python3 scripts/verify-site.py site`：新检查先失败（12 条「另见」缺失），修复后通过，266 个 HTML、215 个目录入口。
- `python3 scripts/verify-performance.py site`：预算通过。
- 按 CI 步骤在副本上跑 `prepare-pages.py --base /LearnUI_PM`、`verify-site.py --base`、`test-live-demos.py`：84 个标本逐一挂载、无 JS 错误，原有动效与重试检查通过。
- Playwright 专项脚本（Chromium）：目录卡片在桌面 1440 与手机 390 下都在运动、无横向溢出；详情页六层开关、拖到亮处（亮度 0.86 → 深色字）与暗处（0.39 → 浅色字）、深浅切换、英文模式文案均符合预期；手机详情无横向溢出。
- WebKit（Playwright WebKit 26.0，从 npmmirror 安装）：自动演示各步截图与 Chromium 一致，可见折射与色散；卡片拖到左右边缘无深色条。

证据边界：WebKit 结果来自 Playwright 内置 WebKit，不等于真实 Safari；Firefox 未测。

## 下一步

- 待人工：在真实 Safari 打开详情页看一眼折射和文字色切换。（2026-11-20 已把线上链接发给用户，等用户看）
- 已知小瑕疵：WebKit 下把卡片手动拖到右上角时，卡片内仍有一条很淡的竖向接缝；自动演示不会到达该位置。
- 2026-11-17 用户要求提交并推送到 main，由 GitHub Pages 工作流自动发布。
