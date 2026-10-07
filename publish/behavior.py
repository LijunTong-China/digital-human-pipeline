# -*- coding: utf-8 -*-
"""L2 行为层:拟人行为库(逐字输入/贝塞尔鼠标/随机滚动/停顿)。

铁律(README §5.2):
- 不用 fill()/一次灌入,不用瞬间 click()
- 所有关键点击前鼠标先拟人移动到位,hover 短暂停留再点
- 打字 50~150ms/字,段落间停 0.5~2s
"""
import math
import random
import time

from common import log


def nap(a: float, b: float):
    time.sleep(random.uniform(a, b))


def move_mouse(page, x: float, y: float, steps: int | None = None):
    """贝塞尔小抖动轨迹移动鼠标(比直线 move 更像人手)。"""
    # 起点取当前视口内随机一点近似"手当前位置"(Playwright 拿不到真实光标位)
    sx, sy = random.uniform(100, 500), random.uniform(100, 400)
    steps = steps or random.randint(18, 32)
    cx, cy = (sx + x) / 2 + random.uniform(-80, 80), (sy + y) / 2 + random.uniform(-60, 60)
    for i in range(1, steps + 1):
        t = i / steps
        bx = (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t ** 2 * x
        by = (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t ** 2 * y
        page.mouse.move(bx + random.uniform(-1.5, 1.5), by + random.uniform(-1.5, 1.5))
        time.sleep(random.uniform(0.005, 0.02))
    page.mouse.move(x, y)


def human_click(page, x: float, y: float):
    """关键点击:拟人移动 → hover 停留 → 按下/抬起间随机间隙。"""
    move_mouse(page, x, y)
    nap(0.15, 0.6)                       # hover 停留
    page.mouse.down()
    time.sleep(random.uniform(0.04, 0.12))
    page.mouse.up()
    nap(0.3, 1.0)


def click_box(page, box: dict):
    """点一个 bounding_box,中心带随机偏移(人不会总点正中心)。"""
    ox = box["x"] + box["width"] * random.uniform(0.35, 0.65)
    oy = box["y"] + box["height"] * random.uniform(0.35, 0.65)
    human_click(page, ox, oy)


def type_human(page, text: str):
    """逐字符输入:50~150ms/字,标点后 0.3~0.8s,段落间 0.5~2s。"""
    for ch in text:
        page.keyboard.type(ch)
        if ch == "\n":
            time.sleep(random.uniform(0.5, 2.0))
        elif ch in "。,、;:?!,;:?!" :
            time.sleep(random.uniform(0.3, 0.8))
        else:
            time.sleep(random.uniform(0.05, 0.15))


def scroll_randomly(page, n: int | None = None):
    """随机滚动 2~4 次、幅度随机、带停顿(浏览痕迹)。"""
    for _ in range(n or random.randint(2, 4)):
        page.mouse.wheel(0, random.randint(180, 700))
        nap(0.6, 2.2)
        if random.random() < 0.3:        # 偶尔回滚一点
            page.mouse.wheel(0, -random.randint(80, 250))
            nap(0.4, 1.2)


def dwell(page, lo: float = 3.0, hi: float = 10.0):
    """随机停留并伴随轻滚动(进入页面后的浏览行为)。"""
    scroll_randomly(page, n=1)
    nap(lo, hi)


def busy_wait(page, sec: float, activity: bool = True):
    """等待期间不闲着:随机滚动/切停顿,不留'上传完成即秒点'的机械时序。"""
    t0 = time.time()
    while time.time() - t0 < sec:
        if activity and random.random() < 0.5:
            scroll_randomly(page, n=1)
        nap(3.0, 8.0)


def move_to_element(page, loc):
    """locator → 拟人点击(中心随机偏移)。"""
    box = loc.bounding_box(timeout=10000)
    if not box:
        raise RuntimeError("元素无 bounding_box(不可见?)")
    click_box(page, box)
    return box
