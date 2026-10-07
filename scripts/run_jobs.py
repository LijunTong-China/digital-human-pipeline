# -*- coding: utf-8 -*-
"""EMV3-Flash 常驻批量(方案②:不裁剪+GFPGAN)。模型只加载一次,31段循环推理。
阶段1: 全部段落推理(跳过已有 raw)
阶段2: GFPGAN 修复 + 每页拼接(跳过已有)
"""
import os, sys, json, glob, subprocess
sys.path.insert(0, "/root/autodl-tmp")
from batch_emv3_v2 import (split_audio, gfp_repair, log, read_wav,
                           BASE, REPO, PAGES, OUT, WORK, IMG, PY, FPS, MAX_FRAMES)

JOBSF = f"{BASE}/emv3_jobs.json"

def build_jobs():
    jobs, plan = [], []
    for i in range(9):
        pid = f"p{i:02d}"
        wav = f"{PAGES}/v2_{pid}.wav"
        if not os.path.exists(wav):
            log(f"{pid} SKIP no wav"); continue
        pdir = f"{WORK}/{pid}"
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
    log("=== resident batch start ===")
    plan = build_jobs()
    if phase1():
        phase2(plan)
        log("=== resident batch end ===")
    else:
        log("=== resident batch aborted (phase1 fail) ===")
