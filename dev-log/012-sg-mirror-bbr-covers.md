# 012 新加坡镜像、BBR 拥塞控制与列表页封面缩略图

## 目标

用户 2026-11-18/19 提出：GitHub Pages 大陆访问太慢，想部署到自己的服务器。随后发现速度仍然不行，用户要求「先去调研下这是啥情况」，再评估方案是否合适。

## 改动

### 新加坡镜像

- 腾讯云轻量 新加坡 锐驰型 2核2G（¥40/月，不限流量），Ubuntu 24.04。SSH 别名 `sg-server`，IP 只写在 `~/.ssh/config`，不进仓库。
- Nginx 静态站：限流（15r/s、单 IP 20 连接）、gzip、分层缓存（HTML 不缓存、assets 一天、api 一小时）。
- 域名 `www.kettywu.art`，网站挂在 `/UIUX/` 子路径（根路径留给用户以后的个人主页，暂时 302 到 `/UIUX/`）。certbot 签发 Let's Encrypt 证书，`certbot.timer` 自动续期，http 全站 301 到 https。
- `scripts/deploy-sg.sh`：从 `git archive HEAD` 导出**已提交**的版本构建再同步，不会把在途改动发上线。

### BBR 拥塞控制（本轮最大的修复）

- 服务器 `net.ipv4.tcp_congestion_control=bbr`、`net.core.default_qdisc=fq`，写在 `/etc/sysctl.d/99-bbr.conf`，重启保留。

### 列表页封面缩略图

- 新增 `scripts/graphics/make_covers.py`：按 450 / 1000px 两档生成 `<slug>-cover.webp`、`<slug>-cover@2x.webp`。
- `build.py` 新增 `graphic_cover()`，列表卡片改用缩略图加 srcset；详情页大图和点击放大的文件不变。
- `scripts/validate-data.py` 校验封面存在且与当前原图一致（过期会报错并提示重跑脚本）。
- `scripts/test-graphics-layout.py` 新增像素充足性检查：图片不能比屏幕需要的少（发虚），列表封面也不能比屏幕能显示的多出 2.2 倍（浪费）。

### 顺带修复

- `assets/workspace.css`：恢复「文字跟随窗口宽度」规则。它在 `3ff80d2` 移除 references 栏目时被连带删掉（和 `.reference-detail-grid` 写在同一行），`test-text-width.py` 报 68 处失败抓到。规则移到文件末尾并加注释说明由哪个测试守护。
- `scripts/test-text-width.py`：页面清单去掉已删除的 references 和 guides/translate。
- 发布流程加入 `test-mobile-language.py`（另一会话新增，按项目惯例进 CI）。

## 关键决策与踩坑

### 我误诊了三次，根因是丢包不是带宽

前两轮我依次归咎于「公司网络」「新加坡线路不行」，并建议用户迁 Cloudflare。用户要求先调研后，补测两个数据才找到真因：

- **丢包 10%**，RTT 144ms（抖动到 748ms）；
- 服务器用 CUBIC——靠丢包判断拥塞，一丢包就猛降窗口。

Mathis 公式 `MSS/(RTT×√p)` = 1460/(0.144×√0.1) = **31.3 KB/s**，与实测 13–29 KB/s 吻合。带宽从来不是瓶颈（服务器出网实测 87MB/s）。

换 BBR 后同一条家宽：**291–339 KB/s，约 15 倍**；2.4MB 高清图 40–60 秒 → 1.9 秒。

**对 Cloudflare 建议的更正**：我当时拿 `speed.cloudflare.com` 的 303 KB/s 当证据，但那是 CF 自家测速端点，代表不了免费版客户站点；且 CF 免费版在中国大陆没有节点。BBR 之后我们自己就是 ~300KB/s——CF 快是因为**它全线跑 BBR**，不是因为有大陆节点。差点让用户为一个内核参数迁走整个域名的 NS。已撤回该建议。

### 封面浪费 4 倍是我自己埋的

做平面设计栏目时，列表封面直接用了 1400px 原图，而卡片只显示 357 点宽。与网络无关，所有访客都在白等。

### 两个测量方法上的坑

1. **`naturalWidth` 会被 srcset 密度描述符除以 2**。首次运行像素检查报 53 处「发虚」，全是假阳性——900px 的 `2x` 图读出来是 450。改用探针 `new Image()` 单独加载 `currentSrc` 才拿到真实像素。
2. **不能要求图片比它的源更清晰**。`ti-2025` 原图只有 788px 宽，在 2000px 窗口的高清屏上需要 891px，永远达不到。检查改为与「该文件可能的最大像素」取较小值比较。

### 封面尺寸从 900 提到 1000

2000px 窗口下封面槽位实测需要 891 设备像素，900px 只有 1% 余量，布局稍有变化就会不足。提到 1000px 换取余量，代价是高清屏总量从 1.16MB 增到约 1.4MB。

## 验证

- **网络**：服务器本机 https 200、http 301；大陆腾讯机房直连 0.76s；itdog 全国拨测电信/联通 0.2–0.4s、移动平均 0.38s（合肥长沙两节点超时）。BBR 前后家宽对比 13–29 KB/s → 291–339 KB/s。
- **画质**：900px 缩略图与 1400px 原图渲染到高清屏实际尺寸后，平均每像素色差 **1.38/255**（肉眼可辨阈值 2–3），并排截图人工确认无差别。
- **测试**：`validate-data`、`build`（291 页）、`verify-site`（293 页 / 242 目录项）、`verify-performance` 通过；生产路径下 `test-live-demos`（102 标本、errors 空）、`test-logo-layout`（183）、`test-graphics-layout`（219）、`test-text-width`（32）、`test-mobile-language`（3）全通过。Chromium + WebKit：graphics 438、text-width 64 通过。
- **反向验证**：把封面换回全尺寸原图 → 排版测试报 8 处「超出屏幕可显示」；删掉一个封面文件 → 数据校验报「封面缺失」；恢复前的 CSS → 宽度测试报 68 处。

## 下一步

- 10% 丢包的链路问题客观存在，BBR 只是绕过其影响。观察几天晚高峰是否稳定。
- `build.py` 的 `SITE_URL` 仍指向 GitHub Pages。若要把 `www.kettywu.art/UIUX` 定为正式地址，需改 `SITE_URL`、重跑 `scripts/gen-og.py --force` 并提交 `assets/og/` 变动——等用户拍板。
