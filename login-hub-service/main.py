"""多平台登录中心（login-hub-service）

启动: uvicorn main:app --host 0.0.0.0 --port 3459

接口：
  GET  /api/quant/platforms                    已接入平台列表
  GET  /api/quant/login_status_all             所有平台登录状态
  GET  /api/quant/login_status/{platform}      单平台登录状态
  POST /api/quant/open-login-tab/{platform}    打开登录页并阻塞等待人工登录
  POST /api/quant/keepalive/{platform}         手动保活（调试用）
  GET  /api/quant/cookies/{platform}           导出 Cookies
  POST /api/quant/fetch/{platform}             登录态浏览器代抓页面
  POST /api/quant/xhr_capture/{platform}       通用 XHR 拦截抓取
抖音特有能力（搜索/视频详情/媒体捕获）保留在 /api/quant/douyin/* 路由组。
"""
import asyncio
import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from agent.graph import login_graph
from browser.manager import browser_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
# 同时落盘日志，便于排查"谁在弹浏览器"
_file_handler = logging.FileHandler(config.BASE_DIR / "logs" / "loginhub.log", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
logging.getLogger().addHandler(_file_handler)
logger = logging.getLogger("loginhub.main")


async def keepalive_loop() -> None:
    """定时保活：对每个平台周期性执行 keepalive 工作流，防止 token 过期。

    发现掉登录时仅记录日志（登录状态页会显示未登录），等待人工重新登录。
    """
    while True:
        for platform in config.PLATFORMS:
            try:
                await login_graph.ainvoke({"platform": platform, "action": "keepalive"})
            except Exception:  # noqa: BLE001
                logger.exception("[%s] 保活工作流执行异常", platform)
        await asyncio.sleep(config.KEEPALIVE_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(keepalive_loop())
    logger.info("保活调度已启动，间隔 %s 秒，平台: %s",
                config.KEEPALIVE_INTERVAL_SECONDS, ", ".join(config.PLATFORMS))
    yield
    task.cancel()
    await browser_manager.shutdown()


app = FastAPI(title="多平台登录中心", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request, call_next):
    """排查弹窗：记录每一个 HTTP 请求（方法/路径/来源端口）"""
    if not request.url.path.startswith("/api/quant/login_status"):
        logger.warning("HTTP %s %s from %s", request.method, request.url.path,
                       request.client.port if request.client else "?")
    return await call_next(request)


def _require_platform(platform: str) -> None:
    if platform not in config.PLATFORMS:
        raise HTTPException(
            status_code=404,
            detail=f"平台 {platform} 尚未接入（已接入: {', '.join(config.PLATFORMS)}）")


# ---------- 对齐原系统的接口（多平台通用） ----------

@app.get("/api/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "browser_running": await browser_manager.is_running()}


@app.get("/api/quant/platforms")
async def platforms() -> Dict[str, Any]:
    return {"platforms": [
        {"name": p.name, "home": p.home,
         "session_cookies": p.session_cookie_names}
        for p in config.PLATFORMS.values()
    ]}


@app.get("/api/quant/login_status_all")
async def login_status_all() -> Dict[str, Any]:
    """所有平台登录状态"""
    result: Dict[str, Any] = {}
    for name in config.PLATFORMS:
        status = await login_graph.ainvoke({"platform": name, "action": "check"})
        result[name] = {
            "platform": name,
            "logged_in": status["logged_in"],
            "error": status.get("error"),
            "cdp_endpoint": None,          # 预留：原系统 Chrome CDP 接入点
            "last_update_time": None,
            "url": config.PLATFORMS[name].home,
        }
    return result


@app.get("/api/quant/login_status/{platform}")
async def login_status(platform: str) -> Dict[str, Any]:
    _require_platform(platform)
    result = await login_graph.ainvoke({"platform": platform, "action": "check"})
    return {"platform": platform, "logged_in": result["logged_in"], "error": result.get("error")}


@app.post("/api/quant/open-login-tab/{platform}")
async def open_login_tab(platform: str) -> Dict[str, Any]:
    """打开登录页（弹出扫码/登录框），并阻塞等待人工登录结果"""
    _require_platform(platform)
    result = await login_graph.ainvoke({"platform": platform, "action": "login", "retries": 0})
    return {
        "platform": platform,
        "logged_in": result["logged_in"],
        "success": result.get("success", False),
        "message": result.get("message"),
        "error": result.get("error"),
    }


# ---------- 辅助接口 ----------

@app.post("/api/quant/keepalive/{platform}")
async def trigger_keepalive(platform: str) -> Dict[str, Any]:
    """手动触发一次保活（调试用；正常由后台定时执行）"""
    _require_platform(platform)
    result = await login_graph.ainvoke({"platform": platform, "action": "keepalive"})
    return {"platform": platform, "logged_in": result["logged_in"], "message": result.get("message")}


# ---------- 浏览器能力接口（供爬虫/监控服务复用登录态） ----------

class FetchRequest(BaseModel):
    url: str
    wait_ms: int = 5000       # 页面渲染等待
    scroll_times: int = 0     # 滚动次数（触发懒加载）


@app.get("/api/quant/cookies/{platform}")
async def export_cookies(platform: str) -> Dict[str, Any]:
    """导出当前登录态的 Cookies（供爬虫服务直连请求使用）"""
    _require_platform(platform)
    context = await browser_manager.get_context()
    cookies = await context.cookies(config.PLATFORMS[platform].home)
    return {
        "platform": platform,
        "count": len(cookies),
        "cookies": {c["name"]: c["value"] for c in cookies},
    }


@app.post("/api/quant/fetch/{platform}")
async def fetch_page(platform: str, req: FetchRequest) -> Dict[str, Any]:
    """用登录态浏览器代抓页面：打开URL → 等渲染 → 可滚动 → 返回渲染后HTML+Cookies

    供热点监控服务的爬虫模块复用真实登录态，规避无签名请求被拦截的问题。
    """
    _require_platform(platform)
    context = await browser_manager.get_context()
    page = await context.new_page()
    try:
        await page.goto(req.url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(req.wait_ms)
        for _ in range(req.scroll_times):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight * 0.8)")
            await page.wait_for_timeout(1500)
        html = await page.content()
        cookies = await context.cookies()
        title = await page.title()
        return {
            "platform": platform,
            "url": req.url,
            "title": title,
            "logged_in": _has_session_cookies(platform, cookies),
            "cookies": {c["name"]: c["value"] for c in cookies},
            "html": html,
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"页面抓取失败: {e}")
    finally:
        await page.close()


def _has_session_cookies(platform: str, cookies: List[Dict[str, Any]]) -> bool:
    names = {c["name"] for c in cookies}
    return all(n in names for n in config.PLATFORMS[platform].session_cookie_names)


class XhrCaptureRequest(BaseModel):
    url: str
    api_pattern: str = "search"    # 拦截包含该关键字的XHR响应
    wait_ms: int = 6000
    scroll_times: int = 2


@app.post("/api/quant/xhr_capture/{platform}")
async def xhr_capture(platform: str, req: XhrCaptureRequest) -> Dict[str, Any]:
    """通用XHR拦截抓取：打开URL→可选滚动→返回命中api_pattern的JSON响应列表

    用于客户端渲染站点（知乎搜索等）：页面数据由XHR加载，直接拦截接口响应最干净。
    """
    _require_platform(platform)
    context = await browser_manager.get_context()
    page = await context.new_page()
    captured: List[Dict[str, Any]] = []

    async def on_response(resp):
        if req.api_pattern in resp.url:
            try:
                captured.append(await resp.json())
            except Exception:  # noqa: BLE001
                pass

    page.on("response", on_response)
    try:
        await page.goto(req.url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(req.wait_ms)
        for _ in range(req.scroll_times):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight * 0.8)")
            await page.wait_for_timeout(2000)
        cookies = await context.cookies()
        return {
            "platform": platform,
            "url": req.url,
            "title": await page.title(),
            "captured_count": len(captured),
            "captured": captured,
            "cookies": {c["name"]: c["value"] for c in cookies},
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"XHR拦截失败: {e}")
    finally:
        await page.close()


# ---------- 抖音特有能力（保留原逻辑，路由前缀不变以兼容热点监控服务） ----------

class SearchRequest(BaseModel):
    keyword: str
    wait_ms: int = 6000
    scroll_times: int = 3


@app.post("/api/quant/search/{platform}")
async def search_videos(platform: str, req: SearchRequest) -> Dict[str, Any]:
    """真实用户行为搜索：首页→输入关键词→回车→等结果渲染→返回HTML

    模拟真人操作让页面JS自行生成搜索签名，避免直接跳URL触发验证码。
    """
    if platform != "douyin":
        raise HTTPException(status_code=404, detail="搜索为抖音特有能力")
    context = await browser_manager.get_context()
    page = await context.new_page()
    try:
        await page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(3000)

        # 搜索框输入（模拟真人）
        box = page.locator('input[data-e2e="searchbar-input"]')
        await box.wait_for(state="visible", timeout=15_000)
        await box.click()
        await box.fill(req.keyword)
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")

        # 等待跳转到搜索结果页
        await page.wait_for_url("**/search/**", timeout=20_000)
        await page.wait_for_timeout(req.wait_ms)

        for _ in range(req.scroll_times):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight * 0.8)")
            await page.wait_for_timeout(1500)

        html = await page.content()
        cookies = await context.cookies()
        is_captcha = "验证码" in (await page.title()) or "验证码中间页" in html[:5000]
        return {
            "platform": platform,
            "keyword": req.keyword,
            "url": page.url,
            "logged_in": _has_session_cookies(platform, cookies),
            "captcha": is_captcha,
            "cookies": {c["name"]: c["value"] for c in cookies},
            "html": html,
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"搜索失败: {e}")
    finally:
        await page.close()


class VideoDetailRequest(BaseModel):
    video_id: str
    wait_ms: int = 6000


@app.post("/api/quant/video_detail/{platform}")
async def video_detail(platform: str, req: VideoDetailRequest) -> Dict[str, Any]:
    """打开视频详情页并拦截 /aweme/detail XHR响应，获取完整真实视频数据（含无水印播放地址）"""
    if platform != "douyin":
        raise HTTPException(status_code=404, detail="视频详情为抖音特有能力")
    context = await browser_manager.get_context()
    page = await context.new_page()
    captured: Dict[str, Any] = {}

    async def on_response(resp):
        if "aweme/detail" in resp.url or ("/aweme/v1/web/" in resp.url and "detail" in resp.url):
            try:
                body = await resp.json()
                if isinstance(body, dict) and body.get("aweme_detail"):
                    captured["data"] = body
            except Exception:  # noqa: BLE001
                pass

    page.on("response", on_response)
    try:
        await page.goto(f"https://www.douyin.com/video/{req.video_id}",
                        wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(req.wait_ms)
        title = await page.title()
        cookies = await context.cookies()
        return {
            "platform": platform,
            "video_id": req.video_id,
            "title": title,
            "captcha": "验证码" in title,
            "detail": captured.get("data"),
            "cookies": {c["name"]: c["value"] for c in cookies},
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"详情抓取失败: {e}")
    finally:
        await page.close()


class CaptureRequest(BaseModel):
    video_id: str
    max_wait_seconds: int = 90    # 最长捕获等待（边播边收分段）
    min_bytes: int = 200_000      # 最少捕获字节数（防误判）


class CaptureRequest(BaseModel):
    video_id: str
    max_wait_seconds: int = 90    # 最长捕获等待（边播边收分段）
    min_bytes: int = 200_000      # 最少捕获字节数（防误判）


class PublishRequest(BaseModel):
    video_path: str               # 视频文件绝对路径
    title: str                    # 标题/文案
    topics: List[str] = []        # 话题（不带#号）
    dry_run: bool = False         # 预演：走到发布按钮前停下，不点发布


@app.post("/api/quant/publish/{platform}")
async def publish_video(platform: str, req: PublishRequest) -> Dict[str, Any]:
    """全自动发布视频（当前仅抖音）：上传→转码→填标题话题→直接发布"""
    if platform != "douyin":
        raise HTTPException(status_code=404, detail="发布为抖音特有能力（其余平台后续接入）")
    import os
    if not os.path.isfile(req.video_path):
        raise HTTPException(status_code=400, detail=f"视频文件不存在: {req.video_path}")
    from services import douyin_publish
    try:
        result = await douyin_publish.publish_video(req.video_path, req.title, req.topics,
                                                    dry_run=req.dry_run)
        return result
    except douyin_publish.PublishError as e:
        raise HTTPException(status_code=502, detail=f"[{e.stage}] {e.detail}")


# L3: MSE媒体分段捕获 —— 抖音播放用blob:src，但真实媒体分段走CDN，
# 浏览器要播就必须下载分段，拦截响应即可还原视频（不受"不允许下载"限制）
CDN_PATTERNS = ("douyinvod.com", "/aweme/v1/play/", "bytevod")


@app.post("/api/quant/capture_video/{platform}")
async def capture_video(platform: str, req: CaptureRequest) -> Dict[str, Any]:
    """打开详情页→模拟播放→拦截CDN媒体分段→按流分组拼接还原文件

    抖音音轨/视频轨是两条独立的CDN流（各自有独立总长度），
    必须按URL分组分别拼接；ASR侧只取含音轨的文件。
    返回落盘文件列表（与热点监控服务同机，可直读），调用方负责用后删除。
    """
    if platform != "douyin":
        raise HTTPException(status_code=404, detail="媒体捕获为抖音特有能力")

    context = await browser_manager.get_context()
    page = await context.new_page()
    # group_key(url去query) -> [(range_start, body)]
    stream_groups: Dict[str, List[Tuple[int, bytes]]] = {}
    total_bytes = 0

    async def on_response(resp):
        nonlocal total_bytes
        u = resp.url
        if not any(p in u for p in CDN_PATTERNS):
            return
        try:
            body = await resp.body()
            if not body:
                return
            start = 0
            cr = resp.headers.get("content-range")  # "bytes 12345-67890/999999"
            if cr:
                m = re.match(r"bytes\s+(\d+)-", cr)
                if m:
                    start = int(m.group(1))
            stream_groups.setdefault(u.split("?")[0], []).append((start, body))
            total_bytes += len(body)
        except Exception:  # noqa: BLE001
            pass

    page.on("response", on_response)
    try:
        await page.goto(f"https://www.douyin.com/video/{req.video_id}",
                        wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(3000)
        title = await page.title()
        if "验证码" in title:
            raise HTTPException(status_code=502, detail="触发验证码")

        # 模拟点击播放
        try:
            await page.locator("xg-video-container, video").first.click(timeout=5000)
        except Exception:  # noqa: BLE001
            await page.keyboard.press("Space")

        # 8倍速播放加速分段下发；连续2轮字节不增长视为完成
        try:
            await page.evaluate(
                "const v=document.querySelector('video'); if(v) v.playbackRate = 8")
        except Exception:  # noqa: BLE001
            pass

        deadline = time.time() + req.max_wait_seconds
        last_total, stable_rounds = 0, 0
        while time.time() < deadline:
            await page.wait_for_timeout(2000)
            if total_bytes == last_total and total_bytes >= req.min_bytes:
                stable_rounds += 1
                if stable_rounds >= 2:
                    break
            elif total_bytes == last_total:
                try:
                    await page.evaluate(
                        "const v=document.querySelector('video'); if(v) v.currentTime += 5")
                except Exception:  # noqa: BLE001
                    pass
            else:
                stable_rounds = 0
            last_total = total_bytes

        if total_bytes < req.min_bytes:
            raise HTTPException(status_code=502,
                                detail=f"分段捕获不足: {total_bytes}字节")

        # 每条流独立拼接落盘
        os.makedirs(config.MEDIA_DIR, exist_ok=True)
        files = []
        for idx, (gkey, items) in enumerate(sorted(stream_groups.items(),
                                                   key=lambda kv: -sum(len(b) for _, b in kv[1]))):
            out_path = str(config.MEDIA_DIR / f"{req.video_id}_s{idx}.mp4")
            with open(out_path, "wb") as f:
                for _, body in sorted(items, key=lambda x: x[0]):
                    f.write(body)
            files.append({"path": out_path, "bytes": sum(len(b) for _, b in items),
                          "segments": len(items), "stream": gkey[-60:]})

        return {
            "platform": platform,
            "video_id": req.video_id,
            "title": title,
            "files": files,
            "total_bytes": total_bytes,
        }
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"媒体捕获失败: {e}")
    finally:
        await page.close()


app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3459)
