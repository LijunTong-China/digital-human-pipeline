"""LangGraph 工作流节点：多平台登录态管理

工作流（按 state.platform 分平台执行）：
  check_login ──已登录──▶ finish(成功)
      │未登录
      ├─ action=login ───▶ open_login_page ─▶ wait_for_scan ─┬─成功▶ finish(成功)
      │                                                      └─超时▶ retry/finish(失败)
      └─ action=keepalive ─▶ keepalive_touch ─▶ finish

保活过程发现掉登录（action=keepalive 且 logged_in=False）也走 finish(失败)，
由调度层记录日志，等待人工重新登录。
"""
import logging
from typing import Any, Dict

import config
import services.core as core
from agent.state import LoginState

logger = logging.getLogger("loginhub.graph")

MAX_RETRIES = 1  # 人工登录最多重试 1 次


def _platform(state: LoginState) -> str:
    return state.get("platform") or "douyin"


async def node_check_login(state: LoginState) -> Dict[str, Any]:
    platform = _platform(state)
    status = await core.check_login(platform)
    return {
        "logged_in": status["logged_in"],
        "error": status.get("error"),
        "message": "已登录" if status["logged_in"] else "未登录",
    }


async def node_open_login_page(state: LoginState) -> Dict[str, Any]:
    platform = _platform(state)
    result = await core.open_login_page(platform)
    return {
        "success": result.get("ok", False),
        "error": result.get("error"),
        "message": result.get("message", config.get_platform(platform).login_hint),
    }


async def node_wait_for_scan(state: LoginState) -> Dict[str, Any]:
    platform = _platform(state)
    result = await core.wait_for_login(platform)
    return {
        "logged_in": result.get("logged_in", False),
        "success": result.get("success", False),
        "error": result.get("error"),
        "retries": state.get("retries", 0) + (0 if result.get("success") else 1),
        "message": "登录成功" if result.get("success") else (result.get("error") or "登录未完成"),
    }


async def node_keepalive(state: LoginState) -> Dict[str, Any]:
    platform = _platform(state)
    result = await core.keepalive_touch(platform)
    return {
        "logged_in": result.get("logged_in", False),
        "success": result.get("logged_in", False) and result.get("keepalive") == "done",
        "error": result.get("error"),
        "message": f"保活完成: {result.get('keepalive')}",
    }


async def node_finish(state: LoginState) -> Dict[str, Any]:
    logger.info("流程结束: platform=%s action=%s logged_in=%s message=%s",
                _platform(state), state.get("action"),
                state.get("logged_in"), state.get("message"))
    return {}
