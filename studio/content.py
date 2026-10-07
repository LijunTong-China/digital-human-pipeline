# -*- coding: utf-8 -*-
"""内容生成(①选题+源文档 → ②NotebookLM 出 PPT → ③动态演播稿),设计见 README §1.5。

用法:
  python studio/content.py topic "话题关键词"   # 指定话题:①选题→②NotebookLM出PPT→③演播稿,一条跑完
  python studio/content.py all                 # 同上,但自动选题(结合热点,避开已做过的题)
  python studio/content.py script              # 只重跑 ③:读 assets/slides.pdf 逐页生成演播稿
  换题自动清旧产物(voices.txt/slides.pdf/笔记本链接/来源文章),无需手动删除。
"""
import json
import re
import functools
print = functools.partial(print, flush=True)
import sys
import time
from pathlib import Path

import avutils as U

CFG = U.CFG
C = CFG["content"]
STUDIO = U.STUDIO
WORK = STUDIO / CFG["paths"]["work"]
ASSETS = STUDIO / CFG["paths"]["assets"]

# ---------------------------------------------------------------- ① 选题 → 结构规划(骨架进提示词)

TOPIC_PROMPT = """你是资深科技内容策划。请为一条面向程序员/技术爱好者的科普短视频选题。
方向:{direction}。{hint}
要求:
- 选题要有信息增量,不是"什么是X"的百科式题目,而是有观点、有反差、有实用价值的题目
- 适合 {min_pages}~{max_pages} 页演示文稿讲透
只输出 JSON:{{"title": "...", "angle": "一句话说清切入角度", "takeaway": "观众看完能带走的1句话"}}"""

# 结构规划:刻意设计,页数给足、钩子先行、叙事递进引人深思(README §1.5)
PLAN_PROMPT = """你是顶级科技内容策划,为短视频《{title}》规划一份演示文稿的完整结构。
切入角度:{angle}
观众收获:{takeaway}

规划要求:
1. 页数 {min_pages}~{max_pages} 页,信息量给足;宁可深挖,不要罗列
2. 叙事主线必须层层递进、引人深思,按此弧线展开:
   开场钩子(反常识现象/痛点) → 现象铺开 → 为什么会这样(原因) → 背后机制/原理
   → 数据与真实案例佐证 → 反直觉的深层结论(让人"原来如此") → 看完可以怎么做(行动清单)
3. 每页 3~5 条要点,必须具体:带数字、版本号、案例名,禁止"赋能""提升效率"式空话
4. 每页给一个"钩子":反常识点/痛点/金句,让观众停下滑动
5. 中间至少安排 1 页"常见误解/踩坑对比",1 页"如果继续演化会怎样"的前瞻思考
6. 严禁在任何标题/要点/钩子里出现制作工具或平台名称(如 NotebookLM、Gemini、
   Google 等),只写主题相关内容

只输出 JSON:
{{"n_pages": 数字, "narrative": "一句话概括叙事主线",
  "pages": [{{"title": "页标题", "points": ["要点1", "要点2", "要点3"],
             "hook": "本页钩子(反常识/痛点/金句)"}}]}}"""


def pick_topic(hint_topic: str = "") -> dict:
    """选一个未做过的题(查重缓存),hint 非空则围绕它出题。"""
    cache = STUDIO / C["topic_cache"]
    done = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else []
    direction = C["directions"][len(done) % len(C["directions"])]
    hint = f"希望围绕「{hint_topic}」出题。" if hint_topic else \
        "请结合当前该方向的热点趋势(新模型/新框架/工程实践变化)自主命题。"
    raw = U.llm([
        {"role": "system", "content": TOPIC_PROMPT.format(
            direction=direction, hint=hint, min_pages=C["plan"]["min_pages"],
            max_pages=C["plan"]["max_pages"])},
        {"role": "user", "content": f"已做过的选题(必须避开):{json.dumps(done, ensure_ascii=False)}"},
    ], json_mode=True, timeout=300)
    raw = U.strip_think(raw)
    topic = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    topic["direction"] = direction
    return topic


def write_nb_prompt(topic: dict, outline: dict):
    """骨架直接内嵌进提示词:NotebookLM 按提示词执行,不做参考文档。"""
    page_lines = "\n".join(
        f"第{i}页《{pg['title']}》:要点 {' / '.join(str(x) for x in pg['points'])}"
        f"(钩子:{pg['hook']})"
        for i, pg in enumerate(outline["pages"], 1))
    nb_prompt = (f"请生成一份演示文稿,主题《{topic['title']}》,共 {outline['n_pages']} 页。\n"
                 "每页一个大标题 + 3~5 条短要点(每条不超过 18 字),不要大段文字。\n"
                 "第 1 页只放主标题和一句话副标题;最后一页放行动清单。"
                 "要点具体,内容有深度、引人深思,禁止'赋能/提升效率'式空话。\n"
                 f"叙事主线:{outline['narrative']}\n逐页要求如下:\n" + page_lines)
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "nb_prompt.txt").write_text(nb_prompt, encoding="utf-8")


def plan_outline(topic: dict) -> dict:
    """PPT 结构规划:页数/每页标题要点/钩子/叙事主线,落 work/outline.json。"""
    raw = U.strip_think(U.llm([
        {"role": "system", "content": PLAN_PROMPT.format(
            title=topic["title"], angle=topic["angle"], takeaway=topic["takeaway"],
            min_pages=C["plan"]["min_pages"], max_pages=C["plan"]["max_pages"])},
        {"role": "user", "content": "开始规划结构。"},
    ], json_mode=True, max_tokens=8192, timeout=600))
    raw = raw[raw.index("{"): raw.rindex("}") + 1]
    outline = json.loads(raw)
    p = C["plan"]
    if len(outline.get("pages", [])) < p["min_pages"] or \
            len(outline["pages"]) > p["max_pages"]:
        raise RuntimeError(f"[plan] 页数 {len(outline.get('pages', []))} "
                           f"超出 {p['min_pages']}~{p['max_pages']}")
    outline["n_pages"] = len(outline["pages"])   # 以实际页列表为准(LLM 可能自报不一致)
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "outline.json").write_text(
        json.dumps(outline, ensure_ascii=False, indent=1), encoding="utf-8")
    write_nb_prompt(topic, outline)
    # 选题登记:写入查重缓存与 topic.json(供开场白 auto / 复用)
    cache = STUDIO / C["topic_cache"]
    done = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else []
    done.append(topic["title"])
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(done, ensure_ascii=False), encoding="utf-8")
    tf = WORK / "topic.json"
    tf.parent.mkdir(parents=True, exist_ok=True)
    tf.write_text(json.dumps(topic, ensure_ascii=False, indent=1), encoding="utf-8")
    return outline


# ------------------------------------------------- ②前置 NotebookLM 来源(血肉)

SOURCE_PROMPT = """你是科技资料撰写人。基于下面的 PPT 结构规划,写一篇支撑该演示文稿的资料文章:

{outline}

要求:
1. {n}~{n_max} 个字,信息密度高,把每页要点展开成有论据、有数据感、有案例的正文
2. 覆盖全部 {pages} 页的内容,按页的顺序组织段落
3. 直接输出文章正文,不要标题层级符号、不要"第X页"字样
4. 这是给观众看的科普资料,严禁出现任何制作工具/平台名称(如 NotebookLM、Gemini、
   Google、AI 生成、演示文稿软件等),只讲主题内容本身"""

SOURCE_MIN, SOURCE_MAX = 2000, 3000


def gen_source_text(outline: dict) -> str:
    """基于 outline 生成来源资料文章(血肉),NotebookLM 0 来源会被静默丢弃,必须先加来源。"""
    raw = U.llm([
        {"role": "system", "content": SOURCE_PROMPT.format(
            outline=json.dumps(outline, ensure_ascii=False, indent=1),
            n=SOURCE_MIN, n_max=SOURCE_MAX, pages=outline["n_pages"])},
        {"role": "user", "content": "开始写资料文章。"},
    ], temperature=0.7, timeout=600)
    text = U.strip_think(raw).strip()
    if len(text) < 800:
        raise RuntimeError(f"[source] 来源文章过短({len(text)} 字),LLM 输出异常")
    dst = WORK / "source_text.txt"
    dst.write_text(text + "\n", encoding="utf-8")
    print(f"[source] 来源文章 {len(text)} 字 → {dst}")
    return str(dst)


# ---------------------------------------------------------------- ③ 动态演播稿

FULL_SCRIPT_PROMPT = """你是顶级科技短视频口播撰稿人。下面是一份演示文稿的全部 {n} 页内容,
通读全文后,为整支视频写一套完整的口播稿。

{all_pages}

总要求(叙事在全局层面设计,不是逐页拼凑):
1. 先通盘设计叙事弧线:开场钩子 → 展开 → 原因 → 机制 → 论据 → 反直觉结论 → 行动清单,
   让 12 页像一篇完整的演讲,而不是 12 段独立的解说
2. 每页口播稿 {lo}~{hi} 个字,短句为主,长短交错,像对朋友讲话
3. 页间必须自然衔接:上一页的结尾钩住下一页的开头,允许前后呼应,但每页忠于本页要点
4. 第 1 页开头必须是全片最强的钩子;最后一页收在行动/反思上
5. 禁止 AI 腔口头禅:说白了、其实呢、值得注意的是、总的来说、众所周知、
   赋能、提升效率、不仅仅是、更是;同一比喻/短语全片只出现一次
6. 严禁出现任何制作工具/平台名称(如 NotebookLM、Gemini、Google、
   "这份演示文稿/PPT"等字眼),就当直接对着观众讲这个主题

输出格式(严格遵守,只输出一个 JSON 对象,不要 markdown 代码块、不要任何解释):
{{"pages": ["第一页的口播稿正文", "第二页的口播稿正文", "... 共 {n} 页,一页不多一页不少"]}}"""

REVIEW_PROMPT = """你是口播稿主编。下面是一支科技短视频的 {n} 页讲解词,按页编号:

{script}

任务:全局审一遍,只评分、不重写。检查三点:
1. 跨页重复的表述/口头禅/句式(同一比喻、同一短语是否出现多次)
2. 页间衔接:每页开头是否自然接住上一页结尾(第1页除外)
3. 是否混入制作工具/平台名称(如 NotebookLM、Gemini、Google)或 AI 腔

输出格式:只输出一个 JSON 对象,不要 markdown 代码块、不要任何解释:
{{"score": 0到100的整数, "issues": ["第X页:具体问题一句话", "最多列5条,没问题则为空数组"]}}"""


def _parse_json_pages(raw: str, n: int) -> list:
    """从 LLM 输出解析 JSON 逐页稿件;格式/页数/空页任何一项不符返回空列表。"""
    txt = U.strip_think(raw).strip()
    txt = re.sub(r"^```(json)?|```$", "", txt, flags=re.M).strip()
    try:
        obj = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
    except (ValueError, IndexError):
        return []
    pages = obj.get("pages") if isinstance(obj, dict) else None
    if not isinstance(pages, list) or len(pages) != n:
        return []
    pages = [str(p).strip() for p in pages]
    return pages if all(pages) else []

# 代码级质检禁词:命中即触发该页重写
BANNED_WORDS = ["gemini", "notebooklm", "google", "演示文稿", "这份ppt",
                "说白了", "值得注意的是", "总的来说", "众所周知", "赋能"]


def _ocr_engines():
    """按 config content.ocr 顺序构造可用的 OCR 引擎,找不到任何引擎则报错。"""
    engines = []
    for name in C.get("ocr", ["paddleocr", "easyocr", "tesseract"]):
        try:
            if name == "paddleocr":
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
                engines.append(("paddleocr",
                                lambda im, o=ocr: "".join(
                                    ln[1] for ln in ocr.ocr(im, cls=True)[0]) if ocr.ocr(im, cls=True) else ""))
            elif name == "easyocr":
                from easyocr import Reader
                rd = Reader(["ch_sim", "en"], gpu=False, verbose=False)
                engines.append(("easyocr",
                                lambda im, r=rd: "".join(r.readtext(im, detail=0))))
            elif name == "tesseract":
                import pytesseract
                cmd = C.get("tesseract_cmd")
                if cmd:
                    pytesseract.pytesseract.tesseract_cmd = cmd
                engines.append(("tesseract",
                                lambda im, p=pytesseract: p.image_to_string(
                                    im, lang=C.get("tesseract_lang", "chi_sim+eng"))))
        except Exception:
            continue
    return engines


def _mineru_parse(pdf: Path) -> list:
    """MinerU API 整体解析 slides.pdf 单任务,按 content_list.json 的 page_idx
    归并出每页纯文本(与 PDF 页序一致)。key 读 env MINERU_API_KEY。"""
    import io
    import json as _json
    import zipfile
    key = U.ENV.get("MINERU_API_KEY")
    if not key:
        raise RuntimeError("env 缺 MINERU_API_KEY")
    base = "https://mineru.net/api/v4"
    h = {"Authorization": f"Bearer {key}"}

    def _check(r, what):
        if r.status_code != 200:
            raise RuntimeError(f"{what} HTTP {r.status_code}: {r.text[:300]}")
        body = r.json()
        if body.get("code") != 0:
            raise RuntimeError(f"{what} 业务失败 code={body.get('code')} msg={body.get('msg')}")
        return body["data"]

    # 1. 申请上传链接(单文件)
    r = U.SESSION.post(f"{base}/file-urls/batch", headers=h, timeout=60, json={
        "enable_formula": False, "language": "ch",
        "files": [{"name": pdf.name, "data_id": "slides"}]})
    d = _check(r, "申请上传链接")
    batch_id, url = d["batch_id"], d["file_urls"][0]
    # 2. 上传(PUT,无需鉴权头)
    with open(pdf, "rb") as f:
        pr = U.SESSION.put(url, data=f, timeout=600)
    if pr.status_code != 200:
        raise RuntimeError(f"上传失败 HTTP {pr.status_code}")
    print(f"[mineru] 整本已上传({pdf.stat().st_size//1024}KB),批次 {batch_id},轮询中…")
    # 3. 轮询单任务结果(最长 20 分钟),waiting-file 停留过久视为上传未落地
    zu = None
    t0 = time.time()
    while time.time() - t0 < 1200:
        time.sleep(10)
        r = U.SESSION.get(f"{base}/extract-results/batch/{batch_id}", headers=h, timeout=60)
        it = _check(r, "查询批量结果")["extract_result"][0]
        print(f"[mineru] 状态: {it['state']} ({int(time.time()-t0)}s)")
        if it["state"] == "waiting-file" and time.time() - t0 > 120:
            raise RuntimeError("上传后 2 分钟仍 waiting-file,文件未落地,终止轮询")
        if it["state"] == "failed":
            raise RuntimeError(f"MinerU 解析失败: {it.get('err_msg')}")
        if it["state"] == "done":
            zu = it["full_zip_url"]
            break
    if not zu:
        raise RuntimeError("MinerU 轮询超时(1200s)")
    # 4. 下载结果包,content_list.json 按 page_idx 归并每页文本
    zb = U.SESSION.get(zu, timeout=600).content
    pages = None
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        for n in z.namelist():
            if n.endswith("content_list.json"):
                blocks = _json.loads(z.read(n).decode("utf-8"))
                pages = {}
                for b in blocks:
                    if b.get("type") == "text" and b.get("text", "").strip():
                        pages.setdefault(b.get("page_idx", 0), []).append(
                            b["text"].strip())
                break
    if pages is None:
        raise RuntimeError("MinerU 结果包内无 content_list.json")
    n = max(pages) + 1 if pages else 0
    return ["\n".join(pages.get(i, [])) for i in range(n)]


def _ocr_vision(png: str) -> str:
    """视觉 LLM 识别页面图(复用 LLM 通道,免装本地 OCR 依赖)。
    模型取 env LLM_VISION_MODEL(缺省回落 LLM_MODEL)。"""
    import base64
    b64 = base64.b64encode(Path(png).read_bytes()).decode()
    model = U.ENV.get("LLM_VISION_MODEL") or U.ENV["LLM_MODEL"]
    raw = U.llm([
        {"role": "system", "content":
         "你是幻灯片文字识别器。逐字转录图片中所有文字,一行一条,保持原文, "
         "不要翻译、不要总结、不要添加任何解释。"},
        {"role": "user", "content": [
            {"type": "text", "text": "转录这张幻灯片上的全部文字。"},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]},
    ], temperature=0, timeout=120, model=model)
    return U.strip_think(raw).strip()


def pdf_page_texts() -> list:
    """提取 slides.pdf 每一页的文本。
    NotebookLM 导出的是图片型 PDF(每页 1 图 0 文本),无文本层时自动:渲染 PNG → OCR。
    OCR 顺序:视觉 LLM(免依赖)→ 本地引擎(paddleocr/easyocr/tesseract,按 config)。
    页面 PNG 缓存到 work/slides_png/ 供后续口型/封面等步骤复用。"""
    import fitz
    doc = fitz.open(ASSETS / Path(CFG["paths"]["slides"]).name)
    texts = [p.get_text().strip() for p in doc]
    if any(texts):
        doc.close()
        return texts

    # 图片型 PDF:MinerU 整体解析(可配置禁用) → 失败才降级(渲染 PNG → 视觉 LLM/本地 OCR 逐页)
    pdf_path = ASSETS / Path(CFG["paths"]["slides"]).name
    doc.close()
    if C.get("use_mineru", True):
        try:
            out = _mineru_parse(pdf_path)
            for i, t in enumerate(out, 1):
                print(f"[mineru] p{i}/{len(out)}: {len(t)} 字")
            return out
        except Exception as e:
            print(f"[mineru] 整体解析失败({type(e).__name__}: {e}),降级逐页 OCR")
    else:
        print("[mineru] use_mineru=false,已跳过,直接逐页 OCR")
    doc = fitz.open(pdf_path)
    png_dir = WORK / "slides_png"
    png_dir.mkdir(parents=True, exist_ok=True)
    # 指纹防旧 OCR 页图复用:slides.pdf 一变,整目录作废重渲染重 OCR
    import hashlib as _h
    _fp = _h.md5(pdf_path.read_bytes()).hexdigest()
    _stamp = png_dir / "_slides.md5"
    if _stamp.exists() and _stamp.read_text(encoding="utf-8").strip() != _fp:
        for old in png_dir.glob("p*.png"):
            old.unlink()
        print("[ocr] slides.pdf 已变化,旧 OCR 页图缓存已清")
    _stamp.write_text(_fp + "\n", encoding="utf-8")
    zoom = C.get("ocr_zoom", 2.0)
    pngs = []
    for i, page in enumerate(doc, 1):
        png = png_dir / f"p{i:02d}.png"
        if not png.exists():
            page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(str(png))
        pngs.append(png)
    doc.close()
    local = _ocr_engines()          # [(name, fn), ...] 可能空
    out = []
    for i, png in enumerate(pngs, 1):
        text = ""
        for name, fn in [("vision-llm", _ocr_vision)] + local:
            try:
                text = fn(str(png)).strip()
            except Exception as ex:
                print(f"[ocr:{name}] p{i} 失败: {type(ex).__name__},换下一引擎")
                continue
            if text:
                break
        if not text:
            raise RuntimeError(f"slides.pdf 第 {i} 页所有解析引擎均未出文字")
        out.append(text)
        print(f"[ocr:{name}] p{i}/{len(pngs)}: {len(text)} 字")
    return out


def _lint_page(text: str) -> list:
    """代码级质检:返回命中的禁词列表(小写比对)。"""
    low = text.lower()
    return [w for w in BANNED_WORDS if w in low]


def _parse_pages(raw: str, n: int) -> list:
    """按 '=== 第X页 ===' 分隔解析逐页稿件;页数/空页不符返回空列表。"""
    parts = re.split(r"===\s*第\s*\d+\s*页\s*===", U.strip_think(raw))
    rev = [p.strip().splitlines()[0].strip() if p.strip() else ""
           for p in parts if p.strip()]
    if len(rev) != n or not all(rev):
        return []
    return rev


def gen_script() -> str:
    """整篇通写讲解词,空行分页写 assets/voices.txt(页数随 PPT 动态)。
    流程:①LLM 通读全部页面一次成稿(全局叙事/页间衔接) → ②解析逐页,
    页数不符自动重试 → ③代码级禁词质检,命中页带反馈重写 → ④主编审去重复。
    全文一次成稿才能设计叙事弧线与前后呼应,逐页闭卷写做不到。"""
    pages = [t for t in pdf_page_texts() if t]
    if not pages:
        raise RuntimeError("slides.pdf 无文本,请确认 NotebookLM 产物有效")
    n, lo, hi = len(pages), C["script_min_chars"], C["script_max_chars"]
    all_pages = "\n".join(f"=== 第{i+1}页 ===\n标题与要点:\n{t}" for i, t in enumerate(pages))

    # ①整篇通写 → ②禁词重写 → ③主编评分:<70 打回整篇重写(最多两轮)
    import json as _json
    out = []
    for attempt in (1, 2):
        # ① 整篇通写(页数不符自动重试一次)
        for sub in (1, 2):
            raw = U.llm([
                {"role": "system", "content": FULL_SCRIPT_PROMPT.format(
                    n=n, all_pages=all_pages, lo=lo, hi=hi)},
                {"role": "user", "content": "开始写全套口播稿。"},
            ], temperature=0.8, timeout=900, max_tokens=16384, json_mode=True)
            out = _parse_json_pages(raw, n)
            if out:
                print(f"[script] 整篇通写成功:{n} 页(第 {attempt} 轮第 {sub} 次)")
                break
            print(f"[script] 第 {attempt} 轮第 {sub} 次通写页数/格式不符,重试…")
        if not out:
            if attempt == 1:
                print("[script] 本轮通写两次均未返回正确分页格式,进入下一轮")
                continue
            raise RuntimeError("[script fail] 整篇通写两轮均未返回正确的分页格式,"
                               "检查 LLM 输出或调大 max_tokens")

        # ② 代码级质检:禁词命中页单独重写(携带前后页上下文)
        for i, seg in enumerate(out):
            banned = _lint_page(seg)
            if not banned:
                continue
            prev_ctx = f"上一页结尾:…{out[i-1][-60:]}" if i > 0 else "(这是第一页)"
            nxt_ctx = f"下一页开头:…{out[i+1][:40]}" if i + 1 < n else "(这是最后一页)"
            raw = U.llm([
                {"role": "system", "content":
                 f"重写这段口播稿(第{i+1}/{n}页)。要求:字数 {lo}~{hi},口语化短句,"
                 f"开头接住上一页,严禁出现这些词:{BANNED_WORDS}。只输出正文。\n"
                 f"本页要点:\n{pages[i]}\n{prev_ctx}\n{nxt_ctx}"},
                {"role": "user", "content": f"原稿(命中禁词 {banned}):\n{seg}\n重写:"},
            ], temperature=0.7, timeout=300)
            seg2 = U.strip_think(raw).strip().splitlines()[0].strip()
            if seg2 and not _lint_page(seg2):
                out[i] = seg2
                print(f"[script] p{i+1} 禁词 {banned} → 已重写")
            else:
                print(f"[script] p{i+1} 禁词重写未通过,保留并告警: {banned}")

        # ③ 主编审:只评分+列问题(输出极小,不重写全文),≥70 定稿,<70 打回
        try:
            joined = "\n\n".join(f"=== 第{i+1}页 ===\n{s}" for i, s in enumerate(out))
            raw = U.llm([
                {"role": "system", "content": REVIEW_PROMPT.format(n=n, script=joined)},
                {"role": "user", "content": "开始审稿。"},
            ], temperature=0.5, timeout=900, max_tokens=512, json_mode=True)
            data = _json.loads(U.strip_think(raw).strip())
            score = int(data.get("score", 0))
            issues = [str(x) for x in data.get("issues", [])][:5]
            print(f"[review] 主编评分:{score}/100" + (f",问题:{'; '.join(issues)}" if issues else ""))
            if score >= 70:
                break
            if attempt == 1:
                print("[review] 低于 70 分,打回重写整篇口播稿…")
                continue
            print("[review] 重写后仍低于 70 分,采用本轮稿继续")
        except Exception as e:
            print(f"[review] 审稿跳过({type(e).__name__}),保留原稿")
            break

    dst = ASSETS / Path(CFG["paths"]["voices"]).name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n\n".join(out) + "\n", encoding="utf-8")
    print(f"[script ok] {n} 页整篇通写 → {dst}")
    return str(dst)


# ---------------------------------------------------------------- 入口

def _invalidate_stale(t: dict):
    """换题自动清旧产物:旧稿/旧PPT/旧NotebookLM笔记本/旧来源文章,绝不新旧混用。
    以选题标题为指纹,标题变了(或首次运行)即清理。"""
    stamp = WORK / "_topic_stamp.txt"
    if stamp.exists() and stamp.read_text(encoding="utf-8").strip() == t["title"]:
        return
    removed = []
    for f in (ASSETS / Path(CFG["paths"]["voices"]).name,     # 旧演播稿
              ASSETS / Path(CFG["paths"]["slides"]).name,     # 旧 PPT
              WORK / "nb_notebook_url.txt",                   # 旧笔记本链接(防误走 --collect)
              WORK / "nb_status.log",
              WORK / "source_text.txt",                       # 旧来源文章(跟着 outline 走)
              WORK / "opening.wav", WORK / "opening_raw.wav",   # 旧开场白音频(文本随题)
              WORK / "opening_text.txt"):                       # 旧开场白文案缓存(auto 随题)
        if f.exists():
            f.unlink()
            removed.append(f.name)
    # 旧音频/口型/页图/合成中间品整目录清:换题后绝不允许旧题的声音画面混进新片
    for d, names in ((WORK, ("pages", "lipsync")),
                     (ASSETS, ())):
        for n in names:
            p = d / n
            if p.exists():
                import shutil
                shutil.rmtree(p)
                removed.append(n + "/")
    for p in WORK.glob("voice_p*.wav"):
        p.unlink(); removed.append(p.name)
    for p in WORK.glob("clone_p*.wav"):
        p.unlink(); removed.append(p.name)
    for p in WORK.glob("seg_*.mp4"):
        p.unlink(); removed.append(p.name)
    WORK.mkdir(parents=True, exist_ok=True)
    stamp.write_text(t["title"] + "\n", encoding="utf-8")
    if removed:
        print(f"[换题] 检测到新选题,已自动清旧产物: {', '.join(removed)}")


def step_content(hint: str = "", force_script: bool = False):
    """①③ 动态生成;②(NotebookLM)由浏览器自动化完成,无 slides.pdf 时停下等它。"""
    slides = ASSETS / Path(CFG["paths"]["slides"]).name
    voices = ASSETS / Path(CFG["paths"]["voices"]).name

    # 换题检测必须先于一切:旧稿还躺着也不能挡住清旧+重写
    topic_file = WORK / "topic.json"
    if topic_file.exists():
        _invalidate_stale(json.loads(topic_file.read_text(encoding="utf-8")))

    if not voices.exists() or force_script:
        if not slides.exists():
            outline_file = WORK / "outline.json"
            if topic_file.exists() and outline_file.exists():
                t = json.loads(topic_file.read_text(encoding="utf-8"))
                o = json.loads(outline_file.read_text(encoding="utf-8"))
                print(f"[选题复用] [{t.get('direction', '')}] {t['title']}")
                if not (WORK / "nb_prompt.txt").exists():
                    write_nb_prompt(t, o)   # 复用也要保证提示词在
            else:
                t = pick_topic(hint)
                print(f"[选题] [{t['direction']}] {t['title']}\n[角度] {t['angle']}")
                o = plan_outline(t)
                print(f"[规划] {o['n_pages']} 页 | 主线: {o['narrative']}")
                _invalidate_stale(t)   # 全新选题也要盖章+清残留
            if not (WORK / "source_text.txt").exists():
                gen_source_text(o)   # ② 需要:NotebookLM 无来源提交会被静默丢弃
            # ② 自动执行 NotebookLM(加来源 → 骨架提示词 → 生成 → 等卡片 → 下 PDF)
            import subprocess
            collect = (WORK / "nb_notebook_url.txt").exists() and not slides.exists()
            cmd = [sys.executable, str(STUDIO / "nb_auto.py")]
            if collect:
                cmd.append("--collect")   # 已排队/已生成:只补收,不新建笔记本
            r = subprocess.run(cmd)
            if r.returncode == 3:
                raise SystemExit(
                    "[② 排队] NotebookLM 额度尽,已走「稍后生成」(几小时内完成)。\n"
                    "  之后重跑本步骤会自动补收该笔记本,无需重新生成。")
            if r.returncode != 0 or not slides.exists():
                raise SystemExit(
                    f"[② 失败] nb_auto.py 退出码 {r.returncode},"
                    f"日志见 {WORK / 'nb_status.log'}")
            print(f"[② ok] {slides}")
        print("── ③ 生成演播稿 ──")
        gen_script()
    print(f"[content ok] voices={voices} ({len(U.voices_pages())} 页)")


if __name__ == "__main__":
    args = sys.argv[1:]
    cmd = args[0] if args else "all"
    hint = " ".join(args[1:]).strip()
    if cmd in ("topic", "all"):
        # topic=指定话题跑全流程;all=自动选题跑全流程,二者仅选题来源不同
        step_content(hint if cmd == "topic" else "")
    elif cmd == "script":
        gen_script()
    elif cmd == "all":
        step_content(hint)
    else:
        raise SystemExit(__doc__)
