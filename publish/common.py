# -*- coding: utf-8 -*-
"""发布模块公共层:配置/日志/熔断器/发布记录/幂等/时间窗/素材校验。

设计见 publish/README.md(五层防风控体系 §5)。本模块只做本地判断,不碰浏览器。
"""
import hashlib
import json
import random
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

PUBLISH = Path(__file__).resolve().parent
if str(PUBLISH) not in sys.path:
    sys.path.insert(0, str(PUBLISH))
# studio 放到队尾:publish/content.py 不能被 studio/content.py 遮蔽
_STUDIO = str(PUBLISH.parent / "studio")
if _STUDIO not in sys.path:
    sys.path.append(_STUDIO)
import avutils as U  # noqa: E402  复用 load_config/load_env/llm

CFG = U.load_config()
PCFG = CFG["publish"]
OUT = PUBLISH / "out"
LOG = OUT / "publish_run.log"
STATE = OUT / "state.json"          # 熔断器状态
VIDEO = PUBLISH.parent / "studio" / CFG["paths"]["final"] / CFG["paths"]["output_name"]
WORK = PUBLISH.parent / "studio" / CFG["paths"]["work"]

RISK_BANNER_WORDS = ["验证码", "异常", "违规", "封禁", "受限", "申诉", "风险"]


def log(msg: str):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    OUT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def abort(reason: str, platform: str = "", code: int = 2):
    log(f"[终止{('/' + platform) if platform else ''}] {reason}")
    sys.exit(code)


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {}


def save_state(st: dict):
    OUT.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- 熔断器(README §5.5) ----------

def breaker_open(platform: str) -> str:
    """熔断中返回原因,未熔断返回空串。"""
    until = load_state().get(platform, {}).get("breaker_until", 0)
    if until > time.time():
        return f"熔断中(至 {datetime.fromtimestamp(until):%m-%d %H:%M}),只许人工介入"
    return ""


def breaker_hit(platform: str):
    """硬信号:连续 N 次失败 → 熔断 N 天(配置 circuit_breaker)。"""
    cb = PCFG.get("circuit_breaker", {"max_fails": 2, "days": 3})
    st = load_state()
    cur = st.setdefault(platform, {"fails": 0, "breaker_until": 0})
    cur["fails"] += 1
    if cur["fails"] >= cb["max_fails"]:
        cur["breaker_until"] = time.time() + cb["days"] * 86400
        cur["fails"] = 0
        log(f"[熔断] {platform} 连续失败达 {cb['max_fails']} 次 → 熔断 {cb['days']} 天")
    save_state(st)


def breaker_clear(platform: str):
    st = load_state()
    if platform in st:
        st[platform]["fails"] = 0
        save_state(st)


# ---------- 发布记录(README §2⑨) ----------

def journal(rec: dict):
    OUT.mkdir(parents=True, exist_ok=True)
    rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with (OUT / "publish_log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def journal_query(platform: str = "", result: str = "", day: str = "") -> list:
    """day 格式 YYYY-MM-DD,不传=全部。"""
    fp = OUT / "publish_log.jsonl"
    if not fp.exists():
        return []
    out = []
    for line in fp.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if platform and r.get("platform") != platform:
            continue
        if result and r.get("result") != result:
            continue
        if day and not r.get("ts", "").startswith(day):
            continue
        out.append(r)
    return out


def md5_of(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def already_published(platform: str, video_md5: str) -> bool:
    """幂等铁律:同 md5 + 同平台已成功 → 拒绝重发(README §2⑨)。"""
    hits = [r for r in journal_query(platform=platform, result="success")
            if r.get("video_md5") == video_md5]
    return bool(hits)


def daily_count(platform: str) -> int:
    return len(journal_query(platform=platform, result="success",
                             day=time.strftime("%Y-%m-%d")))


# ---------- 发布窗口决策(README §2⑤) ----------

def window_decision(platform: str, force: bool = False) -> str:
    """返回 'go' | 'later'。不整点/不固定时间:窗口内随机抖动 ±10 分钟。"""
    if force:
        log(f"[窗口] force=True 跳过时间窗检查({platform})")
        return "go"
    if daily_count(platform) >= PCFG.get("daily_limit", 1):
        log(f"[限频] {platform} 今日已达 daily_limit={PCFG.get('daily_limit', 1)},跳过")
        return "later"
    windows = PCFG.get("time_windows", [["10:30", "11:40"], ["19:10", "21:30"]])
    jitter = PCFG.get("window_jitter_min", 10)
    now = datetime.now()
    today = now.date()
    for a, b in windows:
        ha, ma = map(int, a.split(":"))
        hb, mb = map(int, b.split(":"))
        lo = datetime.combine(today, datetime.min.time()) + timedelta(hours=ha, minutes=ma + random.randint(0, jitter))
        hi = datetime.combine(today, datetime.min.time()) + timedelta(hours=hb, minutes=mb - random.randint(0, jitter))
        if lo <= now <= hi:
            return "go"
    log(f"[窗口] {platform} 当前 {now:%H:%M} 不在发布窗口 {windows} 内,顺延(稍后再跑本脚本)")
    return "later"


# ---------- 素材校验(README §2②) ----------

def ffprobe_meta(video: Path) -> dict:
    """用 imageio_ffmpeg 的 ffmpeg -i 从 stderr 解析时长/分辨率(机器上无独立 ffprobe)。"""
    import re
    r = subprocess.run([U.FF, "-i", str(video)], capture_output=True,
                       text=True, errors="replace", timeout=60)
    err = r.stderr or ""
    dur = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", err)
    res = re.search(r", (\d{3,5})x(\d{3,5})[\s,]", err)
    if not dur:
        return {}
    return {"duration": int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)),
            "width": int(res.group(1)) if res else None,
            "height": int(res.group(2)) if res else None}


def validate_material() -> dict:
    """①素材校验:坏文件/占位文件拒发(gfp 坏文件教训)。返回视频元信息。"""
    if not VIDEO.exists():
        abort(f"成片不存在: {VIDEO}")
    size_mb = VIDEO.stat().st_size / 1e6
    if size_mb < 10:
        abort(f"成片仅 {size_mb:.1f}MB(<10MB,疑坏文件/占位文件),拒发")
    meta = ffprobe_meta(VIDEO)
    if not meta.get("duration"):
        abort("ffprobe 读不到视频时长,文件可能损坏,拒发")
    md5 = md5_of(VIDEO)
    log(f"[素材] {VIDEO.name} {size_mb:.0f}MB {meta['width']}x{meta['height']} "
        f"{meta['duration']:.0f}s md5={md5[:12]}…")
    return {"path": str(VIDEO), "size_mb": round(size_mb, 1), "md5": md5, **meta}


# ---------- 封面截取(README §2④) ----------

def extract_cover(voices_txt: Path) -> Path:
    """取开场白中段一帧(形象满高)。开场白时长≈首页字数/4.5字每秒。"""
    cover = OUT / "cover.jpg"
    half = 3.0
    try:
        text = voices_txt.read_text(encoding="utf-8") if isinstance(voices_txt, Path) else voices_txt
        first_page = text.strip().splitlines()[0]
        half = max(2.0, len(first_page) / 4.5 / 2)
    except Exception as e:
        log(f"[warn] 估算开场白时长失败({e}),用默认 3s 处截取")
    OUT.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [U.FF, "-y", "-v", "error", "-ss", f"{half:.1f}", "-i", str(VIDEO),
         "-frames:v", "1", "-q:v", "2", str(cover)],
        capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not cover.exists() or cover.stat().st_size < 5000:
        abort(f"封面截取失败: {r.stderr[-300:]}")
    log(f"[封面] {cover}({half:.1f}s 处, {cover.stat().st_size // 1024}KB)")
    return cover


def topic_and_voices():
    topic_fp = WORK / "topic.json"
    voices_fp = PUBLISH.parent / "studio" / CFG["paths"]["voices"]
    if not topic_fp.exists():
        abort(f"缺 {topic_fp}(先跑 studio 流程 ①选题)")
    topic = json.loads(topic_fp.read_text(encoding="utf-8"))
    voices = voices_fp.read_text(encoding="utf-8") if voices_fp.exists() else ""
    return topic, voices
