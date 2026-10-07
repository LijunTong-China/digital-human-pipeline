# -*- coding: utf-8 -*-
"""②PPT 生成自动化(NotebookLM):加来源 → 填骨架提示词 → 生成 → 等卡片 → 下载 PDF。

设计见 README §2。关键教训(实测):
- **0 来源提交会被静默丢弃**(弹框照常关闭但不生成),必须先有 ≥1 个来源
- 来源=LLM 基于 outline 生成的资料文章(content.py ②前置步骤),经「添加来源→复制的文字」粘贴
- 演示文稿弹框内显示"来源 N 个",提交前自检 N=0 拒绝生成
- 产物:Studio 卡片出现"正在生成演示文稿…"→完成后卡片就位 → 卡片查看器 ⋮ → 下载 PDF

用法:python studio/nb_auto.py [--explore]
退出码:0=slides.pdf 已就位;2=服务不可用/环境问题(日志见 nb_status.log)
"""
import json
import subprocess
import sys
import time
from pathlib import Path

STUDIO = Path(__file__).resolve().parent
import avutils
CFG = avutils.load_config()   # 支持 // 注释
NB = CFG["nb"]
WORK = STUDIO / CFG["paths"]["work"]
LOG = WORK / "nb_status.log"
PROMPT = WORK / "nb_prompt.txt"
SRC_TEXT = WORK / "source_text.txt"


def log(msg: str):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def abort(reason: str, code: int = 2):
    log(f"[终止] {reason}")
    sys.exit(code)


def open_page():
    """复用 CDP 实例(若配置),否则用专用 profile 起浏览器,返回 (pw, browser, page)。"""
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    cdp = NB.get("cdp_port")
    if cdp:
        try:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp}")
            ctx = browser.contexts[0]
            return pw, browser, ctx.new_page()
        except Exception as e:
            log(f"[cdp] 连接 {cdp} 失败({e}),改用 profile 启动")
    browser = pw.chromium.launch_persistent_context(
        NB["profile_dir"], executable_path=NB.get("chrome_path"),
        headless=NB.get("headless", False), viewport=NB.get("viewport") or None,
        args=["--lang=zh-CN", f"--remote-debugging-port={NB.get('debug_port', 9333)}"])
    return pw, browser, browser.pages[0] if browser.pages else browser.new_page()


def click_label(page, text: str):
    """自绘 div 单选/按钮:完整鼠标事件序列兜底(先试 Playwright 真实点击)。"""
    loc = page.get_by_text(text, exact=True).last
    try:
        loc.click(timeout=3000)
        return True
    except Exception:
        pass
    return page.evaluate(
        """(label) => {
          const els = [...document.querySelectorAll('span,div')]
            .filter(e => e.childElementCount === 0 && (e.textContent||'').trim() === label);
          if (!els.length) return false;
          const el = els[els.length-1];
          const r = el.getBoundingClientRect();
          const o = {bubbles:true, cancelable:true, clientX:r.x+r.width/2, clientY:r.y+r.height/2};
          for (const t of ['pointerdown','mousedown','pointerup','mouseup','click'])
            el.dispatchEvent(t.startsWith('pointer')
              ? new PointerEvent(t, o) : new MouseEvent(t, o));
          return true;
        }""", text)


def click_tile(page, label: str, scope: str, max_w: int = 400):
    """点卡片磁贴:文字标签本身点不触发,须点其容器中心(真实鼠标)。
    scope 以 "tag:" 开头时按祖先标签名匹配(如 tag:mat-radio-button),否则按文字匹配。"""
    box = page.evaluate(
        """([label, scope, maxW]) => {
          const byTag = scope.startsWith('tag:');
          const leaves = [...document.querySelectorAll('span,div')]
            .filter(e => e.childElementCount === 0 && (e.textContent||'').trim() === label);
          for (const el of leaves.reverse()) {
            let a = el.parentElement;
            while (a && a !== document.body) {
              if (byTag ? a.tagName.toLowerCase() === scope.slice(4)
                        : (a.textContent||'').includes(scope)) {
                const r = a.getBoundingClientRect();
                if (r.width > 100 && r.height > 40 && r.width < maxW)
                  return {x: r.x + r.width/2, y: r.y + r.height/2};
              }
              a = a.parentElement;
            }
          }
          return null;
        }""", [label, scope, max_w])
    if not box:
        return False
    page.mouse.click(box["x"], box["y"])
    return True


def click_in_panel(page, label: str, scope: str):
    """在包含 scope 文字的祖先容器内点击 label(避免点到来源/搜索区的同名入口)。"""
    # 先试 Playwright 真实点击(限定在 scope 容器内)
    try:
        loc = page.locator(f"text=\"{label}\"").last
        # 真实点击前校验其祖先含 scope,否则跳过走 JS
        ok = page.evaluate(
            """([label, scope]) => {
              const leaves = [...document.querySelectorAll('span,div')]
                .filter(e => e.childElementCount === 0 && (e.textContent||'').trim() === label);
              for (const el of leaves.reverse()) {
                let a = el.parentElement;
                while (a && a !== document.body) {
                  if ((a.textContent||'').includes(scope)) return true;
                  a = a.parentElement;
                }
              }
              return false;
            }""", [label, scope])
        if ok:
            loc.click(timeout=3000)
            return True
    except Exception:
        pass
    return page.evaluate(
        """([label, scope]) => {
          const leaves = [...document.querySelectorAll('span,div')]
            .filter(e => e.childElementCount === 0 && (e.textContent||'').trim() === label);
          for (const el of leaves.reverse()) {
            let a = el.parentElement;
            while (a && a !== document.body) {
              if ((a.textContent||'').includes(scope)) {
                const r = el.getBoundingClientRect();
                const o = {bubbles:true, cancelable:true, clientX:r.x+r.width/2, clientY:r.y+r.height/2};
                for (const t of ['pointerdown','mousedown','pointerup','mouseup','click'])
                  el.dispatchEvent(t.startsWith('pointer')
                    ? new PointerEvent(t, o) : new MouseEvent(t, o));
                return true;
              }
              a = a.parentElement;
            }
          }
          return false;
        }""", [label, scope])


def in_dialog(page) -> bool:
    """deck 表单是否开着:认「立即生成/稍后生成」按钮(表单可能无 textarea)。"""
    return page.evaluate(
        """() => [...document.querySelectorAll('button')]
             .some(b => b.offsetParent !== null &&
                  ['立即生成','稍后生成'].some(t => (b.textContent||'').includes(t)))""")


def source_count(page) -> int:
    m = __import__("re").search(r"(\d+)\s*个来源",
                                page.evaluate("() => document.body.innerText"))
    return int(m.group(1)) if m else 0


def add_source(page):
    """添加来源(复制的文字):0 来源提交会被静默丢弃,必须先有 ≥1 个来源。"""
    if source_count(page) > 0:
        log(f"[来源] 已有 {source_count(page)} 个来源,跳过添加")
        return
    if not SRC_TEXT.exists():
        abort(f"缺来源文章 {SRC_TEXT}(content.py 会先生成它)")
    text = SRC_TEXT.read_text(encoding="utf-8").strip()
    page.keyboard.press("Escape")   # 清掉残留弹框/菜单
    page.wait_for_timeout(1000)
    page.locator("button", has_text="添加来源").first.click(timeout=10000)
    page.wait_for_timeout(2000)
    item = page.get_by_text("复制的文字", exact=True).last
    item.click(timeout=10000)
    page.wait_for_selector("textarea", timeout=10000)
    page.wait_for_timeout(800)
    # fill() 会被 Angular 丢弃,必须原生 setter + input 事件
    ok = page.evaluate("""(text) => {
      const ta = document.querySelector('mat-dialog-container textarea');
      if (!ta) return -1;
      const set = Object.getOwnPropertyDescriptor(
        HTMLTextAreaElement.prototype, 'value').set;
      set.call(ta, text);
      ta.dispatchEvent(new Event('input', {bubbles: true}));
      ta.dispatchEvent(new Event('change', {bubbles: true}));
      return ta.value.length;
    }""", text)
    if ok < 0:
        abort("未找到粘贴文字的 textarea")
    page.wait_for_timeout(2000)
    page.locator("button", has_text="插入").first.click(timeout=10000)
    for _ in range(12):  # 最长 60s 等来源计数 ≥1
        page.wait_for_timeout(5000)
        if source_count(page) > 0:
            log(f"[来源] 已插入,当前 {source_count(page)} 个来源")
            return
    abort("来源插入后计数仍为 0")


def wait_deck_done(page):
    """轮询直到演示文稿生成完成(卡片就位)。"""
    timeout = NB.get("card_timeout_sec", 1800)
    poll = NB.get("poll_sec", 60)
    t0 = time.time()
    while time.time() - t0 < timeout:
        txt = page.evaluate("() => document.body.innerText")
        if "将保存在此处" in txt:
            log("[等待] Studio 仍为空,刷新再等")
        elif "正在生成" in txt:
            log(f"[等待] 生成中… {int(time.time()-t0)}s")
        else:
            log(f"[完成] 演示文稿卡片就位,用时 {int(time.time()-t0)}s")
            return
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(8000)
        time.sleep(poll)
    abort(f"等待演示文稿生成超时({timeout}s)")


def download_pdf(page):
    """卡片自身 ⋮ 菜单 → 下载 PDF → 存 assets/slides.pdf(最短路径,无需开查看器)。"""
    dst = STUDIO / CFG["paths"]["slides"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    page.keyboard.press("Escape")   # 关掉可能残留的菜单
    page.wait_for_timeout(1000)
    # Studio 面板内各卡片的 ⋮(x>1400, y>300);取最上面的=最新产物(演示文稿卡)
    boxes = [b.bounding_box() for b in page.locator("button:has-text('more_vert')").all()]
    boxes = [b for b in boxes if b and b["x"] > 1400 and b["y"] > 300]
    if not boxes:
        abort("Studio 面板未找到演示文稿卡片的 ⋮ 菜单")
    box = sorted(boxes, key=lambda b: b["y"])[0]
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(1500)
    item = page.get_by_text("下载 PDF 文档", exact=False).last
    ib = item.bounding_box(timeout=10000)
    with page.expect_download(timeout=180000) as dl:
        page.mouse.click(ib["x"] + ib["width"] / 2, ib["y"] + ib["height"] / 2)
    dl.value.save_as(str(dst))   # 立即落盘,临时文件会被快速清理
    log(f"[产物] {dst} ({dst.stat().st_size} bytes)")


def diag_tile(page, why: str):
    """失败时把磁贴现场写进日志:leaf 数、磁贴盒、点击点被谁挡住、有哪些遮罩。"""
    info = page.evaluate(r"""() => {
      const leaves = [...document.querySelectorAll('span,div')]
        .filter(e => e.childElementCount === 0 && (e.textContent||'').trim() === '演示文稿');
      const leaf = leaves[leaves.length-1];
      const tile = document.querySelector('basic-create-artifact-button');
      const out = {leafCount: leaves.length};
      if (tile) {
        const r = tile.getBoundingClientRect();
        out.tile = {x: Math.round(r.x), y: Math.round(r.y),
                    w: Math.round(r.width), h: Math.round(r.height)};
        const cx = r.x + r.width/2, cy = r.y + r.height/2;
        const at = document.elementFromPoint(cx, cy);
        out.atPoint = at ? (at.tagName + '.' + (at.className||'').toString().slice(0,40)) : 'null';
        out.tileContainsAt = tile.contains(at);
      }
      out.overlays = [...document.querySelectorAll('.cdk-overlay-backdrop, .cdk-overlay-container > *')]
        .map(e => e.className.toString().slice(0, 60)).slice(0, 5);
      const pop = document.querySelector('.cdk-overlay-container');
      if (pop) {
        out.popoverText = (pop.innerText || '').replace(/\s+/g, ' ').slice(0, 200);
        out.popoverButtons = [...pop.querySelectorAll('button')]
          .map(b => (b.textContent || '').trim()).filter(Boolean).slice(0, 10);
      }
      return out;
    }""")
    log(f"[诊断:{why}] {json.dumps(info, ensure_ascii=False)}")


def main():
    # --collect:不新建笔记本,只补收之前「稍后生成」的产物
    if "--collect" in sys.argv:
        url_file = WORK / "nb_notebook_url.txt"
        if not url_file.exists():
            abort("无存档笔记本 URL(nb_notebook_url.txt),无需补收")
        url = url_file.read_text(encoding="utf-8").strip()
        log(f"[补收] {url}")
        pw, browser, page = open_page()
        try:
            page.goto(url, wait_until="domcontentloaded",
                      timeout=NB.get("nav_timeout_sec", 30) * 1000)
            page.wait_for_timeout(4000)
            wait_deck_done(page)
            download_pdf(page)
            log("[完成] slides.pdf 已就位")
        finally:
            pw.stop()
        return

    if not PROMPT.exists():
        abort(f"缺提示词 {PROMPT}(先跑 content 步骤)")
    prompt = PROMPT.read_text(encoding="utf-8").strip()
    log(f"[开始] prompt={len(prompt)} 字符, profile={NB['profile_dir']}")

    pw, browser, page = open_page()
    try:
        page.goto("https://notebook.google.com/", wait_until="domcontentloaded",
                  timeout=NB.get("nav_timeout_sec", 30) * 1000)
        page.wait_for_timeout(3000)
        if "accounts.google.com" in page.url or "ServiceLogin" in page.url:
            abort(f"登录态失效,请人工在该 profile 登录一次: {page.url}")

        # 1. 新建笔记本
        nb_new = page.get_by_role("button", name="新建笔记本")
        nb_new.click(timeout=10000)
        page.wait_for_url("**/notebook/**", timeout=20000)
        page.wait_for_timeout(4000)
        log(f"[笔记本] {page.url}")

        # 1.5 添加来源(0 来源提交会被静默丢弃);收起弹框后再开演示文稿
        add_source(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(2000)

        # 2. Studio 面板 → 演示文稿(限定在 Studio 面板内点,别点到来源/搜索)
        body_txt = page.evaluate("() => document.body.innerText")
        if "将保存在此处" not in body_txt and "添加音频概览" not in body_txt:
            if not click_in_panel(page, "Studio", "Studio"):
                abort("未找到 Studio 面板入口")
            page.wait_for_timeout(2000)
        # 2. Studio 面板 → 演示文稿磁贴(渲染延迟带重试;每次点击后轮询弹框,不盲点)
        tile = False
        for attempt in range(6):
            if not click_tile(page, "演示文稿", "tag:basic-create-artifact-button"):
                page.wait_for_timeout(3000)   # 磁贴还没渲染出来
                continue
            tile = True
            for _ in range(12):               # 点一次后最多等 12s 弹框出现
                if in_dialog(page):
                    break
                page.wait_for_timeout(1000)
            if in_dialog(page):
                break
            log(f"[warn] 第 {attempt+1} 次点击后弹框未出现")
            diag_tile(page, f"点击第{attempt+1}次未开")
        if not tile:
            diag_tile(page, "磁贴始终未渲染")
            abort("Studio 面板内未找到「演示文稿」磁贴(等待 30s)")
        opened = False
        for _ in range(15):                # 表单可能无 textarea,按按钮判定
            if in_dialog(page):
                opened = True
                break
            page.wait_for_timeout(1000)
        if not opened:
            diag_tile(page, "点击后表单未出现")
            abort("演示文稿表单未打开(诊断见日志)")
        page.wait_for_timeout(1000)

        # 3. 格式:演示用幻灯片(自绘单选,点整个 mat-radio-button 行;未命中保持默认)
        if not click_tile(page, "演示用幻灯片", "tag:mat-radio-button", max_w=800):
            log("[warn] 格式单选未命中,保持默认「详细演示文稿」")

        # 4. 填提示词(容器无关定位;真实键盘注入,防 Angular 丢值)
        #    教训1(2026-10-02):原生 setter 写 DOM value 虽回读有值,但 Angular 模型没绑定,
        #    弹框状态一变值就被清空 —— 提交时其实是空提示词。
        #    教训2:mat-radio-button 内的 radio input 祖先同样含"自定义演示文稿",会误命中,
        #    必须排除单选/复选框内的 input,只认真正的文本框(textarea/contenteditable/文本input)。
        target = page.evaluate(
            """() => {
              const isText = (e) => e.isContentEditable ||
                e.tagName === 'TEXTAREA' ||
                (e.tagName === 'INPUT' && !['radio','checkbox','hidden'].includes(e.type) &&
                 !e.closest('mat-radio-button, mat-checkbox'));
              const fields = [...document.querySelectorAll(
                'textarea, input, [contenteditable="true"]')]
                .filter(e => e.offsetParent !== null && isText(e));
              for (let i = 0; i < fields.length; i++) {
                let a = fields[i].parentElement, near = false;
                while (a && a !== document.body) {
                  const t = a.innerText || '';
                  if (t.includes('自定义演示文稿') ||
                      t.includes('请描述您要创建的演示文稿')) { near = true; break; }
                  a = a.parentElement;
                }
                if (near) return i;
              }
              return -1;
            }""")
        if target < 0:
            diag_tile(page, "未找到提示词输入框")
            abort("未找到提示词输入框(诊断见日志)")
        # 真实鼠标点击其中心聚焦(避开 Playwright click 的遮挡判定),再键盘注入
        box = page.evaluate(
            """(i) => {
              const isText = (e) => e.isContentEditable ||
                e.tagName === 'TEXTAREA' ||
                (e.tagName === 'INPUT' && !['radio','checkbox','hidden'].includes(e.type) &&
                 !e.closest('mat-radio-button, mat-checkbox'));
              const fields = [...document.querySelectorAll(
                'textarea, input, [contenteditable="true"]')]
                .filter(e => e.offsetParent !== null && isText(e));
              const e = fields[i];
              const r = e.getBoundingClientRect();
              return {x: r.x + Math.min(r.width/2, 300), y: r.y + r.height/2};
            }""", target)
        page.mouse.click(box["x"], box["y"])
        page.wait_for_timeout(500)
        page.keyboard.insert_text(prompt)             # CDP 真实输入事件,Angular 必绑定
        page.wait_for_timeout(3000)
        # 延时复核:从 DOM 重读,值还在才算填入成功
        n = page.evaluate(
            """(i) => {
              const isText = (e) => e.isContentEditable ||
                e.tagName === 'TEXTAREA' ||
                (e.tagName === 'INPUT' && !['radio','checkbox','hidden'].includes(e.type) &&
                 !e.closest('mat-radio-button, mat-checkbox'));
              const fields = [...document.querySelectorAll(
                'textarea, input, [contenteditable="true"]')]
                .filter(e => e.offsetParent !== null && isText(e));
              const e = fields[i];
              return e ? (e.value || e.textContent || '').length : -1;
            }""", target)
        if n != len(prompt):
            abort(f"提示词复核失败:DOM 中只有 {n}/{len(prompt)} 字符,Angular 未接住输入")
        log(f"[填词] 输入框实际 {n} 字符(3s 后复核通过)")

        # 5. 提交(可关):config nb.submit=false 时只填词不提交,页面保持打开供人工核对
        if not NB.get("submit", True):
            log(f"[调试] submit=false:已填词 {n} 字符,不提交。页面保持打开,请核对骨架是否在框内;确认后 Ctrl+C 退出")
            while True:
                time.sleep(3600)

        # 5.1 提交:优先「立即生成」;额度尽则按配置走「稍后生成」
        state = page.evaluate(
            """() => {
              const btns = [...document.querySelectorAll('button')]
                .filter(b => b.offsetParent !== null);
              const find = (t) => btns.find(b => (b.textContent||'').includes(t));
              const now = find('立即生成');
              const later = find('稍后生成');
              const box = (b) => { const r = b.getBoundingClientRect();
                return {x:r.x, y:r.y, w:r.width, h:r.height, dis:b.disabled}; };
              const ta = [...document.querySelectorAll('textarea, input, [contenteditable="true"]')]
                .find(e => e.offsetParent !== null);
              return {now: now ? box(now) : null,
                      later: later ? box(later) : null,
                      txt: document.body.innerText.slice(0, 4000)};
            }""")
        if state["now"] and not state["now"]["dis"]:
            pass                                    # 正常路径:立即生成
        elif state["later"]:
            if not NB.get("allow_later_generation", True):
                abort("「立即生成」不可用(疑额度尽),allow_later_generation=false → 终止")
            log("[额度] 立即生成不可用,改走「稍后生成」(几小时内完成)")
        elif state["now"]:
            page.mouse.move(state["now"]["x"] + state["now"]["w"]/2,
                            state["now"]["y"] + state["now"]["h"]/2)
            page.wait_for_timeout(1500)
            tip = page.evaluate(
                """() => {
                  const els = [...document.querySelectorAll(
                    '[role="tooltip"], .cdk-overlay-container span, .cdk-overlay-container div')];
                  return els.map(e => (e.textContent||'').trim()).filter(t => t).join('\\n');
                }""")
            if "目前无法使用" in tip or "恢复" in tip:
                abort("NotebookLM 服务不可用(立即生成禁用,提示:目前无法使用,正在恢复)→ 暂缓生成")
            abort(f"立即生成禁用且提示未知,原文: {tip[:300]!r}")
        else:
            diag_tile(page, "无任何生成按钮")
            abort("表单上既无「立即生成」也无「稍后生成」(诊断见日志)")

        # 6. 点击生成 → 等卡片 → 下载 PDF
        use_later = not state["now"] or state["now"]["dis"]
        box = state["later"] if use_later else state["now"]
        page.mouse.click(box["x"] + box["w"]/2, box["y"] + box["h"]/2)
        page.wait_for_timeout(3000)
        if in_dialog(page):
            log("[warn] 点击后表单仍在,可能提交未生效,需人工检查")
            sys.exit(2)
        if use_later:
            (WORK / "nb_notebook_url.txt").write_text(page.url, encoding="utf-8")
            log("[排队] 已提交「稍后生成」,笔记本 URL 已存档;几小时后用 --collect 补收")
            sys.exit(3)
        log("[提交] 已点击「立即生成」")
        wait_deck_done(page)
        download_pdf(page)
        log("[完成] slides.pdf 已就位")
        # --explore:保持浏览器打开供人工/脚本探查 UI 结构(调试用)
        if "--explore" in sys.argv:
            log(f"[explore] 浏览器保持打开,调试端口 {NB.get('debug_port', 9333)},Ctrl+C 退出")
            while True:
                time.sleep(3600)
    finally:
        if not NB.get("cdp_port") and "--explore" not in sys.argv:
            browser.close()
        pw.stop()


if __name__ == "__main__":
    main()
