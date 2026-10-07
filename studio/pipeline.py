# -*- coding: utf-8 -*-
"""总控(④配音 → ⑤口型 → ⑤b开场白口型 → ⑥合成 → ⑦关机),配置见 config.json/README.md。

用法:
  python studio/pipeline.py                # ①③内容→④配音→(口型/开场白)→⑥合成→⑦关机
  python studio/pipeline.py content voice  # 分步: content|voice|lipsync|opening|compose|shutdown
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

STUDIO = Path(__file__).resolve().parent
sys.path.insert(0, str(STUDIO))
import avutils as U

CFG = U.CFG
SRV = CFG["server"]
P = CFG["paths"]
WORK = STUDIO / P["work"]
LIP = WORK / "lipsync"
ASSETS = STUDIO / P["assets"]


def ssh(cmd: str, check=True):
    r = subprocess.run(
        ["ssh", "-o", f"ConnectTimeout={SRV.get('connect_timeout_sec', 10)}",
         "-p", str(SRV["port"]), f"root@{SRV['host']}", cmd],
        capture_output=True, text=True, timeout=SRV.get("ssh_cmd_timeout_sec", 3600))
    if check and r.returncode != 0:
        sys.exit(f"[ssh fail] {cmd}\n{r.stdout[-500:]}\n{r.stderr[-500:]}")
    return r


def scp(remote: str, local, to_remote=False, retries=None, wait=None):
    """scp 带重试。to_remote=False: 下载;True: 上传。"""
    retries = retries or SRV["scp_retries"]
    wait = wait or SRV["scp_wait_sec"]
    if not to_remote:
        LIP.mkdir(parents=True, exist_ok=True)
    for i in range(1, retries + 1):
        cmd = (["scp", "-o", f"ConnectTimeout={SRV.get('connect_timeout_sec', 10)}",
                "-P", str(SRV["port"]), str(local), f"root@{SRV['host']}:{remote}"]
               if to_remote else
               ["scp", "-o", f"ConnectTimeout={SRV.get('connect_timeout_sec', 10)}",
                "-P", str(SRV["port"]), f"root@{SRV['host']}:{remote}", str(local)])
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            return
        print(f"[scp] {i}/{retries} 失败,等 {wait}s 重试...")
        time.sleep(wait)
    sys.exit(f"[scp fail] {local} <-> {remote}")


def srv_path(rel: str) -> str:
    return f"{SRV['root']}/{rel}"


def srv_up() -> bool:
    return ssh("echo alive", check=False).returncode == 0


def srv_wait_recover(max_min: int = 30):
    """轮询期间服务器失联(掉线/重启)时等待恢复;超时才判死。"""
    t0 = time.time()
    while not srv_up():
        if time.time() - t0 > max_min * 60:
            sys.exit(f"[fail] 服务器失联超过 {max_min} 分钟,判定实例已关机/崩溃")
        print(f"[poll] 服务器失联,等待恢复… {int(time.time()-t0)}s")
        time.sleep(30)


def voices_txt_path() -> Path:
    return STUDIO / P["voices"]


def sync_inputs():
    """服务器输入指纹:稿子/参考音/参考转写/参考形象任一变化,自动清空服务器上
    全部输入与口型中间产物(含参考声音/形象/页音频/lipsync/emv3_batch),再由
    各步骤全量重传。杜绝新旧输入混用;纯代码实现,无手工清理。"""
    files = [voices_txt_path(), STUDIO / P["voice_ref"],
             STUDIO / P["ref_prompt"], STUDIO / P["ref_image_white"]]
    m = hashlib.md5()
    for f in files:
        m.update(U.md5_of(f).encode() if f.exists() else b"-")
    fp = m.hexdigest()
    old = ssh(f"cat {srv_path('_inputs.md5')} 2>/dev/null", check=False).stdout.strip()
    if old == fp:
        return
    if old:
        print("[sync] 输入已变化,自动清空服务器旧输入与中间产物")
        ssh(f"cd {SRV['root']} && rm -rf pages lipsync_out emv3_batch "
            f"emv3_jobs.json opening_job.json _voices.md5")
        # 本地对应产物一并作废:服务器重做后,本地旧 clone 音频/口型不许再被复用
        for p in WORK.glob("clone_p*.wav"):
            p.unlink()
        for p in LIP.glob("lipsync_p*.mp4"):
            p.unlink()
    ssh(f"echo {fp} > {srv_path('_inputs.md5')}")
    print("[sync] 输入指纹已登记,后续步骤全量上传")


def _patch_port(new_port: str):
    """只替换 config.json 文本里的 server.port 值(保留 // 注释原样)。"""
    import re
    f = STUDIO / "config.json"
    txt = f.read_text(encoding="utf-8")
    txt = re.sub(r'("port"\s*:\s*)\d+', rf'\g<1>{new_port}', txt, count=1)
    f.write_text(txt, encoding="utf-8")
    global CFG
    CFG = U.load_config()
    SRV.clear()
    SRV.update(CFG["server"])


def wait_gpu():
    """GPU 步骤统一入口:先快连;连不上则提示用户开卡,等用户回车确认后
    快速轮询连接(带进度提示)。超时允许输入新端口(AutoDL 重启端口常变)。"""
    if ssh("echo alive", check=False).returncode == 0:
        print("[gpu] 实例在线,直接干活")
        return
    print("[gpu] 需要 GPU:连不上 4090 实例(可能已自动关机)。")
    print("[gpu] >>> 请到 AutoDL 控制台开机 <<<")
    print("[gpu] 开机完成后回来按回车确认,我会立刻连接服务器干活。")
    try:
        input("[gpu] 确认已开机请按回车 > ")
    except EOFError:
        pass
    # 用户确认后快速轮询:开机到 ssh 就绪一般 1~3 分钟
    t0 = time.time()
    while time.time() - t0 < 600:
        if ssh("echo alive", check=False).returncode == 0:
            print(f"[gpu] 实例就绪(等了 {int(time.time()-t0)}s),开干")
            return
        print(f"[gpu] 连接中… {int(time.time()-t0)}s(开机+SSH 就绪通常 1~3 分钟)")
        time.sleep(10)
    # 超时:多半是重启后端口变了,允许就地改端口
    try:
        np = input("[gpu] 10 分钟未连上。若控制台显示的 SSH 端口变了,输入新端口后回车;"
                   "直接回车=放弃 > ").strip()
    except EOFError:
        np = ""
    if np.isdigit():
        _patch_port(np)
        print(f"[gpu] 端口已改为 {np} 并写入 config,重试连接…")
        t0 = time.time()
        while time.time() - t0 < 300:
            if ssh("echo alive", check=False).returncode == 0:
                print("[gpu] 实例就绪,开干")
                return
            time.sleep(10)
    sys.exit("[gpu fail] 仍连不上,请核对实例状态/端口(config server.host/port)后重跑")


# ---------------------------------------------------------------- ①②③ 内容

def step_content():
    print("── ①③ 内容生成(选题/源文档/演播稿)──")
    import content
    content.step_content()


# ---------------------------------------------------------------- ④ 配音

def step_voice():
    """clone=服务器克隆;预置音色=本地TTS后上传 v2_pXX.wav 供⑤切段。"""
    print(f"── ④ 配音(voice={CFG['voice']})──")
    voices = U.voices_pages()
    npages = U.n_pages()

    if CFG["voice"] != "clone":   # 预置音色:本地 TTS,不占用 GPU
        import hashlib
        for i in range(npages):
            w = WORK / f"{P['page_audio_prefix']}{i:02d}.wav"
            # 文本指纹:稿件本页一变,旧配音作废重合成(与 compose.page_audio 同一规则)
            stamp = WORK / f"{P['page_audio_prefix']}{i:02d}.md5"
            fp = hashlib.md5((CFG["voice"] + "\n" + voices[i]).encode("utf-8")).hexdigest()
            if w.exists() and not (stamp.exists() and
                                   stamp.read_text(encoding="utf-8").strip() == fp):
                w.unlink()
                print(f"[④] p{i:02d} 稿件已变化,重新配音")
            if not w.exists():
                U.tts(voices[i], str(w), CFG["tts_api"]["voice_prefix"] + CFG["voice"])
                stamp.write_text(fp + "\n", encoding="utf-8")
        if CFG["layout"] == "board":   # 只有 board 的逐页口型才需要页音频上服务器
            wait_gpu()
            ssh(f"mkdir -p {srv_path(SRV['pages_dir'])}")
            for i in range(npages):
                w = WORK / f"{P['page_audio_prefix']}{i:02d}.wav"
                scp(srv_path(f"{SRV['pages_dir']}/v2_p{i:02d}.wav"), str(w), to_remote=True)
            print(f"[④ ok] {CFG['voice']} × {npages} 页本地合成并已上传")
        else:
            print(f"[④ ok] {CFG['voice']} × {npages} 页本地合成(layout={CFG['layout']} 无需上传)")
        return

    wait_gpu()   # 只有克隆音色才需要 GPU
    ssh(f"mkdir -p {srv_path(SRV['pages_dir'])}")
    # 指纹检查必须先于缺页判断:稿子/参考音/参考形象变了,服务器旧音频先清掉,
    # 否则旧 v2_pXX.wav 还在 → missing 为空 → 永远不重克隆,旧声音混进新片
    sync_inputs()
    missing = [i for i in range(npages)
               if ssh(f"test -f {srv_path(SRV['pages_dir'])}/v2_p{i:02d}.wav",
                      check=False).returncode != 0]
    if missing:
        print(f"服务器缺 {len(missing)} 页,启动克隆...")
        srv = srv_path(SRV["pages_dir"])
        loc_scripts = STUDIO / "server_scripts"
        # 2) 上传:voices.txt / voice_ref / ref_prompt(每次覆盖)
        scp(f"{srv}/voices.txt", voices_txt_path(), to_remote=True)
        scp(f"{srv}/voice_ref.wav", str(STUDIO / P["voice_ref"]), to_remote=True)
        scp(f"{srv}/ref_prompt.txt", str(STUDIO / P.get("ref_prompt", "assets/ref_prompt.txt")),
            to_remote=True)
        # 3) 服务器脚本:本地为准,md5 不同或缺就上传
        for fn in ("clone_pages.py", "setup_cosyvoice.sh"):
            lmd5, rmd5 = U.md5_of(loc_scripts / fn), ssh(
                f"md5sum {srv}/{fn} 2>/dev/null | cut -d' ' -f1",
                check=False).stdout.strip()
            if lmd5 != rmd5:
                scp(f"{srv}/{fn}", str(loc_scripts / fn), to_remote=True)
        # 4) CosyVoice 代码自愈(缺失自动补拉)
        ssh(f"bash {srv}/../setup_cosyvoice.sh 2>/dev/null || "
            f"bash {srv_path('setup_cosyvoice.sh')}")
        # 5) 合成(同步跑完,12 页约十几分钟)
        r = ssh(f"{SRV['clone_python']} {srv}/{SRV['clone_script']}", check=False)
        if "ALL_DONE" not in r.stdout:
            sys.exit(f"[④ fail] clone_pages 异常:\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
        still = [i for i in missing
                 if ssh(f"test -f {srv_path(SRV['pages_dir'])}/v2_p{i:02d}.wav",
                        check=False).returncode != 0]
        if still:
            sys.exit(f"[④ fail] 服务器仍缺: {still}")
    for i in range(npages):
        dst = WORK / f"{P['clone_page_prefix']}{i:02d}.wav"
        if not dst.exists():
            scp(srv_path(f"{SRV['pages_dir']}/v2_p{i:02d}.wav"), dst)
    print("[④ ok] 克隆音频齐")


# ---------------------------------------------------------------- ⑤ 口型

def step_lipsync():
    if CFG["layout"] != "board":
        print(f"[⑤] 跳过:layout={CFG['layout']} 不需要逐页口型(仅 board 用);"
              f"intro 版请走 opening 步骤")
        return
    print("── ⑤ 口型生成 ──")
    wait_gpu()
    sync_inputs()   # 即使只跑口型,输入指纹变了也会先清旧产物再干活
    npages = U.n_pages()
    ref = STUDIO / P["ref_image_white"]
    if ref.exists():
        scp(srv_path(SRV["ref_image"]), str(ref), to_remote=True)
        LIP.mkdir(parents=True, exist_ok=True)
        (LIP / "key.txt").write_text("white", encoding="utf-8")   # 键控跟随参考图底色
        print("[⑤] 白底参考图已上传,合成走白色键控")
    # 口型脚本同步:本地 server_scripts/ 为准,md5 不同或缺就上传(与 ④ 同一规矩)
    loc_scripts = STUDIO / "server_scripts"
    for fn in ("run_jobs.py", "batch_emv3_v2.py", "patch_infer_jobs.py"):
        lp = loc_scripts / fn
        if not lp.exists():
            continue
        lmd5, rmd5 = U.md5_of(lp), ssh(
            f"md5sum {srv_path(fn)} 2>/dev/null | cut -d' ' -f1",
            check=False).stdout.strip()
        if lmd5 != rmd5:
            scp(f"{srv_path(fn)}", str(lp), to_remote=True)
            print(f"[⑤] 已同步 {fn}")
    ssh(f"cd {SRV['root']} && {SRV['python']} {srv_path(SRV['patch_script'])}")
    r = ssh(f"cd {SRV['root']} && PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True "
            f"nohup {SRV['python']} run_jobs.py > {SRV['root']}/run_jobs.log 2>&1 & echo started")
    print(r.stdout.strip())
    # 轮询上限:整批口型超过 lipsync_timeout_min 仍未齐则判定卡死
    deadline = time.time() + SRV.get("lipsync_timeout_min", 120) * 60
    while True:
        if time.time() > deadline:
            sys.exit("[⑤ fail] 口型生成超时,日志: "
                     + ssh(f"tail -40 {srv_path('run_jobs.log')}").stdout)
        time.sleep(300)
        srv_wait_recover()   # 失联等待恢复,不掉线就杀整个流程
        done = ssh(f"ls {srv_path(SRV['lipsync_out_dir'])}/p*.mp4 2>/dev/null | wc -l").stdout.strip()
        tail = ssh(f"tail -2 {srv_path('emv3_batch_status.log')}").stdout.strip()
        print(f"[poll] {done}/{npages} 页 | {tail}")
        if done == str(npages):
            break
        if "FAIL" in tail or "aborted" in tail:
            sys.exit("[⑤ fail] " + ssh(f"tail -40 {srv_path('run_jobs.log')}").stdout)
    for i in range(npages):
        dst = LIP / f"{P['lipsync_prefix']}{i:02d}.mp4"
        if not dst.exists():
            scp(srv_path(f"{SRV['lipsync_out_dir']}/p{i:02d}.mp4"), dst)
    print(f"[⑤ ok] {npages} 个口型视频已下载")


def step_opening():
    """⑤b 开场白口型(intro 模式):单段 EMV3 推理。"""
    if CFG["layout"] != "intro":
        return
    print("── ⑤b 开场白口型 ──")
    wait_gpu()
    from compose import opening_audio
    # 参考形象按 config 上传(intro 也用白底图),键控标记同步写,绝不留旧图旧标记
    ref = STUDIO / P["ref_image_white"]
    if ref.exists():
        scp(srv_path(SRV["ref_image"]), str(ref), to_remote=True)
        LIP.mkdir(parents=True, exist_ok=True)
        (LIP / "key.txt").write_text("white", encoding="utf-8")
        print("[⑤b] 白底参考图已上传,合成走白色键控")
    owav = opening_audio(U.intro_text(), float(CFG["intro"]["max_sec"]))
    dur = U.wav_duration(owav)
    vl = min(SRV.get("opening_max_frames", 129), int(round(dur * 25)) + 2)
    job = [dict(image_path=srv_path(SRV["ref_image"]),
                audio_path=srv_path(f"{SRV['pages_dir']}/opening.wav"),
                save_path=f"{SRV['root']}/emv3_batch/opening",
                video_length=vl)]
    scp(srv_path(f"{SRV['pages_dir']}/opening.wav"), str(owav), to_remote=True)
    # 开场白音频指纹:音频一变,服务器旧口型成品作废重推理(防换题后旧脸旧声)
    import hashlib as _h
    afp = _h.md5(Path(owav).read_bytes()).hexdigest()
    rafp = ssh(f"cat {srv_path('_opening_audio.md5')} 2>/dev/null", check=False).stdout.strip()
    if rafp != afp:   # 无记录也视为不匹配:服务器有旧 mp4 但没指纹=来历不明,一律重做
        ssh(f"rm -f {srv_path(SRV['lipsync_out_dir'])}/opening.mp4")
        ssh(f"rm -rf {srv_path('emv3_batch/opening')}")
        if rafp:
            print("[⑤b] 开场白音频已变化,旧口型成品作废重推理")
    ssh(f"echo {afp} > {srv_path('_opening_audio.md5')}")
    jf = WORK / "opening_job.json"
    WORK.mkdir(parents=True, exist_ok=True)
    jf.write_text(json.dumps(job), encoding="utf-8")
    scp(srv_path("opening_job.json"), str(jf), to_remote=True)
    # 服务器脚本同步(与 ⑤ 同规矩,本地为准):run_jobs 单任务模式依赖 batch_emv3_v2
    loc_scripts = STUDIO / "server_scripts"
    for fn in ("run_jobs.py", "batch_emv3_v2.py", "patch_infer_jobs.py"):
        lp = loc_scripts / fn
        if not lp.exists():
            continue
        lmd5, rmd5 = U.md5_of(lp), ssh(
            f"md5sum {srv_path(fn)} 2>/dev/null | cut -d' ' -f1",
            check=False).stdout.strip()
        if lmd5 != rmd5:
            scp(srv_path(fn), str(lp), to_remote=True)
            print(f"[⑤b] 已同步 {fn}")
    ssh(f"cd {SRV['root']} && {SRV['python']} {srv_path(SRV['patch_script'])}")
    if ssh(f"test -f {srv_path(SRV['lipsync_out_dir'])}/opening.mp4",
           check=False).returncode != 0:
        # 复用 run_jobs.py 单任务模式(EMV3_OPENING_JOB):推理参数链与批量完全一致,
        # 不再裸调 infer_jobs(其 argparse required + 参数默认值是相对路径,必踩坑)
        ssh(f"cd {SRV['root']} && EMV3_OPENING_JOB={SRV['root']}/opening_job.json "
            f"PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True "
            f"nohup {SRV['python']} run_jobs.py > {SRV['root']}/opening_run.log 2>&1 & echo started")
        t0 = time.time()
        while True:
            if time.time() - t0 > SRV.get("opening_timeout_min", 20) * 60:
                sys.exit("[⑤b fail] 开场白推理超时,日志: "
                         + ssh(f"tail -30 {srv_path('opening_run.log')}"))
            time.sleep(20)
            srv_wait_recover()   # 失联等待恢复,不掉线就杀整个流程
            if ssh(f"test -f {srv_path(SRV['lipsync_out_dir'])}/opening.mp4",
                   check=False).returncode == 0:
                break
            # 进程活性检测:推理进程没了且产物没出,立即报错,不再傻等 20 分钟
            if ssh("pgrep -f 'run_jobs.py|infer_jobs.py'", check=False).returncode != 0:
                sys.exit("[⑤b fail] 推理进程已死但无产物,日志: "
                         + ssh(f"tail -30 {srv_path('opening_run.log')}"))
            tail = ssh(f"tail -2 {srv_path('opening_run.log')}").stdout
            if "Error" in tail or "Traceback" in tail:
                sys.exit("[⑤b fail] " + ssh(f"tail -30 {srv_path('opening_run.log')}"))
            print(f"[poll] 开场白推理中… {int(time.time()-t0)}s")
    scp(srv_path(f"{SRV['lipsync_out_dir']}/opening.mp4"), LIP / "lipsync_opening.mp4")
    print("[⑤b ok] lipsync_opening.mp4")


# ---------------------------------------------------------------- ⑥⑦

def step_compose():
    print("── ⑥ 合成 ──")
    subprocess.run([sys.executable, str(STUDIO / "compose.py")], cwd=str(STUDIO), check=True)
    print(f"[⑥ ok] {P['final']}/{P['output_name']}")


def step_shutdown():
    print("── ⑦ 关机 ──")
    for attempt in range(1, SRV["shutdown_retries"] + 1):
        ssh("shutdown", check=False)
        print(f"[⑦] 第 {attempt} 次指令已发,{SRV['shutdown_verify_sec']}s 后验证...")
        time.sleep(SRV["shutdown_verify_sec"])
        r = subprocess.run(["ssh", "-o", "ConnectTimeout=10", "-p", str(SRV["port"]),
                            f"root@{SRV['host']}", "echo alive"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            print(f"[⑦ ok] 实例已失联(第 {attempt} 次成功)")
            return
        print(f"[⑦] 仍在线,重试...")
    sys.exit("[⑦ fail] 请到控制台手动关机")


if __name__ == "__main__":
    steps = sys.argv[1:]
    # 步骤统一由 layout 决定:敲 lipsync 或 opening 都解析为当前版式
    # 实际需要的那种口型步骤(board=逐页口型,intro=开场白口型),命令敲错也不跑多余 GPU
    lip_step = "lipsync" if CFG["layout"] == "board" else "opening"
    steps = [lip_step if s in ("lipsync", "opening") else s for s in steps]
    if not steps:
        steps = ["content", "voice", lip_step, "compose", "shutdown"]
    for s in steps:
        {"content": step_content, "voice": step_voice, "lipsync": step_lipsync,
         "opening": step_opening, "compose": step_compose,
         "shutdown": step_shutdown}[s]()
    # 用完 GPU 即关机:本次运行跑完了最后一个 GPU 消耗步骤(lipsync/opening)
    # 且未显式安排 shutdown,则自动关机,不留烧钱的空转实例
    if "shutdown" not in steps and {"lipsync", "opening"} & set(steps):
        print("[auto] GPU 步骤全部完成,自动关机")
        step_shutdown()
    elif {"voice", "lipsync", "opening"} & set(steps):
        print("[hint] 本次运行未含 lipsync/opening,GPU 后续还要用,不自动关机;"
              "干完记得 `python pipeline.py shutdown`")
