"""向量相似度去重 - 基于OpenAI兼容embeddings协议"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from openai import OpenAI

import config
from models import Topic, get_db

logger = logging.getLogger("dedup.vector")


class VectorDedup:
    """向量相似度去重类"""

    def __init__(self, db: Session):
        self.db = db
        self.threshold = config.VECTOR_SIMILARITY_THRESHOLD
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """懒加载embeddings客户端"""
        if self._client is None:
            self._client = OpenAI(
                api_key=config.EMBEDDING_API_KEY,
                base_url=config.EMBEDDING_BASE_URL
            )
        return self._client

    def calculate_embedding(self, text: str) -> Optional[List[float]]:
        """计算文本向量（OpenAI兼容/v1/embeddings协议）"""
        if not text or not text.strip():
            return None
        try:
            response = self.client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=text[:512]  # bge-m3 建议8192内，截断防御
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"向量计算失败: {e}")
            return None

    def calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算向量相似度（余弦相似度）"""
        try:
            vec1 = np.array(vec1, dtype=float)
            vec2 = np.array(vec2, dtype=float)
            norm = np.linalg.norm(vec1) * np.linalg.norm(vec2)
            if norm == 0:
                return 0.0
            return float(np.dot(vec1, vec2) / norm)
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            return 0.0

    def find_similar_topics(self, title: str, exclude_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """查找相似选题"""
        try:
            new_embedding = self.calculate_embedding(title)
            if not new_embedding:
                return []

            topics = self.db.query(Topic).filter(
                Topic.status == "pending"
            ).all()

            similar_topics = []
            for topic in topics:
                if topic.embedding and topic.id != exclude_id:
                    similarity = self.calculate_similarity(new_embedding, list(topic.embedding))
                    if similarity >= self.threshold:
                        similar_topics.append({
                            "id": topic.id,
                            "title": topic.title,
                            "similarity": similarity
                        })

            similar_topics.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_topics

        except Exception as e:
            logger.error(f"查找相似选题失败: {e}")
            return []

    def is_duplicate(self, title: str, exclude_id: Optional[int] = None) -> bool:
        """判断是否为重复选题"""
        similar_topics = self.find_similar_topics(title, exclude_id)
        return len(similar_topics) > 0

    def deduplicate_topics(self, topics: List[Topic]) -> List[Topic]:
        """对选题列表去重：相似度超阈值的标记为duplicate"""
        result = []
        seen_embeddings: List[List[float]] = []

        for topic in topics:
            if not topic.embedding:
                # 补算向量
                emb = self.calculate_embedding(topic.title)
                topic.embedding = emb
            emb = list(topic.embedding) if topic.embedding else None

            if emb is None:
                result.append(topic)
                continue

            is_dup = any(self.calculate_similarity(emb, s) >= self.threshold for s in seen_embeddings)
            if is_dup:
                topic.status = "duplicate"
            else:
                seen_embeddings.append(emb)
            result.append(topic)

        return result


# 向量去重服务工厂
def get_vector_dedup_service() -> VectorDedup:
    """获取向量去重服务实例"""
    db = next(get_db())
    return VectorDedup(db)
