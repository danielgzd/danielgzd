#!/usr/bin/env python3
"""Merge daily public-repo traffic without double counting overlapping 14-day windows."""
import datetime as dt
import json
from update_profile import ROOT, USER, api

def main():
    source = json.loads((ROOT/'data/public.json').read_text())
    path = ROOT/'data/traffic.json'
    history = json.loads(path.read_text()) if path.exists() else {'repositories':{}}
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    errors = []
    for repo in source['repositories']:
        if repo['fork']:
            continue
        name = repo['name']
        entry = history['repositories'].setdefault(name, {})
        for kind in ['views', 'clones']:
            try:
                result = api(f'repos/{USER}/{name}/traffic/{kind}?per=day')
                days = entry.setdefault(kind, {})
                for day in result[kind]:
                    days[day['timestamp'][:10]] = {'count':day['count'], 'uniques':day['uniques']}
                entry[kind+'_updated_at'] = now
            except Exception:
                errors.append(name+'/'+kind)
    history['last_attempt_at'] = now
    history['unavailable'] = errors
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2)+'\n')
    lines = ['# 官方仓库访问与克隆归档', '', f'最近采集尝试：{now}', '',
        '仅采集公开非 Fork 仓库。GitHub 提供最近 14 天窗口；脚本按 UTC 日期覆盖合并，避免重复累加窗口。当天数据尚未完整。每日 unique 不可相加当作跨日独立人数。中断超过窗口会永久缺失历史数据，未采集日期不补零。', '',
        '| 仓库 | 已记录浏览次数 | 已记录克隆次数 | 浏览采集成功时间（UTC） |', '| --- | ---: | ---: | --- |']
    for name, entry in history['repositories'].items():
        views = sum(d['count'] for d in entry.get('views',{}).values()) if 'views' in entry else '未取得'
        clones = sum(d['count'] for d in entry.get('clones',{}).values()) if 'clones' in entry else '未取得'
        lines.append(f"| [{name}](https://github.com/{USER}/{name}) | {views} | {clones} | {entry.get('views_updated_at','未取得')} |")
    lines += ['',f'本次不可用端点：{len(errors)}；旧数据保留原采集时间。无权限、限流或接口异常均不会伪装为零。', '', '原始逐日数据：[traffic.json](../data/traffic.json)。这些是仓库页面访问量，不是个人主页访客统计。', '']
    (ROOT/'docs/TRAFFIC.md').write_text('\n'.join(lines))
    print(f'Traffic archive updated; unavailable endpoints: {len(errors)}')

if __name__ == '__main__':
    main()
