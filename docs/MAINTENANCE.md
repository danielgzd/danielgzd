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

公开输出不包含私有仓库；如果以后扩展输入源，也应继续保留这一限制。MIT 许可仅覆盖本仓库自己的脚本和文档，所链接项目使用各自许可。
