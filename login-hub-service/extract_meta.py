# -*- coding: utf-8 -*-
"""从真实搜索页HTML提取视频元数据"""
import json
import re
import html as htmllib

d = json.load(open('search_result.json', encoding='utf-8'))
html = d['html']

ids = re.findall(r'"aweme_id":"(\d{15,20})"', html)
descs = re.findall(r'"desc":"((?:[^"\\\\]|\\\\.){5,120})"', html)
plays = re.findall(r'"playAddr":\{"uri":"[^"]*","url_list":\["(https:[^"]+?)"', html)
authors = re.findall(r'"nickname":"([^"]{1,30})"', html)
digs = re.findall(r'"digg_count":(\d+)', html)
cmts = re.findall(r'"comment_count":(\d+)', html)
durs = re.findall(r'"duration":(\d{3,7})', html)

print('aweme_id:', len(ids), '| desc:', len(descs), '| playAddr:', len(plays),
      '| nickname:', len(authors), '| digg:', len(digs), '| dur:', len(durs))
print()

def unesc(s):
    try:
        return htmllib.unescape(s.encode('utf-8', 'ignore').decode('unicode_escape', 'ignore'))
    except Exception:
        return s

for i in range(min(8, len(plays))):
    desc = unesc(descs[i]) if i < len(descs) else '?'
    dur = f"{int(durs[i])//1000}s" if i < len(durs) else '?'
    print(f"[{i}] id: {ids[i] if i < len(ids) else '?'} | 时长: {dur}")
    print(f"    标题: {desc[:60]}")
    print(f"    作者: {authors[i] if i < len(authors) else '?'} | 赞:{digs[i] if i < len(digs) else '?'} | 评:{cmts[i] if i < len(cmts) else '?'}")
    print(f"    play: {plays[i][:110]}")
    print()

# 保存结构化结果
videos = []
n = min(len(plays), len(descs), 10)
for i in range(n):
    videos.append({
        'aweme_id': ids[i] if i < len(ids) else '',
        'title': unesc(descs[i]),
        'author': authors[i] if i < len(authors) else '',
        'duration_ms': int(durs[i]) if i < len(durs) else 0,
        'digg_count': int(digs[i]) if i < len(digs) else 0,
        'comment_count': int(cmts[i]) if i < len(cmts) else 0,
        'play_url': plays[i],
    })
json.dump({'keyword': d.get('keyword'), 'videos': videos, 'cookies': d.get('cookies')},
          open('real_videos.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'>>> 已保存 {len(videos)} 个真实视频到 real_videos.json')
