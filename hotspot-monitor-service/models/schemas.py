"""Pydantic 数据模型定义"""
from typing import Generic, List, Optional, Dict, Any, TypeVar
from pydantic import BaseModel, Field, field_validator


def _orm_to_dict(o):
    """SQLAlchemy ORM 对象 → 列名 dict(pydantic v2 不会自动序列化 ORM 对象)"""
    return {c.name: getattr(o, c.name) for c in o.__table__.columns}
from datetime import datetime


class CreatorBase(BaseModel):
    """创作者基础模型"""
    nickname: str = Field(..., description="创作者昵称")
    note: Optional[str] = Field(None, description="备注信息")
    platform: str = Field("douyin", description="平台名称")
    creator_id: Optional[str] = Field(None, description="平台创作者ID")
    is_active: bool = Field(True, description="是否启用监控")
    sync_interval_hours: int = Field(24, description="同步间隔（小时）")
    last_sync_time: Optional[datetime] = Field(None, description="最后同步时间")
    last_sync_status: Optional[str] = Field(None, description="最后同步状态")


class CreatorCreate(CreatorBase):
    """创建创作者模型"""
    pass


class CreatorUpdate(BaseModel):
    """更新创作者模型"""
    nickname: Optional[str] = None
    note: Optional[str] = None
    is_active: Optional[bool] = None
    sync_interval_hours: Optional[int] = None


class Creator(CreatorBase):
    """创作者模型（数据库返回）"""
    id: int = Field(..., description="创作者ID")
    video_count: int = Field(0, description="视频总数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class VideoBase(BaseModel):
    """视频基础模型"""
    creator_id: int = Field(..., description="创作者ID")
    video_id: str = Field(..., description="平台视频ID")
    title: str = Field(..., description="视频标题")
    description: Optional[str] = Field(None, description="视频描述")
    published_at: datetime = Field(..., description="发布时间")
    duration: int = Field(..., description="视频时长（秒）")
    cover_url: Optional[str] = Field(None, description="封面图URL")
    video_url: Optional[str] = Field(None, description="视频URL")
    transcript_status: str = Field("pending", description="转写状态")
    transcript_text: Optional[str] = Field(None, description="转写文本")
    transcript_language: Optional[str] = Field("zh", description="转写语言")


class VideoCreate(VideoBase):
    """创建视频模型"""
    pass


class VideoUpdate(BaseModel):
    """更新视频模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    transcript_status: Optional[str] = None
    transcript_text: Optional[str] = None


class Video(VideoBase):
    """视频模型（数据库返回）"""
    id: int = Field(..., description="视频ID")
    stats_views: int = Field(0, description="播放量")
    stats_likes: int = Field(0, description="点赞数")
    stats_comments: int = Field(0, description="评论数")
    stats_shares: int = Field(0, description="分享数")
    stats_collected_at: Optional[datetime] = Field(None, description="统计数据采集时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class TopicBase(BaseModel):
    """选题基础模型"""
    source_video_id: int = Field(..., description="源视频ID")
    title: str = Field(..., description="选题标题")
    summary: Optional[str] = Field(None, description="选题摘要")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    category: Optional[str] = Field(None, description="选题分类")
    hot_score: float = Field(0.0, description="热度评分")
    quality_score: float = Field(0.0, description="质量评分")
    status: str = Field("pending", description="状态")


class TopicCreate(TopicBase):
    """创建选题模型"""
    pass


class TopicUpdate(BaseModel):
    """更新选题模型"""
    title: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    category: Optional[str] = None
    hot_score: Optional[float] = None
    quality_score: Optional[float] = None
    status: Optional[str] = None


class Topic(TopicBase):
    """选题模型（数据库返回）"""
    id: int = Field(..., description="选题ID")
    embedding: Optional[List[float]] = Field(None, description="标题向量")
    llm_model: Optional[str] = Field(None, description="使用的LLM模型")
    extraction_method: Optional[str] = Field(None, description="提取方法")
    extracted_at: Optional[datetime] = Field(None, description="提取时间")

    class Config:
        from_attributes = True


class SyncTaskBase(BaseModel):
    """同步任务基础模型"""
    task_type: str = Field(..., description="任务类型")
    target_id: Optional[int] = Field(None, description="目标ID")
    status: str = Field("pending", description="任务状态")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    retry_count: int = Field(0, description="重试次数")


class SyncTaskCreate(SyncTaskBase):
    """创建同步任务模型"""
    pass


class SyncTask(SyncTaskBase):
    """同步任务模型（数据库返回）"""
    id: int = Field(..., description="任务ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """通用API响应模型"""
    success: bool = Field(..., description="操作是否成功")
    data: Optional[Any] = Field(None, description="返回数据")

    @field_validator("data", mode="before")
    @classmethod
    def _dump_orm(cls, v):
        if hasattr(v, "__table__"):
            return _orm_to_dict(v)
        if isinstance(v, list) and v and hasattr(v[0], "__table__"):
            return [_orm_to_dict(o) for o in v]
        return v
    message: Optional[str] = Field(None, description="消息信息")
    error: Optional[str] = Field(None, description="错误信息")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[Any] = Field(..., description="数据列表")

    @field_validator("items", mode="before")
    @classmethod
    def _dump_orm(cls, v):
        if isinstance(v, list) and v and hasattr(v[0], "__table__"):
            return [_orm_to_dict(o) for o in v]
        return v
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class CreatorStats(BaseModel):
    """创作者统计信息"""
    total_videos: int = Field(..., description="视频总数")
    last_sync_time: Optional[datetime] = Field(None, description="最后同步时间")
    last_sync_status: Optional[str] = Field(None, description="最后同步状态")


class VideoStats(BaseModel):
    """视频统计信息"""
    views: int = Field(..., description="播放量")
    likes: int = Field(..., description="点赞数")
    comments: int = Field(..., description="评论数")
    shares: int = Field(..., description="分享数")
    collected_at: datetime = Field(..., description="采集时间")


class TopicStats(BaseModel):
    """选题统计信息"""
    hot_score: float = Field(..., description="热度评分")
    quality_score: float = Field(..., description="质量评分")
    category: Optional[str] = Field(None, description="分类")