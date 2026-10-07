"""抖音视频发布（创作者平台 web 端，全自动）

流程：creator.douyin.com 上传页 → 选文件 → 等上传/转码完成 → 填标题话题 → 点发布
选择器以页面实测为准，找不到元素时抛出带阶段名的错误，便于迭代。
"""
import logging
from typing import Any, Dict, Optional

from browser.manager import browser_manager

logger = logging.getLogger("loginhub.publish.douyin")

UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"


class PublishError(Exception):
    """带阶段信息的发布失败"""

    def __init__(self, stage: str, detail: str):
        super().__init__(f"[{stage}] {detail}")
        self.stage = stage
        self.detail = detail


async def publish_video(video_path: str,
                        title: str,
                        topics: Optional[list[str]] = None,
                        timeout_ms: int = 300_000,
                        dry_run: bool = False) -> Dict[str, Any]:
    """发布一条视频。

    Args:
        video_path: 视频文件绝对路径（浏览器所在机器可访问）
        title: 视频标题/文案
        topics: 话题列表（不带#号），拼进文案
        timeout_ms: 上传+转码总超时
        dry_run: 预演模式——走完上传/转码/填文案，停在发布按钮前不点击，且不关闭页面
    """
    topics = topics or []
    topic_text = " ".join(f"#{t}" for t in topics)
    full_text = f"{title} {topic_text}".strip()

    context = await browser_manager.get_context()
    page = await context.new_page()
    try:
        # ---- 阶段1: 打开上传页（会校验登录态）----
        try:
            await page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=60_000)
        except Exception as e:  # noqa: BLE001
            raise PublishError("open_upload_page", str(e))
        await page.wait_for_timeout(3000)
        if "login" in page.url:
            raise PublishError("not_logged_in",
                               "创作者平台未登录，请先在登录中心登录抖音")

        # ---- 阶段1.5: 清掉上次未发布的残留草稿（否则会占着编辑器）----
        try:
            discard = page.get_by_text("放弃", exact=True)
            if await discard.count() > 0:
                await discard.first.click(timeout=5_000)
                logger.info("已放弃上次残留的未发布草稿")
                await page.wait_for_timeout(2000)
        except Exception:  # noqa: BLE001
            pass

        # ---- 阶段2: 上传文件 ----
        # 上传页的隐藏 input[type=file]（accept 含 video）
        try:
            file_input = page.locator('input[type="file"]').first
            await file_input.wait_for(state="attached", timeout=20_000)
            await file_input.set_input_files(video_path)
        except PublishError:
            raise
        except Exception as e:  # noqa: BLE001
            raise PublishError("select_file", f"找不到上传入口或选文件失败: {e}")

        # ---- 阶段3: 等待上传+转码完成 ----
        # 关键：不能只看"重新上传"字样（转码期间也存在）。
        # 以"转码中"提示消失 + 发布按钮可用为准。
        try:
            await page.wait_for_selector('text=重新上传', timeout=timeout_ms)
        except Exception:  # noqa: BLE001
            raise PublishError("wait_upload", "等待上传完成超时（未见重新上传字样）")
        # 轮询等转码结束："预览转码中"字样消失
        deadline = timeout_ms / 1000
        waited = 0.0
        while waited < deadline:
            transcoding = await page.locator('text=转码中').count()
            if transcoding == 0:
                break
            await page.wait_for_timeout(3000)
            waited += 3
        else:
            raise PublishError("wait_transcode", f"等待转码完成超时（{deadline}s）")
        logger.info("转码完成，耗时约 %.0fs", waited)
        await page.wait_for_timeout(1000)  # 留缓冲让封面生成

        # ---- 阶段4: 填标题与话题 ----
        # 创作者平台的标题即文案输入框（contenteditable 或 textarea）
        try:
            editor = page.locator(
                'div[contenteditable="true"], textarea[placeholder*="标题"]').first
            await editor.wait_for(state="visible", timeout=15_000)
            await editor.click()
            await page.keyboard.insert_text(full_text)
        except Exception as e:  # noqa: BLE001
            raise PublishError("fill_title", f"填写标题/文案失败: {e}")

        # ---- 阶段5: 点发布（含可能的确认弹窗）；预演模式到此为止 ----
        shot_before = await config_shots(page)
        logger.warning("点击发布前截图: %s, URL=%s", shot_before, page.url)
        if dry_run:
            btn = page.get_by_role("button", name="发布", exact=False).first
            btn_visible = await btn.count() > 0 and await btn.is_visible()
            return {
                "ok": btn_visible,
                "dry_run": True,
                "url": page.url,
                "video_path": video_path,
                "title": full_text,
                "message": ("预演通过：上传/转码/文案就绪，发布按钮可见，未点击"
                            if btn_visible else
                            "预演未通过：找不到可见的发布按钮，需核对选择器"),
            }
        try:
            btn = page.get_by_role("button", name="发布", exact=False).first
            await btn.click(timeout=10_000)
            await page.wait_for_timeout(2000)
            # 可能出现二次确认弹窗
            confirm = page.get_by_role("button", name="确认", exact=False)
            if await confirm.count() > 0:
                await confirm.first.click(timeout=5_000)
        except Exception as e:  # noqa: BLE001
            raise PublishError("click_publish", str(e))

        # ---- 阶段6: 确认发布结果（URL 跳到内容管理 / 成功提示）----
        await page.wait_for_timeout(3000)
        shot_after = await config_shots(page)
        logger.warning("点击发布后截图: %s, URL=%s", shot_after, page.url)
        # 抓取页面上的 toast/弹窗文本，便于定位拦截原因
        toasts: list[str] = []
        try:
            for loc in page.locator(
                    'div[class*="toast"],div[class*="modal"],div[class*="dialog"],'
                    'div[class*="message"],div[role="alert"]').all()[:10]:
                t = (await loc.inner_text()).strip()
                if t:
                    toasts.append(t[:100])
        except Exception:  # noqa: BLE001
            pass
        logger.warning("点击后弹窗/提示: %s", toasts)
        ok_hint = ("content/manage" in page.url
                   or await page.locator('text=发布成功').count() > 0)
        return {
            "ok": bool(ok_hint),
            "url": page.url,
            "video_path": video_path,
            "title": full_text,
            "toasts": toasts,
            "message": "发布成功" if ok_hint else f"已点击发布但未见成功标志，提示: {toasts}",
        }
    except PublishError as e:
        logger.error("抖音发布失败: %s %s", e.stage, e.detail)
        # 失败时截图留档
        try:
            shot = await config_shots(page)
            if shot:
                logger.error("失败截图: %s", shot)
        except Exception:  # noqa: BLE001
            pass
        raise
    finally:
        if not dry_run:  # 预演模式保留页面供人工检查
            await page.close()


async def config_shots(page) -> Optional[str]:
    """现场截图（异步）"""
    import time
    import config
    d = config.BASE_DIR / "data" / "publish_shots"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"fail_{int(time.time())}.png"
    try:
        await page.screenshot(path=str(path), full_page=False)
        return str(path)
    except Exception:  # noqa: BLE001
        return None
