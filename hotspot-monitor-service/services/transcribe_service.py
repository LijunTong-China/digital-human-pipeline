"""视频转写服务"""
import logging
import os
import tempfile
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import requests
from openai import OpenAI

import config
from models import Video, Creator, SyncTask
from models.schemas import VideoStats
from models import get_db

logger = logging.getLogger("transcribe_service")


class TranscribeService:
    """视频转写服务类"""

    def __init__(self, db: Session):
        self.db = db

    def transcribe_video(self, video_id: int) -> Optional[Dict[str, Any]]:
        """转写视频内容（ASR转写，LLM不参与音频处理）"""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            logger.error(f"视频不存在: {video_id}")
            return None

        if video.transcript_status != "pending":
            logger.warning(f"视频已转写或状态不正确: {video_id}, 状态: {video.transcript_status}")
            return None

        try:
            # 获取视频URL
            if not video.video_url:
                logger.error(f"视频URL不存在: {video_id}")
                return None

            # 下载媒体文件并调用Whisper兼容ASR转写
            transcript_text = self._transcribe_from_url(video.video_url)
            if not transcript_text:
                logger.error(f"视频转写失败: {video_id}")
                return None

            # 更新视频转写状态
            video.transcript_status = "done"
            video.transcript_text = transcript_text
            video.transcript_language = "zh"
            video.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(video)

            logger.info(f"视频转写成功: {video_id} - {video.title}")
            return {
                "success": True,
                "video_id": video_id,
                "transcript_length": len(transcript_text),
                "asr_model": config.ASR_MODEL
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"视频转写异常: {video_id} - {e}")
            # 标记失败，便于重试
            self.mark_transcribe_failed(video_id, str(e))
            return {
                "success": False,
                "error": str(e),
                "video_id": video_id
            }

    def _transcribe_from_url(self, media_url: str) -> Optional[str]:
        """下载媒体文件并通过Whisper兼容协议转写"""
        asr_client = OpenAI(api_key=config.ASR_API_KEY, base_url=config.ASR_BASE_URL)

        tmp_path = None
        try:
            # 下载到临时文件（ASR接口需要multipart上传）
            resp = requests.get(media_url, timeout=120, stream=True)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                for chunk in resp.iter_content(chunk_size=1024 * 256):
                    tmp.write(chunk)
                tmp_path = tmp.name

            return self._transcribe_file(tmp_path, asr_client)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _transcribe_from_file(self, local_path: str) -> Optional[str]:
        """转写本地媒体文件（供同步服务调用，文件由调用方清理）"""
        asr_client = OpenAI(api_key=config.ASR_API_KEY, base_url=config.ASR_BASE_URL)
        return self._transcribe_file(local_path, asr_client)

    @staticmethod
    def _transcribe_file(path: str, asr_client: OpenAI) -> Optional[str]:
        """调用 /v1/audio/transcriptions（Whisper协议）

        先用ffmpeg统一转为16k单声道wav（兼容fMP4分段捕获等非标准容器），
        转换失败则直接上传原文件。
        """
        prepared = TranscribeService._prepare_audio(path)
        try:
            with open(prepared, "rb") as f:
                result = asr_client.audio.transcriptions.create(
                    model=config.ASR_MODEL,
                    file=f
                )
            return result.text or ""
        except Exception:
            # wav转换后仍失败则回退原文件直传
            if prepared != path:
                with open(path, "rb") as f:
                    result = asr_client.audio.transcriptions.create(
                        model=config.ASR_MODEL,
                        file=f
                    )
                return result.text or ""
            raise
        finally:
            if prepared != path and os.path.exists(prepared):
                os.remove(prepared)

    @staticmethod
    def _prepare_audio(path: str) -> str:
        """ffmpeg抽取音轨为16k单声道wav（imageio-ffmpeg自带二进制，无需系统安装）"""
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:  # noqa: BLE001
            return path

        out = path + ".wav"
        try:
            import subprocess
            r = subprocess.run(
                [ffmpeg, "-y", "-i", path, "-vn", "-acodec", "pcm_s16le",
                 "-ar", "16000", "-ac", "1", out],
                capture_output=True, timeout=300
            )
            if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 1000:
                return out
        except Exception:  # noqa: BLE001
            pass
        return path

    def batch_transcribe_videos(self, video_ids: List[int]) -> Dict[str, Any]:
        """批量转写视频"""
        results = {
            "success_count": 0,
            "failed_count": 0,
            "results": []
        }

        for video_id in video_ids:
            result = self.transcribe_video(video_id)
            if result and result.get("success"):
                results["success_count"] += 1
            else:
                results["failed_count"] += 1
            results["results"].append(result)

        return results

    def get_videos_for_transcribe(self, limit: int = 10) -> List[Video]:
        """获取需要转写的视频"""
        return self.db.query(Video).filter(
            Video.transcript_status == "pending"
        ).order_by(Video.created_at.asc()).limit(limit).all()

    def get_transcribe_queue_size(self) -> int:
        """获取转写队列大小"""
        return self.db.query(Video).filter(
            Video.transcript_status == "pending"
        ).count()

    def get_transcribe_stats(self) -> Dict[str, Any]:
        """获取转写统计信息"""
        total_videos = self.db.query(Video).count()
        pending_videos = self.db.query(Video).filter(
            Video.transcript_status == "pending"
        ).count()
        done_videos = self.db.query(Video).filter(
            Video.transcript_status == "done"
        ).count()
        failed_videos = self.db.query(Video).filter(
            Video.transcript_status == "failed"
        ).count()

        return {
            "total_videos": total_videos,
            "pending_videos": pending_videos,
            "done_videos": done_videos,
            "failed_videos": failed_videos,
            "completion_rate": (done_videos / total_videos * 100) if total_videos > 0 else 0
        }

    def mark_transcribe_failed(self, video_id: int, error_message: str) -> bool:
        """标记转写失败"""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return False

        try:
            video.transcript_status = "failed"
            video.transcript_text = None
            video.error_message = error_message
            video.updated_at = datetime.utcnow()
            self.db.commit()
            logger.warning(f"视频转写失败标记: {video_id} - {error_message}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"标记转写失败异常: {video_id} - {e}")
            return False

    def retry_failed_transcribe(self, video_id: int) -> Optional[Dict[str, Any]]:
        """重试失败的转写"""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return None

        if video.transcript_status != "failed":
            logger.warning(f"视频不是失败状态: {video_id}, 状态: {video.transcript_status}")
            return None

        return self.transcribe_video(video_id)


# 服务工厂
def get_transcribe_service() -> TranscribeService:
    """获取转写服务实例"""
    db = next(get_db())
    return TranscribeService(db)


# 初始化示例数据
def init_sample_transcribe_data():
    """初始化示例转写数据"""
    db = next(get_db())
    service = TranscribeService(db)

    # 检查是否已有数据
    if service.get_transcribe_queue_size() > 0:
        logger.info("示例转写数据已存在")
        return

    # 获取需要转写的视频
    videos = service.get_videos_for_transcribe(limit=5)
    if not videos:
        logger.warning("没有找到需要转写的视频，跳过转写数据初始化")
        return

    # 创建示例转写任务
    for video in videos:
        # 模拟转写结果
        video.transcript_status = "done"
        video.transcript_text = f"这是视频《{video.title}》的转写文本，内容包含视频的主要观点和关键信息。"
        video.transcript_language = "zh"
        video.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(video)

    logger.info("示例转写数据初始化完成")