#!/bin/bash
# CosyVoice2 一键安装:clone + pip 依赖 + ModelScope 权重
set -x
exec > /root/setup_cosyvoice.log 2>&1
source /etc/network_turbo 2>/dev/null || true
source /root/miniconda3/etc/profile.d/conda.sh
conda activate cosyvoice
cd /root/autodl-tmp

# 1. 代码 + 子模块
if [ ! -d CosyVoice ]; then
  git clone https://github.com/FunAudioLLM/CosyVoice.git
fi
cd CosyVoice
git submodule update --init --recursive

# 2. torch (CUDA 12.x wheel)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 -q

# 3. 依赖(pynini 用 conda-forge 避免编译失败)
pip install -r requirements.txt -q -i https://mirrors.aliyun.com/pypi/simple/ || true
conda install -y -c conda-forge pynini=2.1.6 -q
pip install WeTextProcessing -i https://mirrors.aliyun.com/pypi/simple/ -q

# 4. 权重(ModelScope 国内直连)
python -c "
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice2-0.5B', local_dir='/root/autodl-tmp/CosyVoice2-0.5B')
print('MODEL_OK')
"

# 5. 冒烟测试:加载模型
python -c "
import sys; sys.path.append('third_party/Matcha-TTS')
from cosyvoice.cli.cosyvoice import CosyVoice2
model = CosyVoice2('/root/autodl-tmp/CosyVoice2-0.5B', load_jit=False, load_trt=False, fp16=True)
print('LOAD_OK')
"

echo SETUP_ALL_DONE
