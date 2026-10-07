"""通用LLM客户端 - 基于OpenAI兼容协议

不绑定特定厂商/模型：DeepSeek、通义千问(兼容模式)、GPT、Kimi、GLM 等
所有兼容 OpenAI Chat Completions 协议的服务均可通过 base_url + model 接入。
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger("llm.client")


class LLMClient:
    """通用LLM客户端（OpenAI兼容协议）"""

    def __init__(self, api_key: str, base_url: str, model: str):
        if not api_key:
            raise ValueError("LLM_API_KEY 未配置")
        self.model = model
        # 异步客户端（供异步调用方使用）
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        # 同步客户端（供同步服务层/调度器使用）
        self.sync_client = OpenAI(api_key=api_key, base_url=base_url)

    # ---------- 核心方法 ----------

    async def chat_async(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """异步对话"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """同步对话"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.sync_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    # ---------- 业务方法 ----------

    def extract_topics(self, transcript_text: str, max_topics: int = 3) -> List[Dict[str, Any]]:
        """从转写文本提取选题"""
        system = (
            "你是短视频选题策划专家。从视频转写文本中提炼有热度的选题，"
            "严格按JSON数组格式返回，不要输出其他内容。"
        )
        prompt = f"""从以下视频转写文本中提取最多{max_topics}个选题，返回JSON数组：
[{{"title": "选题标题", "summary": "选题摘要", "keywords": ["关键词1"], "category": "分类", "hot_score": 0.0, "quality_score": 0.0}}]

视频转写文本：
{transcript_text[:4000]}"""

        content = self.chat(prompt, system=system, temperature=0.5)
        return self._parse_json_list(content)

    def summarize_text(self, text: str) -> str:
        """文本摘要"""
        return self.chat(
            f"请将以下内容总结为200字以内的摘要：\n\n{text[:4000]}",
            temperature=0.3
        )

    def generate_content(self, prompt: str) -> str:
        """生成内容"""
        return self.chat(prompt)

    def transcribe_video(self, video_url: str) -> str:
        """视频转写（占位：实际应由ASR服务完成，LLM仅做文本整理）

        保留此方法以兼容服务层调用，真实转写走阿里云ASR。
        """
        raise NotImplementedError("视频转写应由ASR服务（阿里云ASR）完成，LLM不直接处理音频")

    # ---------- 工具方法 ----------

    @staticmethod
    def _parse_json_list(content: str) -> List[Dict[str, Any]]:
        """解析LLM返回的JSON列表（容忍markdown代码块等杂质）"""
        try:
            # 提取 ```json ... ``` 或首个 [ ... ] 块
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                return json.loads(match.group())
            logger.warning("LLM返回内容中未找到JSON数组: %s", content[:200])
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("解析LLM选题JSON失败: %s", e)
            return []
