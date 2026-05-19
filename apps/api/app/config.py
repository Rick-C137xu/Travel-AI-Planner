"""V4 后端配置读取。

只从环境变量读取非敏感和敏感配置，绝不在源码里写死任何 Key。
通过实例化 Settings() 在应用启动时统一读取一次，方便调试接口和服务模块复用。
"""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://travel-ai-planner-lake.vercel.app",
]


def _parse_origins(raw_value: str | None) -> tuple[list[str], bool]:
    if raw_value is None:
        return list(DEFAULT_ALLOWED_ORIGINS), False
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    if "*" in origins:
        return ["*"], True
    return (origins or list(DEFAULT_ALLOWED_ORIGINS)), True


@dataclass(frozen=True)
class Settings:
    service_name: str = "travel-ai-planner-api"
    version: str = "v4.1"

    ai_provider: str = "openai-compatible"
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"

    amap_key: str = ""

    allowed_origins: tuple[str, ...] = tuple(DEFAULT_ALLOWED_ORIGINS)
    allowed_origins_env_configured: bool = False

    @property
    def ai_enabled(self) -> bool:
        return bool(self.ai_api_key)

    @property
    def amap_enabled(self) -> bool:
        return bool(self.amap_key)

    @property
    def data_mode(self) -> str:
        """V4.1 起，dataMode 命名统一为产品文案要求的版本。

        注意：这里返回的是"后端能力"层级的 dataMode；具体一次请求的真实 dataSourceLabel
        由 PlannerService 在请求时给出（可能因 AI 调用失败而降级为「高德地图 + 后端模板」）。
        """
        if self.ai_enabled and self.amap_enabled:
            return "高德地图 + AI"
        if self.amap_enabled:
            return "高德地图"
        if self.ai_enabled:
            return "AI 生成"
        return "后端 Mock"

    @property
    def allow_credentials(self) -> bool:
        return "*" not in self.allowed_origins


def load_settings() -> Settings:
    origins, configured = _parse_origins(os.getenv("ALLOWED_ORIGINS"))
    return Settings(
        ai_provider=os.getenv("AI_PROVIDER", "openai-compatible"),
        ai_api_key=os.getenv("AI_API_KEY", "").strip(),
        ai_base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        ai_model=os.getenv("AI_MODEL", "gpt-4o-mini"),
        amap_key=os.getenv("AMAP_KEY", "").strip(),
        allowed_origins=tuple(origins),
        allowed_origins_env_configured=configured,
    )
