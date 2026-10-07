# 视频流水线 · 正式版设计文档

> 本文档是唯一设计来源。代码必须服从文档;改需求先改文档再改代码。
> 所有可变参数一律进 `config.json`,代码中禁止写死路径/尺寸/音色/页数等。
> 服务器资产位置/坑/自检清单见 `SERVER.md`;动过服务器必须同步更新它。

## 1. 总体流程(七步链,①②③ 动态生成)

```
①选题+源文档 → ②NotebookLM 出 PPT → ③动态演播稿 → ④配音 → ⑤口型 → ⑥合成 → ⑦交付关机
```

- ①③ 由 `content.py` 用 LLM 动态生成(选题查重、源文档、按 PPT 页逐页写演播稿)
- ② NotebookLM 无公开 API:由 Claude 会话用浏览器自动化执行(源文档+提示词生成后,
  在 NotebookLM 生成演示文稿并导出 PDF 到 `assets/slides.pdf`);已有 PDF 则直接复用
- ④⑤⑥⑦ 由 `pipeline.py` 总控,一条命令 `python studio/pipeline.py` 到成片
- 分步可跑:`python studio/pipeline.py content|voice|lipsync|opening|compose|shutdown`
- `n_pages` 默认 `auto`:以演播稿分段数为准(与 PPT 页数一致),不再写死

## 2. 配置驱动(config.json 全量参数)

| 分组 | 键 | 说明 |
|---|---|---|
| 内容 | `content.*` | 选题方向轮换、话题缓存、逐页演播稿字数范围(见 §1.5) |
| 声音 | `voice` | `clone`=自己的声音(服务器 CosyVoice 克隆);`alex`/`benjamin`/`charles`/`david`=预置男声(本地 API 合成,免 GPU) |
| 声音 | `tts_api.*` | TTS 服务 base_url/model/音色前缀(读 docker/.env 的 key) |
| 结构 | `layout` | `voiceonly` / `intro` / `board`(见 §3) |
| 结构 | `intro.max_sec` | 开场白时长**软限**(秒):超限最多加速 `intro.speed_max`,不再硬压 |
| 结构 | `intro.speed_max` | 开场白加速上限倍数(默认 1.2) |
| 结构 | `intro_text` | 开场白文案;`auto`=LLM 3 候选自评选优(喂主题+第一页讲解词,字数按时长反推) |
| 画面 | `canvas.*` | 画布宽高、幻灯片底边、小窗宽/边距、键控色/容差 |
| 画面 | `board.*` | 讲课模式:PPT 占宽比、倾斜角、形象列宽度 |
| 字幕 | `subtitle.*` | 每条最大字数(原版节奏)、字号、底边距 |
| 节奏 | `page_gap` | 页间静音秒数 |
| 服务器 | `server.*` | host/port、数据盘根、conda python、服务器脚本路径 |
| 产物 | `paths.*` | 素材目录、工作目录、输出文件名 |
| 页数 | `n_pages` | `auto`(默认,按演播稿分段数)或固定数字 |

## 1.5 内容生成(content.py,①②③)

### ①选题 → 结构规划(骨架由提示词直接驱动 NotebookLM)

拿到主题后**先规划**,分两步:

1. **选题**:LLM 按 `content.directions` 轮换方向自主命题(话题查重缓存,不重复)
2. **PPT 结构规划**(`content.plan.*`):LLM 产出一页页的结构方案 JSON——
   - 页数落在 `plan.min/max_pages`(默认 10~14 页,demo 的 8 页信息量不够)
   - 每页:标题 + 3~5 条具体要点 + 本页"钩子"(反常识/痛点/金句)
   - 叙事主线强制"引人深思":现象反差 → 为什么会这样 → 背后机制 → 数据/案例佐证
     → 反直觉的深层结论 → "看完可以怎么做"行动清单
   - 要点必须具体:带数字、版本、案例名,禁止"赋能/提升效率"式空话

**不写源文档**:规划出的骨架(页数/逐页标题/要点/钩子/叙事主线)直接**内嵌进
NotebookLM 提示词**,NotebookLM 按提示词执行生成 PPT——骨架由提示词下达,
血肉由 NotebookLM 扩充。规划 JSON 存 `output/work/outline.json`,
提示词存 `output/work/outline.json` 同目录的 `nb_prompt.txt`。

### ②PPT(NotebookLM,浏览器自动化 nb_auto.py)

- 流程:打开 NotebookLM(专用已登录 profile)→ 新建笔记本 →
  **添加来源**(`复制的文字` 粘贴 `output/work/source_text.txt`,见下)→
  Studio"演示文稿"对话框 → 选格式 → 填入 `output/work/nb_prompt.txt` 的骨架提示词 →
  立即生成 → 轮询等 Studio 卡片 → 卡片 ⋮ 菜单"下载 PDF"→ `assets/slides.pdf`
- **必须有 ≥1 个来源**:0 来源提交会被**静默丢弃**(弹框照常关闭但不生成)。
  来源=LLM 基于 outline 生成的资料文章(`content.py → work/source_text.txt`,
  "血肉"),骨架提示词负责结构;弹框显示"0 个来源"时拒绝点生成(自检终止)
- 实测坑(均已固化进代码):
  - 演示文稿弹框的 textarea 用 `fill()` 可写入;**来源粘贴的 textarea 必须用
    原生 value setter + input 事件**,否则值被 Angular 丢弃、「插入」恒禁用
  - 「演示文稿」按钮必须限定在 Studio 面板内点击,否则会误点来源/搜索区同名入口
  - 提交后浏览器不能关,轮询刷新等卡片(生成约 3~10 分钟);
    下载入口在**卡片自身 ⋮ 菜单**(无需打开查看器)
- **服务不可用容错**:提交前悬停"立即生成"检测提示,
  若出现"目前无法使用,我们正在努力让其恢复正常"等不可用文案 → 记日志
  (`output/work/nb_status.log`)并**终止流程**(暂缓生成,不空等、不重试烧额度)
- 产物卡片超时未出现 → 记日志终止;`assets/slides.pdf` 已存在则直接复用
  (换选题删掉它即可)
- 全程 Playwright 驱动(`nb_auto.py`),无人工;由 content 步骤自动调起;
  参数在 `config.json → nb` 节(profile/chrome/cdp 端口/headless/卡片超时/轮询间隔)

### ③动态演播稿

- 读取 `assets/slides.pdf` 每一页文字,LLM 逐页扩写成口播讲解词
  (字数在 `content.script_min/max_chars` 内,口语化、忠于该页要点),
  空行分页写入 `assets/voices.txt`;页数随 PPT 动态,代码不写死
- **图片型 PDF 自动解析**(NotebookLM 导出即此类):优先 **MinerU API** 整体解析
  (env `MINERU_API_KEY`,`content_list.json` 按 page_idx 归并每页文字);
  失败自动降级:视觉 LLM(env `LLM_VISION_MODEL`)→ 本地 OCR
  (paddleocr/easyocr/tesseract,按 `content.ocr` 顺序);页面 PNG 缓存 `work/slides_png/`
- 前置条件:`docker/.env` 提供 `LLM_API_KEY / LLM_BASE_URL / LLM_MODEL / MINERU_API_KEY`

## 3. 视频结构三模式(layout)

### 3.1 voiceonly —— 最省
- 全程 **PPT 全屏 + 字幕 + 声音**,形象永不出现,不需要 GPU
- 产物链:演播稿 → TTS/克隆音频 → 合成

### 3.2 intro —— 开场白模式
1. **开场白段**:形象出镜满高居中讲开场白,配字幕+声音,**不播 PPT**
   - 开场白时长 `intro.max_sec`(默认 12s)是**软限**:超限最多加速 `intro.speed_max`
     (默认 1.2 倍,2026-10-04 定版;1.5 倍声音发飘弃用),再超就接受超时成片
   - **文案提质三件套(2026-10-04)**:①生成时喂主题+正片第一页讲解词(钩子对着
     正片内容写);②一次 3 候选,LLM 自评(钩子/口语度/衔接)选优;③字数按时长
     反推(≈4.5字/秒 × max_sec × 加速余量),天然少触发 atempo。缓存
     `work/opening_text.txt`,重写文案删它
   - 开场白口型 = 单段 EMV3 推理(≤129 帧 ≈5.2s),只此一段用 GPU
     ⚠️ 已知限制:音频长于 5.2s 时,超出部分形象定格不动嘴(口型单段上限所限)
2. **正片段**:PPT 全屏 + 字幕 + 声音,形象不再出现(省 GPU/生成时间)
- 产物链:开场白音频+口型 → 各页音频 → 合成

### 3.3 board —— 老师讲课模式
- PPT 卡片占左侧 `board.slide_ratio` 宽,**绕竖轴向内透视旋转**(`board.persp`:右缘向纵深退、变短,像门板往里推开;从上往下看是逆时针)
- `board.fit: true` = 整页 PPT 完整放进画面不裁内容;`slide_left`/`slide_top` 控制卡片位置(缺省垂直居中)
- **形象全程满高站右侧**(`gap_right` 调边距),像老师站在幕布旁讲课
- 全程 形象+声音+字幕;每页口型视频(GPU)。`persp=0` 时退回 2D 倾斜(`board.angle`)

## 4. 声音配置(voice)

| 取值 | 来源 | GPU | 用途 |
|---|---|---|---|
| `clone` | 服务器 CosyVoice zero_shot + voice_ref(自己的声音) | 需要 | 各页+开场白 |
| `alex/benjamin/charles/david` | SiliconFlow CosyVoice2 预置音色,本地合成 | 不需要 | 各页+开场白 |

- 页音频统一命名 `voice_pXX.wav` 落工作目录;clone 模式兼容迁移自 demo 的 `clone_pXX.wav`
- ⑤ 口型切段需要服务器上有各页音频:预置音色模式下,pipeline 本地合成后**自动上传**为服务器 `pages/v2_pXX.wav`
- 开场白在 `clone` 模式下走 SiliconFlow 克隆 API(注册参考音一次,voice id 缓存复用)

## 5. 字幕规格(原版节奏)

- 文本来源:**演播稿原文**(与语音一致;禁用 whisper 转写,错字多)
- 分条:标点切句 + 长句按 `subtitle.max_chars`(默认 18)切段,一条一行
- 时间轴:页内按字数比例线性铺;整页时间 = 页音频时长 + `page_gap`
- 渲染:微软雅黑,字号/底边距由 `subtitle.*` 配置

## 6. 口型生成(⑤,服务器)

- EMV3-Flash:seed 43 / 8 步蒸馏 / TeaCache / ≤5s 静音点切段 / ≤129 帧(与定版参数一致)
- 参考图:优先 `assets/形象_white.png`(白底)自动上传替换,并在工作目录落 `use_whitekey` 标记 → 合成时白色键控抠图
- 每次启动前自动重打 `patch_infer_jobs.py`(防实例拷贝后补丁损坏;补丁锚点=最后一个 `with torch.no_grad():`)
- 断点续跑:服务器/本地都按"缺哪页补哪页"

## 7. 可靠性

- **GPU 生命周期(pipeline 自动)**:④⑤⑤b 步骤开头先快连(`connect_timeout_sec`,10s);连不上 → 打印「请到控制台开机」并**等待用户回车确认** → 5s 轮询至 ssh 就绪立即开干;跑完最后一个 GPU 步骤(lipsync/opening)**自动关机**,不留空转实例
- scp 自动重试(3 次/30s);实例重启端口变更只改 `config.json → server.port`
- ⑦ 关机:发指令 → 60s → SSH 探活验证失联,失败重试,最多 3 次
- 建议服务器侧看门狗(可选):9 页齐后宽限 30 分钟自动关机,防失联空烧

## 8. 目录结构

```
studio/
  README.md          本文档
  config.json        全量配置
  content.py         ①选题+源文档 ③动态演播稿(②PPT 由浏览器自动化通道产出)
  pipeline.py        总控 ④⑤(⑥⑦)
  compose.py         ⑥ 合成(读配置,三布局)
  avutils.py         音视频/LLM 公共工具
  assets/            slides.pdf / voices.txt(动态生成,已存在则复用)+ 参考音/形象图
  output/            工作目录+成片(work/ 中间产物,final/ 成片)
```

## 9. 前置资产

| 资产 | 来源 |
|---|---|
| 演播稿 voices.txt(空行分页) | ③ 动态生成;已存在则复用 |
| 幻灯片 slides.pdf | ② NotebookLM 产出;已存在则复用 |
| 参考音 voice_ref.wav | 一次性准备(clone 模式必需) |
| 形象白底图 形象_white.png(768²,纯白 RGB 背景) | 一次性准备(intro/board 模式必需) |
| docker/.env | LLM_API_KEY/LLM_BASE_URL/LLM_MODEL、ASR_API_KEY/ASR_BASE_URL |
| 服务器脚本 clone_zero_shot.py / run_jobs.py / patch_infer_jobs.py | server.paths 指定 |

## 10. 执行命令速查(照抄即跑)

### 10.1 本地执行(Windows,项目根 `E:\selfProject\cloneAIProject`)

```bash
# 全流程(④配音→⑤口型→⑥合成→⑦关机,一条命令到成片)
python studio/pipeline.py

# 分步执行(每步幂等,断点续跑:缺哪页补哪页)
python studio/pipeline.py content    # ①选题+源文档 ②NotebookLM PPT ③动态演播稿
python studio/pipeline.py voice      # ④配音(本地或服务器克隆)
python studio/pipeline.py lipsync    # ⑤批量口型(需 GPU 实例开机)
python studio/pipeline.py opening    # ⑤b 开场白口型(intro/board 布局才需要)
python studio/pipeline.py compose    # ⑥合成(本地,不需要 GPU)
python studio/pipeline.py shutdown   # ⑦关机(防空烧)
```

- 前置:`docker/.env` 提供 `LLM_API_KEY / LLM_BASE_URL / LLM_MODEL / MINERU_API_KEY`
- GPU 步骤(voice/lipsync/opening)开头自动快连,连不上会提示「请到控制台开机」并等待回车;
  跑完最后一个 GPU 步骤自动关机
- 实例重启换端口:只改 `config.json → server.port`(当前 connect.nmb1.seetacloud.com:23278)

### 10.2 服务器侧人工排查(仅 pipeline 出问题才需要 ssh 上去看)

> 与 `SERVER.md`「每次开机自检清单」保持一致,以那边为真源;此处是执行入口速记。

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

> 详细运维实录(目录结构/历史残留/乌龙与教训)见 `SERVER.md`。

### 10.3 各阶段文件上传/下载分配(2026-10-03 按源码核实)

**全局前置(sync_inputs)**:对本地 `voices.txt + voice_ref.wav + ref_prompt.txt + 形象_white.png`
做联合 md5,存服务器 `_inputs.md5`。任一变化 → 自动删服务器
`pages/ lipsync_out/ emv3_batch/` 及本地旧 clone 音频/口型,再由各步骤全量重传。

| 阶段 | 上传(本地→服务器) | 下载(服务器→本地) |
|---|---|---|
| ④ voice(clone) | `voices.txt`、`voice_ref.wav`、`ref_prompt.txt`(每次覆盖);`clone_pages.py`、`setup_cosyvoice.sh`(md5 不同才传);CosyVoice 代码缺失自愈 | 各页 `v2_pXX.wav` → `work/clone_pXX.wav`(缺哪页下哪页) |
| ④ voice(预置音色) | 本地 TTS 合成,**仅 board 布局**才把页音频传为 `pages/v2_pXX.wav` | 无 |
| ⑤ lipsync(board) | 白底参考图 → `input_xingxiang.png`;`run_jobs.py`/`batch_emv3_v2.py`/`patch_infer_jobs.py`(md5 不同才传);打补丁后 nohup `run_jobs.py` | 各页 `pXX.mp4` → `work/lipsync/lipsync_pXX.mp4` |
| ⑤b opening(intro) | 白底参考图;本地合成的开场白音频 → `pages/opening.wav`;`opening_job.json`(单任务清单);开场白音频 md5 存 `_opening_audio.md5`,变化自动删旧 `opening.mp4` 重推理 | `opening.mp4` → `work/lipsync/lipsync_opening.mp4` |
| ⑥ compose | **纯本地**,零上传 | 无 |

- 所有服务器脚本以本地 `studio/server_scripts/` 为唯一真源,md5 比对自动上传,服务器上手改会被覆盖
- 开机提醒(`wait_gpu`)只在三个 GPU 步骤入口触发:`voice(clone)`、`lipsync`、`opening`;
  第一个 GPU 步骤提醒开卡,后续步骤在线即直接干活
- 命令别名:`lipsync`/`opening` 都解析为当前 layout 实际需要的那个口型步骤
  (board→lipsync,intro→opening);`layout=intro` 时若不写口型步骤,compose 因缺
  `lipsync_opening.mp4` 会报错

### 10.4 强制重做细则(缓存指纹与对应命令)

缓存全部带指纹,指纹不变就复用。想强制重做,删对应缓存+指纹戳再跑。

**改了演播稿(voices.txt)**:不用删任何东西,从 `voice` 进,指纹自动作废:

```bash
python studio/pipeline.py voice lipsync compose shutdown
```

- clone 模式:sync_inputs 检测稿件指纹变化 → 自动清服务器 pages/lipsync_out 与本地旧音频,整批重克隆
- 预置音色:每页 md5(音色+文本)比对,只重配变化的页

**稿子没变,但想强制重新出声(重 TTS/重新克隆)**:删缓存+指纹戳(PowerShell):

```powershell
# ① 页配音(预置音色 voice_pXX;clone 音色则是 clone_pXX)
Remove-Item output\work\voice_p*.wav, output\work\voice_p*.md5

# ② 开场白音频
Remove-Item output\work\opening.wav, output\work\_opening.md5

# (可选)重写开场白文案(仅 intro.text=auto 时存在缓存)
# Remove-Item output\work\opening_text.txt

# ③ 重跑
python pipeline.py voice lipsync compose shutdown
```

- Bash 版:`rm output/work/voice_p*.wav output/work/voice_p*.md5` 等(多模式空格分隔);
  PowerShell 的 `rm`=Remove-Item,多模式必须**逗号**分隔,否则 ParameterBindingException
- 服务器开场白口型 opening.mp4 **不用手动清**:新音频字节必与旧的不同,
  `_opening_audio.md5` 指纹不匹配 → 自动删旧口型重推理(pipeline ⑤b)
- ⚠️ TTS 同音色+同文本重合成,结果几乎不变(指纹相同才复用,但服务端对相同输入
  本身就返回近似输出)。想换朗读效果,换 `voice` 或微调文案,光删缓存没用
- 改了素材入口判断:**改内容 → 从 content/voice 跑;没改内容 → 才可用下游分步**。
  只跑下游步骤永远不会重新生成演播稿
