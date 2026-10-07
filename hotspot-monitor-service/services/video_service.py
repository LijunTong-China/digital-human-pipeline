"""视频管理服务"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from models import Video, Creator, SyncTask
from models.schemas import VideoCreate, VideoUpdate, VideoStats
from models import get_db

logger = logging.getLogger("video_service")


class VideoService:
    """视频管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_video(self, video_data: VideoCreate) -> Video:
        """创建新视频"""
        try:
            video = Video(**video_data.dict())
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            logger.info(f"视频创建成功: {video.id} - {video.title}")
            return video
        except Exception as e:
            self.db.rollback()
            logger.error(f"视频创建失败: {e}")
            raise

    def get_video(self, video_id: int) -> Optional[Video]:
        """获取视频信息"""
        return self.db.query(Video).filter(Video.id == video_id).first()

    def get_videos(
        self,
        creator_id: Optional[int] = None,
        transcript_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "published_at",
        sort_order: str = "desc"
    ) -> List[Video]:
        """获取视频列表"""
        query = self.db.query(Video)

        if creator_id is not None:
            query = query.filter(Video.creator_id == creator_id)

        if transcript_status:
            query = query.filter(Video.transcript_status == transcript_status)

        # 排序
        if sort_by == "published_at":
            query = query.order_by(Video.published_at.desc() if sort_order == "desc" else Video.published_at.asc())
        elif sort_by == "stats_views":
            query = query.order_by(Video.stats_views.desc() if sort_order == "desc" else Video.stats_views.asc())
        else:
            query = query.order_by(Video.created_at.desc() if sort_order == "desc" else Video.created_at.asc())

        query = query.offset((page - 1) * page_size).limit(page_size)
        return query.all()

    def update_video(self, video_id: int, video_data: VideoUpdate) -> Optional[Video]:
        """更新视频信息"""
        video = self.get_video(video_id)
        if not video:
            return None

        try:
            for field, value in video_data.dict(exclude_unset=True).items():
                setattr(video, field, value)

            video.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(video)
            logger.info(f"视频更新成功: {video.id}")
            return video
        except Exception as e:
            self.db.rollback()
            logger.error(f"视频更新失败: {e}")
            raise

    def delete_video(self, video_id: int) -> bool:
        """删除视频"""
        video = self.get_video(video_id)
        if not video:
            return False

        try:
            self.db.delete(video)
            self.db.commit()
            logger.info(f"视频删除成功: {video.id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"视频删除失败: {e}")
            raise

    def get_video_stats(self, video_id: int) -> Optional[VideoStats]:
        """获取视频统计信息"""
        video = self.get_video(video_id)
        if not video:
            return None

        return VideoStats(
            views=video.stats_views,
            likes=video.stats_likes,
            comments=video.stats_comments,
            shares=video.stats_shares,
            collected_at=video.stats_collected_at
        )

    def update_video_stats(self, video_id: int, stats: Dict[str, int]) -> Optional[Video]:
        """更新视频统计数据"""
        video = self.get_video(video_id)
        if not video:
            return None

        try:
            if "views" in stats:
                video.stats_views = stats["views"]
            if "likes" in stats:
                video.stats_likes = stats["likes"]
            if "comments" in stats:
                video.stats_comments = stats["comments"]
            if "shares" in stats:
                video.stats_shares = stats["shares"]

            video.stats_collected_at = datetime.utcnow()
            video.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(video)
            return video
        except Exception as e:
            self.db.rollback()
            logger.error(f"视频统计更新失败: {e}")
            raise

    def get_videos_for_transcribe(self, limit: int = 10) -> List[Video]:
        """获取需要转写的视频"""
        return self.db.query(Video).filter(
            Video.transcript_status == "pending"
        ).order_by(Video.created_at.asc()).limit(limit).all()

    def mark_video_transcribed(self, video_id: int, transcript_text: str, language: str = "zh") -> Optional[Video]:
        """标记视频已转写"""
        video = self.get_video(video_id)
        if not video:
            return None

        try:
            video.transcript_status = "done"
            video.transcript_text = transcript_text
            video.transcript_language = language
            video.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(video)
            logger.info(f"视频转写完成: {video.id}")
            return video
        except Exception as e:
            self.db.rollback()
            logger.error(f"视频转写标记失败: {e}")
            raise

    def get_video_by_video_id(self, video_id: str) -> Optional[Video]:
        """通过平台视频ID获取视频"""
        return self.db.query(Video).filter(Video.video_id == video_id).first()

    def get_latest_videos(self, creator_id: int, limit: int = 10) -> List[Video]:
        """获取创作者最新视频"""
        return self.db.query(Video).filter(
            Video.creator_id == creator_id
        ).order_by(Video.published_at.desc()).limit(limit).all()

    def get_video_count(self, creator_id: Optional[int] = None) -> int:
        """获取视频总数"""
        query = self.db.query(Video)
        if creator_id is not None:
            query = query.filter(Video.creator_id == creator_id)
        return query.count()


# 服务工厂
def get_video_service() -> VideoService:
    """获取视频服务实例"""
    db = next(get_db())
    return VideoService(db)


# 初始化示例数据
def init_sample_videos():
    """初始化示例视频数据"""
    db = next(get_db())
    service = VideoService(db)

    # 检查是否已有数据
    if service.get_videos(page_size=1):
        logger.info("示例视频数据已存在")
        return

    # 获取示例创作者
    from services.creator_service import get_creator_service
    creator_service = get_creator_service()
    creators = creator_service.get_active_creators()
    if not creators:
        logger.warning("没有找到示例创作者，跳过视频数据初始化")
        return

    # 创建示例视频
    sample_videos = [
        {
            "creator_id": creators[0].id,
            "video_id": "v123456789",
            "title": "AI技术最新进展",
            "description": "AI技术的最新进展和应用场景分析",
            "published_at": datetime(2026, 9, 14, 15, 0, 0),
            "duration": 180,
            "stats_views": 100000,
            "stats_likes": 5000,
            "stats_comments": 300,
            "stats_shares": 100
        },
        {
            "creator_id": creators[0].id,
            "video_id": "v234567890",
            "title": "机器学习入门教程",
            "description": "机器学习基础知识和实践案例",
            "published_at": datetime(2026, 9, 13, 10, 0, 0),
            "duration": 120,
            "stats_views": 80000,
            "stats_likes": 4000,
            "stats_comments": 200,
            "stats_shares": 80
        },
        {
            "creator_id": creators[1].id,
            "video_id": "v345678901",
            "title": "家常菜制作教程",
            "description": "简单易学的家常菜制作方法",
            "published_at": datetime(2026, 9, 14, 12, 0, 0),
            "duration": 240,
            "stats_views": 150000,
            "stats_likes": 8000,
            "stats_comments": 500,
            "stats_shares": 200
        }
    ]

    for video_data in sample_videos:
        video_create = VideoCreate(**video_data)
        service.create_video(video_create)

    logger.info("示例视频数据初始化完成")