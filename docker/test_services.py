#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LLM / ASR 服务连通性测试（读取 docker/.env）"""
import io
import os
import sys
import wave
import struct
import math

# 加载 .env
def load_env(path):
    if not os.path.exists(path):
        print(f"❌ 未找到配置文件: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env(os.path.join(os.path.dirname(__file__), ".env"))

from openai import OpenAI

PASS, FAIL = "✅ 通过", "❌ 失败"
results = []


def record(name, ok, detail):
    results.append((name, PASS if ok else FAIL, detail))
    print(f"{PASS if ok else FAIL}  {name}: {detail}")


# ---------- 1. LLM 连通性测试 ----------
print("\n===== 1. LLM 连通性测试 =====")
try:
    base_url = os.environ["LLM_BASE_URL"]
    model = os.environ["LLM_MODEL"]
    llm = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=base_url)
    resp = llm.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "回复两个字：正常"}],
        max_tokens=16,
        temperature=0,
    )
    text = resp.choices[0].message.content.strip()
    record("LLM 对话", True, f"base_url={base_url}, model={model}, 回复=\"{text}\"")
except Exception as e:
    record("LLM 对话", False, f"{type(e).__name__}: {str(e)[:200]}")

# ---------- 2. LLM 选题提取测试（模拟业务调用） ----------
print("\n===== 2. LLM 选题提取测试 =====")
try:
    transcript = ("大家好，今天聊聊AI视频自动化。现在用AI一键生成短视频已经非常成熟了，"
                  "从脚本、配音到画面全自动，一个月可以做几百条视频。普通人也能靠这个做自媒体变现。")
    prompt = f"""从以下视频转写文本中提取2个选题，返回JSON数组：
[{{"title": "选题标题", "summary": "摘要", "keywords": ["关键词"], "hot_score": 0.0}}]

文本：{transcript}"""
    resp = llm.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.3,
    )
    content = resp.choices[0].message.content
    import json, re
    m = re.search(r"\[.*\]", content, re.DOTALL)
    topics = json.loads(m.group()) if m else []
    record("LLM 选题提取", len(topics) > 0,
           f"提取到{len(topics)}个选题: {[t.get('title') for t in topics]}")
except Exception as e:
    record("LLM 选题提取", False, f"{type(e).__name__}: {str(e)[:200]}")

# ---------- 3. ASR 连通性测试 ----------
print("\n===== 3. ASR 连通性测试（硅基流动 SenseVoice） =====")
try:
    asr_base = os.environ["ASR_BASE_URL"]
    asr_model = os.environ["ASR_MODEL"]

    # 生成1秒440Hz正弦波测试音频（验证API链路是否通）
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        frames = b"".join(
            struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / 16000)))
            for i in range(16000)
        )
        w.writeframes(frames)
    buf.seek(0)

    asr = OpenAI(api_key=os.environ["ASR_API_KEY"], base_url=asr_base)
    result = asr.audio.transcriptions.create(model=asr_model, file=("test.wav", buf, "audio/wav"))
    record("ASR 转写", True,
           f"base_url={asr_base}, model={asr_model}, 返回=\"{getattr(result, 'text', result)!r}\"")
except Exception as e:
    record("ASR 转写", False, f"{type(e).__name__}: {str(e)[:200]}")

# ---------- 4. config.py 校验 ----------
print("\n===== 4. 项目 config.py 校验 =====")
os.environ["LLM_API_KEY"] = os.environ.get("LLM_API_KEY", "")
os.environ["ASR_API_KEY"] = os.environ.get("ASR_API_KEY", "")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hotspot-monitor-service"))
try:
    import importlib
    import config as svc_config
    importlib.reload(svc_config)
    v = svc_config.validate_config()
    record("config 校验", v["valid"], "无缺失配置" if v["valid"] else str(v["errors"]))
except Exception as e:
    record("config 校验", False, f"{type(e).__name__}: {str(e)[:200]}")

# ---------- 汇总 ----------
print("\n===== 测试汇总 =====")
print(f"{'测试项':<20}{'状态':<10}说明")
print("-" * 70)
all_ok = True
for name, status, detail in results:
    print(f"{name:<20}{status:<10}{detail[:60]}")
    if status != PASS:
        all_ok = False
print("-" * 70)
print("🎉 全部通过" if all_ok else "⚠️ 存在失败项，请检查上方错误信息")
sys.exit(0 if all_ok else 1)
