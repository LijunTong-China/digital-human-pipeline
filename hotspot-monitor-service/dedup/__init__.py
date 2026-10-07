"""去重模块包"""
from dedup.vector_dedup import VectorDedup

# 兼容别名
VectorDeduplication = VectorDedup

__all__ = ["VectorDedup", "VectorDeduplication"]
