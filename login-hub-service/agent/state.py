"""LangGraph 工作流状态定义"""
from typing import Optional, TypedDict


class LoginState(TypedDict, total=False):
    platform: str               # 平台名（config.PLATFORMS 的 key）
    action: str                 # "check" | "login" | "keepalive"
    logged_in: bool
    success: bool               # login/keepalive 流程是否达成目标
    message: str
    error: Optional[str]
    retries: int
