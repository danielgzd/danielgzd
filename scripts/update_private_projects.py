#!/usr/bin/env python3
"""Export reviewed private-project introductions and monthly activity; never export raw commit details."""
import collections
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.error
from update_profile import ROOT, USER, api, clean

PROJECT_KEYS = {'id','name','description','category','language','archived','commit_count','activity'}
SNAPSHOT_KEYS = {'schema_version','updated_month','window_start_month','window_end_month','projects'}


def read_private_api(path):
    for attempt in range(3):
        try:
            return api(path)
        except urllib.error.HTTPError as error:
            if error.code < 500 or attempt == 2:
                raise
        except (RuntimeError, urllib.error.URLError):
            if attempt == 2:
                raise


def summarize_commits(commits):
    months = collections.Counter()
    for commit in commits:
        date = commit.get('commit', {}).get('committer', {}).get('date')
        if not date:
            raise ValueError('Commit date missing')
        months[date[:7]] += 1
    return [{'month': month, 'commits': months[month]} for month in sorted(months, reverse=True)]


def validate_snapshot(data):
    if set(data) != SNAPSHOT_KEYS or data['schema_version'] != 3:
        raise ValueError('Only reviewed showcase schema version 3 may be published')
    for key in ['updated_month','window_start_month','window_end_month']:
        if not re.fullmatch(r'\d{4}-\d{2}',data[key]):
            raise ValueError('Only month precision is allowed')
    ids = set()
    for project in data['projects']:
        if set(project) != PROJECT_KEYS or not re.fullmatch(r'private-[0-9a-f]{12}',project['id']):
            raise ValueError('Invalid public private-project fields')
        if project['id'] in ids or not isinstance(project['name'],str) or not project['name'].strip():
            raise ValueError('Invalid display identity')
        ids.add(project['id'])
        for day in project['activity']:
            if set(day) != {'month','commits'} or not re.fullmatch(r'\d{4}-\d{2}',day['month']):
                raise ValueError('Daily or raw activity is not publishable')
        if sum(row['commits'] for row in project['activity']) != project['commit_count']:
            raise ValueError('Activity totals differ')


def render_private(root=ROOT):
    path = root / 'data/private-projects.json'
    if not path.exists():
        return
    data = json.loads(path.read_text())
    validate_snapshot(data)
    directory = root / 'docs/private-projects'
    directory.mkdir(parents=True, exist_ok=True)
    expected_pages = {p['id'] + '.md' for p in data['projects']}
    for page in directory.glob('*.md'):
        if page.name not in expected_pages:
            page.unlink()
    lines = ['# 非公开项目', '',
        '展示私有项目的名称、基本介绍与月度开发活动。点击项目名称查看更新记录；源码与敏感信息保持私有。', '',
        f"快照月份：{data['updated_month']}。统计为采集时近 365 天默认分支可达提交，包含所有作者。日期仅保留到月，不展示具体开发日期。", '',
        '| 项目 | 分类 | 主语言 | 窗口提交数 | 最近活动月份 | 基本介绍 |',
        '| --- | --- | --- | ---: | --- | --- |']
    for p in data['projects']:
        identity = p['id']
        lines += [f"| [{clean(p['name'])}](private-projects/{identity}.md) | {clean(p['category'])} | {clean(p['language'])} | {p['commit_count']} | {p['activity'][0]['month'] if p['activity'] else '窗口内无活动'} | {clean(p['description'])} |"]
        detail = [f"# {clean(p['name'])}", '', clean(p['description']), '',
            '- 项目状态：私有', f"- 分类：{clean(p['category'])}", f"- 主语言：{clean(p['language'])}",
            f"- 统计月份范围：{data['window_start_month']} 至 {data['window_end_month']}（首尾月为部分月份）",
            f"- 采集时近 365 天提交数：{p['commit_count']}（默认分支，所有作者）",
            f"- 快照月份：{data['updated_month']}", '',
            '## 更新记录', '', '仅按 UTC 月份汇总开发活动。提交标题、作者、邮箱、哈希、分支、文件路径、具体日期与源码均不展示。', '',
            '| 月份 | 提交次数 | 更新摘要 |', '| --- | ---: | --- |']
        for month in p['activity']:
            detail += [f"| {month['month']} | {month['commits']} | 项目维护与开发 |"]
        if not p['activity']:
            detail += ['| — | 0 | 统计窗口内无活动 |']
        detail += ['', '[返回非公开项目目录](../PRIVATE_PROJECTS.md) · [返回主页](../../README.md)', '']
        (directory / (identity + '.md')).write_text('\n'.join(detail))
    (root / 'docs/PRIVATE_PROJECTS.md').write_text('\n'.join(lines) + '\n')


def load_private_config():
    raw = os.environ.get('PRIVATE_PROJECTS_CONFIG_JSON')
    if raw:
        return json.loads(raw)
    default = Path.home()/'Library/Application Support/GitHubProfile/private-projects.json'
    path = Path(os.environ.get('PRIVATE_PROJECTS_CONFIG',str(default)))
    return json.loads(path.read_text())


def main():
    config = load_private_config()
    end = dt.datetime.now(dt.timezone.utc)
    start = end - dt.timedelta(days=365)
    window = urllib.parse.urlencode({'since': start.isoformat(), 'until': end.isoformat(), 'per_page':100})
    display = {p['id']:p for p in json.loads((ROOT/'profile.json').read_text())['private_project_display']}
    projects = []
    for index, entry in enumerate(config['projects'],1):
        name = entry['repository']
        if not re.fullmatch(r'[A-Za-z0-9._-]+',name):
            raise ValueError('Invalid repository configuration')
        repo = read_private_api(f'repos/{USER}/{name}')
        if repo['owner']['login'].lower() != USER or not repo['private']:
            raise ValueError('Expected owned private repository')
        commits = []
        page = 1
        while True:
            batch = read_private_api(f'repos/{USER}/{name}/commits?{window}&page={page}')
            commits.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        # Names and descriptions come only from explicitly reviewed public display metadata.
        public = display[entry['id']]
        projects.append({'id':entry['id'], 'name':public['name'],
            'description':public['description'],
            'category':public['category'], 'language':repo['language'], 'archived':repo['archived'],
            'commit_count':len(commits), 'activity':summarize_commits(commits)})
    snapshot = {'schema_version':3,'updated_month':end.strftime('%Y-%m'),
        'window_start_month':start.strftime('%Y-%m'),'window_end_month':end.strftime('%Y-%m'), 'projects':projects}
    validate_snapshot(snapshot)
    (ROOT / 'data/private-projects.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
    render_private(ROOT)
    print(f'Exported {len(projects)} reviewed private-project summaries')

if __name__ == '__main__':
    try:
        main()
    except Exception:
        # API error strings may contain private repository paths. Do not print exceptions.
        sys.exit('私有项目刷新失败；请在本地检查权限与映射配置，不输出私有请求详情。')
