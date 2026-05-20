"""V4.3 高德天气服务封装。

使用现有 AMAP_KEY，调用高德天气查询 API（https://restapi.amap.com/v3/weather/weatherInfo）。
- live (extensions=base)：实时天气，含 weather/temperature/humidity/winddirection/windpower/reporttime。
- forecast (extensions=all)：未来 3-4 天预报，含 dayweather/daytemp/nighttemp/daywind/daypower。

所有请求都带 timeout；任何错误都会被捕获并返回结构化 dict，不抛异常。
不在代码中写死 Key；Key 来自 Settings.amap_key。返回内容也不会包含 Key。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from ..config import Settings

logger = logging.getLogger(__name__)

AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"


class WeatherClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.amap_enabled

    async def fetch_summary(
        self,
        city: str,
        *,
        timeout: float = 6.0,
    ) -> dict[str, Any]:
        """返回精简天气摘要 dict。失败时 status=error 并附 reason，不抛异常。"""
        if not self.enabled:
            return {
                "status": "disabled",
                "reason": "AMAP_KEY 未配置，无法查询天气。",
                "source": "amap-weather",
            }
        if not city or not city.strip():
            return {
                "status": "error",
                "reason": "city 参数为空，无法查询天气。",
                "source": "amap-weather",
            }
        city = city.strip()

        live_task = self._request(city, "base", timeout=timeout)
        forecast_task = self._request(city, "all", timeout=timeout)
        live_payload, forecast_payload = await asyncio.gather(
            live_task, forecast_task, return_exceptions=True
        )

        result: dict[str, Any] = {
            "status": "error",
            "city": city,
            "source": "amap-weather",
        }

        live = _pick_live(live_payload)
        forecast = _pick_forecast(forecast_payload)

        if live:
            result.update(
                {
                    "status": "ok",
                    "city": live.get("city") or city,
                    "weather": live.get("weather", ""),
                    "temperature": live.get("temperature", ""),
                    "winddirection": live.get("winddirection", ""),
                    "windpower": live.get("windpower", ""),
                    "humidity": live.get("humidity", ""),
                    "reporttime": live.get("reporttime", ""),
                }
            )
        elif forecast and forecast.get("casts"):
            today = forecast["casts"][0]
            result.update(
                {
                    "status": "ok",
                    "city": forecast.get("city") or city,
                    "weather": today.get("dayweather", ""),
                    "temperature": today.get("daytemp", ""),
                    "winddirection": today.get("daywind", ""),
                    "windpower": today.get("daypower", ""),
                    "humidity": "",
                    "reporttime": forecast.get("reporttime", "")
                    or today.get("date", ""),
                }
            )

        if forecast and forecast.get("casts"):
            casts = forecast["casts"][:4]
            result["forecast"] = [
                {
                    "date": c.get("date", ""),
                    "week": c.get("week", ""),
                    "dayweather": c.get("dayweather", ""),
                    "nightweather": c.get("nightweather", ""),
                    "daytemp": c.get("daytemp", ""),
                    "nighttemp": c.get("nighttemp", ""),
                    "daywind": c.get("daywind", ""),
                    "daypower": c.get("daypower", ""),
                }
                for c in casts
                if isinstance(c, dict)
            ]

        if result["status"] != "ok":
            result["reason"] = "高德天气查询失败或返回为空，已降级。"
        return result

    async def _request(
        self, city: str, extensions: str, *, timeout: float
    ) -> dict[str, Any] | None:
        params = {
            "key": self._settings.amap_key,
            "city": city,
            "extensions": extensions,
            "output": "JSON",
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(AMAP_WEATHER_URL, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError:
            logger.warning("amap weather http error city=%s ext=%s", city, extensions)
            return None
        except ValueError:
            logger.warning("amap weather json decode error city=%s", city)
            return None
        if str(payload.get("status")) != "1":
            logger.warning(
                "amap weather non-ok status: info=%s city=%s ext=%s",
                payload.get("info"),
                city,
                extensions,
            )
            return None
        return payload


def _pick_live(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    lives = payload.get("lives") or []
    if not isinstance(lives, list) or not lives:
        return None
    first = lives[0]
    return first if isinstance(first, dict) else None


def _pick_forecast(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    forecasts = payload.get("forecasts") or []
    if not isinstance(forecasts, list) or not forecasts:
        return None
    first = forecasts[0]
    return first if isinstance(first, dict) else None


def build_prompt_line(weather: dict[str, Any]) -> str:
    """把 weather dict 压成单行提示语，用于 AI prompt。失败返回空串。"""
    if not weather or weather.get("status") != "ok":
        return ""
    parts: list[str] = []
    city = weather.get("city") or ""
    wx = weather.get("weather") or ""
    temp = weather.get("temperature") or ""
    humidity = weather.get("humidity") or ""
    wind = weather.get("winddirection") or ""
    power = weather.get("windpower") or ""
    head = f"天气参考：{city}".rstrip("：")
    if wx:
        head += f"，{wx}"
    if temp:
        head += f"，{temp}℃"
    if humidity:
        head += f"，湿度 {humidity}%"
    if wind or power:
        head += f"，{wind}风 {power}级"
    parts.append(head + "。")
    return "".join(parts)[:120]
