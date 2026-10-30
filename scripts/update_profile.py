#!/usr/bin/env python3
"""Public GitHub inventory plus sanitized private-project showcase generator. Python standard library only."""
import collections
import datetime as dt
import html
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
USER = 'danielgzd'

def api(path, payload=None):
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        # gh manages credentials locally; never print or persist tokens.
        args = ['gh', 'api', path]
        if payload is not None:
            args += ['--input', '-']
        result = subprocess.run(args, input=json.dumps(payload) if payload else None,
                                text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError('GitHub API request failed: ' + path.split('?')[0])
        return json.loads(result.stdout)
    url = 'https://api.github.com/' + path
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload else None,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'danielgzd-profile', 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)

def category(repo, config):
    if repo['name'] in config['overrides']:
        return config['overrides'][repo['name']]
    text = ' '.join([repo['name'], repo.get('description') or '', *repo.get('topics', [])]).lower()
    for rule in config['categories']:
        if any(word.lower() in text for word in rule['keywords']):
            return rule['name']
    return '其他探索'

def clean(value):
    return html.escape(str(value or '—')).replace('|', '&#124;').replace('\n', ' ')

def render(snapshot, config):
    repos = snapshot['repositories']
    own = [r for r in repos if not r['fork'] and r['name'] != USER]
    forks = [r for r in repos if r['fork']]
    langs = collections.Counter(r['language'] for r in own if r['language'])
    groups = collections.defaultdict(list)
    for repo in repos:
        if repo['name'] != USER:
            groups[category(repo, config)].append(repo)
    private_path = ROOT / 'data/private-projects.json'
    private_snapshot = json.loads(private_path.read_text()) if private_path.exists() else None
    if private_snapshot:
        from update_private_projects import validate_snapshot
        validate_snapshot(private_snapshot)
    private_projects = private_snapshot['projects'] if private_snapshot else []
    c = snapshot.get('contributions')
    lines = ['<div align="center">', '',
        '# Hi, I’m Daniel 👋', '',
        '**把好奇心写成代码，把重复的事交给工具。**', '',
        '在 Apple 生态、自动化与网络工具之间持续探索，',
        '把日常遇到的小问题，做成可复用、可维护的小作品。', '',
        '[项目地图](docs/PROJECTS.md) · [非公开项目](docs/PRIVATE_PROJECTS.md) · [数据与口径](docs/METRICS.md) · [访问归档](docs/TRAFFIC.md) · [兴趣画像](docs/INTERESTS.md) · [更新指南](docs/MAINTENANCE.md)', '',
        '![Profile views](https://komarev.com/ghpvc/?username=danielgzd&label=PROFILE+VIEWS&color=0f766e&style=flat-square)',
        '[![每日更新](https://github.com/danielgzd/danielgzd/actions/workflows/profile.yml/badge.svg)](https://github.com/danielgzd/danielgzd/actions/workflows/profile.yml)', '',
        '</div>', '', '## 正在构建的作品', '',
        '> 从一个具体需求出发，让工具真正融入日常。', '']
    by_name = {r['name']: r for r in own}
    for name in config['featured']:
        if name in by_name:
            r = by_name[name]
            desc = config['descriptions'].get(name) or r['description'] or '项目内容持续整理中。'
            lines += [f"- **[{name}]({r['html_url']})** · {desc}"]
    if private_snapshot:
        lines += ['', '## 幕后也在生长的作品', '', '有些项目仍在打磨，有些服务于个人工作流。这里保留它们的开发足迹，代码继续私有。', '', '| 项目与更新记录 | 基本介绍 |', '| --- | --- |']
        for project in private_projects:
            lines += [f"| [{clean(project['name'])}](docs/private-projects/{project['id']}.md) | {clean(project['description'])} |"]
        lines += ['', f"私有项目快照月份：{private_snapshot['updated_month']} · [查看完整统计与更新记录](docs/PRIVATE_PROJECTS.md)"]
    lines += ['', '## 项目与开发足迹', '', '| 指标 | 当前快照 |', '| :--- | ---: |',
        f'| 公开仓库（包含本首页） | {len(repos)} |', f'| 公开自有非 Fork 项目（不含首页） | {len(own)} |',
        f'| Fork 探索仓库 | {len(forks)} |', f"| 公开自有项目获得 Star | {sum(r['stargazers_count'] for r in own)} |",
        f"| 公开自有项目被 Fork | {sum(r['forks_count'] for r in own)} |",
        f"| Followers / Following | {snapshot['profile']['followers']} / {snapshot['profile']['following']} |",
        f"| 公开自有项目已归档 | {sum(r['archived'] for r in own)} |",
        f"| 公开自有项目开放 Issue + PR | {sum(r['open_issues_count'] for r in own)} |"]
    if private_snapshot:
        lines += [f'| 私有项目（已纳入展示） | {len(private_projects)} |', f'| 已统计仓库合计（公开 + 私有） | {len(repos) + len(private_projects)} |', f'| 自有项目合计（公开 + 私有，不含首页与 Fork） | {len(own) + len(private_projects)} |', f"| 私有项目近 365 天默认分支提交（所有作者） | {sum(p['commit_count'] for p in private_projects)} |"]
    if c:
        lines += [f"| 近一年公开贡献 | {c['contributionCalendar']['totalContributions']} |",
            f"| 近一年 Commit 贡献 | {c['totalCommitContributions']} |",
            f"| 近一年 PR / Issue / Review 贡献 | {c['totalPullRequestContributions']} / {c['totalIssueContributions']} / {c['totalPullRequestReviewContributions']} |",
            f"| 近一年有贡献的天数 | {sum(d['contributionCount'] > 0 for w in c['contributionCalendar']['weeks'] for d in w['contributionDays'])} |"]
    else:
        lines += ['| 近一年贡献 / Commit | 暂未取得，见数据说明 |']
    if c:
        lines += ['', '贡献快照时间：' + snapshot.get('contributions_updated_at', snapshot['updated_at'])]
    lines += ['', '![公开自有项目语言分布](assets/languages.svg)', '',
        '语言按公开自有非 Fork 项目的主语言计数，不代表代码行数或熟练程度。Commit 为 GitHub 贡献口径，非全平台、全分支的历史提交总量。', '',
        '## 我的探索地图', '', '| 方向 | 公开自有项目 | Fork 收藏 | 私有项目 |', '| :--- | ---: | ---: | ---: |']
    for group in dict.fromkeys([*groups, *(p['category'] for p in private_projects)]):
        items = groups[group]
        lines += [f"| {group} | {sum(not r['fork'] for r in items)} | {sum(r['fork'] for r in items)} | {sum(p['category'] == group for p in private_projects)} |"]
    lines += ['', '从公开仓库看，我的探索集中在 **Apple 生态、网络配置与自动化**。这是一份可修正的项目兴趣地图；Fork 表达关注，不代表参与开发、实际使用或认可项目的全部功能。', '',
        '## 最近更新', '']
    for r in sorted(own, key=lambda r: r['pushed_at'] or '', reverse=True)[:5]:
        lines += [f"- [{r['name']}]({r['html_url']}) · {str(r['pushed_at'])[:10]} · {clean(r['language'])}"]
    lines += ['', '---', '', f"<sub>公开数据更新于 {snapshot['updated_at']} · 每日自动整理 · MIT License</sub>", '',
        '<sub>访客徽章来自第三方，记录图片请求次数，受缓存影响，并非独立访客数。私有项目仅发布匿名概括信息与月度活动，源码保持私有。</sub>', '']
    (ROOT / 'README.md').write_text('\n'.join(lines))
    catalog = ['# 项目地图', '', '私有项目的基本介绍与更新记录见 [非公开项目目录](PRIVATE_PROJECTS.md)。以下按用途分类，保留全部公开仓库。自有非 Fork 仅指仓库属性，不等同于独立原创认证。分类可在 `profile.json` 修正。', '']
    for group, items in groups.items():
        catalog += [f'## {group}', '', '| 项目 | 类型 | 主语言 | Star | 简介 |', '| --- | --- | --- | ---: | --- |']
        for r in sorted(items, key=lambda r: (r['fork'], r['name'].lower())):
            desc = config['descriptions'].get(r['name']) or r['description'] or '暂无公开描述'
            catalog += [f"| [{clean(r['name'])}]({r['html_url']}) | {'Fork' if r['fork'] else '自有'}{' · 已归档' if r['archived'] else ''} | {clean(r['language'])} | {r['stargazers_count']} | {clean(desc)} |"]
        catalog += ['']
    (ROOT / 'docs/PROJECTS.md').write_text('\n'.join(catalog))
    interests = ['# 公开项目兴趣画像', '', '这是基于仓库元数据的规则分析，不推断私人生活、性格或敏感属性。', '',
        '## 方法', '', '按名称、描述、Topics 匹配关键词，人工覆盖优先；每个仓库归入一个主要方向。自有项目与 Fork 分开计数，不用上游 Star 推断个人影响力。', '',
        '| 探索方向 | 自有项目数 | Fork 数 | 可核查的依据 |', '| --- | ---: | ---: | --- |']
    for group, items in groups.items():
        evidence = ', '.join(f"[{r['name']}]({r['html_url']})" for r in sorted(items, key=lambda r:r['fork'])[:4])
        interests += [f"| {group} | {sum(not r['fork'] for r in items)} | {sum(r['fork'] for r in items)} | {evidence} |"]
    interests += ['', '## 如何解读', '', '自有项目比单纯 Fork 更能表明投入方向；但主语言、仓库数量和更新时间均不能证明投入时长或技能等级。Fork 的更新时间可能来自上游，不能当作个人活跃记录。没有描述的项目保留在“其他探索”，不凭名字编造用途。', '',
        '## 后续可扩展', '', '- 人工确认项目阶段、用途与展示顺序。', '- 按月比较公开快照，观察方向变化。', '- 经本人选择后再引入 Star 列表或公开 README 文本，增加证据覆盖。', '']
    if private_projects:
        interests += ['## 私有项目补充证据', '', '以下仅使用本人允许展示的项目方向与主语言，不读取源码、提交标题或笔记内容。', '', '| 方向 | 私有项目数 | 项目 |', '| --- | ---: | --- |']
        for group in dict.fromkeys(p['category'] for p in private_projects):
            entries = [p for p in private_projects if p['category'] == group]
            links = ', '.join(f"[{clean(p['name'])}](private-projects/{p['id']}.md)" for p in entries)
            interests += [f'| {group} | {len(entries)} | {links} |']
        interests += ['', '私有项目仅以匿名编号与概括方向补充统计，不推断具体业务、私人生活偏好或技能等级。', '']
    (ROOT / 'docs/INTERESTS.md').write_text('\n'.join(interests))
    height = 75 + len(langs) * 35
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}" role="img" aria-label="公开自有项目主语言分布">',f'<rect width="720" height="{height}" rx="16" fill="#0f172a"/>','<text x="28" y="36" fill="#f8fafc" font-size="18" font-family="sans-serif">BUILD WITH · 公开自有项目主语言</text>']
    for i, (lang, count) in enumerate(langs.most_common()):
        y = 65 + i*35
        svg += [f'<text x="28" y="{y+14}" fill="#cbd5e1" font-size="14" font-family="sans-serif">{html.escape(lang)}</text>', f'<rect x="160" y="{y}" width="{450*count/max(langs.values())}" height="19" rx="5" fill="#2dd4bf"/>',f'<text x="640" y="{y+14}" fill="#e2e8f0" font-size="14">{count}</text>']
    (ROOT / 'assets/languages.svg').write_text('\n'.join(svg + ['</svg>']))

def main():
    config = json.loads((ROOT / 'profile.json').read_text())
    repos = []
    page = 1
    while True:
        batch = api(f'users/{USER}/repos?type=owner&per_page=100&page={page}')
        repos += [r for r in batch if not r.get('private') and r['owner']['login'].lower() == USER]
        if len(batch) < 100:
            break
        page += 1
    fields = ['name', 'html_url', 'description', 'fork', 'language', 'topics', 'stargazers_count', 'forks_count', 'open_issues_count', 'archived', 'pushed_at', 'created_at']
    profile = api('users/' + USER)
    snapshot = {'updated_at': dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M UTC+8'),
        'profile': {k: profile[k] for k in ['login', 'name', 'followers', 'following', 'public_repos']},
        'repositories': [{k:r.get(k) for k in fields} for r in repos]}
    query = '''query { user(login:"danielgzd") { contributionsCollection { totalCommitContributions totalIssueContributions totalPullRequestContributions totalPullRequestReviewContributions contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }'''
    try:
        if os.environ.get('GITHUB_ACTIONS') != 'true':
            raise RuntimeError('Contribution collection requires repository-scoped Actions token')
        result = api('graphql', {'query':query})
        if result.get('errors'):
            raise RuntimeError('GraphQL returned errors')
        snapshot['contributions'] = result['data']['user']['contributionsCollection']
        snapshot['contributions_status'] = 'ok'
    except (RuntimeError, urllib.error.HTTPError, KeyError):
        snapshot['contributions'] = None
        snapshot['contributions_status'] = 'unavailable'
        previous = ROOT / 'data/public.json'
        if previous.exists():
            old = json.loads(previous.read_text())
            if old.get('contributions_source') == 'public-actions':
                snapshot['contributions'] = old.get('contributions')
                snapshot['contributions_status'] = 'retained'
                snapshot['contributions_updated_at'] = old.get('contributions_updated_at')
    if snapshot['contributions_status'] == 'ok':
        snapshot['contributions_updated_at'] = snapshot['updated_at']
    if snapshot['contributions']:
        snapshot['contributions_source'] = 'public-actions'
    (ROOT / 'data/public.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
    render(snapshot, config)
    from update_private_projects import render_private
    render_private(ROOT)
    print(f'Generated profile: {len(repos)} public repositories; contributions: {snapshot["contributions_status"]}')

if __name__ == '__main__':
    main()
