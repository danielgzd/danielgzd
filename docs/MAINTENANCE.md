# 更新与扩展

## 本地刷新

需要 Python 3.10+ 与已登录的 GitHub CLI，无第三方 Python 依赖。

```sh
python3 scripts/update_profile.py
python3 scripts/collect_traffic.py
```

生成内容为 README、项目目录、兴趣画像、语言 SVG 与 data 下的公开快照。介绍文案可修改生成脚本；精选顺序、描述和分类规则在 profile.json。

## 自动更新

GitHub Actions 每天北京时间 08:23 左右执行（平台可能延迟），支持手动运行。公开目录与贡献使用自带 GITHUB_TOKEN，无需新增密钥。贡献仅在仓库范围的 Actions 权限下刷新，避免本机广权限凭据读取额外可见信息；本地刷新保留上一次来自 Actions 的贡献快照及时间。公开仓库长时间无活动时定时工作流可能被 GitHub 暂停，需要重新启用。

默认令牌仅限当前仓库，无法定期归档所有项目的官方 traffic。若需要，创建只选择本人公开非 Fork 仓库、Administration: read 的细粒度令牌，存为本仓库 Actions Secret `PROFILE_ANALYTICS_TOKEN`。脚本只在该 Secret 存在时采集；禁止把令牌写入文件或提交。过期后保留最后成功采集时间。

## 后续迭代建议

1. 先补齐没有介绍的自有项目，人工确认分类和精选。
2. 增加项目阶段、演示截图、版本发布与路线图。
3. 用历史快照做月度 Star、Followers 与项目方向趋势图；当前仅保留最新公开快照，Git 历史可追溯，traffic 单独逐日归档。
4. 如需交互搜索与筛选，再扩展独立站；当前优先使用直接展示在账户首页的 README。

私有项目仅公开显式配置的基本信息与每日提交次数，不发布源码、私有文档或原始提交信息。MIT 许可仅覆盖本仓库自己的脚本和文档，所链接项目使用各自许可。

## 私有项目基本信息与更新记录

纳入展示的 8 个私有项目在 `profile.json` 的 `private_projects` 中列出。只有这份清单中的项目可以公开其基本介绍；新私有仓库不会自动进入展示。增加项目时填写名称、基本介绍和分类，无需上传源码或复制私有 README。

本地使用已登录且拥有原仓库读取权限的 GitHub CLI：

```sh
python3 scripts/update_private_projects.py
python3 scripts/update_profile.py
python3 -m unittest discover -s tests -v
```

默认每日工作流保留最后一次脱敏私有项目快照，继续更新公开统计。如果要让私有项目更新记录也每天刷新，需在本主仓库 Actions Secret 中设置 `PRIVATE_PROJECTS_READ_TOKEN`：使用仅选择这些私有项目、Contents: read 的细粒度令牌。工作流不会输出原始 API 响应或令牌，也不会把私有源码检出到公开仓库。

该权限仅用于 GitHub API 读取提交元数据；不要把本机已有广权限登录令牌复制到公开仓库。没有配置凭据时，页面保留明确的采集时间，可随时在本地刷新。撤销展示时同时删除配置、JSON 记录与对应页面；已公开版本仍可能存在于 Git 历史中。

