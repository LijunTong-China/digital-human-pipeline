"""创作者管理服务"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from models import Creator, Video, SyncTask
from models.schemas import CreatorCreate, CreatorUpdate, CreatorStats
from models import get_db

logger = logging.getLogger("creator_service")


class CreatorService:
    """创作者管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_creator(self, creator_data: CreatorCreate) -> Creator:
        """创建新创作者"""
        try:
            creator = Creator(**creator_data.dict())
            self.db.add(creator)
            self.db.commit()
            self.db.refresh(creator)
            logger.info(f"创作者创建成功: {creator.id} - {creator.nickname}")
            return creator
        except Exception as e:
            self.db.rollback()
            logger.error(f"创作者创建失败: {e}")
            raise

    def get_creator(self, creator_id: int) -> Optional[Creator]:
        """获取创作者信息"""
        return self.db.query(Creator).filter(Creator.id == creator_id).first()

    def get_creators(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        platform: Optional[str] = None
    ) -> List[Creator]:
        """获取创作者列表"""
        query = self.db.query(Creator)

        if is_active is not None:
            query = query.filter(Creator.is_active == is_active)

        if platform:
            query = query.filter(Creator.platform == platform)

        query = query.offset((page - 1) * page_size).limit(page_size)
        return query.all()

    def update_creator(self, creator_id: int, creator_data: CreatorUpdate) -> Optional[Creator]:
        """更新创作者信息"""
        creator = self.get_creator(creator_id)
        if not creator:
            return None

        try:
            for field, value in creator_data.dict(exclude_unset=True).items():
                setattr(creator, field, value)

            creator.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(creator)
            logger.info(f"创作者更新成功: {creator.id}")
            return creator
        except Exception as e:
            self.db.rollback()
            logger.error(f"创作者更新失败: {e}")
            raise

    def delete_creator(self, creator_id: int) -> bool:
        """删除创作者（软删除）"""
        creator = self.get_creator(creator_id)
        if not creator:
            return False

        try:
            creator.is_active = False
            creator.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"创作者删除成功: {creator.id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"创作者删除失败: {e}")
            raise

    def get_creator_stats(self, creator_id: int) -> Optional[CreatorStats]:
        """获取创作者统计信息"""
        creator = self.get_creator(creator_id)
        if not creator:
            return None

        video_count = self.db.query(Video).filter(Video.creator_id == creator_id).count()

        return CreatorStats(
            total_videos=video_count,
            last_sync_time=creator.last_sync_time,
            last_sync_status=creator.last_sync_status
        )

    def sync_creator_videos(self, creator_id: int) -> Dict[str, Any]:
        """同步创作者视频（创建同步任务）"""
        try:
            # 创建同步任务
            task = SyncTask(
                task_type="creator_sync",
                target_id=creator_id,
                status="pending"
            )
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            logger.info(f"创作者同步任务创建成功: {task.id} - 创作者 {creator_id}")
            return {
                "success": True,
                "task_id": task.id,
                "message": "同步任务已创建"
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"创作者同步任务创建失败: {e}")
            raise

    def get_sync_tasks(self, creator_id: int = None, status: str = None) -> List[SyncTask]:
        """获取同步任务列表"""
        query = self.db.query(SyncTask)

        if creator_id is not None:
            query = query.filter(SyncTask.target_id == creator_id)

        if status:
            query = query.filter(SyncTask.status == status)

        return query.order_by(SyncTask.created_at.desc()).all()

    def update_sync_task(self, task_id: int, status: str, result: Optional[Dict] = None, error_message: Optional[str] = None) -> Optional[SyncTask]:
        """更新同步任务状态"""
        task = self.db.query(SyncTask).filter(SyncTask.id == task_id).first()
        if not task:
            return None

        try:
            task.status = status
            task.result = result
            task.error_message = error_message
            task.completed_at = datetime.utcnow()

            if status == "running":
                task.started_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(task)
            return task
        except Exception as e:
            self.db.rollback()
            logger.error(f"同步任务更新失败: {e}")
            raise

    def get_creator_by_nickname(self, nickname: str, platform: str = "douyin") -> Optional[Creator]:
        """通过昵称获取创作者"""
        return self.db.query(Creator).filter(
            Creator.nickname == nickname,
            Creator.platform == platform
        ).first()

    def get_active_creators(self) -> List[Creator]:
        """获取所有活跃创作者"""
        return self.db.query(Creator).filter(Creator.is_active == True).all()


# 服务工厂
def get_creator_service() -> CreatorService:
    """获取创作者服务实例"""
    db = next(get_db())
    return CreatorService(db)


# 初始化示例数据
def init_sample_creators():
    """初始化示例创作者数据"""
    db = next(get_db())
    service = CreatorService(db)

    # 检查是否已有数据
    if service.get_creators(page_size=1):
        logger.info("示例创作者数据已存在")
        return

    # 创建示例创作者
    sample_creators = [
        CreatorCreate(
            nickname="科技博主",
            note="科技领域创作者",
            platform="douyin",
            creator_id="123456789",
            is_active=True,
            sync_interval_hours=24
        ),
        CreatorCreate(
            nickname="美食达人",
            note="美食烹饪创作者",
            platform="douyin",
            creator_id="987654321",
            is_active=True,
            sync_interval_hours=12
        ),
        CreatorCreate(
            nickname="旅游探险",
            note="旅游和探险内容",
            platform="douyin",
            creator_id="456789123",
            is_active=True,
            sync_interval_hours=48
        )
    ]

    for creator_data in sample_creators:
        service.create_creator(creator_data)

    logger.info("示例创作者数据初始化完成")