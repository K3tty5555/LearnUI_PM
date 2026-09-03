# Learn UI PM 部署说明

正式公网地址：<https://K3tty5555.github.io/LearnUI_PM/>

## 自动部署

仓库使用 GitHub Actions 部署 GitHub Pages：

- 工作流：`.github/workflows/deploy-pages.yml`
- 触发条件：推送到 `main`，或在 Actions 页面手动执行
- 构建命令：`python3 build.py`
- 项目路径处理：`python3 scripts/prepare-pages.py site --base /LearnUI_PM`
- 静态资源版本：构建器为 CSS/JS URL 注入内容哈希，避免新页面命中旧浏览器缓存
- 发布目录：`site/`

推送代码后，Actions 会自动构建并发布。构建器默认使用
`https://K3tty5555.github.io/LearnUI_PM` 生成 Canonical、Open Graph、RSS 和 Sitemap
地址；如需临时预览其它地址，可通过 `SITE_URL` 环境变量覆盖。

## 本地验证

```bash
python3 build.py
cd site && python3 -m http.server 8000
```

打开 <http://127.0.0.1:8000/> 检查首页和静态资源。

## 说明

- 本项目只维护 GitHub 仓库和 GitHub Pages，不维护其它域名、VPS、DNS、证书或第三方统计服务。
- `site/` 是构建产物，已加入 `.gitignore`，不要手工提交；源文件修改后重新运行 `python3 build.py` 即可生成。
