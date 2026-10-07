# -*- coding: utf-8 -*-
"""阶段A: 真实热点 + 真登录态浏览器搜索视频列表"""
import json
import os
import shutil
import sys
import time
import urllib.parse

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# ---------- 1. 真实热点榜 ----------
print(">>> 获取抖音实时热点榜...")
r = requests.get("https://www.iesdouyin.com/web/api/v2/hotsearch/billboard/word/",
                 headers={"User-Agent": UA}, timeout=15)
hot_data = r.json()
active_time = hot_data.get("active_time")
hot_words = [{"word": w["word"], "hot_value": w["hot_value"]} for w in hot_data["word_list"][:10]]
print(f"热点榜更新时间: {active_time}")
for i, w in enumerate(hot_words, 1):
    print(f"  {i}. {w['word']}  (热度:{w['hot_value']:,})")

# 选第1个热点词
keyword = hot_words[0]["word"]
print(f"\n>>> 选定热点词: {keyword}")

# ---------- 2. 复制登录态浏览器配置 ----------
SRC_PROFILE = r"E:\selfProject\cloneAIProject\login-hub-service\browser_data\douyin"
PROFILE = r"E:\selfProject\cloneAIProject\hotspot-monitor-service\.chrome_profile"
if os.path.exists(PROFILE):
    shutil.rmtree(PROFILE, ignore_errors=True)
print(">>> 复制登录态浏览器配置(约100MB)...")
shutil.copytree(SRC_PROFILE, PROFILE, ignore=shutil.ignore_patterns("*.log", "LOCK"))

# ---------- 3. DrissionPage 打开搜索页 ----------
from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.set_paths(user_data_path=PROFILE)
co.set_argument("--window-size", "1400,900")
co.set_argument("--disable-blink-features=AutomationControlled")
co.headless(False)

print(">>> 启动浏览器(带登录态)...")
page = ChromiumPage(co)
try:
    search_url = f"https://www.douyin.com/search/{urllib.parse.quote(keyword)}?type=video"
    print(f">>> 打开搜索页: {search_url}")
    page.get(search_url)
    time.sleep(6)

    # 登录态检查
    logged = any(c.get("name") == "sessionid" and c.get("value") for c in page.cookies())
    print(f">>> 浏览器登录态(sessionid): {logged}")

    # 滚动加载更多
    for _ in range(3):
        page.scroll.to_bottom()
        time.sleep(2)

    # ---------- 4. 提取真实视频卡片 ----------
    print(">>> 提取搜索结果...")
    videos = []
    seen = set()
    # 搜索结果卡片链接形如 /video/<id> 或 /note/<id>
    cards = page.eles("xpath://a[contains(@href,'/video/') or contains(@href,'/note/')]")
    for a in cards:
        href = a.attr("href") or ""
        vid = href.split("/video/")[-1].split("/note/")[-1].split("?")[0].strip("/")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        # 标题: 卡片内文本
        title = (a.attr("aria-label") or a.text or "").strip()[:120]
        videos.append({"aweme_id": vid, "title": title, "href": href})
        if len(videos) >= 8:
            break

    print(f">>> 提取到 {len(videos)} 个真实视频:")
    for v in videos:
        print(f"   [{v['aweme_id']}] {v['title'][:60]}")

    # 保存浏览器cookies供下载用
    cookies = {c["name"]: c["value"] for c in page.cookies()}

    out = {"active_time": active_time, "hot_words": hot_words, "keyword": keyword,
           "logged_in": logged, "videos": videos, "cookies": cookies}
    with open("real_data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(">>> 已保存 real_data.json")
finally:
    page.quit()
    print(">>> 浏览器已关闭")
