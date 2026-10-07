"""抖音创作者同步服务 - 真实数据同步+自动转写全流程

流程: 订阅博主 → 抓主页最新视频 → 入库去重 → 新视频下载 → ASR转写 → 更新状态
"""
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

import config
from models import Creator, Video, SyncTask
from crawlers.douyin_crawler import get_crawler
from services.transcribe_service import TranscribeService

logger = logging.getLogger("sync_service")


class SyncService:
    """创作者同步执行器"""

    def __init__(self, db: Session):
        self.db = db
        self.crawler = get_crawler(config.LOGIN_SERVICE_URL)
        self.transcriber = TranscribeService(db)

    def sync_creator(self, creator_id: int, max_videos: int = 10) -> Dict[str, Any]:
        """同步单个创作者: 抓最新视频→入库→新视频自动转写"""
        creator = self.db.query(Creator).filter(Creator.id == creator_id).first()
        if not creator:
            return {"success": False, "error": "创作者不存在"}

        sec_uid = creator.creator_id  # creator_id 字段存 sec_uid
        if not sec_uid:
            self._mark_sync(creator, "failed", "缺少sec_user_id")
            return {"success": False, "error": "缺少sec_user_id"}

        if not self.crawler.login.health():
            self._mark_sync(creator, "failed", "登录态服务不可用")
            return {"success": False, "error": "登录态服务(3459)不可用"}

        # 创建同步任务记录
        task = SyncTask(task_type="creator_sync", target_id=creator_id, status="running",
                        started_at=datetime.utcnow())
        self.db.add(task)
        self.db.commit()

        try:
            videos = self.crawler.get_creator_videos(sec_uid, max_videos=max_videos)
            if not videos:
                self._mark_sync(creator, "failed", "未抓取到视频")
                self._finish_task(task, "failed", error="未抓取到视频")
                return {"success": False, "error": "未抓取到视频（可能触发风控或主页无视频）"}

            new_count, transcribed = 0, []
            for item in videos:
                aweme_id = item["aweme_id"]
                existing = self.db.query(Video).filter(Video.video_id == aweme_id).first()
                if existing:
                    continue

                # 详情拦截：真实标题/时长/互动数据（主页卡片常无标题）
                detail = self.crawler.get_video_detail(aweme_id) or {}
                title = detail.get("desc") or item.get("title") or "(无标题)"

                video = Video(
                    creator_id=creator.id,
                    video_id=aweme_id,
                    title=title,
                    description=detail.get("desc") or "",
                    published_at=datetime.utcnow(),  # 主页列表无精确发布时间, 用同步时间
                    duration=detail.get("duration_sec") or item.get("duration_sec") or 0,
                    stats_views=detail.get("play_count") or 0,
                    stats_likes=detail.get("digg_count") or 0,
                    stats_comments=detail.get("comment_count") or 0,
                    stats_shares=detail.get("share_count") or 0,
                    video_url=item.get("share_url"),
                    source="douyin_user_page",
                    sync_batch_id=str(task.id),
                    transcript_status="pending",
                )
                self.db.add(video)
                self.db.commit()
                self.db.refresh(video)
                new_count += 1

                # 新视频: 立即转写（详情页已带播放地址→下载→ASR）
                tr = self._transcribe_video(video, detail)
                if tr:
                    transcribed.append(aweme_id)

            self._mark_sync(creator, "success", None)
            result = {
                "success": True,
                "creator": creator.nickname,
                "total_crawled": len(videos),
                "new_videos": new_count,
                "transcribed": len(transcribed),
                "task_id": task.id,
            }
            self._finish_task(task, "success", result=result)
            logger.info(f"同步完成: {creator.nickname} 新增{new_count} 转写{len(transcribed)}")
            return result

        except Exception as e:
            self.db.rollback()
            self._mark_sync(creator, "failed", str(e))
            self._finish_task(task, "failed", error=str(e))
            logger.exception(f"同步异常: {creator.nickname}")
            return {"success": False, "error": str(e)}

    def _transcribe_video(self, video: Video, detail: Optional[Dict[str, Any]] = None) -> bool:
        """下载单个视频并ASR转写（L2a详情拦截/L2b share/L3捕获，多候选依次尝试）"""
        candidates: List[str] = []
        tmp_path = None
        try:
            # 先试详情拦截已带的播放地址（省一次detail请求）
            detail = detail if detail is not None else (self.crawler.get_video_detail(video.video_id) or {})
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp_path = tmp.name

            cookies = self.crawler.login.cookies()
            for play_url in detail.get("play_urls", []):
                if self.crawler.download_video(play_url, tmp_path, cookies):
                    candidates = [tmp_path]
                    break

            # 常规降级链（L2b share / L3 分段捕获）
            if not candidates:
                candidates = self.crawler.fetch_video_for_transcribe(video.video_id, tmp_path) or []

            if not candidates:
                logger.warning(f"下载失败, 转写跳过: {video.video_id}")
                return False

            # 依次尝试候选文件（L3捕获的音/视频轨分开，音轨文件能转写成功）
            text = None
            for path in candidates:
                if not os.path.exists(path) or os.path.getsize(path) < 10_000:
                    continue
                text = self.transcriber._transcribe_from_file(path)
                if text:
                    break

            if not text:
                self.transcriber.mark_transcribe_failed(video.id, "所有候选文件ASR均失败")
                return False

            video.transcript_status = "done"
            video.transcript_text = text
            video.transcript_language = "zh"
            video.transcribed_at = datetime.utcnow()
            video.stats_collected_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"转写完成: {video.video_id} ({len(text)}字)")
            return True
        except Exception as e:
            logger.exception(f"转写异常: {video.video_id} - {e}")
            self.transcriber.mark_transcribe_failed(video.id, str(e))
            return False
        finally:
            for p in set(candidates) | {tmp_path}:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

    def _mark_sync(self, creator: Creator, status: str, error: Optional[str]):
        creator.last_sync_time = datetime.utcnow()
        creator.last_sync_status = status
        creator.video_count = self.db.query(Video).filter(Video.creator_id == creator.id).count()
        if error:
            logger.error(f"同步失败[{creator.nickname}]: {error}")
        self.db.commit()

    def _finish_task(self, task: SyncTask, status: str, result: Optional[Dict] = None,
                     error: Optional[str] = None):
        task.status = status
        task.result = result
        task.error_message = error
        task.completed_at = datetime.utcnow()
        self.db.commit()


# 服务工厂
def get_sync_service() -> SyncService:
    from models import get_db
    db = next(get_db())
    return SyncService(db)
