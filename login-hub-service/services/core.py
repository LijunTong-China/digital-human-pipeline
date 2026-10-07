"""通用平台登录态检测 / 登录 / 保活逻辑（配置驱动，全平台复用，单窗口多标签）

无痕原则：检测状态、保活都**不会主动拉起浏览器**——
- 浏览器未运行：状态读磁盘缓存（status_cache.json），但缓存有时效（STATUS_CACHE_TTL_SECONDS）:
  过期缓存只说明"上次检查时已登录",不能当当前登录态——cookie 过期/被风控踢下线/
  profile 更换都会失真。过期一律降级为 logged_in=False + 提示重新验证(2026-10-07 修)
- 浏览器运行中：实时读 Cookie 检测并更新缓存
只有用户点「登录」才会开浏览器。
"""
import json
import logging
import time
from typing import Any, Dict

import asyncio

import config
from browser.manager import browser_manager

logger = logging.getLogger("loginhub.core")


# ---------- 磁盘缓存（浏览器未运行时使用） ----------

def _cache_fresh(entry: Dict[str, Any]) -> bool:
    """缓存是否在 TTL 内(TTL 内才可当作当前登录态)。"""
    try:
        t = time.mktime(time.strptime(entry.get("last_check", ""), "%Y-%m-%d %H:%M:%S"))
    except (ValueError, TypeError):
        return False
    return (time.time() - t) < config.STATUS_CACHE_TTL_SECONDS


def _load_cache() -> Dict[str, Any]:
    try:
        return json.loads(config.STATUS_CACHE.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _save_cache(platform: str, result: Dict[str, Any]) -> None:
    try:
        cache = _load_cache()
        result = dict(result)
        result["source"] = "cache"
        cache[platform] = result
        config.STATUS_CACHE.parent.mkdir(parents=True, exist_ok=True)
        config.STATUS_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), "utf-8")
    except Exception:  # noqa: BLE001
        logger.warning("状态缓存写入失败", exc_info=True)


async def check_login(platform: str) -> Dict[str, Any]:
    """检测登录态：浏览器运行中读实时 Cookie；未运行读磁盘缓存，不弹窗。

    Returns:
        {"platform", "logged_in", "error", "last_check", "url", "source"}
    """
    pcfg = config.get_platform(platform)
    result: Dict[str, Any] = {
        "platform": platform,
        "logged_in": False,
        "error": None,
        "last_check": time.strftime("%Y-%m-%d %H:%M:%S"),
        "url": pcfg.home,
        "source": "live",
    }
    if not await browser_manager.is_running():
        cached = _load_cache().get(platform)
        if cached and _cache_fresh(cached):
            cached = dict(cached)
            cached["last_check"] = f"{cached.get('last_check')}（缓存，浏览器未运行）"
            return cached
        if cached:
            result["error"] = (f"登录状态缓存已过期({cached.get('last_check')},超过 "
                               f"{config.STATUS_CACHE_TTL_SECONDS//3600}h),需开浏览器重新验证;"
                               "若页面也未登录,请到登录中心重新扫码")
        else:
            result["error"] = "浏览器未运行且无历史状态"
        return result
    try:
        context = await browser_manager.get_context_if_running()
        if context is None:  # 关窗竞态：按未运行处理
            cached = _load_cache().get(platform)
            if cached and _cache_fresh(cached):
                return cached
            result["error"] = "浏览器未运行且缓存缺失/过期,需重新验证"
            return result
        cookies = await context.cookies(pcfg.home)
        names = {c["name"] for c in cookies}
        logged_in = all(n in names for n in pcfg.session_cookie_names)
        result["logged_in"] = logged_in
        if not logged_in:
            result["error"] = f"未检测到登录 Cookie（{', '.join(pcfg.session_cookie_names)}）"
        _save_cache(platform, result)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] 登录检测失败", platform)
        result["error"] = str(exc)
        return result


async def open_login_page(platform: str) -> Dict[str, Any]:
    """打开（或拉起）浏览器窗口，新开标签页进入登录页，等待人工完成登录。

    这是唯一会主动启动浏览器的路径。
    """
    pcfg = config.get_platform(platform)
    try:
        logger.warning(" [%s] 打开登录页 —— 触发来源排查点", platform)
        page = await browser_manager.open_page(pcfg.login_url)
        try:
            await page.bring_to_front()
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "url": page.url, "message": pcfg.login_hint}
    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] 打开登录页失败", platform)
        return {"ok": False, "error": str(exc)}


async def wait_for_login(platform: str,
                         timeout: int = config.QR_WAIT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """轮询等待人工登录完成（供 LangGraph 节点调用）。"""
    deadline = time.monotonic() + timeout
    status = await check_login(platform)
    while time.monotonic() < deadline:
        status = await check_login(platform)
        if status["logged_in"]:
            logger.info("[%s] 登录成功", platform)
            return {"success": True, **status}
        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)
    return {"success": False, **status, "error": f"登录等待超时（{timeout}s）"}


async def keepalive_touch(platform: str) -> Dict[str, Any]:
    """保活：仅当浏览器已运行时开标签页刷新会话 Cookie；未运行则跳过，不弹窗。"""
    if not await browser_manager.is_running():
        status = await check_login(platform)
        status["keepalive"] = "skipped_browser_closed"
        return status
    status = await check_login(platform)  # 此刻浏览器在运行，实时检测
    if not status["logged_in"]:
        status["keepalive"] = "skipped_not_logged_in"
        return status
    try:
        page = await browser_manager.open_page(config.get_platform(platform).home)
        await page.mouse.wheel(0, 600)
        await asyncio.sleep(2)
        await page.close()  # 保活页即用即关，避免标签页越积越多
        # 重新确认会话仍有效（访问后 Cookie 可能被刷新）
        refreshed = await check_login(platform)
        refreshed["keepalive"] = "done"
        logger.info("[%s] 保活完成, logged_in=%s", platform, refreshed["logged_in"])
        return refreshed
    except Exception as exc:  # noqa: BLE001
        logger.exception("[%s] 保活失败", platform)
        status["keepalive"] = f"failed: {exc}"
        return status
