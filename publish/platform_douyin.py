# -*- coding: utf-8 -*-
"""⑥ 抖音平台适配:creator.douyin.com 创作者中心全自动发布。

流程(README §2⑥):入口 → 上传 → 轮询进度 → 填表(逐字拟人) → AI声明 → 发布 → 验证。
铁律:
- 选择器失配/风控弹窗/验证码 → 截图 + 抛 RiskError,绝不自动重试
- DOM 结构未实机核对前,先跑 `python publish/publish.py douyin --explore` 人工过一遍
"""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import behavior as B
from browser import open_page, health_check, warmup
from common import PCFG, log, abort
from content import tag_line

DONE_URL = re.compile(r"creator\.douyin\.com/creator-micro/content/(manage|publish)")


class RiskError(RuntimeError):
    """硬信号:验证码/风控横幅/选择器失配。触发即熔断计时。"""


def _shot(page, name: str):
    fp = Path(__file__).parent / "out" / f"douyin_{name}.png"
    page.screenshot(path=str(fp), full_page=True)
    log(f"[截图] {fp}")


def _body(page) -> str:
    return page.evaluate("() => document.body.innerText")[:5000]


def _check_risk(page):
    body = _body(page)
    if "验证码" in body or "安全验证" in body:
        _shot(page, "captcha")
        raise RiskError("出现验证码/安全验证,终止且熔断")


def run(video: Path, meta: dict, cover: Path | None, explore: bool = False):
    """全流程发布抖音。成功返回作品页 URL。"""
    pw, browser, page = open_page("douyin")
    try:
        if not health_check(page, "douyin"):
            abort("账号体检未过,跳过抖音", platform="douyin", code=3)
        warmup(page, "douyin")
        if explore:
            from browser import explore_hold
            explore_hold(page, PCFG["douyin"].get("debug_port", 9334))

        # 1. 进发布页
        page.goto("https://creator.douyin.com/creator-micro/content/upload",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        _check_risk(page)

        # 2. 上传(文件选择器喂 final_video.mp4)
        page.set_input_files("input[type=file]", str(video))
        log("[抖音] 已喂视频文件,等上传+转码…")
        deadline = time.time() + PCFG.get("upload_timeout_min", 15) * 60
        while time.time() < deadline:
            body = _body(page)
            if "重新上传" in body or "上传成功" in body or "%)" not in body and "%" not in body:
                break
            B.busy_wait(page, 8)     # 等待期间拟人活动,不机械空转
        else:
            _shot(page, "upload_timeout")
            raise RiskError("上传/转码超时")
        log("[抖音] 上传就绪")

        # 3. 填标题/简介(逐字拟人输入;先真实点击聚焦)
        m = meta["douyin"]
        title_loc = page.locator("input[placeholder*='标题'], textarea[placeholder*='标题']").first
        B.move_to_element(page, title_loc)
        title_loc.click()
        B.type_human(page, m["title"])
        B.nap(1.0, 3.0)
        desc_loc = page.locator(".notranslate, [contenteditable=true]").first
        try:
            B.move_to_element(page, desc_loc)
            desc_loc.click()
            B.type_human(page, m["desc"] + " " + tag_line(m["tags"]))
        except Exception as e:
            log(f"[warn] 简介区定位失败({e}),需核对选择器")
            _shot(page, "desc_fail")
            raise RiskError("简介区定位失败")

        # 4. AI 声明(合规必勾)
        if PCFG.get("ai_declare", True):
            try:
                sw = page.locator("text=内容由AI生成").first
                B.move_to_element(page, sw)
                sw.click()
                log("[抖音] 已勾选 AI 生成声明")
            except Exception:
                log("[warn] AI 声明入口未命中,人工核对选择器(不阻断)")

        # 5. 发布(拟人点击,失败即停)
        B.nap(2.0, 5.0)
        pub = page.locator("button:has-text('发布')").last
        B.move_to_element(page, pub)
        pub.click()
        log("[抖音] 已点发布,等跳转…")

        # 6. 验证:跳转 URL 匹配作品管理/发布成功页
        deadline = time.time() + 120
        while time.time() < deadline:
            if DONE_URL.search(page.url):
                log(f"[抖音] 发布成功 → {page.url}")
                return page.url
            page.wait_for_timeout(3000)
        _shot(page, "verify_fail")
        raise RiskError("点发布后 120s 未跳转成功页")
    finally:
        # 发布完成后停留 1~3 分钟看数据页再关(session 时长拟人,README §5.2)
        try:
            B.nap(60, 180)
        finally:
            browser.close()
            pw.stop()
