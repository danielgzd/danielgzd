#!/usr/bin/env python3
"""Export approved private-project metadata and daily counts; never export source or messages."""
import collections
import datetime as dt
import json
import urllib.parse
from update_profile import ROOT, USER, api, clean


def summarize_commits(commits):
    days = collections.Counter()
    for commit in commits:
        date = commit.get('commit', {}).get('committer', {}).get('date')
        if not date:
            raise ValueError('Commit date missing; refusing partial statistics')
        days[date[:10]] += 1
    return [{'date': date, 'commits': days[date]} for date in sorted(days, reverse=True)]


def render_private(root=ROOT):
    path = root / 'data/private-projects.json'
    if not path.exists():
        return
    data = json.loads(path.read_text())
    directory = root / 'docs/private-projects'
    directory.mkdir(parents=True, exist_ok=True)
    lines = ['# 非公开项目', '',
        '这些项目保留私有，仅展示基本介绍和按日汇总的更新记录。点击项目名称查看公开更新页，无法从这里浏览源码。', '',
        f"统计快照：{data['updated_at']}。统计窗口为近 365 天，按默认分支可达提交计算，包含所有作者；不是个人贡献数，也不是所有分支或终身总量。", '',
        '| 项目 | 分类 | 主语言 | 近 365 天提交 | 最近提交日期（UTC） | 基本介绍 |',
        '| --- | --- | --- | ---: | --- | --- |']
    for p in data['projects']:
        name = p['name']
        lines += [f"| [{clean(name)}](private-projects/{name}.md) | {clean(p['category'])} | {clean(p['language'])} | {p['commit_count']} | {p['activity'][0]['date'] if p['activity'] else '窗口内无提交'} | {clean(p['description'])} |"]
        detail = [f'# {clean(name)}', '', clean(p['description']), '',
            f"- 项目状态：私有{' · 已归档' if p['archived'] else ''}",
            f"- 分类：{clean(p['category'])}", f"- 主语言：{clean(p['language'])}",
            f"- 统计区间：{data['window_start'][:10]} 至 {data['window_end'][:10]}（UTC）",
            f"- 区间提交数：{p['commit_count']}（默认分支，所有作者）",
            f"- 数据采集时间：{data['updated_at']}", '',
            '## 更新记录', '', '以下为按 UTC 日期汇总的开发活动，不包含提交标题、作者、邮箱、哈希、分支、文件路径、差异或源码。', '',
            '| 日期（UTC） | 提交次数 | 更新摘要 |', '| --- | ---: | --- |']
        for day in p['activity']:
            detail += [f"| {day['date']} | {day['commits']} | 项目开发更新 |"]
        if not p['activity']:
            detail += ['| — | 0 | 统计窗口内没有可达提交 |']
        detail += ['', '[返回非公开项目目录](../PRIVATE_PROJECTS.md) · [返回主页](../../README.md)', '']
        (directory / (name + '.md')).write_text('\n'.join(detail))
    (root / 'docs/PRIVATE_PROJECTS.md').write_text('\n'.join(lines) + '\n')


def main():
    config = json.loads((ROOT / 'profile.json').read_text())
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=365)
    window = urllib.parse.urlencode({'since': start.isoformat(), 'until': end.isoformat(), 'per_page':100})
    projects = []
    for entry in config['private_projects']:
        name = entry['name']
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-' for c in name):
            raise ValueError('Invalid configured project name')
        repo = api(f'repos/{USER}/{name}')
        if repo['owner']['login'].lower() != USER or not repo['private']:
            raise ValueError('Configured repository is not an owned private repository')
        commits = []
        page = 1
        while True:
            batch = api(f'repos/{USER}/{name}/commits?{window}&page={page}')
            commits.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        activity = summarize_commits(commits)
        projects.append({'name':name, 'description':entry['description'], 'category':entry['category'],
            'language':repo['language'], 'archived':repo['archived'], 'commit_count':len(commits), 'activity':activity})
    # No raw API responses are written; failure above leaves the last complete snapshot intact.
    snapshot = {'updated_at':end.isoformat(timespec='seconds'), 'window_start':start.isoformat(),
        'window_end':end.isoformat(), 'projects':projects}
    (ROOT / 'data/private-projects.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
    render_private(ROOT)
    print(f'Exported sanitized summaries for {len(projects)} configured private projects')

if __name__ == '__main__':
    main()
