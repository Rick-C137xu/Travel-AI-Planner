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

DEFAULT_TIMEOUT_SECONDS = 45.0
DEFAULT_MAX_TOKENS = 1600
DEBUG_TIMEOUT_SECONDS = 20.0
DEBUG_MAX_TOKENS = 32

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

    def debug_status(self) -> dict[str, Any]:
        return {
            "aiConfigured": self.enabled,
            "aiProvider": self._settings.ai_provider,
            "aiBaseUrl": self._settings.ai_base_url if self.enabled else "",
            "aiModel": self._settings.ai_model if self.enabled else "",
            "requestUrl": self.request_url if self.enabled else "",
            "timeoutSeconds": DEBUG_TIMEOUT_SECONDS,
            "maxTokens": DEBUG_MAX_TOKENS,
            "probeEnabled": False,
            "message": "默认不发起真实 AI 请求，如需测试请使用 ?probe=1",
        }

    async def json_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.4,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> tuple[Any | None, str | None]:
        if not self.enabled:
            return None, "未配置 AI_API_KEY，已使用 Mock 数据。"

        result, warning, _diagnostic = await self.json_completion_detailed(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            timeout=timeout,
            max_tokens=max_tokens,
        )
        return result, warning

    async def json_completion_detailed(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.4,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> tuple[Any | None, str | None, dict[str, Any]]:
        if not self.enabled:
            return None, "未配置 AI_API_KEY，已使用 Mock 数据。", {
                "errorType": "not_configured",
                "errorMessage": "AI_API_KEY 未配置",
                "rawPreview": "",
                "choicesContentFound": False,
                "parsedJsonOk": False,
            }

        outcome = await self._raw_chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            timeout=timeout,
            require_json=True,
            max_tokens=max_tokens,
        )
        if outcome["ok"]:
            content = outcome["content"]
            diagnostic = {
                "errorType": None,
                "errorMessage": None,
                "rawPreview": _sanitize(content, limit=300),
                "choicesContentFound": True,
                "parsedJsonOk": False,
            }
            try:
                parsed = parse_json_content(content)
                diagnostic["parsedJsonOk"] = True
                return parsed, None, diagnostic
            except (ValueError, json.JSONDecodeError) as exc:
                logger.warning(
                    "AI JSON parse failed: errorType=json_parse_error, model=%s, preview=%s",
                    self._settings.ai_model,
                    diagnostic["rawPreview"],
                )
                diagnostic["errorType"] = "json_parse_error"
                diagnostic["errorMessage"] = f"AI JSON 解析失败：{exc}"
                return None, "AI 返回格式异常，已使用后端模板", diagnostic
        diagnostic = {
            "errorType": outcome.get("errorType"),
            "errorMessage": outcome.get("warning"),
            "rawPreview": _sanitize(outcome.get("rawPreview", ""), limit=300),
            "choicesContentFound": outcome.get("choicesContentFound", False),
            "parsedJsonOk": False,
        }
        return None, outcome["warning"], diagnostic

    async def debug_probe(self, *, timeout: float = DEBUG_TIMEOUT_SECONDS) -> dict[str, Any]:
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
            "timeoutSeconds": timeout,
            "maxTokens": DEBUG_MAX_TOKENS,
            "probeEnabled": True,
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
            max_tokens=DEBUG_MAX_TOKENS,
        )
        info["statusCode"] = outcome.get("statusCode")
        info["errorType"] = outcome.get("errorType")
        info["errorMessage"] = outcome.get("warning")
        info["rawPreview"] = _sanitize(outcome.get("rawPreview", ""), limit=300)

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
                info["errorType"] = "json_parse_error"
                info["errorMessage"] = f"AI 返回格式异常：{exc}"
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
            "choicesContentFound": False,
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

            try:
                body = response.json()
            except json.JSONDecodeError:
                preview = _sanitize(response.text, limit=500)
                logger.warning(
                    "AI response not JSON: model=%s, preview=%s",
                    self._settings.ai_model,
                    preview,
                )
                result["errorType"] = "json_parse_error"
                result["warning"] = "AI 返回格式异常，已使用后端模板"
                result["rawPreview"] = preview
                return result
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
                result["warning"] = "AI 返回格式异常，已使用后端模板"
                result["rawPreview"] = preview
                result["choicesContentFound"] = False
                return result

            if not content or not str(content).strip():
                preview = _sanitize(json.dumps(body, ensure_ascii=False), limit=500)
                logger.warning(
                    "AI empty content body: model=%s, preview=%s",
                    self._settings.ai_model,
                    preview,
                )
                result["errorType"] = "empty_content"
                result["warning"] = "AI 返回格式异常，已使用后端模板"
                result["rawPreview"] = preview
                result["choicesContentFound"] = False
                return result

            result["ok"] = True
            result["content"] = content
            result["choicesContentFound"] = True
            return result

        except httpx.TimeoutException as exc:
            logger.warning(
                "AI timeout: model=%s, url=%s, errorType=timeout, detail=%s",
                self._settings.ai_model,
                url,
                _sanitize(str(exc), limit=200),
            )
            result["errorType"] = "timeout"
            result["warning"] = f"AI 请求超时（{timeout}s），已使用后端模板"
            return result
        except httpx.HTTPError as exc:
            logger.warning(
                "AI request error: model=%s, url=%s, errorType=request_error, detail=%s",
                self._settings.ai_model,
                url,
                _sanitize(str(exc), limit=200),
            )
            result["errorType"] = "request_error"
            result["warning"] = f"AI 请求失败（{type(exc).__name__}），已使用后端模板"
            return result
        except json.JSONDecodeError as exc:
            logger.warning(
                "AI response not JSON: model=%s, detail=%s",
                self._settings.ai_model,
                _sanitize(str(exc), limit=200),
            )
            result["errorType"] = "json_parse_error"
            result["warning"] = "AI 返回格式异常，已使用后端模板"
            return result
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "AI unknown error: model=%s, errorType=%s, detail=%s",
                self._settings.ai_model,
                type(exc).__name__,
                _sanitize(str(exc), limit=200),
            )
            result["errorType"] = "unknown"
            result["warning"] = f"AI 请求失败（{type(exc).__name__}），已使用后端模板"
            return result


def parse_json_content(content: str) -> Any:
    text = _strip_markdown_fence(content).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    extracted = _extract_first_json_value(text)
    if extracted:
        return json.loads(extracted)
    raise ValueError("AI 返回内容中未找到完整 JSON object 或 array")


def _strip_markdown_fence(content: str) -> str:
    text = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.S | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return re.sub(r"```(?:json)?|```", "", text, flags=re.IGNORECASE).strip()


def _extract_first_json_value(text: str) -> str | None:
    starts = [(idx, char) for idx, char in ((text.find("{"), "{"), (text.find("["), "[")) if idx >= 0]
    if not starts:
        return None
    start, _ = min(starts, key=lambda item: item[0])
    stack: list[str] = []
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        char = text[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]":
            if not stack:
                return None
            expected = "}" if stack[-1] == "{" else "]"
            if char != expected:
                return None
            stack.pop()
            if not stack:
                return text[start : idx + 1]
    return None
