"""API路由定义"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models import Creator, Video, Topic, SyncTask
from models.schemas import (
    CreatorCreate, CreatorUpdate, Creator, CreatorStats,
    VideoCreate, VideoUpdate, Video, VideoStats,
    TopicCreate, TopicUpdate, Topic, TopicStats,
    SyncTaskCreate, SyncTask, APIResponse, PaginatedResponse
)
from services import (
    get_creator_service, get_video_service, get_transcribe_service, get_topic_service
)
from .dependencies import get_db

router = APIRouter(tags=["api"])   # 前缀由 main.py 统一挂 /api/hotspot,避免双重前缀


# 创作者管理路由
@router.post("/creators", response_model=APIResponse[Creator])
async def create_creator(
    creator_data: CreatorCreate,
    db: Session = Depends(get_db)
):
    """创建新创作者"""
    service = get_creator_service()
    creator = service.create_creator(creator_data)
    return APIResponse(success=True, data=creator)


@router.get("/creators/{creator_id}", response_model=APIResponse[Creator])
async def get_creator(
    creator_id: int,
    db: Session = Depends(get_db)
):
    """获取创作者信息"""
    service = get_creator_service()
    creator = service.get_creator(creator_id)
    if not creator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="创作者不存在")
    return APIResponse(success=True, data=creator)


@router.get("/creators", response_model=APIResponse[PaginatedResponse[Creator]])
async def get_creators(
    page: int = 1,
    page_size: int = 20,
    is_active: Optional[bool] = None,
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取创作者列表"""
    service = get_creator_service()
    creators = service.get_creators(page=page, page_size=page_size, is_active=is_active, platform=platform)
    total = service.get_creator_count(is_active=is_active, platform=platform)
    return APIResponse(success=True, data=PaginatedResponse(
        items=creators,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.put("/creators/{creator_id}", response_model=APIResponse[Creator])
async def update_creator(
    creator_id: int,
    creator_data: CreatorUpdate,
    db: Session = Depends(get_db)
):
    """更新创作者信息"""
    service = get_creator_service()
    creator = service.update_creator(creator_id, creator_data)
    if not creator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="创作者不存在")
    return APIResponse(success=True, data=creator)


@router.delete("/creators/{creator_id}", response_model=APIResponse[bool])
async def delete_creator(
    creator_id: int,
    db: Session = Depends(get_db)
):
    """删除创作者"""
    service = get_creator_service()
    success = service.delete_creator(creator_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="创作者不存在")
    return APIResponse(success=True, data=success)


@router.get("/creators/{creator_id}/stats", response_model=APIResponse[CreatorStats])
async def get_creator_stats(
    creator_id: int,
    db: Session = Depends(get_db)
):
    """获取创作者统计信息"""
    service = get_creator_service()
    stats = service.get_creator_stats(creator_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="创作者不存在")
    return APIResponse(success=True, data=stats)


@router.post("/creators/{creator_id}/sync", response_model=APIResponse[Dict[str, Any]])
async def sync_creator_videos(
    creator_id: int,
    db: Session = Depends(get_db)
):
    """同步创作者视频"""
    service = get_creator_service()
    result = service.sync_creator_videos(creator_id)
    return APIResponse(success=True, data=result)


@router.get("/creators/{creator_id}/tasks", response_model=APIResponse[List[SyncTask]])
async def get_sync_tasks(
    creator_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取同步任务列表"""
    service = get_creator_service()
    tasks = service.get_sync_tasks(creator_id=creator_id, status=status)
    return APIResponse(success=True, data=tasks)


# 视频管理路由
@router.post("/videos", response_model=APIResponse[Video])
async def create_video(
    video_data: VideoCreate,
    db: Session = Depends(get_db)
):
    """创建新视频"""
    service = get_video_service()
    video = service.create_video(video_data)
    return APIResponse(success=True, data=video)


@router.get("/videos/{video_id}", response_model=APIResponse[Video])
async def get_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """获取视频信息"""
    service = get_video_service()
    video = service.get_video(video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")
    return APIResponse(success=True, data=video)


@router.get("/videos", response_model=APIResponse[PaginatedResponse[Video]])
async def get_videos(
    creator_id: Optional[int] = None,
    transcript_status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "published_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """获取视频列表"""
    service = get_video_service()
    videos = service.get_videos(
        creator_id=creator_id,
        transcript_status=transcript_status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    total = service.get_video_count(creator_id=creator_id)
    return APIResponse(success=True, data=PaginatedResponse(
        items=videos,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.put("/videos/{video_id}", response_model=APIResponse[Video])
async def update_video(
    video_id: int,
    video_data: VideoUpdate,
    db: Session = Depends(get_db)
):
    """更新视频信息"""
    service = get_video_service()
    video = service.update_video(video_id, video_data)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")
    return APIResponse(success=True, data=video)


@router.delete("/videos/{video_id}", response_model=APIResponse[bool])
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """删除视频"""
    service = get_video_service()
    success = service.delete_video(video_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")
    return APIResponse(success=True, data=success)


@router.get("/videos/{video_id}/stats", response_model=APIResponse[VideoStats])
async def get_video_stats(
    video_id: int,
    db: Session = Depends(get_db)
):
    """获取视频统计信息"""
    service = get_video_service()
    stats = service.get_video_stats(video_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")
    return APIResponse(success=True, data=stats)


@router.post("/videos/{video_id}/stats", response_model=APIResponse[Video])
async def update_video_stats(
    video_id: int,
    stats: Dict[str, int],
    db: Session = Depends(get_db)
):
    """更新视频统计数据"""
    service = get_video_service()
    video = service.update_video_stats(video_id, stats)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="视频不存在")
    return APIResponse(success=True, data=video)


@router.post("/videos/{video_id}/transcribe", response_model=APIResponse[Dict[str, Any]])
async def transcribe_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """转写视频内容"""
    service = get_transcribe_service()
    result = service.transcribe_video(video_id)
    if not result or not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="转写失败")
    return APIResponse(success=True, data=result)


# 选题管理路由
@router.post("/topics", response_model=APIResponse[Topic])
async def create_topic(
    topic_data: TopicCreate,
    db: Session = Depends(get_db)
):
    """创建新选题"""
    service = get_topic_service()
    topic = Topic(**topic_data.dict())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return APIResponse(success=True, data=topic)


@router.get("/topics/hot", response_model=APIResponse[List[Topic]])
async def get_hot_topics(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取热门选题"""
    service = get_topic_service()
    topics = service.get_hot_topics(limit=limit)
    return APIResponse(success=True, data=topics)


@router.get("/topics/quality", response_model=APIResponse[List[Topic]])
async def get_quality_topics(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取高质量选题"""
    service = get_topic_service()
    topics = service.get_quality_topics(limit=limit)
    return APIResponse(success=True, data=topics)


@router.get("/topics/{topic_id}", response_model=APIResponse[Topic])
async def get_topic(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """获取选题信息"""
    service = get_topic_service()
    topic = service.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选题不存在")
    return APIResponse(success=True, data=topic)


@router.get("/topics", response_model=APIResponse[PaginatedResponse[Topic]])
async def get_topics(
    video_id: Optional[int] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "hot_score",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """获取选题列表"""
    service = get_topic_service()
    topics = service.get_topics(
        video_id=video_id,
        category=category,
        status=status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    total = service.get_topic_count(video_id=video_id, category=category)
    return APIResponse(success=True, data=PaginatedResponse(
        items=topics,
        total=total,
        page=page,
        page_size=page_size
    ))


@router.put("/topics/{topic_id}", response_model=APIResponse[Topic])
async def update_topic(
    topic_id: int,
    topic_data: TopicUpdate,
    db: Session = Depends(get_db)
):
    """更新选题信息"""
    service = get_topic_service()
    topic = service.update_topic(topic_id, topic_data)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选题不存在")
    return APIResponse(success=True, data=topic)


@router.delete("/topics/{topic_id}", response_model=APIResponse[bool])
async def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """删除选题"""
    service = get_topic_service()
    success = service.delete_topic(topic_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选题不存在")
    return APIResponse(success=True, data=success)


@router.get("/topics/{topic_id}/stats", response_model=APIResponse[TopicStats])
async def get_topic_stats(
    topic_id: int,
    db: Session = Depends(get_db)
):
    """获取选题统计信息"""
    service = get_topic_service()
    stats = service.get_topic_stats(topic_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="选题不存在")
    return APIResponse(success=True, data=stats)


@router.post("/topics/{video_id}/extract", response_model=APIResponse[Dict[str, Any]])
async def extract_topics_from_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """从视频提取选题"""
    service = get_topic_service()
    result = service.extract_topics_from_video(video_id)
    if not result or not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="选题提取失败")
    return APIResponse(success=True, data=result)


@router.post("/topics/{video_id}/deduplicate", response_model=APIResponse[Dict[str, Any]])
async def deduplicate_topics(
    video_id: int,
    db: Session = Depends(get_db)
):
    """选题去重"""
    service = get_topic_service()
    result = service.deduplicate_topics(video_id)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="选题去重失败")
    return APIResponse(success=True, data=result)


# 统计路由
@router.get("/stats/overview", response_model=APIResponse[Dict[str, Any]])
async def get_overview_stats(db: Session = Depends(get_db)):
    """获取概览统计信息"""
    creator_service = get_creator_service()
    video_service = get_video_service()
    topic_service = get_topic_service()
    transcribe_service = get_transcribe_service()

    return APIResponse(success=True, data={
        "creator_count": creator_service.get_creator_count(),
        "video_count": video_service.get_video_count(),
        "topic_count": topic_service.get_topic_count(),
        "transcribe_stats": transcribe_service.get_transcribe_stats()
    })