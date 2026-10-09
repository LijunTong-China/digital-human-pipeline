# cloneAIProject —— AI 视频全自动生产流水线

> 一个人、一条命令,从热点到发布的全自动化短视频工厂:
> **抓热点 → 出选题 → NotebookLM 生成 PPT → 写稿 → AI 配音 → 数字人口播 → 合成成片 → 定时发布抖音/小红书**

整个项目没有人工环节。跑通后,每天的内容生产只需要 `python run_all.py`。

---

## 一、这个项目解决什么问题

做一个"AI 讲知识"的短视频账号,传统流程是这样的:

```
选题(刷1小时热点) → 找资料 → 做PPT(1-2小时) → 写口播稿(1小时)
→ 录音/配音(1小时) → 剪辑合成(2小时) → 写文案发布(30分钟)
```

一条视频半天起步,瓶颈全在重复劳动上。本项目的目标:**把这条链全部代码化,
让"一天量产几十条"从口号变成配置文件里的一个数字**。

核心设计决策是**能用成熟平台就不自己造**:

| 环节 | 自己造的方案(已否决) | 最终采用 |
|---|---|---|
| PPT 生成 | python-pptx 自己排版 | NotebookLM(其排版质量远超自研) |
| 口播稿 | 模板填空 | LLM 整篇通写(全局叙事弧线) |
| 声音 | 训练自己的 TTS | CosyVoice2 克隆 / 预置音色 |
| 数字人 | 训练专属形象 | 单张形象图 + EchoMimicV3-Flash 音频驱动口型 |
| 发布 | 平台 API(个人号没有) | CDP 接管真实登录态浏览器,拟人操作 |

## 二、系统架构(五个模块)

```
cloneAIProject/
├── run_all.py                  # 总控:登录保活→热点抓题→视频制作→发布,一条命令
├── studio/                     # 视频制作流水线(核心)
│   ├── pipeline.py             #   七步链总控:④配音→⑤口型→⑥合成→⑦关机
│   ├── content.py              #   ①选题 ③演播稿(LLM 动态生成)
│   ├── nb_auto.py              #   ②NotebookLM 浏览器自动化(出 PPT)
│   ├── compose.py              #   ⑥ffmpeg 合成(画布/抠像/字幕)
│   ├── config.json             #   全量参数,改值即生效
│   └── server_scripts/         #   4090 服务器端脚本(克隆音色/EMV3口型)
├── hotspot-monitor-service/    # 热点监控(FastAPI :8000 + PostgreSQL/pgvector)
│   └── 爬虫借 login-hub 登录态抓抖音创作者视频 → ASR 转写 → LLM 提选题 → 向量去重
├── login-hub-service/          # 多平台登录中心(FastAPI :3459)
│   └── 人工登录一次 + 定时保活,统一供爬虫/发布两个下游接管浏览器
├── publish/                    # 发布模块(抖音/小红书)
│   └── 时间窗/拟人操作/熔断/幂等,五层防风控
├── docker/                     # TTS/LLM 等 API 的 .env
└── Docs/                       # 全部设计文档与踩坑实录(一律不删,横幅标现行/历史)
```

一条命令串起来:`python run_all.py`(详见 [Docs/全链路总控与流程图.md](Docs/全链路总控与流程图.md))。

## 三、特色设计

### 1. 指纹驱动的自愈流水线
每个环节的产物都带 md5 指纹戳:换选题、改稿子、换参考音,下一环节自动检测指纹变化,
把旧产物全部作废重做。**没有"清理缓存"这个手工步骤**——新旧数据永远不会混用
(踩过"旧声音混进新片"的坑之后固化下来的设计)。

### 2. 断点续跑 + NotebookLM 额度保护
`voices.txt` 在就跳过选题/出PPT/写稿直接续跑;NotebookLM 无公开 API,
用浏览器自动化操作,`submit=false` 只填词不提交防误烧额度,额度尽走「稍后生成」
排队,重跑自动补收。

### 3. 不对抗风控,借真实登录态
爬虫和发布都不裸奔:统一从 login-hub 借**真实登录态的浏览器**(人工扫码一次,
后台定时保活)。热点抓取借它打开创作者主页,发布用 CDP 接管同一个浏览器拟人操作。

### 4. 发布端五层防风控(宁可少发,不烧号)
账号体检 → 时间窗(不整点+随机抖动)→ 每日限额 → 拟人操作(逐字输入/暖场浏览/
等待期活动/session 时长控制)→ 熔断+幂等(连败停 3 天,同视频绝不重发)。
所有异常一律 RiskError 停机带截图,**绝不自动重试**。

### 5. 内容质量管线,不是套话机器
- 选题查重缓存,方向池轮换,热点 hint 注入
- PPT 提示词经 AB 实验定版:不锁骨架,只下质量纪律+叙事弧线,血肉由 NotebookLM
  联网检索的真实来源填充(骨架填空式提示词会导致套话 PPT,已弃用)
- 演播稿整篇通写(全局叙事、页间衔接)→ 代码级禁词质检 → LLM 主编审稿,<70 分打回重写
- 开场白文案 LLM 3 候选自评选优

### 6. GPU 用完即走
4090(AutoDL)只在克隆配音/口型推理时开机,步骤间断点续传,
⑦ 用完自动 `shutdown` 三连验证,还有"关门狗"兜底:跑完 GPU 步骤未显式安排关机
就自动补关,不留烧钱的空转实例。

## 四、试错过程(为什么现在是这个样子)

完整记录见 [Docs/方案演进全景图.md](Docs/方案演进全景图.md),这里只讲几个关键岔路口:

### 声音线:instruct 模式全军覆没
CosyVoice2 的 `instruct2` 模式(用指令描述想要的音色)各种指令都会漂移成女声,
全线禁用;`zero_shot` 克隆音色对但韵律平淡(照抄参考音频节奏)——
最终定版:**口语化演播稿 + zero_shot 克隆**,短句、语气词、感叹号、反问,
韵律立刻活了。写稿风格和 TTS 模式是配套的,这是一个隐藏耦合。

### 形象线:卡通脸是死胡同
最初想用即梦生成 3D 卡通娃娃脸,MuseTalk/EchoMimicV2 全部崩掉——
**口型模型的训练数据都是真人脸,卡通=分布外**。转向 Kolors/AI 生成写实形象,
又踩了"特写构图"的坑(头部占画面 50%,口型模型必糊),迭代 4 轮提示词才定版:
半身远景、头部占画面高 1/3。教训:**喂给口型模型的图,构图比画质重要**。

### 对口型引擎线:三条路死了两条
- MuseTalk(只动嘴):卡通脸时期检测不到脸,真人脸时期短期定版后被碾压;
- LivePortrait(视频驱动):需要真人驱动视频、不吃音频,直接放弃;
- EchoMimicV2(整帧扩散):依赖地狱+12G 显存 OOM+整帧重画脸部必糊,弃;
- **EchoMimicV3-Flash 定版**:Wan2.1 底座+8 步蒸馏,构图对了就清晰,
  129 帧×768² 一段 ~5s。GFPGAN 逐帧修复作为特写场景的补充手段保留。

### PPT 提示词的 AB 实验
方案 A(逐页骨架填空)产出套话 PPT;方案 B(只给质量纪律+叙事弧线,
让 NotebookLM 的「发现来源」联网检索真实资料)信息密度碾压。来源必须走
NotebookLM 自带检索——0 来源的提交会被静默丢弃,这是踩过才知道的隐性规则。

### 发布:先写文档再写代码
发布模块是唯一"文档先行"的模块:先在 `publish/README.md` 把五层防风控
逐条定稿,再动手实现。因为这一步错了不可逆——**宁可少发,不烧号**。

## 五、快速开始

```bash
# 0. 前置:PostgreSQL(Docker cloneai_postgres,含 pgvector)、docker/.env 密钥、
#    三个一次性登录(login-hub 抖音/小红书扫码、NotebookLM Google 账号)
# 1. 建表(一次性)
cd hotspot-monitor-service && python -c "from models.database import init_db; init_db()"
# 2. 加对标创作者(热点树的根)
curl -X POST http://127.0.0.1:8000/api/hotspot/creators -H "Content-Type: application/json" \
  -d '{"nickname":"某博主","creator_id":"MS4wLjABAAAAxxxx","sync_interval_hours":12}'
# 3. 一条命令全链路
python run_all.py              # 登录保活→热点抓题→视频制作→发布
python run_all.py --new-topic  # 强制换题全部重来
python run_all.py --no-publish # 只产视频
```

视频制作也可单独跑:`python studio/pipeline.py`(分步:`content|voice|lipsync|opening|compose|shutdown`)。

## 六、文档导航

| 文档 | 定位 |
|---|---|
| [Docs/全链路总控与流程图.md](Docs/全链路总控与流程图.md) | run_all 四步链+分阶段流程图(现行) |
| [studio/README.md](studio/README.md) | 视频制作七步链唯一设计来源(现行) |
| [studio/SERVER.md](studio/SERVER.md) | 4090 服务器运维实录(现行) |
| [publish/README.md](publish/README.md) | 发布模块五层防风控设计(现行) |
| [Docs/方案演进全景图.md](Docs/方案演进全景图.md) | 声音/形象/口型三条线的试错史(历史留档) |
| [Docs/README.md](Docs/README.md) | 全部文档索引(现行+历史) |
