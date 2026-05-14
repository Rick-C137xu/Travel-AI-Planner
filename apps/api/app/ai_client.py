import json
import os
import re
from typing import Any

import httpx


class AIClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("AI_API_KEY", "")
        self.base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def json_completion(self, system_prompt: str, user_prompt: str) -> tuple[Any | None, str | None]:
        if not self.enabled:
            return None, "未配置 AI_API_KEY，已使用 mock 数据。"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        }
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return parse_json_content(content), None
        except Exception as exc:  # noqa: BLE001 - API failures should never break the MVP flow.
            return None, f"AI 生成失败，已使用 mock 数据。原因：{exc}"


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

    start = min([idx for idx in [content.find("{"), content.find("[")] if idx >= 0], default=-1)
    end = max(content.rfind("}"), content.rfind("]"))
    if start >= 0 and end > start:
        return json.loads(content[start : end + 1])
    raise ValueError("AI 返回内容不是合法 JSON")
