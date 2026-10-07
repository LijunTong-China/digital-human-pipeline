"""抖音登录态：现委托给通用 core，保留模块入口便于单独扩展抖音特有逻辑"""
from typing import Any, Dict

import services.core as core


async def check_login() -> Dict[str, Any]:
    return await core.check_login("douyin")


async def open_login_page() -> Dict[str, Any]:
    return await core.open_login_page("douyin")


async def wait_for_login() -> Dict[str, Any]:
    return await core.wait_for_login("douyin")


async def keepalive_touch() -> Dict[str, Any]:
    return await core.keepalive_touch("douyin")
