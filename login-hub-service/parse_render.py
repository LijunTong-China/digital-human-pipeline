# -*- coding: utf-8 -*-
"""解码RENDER_DATA获取真实播放地址"""
import json, re
from urllib.parse import unquote

d = json.load(open('detail.json', encoding='utf-8'))
html = d['html']

# RENDER_DATA 是 <script id="RENDER_DATA">URL编码JSON</script>
m = re.search(r'<script[^>]*id="RENDER_DATA"[^>]*>([^<]+)</script>', html)
if not m:
    print('未找到RENDER_DATA脚本')
    raise SystemExit(1)

data = unquote(m.group(1))
print('RENDER_DATA 解码长度:', len(data))

# 播放地址
urls = re.findall(r'"(?:playAddr|play_addr)"[^"]*?"url_list":\["(https://[^"]+?)"', data)
print('playAddr url:', len(urls))
for u in urls[:2]:
    print('  ', u[:140])

# playApi
papis = re.findall(r'"playApi":"(/[^"]+|https://[^"]+)"', data)
print('playApi:', len(papis))
for p in papis[:2]:
    print('  ', ('https://www.douyin.com' + p if p.startswith('//') else p)[:140])

# 元数据
def find1(p):
    mm = re.search(p, data)
    return mm.group(1) if mm else None

desc = find1(r'"desc":"(.{5,200}?)"')
nick = find1(r'"nickname":"([^"]{1,40})"')
dur = find1(r'"duration":(\d{4,8})')
digg = find1(r'"digg_count":(\d+)')
cmt = find1(r'"comment_count":(\d+)')
shr = find1(r'"share_count":(\d+)')
print()
print('desc:', desc)
print('nickname:', nick)
print('duration(ms):', dur, '| 赞:', digg, '| 评:', cmt, '| 转:', shr)

# 保存
out = json.load(open('video_detail.json', encoding='utf-8'))
out.update({
    'desc': desc, 'author': nick,
    'duration_ms': int(dur) if dur else out.get('duration_ms', 0),
    'digg_count': int(digg or 0), 'comment_count': int(cmt or 0), 'share_count': int(shr or 0),
    'play_urls': urls or [],
    'play_api': (papis[0] if papis else None),
})
json.dump(out, open('video_detail.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('>>> video_detail.json 已更新')
