# -*- coding: utf-8 -*-
"""
CosyVoice2 zero_shot 声音克隆(定版 2026-09-29,音色已确认像本人)
用法(服务器): conda activate cosyvoice && python -u /root/autodl-tmp/clone_zero_shot.py
要点:
- 接口: inference_zero_shot(text, prompt_text, prompt_speech_路径),返回 generator,逐段取 out['tts_speech']
- prompt_text = 参考音频的精确文字稿(whisper medium 转写,language='zh')
- prompt_speech ≤30s(CosyVoice2 声纹提取上限);fp16=False(fp16=True 有 triton 报错风险)
- 产物 24kHz wav
"""
import sys, torchaudio
sys.path.append('/root/autodl-tmp/CosyVoice/third_party/Matcha-TTS')
sys.path.append('/root/autodl-tmp/CosyVoice')
from cosyvoice.cli.cosyvoice import CosyVoice2

PROMPT_SPEECH = '/root/autodl-tmp/voice_ref_v2.wav'
PROMPT_TEXT = "欢迎来到我的频道,今天我们聊聊人工智能的最新进展。大模型正在改变我们的工作和学习方式,从大模型到做视频,效率提升非常明显。如果你觉得内容有帮助,别忘了点赞关注,我们下期再见。"
TEXT = "大家好,今天我们聊一个不一样的话题:普通人如何用AI工具把自己的效率提升十倍。很多人以为学AI很难,其实掌握三个核心方法就够了,接下来我用五分钟给你讲明白。"
OUT = '/root/autodl-tmp/clone_v2_zs_new.wav'

cv = CosyVoice2('/root/autodl-tmp/CosyVoice2-0.5B', load_jit=False, load_trt=False, fp16=False)
for i, out in enumerate(cv.inference_zero_shot(TEXT, PROMPT_TEXT, PROMPT_SPEECH)):
    torchaudio.save(OUT.replace('.wav', '_%d.wav' % i), out['tts_speech'], 24000)
    print('SAVED_%d' % i)
print('DONE')
