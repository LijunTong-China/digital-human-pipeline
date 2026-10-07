#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阶段2端到端真实链路测试

链路: 创作者 → 视频 → (模拟转写文本) → LLM提取选题入库 → 向量去重 → ASR下载转写验证
前置: docker/.env 已配置 LLM/ASR 密钥; 容器 postgres 已建表
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DOCKER_ENV = os.path.join(BASE, "..", "docker", ".env")

# 1) 加载 docker/.env 到环境变量
with open(DOCKER_ENV, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# 2) 指向容器数据库
os.environ["DATABASE_URL"] = "postgresql://cloneai:cloneai_pass@localhost:15433/hotspot_monitor"
sys.path.insert(0, BASE)

PASS, FAIL = "✅", "❌"
results = []


def record(name, ok, detail):
    results.append((name, ok, detail))
    print(f"{PASS if ok else FAIL} {name}: {detail}\n")


print("=" * 60)
print("阶段2 端到端真实链路测试")
print("=" * 60)

from models.database import init_db, engine, Creator, Video, Topic
from models import get_db
from sqlalchemy import text as sql_text
from services.creator_service import CreatorService, CreatorCreate
from services.video_service import VideoService, VideoCreate
from services.topic_service import TopicService
from services.transcribe_service import TranscribeService
from datetime import datetime

# ---- 步骤0: 数据库 ----
init_db()
db = next(get_db())

# 清理上次测试数据
db.query(Topic).delete()
db.query(Video).delete()
db.query(Creator).delete()
db.commit()
record("步骤0 数据库连接与建表", True, "已连接容器postgres(15433)，历史测试数据已清理")

# ---- 步骤1: 创建创作者 ----
creator_svc = CreatorService(db)
creator = creator_svc.create_creator(CreatorCreate(
    nickname="E2E测试博主", platform="douyin", creator_id="e2e_001",
    is_active=True, sync_interval_hours=24
))
record("步骤1 创建创作者", creator is not None, f"id={creator.id}, nickname={creator.nickname}")

# ---- 步骤2: 创建视频（预置转写文本，模拟ASR输出） ----
video_svc = VideoService(db)
TRANSCRIPT = ("大家好，今天聊聊AI视频自动化这个话题。现在用AI一键生成短视频已经非常成熟了，"
              "从写脚本、AI配音到自动生成画面全流程自动化，一个人一天能做几十条视频。"
              "很多普通人靠这个方法做自媒体，三个月就涨粉十万，接广告变现。"
              "后面我还会分享具体的工具清单和操作步骤，记得点赞关注。")
video = video_svc.create_video(VideoCreate(
    creator_id=creator.id, video_id="e2e_video_001",
    title="AI视频自动化全流程演示", description="测试视频",
    published_at=datetime.utcnow(), duration=180,
    stats_views=50000, stats_likes=2000,
))
# 直接写入转写文本（模拟ASR完成后的状态）
video.transcript_status = "done"
video.transcript_text = TRANSCRIPT
db.commit()
record("步骤2 创建视频+预置转写文本", video is not None,
       f"id={video.id}, title={video.title}, 转写文本{len(TRANSCRIPT)}字")

# ---- 步骤3: LLM真实提取选题 ----
topic_svc = TopicService(db)
t0 = datetime.now()
result = topic_svc.extract_topics_from_video(video.id)
elapsed = (datetime.now() - t0).total_seconds()
topics = db.query(Topic).filter(Topic.source_video_id == video.id).all()
ok = result and result.get("success") and len(topics) > 0
record("步骤3 LLM提取选题(真实API)", ok,
       f"提取{len(topics)}个选题, 耗时{elapsed:.1f}s: " +
       "; ".join(f"[{t.title}] (向量:{'✓' if t.embedding else '✗'})" for t in topics))

# ---- 步骤4: 向量去重（真实embedding API） ----
dup_topic = Topic(
    source_video_id=video.id,
    title=topics[0].title if topics else "重复选题",  # 与第一个选题同标题 → 必然重复
    summary="去重测试",
    status="pending"
)
db.add(dup_topic)
db.commit()
before_dup = db.query(Topic).filter(Topic.status == "duplicate").count()
dedup_result = topic_svc.deduplicate_topics(video.id)
after_dup = db.query(Topic).filter(Topic.status == "duplicate").count()
ok = dedup_result.get("success") and after_dup >= 1
record("步骤4 向量去重(真实bge-m3)", ok,
       f"共{dedup_result.get('total_count')}个选题, 标记重复{dedup_result.get('duplicate_count')}个 "
       f"(阈值{os.environ.get('VECTOR_SIMILARITY_THRESHOLD', '0.85')})")

# ---- 步骤5: ASR下载+转写链路（公开测试音频） ----
transcribe_svc = TranscribeService(db)
TEST_AUDIO_URL = "https://download.samplelib.com/mp3/sample-6s.mp3"
try:
    text_result = transcribe_svc._transcribe_from_url(TEST_AUDIO_URL)
    ok = text_result is not None  # 音乐类音频可能无语音内容，返回空串也算链路通过
    record("步骤5 ASR下载+转写链路(真实API)", ok,
           f"下载mp3→上传SiliconFlow→返回: {text_result!r}")
except Exception as e:
    record("步骤5 ASR下载+转写链路(真实API)", False, f"{type(e).__name__}: {str(e)[:150]}")

# ---- 步骤6: 数据落库完整性验证 ----
counts = {}
with engine.connect() as c:
    for table in ["creators", "creator_videos", "topics"]:
        counts[table] = c.execute(sql_text(f"SELECT COUNT(*) FROM {table}")).scalar()
vec_count = db.query(Topic).filter(Topic.embedding.isnot(None)).count()
ok = counts["creators"] >= 1 and counts["creator_videos"] >= 1 and counts["topics"] >= 3 and vec_count >= 2
record("步骤6 数据落库完整性", ok,
       f"creators={counts['creators']}, videos={counts['creator_videos']}, "
       f"topics={counts['topics']}, 含向量={vec_count}")

# ---- 汇总 ----
print("=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
print(f"测试汇总: {passed}/{len(results)} 通过")
for name, ok, _ in results:
    print(f"  {PASS if ok else FAIL} {name}")
print("=" * 60)
sys.exit(0 if passed == len(results) else 1)
