"""V4 AI 调用封装。

支持 OpenAI-compatible Chat Completions 协议（OpenAI / DeepSeek / Moonshot / 通义千问 OpenAI 兼容端点等）。
- 不会把 Key 写入代码或日志。
- 所有外部请求都带 timeout。
- 任何异常都会被捕获，返回 (None, warning) 让上层走 Mock fallback。
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from ..config import Settings


class AIClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.ai_enabled

    @property
    def provider(self) -> str:
        return self._settings.ai_provider

    @property
    def model(self) -> str:
        return self._settings.ai_model

    async def json_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.4,
        timeout: float = 45.0,
    ) -> tuple[Any | None, str | None]:
        if not self.enabled:
            return None, "未配置 AI_API_KEY，已使用 Mock 数据。"

        url = f"{self._settings.ai_base_url}/chat/completions"
        payload = {
            "model": self._settings.ai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._settings.ai_api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return parse_json_content(content), None
        except httpx.HTTPStatusError as exc:
            # 不要把完整响应体或 token 透出给前端
            return None, f"AI 请求失败（HTTP {exc.response.status_code}），已使用降级数据。"
        except httpx.HTTPError:
            return None, "AI 请求失败（网络错误或超时），已使用降级数据。"
        except (KeyError, ValueError, json.JSONDecodeError):
            return None, "AI 返回内容解析失败，已使用降级数据。"
        except Exception:  # noqa: BLE001 - 兜底，绝不让前端因为 AI 异常崩溃
            return None, "AI 调用异常，已使用降级数据。"


def parse_json_content(content: str) -> Any:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(.*?)```", content, re.S)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    candidates: list[int] = [idx for idx in (content.find("{"), content.find("[")) if idx >= 0]
    start = min(candidates) if candidates else -1
    end = max(content.rfind("}"), content.rfind("]"))
    if start >= 0 and end > start:
        return json.loads(content[start : end + 1])
    raise ValueError("AI 返回内容不是合法 JSON")
