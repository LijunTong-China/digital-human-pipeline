@echo off
chcp 65001 >nul
cd /d %~dp0
echo == 1. 上传自愈脚本 ==
scp -o ConnectTimeout=10 -P 23278 server_scripts\setup_cosyvoice.sh root@connect.nmb1.seetacloud.com:/root/autodl-tmp/setup_cosyvoice.sh
if errorlevel 1 (echo 上传失败 & pause & exit /b 1)
echo == 2. 服务器执行(拉取 CosyVoice 代码) ==
ssh -p 23278 root@connect.nmb1.seetacloud.com "bash /root/autodl-tmp/setup_cosyvoice.sh 2>&1 | tail -4; df -h /root/autodl-tmp | tail -1"
echo == 3. 验证 import ==
ssh -p 23278 root@connect.nmb1.seetacloud.com "/root/autodl-tmp/envs/cosyvoice/bin/python -c \"import sys;sys.path[:0]=['/root/autodl-tmp/CosyVoice/third_party/Matcha-TTS','/root/autodl-tmp/CosyVoice'];from cosyvoice.cli.cosyvoice import CosyVoice2;print('IMPORT_OK')\" 2>&1 | tail -1"
pause
