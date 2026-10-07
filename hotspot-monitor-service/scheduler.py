"""任务调度模块"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from models import Creator, SyncTask
from services import get_creator_service, get_video_service, get_transcribe_service, get_topic_service
from crawlers.douyin_crawler import DouyinCrawler

logger = logging.getLogger("scheduler")


class HotspotMonitorScheduler:
    """热点监控调度器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.crawler = DouyinCrawler()
        self.creator_service = get_creator_service()
        self.video_service = get_video_service()
        self.transcribe_service = get_transcribe_service()
        self.topic_service = get_topic_service()

    def start(self):
        """启动调度器"""
        try:
            # 添加定时任务
            self._add_sync_tasks()
            self._add_transcribe_tasks()
            self._add_topic_extraction_tasks()
            self._add_deduplication_tasks()

            # 启动调度器
            self.scheduler.start()
            logger.info("调度器启动成功")
        except Exception as e:
            logger.error(f"调度器启动失败: {e}")
            raise

    def stop(self):
        """停止调度器"""
        try:
            self.scheduler.shutdown()
            logger.info("调度器停止成功")
        except Exception as e:
            logger.error(f"调度器停止失败: {e}")

    def _add_sync_tasks(self):
        """添加创作者同步任务"""
        # 每小时同步一次活跃创作者
        self.scheduler.add_job(
            self._sync_creators,
            trigger=IntervalTrigger(hours=1),
            id="sync_creators",
            name="创作者同步任务",
            replace_existing=True
        )

        # 每天凌晨同步一次所有创作者
        self.scheduler.add_job(
            self._sync_all_creators,
            trigger=CronTrigger(hour=0, minute=0),
            id="sync_all_creators",
            name="全量创作者同步任务",
            replace_existing=True
        )

    def _add_transcribe_tasks(self):
        """添加视频转写任务"""
        # 每30分钟检查并转写待处理视频
        self.scheduler.add_job(
            self._process_transcribe_queue,
            trigger=IntervalTrigger(minutes=30),
            id="process_transcribe_queue",
            name="视频转写任务",
            replace_existing=True
        )

    def _add_topic_extraction_tasks(self):
        """添加选题提取任务"""
        # 每1小时提取新视频的选题
        self.scheduler.add_job(
            self._extract_topics,
            trigger=IntervalTrigger(hours=1),
            id="extract_topics",
            name="选题提取任务",
            replace_existing=True
        )

    def _add_deduplication_tasks(self):
        """添加选题去重任务"""
        # 每2小时执行选题去重
        self.scheduler.add_job(
            self._deduplicate_topics,
            trigger=IntervalTrigger(hours=2),
            id="deduplicate_topics",
            name="选题去重任务",
            replace_existing=True
        )

    async def _sync_creators(self):
        """同步活跃创作者"""
        try:
            creators = self.creator_service.get_active_creators()
            for creator in creators:
                # 检查是否需要同步
                if (not creator.last_sync_time or
                    datetime.utcnow() - creator.last_sync_time > timedelta(hours=creator.sync_interval_hours)):
                    result = self.creator_service.sync_creator_videos(creator.id)
                    logger.info(f"创作者同步任务创建: {creator.id} - {creator.nickname}")
        except Exception as e:
            logger.error(f"创作者同步任务异常: {e}")

    async def _sync_all_creators(self):
        """同步所有创作者"""
        try:
            creators = self.creator_service.get_creators()
            for creator in creators:
                result = self.creator_service.sync_creator_videos(creator.id)
                logger.info(f"全量创作者同步任务创建: {creator.id} - {creator.nickname}")
        except Exception as e:
            logger.error(f"全量创作者同步任务异常: {e}")

    async def _process_transcribe_queue(self):
        """处理转写队列"""
        try:
            videos = self.video_service.get_videos_for_transcribe(limit=5)
            if videos:
                results = self.transcribe_service.batch_transcribe_videos([v.id for v in videos])
                logger.info(f"视频转写任务完成: 成功{results['success_count']}个，失败{results['failed_count']}个")
        except Exception as e:
            logger.error(f"视频转写任务异常: {e}")

    async def _extract_topics(self):
        """提取选题"""
        try:
            # 获取最近24小时内已转写的视频
            recent_videos = self.video_service.get_videos(
                transcript_status="done",
                page=1,
                page_size=10,
                sort_by="extracted_at",
                sort_order="asc"
            )

            for video in recent_videos:
                # 检查是否已提取选题
                if not any(t.extracted_at and t.extracted_at > video.updated_at for t in video.topics):
                    result = self.topic_service.extract_topics_from_video(video.id)
                    if result and result.get("success"):
                        logger.info(f"选题提取成功: {video.id} - {video.title}")
                    else:
                        logger.error(f"选题提取失败: {video.id}")
        except Exception as e:
            logger.error(f"选题提取任务异常: {e}")

    async def _deduplicate_topics(self):
        """选题去重"""
        try:
            # 获取最近24小时内新增的选题
            recent_videos = self.video_service.get_videos(
                page=1,
                page_size=5,
                sort_by="created_at",
                sort_order="desc"
            )

            for video in recent_videos:
                result = self.topic_service.deduplicate_topics(video.id)
                if result.get("success"):
                    logger.info(f"选题去重完成: {video.id} - 去重{result['deduplicated_count']}个选题")
        except Exception as e:
            logger.error(f"选题去重任务异常: {e}")

    def run_sync_task(self, task_id: int):
        """执行同步任务"""
        # TODO: 实现具体的同步任务逻辑
        pass

    def run_transcribe_task(self, video_id: int):
        """执行转写任务"""
        # TODO: 实现具体的转写任务逻辑
        pass

    def run_topic_extraction_task(self, video_id: int):
        """执行选题提取任务"""
        # TODO: 实现具体的选题提取逻辑
        pass


# 调度器实例
scheduler = HotspotMonitorScheduler()


# 初始化调度器
def init_scheduler():
    """初始化调度器"""
    try:
        scheduler.start()
        logger.info("调度器初始化完成")
    except Exception as e:
        logger.error(f"调度器初始化失败: {e}")
        raise


# 关闭调度器
def shutdown_scheduler():
    """关闭调度器"""
    try:
        scheduler.stop()
        logger.info("调度器关闭完成")
    except Exception as e:
        logger.error(f"调度器关闭失败: {e}")