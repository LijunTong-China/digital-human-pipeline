# -*- coding: utf-8 -*-
"""⑥ 合成(配置驱动): voiceonly / intro / board 三布局 → output/final/<output_name>

设计见 README.md §3/§5。本模块只做合成;音频/口型产物由 pipeline.py 准备。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

import avutils as U

CFG = U.CFG
STUDIO = U.STUDIO
WORK = STUDIO / CFG["paths"]["work"]
FINAL = STUDIO / CFG["paths"]["final"]
ASSETS = STUDIO / CFG["paths"]["assets"]
LIP = WORK / "lipsync"
CANVAS = CFG["canvas"]
W, H = CANVAS["width"], CANVAS["height"]


# ---------------------------------------------------------------- 页音频

def page_audio(i: int, text: str) -> str:
    """第 i 页配音:clone 模式用服务器克隆产物,预置音色本地 TTS。
    带文本指纹:本页稿件文本一变,旧配音自动作废重合成。"""
    import hashlib
    p = CFG["paths"]
    if CFG["voice"] == "clone":
        w = WORK / f"{p['clone_page_prefix']}{i:02d}.wav"
        assert w.exists(), f"缺 {w}(pipeline voice 步骤产出)"
        return str(w)
    w = WORK / f"{p['page_audio_prefix']}{i:02d}.wav"
    stamp = WORK / f"{p['page_audio_prefix']}{i:02d}.md5"
    fp = hashlib.md5((CFG["voice"] + "\n" + text).encode("utf-8")).hexdigest()
    if w.exists() and not (stamp.exists() and
                           stamp.read_text(encoding="utf-8").strip() == fp):
        w.unlink()
        print(f"[audio] p{i:02d} 稿件已变化,旧配音作废重合成")
    if not w.exists():
        U.tts(text, str(w), CFG["tts_api"]["voice_prefix"] + CFG["voice"])
        stamp.write_text(fp + "\n", encoding="utf-8")
    return str(w)


def opening_audio(text: str, limit: float) -> str:
    """开场白配音。limit 是软限:超限最多加速 intro.speed_max(默认 1.2,不硬压到限内,
    12s 是大致时长);再超就接受超时成片。带指纹:文本/音色/时长上限任一变化,旧音频作废。"""
    import hashlib
    w = WORK / "opening.wav"
    fp = hashlib.md5(f"{CFG['voice']}\n{limit}\n{text}".encode("utf-8")).hexdigest()
    stamp = WORK / "_opening.md5"
    if w.exists() and not (stamp.exists() and
                           stamp.read_text(encoding="utf-8").strip() == fp):
        w.unlink()
        print("[opening] 开场白输入已变化,旧音频作废重合成")
    if w.exists():
        return str(w)
    voice = (CFG["tts_api"]["voice_prefix"] + CFG["voice"] if CFG["voice"] != "clone"
             else U.clone_voice_id())
    src = str(WORK / "opening_raw.wav")
    U.tts(text, src, voice)
    d = U.wav_duration(src)
    speed_max = float(CFG["intro"].get("speed_max", 1.2))
    if d > limit:
        speed = min(d / limit * 1.02, speed_max)
        U.run_ff(["-i", src, "-af", f"atempo={speed:.3f}", "-vn",
                  "-acodec", "pcm_s16le", str(w)], "atempo")
        wd = U.wav_duration(w)
        print(f"[opening] {d:.1f}s 超软限 {limit:.0f}s → 加速 x{speed:.2f} = {wd:.1f}s"
              + (f"(超 {wd - limit:.1f}s,软限接受)" if wd > limit else ""))
    else:
        Path(w).write_bytes(Path(src).read_bytes())
    stamp.write_text(fp + "\n", encoding="utf-8")
    return str(w)


# ---------------------------------------------------------------- 字幕

def est_timeline(text: str, t0: float, d: float, timeline: list):
    """演播稿按字数比例铺时间轴(README §5:原文+原版节奏,无 whisper)。"""
    maxc = CFG["subtitle"]["max_chars"]
    chunks = []
    for s in U.split_sentences(text):
        for pt in re.split(r"(?<=[,，、:：])\s*", s):
            pt = pt.strip().rstrip(".,，。、:：;；!！?？…—~·")
            if not pt:
                continue
            while len(pt) > maxc:
                chunks.append(pt[:maxc - 2])
                pt = pt[maxc - 2:]
            chunks.append(pt.rstrip(".,，。、:：;；!！?？…—~·"))
    chars = [max(len(s), 1) for s in chunks]
    st = t0
    for s, c in zip(chunks, chars):
        sd = d * c / sum(chars)
        timeline.append({"text": s, "start": st, "end": st + sd})
        st += sd


# ---------------------------------------------------------------- 版面

def pdf_pages() -> list:
    import hashlib
    import fitz
    pdf = ASSETS / Path(CFG["paths"]["slides"]).name
    doc = fitz.open(pdf)
    pd = WORK / "pages"
    pd.mkdir(parents=True, exist_ok=True)
    # 指纹防旧页图复用:slides.pdf 一变,整目录页图作废重渲染
    fp = hashlib.md5(pdf.read_bytes()).hexdigest()
    stamp = pd / "_slides.md5"
    if stamp.exists() and stamp.read_text(encoding="utf-8").strip() != fp:
        for old in pd.glob("p*.png"):
            old.unlink()
        print("[pages] slides.pdf 已变化,旧页图缓存已清")
    stamp.write_text(fp + "\n", encoding="utf-8")
    pages = []
    for i, page in enumerate(doc):
        png = pd / f"p{i:02d}.png"
        if not png.exists():
            page.get_pixmap(dpi=110).save(png)
        pages.append(str(png))
    doc.close()
    return pages


def slide_prepare(slide_png: str, dst: str) -> Image.Image:
    """幻灯片裁边→统一宽。fit=False(voiceonly 全屏):居中裁切铺满;
    fit=True(board):整页完整放进深色画布,不裁内容。"""
    slide = Image.open(slide_png).convert("RGB")
    px = slide.getpixel((0, 0))
    from PIL import ImageChops
    diff = ImageChops.difference(slide, Image.new("RGB", slide.size, px)).convert("L")
    bbox = diff.point(lambda v: 255 if v > 12 else 0).getbbox()
    if bbox:
        pad = 8
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(slide.width, bbox[2] + pad), min(slide.height, bbox[3] + pad))
        slide = slide.crop(bbox)
    tw = 1200
    th = int(slide.height * tw / slide.width)
    slide = slide.resize((tw, th), Image.LANCZOS)
    if CFG.get("board", {}).get("fit", False):
        # 完整版:整页缩放进画布(左右留边距,底部对齐 slide_bottom),不裁任何内容。
        # 2026-10-07 修复:原实现固定缩放到 1200 宽 > 画布 1080,paste 时 x=-60
        # 把幻灯片左右各裁掉一条(PPT 展示不全的根因)。
        margin = 40
        max_w, max_h = W - margin * 2, CANVAS["slide_bottom"] - margin
        if tw > max_w or th > max_h:      # 超出可展示区:等比缩到放得下
            k = min(max_w / tw, max_h / th)
            tw, th = int(tw * k), int(th * k)
            slide = slide.resize((tw, th), Image.LANCZOS)
        bg = Image.new("RGB", (W, H), (25, 28, 40))
        img = bg.copy()
        img.paste(slide, ((W - tw) // 2, max(0, CANVAS["slide_bottom"] - th)))
        img.save(dst)
        return img
    slide = slide.crop(((tw - W) // 2, 0, (tw - W) // 2 + W, th))
    bg = slide
    bw, bh = bg.size
    if bh < H:
        bg = bg.resize((int(bw * H / bh), H))
        bw = bg.width
    bg = bg.crop(((bw - W) // 2, 0, (bw - W) // 2 + W, H))
    img = bg.copy()
    img.paste(slide, (0, max(0, CANVAS["slide_bottom"] - th)))
    img.save(dst)
    return img


def bg_blur(img: Image.Image) -> Image.Image:
    bg = img.resize((W, int(img.height * W / img.width))) if img.width == W else img
    if bg.height < H:
        bg = bg.resize((int(bg.width * H / bg.height), H))
    return (bg.crop(((bg.width - W) // 2, 0, (bg.width - W) // 2 + W, H))
            .filter(ImageFilter.GaussianBlur(28)).resize((W, H)))


def frame_voiceonly(slide_png: str, dst: str):
    slide_prepare(slide_png, dst)


def frame_intro(lip_mp4: str, dst: str):
    """开场白底图:形象首帧满高居中,模糊背景垫底。"""
    frame = WORK / "_op_frame.png"
    U.run_ff(["-i", lip_mp4, "-frames:v", "1", "-q:v", "3", str(frame)], "opframe")
    img = Image.open(frame).convert("RGB")
    bg = bg_blur(img)
    img = img.resize((int(img.width * H / img.height), H))
    bg.paste(img, ((W - img.width) // 2, 0))
    bg.save(dst)


def _find_coeffs(pa, pb):
    """求透视变换系数:pb(源四角)→pa(目标四角)。"""
    import numpy as np
    A, B = [], []
    for (x, y), (X, Y) in zip(pb, pa):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        B.append(X)
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
        B.append(Y)
    return np.linalg.solve(A, B).tolist()


def frame_board(slide_png: str, dst: str):
    """讲课底图:PPT 占左侧 board.slide_ratio 宽,绕竖轴向内透视旋转
    (左缘贴观众、右缘向纵深退,右缘高度缩为 (1-board.persp) 倍),
    腾出右侧空间给满高形象口播;persp=0 时退回 2D 旋转 board.angle 度。"""
    b = CFG["board"]
    slide = slide_prepare(slide_png, dst).convert("RGB")   # 返回值已是 Image,勿再 open
    bg = bg_blur(slide)
    sw = int(W * b["slide_ratio"])
    sh = int(slide.height * sw / slide.width)
    if sh > H - 80:
        sh = H - 80
        sw = int(slide.width * sh / slide.height)
    s2 = slide.resize((sw, sh), Image.LANCZOS)
    k = float(b.get("persp", 0))
    if k > 0:   # 绕竖轴内转:左缘(远端)缩短并垂直居中 → 右缘朝向观众
        cy = sh * k / 2
        coeffs = _find_coeffs(
            [(0, cy), (sw, 0), (sw, sh), (0, sh - cy)],
            [(0, 0), (sw, 0), (sw, sh), (0, sh)])
        s2 = s2.transform((sw, sh), Image.PERSPECTIVE, coeffs,
                          resample=Image.BICUBIC, fillcolor=(25, 28, 40))
    else:       # 2D 平面旋转(旧行为)
        s2 = s2.rotate(b.get("angle", 0), expand=True, fillcolor=(25, 28, 40))
    # 卡片位置:x = board.slide_left(占屏宽比例),y = board.slide_top(px,缺省垂直居中)
    y = int(b["slide_top"]) if b.get("slide_top") is not None else (H - s2.height) // 2
    bg.paste(s2, (int(W * b.get("slide_left", 0.02)), y))
    bg.save(dst)
    # 记录卡片几何,供 build_seg 让形象与 PPT 并排对齐(同一竖直区间)
    global _board_geo
    _board_geo = dict(y=y, h=s2.height)

_board_geo = dict(y=0, h=H)


# ---------------------------------------------------------------- 分段

def lip_source(lip_mp4: str) -> tuple:
    """口型视频源与键控滤镜:键控类型跟随批次标记(key.txt: white/green),原样=不抠。"""
    mf = LIP / "key.txt"
    if not mf.exists():          # 兼容旧标记文件
        mf = LIP / "use_whitekey"
    kind = mf.read_text(encoding="utf-8").strip() if mf.exists() else ""
    ck = CANVAS.get(kind + "key") if kind else None
    if ck:
        return str(lip_mp4), (f"colorkey={ck.get('color')}:"
                              f"{ck.get('similarity',0.16)}:{ck.get('blend',0.12)},")
    return str(lip_mp4), ""


def build_seg(bg_png: str, lip: str | None, audio: str, dur: float, dst: str,
              right_col: bool = False, full: bool = False):
    inputs = ["-loop", "1", "-i", bg_png]
    if lip:
        src, key = lip_source(lip)
        inputs += ["-i", src]
        if full:        # intro 开场白:形象满高居中出镜(README §3.2)
            fc = (f"[1:v]scale=-2:{H},crop={W}:{H},{key[:-1] if key else 'null'}[ol];"
                  f"[0:v][ol]overlay=0:0[v]")
        elif right_col:   # board:形象站右侧,高度 = PPT卡片高 × board.avatar_scale
            gy, gh = _board_geo.get("y", 0), _board_geo.get("h", H)
            ah = int(gh * float(CFG["board"].get("avatar_scale", 1)))
            ay = gy + (gh - ah) // 2   # 缩小后仍以卡片竖直中心对齐
            fc = (f"[1:v]scale=-2:{ah},{key[:-1] if key else 'null'}[ol];"
                  f"[0:v][ol]overlay=W-w-{CFG['board']['gap_right']}:{ay}[v]")
        else:           # 右下小窗
            fc = (f"[1:v]scale={CANVAS['lip_width']}:-2,"
                  f"{key[:-1] if key else 'null'}[ol];"
                  f"[0:v][ol]overlay=W-w-{CANVAS['lip_margin_r']}:H-h-{CANVAS['lip_margin_b']}:shortest=1[v]")
        aidx = 2
    else:
        fc = "[0:v]null[v]"
        aidx = 1
    inputs += ["-i", audio]
    subprocess.run([U.FF, "-y", "-loglevel", "error"] + inputs +
                   ["-filter_complex", fc, "-map", "[v]", "-map", f"{aidx}:a",
                    "-t", f"{dur:.2f}", "-r", "25", "-c:v", "libx264",
                    "-preset", "fast", "-crf", "20", "-c:a", "aac", "-b:a", "128k",
                    dst], check=True)


# ---------------------------------------------------------------- 主流程

def main():
    layout = CFG["layout"]
    assert layout in ("voiceonly", "intro", "board"), f"未知 layout: {layout}"
    assert CFG["voice"] == "clone" or CFG["voice"] in CFG["tts_api"]["male_voices"], \
        f"未知 voice: {CFG['voice']}"
    FINAL.mkdir(parents=True, exist_ok=True)

    pages = pdf_pages()
    voices = U.voices_pages()
    n = min(U.n_pages(), len(pages), len(voices))
    print(f"[cfg] voice={CFG['voice']} layout={layout} pages={n}")

    timeline, segs, audio_parts, t = [], [], [], 0.0

    if layout == "intro":
        olimit = float(CFG["intro"]["max_sec"])
        otext = U.intro_text()
        owav = opening_audio(otext, olimit)
        od = U.wav_duration(owav)
        op_lip = LIP / "lipsync_opening.mp4"
        assert op_lip.exists(), "缺开场白口型(pipeline opening 步骤产出)"
        est_timeline(otext, t, od, timeline)
        bgf = str(WORK / "fr_opening.png")
        frame_intro(str(op_lip), bgf)
        seg = str(WORK / "seg_opening.mp4")
        build_seg(bgf, str(op_lip), owav, od, seg, full=True)
        segs.append(seg)
        audio_parts += [owav, U.make_silence(WORK / "gap_op.wav", CFG["page_gap"])]
        t += od + CFG["page_gap"]
        print(f"[opening] {od:.1f}s (上限 {olimit}s)")

    for i in range(n):
        wav = page_audio(i, voices[i])
        d = U.wav_duration(wav)
        audio_parts += [wav, U.make_silence(WORK / f"gap_{i:02d}.wav", CFG["page_gap"])]
        est_timeline(voices[i], t, d, timeline)
        t += d + CFG["page_gap"]

        bgf = str(WORK / f"fr_{i:02d}.png")
        {"voiceonly": frame_voiceonly, "board": frame_board}.get(
            layout, frame_voiceonly)(pages[i], bgf)

        seg = str(WORK / f"seg_{i:02d}.mp4")
        if layout == "board":
            lip = LIP / f"{CFG['paths']['lipsync_prefix']}{i:02d}.mp4"
            assert lip.exists(), f"board 模式需要 {lip}"
            build_seg(bgf, str(lip), wav, d + CFG["page_gap"], seg, right_col=True)
        else:
            build_seg(bgf, None, wav, d + CFG["page_gap"], seg)
        segs.append(seg)
        print(f"[page] p{i:02d}: {d:.1f}s ok")

    lst = WORK / "segs.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs), encoding="utf-8")
    visual = str(WORK / "visuals.mp4")
    subprocess.run([U.FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", visual], check=True)
    audio = U.concat_audio(audio_parts, str(WORK / "full_audio.wav"))
    srt = U.build_srt(timeline, str(WORK / "sub.srt"))
    out = U.mux(visual, audio, str(FINAL / CFG["paths"]["output_name"]), srt)
    print(f"\n=== 完成(voice={CFG['voice']} layout={layout})===\n"
          f"{out}\n时长 {U.media_duration(out):.1f}s | "
          f"大小 {Path(out).stat().st_size / 1048576:.1f} MB")


if __name__ == "__main__":
    main()
