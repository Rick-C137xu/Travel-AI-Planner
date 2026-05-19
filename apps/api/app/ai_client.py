"""V4 起 AIClient 已迁移到 ``app.services.ai_client``。

保留这个模块只是为了向后兼容直接 ``from .ai_client import AIClient`` 的旧引用。
新代码请直接从 ``app.services.ai_client`` / ``app.services.planner_service`` 引入。
"""

from __future__ import annotations

import os

from .config import load_settings
from .services.ai_client import AIClient as _ServiceAIClient, parse_json_content


class AIClient(_ServiceAIClient):
    """兼容旧用法：无参数构造，直接读取环境变量。"""

    def __init__(self) -> None:
        super().__init__(load_settings())
        # 暴露旧字段，避免外部代码直接访问 settings 时报错
        self.api_key = os.getenv("AI_API_KEY", "")
        self.base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")

__all__ = ["AIClient", "parse_json_content"]
