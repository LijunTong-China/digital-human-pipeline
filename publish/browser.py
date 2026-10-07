# -*- coding: utf-8 -*-
"""L1 环境层:公共浏览器驱动 —— **复用 login-hub-service 的登录态**(2026-10-07 定版)。

登录态来源(不再自建 profile):
- login-hub-service(端口 3459)持久化浏览器 `browser_data/shared`,人工登录一次,
  每 30 分钟自动保活,token 不过期;新增平台只改 hub 的 config.PLATFORMS
- 本模块优先 **CDP 接管 hub 的活浏览器**(端口 hub config.CDP_PORT=9340,共享实例零冲突);
  hub 浏览器没开时,用 hub 同一个 user_data_dir 起持久化浏览器(带上同一 CDP 端口)
- 发布前先查 hub `/api/quant/login_status/{platform}`;掉登录 → 终止提示人工去登录中心,
  **绝不自动重新登录**(README §2①)

铁律(README §5.1):禁 headless;不主动改 UA;网络与登录时一致(代码不碰代理)。
"""
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from behavior import dwell, scroll_randomly
from common import CFG, PCFG, log, abort

LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--lang=zh-CN",
    "--start-maximized",
]

# publish 平台名 → login-hub 平台名
HUB_PLATFORM = {"douyin": "douyin", "xhs": "xiaohongshu"}

CREATOR_URL = {
    "douyin": "https://creator.douyin.com/creator-micro/home",
    "xhs": "https://creator.xiaohongshu.com/publish/publish",
}

LOGIN_MARKS = {
    "douyin": ["login", "passport.douyin.com", "扫码登录"],
    "xhs": ["login", "扫码登录", "登录小红书"],
}

HUB = PCFG.get("hub", {})           # hub_api / hub_cdp_port / shared_profile


def hub_login_ok(platform: str) -> bool:
    """查 login-hub 的登录状态;hub 服务没开则视为未知(False,交由页面级体检兜底)。"""
    name = HUB_PLATFORM.get(platform, platform)
    try:
        r = requests.get(f"{HUB['hub_api']}/api/quant/login_status/{name}", timeout=5)
        ok = bool(r.json().get("logged_in"))
        log(f"[hub] {name} 登录态: {'有效' if ok else '失效/未登录'}")
        return ok
    except Exception as e:
        log(f"[hub] 登录态查询失败({e}),稍后由页面级体检兜底")
        return False


def open_page(platform: str):
    """优先 CDP 接管 hub 活浏览器;hub 没开则用 hub 的 shared profile 自起。"""
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    cdp = HUB.get("hub_cdp_port", 9340)
    if cdp:
        try:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp}")
            ctx = browser.contexts[0]
            log(f"[浏览器] {platform} CDP 接管 login-hub 浏览器(端口 {cdp})")
            return pw, browser, ctx.new_page()
        except Exception:
            log(f"[浏览器] hub 浏览器未运行,用 hub shared profile 自起")
    shared = Path(HUB["shared_profile"])
    browser = pw.chromium.launch_persistent_context(
        str(shared), headless=False, viewport=None,
        args=LAUNCH_ARGS + [f"--remote-debugging-port={cdp or 9340}"])
    log(f"[浏览器] {platform} 已启动(hub 同源 profile): {shared}")
    return pw, browser, browser.pages[0] if browser.pages else browser.new_page()


def health_check(page, platform: str) -> bool:
    """①账号体检:hub 登录态 + 页面级登录态 + 风控横幅。不过关返回 False(跳过该平台)。"""
    if not hub_login_ok(platform):
        name = HUB_PLATFORM[platform]
        log(f"[体检] {platform} 需人工登录:打开 http://localhost:3459/ → 「{name}」→ 登录")
        return False
    page.goto(CREATOR_URL[platform], wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    marks = LOGIN_MARKS[platform]
    # 只看可见文本(SPA 的登录弹窗模板会藏在 DOM 里,page.content() 会误报);
    # SSO 跳转可能慢,疑似未登录时等 5s 重查一次再下结论
    for attempt in range(2):
        url = page.url
        visible_txt = page.evaluate(
            "() => document.body.innerText")[:3000]
        url_bad = any(m in url for m in marks[:2])
        qr_visible = "扫码登录" in visible_txt
        if not url_bad and not qr_visible:
            break
        if attempt == 0:
            page.wait_for_timeout(5000)
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
    else:
        log(f"[体检] {platform} hub 认为已登录但创作者页未见登录态(url={url[:80]}),"
            f"去 http://localhost:3459/ 重新保活/登录该平台")
        return False
    body = page.evaluate("() => document.body.innerText")[:3000]
    hits = [w for w in ["验证码", "账号异常", "违规", "封禁", "受限", "申诉"] if w in body]
    if hits:
        log(f"[体检] {platform} 页面出现风控字样 {hits},跳过该平台(不自动处理)")
        return False
    log(f"[体检] {platform} 通过(登录态有效,无风控提示)")
    return True


def warmup(page, platform: str):
    """①暖场:进创作中心后先当 1~2 分钟真人(滚动浏览/停留),再开始发布操作。"""
    if not PCFG.get("warmup", True):
        return
    t0 = time.time()
    log(f"[暖场] {platform} 浏览创作中心…")
    dwell(page, 4, 9)
    scroll_randomly(page)
    dwell(page, 3, 7)
    log(f"[暖场] 完成,用时 {time.time()-t0:.0f}s")


def explore_hold(page, port: int):
    """--explore:浏览器保持打开供人工探查 UI 结构。"""
    log(f"[explore] 浏览器保持打开,调试端口 {port},Ctrl+C 退出")
    while True:
        time.sleep(3600)
