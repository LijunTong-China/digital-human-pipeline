# -*- coding: utf-8 -*-
"""解析详情页: 反转义JSON, 提取真实视频信息+播放地址"""
import json, re, codecs

d = json.load(open('detail.json', encoding='utf-8'))
html = d['html']
print('页面标题:', d.get('title'))
print('HTML长度:', len(html))

# 反转义: \" -> "  & -> &
raw = html.replace('\\u0026', '&').replace('\\/', '/')
decoded = raw.replace('\\"', '"')

def find1(pat, s=decoded, flags=0):
    m = re.search(pat, s, flags)
    return m.group(1) if m else None

print()
desc = find1(r'"desc":"(.{5,200}?)"')
print('desc:', desc)
author = find1(r'"nickname":"(.{1,40}?)"')
print('author:', author)
dur = find1(r'"duration":(\d{4,8})')
print('duration(ms):', dur)
digg = find1(r'"digg_count":(\d+)')
cmt = find1(r'"comment_count":(\d+)')
shr = find1(r'"share_count":(\d+)')
print(f'digg:{digg} comment:{cmt} share:{shr}')

# 播放地址
urls = re.findall(r'"(?:playAddr|play_addr)":\{[^{}]*?"url_list":\["(https://[^"]+?)"', decoded)
print('playAddr url数量:', len(urls))
for u in urls[:3]:
    print('  ', u[:130])

# 备用: playApi
papi = find1(r'"playApi":"(//[^"]+|https://[^"]+)"')
print('playApi:', (papi or '')[:130])

# 保存
out = {'desc': desc, 'author': author, 'duration_ms': int(dur) if dur else 0,
       'digg_count': int(digg or 0), 'comment_count': int(cmt or 0), 'share_count': int(shr or 0),
       'play_urls': urls, 'play_api': papi, 'video_id': json.load(open('pick.json'))['first_video'],
       'cookies': d.get('cookies')}
json.dump(out, open('video_detail.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('>>> 已保存 video_detail.json')
