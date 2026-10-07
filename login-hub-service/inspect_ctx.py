# -*- coding: utf-8 -*-
"""检查playAddr真实JSON上下文"""
import json, re

d = json.load(open('search_result.json', encoding='utf-8'))
html = d['html']

i = html.find('playAddr')
print('playAddr上下文:')
print(html[i-100:i+400])
print()
print('aweme_id上下文:')
j = html.find('aweme_id')
print(html[j-50:j+200] if j >= 0 else '(未找到aweme_id)')
print()
print('desc上下文:')
k = html.find('"desc"')
print(html[k:k+300] if k >= 0 else '(未找到desc)')
