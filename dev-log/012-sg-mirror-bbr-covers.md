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

- 10% 丢包的链路问题客观存在，BBR 只是绕过其影响。观察几天晚高峰是否稳定。（2026-11-20：实测首页 0.9–5.7 秒波动；用户体感「还好」，不处理，继续观察）
- `build.py` 的 `SITE_URL` 仍指向 GitHub Pages。若要把 `www.kettywu.art/UIUX` 定为正式地址，需改 `SITE_URL`、重跑 `scripts/gen-og.py --force` 并提交 `assets/og/` 变动——等用户拍板。（2026-11-20 核对：已完成，见本篇追加）

## 追加（正式地址切换为 www.kettywu.art/UIUX，2026-11-19）

用户拍板：正式地址改为 `www.kettywu.art/UIUX`，GitHub Pages 不再使用。本轮集中改完：

- `build.py` 的 `SITE_URL`、`scripts/sync-sites.py` 的 `BASE`、`scripts/test-live-demos.py` 的 `--base` 默认值改为新地址；README / PRODUCT / DEPLOY 的链接与说明同步改写（DEPLOY.md 重写为新加坡镜像部署文档）。
- `data/sites-manifest.json`：74 条 `sourceUrl` 和 `source` 改为新地址（它们是页面里的「源地址」链接数据）。
- 重新生成全部分享图（`gen-og.py --force`，191 张）：图上印的网址换成 `www.kettywu.art/UIUX`。`assets/og/` 里旧的 `site-*.png` 与新命名并存，以实际生成的 191 张为准。
- CI 工作流：保留全部检查，基路径统一改 `/UIUX`；删掉 GitHub Pages 发布，新增 rsync 到新加坡（`secrets.SG_MIRROR_KEY` + 主机密钥钉死 + `~/.ssh/config` 别名）。
- 服务器上为 CI 生成专用受限密钥：authorized_keys 里用 `command=` 限制只能 `rsync --server -az --delete . /var/www/UIUX/`，加 `restrict`。已验证该密钥执行普通命令会被拒绝。
- `scripts/deploy-sg.sh`（本地部署）不受影响，仍是「只发已提交版本」。

### 验证

- 新基路径下全套检查通过：verify-site（293 页 / 242 项）、102 标本无错误、logo 183、graphics 219、text-width 32、mobile-language 3。
- 构建产物 `github.io` 出现次数：0；新地址在 index / sitemap 就位。
- 分享图底部网址截图核对无误。

### 密钥配置与首次 CI 部署（2026-11-19 补记）

- `SG_MIRROR_KEY` 已通过 `gh secret set` 写入仓库 Secrets（用户授权代操作；本地临时私钥文件已删除）。
- 首次 CI 部署失败：known_hosts 用别名 `sg-server` 作键，而 ssh 按配置里的真实地址（IP）查主机密钥，名字对不上被拒（"Host key verification failed"）。改为 IP 与别名各写一行（提交 `80f9933`）。
- 修复后运行 44448422236 全绿，rsync 步骤成功，服务器 sitemap 已是新地址。自动部署链路（推送 → 全部检查 → rsync 上线）自此打通。

### 追加（服务器地址移出公开仓库，2026-11-19）

发现部署工作流与本篇日志里写着新加坡镜像的 IP，违反「IP 只放 `~/.ssh/config`」的规则（仓库是公开的）。处理：

- IP 从本机 `ssh -G sg-server` 读出，写入仓库 Secrets `SG_MIRROR_HOST`；工作流的 known_hosts 与 ssh config 改为从该密钥取值，密钥缺失时直接报错退出。
- 本篇日志里的 IP 改为文字描述。
- 历史提交（`f4bdc84`、`80f9933`、`71a96f4`）里仍有该 IP。用户决定不改写历史：服务器仅密钥登录，CI 密钥已用 `command=` 限死为 rsync。
