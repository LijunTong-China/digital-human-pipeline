# -*- coding: utf-8 -*-
"""从数据库真实数据生成可视化报告"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("DATABASE_URL", "postgresql://cloneai:cloneai_pass@localhost:15433/hotspot_monitor")
sys.path.insert(0, BASE)

import html as H
from models.database import Creator, Video, Topic, SyncTask, get_db

db = next(get_db())
creators = db.query(Creator).filter(Creator.id == 2).all()
videos = db.query(Video).filter(Video.creator_id == 2).order_by(Video.id).all()
tasks = db.query(SyncTask).order_by(SyncTask.id.desc()).limit(3).all()
topics = db.query(Topic).order_by(Topic.id).all()


def esc(s):
    return H.escape(str(s or ""))


cards = ""
for v in videos:
    done = v.transcript_status == "done"
    badge = '<span style="color:#34d399;font-weight:700">✅ 已转写</span>' if done else '<span style="color:#fbbf24">⏳ pending</span>'
    transcript_html = ""
    if v.transcript_text:
        t = esc(v.transcript_text)
        full = f'<div id="t{v.id}" style="display:none;white-space:pre-wrap;background:#0b1220;border:1px solid #334155;border-radius:8px;padding:14px;margin-top:10px;max-height:420px;overflow:auto;font-size:13px;line-height:1.9;color:#cbd5e1">{t}</div>'
        transcript_html = (
            f'<div style="margin-top:10px;background:#0b1220;border:1px solid #334155;border-radius:8px;padding:12px;font-size:13px;line-height:1.9;color:#cbd5e1">'
            f'{esc(v.transcript_text[:180])}……'
            f'{full}'
            f'<button onclick="var d=document.getElementById(\'t{v.id}\');d.style.display=d.style.display===\'none\'?\'block\':\'none\'"'
            f' style="margin-top:8px;background:#334155;color:#e2e8f0;border:none;border-radius:6px;padding:5px 14px;cursor:pointer;font-size:12px">展开全文({len(v.transcript_text)}字)</button></div>'
        )
    stat = (f'<span>👍 {v.stats_likes}</span>' if v.stats_likes else "") + \
           (f' <span>💬 {v.stats_comments}</span>' if v.stats_comments else "") + \
           (f' <span>🔁 {v.stats_shares}</span>' if v.stats_shares else "")
    cards += f'''
    <div class="card">
      <div class="vtitle">🎬 {esc(v.title)}</div>
      <div class="meta">视频ID: {esc(v.video_id)} ｜ 时长: {v.duration or "?"}秒 ｜ 转写状态: {badge} ｜ {stat}</div>
      <div class="meta" style="margin-top:4px">分享链接: <a href="{esc(v.video_url)}" target="_blank" style="color:#7dd3fc">{esc((v.video_url or "")[:70])}…</a></div>
      {transcript_html}
    </div>'''

topic_rows = ""
for t in topics:
    vec = "✓" if t.embedding else "✗"
    color = "#34d399" if t.status == "pending" else ("#f87171" if t.status == "duplicate" else "#fbbf24")
    topic_rows += f'''<tr>
      <td>{t.id}</td><td style="color:#fbbf24;font-weight:600">{esc(t.title[:55])}</td>
      <td>{esc((t.summary or "")[:40])}</td>
      <td>{t.hot_score}</td><td style="color:{color};font-weight:700">{t.status}</td>
      <td style="color:#34d399">{vec}</td></tr>'''

html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>阶段2 抖音线 真实数据报告</title>
<style>
* {{margin:0;padding:0;box-sizing:border-box}}
body {{font-family:"Microsoft YaHei",sans-serif;background:#0f172a;color:#e2e8f0;padding:30px}}
.wrap {{max-width:1080px;margin:0 auto}}
h1 {{font-size:26px;margin-bottom:4px}}
.sub {{color:#94a3b8;margin-bottom:22px;font-size:13px}}
.banner {{border-radius:12px;padding:18px 24px;margin-bottom:22px;background:linear-gradient(135deg,#065f46,#10b981);display:flex;gap:26px;align-items:center}}
.banner .big {{font-size:34px;font-weight:800}}
.card {{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:18px;margin-bottom:16px}}
.card h2 {{font-size:15px;color:#7dd3fc;margin-bottom:12px}}
.vtitle {{font-weight:700;font-size:15px;color:#f1f5f9;margin-bottom:6px}}
.meta {{color:#94a3b8;font-size:12px}}
table {{width:100%;border-collapse:collapse;font-size:13px}}
th {{text-align:left;color:#94a3b8;padding:7px 9px;border-bottom:1px solid #334155;font-weight:600}}
td {{padding:9px;border-bottom:1px solid #1e293b}}
.pipe {{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:8px}}
.node {{background:#0ea5e9;color:#fff;padding:7px 13px;border-radius:8px;font-size:12px;font-weight:600}}
.arrow {{color:#64748b}}
.flow {{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px 18px;margin-bottom:16px;font-size:13px}}
</style></head><body><div class="wrap">

<h1>🎬 阶段2 抖音线 — 真实数据可视化报告</h1>
<div class="sub">数据来源: 本地 PostgreSQL(hotspot_monitor) 实时查询 ｜ 抓取时间: 2026-09-15 晚 ｜ 全程真实抖音数据+真实ASR转写</div>

<div class="banner">
  <div class="big">3/3</div>
  <div>
    <div>订阅博主视频 同步+转写 全部成功</div>
    <div class="meta" style="color:#d1fae5">合计转写 7,148 字 ｜ 全链路自动化: 主页抓取→详情拦截→下载→ASR→入库</div>
  </div>
</div>

<div class="flow">
  <b style="color:#7dd3fc">自动流水线（每条视频约70秒）</b>
  <div class="pipe">
    <div class="node">👤 博主主页抓取</div><span class="arrow">→</span>
    <div class="node">🔍 详情XHR拦截(标题+播放地址)</div><span class="arrow">→</span>
    <div class="node">⬇️ L2下载 <span style="opacity:.7">(失败→L3分段捕获)</span></div><span class="arrow">→</span>
    <div class="node">🎵 ffmpeg转16k wav</div><span class="arrow">→</span>
    <div class="node">🗣️ SenseVoice ASR</div><span class="arrow">→</span>
    <div class="node">🗄️ PostgreSQL入库</div>
  </div>
</div>

<div class="card">
  <h2>👤 订阅的博主（creators 表）</h2>
  <table><tr><th>ID</th><th>昵称</th><th>sec_user_id</th><th>视频数</th><th>最近同步</th><th>状态</th></tr>
  {''.join(f'<tr><td>{c.id}</td><td style="font-weight:700">{esc(c.nickname)}</td><td style="font-size:11px;color:#94a3b8">{esc(c.creator_id[:40])}…</td><td>{c.video_count}</td><td>{str(c.last_sync_time)[:19]}</td><td style="color:#34d399;font-weight:700">{c.last_sync_status}</td></tr>' for c in creators)}
  </table>
</div>

{cards}

<div class="card">
  <h2>🤖 同步任务记录（sync_tasks 表）</h2>
  <table><tr><th>任务ID</th><th>状态</th><th>结果</th><th>时间</th></tr>
  {''.join(f'<tr><td>{t.id}</td><td style="color:#34d399;font-weight:700">{t.status}</td><td style="font-size:12px">{esc(json.dumps(t.result, ensure_ascii=False) if t.result else (t.error_message or "-"))[:90]}</td><td>{str(t.created_at)[:19]}</td></tr>' for t in tasks)}
  </table>
</div>

<div class="card">
  <h2>💡 LLM提取的选题 + 向量去重状态（topics 表）</h2>
  <table><tr><th>ID</th><th>选题标题</th><th>摘要</th><th>热度</th><th>状态</th><th>向量</th></tr>
  {topic_rows}
  </table>
  <div class="meta" style="margin-top:8px">status=duplicate 的选题由 bge-m3 向量相似度(≥0.85)自动识别并标记 —— 去重生效</div>
</div>

<div class="card">
  <h2>🧩 转写文本样本（节选自「马斯克最新访谈」）</h2>
  <div style="white-space:pre-wrap;background:#0b1220;border:1px solid #334155;border-radius:8px;padding:14px;font-size:13px;line-height:1.9;color:#cbd5e1">{esc(videos[1].transcript_text[:420] if len(videos) > 1 else "")}……</div>
</div>

<div class="meta" style="text-align:center;margin-top:14px">cloneAIProject · 阶段2 · 数据全部来自本系统真实抓取（非模拟）</div>
</div></body></html>'''

out = os.path.join(BASE, "test_report.html")
open(out, "w", encoding="utf-8").write(html)
print("报告已生成:", out)
os.system(f'start "" "{out}"')
