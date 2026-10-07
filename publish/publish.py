# -*- coding: utf-8 -*-
"""发布总控(README §1 九步链):
①账号体检(平台内) → ②素材校验 → ③元信息生成 → ④封面截取 → ⑤发布窗口决策
→ ⑥⑦平台发布 → ⑧结果验证(平台内) → ⑨发布记录落盘(全在本模块汇总)

用法:
  python publish/publish.py            # 全平台(配置 publish.platforms)
  python publish/publish.py douyin     # 单平台
  python publish/publish.py --check    # 只跑 ②③④ 本地校验,不碰浏览器
  python publish/publish.py douyin --explore   # 打开创作中心供人工探查 UI(不发布)
  python publish/publish.py douyin --force     # 跳过时间窗检查(调试)
退出码:0=全部成功 2=失败 3=体检/窗口未过(顺延)
"""
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
from common import (PCFG, log, abort, validate_material, extract_cover,
                    topic_and_voices, breaker_open, breaker_hit, breaker_clear,
                    already_published, journal, window_decision)

PLATFORMS = {"douyin": "platform_douyin", "xhs": "platform_xhs"}


def publish_platform(platform: str, mat: dict, meta: dict, cover, force: bool):
    """单平台子流程:熔断→幂等→窗口→发布→记录。返回 True/False。"""
    rec = {"platform": platform, "video_md5": mat["md5"], "title": meta[platform]["title"]}
    why = breaker_open(platform)
    if why:
        log(f"[跳过] {platform} {why}")
        return False
    if already_published(platform, mat["md5"]):
        log(f"[幂等] {platform} 该视频(md5 {mat['md5'][:12]}…)已发布成功,拒绝重发")
        return False
    if window_decision(platform, force=force) != "go":
        return False
    mod = __import__(PLATFORMS[platform])
    try:
        url = mod.run(Path(mat["path"]), meta, cover, explore=False)
        rec.update(result="success", url=url)
        journal(rec)
        breaker_clear(platform)
        return True
    except Exception as e:
        _mod = sys.modules[PLATFORMS[platform]]
        hard = isinstance(e, _mod.RiskError) if hasattr(e, "__class__") else False
        rec.update(result="fail", error=str(e), hard=hard)
        journal(rec)
        if hard:
            breaker_hit(platform)      # 硬信号才熔断计时
        log(f"[失败] {platform}: {e}\n{traceback.format_exc(limit=3)}")
        return False


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a[2:] for a in sys.argv[1:] if a.startswith("--")}
    platforms = args or PCFG.get("platforms", ["douyin", "xhs"])
    for p in platforms:
        if p not in PLATFORMS:
            abort(f"未知平台 {p}(支持: {list(PLATFORMS)})")

    # ②素材校验
    mat = validate_material()
    # ③元信息生成
    from content import gen_meta, meta_text_ok
    meta = gen_meta(mat["md5"], force="regen" in flags)
    for p in platforms:
        if not meta_text_ok(meta, p):
            abort(f"{p} 元信息自检不通过(标题空/超限),检查 out/ 下 meta 文件")
    # ④封面截取
    _, voices = topic_and_voices()
    cover = extract_cover(voices) if "xhs" in platforms else None

    if "check" in flags:
        log(f"[--check] 本地校验通过:素材/文案/封面就绪。平台={platforms}")
        log(f"[--check] meta 摘要: {json.dumps({k: v for k, v in meta.items() if k != 'video_md5'}, ensure_ascii=False)[:300]}")
        return

    if "explore" in flags:
        p = platforms[0]
        mod = __import__(PLATFORMS[p])
        from browser import open_page, health_check
        pw, browser, page = open_page(p)
        if not health_check(page, p):
            abort("体检未过,请先人工登录该 profile")
        from browser import explore_hold
        explore_hold(page, PCFG[p].get("debug_port", 9334))
        return

    # ⑤~⑨ 各平台独立子流程,互不阻断
    results = {}
    for p in platforms:
        results[p] = publish_platform(p, mat, meta, cover, force="force" in flags)
    log(f"[汇总] {json.dumps(results, ensure_ascii=False)}")
    if not any(results.values()):
        sys.exit(3 if all(v is False for v in results.values()) else 2)


if __name__ == "__main__":
    main()
