# -*- coding: utf-8 -*-
"""EMV3-Flash 批量口型生成(定版方案②:不裁剪全图 + GFPGAN 逐帧修复)
输入: /root/autodl-tmp/pages/v2_pXX.wav (9页)
输出: /root/autodl-tmp/lipsync_out/pXX.mp4
断点续跑: 已存在的段/页产物自动跳过
"""
import os, sys, wave, subprocess, glob
import numpy as np

BASE = "/root/autodl-tmp"
REPO = f"{BASE}/EchoMimicV3/repo"
PAGES = f"{BASE}/pages"
OUT = f"{BASE}/lipsync_out"
WORK = f"{BASE}/emv3_batch"
IMG = f"{BASE}/EchoMimicV3/input_xingxiang.png"   # 方案②:不裁剪全图
PY = "/root/miniconda3/envs/emv3/bin/python"
GFP_MODEL = "/root/.cache/torch/hub/checkpoints/GFPGANv1.4.pth"
SEG_MAX = 5.0      # 每段最长秒数(129帧红线)
FPS = 25
MAX_FRAMES = 129

os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

def log(msg):
    line = f"[{__import__('time').strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(f"{BASE}/emv3_batch_status.log", "a") as f:
        f.write(line + "\n")

def read_wav(path):
    w = wave.open(path, "rb")
    fr, n, sw, ch = w.getframerate(), w.getnframes(), w.getsampwidth(), w.getnchannels()
    data = w.readframes(n); w.close()
    return fr, sw, ch, data

def split_audio(path, outdir):
    """按静音点切 ≤SEG_MAX 的段"""
    fr, sw, ch, data = read_wav(path)
    os.makedirs(outdir, exist_ok=True)
    x = np.frombuffer(data, dtype=np.int16)
    if ch > 1: x = x[::ch]
    total = len(x) / fr
    segs = []
    pos = 0.0
    i = 0
    while pos < total - 0.05:
        target = min(pos + SEG_MAX, total)
        if target < total - 0.3:  # 在目标附近±0.6s找最低能量点切
            lo, hi = max(pos + 1.0, target - 0.6), target + 0.6
            idx0, idx1 = int(lo * fr), min(int(hi * fr), len(x))
            if idx1 > idx0 + fr:
                wlen = int(0.05 * fr)
                rms = [float(np.sqrt(np.mean(x[j:j+wlen].astype(np.float64)**2)) + 1e-9)
                       for j in range(idx0, idx1 - wlen, wlen)]
                cut = idx0 + int(np.argmin(rms)) * wlen + wlen
                tcut = cut / fr
            else:
                tcut = target
        else:
            tcut = target
        segp = os.path.join(outdir, f"seg_{i:02d}.wav")
        if not os.path.exists(segp):
            a, b = int(pos * fr) * ch, int(tcut * fr) * ch
            sw2 = wave.open(segp, "wb"); sw2.setnchannels(ch); sw2.setsampwidth(sw); sw2.setframerate(fr)
            sw2.writeframes(data[a*sw:b*sw] if False else data[int(pos*fr)*ch*sw:int(tcut*fr)*ch*sw]); sw2.close()
        segs.append(segp)
        pos = tcut; i += 1
    return segs

def gfp_repair(in_mp4, out_mp4):
    """GFPGAN 逐帧人脸修复,音频原样拷回"""
    import cv2, torch
    from gfpgan import GFPGANer
    cap = cv2.VideoCapture(in_mp4)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    restorer = GFPGANer(model_path=GFP_MODEL, upscale=1, arch="clean",
                        channel_multiplier=2, bg_upsampler=None)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    k = 0
    while True:
        ok, frame = cap.read()
        if not ok: break
        try:
            _, _, restored = restorer.enhance(frame[:, :, ::-1], has_aligned=False,
                                              only_center_face=False, paste_back=True)
            vw.write(restored[:, :, ::-1])
        except Exception as e:
            log(f"  gfp frame {k} fail({e}), keep raw")
            vw.write(frame)
        k += 1
        if k % 50 == 0: log(f"  gfp {k}/{n}")
    cap.release(); vw.release()
    # 音频拷回
    tmp = out_mp4 + ".a.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", out_mp4, "-i", in_mp4, "-map", "0:v", "-map", "1:a?",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-shortest", tmp], capture_output=True)
    os.replace(tmp, out_mp4)

def process_page(pid):
    wav = f"{PAGES}/v2_{pid}.wav"
    if not os.path.exists(wav):
        log(f"{pid} SKIP no wav"); return False
    final = f"{OUT}/{pid}.mp4"
    if os.path.exists(final):
        log(f"{pid} DONE already"); return True
    pdir = f"{WORK}/{pid}"
    os.makedirs(pdir, exist_ok=True)
    segs = split_audio(wav, pdir)
    log(f"{pid} {len(segs)} segments")
    seg_mp4s = []
    for si, seg in enumerate(segs):
        seg_out = f"{pdir}/seg_{si:02d}_gfp.mp4"
        if os.path.exists(seg_out):
            seg_mp4s.append(seg_out); log(f"  seg{si} exists"); continue
        fr, sw, ch, _ = read_wav(seg)
        dur = wave.open(seg).getnframes() / fr
        vl = min(MAX_FRAMES, int(round(dur * FPS)) + 2)
        sdir = f"{pdir}/run_{si:02d}"
        os.makedirs(sdir, exist_ok=True)
        log(f"  seg{si} dur={dur:.1f}s vl={vl} infer...")
        cmd = [PY, "infer_flash.py",
               "--image_path", IMG, "--audio_path", seg,
               "--prompt", "A person is speaking.",
               "--num_inference_steps", "8",
               "--config_path", "config/config.yaml",
               "--model_name", f"{BASE}/EchoMimicV3/weights/Wan2.1-Fun-V1.1-1.3B-InP",
               "--ckpt_idx", "50000",
               "--transformer_path", f"{BASE}/EchoMimicV3/weights/EchoMimicV3/echomimicv3-flash-pro/diffusion_pytorch_model.safetensors",
               "--save_path", sdir,
               "--wav2vec_model_dir", f"{BASE}/EchoMimicV3/weights/chinese-wav2vec2-base",
               "--sampler_name", "Flow_Unipc", "--video_length", str(vl),
               "--guidance_scale", "6.0", "--audio_guidance_scale", "3.0",
               "--audio_scale", "1.0", "--neg_scale", "1.0", "--neg_steps", "0",
               "--seed", "43", "--enable_teacache", "--teacache_threshold", "0.1",
               "--num_skip_start_steps", "5", "--riflex_k", "6",
               "--weight_dtype", "bfloat16", "--sample_size", "768", "768",
               "--fps", str(FPS)]
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                           env={**os.environ, "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
        if r.returncode != 0:
            log(f"  seg{si} INFER FAIL\n{r.stdout[-500:]}\n{r.stderr[-800:]}"); return False
        raw = glob.glob(f"{sdir}/*_output.mp4")
        if not raw:
            log(f"  seg{si} no output"); return False
        log(f"  seg{si} infer ok, gfp...")
        gfp_repair(raw[0], seg_out)
        seg_mp4s.append(seg_out)
    # 拼接
    lst = f"{pdir}/concat.txt"
    with open(lst, "w") as f:
        for s in seg_mp4s: f.write(f"file '{s}'\n")
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c", "copy", final], capture_output=True, text=True)
    if r.returncode != 0:
        log(f"{pid} concat fail {r.stderr[-300:]}"); return False
    log(f"{pid} DONE -> {final}")
    return True

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    pids = [only] if only else [f"p{i:02d}" for i in range(9)]
    log(f"=== batch start {pids} ===")
    for pid in pids:
        process_page(pid)
    log("=== batch end ===")
