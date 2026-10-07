"""备用API模块 - 第三方数据服务"""
import logging
from typing import Dict, Any, List, Optional
import requests
from datetime import datetime

logger = logging.getLogger("backup_api")


class BackupAPI:
    """备用API服务类"""

    def __init__(self):
        self.session = requests.Session()
        self.api_key = None
        self.base_url = None

    def set_api_key(self, api_key: str, base_url: str):
        """设置API密钥和基础URL"""
        self.api_key = api_key
        self.base_url = base_url
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def get_creator_videos(self, creator_id: str, max_pages: int = 3) -> List[Dict[str, Any]]:
        """通过备用API获取创作者视频列表"""
        try:
            url = f"{self.base_url}/creators/{creator_id}/videos"
            params = {
                "page": 1,
                "page_size": 20,
                "max_pages": max_pages
            }

            logger.info(f"通过备用API获取视频: {url}")

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get("videos", [])

        except Exception as e:
            logger.error(f"备用API获取视频失败: {e}")
            return []

    def get_hot_videos(self, category: str = "hot", max_pages: int = 3) -> List[Dict[str, Any]]:
        """通过备用API获取热门视频"""
        try:
            url = f"{self.base_url}/hot/videos"
            params = {
                "category": category,
                "page": 1,
                "page_size": 20,
                "max_pages": max_pages
            }

            logger.info(f"通过备用API获取热门视频: {url}")

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get("videos", [])

        except Exception as e:
            logger.error(f"备用API获取热门视频失败: {e}")
            return []

    def get_creator_info(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """通过备用API获取创作者信息"""
        try:
            url = f"{self.base_url}/creators/{creator_id}"
            logger.info(f"通过备用API获取创作者信息: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"备用API获取创作者信息失败: {e}")
            return None

    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """通过备用API获取视频详情"""
        try:
            url = f"{self.base_url}/videos/{video_id}"
            logger.info(f"通过备用API获取视频详情: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"备用API获取视频详情失败: {e}")
            return None

    def get_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """通过备用API获取热门话题"""
        try:
            url = f"{self.base_url}/trending/topics"
            params = {
                "limit": limit
            }

            logger.info(f"通过备用API获取热门话题: {url}")

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            return response.json().get("topics", [])

        except Exception as e:
            logger.error(f"备用API获取热门话题失败: {e}")
            return []

    def get_creator_stats(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """通过备用API获取创作者统计信息"""
        try:
            url = f"{self.base_url}/creators/{creator_id}/stats"
            logger.info(f"通过备用API获取创作者统计: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"备用API获取创作者统计失败: {e}")
            return None


# 备用API工厂
def get_backup_api() -> BackupAPI:
    """获取备用API实例"""
    return BackupAPI()