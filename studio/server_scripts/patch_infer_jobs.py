# -*- coding: utf-8 -*-
"""把 infer_flash.py 打补丁为 infer_jobs.py:支持 EMV3_JOBS 任务清单循环推理(模型只加载一次)"""
src = "/root/autodl-tmp/EchoMimicV3/repo/infer_flash.py"
dst = "/root/autodl-tmp/EchoMimicV3/repo/infer_jobs.py"

txt = open(src).read()
marker = "    with torch.no_grad():\n"
i1 = txt.rindex(marker)
i2 = txt.index("\n\nif __name__")
block = txt[i1 + len(marker):i2]
# 原块整体缩进 +4(放入 for 循环内)
indented = "".join(("    " + l if l.strip() else l) for l in block.splitlines(keepends=True))

head = '''    _jobs_file = os.environ.get("EMV3_JOBS")
    if _jobs_file:
        import json as _json
        with open(_jobs_file) as _f:
            jobs = _json.load(_f)
        print(f"JOBS MODE: {len(jobs)} segments")
    else:
        jobs = [dict(image_path=image_path, audio_path=audio_path,
                     save_path=save_path, video_length=video_length)]

    for _job in jobs:
        image_path = _job["image_path"]
        audio_path = _job["audio_path"]
        save_path = _job["save_path"]
        video_length = int(_job["video_length"])
        os.makedirs(save_path, exist_ok=True)
'''

new = txt[:i1] + head + "        with torch.no_grad():\n" + indented + txt[i2:]
# image_name 改为按音频名生成,保证每段输出文件名唯一
new = new.replace('image_name = os.path.basename(image_path).split(\'.\')[0]',
                  'image_name = os.path.splitext(os.path.basename(audio_path))[0]')
open(dst, "w").write(new)
print("patched ->", dst)
