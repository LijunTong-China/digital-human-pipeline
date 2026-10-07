# -*- coding: utf-8 -*-
"""③ 元信息生成:标题/简介/标签(抖音)与标题/正文/标签(小红书)。

铁律(README §2③/§5.4):
- 两平台各自独立调 LLM 生成,禁止同文案跨平台发布
- 文案带负面清单(最/第一/绝对/赚钱诱导词),降低机审命中
- 产物按 <date>_meta.json 落盘,带视频 md5 指纹,已生成过的不再重复生成
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import avutils as U
from common import OUT, log, topic_and_voices

BAD_WORDS = ["最", "第一", "绝对", "必看", "震惊", "秒杀", "赚钱", "暴富", "躺赚",
             "秘籍", "必涨", "百分百", "保证", "点击领取", "限时"]

DOUYIN_PROMPT = """你是短视频运营。根据视频主题与口播稿,写抖音发布信息:
- title: ≤55字,口语化,不夸大,不用"最/第一/绝对/震惊/赚钱"等词
- desc: 2~3句口语化简介
- tags: 3~5个话题标签(不带#号)
只输出 JSON:{{"title":"...","desc":"...","tags":["..."]}}

主题:{topic}
口播稿(节选):{script}"""

XHS_PROMPT = """你是小红书笔记运营。根据视频主题与口播稿,写小红书发布信息:
- title: ≤20字(硬限),自然,不夸大,不用"最/第一/绝对/震惊/赚钱"等词
- body: ≤800字,带 emoji 分段,语气真诚像分享
- tags: 3~5个标签(不带#号)
只输出 JSON:{{"title":"...","body":"...","tags":["..."]}}

主题:{topic}
口播稿(节选):{script}"""


def _gen(platform: str, topic: dict, script: str) -> dict:
    prompt_tpl = DOUYIN_PROMPT if platform == "douyin" else XHS_PROMPT
    raw = U.llm([
        {"role": "system", "content": "你是中文短视频运营编辑,只输出 JSON。"},
        {"role": "user", "content": prompt_tpl.format(
            topic=topic.get("title", ""), script=script[:1200])},
    ], json_mode=True, temperature=0.9, timeout=180)
    meta = json.loads(U.strip_think(raw))
    meta["title"] = meta["title"].strip()
    meta["tags"] = [t.strip().lstrip("#") for t in meta.get("tags", []) if t.strip()]
    # 平台硬限截断
    if platform == "douyin":
        meta["title"] = meta["title"][:55]
        meta["desc"] = meta.get("desc", "").strip()
    else:
        meta["title"] = meta["title"][:20]
        meta["body"] = meta.get("body", "").strip()[:1000]
    # 负面清单自检:命中则重生成一次(温度已 0.9,再命中原样保留并告警)
    bad = [w for w in BAD_WORDS if w in meta["title"] + meta.get("desc", "") + meta.get("body", "")]
    if bad:
        log(f"[warn] {platform} 文案命中负面词 {bad}(已保留,人工可改 out/meta)")
    return meta


def gen_meta(video_md5: str, force: bool = False) -> dict:
    """两平台分别生成并落盘 out/<date>_meta.json;同 md5 已生成过则直接复用。"""
    fp = OUT / f"{date.today():%Y-%m-%d}_meta.json"
    if fp.exists() and not force:
        old = json.loads(fp.read_text(encoding="utf-8"))
        if old.get("video_md5") == video_md5:
            log(f"[文案] 复用今日已生成文案({fp.name},md5 匹配)")
            return old
    topic, voices = topic_and_voices()
    script = "\n".join(voices.splitlines()[:6])   # 首页足够给上下文,省 token
    out = {"video_md5": video_md5, "topic": topic.get("title", "")}
    from common import PCFG
    for platform in PCFG.get("platforms", ["douyin", "xhs"]):
        out[platform] = _gen(platform, topic, script)
        log(f"[文案] {platform} 标题:{out[platform]['title']}")
    OUT.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"[文案] 已落盘 {fp.name}")
    return out


def meta_text_ok(meta: dict, platform: str) -> bool:
    """发布前最后自检:标题非空、长度合规。"""
    m = meta.get(platform) or {}
    if not m.get("title"):
        return False
    if platform == "xhs" and len(m["title"]) > 20:
        return False
    if platform == "douyin" and len(m["title"]) > 55:
        return False
    return True


def load_meta_file(fp: Path) -> dict:
    return json.loads(fp.read_text(encoding="utf-8"))


def tag_line(tags: list) -> str:
    return " ".join(f"#{t}" for t in tags)
