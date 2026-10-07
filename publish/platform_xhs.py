# -*- coding: utf-8 -*-
"""⑦ 小红书平台适配:creator.xiaohongshu.com 全自动发布(含封面上传)。

流程(README §2⑦):上传视频 → 等转码 → 封面 → 填标题/正文/标签 → AI声明 → 发布 → 验证。
铁律同抖音:失配/验证码 → 截图 + RiskError,绝不自动重试。
DOM 未实机核对前,先跑 `python publish/publish.py xhs --explore`。
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

DONE_URL = re.compile(r"xiaohongshu\.com/(explore|user/profile)/|publish\?success")


class RiskError(RuntimeError):
    pass


def _shot(page, name: str):
    fp = Path(__file__).parent / "out" / f"xhs_{name}.png"
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
    pw, browser, page = open_page("xhs")
    try:
        if not health_check(page, "xhs"):
            abort("账号体检未过,跳过小红书", platform="xhs", code=3)
        warmup(page, "xhs")
        if explore:
            from browser import explore_hold
            explore_hold(page, PCFG["xhs"].get("debug_port", 9335))

        # 1. 上传视频(发布页自带 input[type=file])
        page.set_input_files("input[type=file]", str(video))
        log("[小红书] 已喂视频文件,等上传+转码…")
        deadline = time.time() + PCFG.get("upload_timeout_min", 15) * 60
        while time.time() < deadline:
            body = _body(page)
            if "上传成功" in body or ("重新上传" in body and "%" not in body):
                break
            B.busy_wait(page, 8)
        else:
            _shot(page, "upload_timeout")
            raise RiskError("上传/转码超时")
        log("[小红书] 上传就绪")

        # 2. 封面(小红书必传):上传入口需实机核对,失败先告警不阻断(平台会自动取帧)
        if cover:
            try:
                cov = page.locator("text=设置封面, .cover-btn, [class*=cover]").first
                B.move_to_element(page, cov)
                cov.click()
                page.wait_for_timeout(2000)
                page.set_input_files("input[type=file]", str(cover))
                log("[小红书] 已上传封面")
            except Exception as e:
                log(f"[warn] 封面上传入口未命中({e}),平台将自动取帧兜底")
                _shot(page, "cover_fail")

        # 3. 填标题/正文(逐字拟人)
        m = meta["xhs"]
        title_loc = page.locator("input[placeholder*='标题'], textarea[placeholder*='标题']").first
        B.move_to_element(page, title_loc)
        title_loc.click()
        B.type_human(page, m["title"])
        B.nap(1.0, 3.0)
        body_loc = page.locator("[contenteditable=true], textarea[placeholder*='正文']").first
        B.move_to_element(page, body_loc)
        body_loc.click()
        B.type_human(page, m["body"] + "\n\n" + tag_line(m["tags"]))

        # 4. AI 声明
        if PCFG.get("ai_declare", True):
            try:
                sw = page.locator("text=AI生成").first
                B.move_to_element(page, sw)
                sw.click()
                log("[小红书] 已勾选 AI 生成声明")
            except Exception:
                log("[warn] AI 声明入口未命中,人工核对(不阻断)")

        # 5. 发布
        B.nap(2.0, 5.0)
        pub = page.locator("button:has-text('发布')").last
        B.move_to_element(page, pub)
        pub.click()
        log("[小红书] 已点发布,等跳转…")

        # 6. 验证
        deadline = time.time() + 120
        while time.time() < deadline:
            if DONE_URL.search(page.url):
                log(f"[小红书] 发布成功 → {page.url}")
                return page.url
            page.wait_for_timeout(3000)
        _shot(page, "verify_fail")
        raise RiskError("点发布后 120s 未跳转成功页")
    finally:
        try:
            B.nap(60, 180)
        finally:
            browser.close()
            pw.stop()
