#!/usr/bin/env bash
# CosyVoice 代码库自愈:缺失时重新拉取(仅代码,模型权重已在 CosyVoice2-0.5B/)
# 由 pipeline 自动调用;也可人工执行。AutoDL 学术加速提供 GitHub 通道。
set -e
DEST=/root/autodl-tmp/CosyVoice
if [ -f "$DEST/cosyvoice/cli/cosyvoice.py" ]; then
  echo "[setup] CosyVoice 代码已在,跳过"
  exit 0
fi
source /etc/network_turbo 2>/dev/null || true
rm -rf "$DEST"
git clone --depth 1 --recursive \
  https://github.com/FunAudioLLM/CosyVoice.git "$DEST" \
  || git clone --depth 1 --recursive \
  https://gitee.com/mirrors/FunAudioLLM_CosyVoice.git "$DEST"
unset http_proxy https_proxy 2>/dev/null || true
ls "$DEST/cosyvoice/cli/cosyvoice.py" && echo "[setup] CosyVoice 代码就绪"
