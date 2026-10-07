# -*- coding: utf-8 -*-
"""④ 克隆音色逐页合成(数据驱动,由 pipeline 自动上传,勿在服务器手改)。

输入(均在 /root/autodl-tmp/pages/):
  voices.txt        演播稿,空行分页(pipeline ④ 每次上传新稿)
  voice_ref.wav     克隆参考音频
  ref_prompt.txt    参考音频的转写文本(zero_shot 第二参数,pipeline 上传)
输出:pages/v2_pXX.wav(每页一条;已存在且不早于 voices.txt 则跳过,断点续跑)
用法:clone_python clone_pages.py [可选:根目录,默认 /root/autodl-tmp]
"""
import os
import sys
import time

import torchaudio

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/root/autodl-tmp"
PAGES = os.path.join(ROOT, "pages")
VOICES = os.path.join(PAGES, "voices.txt")
REF = os.path.join(PAGES, "voice_ref.wav")
REF_PROMPT = os.path.join(PAGES, "ref_prompt.txt")
COSY = os.path.join(ROOT, "CosyVoice")
MODEL = os.path.join(ROOT, "CosyVoice2-0.5B")

sys.path.append(os.path.join(COSY, "third_party", "Matcha-TTS"))
sys.path.append(COSY)
from cosyvoice.cli.cosyvoice import CosyVoice2   # noqa: E402

pages = [p.strip() for p in open(VOICES, encoding="utf-8").read().split("\n\n") if p.strip()]
prompt_text = open(REF_PROMPT, encoding="utf-8").read().strip()
print(f"[clone] 共 {len(pages)} 页,参考音 {REF}")

cv = CosyVoice2(MODEL, load_jit=False, load_trt=False, fp16=False)
stamp = os.path.getmtime(VOICES)
for i, text in enumerate(pages):
    dst = os.path.join(PAGES, f"v2_p{i:02d}.wav")
    if os.path.exists(dst) and os.path.getmtime(dst) >= stamp:
        print(f"[clone] p{i:02d} 已有,跳过")
        continue
    t0 = time.time()
    for out in cv.inference_zero_shot(text, prompt_text, REF):
        torchaudio.save(dst, out["tts_speech"], 24000)
    print(f"[clone] p{i:02d} 完成({time.time()-t0:.0f}s): {text[:24]}…")
print("[clone] ALL_DONE")
