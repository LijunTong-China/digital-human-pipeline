"""LLM服务入口

统一通过 LLMClient（OpenAI兼容协议）访问任意大模型服务，
模型/厂商由配置决定，代码中不出现特定厂商。
"""
import logging
from typing import Optional

import config
from .base_provider import LLMClient

logger = logging.getLogger("llm.factory")

# 缓存的客户端实例
_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """获取LLM客户端（单例），配置来自 config.LLM_*"""
    global _client
    if _client is None:
        _client = LLMClient(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            model=config.LLM_MODEL
        )
        logger.info("LLM客户端初始化完成: base_url=%s, model=%s", config.LLM_BASE_URL, config.LLM_MODEL)
    return _client


def reset_llm() -> None:
    """重置客户端（配置变更后调用）"""
    global _client
    _client = None
