# 数据口径

- 数据源：GitHub REST 用户公开仓库列表、GraphQL ContributionsCollection。只输出白名单字段，不读取私有仓库内容、邮箱或令牌。
- 自有：owner 为 danielgzd 且非 Fork。首页仓库从作品与语言指标排除；非 Fork 不等于独立原创认证。
- Star / Fork：只汇总自有项目，不汇总 Fork 的上游数据。
- 语言：项目主语言的仓库数，不是字节数、代码行数或技能评分。
- Open issues：GitHub REST open_issues_count 包含 Issue 与 PR。
- 贡献：近一年 GitHub 贡献日历口径。Commit、Issue、PR、Review 分别列出；不包含未被 GitHub 计入贡献的全分支提交，也不是终身总量。不请求私有贡献详情。
- 更新时间：页面快照用 UTC+8；GitHub 贡献日历与 traffic 日期依其 API，traffic 为 UTC。
- API 失败：关键公开列表失败会中止更新；贡献接口不可用时保留已存在的公开权限快照及原始时间；无历史快照时明确标记，不伪造零值。
- 访问徽章：第三方图片请求计数，可能受 GitHub 图片代理缓存影响，不识别访客身份，不是 UV。服务不可用不影响仓库目录和本地语言图。
- 官方访问 / 克隆：[单独归档](TRAFFIC.md)，按每日覆盖合并，不重复累加 14 天滚动窗口；不能回溯采集之前的全部历史。

## 官方参考

- [个人主页 README](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme)
- [GitHub 仓库 Traffic](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository)
- [贡献计数规则](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)
- [GITHUB_TOKEN 仓库权限边界](https://docs.github.com/en/actions/concepts/security/github_token)
- [访客计数器说明](https://github.com/antonkomarev/github-profile-views-counter)

## 私有项目展示口径

私有项目单独发布在 `data/private-projects.json` 与 `docs/private-projects/`，采用脱敏数据结构版本 3。公开数据保留本人确认可展示的项目名称、基本介绍、分类、主语言和月度提交次数。公开展示配置与本地采集映射分开，API 返回的原始描述与提交信息不直接发布。

提交数为采集时近 365 天默认分支可达的所有作者提交，按提交者日期的 UTC 月份汇总。仅发布月份，不公开精确日期、采集时间或私有源码入口；首尾月份可能为部分月份。它与 GitHub 公开个人贡献的统计范围不同，两者不能相加作为个人 Commit 总量。

更新页的“项目维护与开发”为统一摘要，不代表具体功能已经交付。页面不包含原始提交标题、作者、邮箱、哈希、分支、文件路径或源码，也不修改原仓库可见性。更新失败保留上一份脱敏快照。公开历史版本与第三方缓存不会因当前文件脱敏而自动消失。
