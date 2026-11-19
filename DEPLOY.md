# Learn UIUX 部署说明

正式公网地址：<https://www.kettywu.art/UIUX/>

## 正式部署（新加坡镜像）

网站部署在腾讯云轻量应用服务器（新加坡，锐驰型 2C2G，不限流量），SSH 别名 `sg-server`——IP 只写在 `~/.ssh/config`，不进仓库。

一条命令完成「校验 → 构建 → 同步」：

```bash
scripts/deploy-sg.sh
```

脚本从 `git archive HEAD` 导出**已提交**的版本构建（不会把未提交的在途改动发上线），构建时按 `/UIUX` 子路径处理，然后 rsync 到服务器 `/var/www/UIUX/`。

服务器侧（已配置，日常不用动）：

- Nginx 静态站 + 限流（15r/s、单 IP 20 连接）+ gzip + 分层缓存（HTML 不缓存、assets 一天、api 一小时）；
- Let's Encrypt 证书（certbot，`certbot.timer` 自动续期），http 301 到 https；
- 域名根路径 `/` 留给个人主页，当前 302 到 `/UIUX/`；
- 内核 BBR 拥塞控制（`/etc/sysctl.d/99-bbr.conf`）——高丢包跨境链路下比默认 CUBIC 快约 15 倍。

需要 sudo 的服务器操作（改 Nginx、续证书、防火墙）由用户自己执行；只读检查可直接 `ssh sg-server`。

## GitHub Pages（已停用）

仓库曾用 GitHub Actions 自动发布 GitHub Pages，`K3tty5555.github.io/LearnUI_PM` 上的旧版本不会随新提交更新。`.github/workflows/deploy-pages.yml` 仍保留为**推送前的完整检查流程**（构建 + 全部回归测试），只是不再执行发布步骤。

如需临时预览其它地址，通过 `SITE_URL` 环境变量覆盖构建时的 Canonical / Open Graph / RSS / Sitemap 地址。

## 本地验证

```bash
python3 build.py
cd site && python3 -m http.server 8000
```

打开 <http://127.0.0.1:8000/> 检查首页和静态资源（本地是根路径，不带 /UIUX 前缀）。

## 说明

- `site/` 是构建产物，已加入 `.gitignore`，不要手工提交；源文件修改后重新运行 `python3 build.py` 即可生成。
- 构建器为 CSS/JS URL 注入内容哈希，避免新页面命中旧浏览器缓存。
- Service Worker 安装只读取 `offline.html`，不预取全站；回访页面从缓存立即返回，后台更新。

## 2026-09-06 改版

全站外壳使用 `assets/workspace.css`；原 `glass-theme.css` 已移除。浏览器通过 CSS/JS 内容哈希获取新资源；Service Worker 同步缓存新外壳。本地开发不注册 Service Worker，避免旧离线页面干扰验证。

UI 词典已恢复按视口运行的原始动效，演示源由构建器生成到 `api/specimens/`。发布工作流安装 Playwright/Chromium 并运行 `scripts/test-live-demos.py`，实际验证动效、离屏停止、移动端与错误恢复。普通站点构建仍只使用 Python 标准库。

## 知名网站自动加载

`/sites/` 在接近列表底部时自动展示下一批品牌；手动“加载更多”按钮保留为无观察器或键盘使用场景的兜底。搜索、行业和设计气质筛选会重置批次并保持 URL 状态。
