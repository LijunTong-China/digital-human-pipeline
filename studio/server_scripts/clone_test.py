import sys, torchaudio
sys.path.append('/root/autodl-tmp/CosyVoice/third_party/Matcha-TTS')
sys.path.append('/root/autodl-tmp/CosyVoice')
from cosyvoice.cli.cosyvoice import CosyVoice2
model = CosyVoice2('/root/autodl-tmp/CosyVoice2-0.5B', load_jit=False, load_trt=False, fp16=True)
prompt_speech_16k = '/root/autodl-tmp/voice_ref_30s.wav'  # CosyVoice2 收文件路径;参考音频必须≤30s
texts = [
  '大家好,欢迎来到今天的频道,今天我们来聊聊人工智能的最新进展。',
  '如果这把声音听起来像你本人,那就说明声纹克隆成功了。',
]
for i, t in enumerate(texts):
    gen = model.inference_cross_lingual(t, prompt_speech_16k, stream=False)
    item = next(iter(gen))
    speech = item['tts_speech']
    print('TYPE', type(item).__name__, tuple(speech.shape))
    torchaudio.save('/root/autodl-tmp/clone_test_%d.wav' % i, speech, 24000)
    print('SAVED_%d' % i)
print('CLONE_TEST_DONE')
