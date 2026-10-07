# -*- coding: utf-8 -*-
"""真实抖音同步+转写测试: 订阅真实博主 → 抓主页最新视频 → 入库 → ASR转写"""
import os
import sys
import json

BASE = os.path.dirname(os.path.abspath(__file__))
# 加载密钥
with open(os.path.join(BASE, "..", "docker", ".env"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
os.environ["DATABASE_URL"] = "postgresql://cloneai:cloneai_pass@localhost:15433/hotspot_monitor"
sys.path.insert(0, BASE)

from models.database import Creator, Video, get_db
from services.sync_service import SyncService
from datetime import datetime

db = next(get_db())

# 真实博主: 哈佛老徐抓AI趋势 (sec_uid来自原系统公开数据)
REAL_SEC_UID = "MS4wLjABAAAAEMfJKktSQaUca9ThGGFBxiQaXF3WgkswT3j-bIjaoupi3NTK6g8nKaaKCELdx5yA"

creator = db.query(Creator).filter(Creator.creator_id == REAL_SEC_UID).first()
if not creator:
    creator = Creator(nickname="哈佛老徐抓AI趋势", note="真实订阅-AI趋势", platform="douyin",
                      creator_id=REAL_SEC_UID, is_active=True, sync_interval_hours=24)
    db.add(creator)
    db.commit()
    db.refresh(creator)
print(f"订阅博主: {creator.nickname} (id={creator.id})")

svc = SyncService(db)
t0 = datetime.now()
result = svc.sync_creator(creator.id, max_videos=3)
elapsed = (datetime.now() - t0).total_seconds()
print(f"\n同步结果 (耗时{elapsed:.0f}s): {json.dumps(result, ensure_ascii=False, indent=1)}")

# 展示入库数据
print("\n===== 入库的真实视频 =====")
videos = db.query(Video).filter(Video.creator_id == creator.id).order_by(Video.id.desc()).limit(5).all()
for v in videos:
    print(f"[{v.id}] {v.video_id} | {v.title[:40]}")
    print(f"    转写: {v.transcript_status}", end="")
    if v.transcript_text:
        print(f" ({len(v.transcript_text)}字) | 开头: {v.transcript_text[:60]}...")
    else:
        print()
