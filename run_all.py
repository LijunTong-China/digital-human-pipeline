# -*- coding: utf-8 -*-
"""全链路总控:登录保活 → 热点抓题 → 视频制作 → 发布。

用法:
  python run_all.py              # 全链路一条跑完
  python run_all.py --no-topic   # 跳过热点抓题,内容环节自主选题
  python run_all.py --no-publish # 只到视频制作为止,不发布
  python run_all.py --new-topic  # 强制换题:删旧稿/旧PPT,重新选题重新出稿
退出码:0=全链路成功;2=某环节失败(日志已打印);3=发布窗口未到(视频已产出,顺延发布)
"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STUDIO = ROOT / "studio"
HUB = ROOT / "login-hub-service"
HOTSPOT = ROOT / "hotspot-monitor-service"

HUB_API = "http://127.0.0.1:3459"
HOTSPOT_API = "http://127.0.0.1:8000"
PUBLISH_PLATFORMS = ["douyin", "xhs"]   # 与 config.json publish.platforms 保持一致
# login-hub config.PLATFORMS 的注册键:xhs 在 hub 里叫 "xiaohongshu"
HUB_PLATFORM_KEY = {"douyin": "douyin", "xhs": "xiaohongshu"}


def http_json(url: str, timeout: int = 5):
    """GET JSON,失败返回 None(服务未起/网络异常一律视为不可用,不中断主流程)。"""
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return __import__("json").loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _spawn_uvicorn(cwd: Path, port: int, env_file: Path = None) -> subprocess.Popen:
    """后台拉起一个 uvicorn 服务,日志落 logs/。env_file 的键值注入子进程环境
    (热点服务 config.py 不自读 .env,LLM_API_KEY/ASR_API_KEY 等由这里喂)。"""
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    env = None
    if env_file and env_file.exists():
        env = dict(os.environ)
        kv = {}
        for ln in env_file.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, _, v = ln.partition("=")
                kv[k.strip()] = v.strip().strip('"').strip("'")
        for k, v in kv.items():
            env.setdefault(k, v)
        # 热点服务需要 DATABASE_URL,而 docker/.env 里只有 POSTGRES_* 散键,这里拼装
        # (数据库跑在 Docker cloneai_postgres,映射端口 POSTGRES_PORT=15433)
        if "DATABASE_URL" not in env and {"POSTGRES_USER", "POSTGRES_PASSWORD",
                                          "POSTGRES_DB", "POSTGRES_PORT"} <= kv.keys():
            env["DATABASE_URL"] = (f"postgresql://{kv['POSTGRES_USER']}:"
                                   f"{kv['POSTGRES_PASSWORD']}"
                                   f"@localhost:{kv['POSTGRES_PORT']}/{kv['POSTGRES_DB']}")
    f = open(logs / f"{cwd.name}.log", "ab")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0",
         "--port", str(port)], cwd=str(cwd), env=env, stdout=f, stderr=f)


def wait_api(url: str, name: str, max_sec: int = 60) -> bool:
    t0 = time.time()
    while time.time() - t0 < max_sec:
        if http_json(url) is not None:
            print(f"[0] {name} 就绪({int(time.time()-t0)}s)")
            return True
        time.sleep(3)
    return False


# ---------------------------------------------------------------- 步骤0 登录保活

def step_login():
    """确保 login-hub-service 在跑(内部自带定时保活),并核对各平台登录态。
    某平台未登录只告警不中断:视频制作不依赖登录,发布环节还能人工补救。"""
    print("── 步骤0 登录保活(login-hub)──")
    if http_json(f"{HUB_API}/api/health") is None:
        print("[0] login-hub 未启动,拉起 uvicorn…")
        _spawn_uvicorn(HUB, 3459)
        if not wait_api(f"{HUB_API}/api/health", "login-hub"):
            print("[0 警告] login-hub 起不来,发布环节需人工确认登录态")
            return
    st = http_json(f"{HUB_API}/api/quant/login_status_all", timeout=30) or {}
    for name in PUBLISH_PLATFORMS:
        info = st.get(HUB_PLATFORM_KEY.get(name, name), {})
        if info.get("logged_in"):
            print(f"[0 ok] {name} 登录态有效")
        else:
            print(f"[0 警告] {name} 未登录({info.get('error') or '未知'}),"
                  f"请到 login-hub 人工登录,否则发布将失败")


# ---------------------------------------------------------------- 步骤1 热点抓题

def step_topic() -> str:
    """从热点监控服务取最热选题作为内容 hint;服务不可用返回空(自主选题)。"""
    print("── 步骤1 热点抓题(hotspot-monitor)──")
    if http_json(f"{HOTSPOT_API}/api/health") is None:
        print("[1] 热点服务未启动,尝试拉起 uvicorn…")
        _spawn_uvicorn(HOTSPOT, 8000, env_file=ROOT / "docker" / ".env")
        if not wait_api(f"{HOTSPOT_API}/api/health", "hotspot-monitor"):
            print("[1] 热点服务不可用,内容环节自主选题")
            return ""
    d = http_json(f"{HOTSPOT_API}/api/hotspot/topics/hot?limit=5") or {}
    items = d.get("data") or []
    if items:
        print("[1] 热点候选TOP5:")
        for i, t in enumerate(items, 1):
            title = t.get("title") or t.get("keyword") or ""
            if title:
                extra = t.get("hot_score") or t.get("score") or ""
                print(f"    {i}. {title}" + (f"(热度 {extra})" if extra != "" else ""))
    for t in items:
        title = t.get("title") or t.get("keyword") or ""
        if title:
            print(f"[1 ok] 选用热点:「{title}」(候选 {len(items)} 条)")
            return title
    print("[1] 热点队列空,内容环节自主选题")
    return ""


# ---------------------------------------------------------------- 步骤2 视频制作

def step_produce():
    """①选题→②NotebookLM→③演播稿→④配音→⑤口型→⑥合成→⑦关机,一条跑完。"""
    print("── 步骤2 视频制作(studio/pipeline)──")
    r = subprocess.run([sys.executable, str(STUDIO / "pipeline.py")], cwd=str(STUDIO))
    if r.returncode != 0:
        sys.exit(f"[2 fail] pipeline 退出码 {r.returncode},见上方日志")
    print("[2 ok] 成片已产出")


# ---------------------------------------------------------------- 步骤2.5 关键产物汇报

def step_report():
    """把视频制作各关键环节的产物内容打印出来:选题/大纲逐页/演播稿逐页/成片路径。"""
    print("── 步骤2.5 关键环节内容汇报 ──")
    work = STUDIO / "output" / "work"
    assets = STUDIO / "assets"

    # 选题
    tf = work / "topic.json"
    if tf.exists():
        import json as J
        t = J.loads(tf.read_text(encoding="utf-8"))
        print(f"[选题] [{t.get('direction', '')}] {t.get('title')}")
        print(f"    角度: {t.get('angle')}")
        print(f"    观众收获: {t.get('takeaway')}")
    else:
        print("[选题] topic.json 不存在")

    # 大纲逐页
    of = work / "outline.json"
    if of.exists():
        import json as J
        o = J.loads(of.read_text(encoding="utf-8"))
        print(f"[大纲] {o.get('n_pages')} 页 | 主线: {o.get('narrative')}")
        for i, p in enumerate(o.get("pages", []), 1):
            print(f"    P{i} {p.get('title')}  ←钩子: {p.get('hook')}")
    else:
        print("[大纲] outline.json 不存在")

    # 演播稿逐页
    vf = assets / "voices.txt"
    if vf.exists():
        pages = [s for s in vf.read_text(encoding="utf-8").split("\n\n") if s.strip()]
        print(f"[演播稿] {len(pages)} 页")
        for i, s in enumerate(pages, 1):
            head = s.strip().splitlines()[0]
            print(f"    第{i}页({len(s.strip())}字): {head}…")
    else:
        print("[演播稿] voices.txt 不存在")

    # 成片
    final = assets.parent / "output" / "final" / "final_video.mp4"
    if final.exists():
        mb = final.stat().st_size / 1024 / 1024
        print(f"[成片] {final}({mb:.1f} MB)")
    else:
        print("[成片] final_video.mp4 不存在")


# ---------------------------------------------------------------- 步骤3 发布

def step_publish():
    print("── 步骤3 发布(publish)──")
    r = subprocess.run([sys.executable, str(ROOT / "publish" / "publish.py")],
                       cwd=str(ROOT))
    if r.returncode == 3:
        print("[3 顺延] 发布窗口未到/体检未过,视频已就绪,稍后重跑本步骤即可")
        sys.exit(3)
    if r.returncode != 0:
        sys.exit(f"[3 fail] publish 退出码 {r.returncode},见上方日志")
    print("[3 ok] 发布完成")


if __name__ == "__main__":
    flags = {a[2:] for a in sys.argv[1:] if a.startswith("--")}
    step_login()
    if "new-topic" in flags:
        # 强制换题:删掉选题/大纲/旧稿/旧PPT/旧笔记本链接,step_content 才会真正重新出题
        # (只删 voices.txt 会被「[选题复用]」分支接住:topic.json+outline.json 还在就复用旧题)
        for rel in ("assets/voices.txt", "assets/slides.pdf",
                    "output/work/topic.json", "output/work/outline.json",
                    "output/work/nb_notebook_url.txt"):
            f = STUDIO / rel
            if f.exists():
                f.unlink()
                print(f"[换题] 已删 {rel}")
    hint = "" if "no-topic" in flags else step_topic()
    if hint:
        os.environ["TOPIC_HINT"] = hint   # pipeline.step_content 读取
    step_produce()
    step_report()
    if "no-publish" not in flags:
        step_publish()
    print("[全部完成]")
