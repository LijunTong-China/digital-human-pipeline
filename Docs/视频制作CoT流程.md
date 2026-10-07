# 视频制作定稿流程(CoT 执行链,2026-09-30 定版)

> 【2026-10-02 标识·历史文档】本文为 09-30 时点的 demo/ 时代执行链,**其中命令指向 demo/ 路径均已随 demo 废弃失效,不可照抄**。现行七步链固化在 `studio/`(设计来源 `studio/README.md`):②由 nb_auto.py 全自动、③演播稿 LLM 动态生成、④双轨(benjamin 本地 TTS / clone 服务器克隆)、⑤b 开场白、board 版式、MinerU 解析图片型 PDF、GPU 自动等待/关机均为本文所无的现行能力。保留本文以记录当时的链路设计与节点结构。
> 线性执行,上一步产出 = 下一步输入。所有参数均为定版值,照抄即可。〔历史〕

```
①选题 → ②PPT → ③演播稿 → ④克隆配音 → ⑤口型生成 → ⑥合成 → ⑦交付
```

---

## ① 选题与源文档
- 输入:无
- 动作:`python demo/nb_source_gen.py`(三方向轮换选题,自动查重)
- 产出:选题名、源文档 md、NotebookLM 粘贴用提示词 txt
- 通过标准:源文档内容完整

## ② NotebookLM 出 PPT〔历史:现行 nb_auto.py 全自动:0来源自检、骨架提示词键盘注入、稍后生成排队+补收;来源=LLM 生成的 source_text.txt〕
- 输入:源文档 md
- 动作:浏览器自动化 → 新建笔记本 → 粘贴文字作为来源 → Studio 生成演示文稿 → 下载 PDF
- 产出:`demo/input/nb_slides.pdf`(9 页〔历史:现行 n_pages=auto,10~14 页〕)

## ③ 演播稿
- 输入:9 页幻灯片内容
- 动作:按页写讲解词,存 `demo/input/voices_v2.txt`;口语化(短句/语气词/感叹号/反问),每页约 12~18 秒〔历史:现行 140~220 字/页(约 35~55 秒)〕
- 产出:9 页演播稿文本〔历史:现行 n_pages=auto,10~14 页〕

## ④~⑥ 一键执行(pipeline.py 总控)

- **动作(本地):** `python demo/pipeline.py`〔历史:现行 python studio/pipeline.py〕 = ④克隆配音 → ⑤口型生成 → ⑥合成,一条命令到成片
  - 分步可跑:`python demo/pipeline.py lipsync`(断点续跑)/ `compose` / `shutdown`
- 节点细节:

### ④ 克隆配音(pipeline.py voice)〔历史:现行④=clone_pages.py 数据驱动读 voices.txt;预置音色走本地 TTS;无 timings_v2.json〕
- 上传 `voices_v2.txt` → 服务器 `clone_zero_shot.py`(zero_shot + voice_ref_v2)→ 下载 `clone_pXX.wav` × 9〔历史:现行 n_pages=auto,10~14 页〕 + `timings_v2.json`

### ⑤ 口型生成(pipeline.py lipsync)
- 服务器 `run_jobs.py` 常驻批量:每页静音点切 ≤5s 段 → EMV3-Flash 循环推理(8步/TeaCache/seed43/768²/≤129帧)→ GFPGAN(方案②)→ 拼接
- 每 5 分钟轮询,9 页齐后自动下载到 `demo/output/demo8/lipsync/`
- 场景分流:特写镜头换 `形象_crop768.png`(方案③),全景用全图(方案②)〔历史:现行统一形象图(白底形象_white.png+白色键控),无镜头分流〕

### ⑥ 合成(pipeline.py compose)
- 本地 `demo9_lipsync.py`〔历史:现行 compose.py 三版式,产物 output/final/final_video.mp4〕:幻灯片 + 字幕(timings_v2)+ 口型小窗 + 克隆音 → `demo/output/demo9_lipsync.mp4`

## ⑦ 交付
- 确认成片 → `python demo/pipeline.py shutdown` 关 GPU 实例(推理才开卡,用完即关〔历史:现行 wait_gpu 自动等待+自动关机〕)

---

## 步骤间依赖与交接明细(谁用谁的产出、怎么交接)

> 原则:**每一步的产出都是下一步的直接输入,文件名和落点固定,不需要人工改名**。
> 本地↔服务器的搬运全部由 `pipeline.py` 自动完成(上传/下载/重命名一步到位)。

### ①→② 选题 → PPT
| 交接物 | 由①产出 | ②如何使用 |
|---|---|---|
| 源文档 md | `demo/input/nb_source/topic_<slug>.md` | 复制全文,**粘贴文本**进 NotebookLM 当来源(md 文件上传会被分类器拦,必须粘贴) |
| 提示词 txt | `demo/input/nb_source/topic_<slug>_nb_prompt.txt` | 粘贴到 Studio 自定义提示词框,控制幻灯片风格 |

### ②→③ PPT → 演播稿
| 交接物 | 由②产出 | ③如何使用 |
|---|---|---|
| 幻灯片 PDF | `demo/input/nb_slides.pdf` | ③逐页看图写词(每页一段);⑥合成时按页转 PNG 当背景 |

### ③→④ 演播稿 → 克隆配音
| 交接物 | 由③产出 | ④如何使用(pipeline.py 自动处理) |
|---|---|---|
| 演播稿 | `demo/input/voices_v2.txt`(9 段,空行分隔) | pipeline 上传到服务器 `/root/autodl-tmp/pages/voices_v2.txt`;clone_zero_shot.py 按空行切段逐页合成 |
| 参考音频 | `demo/input/voice_ref_v2.wav`(服务器 `/root/autodl-tmp/voice_ref_v2.wav` 常驻) | zero_shot 参考音,连同脚本内写死的文字稿一起用〔历史:现行参考音 assets/voice_ref.wav,文字稿 assets/ref_prompt.txt(config→paths.ref_prompt)〕 |
| **④产出** | `pages/v2_pXX.wav` × 9 + `pages/timings_v2.json`〔历史:现行字幕取演播稿原文按字数比例铺,无 timings 文件〕 | ↓ |

### ④→⑤ 克隆音 → 口型生成
| 交接物 | 由④产出 | ⑤如何使用(pipeline.py / run_jobs.py 自动处理) |
|---|---|---|
| 克隆音 | 服务器 `pages/v2_pXX.wav` | run_jobs.py 读每页 wav,**按静音点切成 ≤5s 段**(`emv3_batch/pXX/seg_XX.wav`)——切点选在 ±0.6s 内能量最低处,保证口型段间不断句 |
| timings_v2.json〔历史:现行字幕取演播稿原文按字数比例铺,无 timings 文件〕 | 同上下载后 pipeline 存为 `demo/output/demo8/timings_v2.json` | ⑤不用,**留给⑥做字幕** |
| 形象图 | 服务器 `EchoMimicV3/input_xingxiang.png`(全图,方案②)常驻;特写镜头换 `形象_crop768.png` | 每段推理的参考图——同一张图+同一 seed 43,保证各段长相一致 |
| **⑤产出** | `lipsync_out/pXX.mp4`(段已拼接、已 GFPGAN) | ↓ |

### ⑤→⑥ 口型视频 → 合成
| 交接物 | 由⑤产出 | ⑥如何使用(pipeline.py 下载时自动重命名) |
|---|---|---|
| 口型视频 | 服务器 `lipsync_out/pXX.mp4` | 下载并**改名**为 `demo/output/demo8/lipsync/lipsync_pXX.mp4`(demo9 的固定输入名) |
| 克隆音 | ④已下载为 `demo/output/demo8/clone_pXX.wav` | 每页音频轨,demo9 按页对齐口型小窗和时长 |
| 字幕时间轴 | `timings_v2.json`(④产) | demo9 读它把每句字幕对到全片时间轴;缺某页则按字数比例兜底 |
| 讲解词缓存 | `demo/output/demo8/voices.json`——**由 pipeline 在④自动生成**(读 `voices_v2.txt` 按空行分段),不是手工产物 | demo9 取每页文本做字幕兜底分句 |
| **⑥产出** | `demo/output/demo9_lipsync.mp4` | ↓ 成片 |

### ⑥→⑦ 成片 → 交付
| 交接物 | 说明 |
|---|---|
| 成片 | `demo/output/demo9_lipsync.mp4`,用户验收 |
| 关机 | 验收通过后 `python demo/pipeline.py shutdown`:**发指令 → 等 60s → SSH 探活验证失联**,失败重试,最多 3 次;3 次仍在线则报错提示去 AutoDL 控制台手动关。所有中间产物留服务器盘可复跑,本地留成片+素材 |

### 依赖链速查(一图流)

```
voices_v2.txt ─上传→ clone_zero_shot ─→ v2_pXX.wav ─┬─切5s段→ run_jobs ─→ lipsync_out/pXX.mp4 ─改名→ lipsync_pXX.mp4 ─┐
                                                     └→ timings_v2.json〔历史:现行字幕取演播稿原文按字数比例铺,无 timings 文件〕 ────────────────────────────────────────────┼─→ demo9 ─→ demo9_lipsync.mp4
nb_slides.pdf ──────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 前置资产(一次性准备,不属于任何步骤产出,已全部就位)

| 资产 | 位置 | 用在哪 |
|---|---|---|
| 参考音频 voice_ref_v2.wav(21.6s) | 本地 `demo/input/` + 服务器 `/root/autodl-tmp/` | ④ zero_shot 参考音 |
| 参考音文字稿 | 写死在 clone_zero_shot.py 内〔历史:现行参考音 assets/voice_ref.wav,文字稿 assets/ref_prompt.txt(config→paths.ref_prompt)〕 | ④ |
| 形象图(全图/裁剪版)〔历史:现行必需=assets/形象_white.png 白底 768²〕 | 服务器 `EchoMimicV3/input_xingxiang.png` / 本地 `demo/input/形象_crop768.png` | ⑤ 参考图 |
| 服务器脚本 | clone_zero_shot.py、run_jobs.py、infer_jobs.py(常驻版) | ④⑤ |
| conda 环境 | cosyvoice(emv3 同理) | ④⑤ |
| GFPGAN 权重 | `/root/.cache/torch/hub/checkpoints/GFPGANv1.4.pth` 等 | ⑤ |

## 固化在流程里的定版参数(无需再决策)

| 环节 | 定版值 |
|---|---|
| 声音模式 | zero_shot + voice_ref_v2.wav(21.6s)〔历史:已废〕 |
| 参考文字稿 | whisper medium 转写,已存脚本内〔历史:已废〕 |
| 口型引擎 | EMV3-Flash,8 步蒸馏 + TeaCache(0.1/skip5)+ Flow_Unipc |
| 生成参数 | seed 43 / guidance 6.0 / audio_guidance 3.0 / audio_scale 1.0 / bfloat16 |
| 分段 | ≤5s/段,静音点切割,≤129 帧 |
| 环境 | 服务器 conda:cosyvoice + emv3;长任务 nohup |
| 磁盘 | 无卡做下载/装依赖;数据盘保持 <80G |
