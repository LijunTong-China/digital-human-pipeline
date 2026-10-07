# -*- coding: utf-8 -*-
"""音视频通用工具(自包含,只依赖 config.json 与 docker/.env 的 API key)。"""
import json
import os
import re
import subprocess
import time
import wave
from pathlib import Path

import requests
from PIL import Image

STUDIO = Path(__file__).resolve().parent


def load_config() -> dict:
    """读 config.json,支持 // 行注释与 /* */ 块注释(字符串内的 // 不受影响)。"""
    src = (STUDIO / "config.json").read_text(encoding="utf-8")
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == '"':                       # 字符串原样拷贝(跳过转义)
            out.append(c)
            i += 1
            while i < n:
                out.append(src[i])
                if src[i] == "\\":
                    out.append(src[i + 1])
                    i += 2
                    continue
                if src[i] == '"':
                    i += 1
                    break
                i += 1
        elif src.startswith("//", i):      # 行注释
            while i < n and src[i] != "\n":
                i += 1
        elif src.startswith("/*", i):      # 块注释
            i = src.find("*/", i + 2)
            i = n if i < 0 else i + 2
        else:
            out.append(c)
            i += 1
    return json.loads("".join(out))


CFG = load_config()

SESSION = requests.Session()
SESSION.trust_env = False


def load_env() -> dict:
    env = {}
    p = STUDIO.parent / "docker" / ".env"
    for line in p.read_text(encoding="utf-8").splitlines() if p.exists() else []:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = load_env()
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()


def run_ff(args, tag="ffmpeg", cwd=None):
    p = subprocess.run([FF, "-y", "-loglevel", "error"] + args, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", cwd=cwd)
    if p.returncode != 0:
        raise RuntimeError(f"[{tag}] fail: {p.stderr[:1500]}")
    return p


def wav_duration(path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def make_silence(dst, seconds: float, sr: int = 44100) -> str:
    n = int(sr * seconds)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"\x00\x00" * n)
    return str(dst)


def concat_audio(wavs: list, dst: str) -> str:
    lst = Path(dst).with_suffix(".txt")
    lst.write_text("\n".join(f"file '{Path(w).resolve().as_posix()}'" for w in wavs),
                   encoding="utf-8")
    run_ff(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", dst], "aconcat")
    lst.unlink()
    return dst


def split_sentences(text: str) -> list:
    parts = re.split(r"(?<=[。!?;!?,;])\s*", text.strip())
    return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------- LLM(内容生成)

def llm(messages: list, json_mode: bool = False, temperature: float = 0.7,
        max_tokens: int = 8192, timeout: int = 300, retries: int = 2,
        model: str = None) -> str:
    """通用对话补全(读 docker/.env 的 LLM_API_KEY/LLM_BASE_URL/LLM_MODEL)。
    model 可覆盖默认模型(如视觉模型);长文生成时中转站可能读超时/断连,
    自动重试 retries 次。流式接收:边生成边回包,timeout 只管字节间隔,
    整篇生成再慢也不会触发 ReadTimeout。"""
    url = ENV["LLM_BASE_URL"].rstrip("/") + "/chat/completions"
    body = {"model": model or ENV["LLM_MODEL"], "messages": messages,
            "temperature": temperature, "max_tokens": max_tokens, "stream": True}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    for i in range(1, retries + 2):
        try:
            r = SESSION.post(url, json=body, timeout=(30, timeout), stream=True,
                             headers={"Authorization": f"Bearer {ENV['LLM_API_KEY']}"})
            r.raise_for_status()
            parts = []
            for raw in r.iter_lines():
                line = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                choices = json.loads(payload).get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                if delta.get("content"):
                    parts.append(delta["content"])
            return "".join(parts)
        except Exception as e:
            print(f"[llm] 第{i}/{retries + 1}次失败: {type(e).__name__}")
            if i > retries:
                raise
            time.sleep(20 * i)


def strip_think(s: str) -> str:
    return re.sub(r"<think>.*?</think>", "", s, flags=re.S).strip()


def md5_of(path) -> str:
    import hashlib
    h = hashlib.md5()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------- 内容页数(动态)

def voices_pages() -> list:
    """演播稿按空行分页(assets/voices.txt)。"""
    t = (STUDIO / CFG["paths"]["voices"]).read_text(encoding="utf-8")
    return [s.strip() for s in t.split("\n\n") if s.strip()]


def n_pages() -> int:
    """页数:n_pages=auto 时以演播稿分段数为准(README §1)。"""
    np = CFG.get("n_pages")
    if np not in ("auto", None):
        return int(np)
    return len(voices_pages())


def intro_text() -> str:
    """开场白文案:配置固定值或 auto(LLM 生成,产物缓存 work/opening_text.txt)。
    提质三件套(README §3.2):喂演播稿上下文、3 候选自评选优、字数按时长软限反推
    (≈4.5字/秒;上限内+1.2 倍加速余量,天然少触发 atempo)。"""
    cfg = CFG["intro"]
    if cfg["text"] != "auto":
        return cfg["text"]
    cache = STUDIO / CFG["paths"]["work"] / "opening_text.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8").strip()
    topic_file = STUDIO / CFG["paths"]["work"] / "topic.json"
    title = (json.loads(topic_file.read_text(encoding="utf-8")).get("title", "")
             if topic_file.exists() else "")
    pages = voices_pages()
    ctx = f"主题标题:{title}\n" if title else ""
    if pages:
        ctx += f"正片第一页讲解词(开场白要自然引出它):\n{pages[0][:300]}"
    # 字数窗:正常语速 ~4.5字/s;上限 max_sec + 1.2 倍加速余量,落在窗内基本不用加速
    speed_max = float(cfg.get("speed_max", 1.2))
    limit = float(cfg.get("max_sec", 12))
    n_min, n_max = int(limit * 4.5 * 0.8), int(limit * 4.5 * speed_max * 0.95)
    sys_p = (
        "你是短视频开场白写手。根据给定主题与正片第一页讲解词,写一句口语化开场白。"
        f"要求:①有钩子(反常识/痛点/悬念),直接切入,不问候不客套;②口语化短句;"
        f"③总字数严格控制在 {n_min}~{n_max} 字(正常语速朗读 {limit:.0f} 秒左右);"
        "④结尾自然衔接第一页内容。只输出开场白正文,一行。")
    cands = []
    for _ in range(3):   # 3 候选,温度拉满保多样性
        raw = llm([{"role": "system", "content": sys_p},
                   {"role": "user", "content": ctx}], temperature=0.9)
        t = strip_think(raw).splitlines()[0].strip()
        if t and n_min - 10 <= len(t) <= n_max + 15:
            cands.append(t)
    if not cands:   # 全部出窗也不空转:退回最接近窗的一条
        cands = [strip_think(raw).splitlines()[0].strip()]
    if len(cands) > 1:   # 自评选优:钩子强度/口语度/与第一页衔接
        raw = llm([
            {"role": "system", "content":
                "你是短视频开场白评审。从候选中选出最好的一条:"
                "钩子最抓人、最口语、与第一页衔接最自然。只输出该条原文,一行。"},
            {"role": "user", "content":
                "第一页讲解词:\n" + (pages[0][:200] if pages else "") +
                "\n\n候选:\n" + "\n".join(f"{i+1}. {c}" for i, c in enumerate(cands))},
        ], temperature=0.2)
        best = strip_think(raw).splitlines()[0].strip()
        text = next((c for c in cands if c == best or best in c), cands[0])
    else:
        text = cands[0]
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return text


def tts(text: str, dst: str, voice: str) -> str:
    """SiliconFlow CosyVoice2 合成,返回 wav 路径。"""
    url = ENV["ASR_BASE_URL"].rstrip("/") + "/audio/speech"
    r = SESSION.post(url, timeout=120,
                     headers={"Authorization": f"Bearer {ENV['ASR_API_KEY']}"},
                     json={"model": CFG["tts_api"]["model"], "input": text,
                           "voice": voice, "response_format": "mp3", "speed": 1.0})
    if r.status_code != 200:
        raise RuntimeError(f"TTS {r.status_code}: {r.text[:300]}")
    mp3 = str(Path(dst).with_suffix(".mp3"))
    Path(mp3).write_bytes(r.content)
    run_ff(["-i", mp3, "-vn", "-ac", "1", "-ar", "44100", "-acodec", "pcm_s16le",
            str(dst)], "tts2wav")
    os.remove(mp3)
    return str(dst)


def clone_voice_id() -> str:
    """注册参考音为克隆音色,voice id 缓存到工作目录。
    缓存带参考音指纹:voice_ref.wav 一换,旧音色 id 作废重新注册。"""
    import hashlib
    vid_file = Path(CFG["paths"]["work"]) / "clone_voice_id.txt"
    fp_file = Path(CFG["paths"]["work"]) / "clone_voice_id.md5"
    ref = Path(CFG["paths"]["voice_ref"])
    fp = hashlib.md5(ref.read_bytes()).hexdigest() if ref.exists() else ""
    if vid_file.exists() and not (fp_file.exists() and
                                  fp_file.read_text(encoding="utf-8").strip() == fp):
        vid_file.unlink()
    if vid_file.exists():
        return vid_file.read_text(encoding="utf-8").strip()
    url = ENV["ASR_BASE_URL"].rstrip("/") + "/uploads/audio/voice"
    import base64
    b64 = base64.b64encode(Path(CFG["paths"]["voice_ref"]).read_bytes()).decode()
    r = SESSION.post(url, timeout=120,
                     headers={"Authorization": f"Bearer {ENV['ASR_API_KEY']}"},
                     json={"model": CFG["tts_api"]["model"], "customName": "my_voice",
                           "audio": f"data:audio/wav;base64,{b64}"})
    if r.status_code != 200:
        raise RuntimeError(f"clone {r.status_code}: {r.text[:300]}")
    vid = r.json().get("uri") or r.json().get("voice")
    Path(vid_file).write_text(vid, encoding="utf-8")
    fp_file.write_text(fp + "\n", encoding="utf-8")
    return vid


def _ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(segments: list, dst: str) -> str:
    lines = []
    for i, s in enumerate(segments, 1):
        lines += [str(i), f"{_ts(s['start'])} --> {_ts(s['end'])}", s["text"], ""]
    Path(dst).write_text("\n".join(lines), encoding="utf-8")
    return dst


def mux(video: str, audio: str, dst: str, srt: str = None) -> str:
    sub_cfg = CFG["subtitle"]
    cwd = None
    vf = None
    if srt:
        srt = Path(srt).resolve()
        cwd = str(srt.parent)
        vf = (f"subtitles={srt.name}:force_style='FontName={sub_cfg['font']},"
              f"FontSize={sub_cfg['font_size']},Outline=1,MarginV={sub_cfg['margin_v']}'")
    args = ["-i", str(Path(video).resolve()), "-i", str(Path(audio).resolve())]
    if vf:
        args += ["-vf", vf]
    args += ["-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "20",
             "-preset", "fast", "-c:a", "aac", "-b:a", "160k", "-shortest",
             "-pix_fmt", "yuv420p", str(Path(dst).resolve())]
    run_ff(args, "mux", cwd=cwd)
    return dst


def media_duration(path) -> float:
    p = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", p.stderr)
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)
