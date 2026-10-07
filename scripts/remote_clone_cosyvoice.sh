#!/bin/bash
set -e
source /etc/network_turbo 2>/dev/null || true
cd /root/autodl-tmp
if [ ! -d CosyVoice ]; then
  git clone https://github.com/FunAudioLLM/CosyVoice.git
fi
cd CosyVoice
git submodule update --init --recursive
echo CLONE_DONE
