"""V4 高德地图 Web 服务封装。

仅使用文档化的高德 Web API：
- POI 搜索（关键字搜索）：https://restapi.amap.com/v3/place/text
所有请求都带 timeout，并且失败时返回空列表，由上层走 Mock fallback。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import Settings

logger = logging.getLogger(__name__)

AMAP_TEXT_URL = "https://restapi.amap.com/v3/place/text"


class AmapClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.amap_enabled

    async def search_pois(
        self,
        keyword: str,
        city: str = "",
        *,
        offset: int = 10,
        page: int = 1,
        timeout: float = 12.0,
    ) -> list[dict[str, Any]]:
        if not self.enabled or not keyword:
            return []

        params = {
            "key": self._settings.amap_key,
            "keywords": keyword,
            "offset": str(offset),
            "page": str(page),
            "extensions": "base",
            "output": "JSON",
        }
        if city:
            params["city"] = city
            params["citylimit"] = "true"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(AMAP_TEXT_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError:
            logger.warning("amap http error for keyword=%s", keyword)
            return []
        except ValueError:
            logger.warning("amap json decode error for keyword=%s", keyword)
            return []

        if str(payload.get("status")) != "1":
            logger.warning("amap non-ok status: %s", payload.get("info"))
            return []

        pois = payload.get("pois") or []
        results: list[dict[str, Any]] = []
        for poi in pois:
            if not isinstance(poi, dict):
                continue
            location = str(poi.get("location") or "")
            lat: float | None = None
            lng: float | None = None
            if "," in location:
                try:
                    lng_s, lat_s = location.split(",", 1)
                    lng = float(lng_s)
                    lat = float(lat_s)
                except ValueError:
                    lat = lng = None
            results.append(
                {
                    "id": str(poi.get("id") or ""),
                    "name": str(poi.get("name") or "").strip(),
                    "address": str(poi.get("address") or "").strip(),
                    "type_label": str(poi.get("type") or "").strip(),
                    "lat": lat,
                    "lng": lng,
                    "tel": str(poi.get("tel") or "").strip(),
                }
            )
        return [item for item in results if item["name"]]
