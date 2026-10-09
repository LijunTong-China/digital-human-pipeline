"""热点监控服务主入口 - FastAPI 应用"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import config
from api.routes import router
from scheduler import scheduler

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger("hotspot.main")

# 验证配置
config_validation = config.validate_config()
if not config_validation["valid"]:
    logger.error("配置验证失败: %s", config_validation["errors"])
    raise ValueError(f"配置验证失败: {config_validation['errors']}")

logger.info("配置摘要: %s", config.get_config_summary())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动定时调度任务
    scheduler.start()
    logger.info("定时调度已启动")

    yield

    # 关闭定时调度任务
    scheduler.stop()
    logger.info("定时调度已停止")


# 创建 FastAPI 应用
app = FastAPI(
    title="热点监控服务",
    description="监控抖音创作者内容，自动提取热点选题",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(router, prefix=config.API_PREFIX)

# 健康检查接口
@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """健康检查接口"""
    return {
        "status": "healthy",
        "environment": config.ENVIRONMENT,
        "version": "1.0.0",
        "scheduler_running": scheduler.scheduler.running
    }

# 配置信息接口
@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    """获取配置信息（不包含敏感信息）"""
    return config.get_config_summary()

# 静态文件服务（可选）
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG
    )