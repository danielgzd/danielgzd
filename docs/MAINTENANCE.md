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

私有项目仅公开匿名概括信息与月度提交次数，不发布源码、私有文档或原始提交信息。MIT 许可仅覆盖本仓库自己的脚本和文档，所链接项目使用各自许可。

## 私有项目匿名展示与更新记录

公开文件仅存随机项目 ID、匿名编号、概括分类、主语言和月度提交次数。真实仓库名与 ID 的对应关系保存在本机 `~/Library/Application Support/GitHubProfile/private-projects.json`，文件权限为仅本人可读写，不在 Git 仓库中。不要把这份映射作为附件、日志或普通配置提交。

本地使用已登录且拥有原仓库读取权限的 GitHub CLI：

```sh
python3 scripts/update_private_projects.py
python3 scripts/update_profile.py
python3 -m unittest discover -s tests -v
```

如需指定其他本地映射文件，设置 `PRIVATE_PROJECTS_CONFIG` 为文件路径。脚本固定生成匿名展示名与概括描述，不直接输出原仓库描述、名称或提交文本。更新活动按月汇总，不发布具体日期。匿名快照只记录月份；公开仓库快照保留其原有更新时间。

默认每日工作流保留最后一份匿名快照。如果需要自动刷新，必须同时配置两个 Actions Secrets：`PRIVATE_PROJECTS_READ_TOKEN`（仅选定私有仓库的 Contents: read 权限）与 `PRIVATE_PROJECTS_CONFIG_JSON`（本地映射文件的 JSON 内容）。工作流不打印映射或原始 API 响应，失败时只输出概括错误。不要将本机广权限登录令牌复制到工作流。

数据结构只允许匿名版本 2；旧的真实名称快照和逐日记录会被拒绝，避免后续刷新重新带入已移除信息。新项目需要先加入本地私密映射，公开配置 `profile.json` 不包含任何真实私有仓库名。
