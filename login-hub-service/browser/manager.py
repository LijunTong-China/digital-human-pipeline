"""Playwright 持久化浏览器管理器（单窗口多标签版）

一个共享 profile（browser_data/shared）+ 一个浏览器窗口：
- 每个平台一个标签页，Cookie 按域名隔离互不干扰
- 人工登录一次后 Cookie 写入本地磁盘，重启不丢
- 配合定时保活访问，最大化延长 token 有效期
"""
import asyncio
import logging
import traceback
from typing import Optional

from playwright.async_api import BrowserContext, Page, async_playwright, Playwright

import config

logger = logging.getLogger("loginhub.browser")


class BrowserManager:
    """单例式管理一个持久化 Chromium 实例（一个窗口，多平台标签页）"""

    def __init__(self) -> None:
        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None
        self._lock = asyncio.Lock()

    async def get_context(self) -> BrowserContext:
        async with self._lock:
            if self._context is not None and self._context.pages:
                return self._context
            config.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            logger.info("启动持久化浏览器: %s", config.USER_DATA_DIR)
            # 排查弹窗：记录是谁触发了浏览器启动
            logger.warning("浏览器启动调用栈:\n%s", "".join(traceback.format_stack()[-8:-1]))
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(config.USER_DATA_DIR),
                headless=False,  # 人工登录需要操作，必须有头
                viewport={"width": 1380, "height": 860},
                args=[
                    *(["--remote-debugging-port=%d" % config.CDP_PORT] if config.CDP_PORT else []),
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
            )
            # 简单隐藏 webdriver 特征，降低风控概率
            await self._context.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
            )
            return self._context

    async def open_page(self, url: str) -> Page:
        """在同一窗口里新开一个标签页访问 url。

        首次启动浏览器自带的 about:blank 标签页直接拿来用，不额外开新页。
        """
        context = await self.get_context()
        blank = next((p for p in context.pages if p.url in ("about:blank", "")), None)
        page = blank if blank else await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        return page

    async def is_running(self) -> bool:
        """浏览器窗口是否真的还开着（用户关窗后返回 False，但不会重新启动）"""
        if self._context is None:
            return False
        try:
            return bool(self._context.pages)
        except Exception:  # noqa: BLE001  窗口已被外部关闭
            self._context = None
            return False

    async def get_context_if_running(self) -> Optional[BrowserContext]:
        """仅在浏览器确实在运行时返回 context；用户已关窗则清理状态并返回 None。

        关键：绝不在这里重新启动浏览器（检测/保活等后台路径用它，避免弹窗）。
        """
        if await self.is_running():
            return self._context
        # 用户关掉了所有标签页 = 关掉了浏览器，清理内部状态
        if self._context is not None:
            try:
                await self._context.close()
            except Exception:  # noqa: BLE001
                pass
            self._context = None
        return None

    async def shutdown(self) -> None:
        if self._context:
            try:
                await self._context.close()
            finally:
                self._context = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


browser_manager = BrowserManager()
