"""选题管理服务"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np

from models import Video, Topic, Creator
from models.schemas import TopicCreate, TopicUpdate, TopicStats
from models import get_db
from llm.factory import get_llm
from dedup.vector_dedup import VectorDedup

logger = logging.getLogger("topic_service")


class TopicService:
    """选题管理服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.vector_dedup = VectorDedup(db)

    def extract_topics_from_video(self, video_id: int) -> Optional[Dict[str, Any]]:
        """从视频提取选题"""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"视频不存在: {video_id}")
            return None

        if not video.transcript_text:
            logger.error(f"视频转写文本不存在: {video_id}")
            return None

        try:
            # 调用LLM提取选题
            topics_list = get_llm().extract_topics(video.transcript_text)
            if not topics_list:
                logger.error(f"选题提取失败: {video_id}")
                return None

            # 处理提取的选题
            extracted_topics = []
            for topic_data in topics_list:
                topic_create = TopicCreate(
                    source_video_id=video_id,
                    title=topic_data.get("title", ""),
                    summary=topic_data.get("summary", ""),
                    keywords=topic_data.get("keywords", []),
                    category=topic_data.get("category", ""),
                    hot_score=topic_data.get("hot_score", 0.0),
                    quality_score=topic_data.get("quality_score", 0.0),
                    extraction_method="llm"
                )
                extracted_topics.append(topic_create)

            # 创建选题并去重
            created_topics = []
            for topic_create in extracted_topics:
                # 检查选题是否已存在（去重）
                existing_topic = self.db.query(Topic).filter(
                    Topic.source_video_id == topic_create.source_video_id,
                    Topic.title == topic_create.title
                ).first()

                if existing_topic:
                    logger.info(f"选题已存在，跳过创建: {existing_topic.id} - {topic_create.title}")
                    created_topics.append(existing_topic)
                else:
                    # 创建新选题（并计算标题向量用于后续去重）
                    topic = Topic(**topic_create.dict())
                    topic.embedding = self.vector_dedup.calculate_embedding(topic.title)
                    topic.extraction_method = "llm"
                    topic.extracted_at = datetime.utcnow()
                    self.db.add(topic)
                    self.db.commit()
                    self.db.refresh(topic)
                    created_topics.append(topic)
                    logger.info(f"选题创建成功: {topic.id} - {topic.title}")

            logger.info(f"视频选题提取完成: {video_id} - 提取{len(created_topics)}个选题")
            return {
                "success": True,
                "video_id": video_id,
                "extracted_count": len(extracted_topics),
                "created_count": len(created_topics)
            }

        except Exception as e:
            logger.error(f"选题提取异常: {video_id} - {e}")
            return {
                "success": False,
                "error": str(e),
                "video_id": video_id
            }

    def get_topics(
        self,
        video_id: Optional[int] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "hot_score",
        sort_order: str = "desc"
    ) -> List[Topic]:
        """获取选题列表"""
        query = self.db.query(Topic)

        if video_id is not None:
            query = query.filter(Topic.source_video_id == video_id)

        if category:
            query = query.filter(Topic.category == category)

        if status:
            query = query.filter(Topic.status == status)

        # 排序
        if sort_by == "hot_score":
            query = query.order_by(Topic.hot_score.desc() if sort_order == "desc" else Topic.hot_score.asc())
        elif sort_by == "quality_score":
            query = query.order_by(Topic.quality_score.desc() if sort_order == "desc" else Topic.quality_score.asc())
        elif sort_by == "extracted_at":
            query = query.order_by(Topic.extracted_at.desc() if sort_order == "desc" else Topic.extracted_at.asc())
        else:
            query = query.order_by(Topic.created_at.desc() if sort_order == "desc" else Topic.created_at.asc())

        query = query.offset((page - 1) * page_size).limit(page_size)
        return query.all()

    def get_topic(self, topic_id: int) -> Optional[Topic]:
        """获取选题信息"""
        return self.db.query(Topic).filter(Topic.id == topic_id).first()

    def update_topic(self, topic_id: int, topic_data: TopicUpdate) -> Optional[Topic]:
        """更新选题信息"""
        topic = self.get_topic(topic_id)
        if not topic:
            return None

        try:
            for field, value in topic_data.dict(exclude_unset=True).items():
                setattr(topic, field, value)

            topic.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(topic)
            logger.info(f"选题更新成功: {topic.id}")
            return topic
        except Exception as e:
            self.db.rollback()
            logger.error(f"选题更新失败: {e}")
            raise

    def delete_topic(self, topic_id: int) -> bool:
        """删除选题"""
        topic = self.get_topic(topic_id)
        if not topic:
            return False

        try:
            self.db.delete(topic)
            self.db.commit()
            logger.info(f"选题删除成功: {topic.id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"选题删除失败: {e}")
            raise

    def get_topic_stats(self, topic_id: int) -> Optional[TopicStats]:
        """获取选题统计信息"""
        topic = self.get_topic(topic_id)
        if not topic:
            return None

        return TopicStats(
            hot_score=topic.hot_score,
            quality_score=topic.quality_score,
            category=topic.category
        )

    def get_hot_topics(self, limit: int = 10) -> List[Topic]:
        """获取热门选题"""
        return self.db.query(Topic).filter(
            Topic.status == "pending"
        ).order_by(Topic.hot_score.desc()).limit(limit).all()

    def get_quality_topics(self, limit: int = 10) -> List[Topic]:
        """获取高质量选题"""
        return self.db.query(Topic).filter(
            Topic.status == "pending"
        ).order_by(Topic.quality_score.desc()).limit(limit).all()

    def get_topic_count(self, video_id: Optional[int] = None, category: Optional[str] = None) -> int:
        """获取选题总数"""
        query = self.db.query(Topic)
        if video_id is not None:
            query = query.filter(Topic.source_video_id == video_id)
        if category:
            query = query.filter(Topic.category == category)
        return query.count()

    def deduplicate_topics(self, video_id: int) -> Dict[str, Any]:
        """选题去重（向量相似度）"""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return {"success": False, "error": "视频不存在"}

        # 获取视频的所有选题
        topics = self.db.query(Topic).filter(Topic.source_video_id == video_id).all()
        if not topics:
            return {"success": True, "total_count": 0, "duplicate_count": 0}

        # 使用向量去重（内部会补算缺失向量并标记duplicate状态）
        self.vector_dedup.deduplicate_topics(topics)
        self.db.commit()

        duplicate_count = len([t for t in topics if t.status == "duplicate"])
        logger.info(f"选题去重完成: {video_id} - 共{len(topics)}个, 重复{duplicate_count}个")
        return {
            "success": True,
            "total_count": len(topics),
            "duplicate_count": duplicate_count
        }

    def get_creator_hot_topics(self, creator_id: int, limit: int = 10) -> List[Topic]:
        """获取创作者热门选题"""
        # 获取创作者的所有视频
        videos = self.db.query(Video).filter(Video.creator_id == creator_id).all()
        if not videos:
            return []

        # 获取所有选题并按热度排序
        all_topics = []
        for video in videos:
            topics = self.db.query(Topic).filter(Topic.source_video_id == video.id).all()
            all_topics.extend(topics)

        # 按热度排序并去重
        unique_topics = list({t.id: t for t in all_topics}.values())
        return sorted(unique_topics, key=lambda x: x.hot_score, reverse=True)[:limit]


# 服务工厂
def get_topic_service() -> TopicService:
    """获取选题服务实例"""
    db = next(get_db())
    return TopicService(db)


# 初始化示例数据
def init_sample_topics():
    """初始化示例选题数据"""
    db = next(get_db())
    service = TopicService(db)

    # 检查是否已有数据
    if service.get_topic_count() > 0:
        logger.info("示例选题数据已存在")
        return

    # 获取示例视频
    from services.video_service import get_video_service
    video_service = get_video_service()
    videos = video_service.get_videos(page_size=5)
    if not videos:
        logger.warning("没有找到示例视频，跳过选题数据初始化")
        return

    # 创建示例选题
    sample_topics = [
        {
            "source_video_id": videos[0].id,
            "title": "AI技术发展趋势",
            "summary": "人工智能技术的最新发展趋势和应用前景分析",
            "keywords": ["AI", "人工智能", "技术趋势", "机器学习"],
            "category": "科技",
            "hot_score": 0.85,
            "quality_score": 0.9
        },
        {
            "source_video_id": videos[0].id,
            "title": "机器学习入门指南",
            "summary": "机器学习基础知识体系和实践案例",
            "keywords": ["机器学习", "深度学习", "入门教程", "算法"],
            "category": "科技",
            "hot_score": 0.75,
            "quality_score": 0.85
        },
        {
            "source_video_id": videos[1].id,
            "title": "家常菜制作技巧",
            "summary": "简单易学的家常菜制作方法和技巧",
            "keywords": ["家常菜", "烹饪技巧", "美食", "菜谱"],
            "category": "美食",
            "hot_score": 0.9,
            "quality_score": 0.8
        },
        {
            "source_video_id": videos[2].id,
            "title": "旅游攻略分享",
            "summary": "热门旅游目的地推荐和行程规划",
            "keywords": ["旅游", "攻略", "目的地", "行程"],
            "category": "旅游",
            "hot_score": 0.8,
            "quality_score": 0.88
        }
    ]

    for topic_data in sample_topics:
        topic_create = TopicCreate(**topic_data)
        topic = Topic(**topic_create.dict())
        db.add(topic)
        db.commit()
        db.refresh(topic)

    logger.info("示例选题数据初始化完成")