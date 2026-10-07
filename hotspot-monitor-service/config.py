"""热点监控服务配置文件"""
import os
from typing import Dict, Any

# 基础配置
BASE_URL = "http://localhost:8000"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# 阶段1登录态服务地址（爬虫复用其登录态浏览器）
LOGIN_SERVICE_URL = os.getenv("LOGIN_SERVICE_URL", "http://localhost:3459")

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/hotspot_monitor")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# 爬虫配置
CRAWLER_USER_AGENT = os.getenv("CRAWLER_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
CRAWLER_MAX_RETRIES = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))
CRAWLER_RETRY_DELAY = int(os.getenv("CRAWLER_RETRY_DELAY", "5"))  # 秒

# ASR语音识别配置（Whisper兼容协议，不绑定特定厂商）
# 兼容 OpenAI /v1/audio/transcriptions 协议的服务均可接入
ASR_API_KEY = os.getenv("ASR_API_KEY", "")
ASR_BASE_URL = os.getenv("ASR_BASE_URL", "https://api.siliconflow.cn/v1")
ASR_MODEL = os.getenv("ASR_MODEL", "SenseVoiceSmall")

# LLM服务配置（OpenAI兼容协议，不绑定特定厂商）
# 任何兼容 OpenAI Chat Completions 的服务均可：改 BASE_URL + MODEL 即完成切换
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# 去重配置
VECTOR_SIMILARITY_THRESHOLD = float(os.getenv("VECTOR_SIMILARITY_THRESHOLD", "0.85"))
KEYWORD_SIMILARITY_THRESHOLD = float(os.getenv("KEYWORD_SIMILARITY_THRESHOLD", "0.7"))

# 向量化服务（OpenAI兼容/v1/embeddings协议，用于选题去重）
# SiliconFlow: https://api.siliconflow.cn/v1  模型: BAAI/bge-m3 (1024维, 中文强, 免费)
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", os.getenv("ASR_API_KEY", ""))
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

# 定时调度配置
SYNC_INTERVAL_HOURS = int(os.getenv("SYNC_INTERVAL_HOURS", "24"))
TRANSCRIBE_INTERVAL_HOURS = int(os.getenv("TRANSCRIBE_INTERVAL_HOURS", "6"))
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))

# API配置
API_PREFIX = "/api/hotspot"
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"

# 环境变量配置
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 验证配置
def validate_config() -> Dict[str, str]:
    """验证必要配置项"""
    errors = []

    if not DATABASE_URL:
        errors.append("DATABASE_URL is required")

    if not LLM_API_KEY:
        errors.append("LLM_API_KEY is required")

    if not ASR_API_KEY:
        errors.append("ASR_API_KEY is required")

    return {"errors": errors, "valid": len(errors) == 0}

# 获取配置摘要
def get_config_summary() -> Dict[str, Any]:
    """获取配置摘要（不包含敏感信息）"""
    return {
        "environment": ENVIRONMENT,
        "database": {
            "url": DATABASE_URL.split('@')[-1] if DATABASE_URL else None,
            "echo": DATABASE_ECHO
        },
        "crawler": {
            "max_retries": CRAWLER_MAX_RETRIES,
            "retry_delay": CRAWLER_RETRY_DELAY
        },
        "asr": {
            "base_url": ASR_BASE_URL,
            "model": ASR_MODEL
        },
        "llm": {
            "base_url": LLM_BASE_URL,
            "model": LLM_MODEL
        },
        "scheduler": {
            "sync_interval_hours": SYNC_INTERVAL_HOURS,
            "transcribe_interval_hours": TRANSCRIBE_INTERVAL_HOURS,
            "max_concurrent_tasks": MAX_CONCURRENT_TASKS
        },
        "api": {
            "prefix": API_PREFIX,
            "max_page_size": MAX_PAGE_SIZE,
            "default_page_size": DEFAULT_PAGE_SIZE
        }
    }