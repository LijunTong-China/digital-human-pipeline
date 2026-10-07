# -*- coding: utf-8 -*-
"""探测详情页中真实的播放地址和元数据"""
import json, re

d = json.load(open('detail.json', encoding='utf-8'))
html = d['html']

# 页面title就是真实标题
print('真实标题:', d.get('title'))

# 反转义
decoded = html.replace('\\u0026', '&').replace('\\"', '"').replace('\\/', '/')

probes = ['v1/play', 'play_addr', 'playAddr', 'playApi', 'mime_type', '<video', 'video/src',
          'og:video', 'aweme/detail', 'awemeDetail', 'RENDER_DATA', 'ROUTER_DATA', 'item_list']
for p in probes:
    print(f'{p!r}: {decoded.count(p)}')

# video标签
for m in re.finditer(r'<video[^>]*>', decoded):
    tag = m.group(0)
    src = re.search(r'src="([^"]{10,200})"', tag)
    print('video标签 src:', (src.group(1)[:150] if src else '(blob或无src)'))
    break

# v1/play 上下文
i = decoded.find('v1/play')
if i > 0:
    print()
    print('v1/play 上下文:')
    print(decoded[i-250:i+250])
