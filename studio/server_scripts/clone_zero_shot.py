import sys, torchaudio
sys.path.append('/root/autodl-tmp/CosyVoice/third_party/Matcha-TTS')
sys.path.append('/root/autodl-tmp/CosyVoice')
from cosyvoice.cli.cosyvoice import CosyVoice2

prompt_text = "欢迎来到我的频道,今天我们聊聊人工智能的最新进展。大模型正在改变我们的工作和学习方式,从大模型到做视频,效率提升非常明显。如果你觉得内容有帮助,别忘了点赞关注,我们下期再见。"
text = "大家好,今天我们聊一个不一样的话题:普通人如何用AI工具把自己的效率提升十倍。很多人以为学AI很难,其实掌握三个核心方法就够了,接下来我用五分钟给你讲明白。"

cv = CosyVoice2('/root/autodl-tmp/CosyVoice2-0.5B', load_jit=False, load_trt=False, fp16=False)
for out in cv.inference_zero_shot(text, prompt_text, '/root/autodl-tmp/voice_ref_v2.wav'):
    torchaudio.save('/root/autodl-tmp/clone_v2_zs_new.wav', out['tts_speech'], 24000)
    print('SAVED')
