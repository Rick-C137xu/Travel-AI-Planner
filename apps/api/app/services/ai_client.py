"""V4.1 AI 调用封装。

支持 OpenAI-compatible Chat Completions 协议（OpenAI / DeepSeek / Moonshot / 通义千问 OpenAI 兼容端点等）。
- 不会把 Key 写入代码或日志。
- 所有外部请求都带 timeout。
- 任何异常都会被捕获，返回 (None, warning) 让上层走 Mock fallback。
- V4.1 新增：失败时记录结构化日志（status_code / errorType / 脱敏 errorPreview），
  并提供 ``debug_probe`` 给 ``/api/debug/ai`` 用，便于线上排查 DeepSeek / OpenAI 兼容端点的真实错误。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from ..config import Settings

logger = logging.getLogger("travel_ai_planner.ai")

# 用于脱敏的正则：Authorization Bearer、sk-xxx 风格 Key 等
_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE)
_SK_KEY_RE = re.compile(r"sk-[A-Za-z0-9_\-]{6,}", re.IGNORECASE)


def _sanitize(text: str | None, *, limit: int = 500) -> str:
    """删除可能出现的 Key 字符串并截断长度，用于日志 / 调试接口输出。"""
    if not text:
        return ""
    cleaned = _BEARER_RE.sub("Bearer ***", text)
    cleaned = _SK_KEY_RE.sub("sk-***", cleaned)
    if len(cleaned) > limit:
        cleaned = cleaned[:limit] + "...<truncated>"
    return cleaned


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

    @property
    def request_url(self) -> str:
        """返回最终请求 URL（不含 Key），用于日志与 /api/debug/ai。"""
        base = self._settings.ai_base_url.rstrip("/")
        return f"{base}/chat/completions"

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

        outcome = await self._raw_chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            timeout=timeout,
            require_json=True,
        )
        if outcome["ok"]:
            content = outcome["content"]
            try:
                return parse_json_content(content), None
            except (ValueError, json.JSONDecodeError) as exc:
                logger.warning(
                    "AI JSON parse failed: errorType=parse_error, model=%s, preview=%s",
                    self._settings.ai_model,
                    _sanitize(content, limit=500),
                )
                return None, f"AI 返回内容解析失败：{exc}".strip()
        return None, outcome["warning"]

    async def debug_probe(self, *, timeout: float = 20.0) -> dict[str, Any]:
        """调试用：发起一次最小化 chat/completions 请求，返回结构化诊断。

        - 不返回 API Key；rawPreview 经过脱敏；最大 500 字符。
        - 与业务路径解耦，方便在前端 /api/debug/ai 看到真实失败原因。
        """
        info: dict[str, Any] = {
            "aiConfigured": self.enabled,
            "aiProvider": self._settings.ai_provider,
            "aiBaseUrl": self._settings.ai_base_url if self.enabled else "",
            "aiModel": self._settings.ai_model if self.enabled else "",
            "requestUrl": self.request_url if self.enabled else "",
            "ok": False,
            "statusCode": None,
            "errorType": None,
            "errorMessage": None,
            "rawPreview": "",
            "parsedJsonOk": False,
        }
        if not self.enabled:
            info["errorType"] = "not_configured"
            info["errorMessage"] = "AI_API_KEY 未配置；请在 Render 后台配置并重新部署。"
            return info

        outcome = await self._raw_chat_completion(
            system_prompt=(
                "You are a connectivity probe. Reply with JSON only. "
                "The JSON must contain a single field named \"ok\" with value true."
            ),
            user_prompt='Return exactly this JSON: {"ok": true}',
            temperature=0.0,
            timeout=timeout,
            require_json=True,
            max_tokens=64,
        )
        info["statusCode"] = outcome.get("statusCode")
        info["errorType"] = outcome.get("errorType")
        info["errorMessage"] = outcome.get("warning")
        info["rawPreview"] = outcome.get("rawPreview", "")

        if outcome["ok"]:
            content = outcome["content"]
            info["rawPreview"] = _sanitize(content, limit=300)
            try:
                parse_json_content(content)
                info["parsedJsonOk"] = True
                info["ok"] = True
                info["errorType"] = None
                info["errorMessage"] = None
            except (ValueError, json.JSONDecodeError) as exc:
                info["ok"] = False
                info["parsedJsonOk"] = False
                info["errorType"] = "parse_error"
                info["errorMessage"] = f"AI 返回非合法 JSON：{exc}"
        return info

    async def _raw_chat_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        timeout: float,
        require_json: bool,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """实际 HTTP 调用层。返回 dict，包含 ok / content / warning / statusCode / errorType / rawPreview。"""
        url = self.request_url
        payload: dict[str, Any] = {
            "model": self._settings.ai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        if require_json:
            # DeepSeek / OpenAI 都要求 prompt 中含有 "json" 才能开启 json_object
            payload["response_format"] = {"type": "json_object"}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self._settings.ai_api_key}",
            "Content-Type": "application/json",
        }
        result: dict[str, Any] = {
            "ok": False,
            "content": "",
            "warning": None,
            "statusCode": None,
            "errorType": None,
            "rawPreview": "",
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
            result["statusCode"] = response.status_code
            if response.status_code >= 400:
                preview = _sanitize(response.text, limit=500)
                logger.warning(
                    "AI HTTP error: status=%s, model=%s, url=%s, preview=%s",
                    response.status_code,
                    self._settings.ai_model,
                    url,
                    preview,
                )
                result["errorType"] = "http_error"
                result["warning"] = f"AI 请求失败（HTTP {response.status_code}）"
                result["rawPreview"] = preview
                return result

            body = response.json()
            try:
                content = body["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                preview = _sanitize(json.dumps(body, ensure_ascii=False), limit=500)
                logger.warning(
                    "AI empty content: model=%s, preview=%s",
                    self._settings.ai_model,
                    preview,
                )
                result["errorType"] = "empty_content"
                result["warning"] = "AI 返回结构异常：未找到 choices[0].message.content"
                result["rawPreview"] = preview
                return result

            if not content or not str(content).strip():
                preview = _sanitize(json.dumps(body, ensure_ascii=False), limit=500)
                logger.warning(
                    "AI empty content body: model=%s, preview=%s",
                    self._settings.ai_model,
                    preview,
                )
                result["errorType"] = "empty_content"
                result["warning"] = "AI 返回 content 为空字符串"
                result["rawPreview"] = preview
                return result

            result["ok"] = True
            result["content"] = content
            return result

        except httpx.TimeoutException as exc:
            logger.warning(
                "AI timeout: model=%s, url=%s, errorType=timeout, detail=%s",
                self._settings.ai_model,
                url,
                _sanitize(str(exc), limit=200),
            )
            result["errorType"] = "timeout"
            result["warning"] = f"AI 请求超时（{timeout}s）"
            return result
        except httpx.HTTPError as exc:
            logger.warning(
                "AI request error: model=%s, url=%s, errorType=request_error, detail=%s",
                self._settings.ai_model,
                url,
                _sanitize(str(exc), limit=200),
            )
            result["errorType"] = "request_error"
            result["warning"] = f"AI 请求失败（{type(exc).__name__}）"
            return result
        except json.JSONDecodeError as exc:
            logger.warning(
                "AI response not JSON: model=%s, detail=%s",
                self._settings.ai_model,
                _sanitize(str(exc), limit=200),
            )
            result["errorType"] = "parse_error"
            result["warning"] = "AI 返回的 HTTP body 不是合法 JSON"
            return result
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "AI unknown error: model=%s, errorType=%s, detail=%s",
                self._settings.ai_model,
                type(exc).__name__,
                _sanitize(str(exc), limit=200),
            )
            result["errorType"] = "unknown"
            result["warning"] = f"AI 调用异常（{type(exc).__name__}）"
            return result


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
