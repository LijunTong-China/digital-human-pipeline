# GPU服务器执行命令记录(AutoDL 4090)

> 【2026-10-02 标识·历史实录】本文件是 2026-09-27~09-30 的服务器操作实录,**全程保留作记录**。
> 已过时部分:实例为旧机 nmb2(:35586,现用 nmb1:23278,见 `studio/SERVER.md`);MuseTalk〔历史:09-30 已删,不在现行方案;现行引擎=EMV3-Flash〕(§11~12)与 EchoMimicV2〔历史:09-30 判死刑并删除〕(§14.2~14.3)相关环境已于 09-30 大扫除删除;GPU 开机等待已由 `studio/pipeline.py wait_gpu()` 自动化(快连→等用户回车→轮询→用完自动关机)。
> **仍然有效**:环境重建命令(CosyVoice §1~4、emv3 §15.4~15.6、GFPGAN 坑)是唯一详细来源,重装环境时照此执行;pip 版本铁律、--no-deps、pynini 走 conda-forge 等教训通用。

> 实例:`autodl`(connect.nmb2.seetacloud.com:35586, root)〔旧实例,历史,旧实例 nmb2,现 nmb1:23278〕
> 目的:装 CosyVoice2 声纹克隆环境(无卡模式下执行,全部不需要 GPU)
> 日期:2026-09-28
> conda 环境名:`cosyvoice`(python 3.10)

## 0. 前置说明

- 所有命令都在 `conda activate cosyvoice` 后执行
- 无卡模式可执行 1~4 步;第 5 步加载验证和后续推理需 4090 开机

## 1. 创建 conda 环境(已完成 2026-09-27)

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda create -n cosyvoice python=3.10 -y
conda activate cosyvoice
```

## 2. 克隆代码(已完成 2026-09-27)

```bash
cd /root/autodl-tmp
git clone https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice
git submodule update --init --recursive
```

## 3. 装 torch(已完成)

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
# 结果: torch 2.14.0 / torchaudio 2.11.0
```

## 4. requirements.txt 踩坑与修复(2026-09-28)

### 坑 A: openai-whisper 源码构建报 `ModuleNotFoundError: No module named 'pkg_resources'`

**完整报错原文(首次出现):**
```
Installing build dependencies ... done
  Getting requirements to build wheel ... error
  error: subprocess-exited-with-error

  × Getting requirements to build wheel did not run successfully.
  │ exit code: 1
  ╰─> [17 lines of output]
      File "/tmp/pip-build-env-luwk8v5t/overlay/lib/python3.10/site-packages/setuptools/build_meta.py", line 520, in run_setup
        super().run_setup(setup_script=setup_script)
      File "/tmp/pip-build-env-luwk8v5t/overlay/lib/python3.10/site-packages/setuptools/build_meta.py", line 317, in run_setup
        exec(code, locals())  # noqa: S102 # exec is intentional here
      File "<string>", line 5, in <module>
    ModuleNotFoundError: No module named 'pkg_resources'
      [end of output]

  note: This error originates from a subprocess, and is likely not a problem with pip.
ERROR: Failed to build 'openai-whisper' when getting requirements to build wheel
```

- 根因:pip 构建隔离环境默认拉 setuptools≥81,已移除 pkg_resources
  (识别特征:报错路径在 `/tmp/pip-build-env-xxxx/overlay/...` = 隔离环境,与主环境 setuptools 版本无关)
- 且环境里的 setuptools 69.5.1 也装坏了(pkg_resources 缺失),需 force-reinstall
- 第二次出现同样错误时报错路径变成 `/root/miniconda3/envs/cosyvoice/...`(用了
  --no-build-isolation),说明主环境的 setuptools 本身也缺 pkg_resources →
  必须 `--force-reinstall` 才真正修好

```bash
# 1) 修复 setuptools(必须 --force-reinstall,普通 install 装不上 pkg_resources)
pip install --force-reinstall --no-deps setuptools==69.5.1 -q

# 2) 验证(应输出 PKG_RES_OK)
python -c "import pkg_resources; print('PKG_RES_OK')"

# 3) 重跑 requirements(--no-build-isolation 用环境内 setuptools,绕过隔离)
cd /root/autodl-tmp/CosyVoice
pip install -r requirements.txt --no-build-isolation -i https://mirrors.aliyun.com/pypi/simple/
```

### 注意
- requirements 锁定 `openai-whisper==20231117`(源码包,必须走上面流程)
- pip 命令接管道时 `echo $?` 取到的是管道最后一个命令(如 tail)的返回值,
  **不能用来判断 pip 是否成功**,要看日志或 `pip show`
- 大包下载慢(onnxruntime-gpu 200MB ≈ 2~9 分钟),建议 nohup 后台跑 + tail 日志

## 5. pynini + WeTextProcessing(✅ 已完成 2026-09-28,PYNINI_OK/WTP_OK)

```bash
conda install -y -c conda-forge pynini=2.1.6 -q   # conda 解依赖较慢,耐心等
pip install WeTextProcessing --no-build-isolation -i https://mirrors.aliyun.com/pypi/simple/
python -c "import pynini; print('PYNINI_OK')"
python -c "import tn; print('WTP_OK')"
```
(pynini 直接 pip 装必编译失败,必须走 conda-forge)

### 附:pyworld 构建失败的修复(requirements 装完后补)
```bash
pip install "cython<3.1" numpy -q
pip install pyworld==0.3.4 --no-build-isolation -i https://mirrors.aliyun.com/pypi/simple/
python -c "import pyworld; print('PYWORLD_OK')"
```

### 附:磁盘清理(requirements 装完后执行)
```bash
pip cache purge   # 释放约12G,系统盘 73% → 26%
```

## 6. 下载权重(✅ 已完成 2026-09-28,用户手动执行,2.4G 已落盘)

```bash
python -c "from modelscope import snapshot_download; snapshot_download('iic/CosyVoice2-0.5B', local_dir='/root/autodl-tmp/CosyVoice2-0.5B'); print('MODEL_OK')"
```
权重存数据盘,换实例不丢。

## 7. 加载验证(⚠️ 需 GPU 实例执行)

**2026-09-28 状态:依赖全部装完,IMPORT_OK(模块导入验证通过,无卡模式);**
**待 GPU 实例跑 LOAD_OK(加载权重)后即可推理。**

经历:第4轮 pyworld 失败整体回滚(pip 全或无)→ 第5轮下载 torch 2.3.1 时系统盘爆满
→ 把 pip 缓存搬到数据盘(`mv /root/.cache/pip /root/autodl-tmp/pipcache` +
软链 + `/root/.config/pip/pip.conf` 设 cache-dir)→ 第6轮成功。
**torch 最终为 requirements 锁定的 2.3.1+cu121(覆盖了之前手装的 2.14)。**
实例多次切换(3080Ti→无卡),SSH config 的 autodl 端口跟着改。

```bash
cd /root/autodl-tmp/CosyVoice
python -c "
import sys; sys.path.append('third_party/Matcha-TTS')
from cosyvoice.cli.cosyvoice import CosyVoice2
model = CosyVoice2('/root/autodl-tmp/CosyVoice2-0.5B', load_jit=False, load_trt=False, fp16=True)
print('LOAD_OK')"
```

## 8. 声纹克隆测试(✅ 2026-09-29 CLONE_TEST_DONE)
> 注:§8~§10 的克隆链路(clone_zero_shot.py)已演进为 studio/server_scripts/clone_pages.py(数据驱动),见 studio/SERVER.md。〔历史〕

- 上传 `voice_ref.wav`(60s)后**裁前30s**为 `voice_ref_30s.wav`(模型声纹提取上限30s,
  只限参考音频,不限生成时长)
- 推理脚本:`scripts/clone_test.py`(本地)→ 服务器 `/root/autodl-tmp/clone_test.py`
- 关键接口坑:**CosyVoice2 的 inference_cross_lingual 第一个参数收文件路径**(内部自行
  load+重采样),传张量会报 `Invalid file: tensor`;返回值是 generator,要 `next(iter())`
- 产物:`demo/output/clone_test_0.wav` / `clone_test_1.wav`(24kHz,已下载回本地待用户试听)

## 下一步
> 〔历史:本节三条均已于 09-30 前后作废——demo8_final 已废、MuseTalk 已删、克隆已并入 studio/pipeline.py ④〕

- 用户试听确认音色 → 把 CosyVoice 克隆接进 demo8_final 流水线(替换原 TTS)
- MuseTalk〔历史:09-30 已删,不在现行方案;现行引擎=EMV3-Flash〕(口型)安装与验证
- 口型视频放 `demo/output/demo8/lipsync/pXX.mp4` 后本地重跑 demo8_final.py

## 9. whisper 转写 + zero_shot 克隆(✅ 2026-09-29)

### 9.1 无卡模式:下载 whisper medium 权重(✅)

```bash
# 无卡开机模式容器内存限 2GB(cgroup memory.max),加载 medium(~5GB)会 OOM Killed
# 无卡模式只用于下载
nohup python -c "import whisper; m=whisper.load_model('medium'); print('DL_OK')" > /root/whisper_dl.log 2>&1 &
# 结果: /root/.cache/whisper/medium.pt 1.5G 下载完成(~4min, 7MiB/s)
# 坑: 首次中断留下 747M 残文件,重跑会因 SHA256 不符整个重新下载(不续传)
```

### 9.2 GPU 模式:ffmpeg 安装(whisper 依赖,之前没装过)

```bash
# whisper transcribe 内部调 ffmpeg 解码音频;CosyVoice 用 torchaudio 读 wav 不需要它
apt-get update && apt-get install -y ffmpeg   # conda-forge 装法失败,apt 成功(4.4.2)
```

### 9.3 whisper 转写(✅ medium, GPU)

```bash
python -c "
import whisper
m = whisper.load_model('medium').to('cuda')
r = m.transcribe('/root/autodl-tmp/voice_ref_v2.wav', language='zh')
print(r['text'].strip())"
# 结果(voice_ref_v2.wav 21.6s):
# 欢迎来到我的频道,今天我们聊聊人工智能的最新进展大模型政策改变我们的工作和学习方式
# 从大模到做视频效率提升非常明显如果你觉得内容有帮助,别忘了点赞关注我们下期再见
```

### 9.4 zero_shot 克隆(✅)

- 脚本:服务器 `/root/clone_zero_shot.py`(参照 clone_test.py,inference_cross_lingual
  → inference_zero_shot(text, prompt_text, prompt_speech_路径))
- fp16=False(fp16=True 会触发 triton autotune 报错风险,稳妥用 fp16=False)
- prompt_text = whisper 转写文本;text = 要合成的目标文本
- 产物:`/root/autodl-tmp/clone_v2_zs.wav` → 已下载回 `demo/output/clone_v2_zs.wav`(24kHz)待试听

## 10. zero_shot 克隆定版(✅ 2026-09-29 用户确认"很像")

- **定版模式:zero_shot;产物 `demo/output/clone_v2_zs_new.wav`(新文本合成)试听通过**
- 定版脚本:本地 `scripts/clone_zero_shot.py` ↔ 服务器 `/root/autodl-tmp/clone_zero_shot.py`(持久盘,重启不丢)〔历史:现行真源=studio/server_scripts/clone_pages.py〕
- 重跑流程(下次重新运行照此):〔历史:现行由 pipeline 自动上传/执行,无需人工〕
  1. AutoDL 开机(GPU 模式,3080Ti/4090 均可)→ `ssh autodl`
  2. 环境已就绪(conda env `cosyvoice` + 权重 `/root/autodl-tmp/CosyVoice2-0.5B` + whisper medium + ffmpeg),直接:
     `conda activate cosyvoice && python -u /root/autodl-tmp/clone_zero_shot.py`
  3. 改文本只改脚本里 `TEXT`;换参考音频则重走:转 m4a→wav(imageio-ffmpeg,≤30s)→ 上传 → whisper 转写更新 PROMPT_TEXT〔历史:现行参考文字稿走 assets/ref_prompt.txt〕
- 参考音频标准:真人朗读、环境安静、21.6s/24kHz 单声道;whisper 转写稿需人工过一遍再进 PROMPT_TEXT(转写偶有漏字)

## ⚠️ 开机模式分类规范(2026-09-29 用户要求,防浪费)

> 原则:**凡是下载/安装,一律无卡模式先做完;只有推理才需要 GPU。开卡前先问自己:这一步能不能无卡干?**

### ✅ 无卡模式可做(不花钱等GPU,内存限2GB 不能加载模型)

| 内容 | 命令/位置 |
|---|---|
| conda env 创建、pip/conda 装依赖(含 torch 下载) | musetalk_setup.sh 全流程 |
| git clone 代码仓库 | MuseTalk(gh-proxy.com 镜像,直连GitHub超时)〔历史:09-30 已删〕 |
| HF 权重下载(hf-mirror) | **注意 hub>=1.32 命令是 `hf download`,旧 `huggingface-cli download` 只打印帮助静默假成功** |
| whisper 权重下载 | /root/.cache/whisper/medium.pt 1.5G(已完) |
| MuseTalk 全部权重 ~5.4G(已完)〔历史:09-30 已删〕 | models/ 下 unet 3.2G + sd-vae + whisper + dwpose + syncnet + face-parse |
| apt-get 装 ffmpeg | ✅ 已装 4.4.2 |
| 上传音频/图片素材 | scp/mcp upload |
| gdown(Google Drive)下载 | face-parse 的 79999_iter.pth(已完) |

### 🔴 必须 GPU 模式(真实推理,2GB内存限制加载不了)

| 内容 | 原因 |
|---|---|
| whisper medium 转写 | 加载需 ~5GB 内存,无卡 2GB 会 OOM Killed |
| CosyVoice2 加载+克隆推理 | 同上,且需 CUDA |
| MuseTalk 加载+对口型推理 | 同上 |
| 任何 LOAD_MODEL / inference | 一律等开卡 |

### 已完成的全部环境(下次直接开卡跑,无需重装)

- conda env: `cosyvoice`(whisper+克隆)、`musetalk`(对口型)均装好
- 权重: CosyVoice2-0.5B、whisper medium、MuseTalk 全套 均在 /root/autodl-tmp 与 ~/.cache(注意:~/.cache/whisper 在系统盘,换实例需重新下!)〔历史:09-30 大扫除已删,与 §15.8 矛盾时以 §15.8 为准〕
- 脚本: /root/autodl-tmp/clone_zero_shot.py(克隆定版)、MuseTalk 代码 /root/autodl-tmp/MuseTalk
- ffmpeg 系统级已装

## 11. MuseTalk 安装记录(2026-09-29)

```bash
# 1) 独立 env(勿装进 cosyvoice,依赖冲突 numpy/tensorflow)
conda create -n musetalk python=3.10 -y && pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
# 2) 依赖:requirements.txt 去掉 tensorflow/tensorboard/gradio/numpy==1.23.5,加 numpy==1.26.4
# 3) 克隆: git clone https://gh-proxy.com/https://github.com/TMElyralab/MuseTalk.git
# 4) 权重:/root/mt_dl.sh(用 hf download + HF_ENDPOINT=https://hf-mirror.com)✅ WEIGHTS_DONE
#    gdown face-parse(79999_iter.pth)✅
# 坑1: huggingface-cli download 在 hub 1.32 是空操作(打印帮助退出0)→ 必须用 hf download
# 坑2: GitHub 直连超时 → gh-proxy.com
# 坑3: 无卡模式就应完成以上全部(GPU时段才被用来下载,已纠偏)
```

## 12. MuseTalk 对口型(✅ 2026-09-29 出片 demo/output/lipsync_char_v1.mp4)

### 运行命令(下次直接跑)

```bash
cd /root/autodl-tmp/MuseTalk && conda activate musetalk
export HF_ENDPOINT=https://hf-mirror.com
# 换素材: 改 data/video/char.mp4(形象帧视频) + data/audio/char.wav(克隆音频) + configs/inference/char.yaml
python -m scripts.inference --inference_config configs/inference/char.yaml \
  --result_dir results --unet_model_path models/musetalkV15/unet.pth \
  --unet_config models/musetalkV15/musetalk.json --version v15 --gpu_id 0
# 产物 results/v15/char_char.mp4(带音轨)
```

### 形象素材制作(本地)

- `assets/character/char_keyed.png`(1198×2061 RGBA)→ 白底化 + 裁上半身(高*0.45)
- ffmpeg 生成静态视频:**必须缩放到宽高偶数且 ~0.5 倍(598×462)** — 坑①脸占满画面 S3FD 检测不到(0.5倍即可);坑②高度奇数 x264 报错
  `ffmpeg -loop 1 -i char_upper.jpg -t 时长+2s -r 25 -vf scale=598:462 -pix_fmt yuv420p char.mp4`

### 踩坑全记录(装依赖花了大头)

1. **mmcv 预编译包**: cu121 只有 torch2.4 目录(2.5 目录 404),且只有 mmcv 2.2.0 → torch 降到 2.4.1+cu121,直装 wheel `.../cu121/torch2.4.0/mmcv-2.2.0-cp310-cp310-manylinux1_x86_64.whl`
2. **chumpy 坏包**挡住 mmpose/mmdet → 全部 `pip install --no-deps` + 手补依赖(json_tricks xtcocotools munkres scipy shapely prettytable pycocotools terminaltables)
3. **mmdet 3.3.0 要求 mmcv<2.2.0** → sed 改 site-packages/mmdet/__init__.py 的 mmcv_maximum_version='2.3.0'
4. **huggingface_hub 必须 0.30.2**(transformers 4.39 要求 <1.0)
5. s3fd 人脸检测模型 85.7M 从 adrianbulat.com 直下很慢(~7min),无镜像
6. **复合命令里一步失败,后面的 cp 等不会执行**(这次音频没复制导致 get_audio_feature 返回 None,报"cannot unpack non-iterable NoneType")
7. scripts/inference.py 的 except 只打印消息,排查时先加 traceback.print_exc()
8. musetalk.json 曾下到嵌套目录 musetalkV15/musetalkV15/,注意移正

### 质量注意

- 形象是 3D 卡通风格,MuseTalk 训练数据是真人脸,口型区域生成效果待用户验收
- 若效果差 → 备选: 换真人形象 / LivePortrait / 即梦等卡通驱动方案

## 14. 声音生动性定版 + 对口型换引擎 EchoMimicV2(2026-09-29~30)

### 14.1 声音:AB 实验结论(GPU 模式做的推理)

| 方案 | 结果 |
|---|---|
| instruct2(新指令"年轻男声热情生动") | ❌ 仍是女声,漂移不可控,**instruct2 全线禁用** |
| zero_shot + 原文案 | 音色对但平淡(韵律照抄参考音频) |
| **zero_shot + 口语化文案(定版 ✅)** | 短句/语气词/感叹号让韵律起伏,音色不跑。样品 `demo/output/ab/ab2_expressive.wav` 用户认可 |

- **演播稿写作铁律(已定版)**:讲解词必须口语化——短句、语气词(诶/嘛/啊/明白了吧)、感叹号、反问。模板:`demo/input/voices_v2.txt`(9页第2版文案,服务器 `/root/autodl-tmp/voices_v2.txt`)
- **定版产物(GPU 已跑完)**:9页克隆音频 `/root/autodl-tmp/pages/v2_pXX.wav` + whisper简体时间轴 `/root/autodl-tmp/pages/timings_v2.json`;脚本 `/root/batch_v2.py`(CosyVoice2 zero_shot + whisper medium,一次跑完)
- 本地已下载:v2 克隆音频 p00、p06(`demo/output/demo8/clone_pXX.wav`),**其余 7 页 + timings_v2.json 待下载**〔历史:后已全部到位;且 timings_v2 属旧链路,现行无此文件〕(服务器持久盘都在)

### 14.2 口型:三次换引擎记录

1. **MuseTalk v1.5 结论**:bbox_shift 在 v15 固定为 0 无效;`--extra_margin 30` 口周出阴影更差 → 娃娃脸超出能力,**弃用**〔历史:09-30 已删,不在现行方案;现行引擎=EMV3-Flash〕
2. **LivePortrait 弃用**:它是**视频驱动**(要真人讲解视频迁移表情),不吃音频,与全自动流程冲突〔历史:已弃〕。权重已删(2.1G),repo 已删
3. **EchoMimicV2 选定**〔历史:09-30 判死刑并删除〕(音频驱动,图+音频→半身说话,antgroup/echomimic_v2)

### 14.3 EchoMimicV2 安装进度(2026-09-30 凌晨关机时状态)

**✅ 已完成(下次开机无需再做):**
- 代码:`/root/autodl-tmp/echomimic_v2`(gh-proxy 克隆)
- conda env **lp**(为 LivePortrait 建的,torch 2.4.1+cu121,python3.10,被 EchoMimicV2 复用)
- 主权重 11G:`/root/autodl-tmp/echomimic_v2/pretrained/`(denoising_unet(_acc)、reference_unet、pose_encoder、motion_module(_acc) 6个pth;已 mv 进 `pretrained_weights/`)
- 辅助权重:`/root/autodl-tmp/echomimic_v2/pretrained_weights/` 下 sd-image-variations-diffusers(~5G)、sd-vae-ft-mse、audio_processor/tiny.pt(hf download + hf-mirror,全部完成)
- 参考图:`/root/autodl-tmp/echomimic_v2/assets/char_ref.png`(char4.mp4 首帧 768×768)
- 测试音频:`/root/autodl-tmp/pages/v2_p00.wav`

### ⚠️ 明日续跑命令(按开机模式分两版,严格按顺序)

━━━ 【第一版:无卡模式先做(便宜)】━━━ ✅ **2026-09-30 已全部完成**

```bash
ssh autodl〔旧实例 nmb2,现 nmb1:23278〕    # 无卡开机模式连接

# ①② 装剩余依赖(实际定版命令,2026-09-30 用户手动执行通过,ALL_IMPORT_OK):
# 主批(注意:不带 --no-deps 会试图升级 torch 2.5.1→2.14(554M)撑爆系统盘,报 No space left;
#       前半段多数包当时已装上,失败点在 torch 升级,所以有下面②③两步):
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lp && pip install decord av==13.1.0 moviepy einops==0.8.0 omegaconf==2.3.0 accelerate==1.1.1 diffusers==0.31.0 transformers==4.46.3 onnxruntime-gpu==1.20.2 open-clip-torch==2.29.0 imageio==2.36.0 imageio-ffmpeg==0.5.1 torchmetrics torchtyping tqdm safetensors numpy==1.26.4 opencv-python==4.10.0.84 -i https://mirrors.aliyun.com/pypi/simple/
# 主包 --no-deps 补装(绕过 torch 升级):
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lp && pip install --no-deps transformers==4.46.3 onnxruntime-gpu==1.20.2 open-clip-torch==2.29.0 imageio==2.36.0 imageio-ffmpeg==0.5.1 torchmetrics torchtyping -i https://mirrors.aliyun.com/pypi/simple/
# 小依赖也必须 --no-deps(否则 timm→torchvision→torch 全家桶 ~1G;公共依赖环境已有,不影响运行):
pip install --no-deps tokenizers==0.20.3 coloredlogs flatbuffers "protobuf<5" ftfy timm lightning-utilities "typeguard<3" humanfriendly wcwidth huggingface_hub==0.30.2 -i https://mirrors.aliyun.com/pypi/simple/

# 验证(必须先 conda activate lp;transformers 4.46 要求 huggingface_hub<1.0,上面用 0.30.2):
python -c "import numpy, decord, moviepy, diffusers, transformers, onnxruntime; print('ALL_IMPORT_OK')"
# 坑:onnxruntime-gpu==1.20.1 阿里源不存在,用 1.20.2

# ③ 补下载 v2 克隆音频到本地 ✅ 2026-09-30 完成(用户在 Windows PowerShell 用 scp 拉取:
#    foreach ($i in "00".."08") { scp -P <端口> root@connect.nmb2.seetacloud.com:/root/autodl-tmp/pages/v2_p$i.wav "E:\...\demo8\clone_p$i.wav" }
#    + timings_v2.json。9个wav+timings_v2.json 全部到位)
#    坑:Windows 原生 scp 不认 ssh 别名 autodl(mcp-ssh 的 config 才认),要用 root@connect.nmb2.seetacloud.com -P 端口直连
```

━━━ 【第二版:有卡模式执行(真推理,~20分钟)】━━━ ⏳ 待执行〔历史:未执行,EchoMimicV2〔历史:09-30 判死刑并删除〕路线已放弃〕
```bash
ssh autodl〔旧实例 nmb2,现 nmb1:23278〕    # GPU 模式开机(批量 9 页建议 4090;3080Ti 12G 可先跑样品)

# ④ p00 单页对口型样品(1-2分钟),给用户验收
cd /root/autodl-tmp/echomimic_v2 && conda activate lp && export FFMPEG_PATH=/usr/bin
python -u infer.py --config ./configs/prompts/infer.yaml -W 768 -H 768 -L 320 \
  --ref_images_dir ./assets --refimg_name char_ref.png \
  --audio_dir /root/autodl-tmp/pages --audio_name v2_p00.wav --steps 30
# 产物在 outputs/ 下(带音轨),下载回本地给用户验收

# ⑤ 验收通过后:9页批量(把④的 --audio_name 换成 v2_pXX.wav 循环跑,
#    或写批量脚本 /root/emv2_batch.py),下载 lipsync pXX 到 demo/output/demo8/lipsync/

# ⑥ 本地合成(demo9_lipsync.py 需先改:timings_v1.json → timings_v2.json)
python demo/demo9_lipsync.py
# 产出 demo/output/demo9_lipsync.mp4
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
注:当前实例是 3080Ti 12G;批量跑 9 页时建议换 4090。

### ⚠️ 无卡全链路验证(定版,2026-09-30 补加——开卡前必做,防止缺包开卡才暴露)

> 教训:之前只验证了 6 个主库 import,没跑 infer.py 完整 import 链,导致开卡后连续 4 次缺包重启
> (ffmpeg-python、torchvision、matplotlib、moviepy 2.x 无 editor)。无卡就能全查出来。

```bash
# ① 补齐今天踩出来的 4 个漏装包(定版版本,别动):
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lp
pip install ffmpeg-python matplotlib "moviepy==1.0.3" -i https://mirrors.aliyun.com/pypi/simple/
pip install torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu121
# 坑:moviepy 必须 1.0.3(2.x 没有 moviepy.editor 模块);torchvision 必须 0.20.1 配 torch 2.5.1,
#     千万别让 pip 自由解析(会拉最新版并重装 torch 全家桶)

# ② 完整 import 干跑(无卡可做,直接 import infer.py 整条依赖链):
cd /root/autodl-tmp/echomimic_v2 && conda activate lp
python -c "import infer; print('FULL_IMPORT_OK')"
# 出 FULL_IMPORT_OK = infer.py 用到的每一个模块都在,开卡不会再缺包

# ③ 配置里所有权重路径存在性检查(无卡可做):
cd /root/autodl-tmp/echomimic_v2 && python - <<'EOF'
import os
from omegaconf import OmegaConf
c = OmegaConf.load('configs/prompts/infer.yaml')
for k, v in c.items():
    if isinstance(v, str) and v.startswith('./'):
        print(('OK  ' if os.path.exists(v) else 'MISS'), k, '=', v)
EOF
# 不能有 MISS;audio_model_path 已改为 "tiny"(whisper 官方模型名,首次 GPU 运行自动下载
# 到 ~/.cache/whisper,已软链到数据盘;HF 上没有原始 tiny.pt,别再试 hf download)
```

### 14.4 用户执行过的全部命令(2026-09-30,原样记录)

```bash
# ① 主批安装(不带 --no-deps,在 torch 升级处失败,但前半段包已装上):
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lp && pip install decord av==13.1.0 moviepy einops==0.8.0 omegaconf==2.3.0 accelerate==1.1.1 diffusers==0.31.0 transformers==4.46.3 onnxruntime-gpu==1.20.2 open-clip-torch==2.29.0 imageio==2.36.0 imageio-ffmpeg==0.5.1 torchmetrics torchtyping tqdm safetensors numpy==1.26.4 opencv-python==4.10.0.84 -i https://mirrors.aliyun.com/pypi/simple/

# ② 主包 --no-deps 补装(成功):
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lp && pip install --no-deps transformers==4.46.3 onnxruntime-gpu==1.20.2 open-clip-torch==2.29.0 imageio==2.36.0 imageio-ffmpeg==0.5.1 torchmetrics torchtyping -i https://mirrors.aliyun.com/pypi/simple/

# ③ 小依赖 --no-deps(成功;不加 --no-deps 会拉 timm→torchvision→torch 约1G):
pip install --no-deps tokenizers==0.20.3 coloredlogs flatbuffers "protobuf<5" ftfy timm lightning-utilities "typeguard<3" humanfriendly wcwidth huggingface_hub==0.30.2 -i https://mirrors.aliyun.com/pypi/simple/

# ④ 删 musetalk 环境腾空间(报错提示但实际删除成功,系统盘 95%→77%):
source /root/miniconda3/etc/profile.d/conda.sh && conda env remove -n musetalk -y

# ⑤ Windows PowerShell 下载 9 页音频 + 时间轴(Windows 原生 scp 不认 ssh 别名,必须 IP+端口):
foreach ($i in "00","01","02","03","04","05","06","07","08") { scp -P 34026〔旧实例 nmb2,现 nmb1:23278〕 root@connect.nmb2.seetacloud.com〔旧实例 nmb2,现 nmb1:23278〕:/root/autodl-tmp/pages/v2_p$i.wav "E:\selfProject\cloneAIProject\demo\output\demo8\clone_p$i.wav" }
scp -P 34026〔旧实例 nmb2,现 nmb1:23278〕 root@connect.nmb2.seetacloud.com〔旧实例 nmb2,现 nmb1:23278〕:/root/autodl-tmp/pages/timings_v2.json "E:\selfProject\cloneAIProject\demo\output\demo8\timings_v2.json"

# ⑥ 验证(PowerShell,9个wav+timings_v2.json 全部到位):
Get-ChildItem "E:\selfProject\cloneAIProject\demo\output\demo8\" | Where-Object {$_.Name -match "clone_p|timings_v2"} | Select-Object Name, Length
```
注:端口 34026 是 2026-09-30 实例端口,**实例重启后会变**,以控制台为准。

### 14.5 今日踩坑(防重蹈)

1. **`hf download --local-dir` 前必须 `mkdir -p`**:脚本里 `cd` 到不存在目录会失败,相对路径下载落到 `/root`(系统盘),一度撑到 96%。救回:`mv /root/sd-image-variations-diffusers …/pretrained_weights/`
2. **pip 装 CLIP 两个死法**:直接 github URL 15s 超时;`gh-proxy.com` 的 zip URL 会被 pip 当 git 参数 mangle 后 clone 失败。**结论:推理不需要 CLIP,直接 grep -v "^clip" 过滤 requirements**
3. **`pkill -f xxx` 放在复合命令里会把整个复合命令自己杀掉**(模式匹配到自身),后续 heredoc/mv 全不执行 → 复合命令里避免 pkill,或用 PID
4. **残留 pip 进程抢锁**:老 `pip install ./CLIP` 挂 8 分钟没死,新 pip 与它并发装同一环境 → 发现装不动先 `ps aux | grep pip` 清场
5. **MCP 复合命令超时(124)不代表失败但也不代表成功**,nohup 后台脚本必须单独验证产物(grep DONE 标记)
6. `requirements.txt` 里 `clip @ https://github.com/...` 这种直连行是整体安装失败的最常见根因(镜像源换不了 GitHub)
7. **磁盘**:安装中途系统盘 99%(pip 想 torch 2.5.1→2.14 升级 554M + 临时文件);**2026-09-30 已删 musetalk env(6.4G, MuseTalk〔历史:09-30 已删,不在现行方案;现行引擎=EMV3-Flash〕),系统盘回到 77%**。MuseTalk 权重(5.6G 数据盘)已删〔历史:同日 §15.8 已删〕
8. **pip 依赖两条铁律**:装包前想清楚会不会拉 torch(开 --no-deps);装完必 conda activate 对应环境再验证

## 13. 磁盘空间整理(2026-09-29,系统盘92%→74%)

- ⚠️ miniconda3(29G)不能搬到数据盘:50G 数据盘放不下(已用21G+环境22G),mv 中断会产生两份不完整副本(本次踩过,rsync 补完后又删除)
- 已做: conda clean -a、pip/apt cache 清、/tmp 清空、whisper+torch 缓存移到 /root/autodl-tmp 并软链接
- 铁律: 权重/数据一律放 /root/autodl-tmp(数据盘);装新环境前先 df -h / 查余量

## 15. 口型引擎第四候选:EchoMimicV3 / V3-Flash(2026-09-30,权重已下载)

### 15.1 背景与可行性结论

- EchoMimicV2 判死刑(整帧扩散、脸必糊必扭)后,唯一同时满足"手能动+音频驱动+全自动"的候选
- **Flash 版官方要求 12G 显存**,支持 768×768;普通版 16-24G。3090(24G)/4090 均可
- 8步推理 + TeaCache,81帧/段速度可用
- ⚠️ 原理仍是**整帧扩散重生**(与 V2 同族,底座 Wan2.1 强一代),脸会不会糊只能出样品验证——先 p00 样品,过了才谈批量

### 15.2 服务器现状(2026-09-30 用户手动下载完成 ✅)

```text
/root/autodl-tmp/EchoMimicV3/
├── repo/            148M  代码(github antgroup/echomimic_v3,含 infer_flash.py / run_flash.sh / config/config.yaml)
└── weights/         27G
    ├── EchoMimicV3/echomimicv3-flash-pro/   flash transformer (diffusion_pytorch_model.safetensors)
    ├── EchoMimicV3/transformer/
    ├── Wan2.1-Fun-V1.1-1.3B-InP/  19G       主模型(umt5-xxl + VAE + clip + diffusion_pytorch_model.safetensors)
    └── chinese-wav2vec2-base/     1.5G     Flash 音频编码器(注意:同目录的 wav2vec2-base-960h 是英文版,Flash 不用它)
```

- 数据盘 73%(73G/100G)。删掉的 echomimic_v2(17G)就是为它腾的位置

### 15.3 运行命令(run_flash.sh 骨架,路径已对准服务器)

```bash
cd /root/autodl-tmp/EchoMimicV3/repo
python infer_flash.py \
  --image_path /root/autodl-tmp/assets/ref/xingxiang1.png \
  --audio_path /root/autodl-tmp/pages/v2_p00.wav \
  --prompt "A person is speaking." \
  --num_inference_steps 8 \
  --config_path config/config.yaml \
  --model_name /root/autodl-tmp/EchoMimicV3/weights/Wan2.1-Fun-V1.1-1.3B-InP \
  --ckpt_idx 50000 \
  --transformer_path /root/autodl-tmp/EchoMimicV3/weights/EchoMimicV3/echomimicv3-flash-pro/diffusion_pytorch_model.safetensors \
  --save_path outputs \
  --wav2vec_model_dir /root/autodl-tmp/EchoMimicV3/weights/chinese-wav2vec2-base \
  --sampler_name Flow_Unipc --video_length 81 --guidance_scale 6.0 \
  --audio_guidance_scale 3.0 --audio_scale 1.0 --neg_scale 1.0 --neg_steps 0 \
  --seed 43 --enable_teacache --teacache_threshold 0.1 --num_skip_start_steps 5 \
  --riflex_k 6 --weight_dtype bfloat16 --sample_size 768 768 --fps 25 --shift 5.0
```

### 15.4 环境安装(2026-09-30 无卡阶段完成 ✅,实际定版命令)

- 环境改用系统盘 conda env(名字 **emv3**,非数据盘 -p 方式):`conda create -n emv3 python=3.10`
- 定版版本(**踩坑后钉死,勿升级**):
  - `torch==2.4.1 torchvision==0.19.1`(cu121)
  - `transformers==4.49.0` —— 5.x 要求 torch≥2.5 会拒载
  - `diffusers==0.31.0` —— 0.40 的 attention_dispatch 在 torch2.4 上 infer_schema 崩;0.31 与官方 README 一致
  - `retina-face`:PyPI 0.0.17/0.0.14 的 wheel 是坏的(只打包 README),须源码装 0.0.19(git+gh-proxy),且 0.0.19 模块改名 `retinaface`,已在 site-packages 手写 `retina_face/__init__.py` 别名兼容
  - requirements 其余照装;requirements 外补 `pyloudnorm`(代码 import 了但没列)
- 验证方式:`python infer_flash.py --image_path x --audio_path x` 干跑,能走到"缺 --prompt"报错 = 全 import 链通过
- ⚠️ 已知问题(不阻塞):retina_face import 链报 tensorflow.keras 缺失(单独 import tf.keras 正常),只影响 infer_preview.py,Flash 不用
- pip 源:aliyun 快(10MB/s),tuna 反而慢;安装中途 pip 卡死 40 分钟无日志进展 = 卡住,杀掉重跑就好

### 15.5 出样验证(2026-09-30 有卡,两轮对比,效果不错 ✅ 待定版)

**第一轮(全身图 1728×2304 直接喂)效果差:**
- 200帧×768×1024 → VAE 解码 OOM(24G 显存不够);降 129帧×768×768 + `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 才跑通
- 生成能跑但**脸糊、五官漂移**:管线把整张竖版图 resize 到 768×768(`get_image_to_video_latent2` 是直接 resize 不裁剪),脸只占画面 1/3(≈200px),必然糊

**第二轮(裁剪图,效果不错 ✅):**
- **构图铁律:先裁剪再喂**。脸部为中心裁 1300×1300 方形(脸占画面 ~2/3),脸部分辨率×3,糊和畸变全部解决
- 裁剪图:本地 `demo/input/形象_crop768.png` ↔ 服务器 `/root/autodl-tmp/EchoMimicV3/input_xingxiang_crop.png`
- 样品:`demo/output/emv3_sample2_crop.mp4`(768×768, 5.2s, 129帧, 眼镜/眉毛/牙齿清晰,口型自然)
- 参数:8步 + TeaCache(0.1) + Flow_Unipc + seed 43;129帧总耗时约 11 分钟(扩散仅 3.5 分钟,大头是模型加载+VAE 解码)
- 长视频显存上限:200帧×768×1024 OOM;129帧×768×768 通过 → 长音频按 ~5s/段分段生成再拼接

### 15.6 定版运行命令(2026-09-30 实测可用)

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate emv3
cd /root/autodl-tmp/EchoMimicV3/repo
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True nohup python infer_flash.py \
  --image_path /root/autodl-tmp/EchoMimicV3/input_xingxiang_crop.png \
  --audio_path /root/autodl-tmp/EchoMimicV3/test_audio.wav \
  --prompt "A person is speaking." \
  --num_inference_steps 8 \
  --config_path config/config.yaml \
  --model_name /root/autodl-tmp/EchoMimicV3/weights/Wan2.1-Fun-V1.1-1.3B-InP \
  --ckpt_idx 50000 \
  --transformer_path /root/autodl-tmp/EchoMimicV3/weights/EchoMimicV3/echomimicv3-flash-pro/diffusion_pytorch_model.safetensors \
  --save_path /root/autodl-tmp/EchoMimicV3/outputs \
  --wav2vec_model_dir /root/autodl-tmp/EchoMimicV3/weights/chinese-wav2vec2-base \
  --sampler_name "Flow_Unipc" \
  --video_length 129 \
  --guidance_scale 6.0 --audio_guidance_scale 3.0 --audio_scale 1.0 --neg_scale 1.0 --neg_steps 0 \
  --seed 43 --enable_teacache --teacache_threshold 0.1 --num_skip_start_steps 5 --riflex_k 6 \
  --weight_dtype bfloat16 --sample_size 768 768 --fps 25 \
  > /root/autodl-tmp/emv3_run3.log 2>&1 &
```

- 音频预处理:24kHz wav,先截到目标段长(`soundfile` 读前 N 秒存 test_audio.wav);video_length=帧数=秒数×25
- 已定版(2026-09-30):正式口型引擎,双方案②③

### 15.7 裁剪比例定版(方案③铁律,换图也照此办)

**原图 1728×2304(即梦 `demo/input/形象.png`)的实测裁剪参数:**
```python
from PIL import Image
im = Image.open('形象.png')          # 1728×2304 竖版半身
box = (210, 150, 1510, 1450)          # (left, top, right, bottom) → 1300×1300
im.crop(box).save('形象_crop768.png') # 管线自己 resize 到 768×768,不用手动缩
```
- 脸部中心约在原图 (860, 780);裁剪窗 1300×1300,上沿 y=150(头顶留空 ~100px),下沿到胸口
- 效果:脸占画面 **~2/3**,768 输出里脸 ≈500px(直喂原图只有 ~200px,必糊)
- **通用规则(换图时)**:
  1. 裁正方形,脸宽/脸高占画面 60%~70%,不是"头占1/3"(那是 MuseTalk 竖版视频的规则,EMV3 是 768 方图,脸要大)
  2. 头顶留 5%~8% 空隙,下方裁到锁骨/上胸
  3. 裁完不需要手动 resize,管线内部 LANCZOS 缩到 768
  4. 裁剪中心对准**脸部中心**(眼鼻之间),不是整头
- 产物链:`demo/input/形象.png`(原图)→ `demo/input/形象_crop768.png`(方案③输入定版)↔ 服务器 `/root/autodl-tmp/EchoMimicV3/input_xingxiang_crop.png`

**推理配置速查(定版):** steps=8 | teacache 0.1 / skip 5 | Flow_Unipc | guidance 6.0 / audio_guidance 3.0 / audio_scale 1.0 | neg_scale 1.0, neg_steps 0 | seed 43 | bfloat16 | 768×768@25fps | video_length≤129(200帧 OOM)| env=emv3(torch2.4.1/transformers4.49/diffusers0.31.0)

### 15.8 运行经过全记录(2026-09-30 晚,三轮出片 + GFPGAN 实验 + 清理收尾)

**第一轮(19:09,run1):全身图直喂 + 200帧×768×1024 → OOM**
- `input_xingxiang.png`(1728×2304 竖版半身)直接喂,video_length=200,sample_size 768×1024
- 8步扩散正常(Transformer 权重加载时日志打印 audio_injection.* 键列表,当时怀疑音频注入层没加载,后证明虚惊),**VAE 解码阶段 CUDA OOM**(24G 显存被 200帧×1024 的逐帧解码撑爆)
- 教训:显存上限由"帧数×分辨率"共同决定,200×1024 不行,129×768 行

**第二轮(19:09,run2):全身图直喂 + 129帧×768×768 → 出片但脸糊**
- 加 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 防碎片;8步扩散仅 3.5 分钟
- 输出被管线从 768² 拉回 656×880(原纵横比)——`get_image_to_video_latent2` 是把输入图**整体 resize 到 768×768,不裁剪**,脸只占画面 1/3(≈200px),必然糊+五官漂移
- 结论:这不是引擎不行,是**输入构图不行**

**第三轮(19:09,run3):裁剪图 + 129帧×768×768 → 定版质量 ✅**
- 本地 PIL 裁剪:crop box (210,150,1510,1450) → 1300×1300,脸占 2/3,上传服务器
- 出片 768×768 纯方形无二次拉伸;眼镜/眉毛/牙齿清晰,口型自然,畸变消失
- 样品 `emv3_sample2_crop.mp4`,总耗时约 11 分钟(扩散 3.5 分钟 + 加载/解码/合成约 7 分钟)

**GFPGAN 逐帧修复实验(20:00~20:40,用户提议 FaceDetailer 思路,等价实现):**
- 用户问的参数映射:audio_guidance_scale 本来就是 3.0;motion_bucket_id 是 AnimateDiff/SVD 的参数 EMV3 没有;FaceDetailer 用"检测脸→GFPGAN 修复→贴回"等价替代
- **安装三坑**:①pip 装 gfpgan 时 basicsr 源码包在构建隔离环境里偷偷下载 torch 2.14(2G+),必须 `--no-build-isolation`;②basicsr 运行时要 patch `basicsr/data/degradations.py`(`functional_tensor`→`functional`,torchvision 新版删了旧模块);③gfpgan 的 PyPI wheel 链有问题装不上模块(与 retina-face 同病),最终源可用
- **权重三坑**:GFPGAN 会从 GitHub 直连下 3 个权重(检测 104M/解析 81.4M/GFPGANv1.4 333M),AutoDL 到 GitHub 只有 ~300KB/s;用 gh-proxy 秒下,放到 `/root/gfpgan/weights/detection_Resnet50_Final.pth`、`/root/.cache/torch/hub/checkpoints/GFPGANv1.4.pth`(解析模型让它自己下)
- **代码坑**:`GFPGANer(model_path=None)` 报 NoneType,必须显式传 v1.4 路径;`cv2.CAP_PROP_POS_FRAMES_FPS` 不存在,是 `CAP_PROP_FPS`
- 修复性能:129 帧中 60 帧 GPU 修复约 1 分钟(0.5s/帧,upscale=1 只修脸不放大)
- 产物 `emv3_sample1_gfp.mp4`(656×880,全图直喂源片修复后):脸清晰度接近裁剪版,方案可行

**定版决策(2026-09-30 用户拍板 ✅):**
- **EchoMimicV3-Flash 定版为正式口型引擎**,双方案并行:②全图直喂+GFPGAN 逐帧修复(不裁剪,适合要全身构图的镜头)/ ③先裁剪再生成(脸部质量上限更高)
- 方案①(全图直喂不修复)效果差弃用
- 定版样品:demo/output/emv3_sample1_gfp.mp4(方案②)、emv3_sample2_crop.mp4(方案③)

**清理收尾(23:00 左右,开机状态下执行):**
- 删:MuseTalk 权重 5.6G + musetalk env 7.2G + lp env(EchoMimicV2 用)6.4G + fix_out/fix_frames.py/req_mt.txt + EMV3 旧样品输出和诊断图
- 本地:scripts/emv2_req5.sh 删除,gen_realistic_character.py / demo9_lipsync.py 注释改指 V3
- 磁盘结果:数据盘 73→61G(剩 40G),系统盘 18→11G(剩 20G);CosyVoice 全套原样保留
- 服务器现存:EchoMimicV3 全套(repo+27G 权重+emv3 env 8.2G+GFPGAN)、CosyVoice 全套(env 26G 数据盘+CosyVoice2-0.5B 5.3G)、9页 v2 音频(pages/ 21M)、形象参考图(assets/)

**待办:** 9 页批量(长音频 ~5s/段分段生成+拼接,按镜头选方案②或③)→ demo9 合成(长音频按 ~5s/段分段生成+拼接, timings_v2)〔历史:已由 studio/pipeline.py ④⑤⑥ 实现〕
