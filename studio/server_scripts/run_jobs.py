# -*- coding: utf-8 -*-
"""EMV3-Flash 常驻批量(方案②:不裁剪+GFPGAN)。模型只加载一次,31段循环推理。
阶段1: 全部段落推理(跳过已有 raw)
阶段2: GFPGAN 修复 + 每页拼接(跳过已有)
"""
import os, sys, re, json, glob, subprocess
sys.path.insert(0, "/root/autodl-tmp")
from batch_emv3_v2 import (split_audio, gfp_repair, log, read_wav,
                           BASE, REPO, PAGES, OUT, WORK, IMG, PY, FPS, MAX_FRAMES)

JOBSF = f"{BASE}/emv3_jobs.json"

def _md5(p):
    import hashlib
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

def _invalidate_stale_audio(pid: str, wav: str, pdir: str):
    """音源指纹:某页音频内容变了,该页的切段/推理中间产物/成品全部清掉,
    绝不复用旧音频的口型段(防新旧声音混在同一支片里)。"""
    stamp = f"{pdir}/_audio.md5"
    cur = _md5(wav)
    old = open(stamp).read().strip() if os.path.exists(stamp) else None
    if old == cur:
        return
    removed = []
    for p in ([f"{OUT}/{pid}.mp4"] + glob.glob(f"{pdir}/seg_*.wav")
              + glob.glob(f"{pdir}/run_*") + [f"{pdir}/concat.txt"]
              + glob.glob(f"{pdir}/seg_*_gfp.mp4")):
        if os.path.isdir(p):
            import shutil; shutil.rmtree(p, ignore_errors=True); removed.append(os.path.basename(p))
        elif os.path.exists(p):
            os.remove(p); removed.append(os.path.basename(p))
    os.makedirs(pdir, exist_ok=True)
    with open(stamp, "w") as f:
        f.write(cur + "\n")
    if removed:
        log(f"{pid} 音源已变,清旧口型产物 {len(removed)} 项重做")

def build_jobs():
    jobs, plan = [], []
    # 数据驱动:以 pages/ 里实际存在的 v2_pXX.wav 为准,不写死页数
    pids = sorted(
        re.match(r"v2_(p\d+)\.wav", os.path.basename(p)).group(1)
        for p in glob.glob(f"{PAGES}/v2_p*.wav")
        if re.match(r"v2_(p\d+)\.wav", os.path.basename(p)))
    for pid in pids:
        wav = f"{PAGES}/v2_{pid}.wav"
        if not os.path.exists(wav):
            log(f"{pid} SKIP no wav"); continue
        pdir = f"{WORK}/{pid}"
        _invalidate_stale_audio(pid, wav, pdir)
        segs = split_audio(wav, pdir)
        seg_runs = []
        for si, seg in enumerate(segs):
            sdir = f"{pdir}/run_{si:02d}"
            raw = f"{sdir}/{os.path.splitext(os.path.basename(seg))[0]}_output.mp4"
            if not os.path.exists(raw):
                fr, sw, ch, _ = read_wav(seg)
                dur = wave_open_dur(seg)
                vl = min(MAX_FRAMES, int(round(dur * FPS)) + 2)
                jobs.append(dict(image_path=IMG, audio_path=seg, save_path=sdir, video_length=vl))
            seg_runs.append((si, seg, raw))
        plan.append((pid, seg_runs))
    with open(JOBSF, "w") as f:
        json.dump(jobs, f)
    log(f"jobs to infer: {len(jobs)}")
    return plan

def wave_open_dur(p):
    import wave
    w = wave.open(p); d = w.getnframes() / w.getframerate(); w.close(); return d

def phase1():
    r = subprocess.run([PY, "infer_jobs.py",
                        "--image_path", IMG, "--audio_path", "unused",
                        "--prompt", "A person is speaking.",
                        "--num_inference_steps", "8",
                        "--config_path", "config/config.yaml",
                        "--model_name", f"{BASE}/EchoMimicV3/weights/Wan2.1-Fun-V1.1-1.3B-InP",
                        "--ckpt_idx", "50000",
                        "--transformer_path", f"{BASE}/EchoMimicV3/weights/EchoMimicV3/echomimicv3-flash-pro/diffusion_pytorch_model.safetensors",
                        "--save_path", "/tmp/unused",
                        "--wav2vec_model_dir", f"{BASE}/EchoMimicV3/weights/chinese-wav2vec2-base",
                        "--sampler_name", "Flow_Unipc", "--video_length", "81",
                        "--guidance_scale", "6.0", "--audio_guidance_scale", "3.0",
                        "--audio_scale", "1.0", "--neg_scale", "1.0", "--neg_steps", "0",
                        "--seed", "43", "--enable_teacache", "--teacache_threshold", "0.1",
                        "--num_skip_start_steps", "5", "--riflex_k", "6",
                        "--weight_dtype", "bfloat16", "--sample_size", "768", "768",
                        "--fps", str(FPS)],
                       cwd=REPO, capture_output=True, text=True,
                       env={**os.environ, "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
                            "EMV3_JOBS": JOBSF})
    if r.returncode != 0:
        log(f"PHASE1 FAIL\n{r.stdout[-800:]}\n{r.stderr[-1500:]}")
        return False
    log("phase1 all infer done")
    return True

def phase2(plan):
    import wave
    ok = True
    for pid, seg_runs in plan:
        final = f"{OUT}/{pid}.mp4"
        if os.path.exists(final):
            log(f"{pid} DONE already"); continue
        seg_mp4s = []
        for si, seg, raw in seg_runs:
            seg_out = f"{WORK}/{pid}/seg_{si:02d}_gfp.mp4"
            if not os.path.exists(seg_out):
                if not os.path.exists(raw):
                    log(f"{pid} seg{si} raw missing!"); ok = False; continue
                log(f"{pid} seg{si} gfp...")
                gfp_repair(raw, seg_out)
            seg_mp4s.append(seg_out)
        if len(seg_mp4s) != len(seg_runs):
            log(f"{pid} INCOMPLETE, skip concat"); continue
        lst = f"{WORK}/{pid}/concat.txt"
        with open(lst, "w") as f:
            for s in seg_mp4s: f.write(f"file '{s}'\n")
        r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                            "-c", "copy", final], capture_output=True, text=True)
        log(f"{pid} {'DONE' if r.returncode == 0 else 'CONCAT FAIL ' + r.stderr[-200:]}")
    return ok

if __name__ == "__main__":
    # 单任务模式:EMV3_OPENING_JOB 指向任务 json(开场白)。走与批量完全相同的
    # 切段→推理→gfp→拼接链(phase1 参数是跑通过的,勿另起炉灶)。
    # 开场白音频可达 12s(300帧),远超 EMV3 单段 129 帧上限,必须切段,禁止整条直推
    ovr = os.environ.get("EMV3_OPENING_JOB")
    if ovr:
        j = json.load(open(ovr))[0]
        wav = j["audio_path"]
        pdir = f"{WORK}/opening"
        _invalidate_stale_audio("opening", wav, pdir)
        segs = split_audio(wav, pdir)
        jobs, seg_runs = [], []
        for si, seg in enumerate(segs):
            sdir = f"{pdir}/run_{si:02d}"
            raw = f"{sdir}/{os.path.splitext(os.path.basename(seg))[0]}_output.mp4"
            if not os.path.exists(raw):
                vl = min(MAX_FRAMES, int(round(wave_open_dur(seg) * FPS)) + 2)
                jobs.append(dict(image_path=IMG, audio_path=seg, save_path=sdir, video_length=vl))
            seg_runs.append((si, seg, raw))
        with open(JOBSF, "w") as f:
            json.dump(jobs, f)
        plan = [("opening", seg_runs)]
        log(f"opening mode: {len(segs)} segs, {len(jobs)} jobs to infer")
        ok = phase1()
        if ok:
            phase2(plan)
            log("=== opening done ===")
        else:
            log("=== opening aborted (phase1 fail) ===")
        sys.exit(0 if ok else 1)
    log("=== resident batch start ===")
    plan = build_jobs()
    if phase1():
        phase2(plan)
        log("=== resident batch end ===")
    else:
        log("=== resident batch aborted (phase1 fail) ===")
