# 服务器运维实录(4090 实例)

> 记录服务器"有什么、缺什么、东西在哪、哪些坑踩过"。每次动过服务器/发现新情况,更新此文档。
> 实例配置与地址见 `config.json → server`;连接靠本机 `~/.ssh/id_ed25519` 密钥,无密码。

## 实例概况(2026-10-02 核验)

| 项 | 状态 |
|---|---|
| 主机 | connect.nmb1.seetacloud.com:23278(AutoDL,root) |
| 数据盘 | /root/autodl-tmp(50G,已用 42G,余 8.5G) |
| GPU | 4090;无卡开机时 nvidia-smi 显示 No devices 属正常 |
| conda 环境 | base / cosyvoice(实体在 autodl-tmp/envs/cosyvoice,miniconda3 下是软链) / emv3 |
| 重启注意 | **AutoDL 重启后 SSH 端口可能变化**,变了改 config.json → server.port |

## 数据盘目录结构(/root/autodl-tmp/,2026-10-02 实测)

> 记这里就是为了防上次的乌龙:删除任何目录前先对照本表确认它没被现行链路引用。

### 现行在用(删了 pipeline 就瘫)

| 目录/文件 | 大小 | 用途 |
|---|---|---|
| EchoMimicV3/ | 24G | ⑤口型:repo/ 推理代码 + weights/ 权重 + input_xingxiang.png 参考图 |
| envs/ | 11G | cosyvoice conda 环境(实体,miniconda3 下是软链) |
| CosyVoice2-0.5B/ | 5.3G | ④克隆:CosyVoice2 模型权重 |
| CosyVoice/ | 7M | ④克隆:CosyVoice 代码(曾误删,setup_cosyvoice.sh 自愈) |
| gfpgan/ | 186M | ⑤ 口型修复 |
| pages/ | 21M | 页音频 v2_pXX.wav + _voices.md5 稿件指纹 |
| lipsync_out/ | 26M | ⑤口型产物 pXX.mp4 / opening.mp4 |
| run_jobs.py + patch_infer_jobs.py + batch_emv3_v2.py | — | ⑤批量口型(pipeline 自动比对上传,勿手改) |
| clone_pages.py / setup_cosyvoice.sh | — | ④克隆/自愈(pipeline 自动上传) |
| emv3_jobs.json / emv3_batch/ | 44M | ⑤任务清单+中间产物 |
| voice_ref.wav | 1.9M | ④克隆参考音 |
| assets/ | 6.7M | 服务器侧参考图等 |
| CLIP/ | 15M | EMV3 依赖 |

### 历史残留(不再被现行链路引用,腾空间时可删,删前 grep 确认)

| 目录/文件 | 大小 | 说明 |
|---|---|---|
| whisper_cache/ | 1.5G | 旧链路 whisper 转写缓存(现行文字稿走 assets/ref_prompt.txt) |
| torch_cache/ pipcache/ | ~470M | pip/torch 下载缓存,可清 |
| clone_test.py / clone_zero_shot.py / clone_v2_zs*.wav | ~3M | 旧克隆脚本与试音(现行=clone_pages.py) |
| voices.txt / voices_v2.txt / voice_ref_v2.wav | — | 旧稿件/参考音(现行由 pipeline 从本地上传) |
| emv2_p00_v*.log / emv3_run*.log / emv3_*download.log / gfp_*.log / run_jobs*.log / watchdog.log | — | 历史运行日志 |
| dl_emv3.sh / dl_emv3_base.sh / install_emv3.sh / req_emv3.txt / fix_frames.py / gfp_case.sh / wd.sh / __pycache__ | — | 历史安装/辅助脚本(emv3 环境已装好,不需要重跑) |
| emv3_base_download 相关 | — | EMV3 base 权重下载残留 |

### 系统侧

- /root/miniconda3/envs/emv3:torch 2.4.1+cu121(⑤推理环境)
- /root/miniconda3/envs/cosyvoice:软链 → /root/autodl-tmp/envs/cosyvoice
- 磁盘:50G 数据盘,用 42G 余 8.5G(2026-10-02)



## 关键资产位置(全部在 /root/autodl-tmp/ 下)

| 资产 | 路径 | 说明 |
|---|---|---|
| CosyVoice 代码 | CosyVoice/ | **曾被我清理误删(2026-10-02 发现),已用 studio/server_scripts/setup_cosyvoice.sh 重新拉回**;import 验证通过 |
| CosyVoice2 模型权重 | CosyVoice2-0.5B/(5.3G) | clone_pages.py 用 |
| EMV3-Flash | EchoMimicV3/(权重 weights/、repo/、参考图 input_xingxiang.png) | ⑤口型用 |
| GFPGAN | gfpgan/ | 口型修复 |
| emv3 conda 环境 | /root/miniconda3/envs/emv3(torch 2.4.1+cu121) | run_jobs.py / infer_jobs.py |
| cosyvoice conda 环境 | envs/cosyvoice(python3.10) | clone_pages.py 用,torchaudio 可用 |
| 页音频目录 | pages/ | v2_pXX.wav=克隆音;_voices.md5=稿件指纹 |
| 口型产物 | lipsync_out/ | pXX.mp4 / opening.mp4 |
| 批量口型脚本 | run_jobs.py + patch_infer_jobs.py + batch_emv3_v2.py | pipeline ⑤ 自动打补丁再启动 |

## 乌龙与教训(防重蹈)

1. **2026-10-02:CosyVoice 代码被误删**——前次会话腾空间清理时执行
   `rm -rf /root/autodl-tmp/CosyVoice`(连同 env 内嵌包源),只留了权重,导致 ④ 克隆瘫痪。
   教训:**清理前必须 grep 引用(脚本/配置里是否还有路径指向它)**;可再生的代码库删除前要记录拉取方式。
   现在自愈脚本 `server_scripts/setup_cosyvoice.sh` 已固化,pipeline ④ 每次运行自动检测补拉。
2. **服务器脚本以本地为准**:`studio/server_scripts/` 是唯一真源,每次 pipeline 运行比对 md5 自动上传;
   不要在服务器上手改脚本(会被覆盖)。
3. **旧稿/旧音频必须清**:`pipeline.py → sync_inputs()` 对稿子+参考音+参考转写+参考形象做联合指纹
   (存 `/root/autodl-tmp/_inputs.md5`),任一变化自动删服务器上全部输入与口型中间产物
   (pages/、voice_ref、ref_prompt、assets、lipsync_out、emv3_batch 等),再由各步骤全量重传。
   输入管理只认这段代码,不允许再手工 ssh 清理。
4. **旧实例残留**:本机 .ssh/known_hosts 里 nmb2 等旧实例指纹属历史遗留,无害;ssh config 里 `autodl` 别名指向旧机(不用管)。
5. **2026-10-03:口型批任务整批崩溃(音频零头段)**——`split_audio` 切段后尾段仅 0.096s,
   pyloudnorm 响度统计要求音频 >0.4s,`infer_jobs.py` 抛
   `Audio must have length greater than the block size`,phase1 全批中止(已跑 44 分钟,靠 DONE 跳过续跑)。
   修复:`server_scripts/batch_emv3_v2.py` 切分时尾段 <0.5s 自动垫静音;同时修掉 `run_jobs.py`/`batch_emv3_v2.py`
   写死 `range(9)` 的页数(改数据驱动,以 pages/v2_pXX.wav 实际存在为准)。
   两脚本已本地留底,pipeline ⑤ 每次运行 md5 比对自动上传。
   **教训:所有只在服务器上的脚本必须留底 `server_scripts/`,无卡开机即可取回,别等要用时才发现没备份。**
6. **2026-10-03:口型中间产物按音源加指纹**——此前换配音音色(alex↔clone)后重跑,`split_audio`
   见同名 seg 文件就跳过,旧音色的切段被复用,口型与声音错配(预览段暴露此问题)。
   修复:`run_jobs.py` 对每页 v2_pXX.wav 记 md5 指纹(`emv3_batch/pXX/_audio.md5`),
   音源一变自动清该页切段/中间产物/成品重做。与 ④ 的稿件指纹同一机制。
   **教训:任何缓存产物必须带"输入变了就作废"的指纹;给用户预览前先核对素材是哪一批次的。**

## 每次开机自检清单(pipeline 已自动,人工排查用)

```bash
# 1. 关键目录
ls -d /root/autodl-tmp/{CosyVoice,CosyVoice2-0.5B,EchoMimicV3,envs/cosyvoice,gfpgan,pages,lipsync_out}
# 2. CosyVoice import(失败→ bash setup_cosyvoice.sh)
/root/autodl-tmp/envs/cosyvoice/bin/python -c "import sys;sys.path[:0]=['/root/autodl-tmp/CosyVoice/third_party/Matcha-TTS','/root/autodl-tmp/CosyVoice'];from cosyvoice.cli.cosyvoice import CosyVoice2;print('IMPORT_OK')"
# 3. emv3 torch
/root/miniconda3/envs/emv3/bin/python -c "import torch;print(torch.__version__)"
# 4. 磁盘(紧张时先删 pages/*.wav 旧稿产物与 lipsync_out,均可由 pipeline 重建)
df -h /root/autodl-tmp
```
7. **2026-10-03:opening 推理裸调 infer_jobs.py 报"缺参数"+轮询不容忍掉线**——⑤b 直接调
   `infer_jobs.py` 没先跑 `patch_infer_jobs.py`(EMV3_JOBS 支持靠补丁),argparse 直接退出;
   改为与 ⑤ 同规矩:补丁前置 + nohup 后台 + 轮询。且轮询里任何一条 ssh 失败(服务器瞬断/掉线)
   就 sys.exit 杀全流程;新增 `srv_wait_recover()`(两处轮询:⑤/⑤b),失联等恢复,超 30 分钟才判死。
   **教训:长任务轮询必须容忍网络抖动;依赖环境变量的调用方式,其前置补丁必须在每个入口都执行。**
