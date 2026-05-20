from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import load_settings
from .models import (
    ApiEnvelope,
    ExtractRequest,
    ItineraryRequest,
    NextQuestionRequest,
    RecommendRequest,
)
from .services.ai_client import AIClient
from .services.amap_client import AmapClient
from .services.planner_service import PlannerService
from .services.weather_client import WeatherClient

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")
load_dotenv()

settings = load_settings()
API_VERSION = settings.version
SERVICE_NAME = settings.service_name

allowed_origins = list(settings.allowed_origins)
allow_credentials = settings.allow_credentials
allowed_origins_env_configured = settings.allowed_origins_env_configured

app = FastAPI(title="Travel AI Planner API", version=API_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_client = AIClient(settings)
amap_client = AmapClient(settings)
weather_client = WeatherClient(settings)
planner = PlannerService(settings, ai=ai_client, amap=amap_client, weather=weather_client)


def _envelope(data: Any, meta: dict[str, Any]) -> ApiEnvelope:
    return ApiEnvelope(
        data=data,
        warning=meta.get("warning"),
        dataSourceLabel=meta.get("dataSourceLabel"),
        aiEnabled=meta.get("aiEnabled"),
        amapEnabled=meta.get("amapEnabled"),
        backendMode=meta.get("backendMode", True),
        aiErrorType=meta.get("aiErrorType"),
        aiErrorMessage=meta.get("aiErrorMessage"),
        aiRawPreview=meta.get("aiRawPreview"),
        aiChoicesContentFound=meta.get("aiChoicesContentFound"),
        aiParsedJsonOk=meta.get("aiParsedJsonOk"),
        weather=meta.get("weather"),
    )


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Travel AI Planner API", "version": API_VERSION}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME, "version": API_VERSION}


@app.get("/api/health")
def api_health() -> dict[str, Any]:
    return {
        **health(),
        "aiEnabled": settings.ai_enabled,
        "amapEnabled": settings.amap_enabled,
        "dataMode": settings.data_mode,
    }


@app.get("/api/debug/cors")
def debug_cors() -> dict[str, list[str] | bool]:
    return {
        "allowedOrigins": allowed_origins,
        "allowCredentials": allow_credentials,
        "envConfigured": allowed_origins_env_configured,
    }


@app.get("/api/debug/config")
def debug_config() -> dict[str, Any]:
    """返回非敏感的运行时配置，方便从前端快速判断当前是否启用了 AI / 高德。

    严格不返回任何 Key 或完整密钥；ai_base_url 只作为调试提示，不包含凭据。
    """
    return {
        "service": SERVICE_NAME,
        "version": API_VERSION,
        "aiProvider": settings.ai_provider,
        "aiEnabled": settings.ai_enabled,
        "aiBaseUrl": settings.ai_base_url if settings.ai_enabled else "",
        "aiModel": settings.ai_model if settings.ai_enabled else "",
        "amapEnabled": settings.amap_enabled,
        "allowedOrigins": allowed_origins,
        "dataMode": settings.data_mode,
    }


@app.get("/api/debug/ai")
async def debug_ai(probe: bool = Query(False)) -> dict[str, Any]:
    """V4.1 调试接口：默认只返回配置状态，probe=1 时真实请求一次 AI。

    用于排查 DeepSeek / OpenAI 兼容端点接入失败的真实原因。
    严格不返回 API Key；rawPreview 已脱敏并截断（成功 ≤300 / 失败 ≤500 字符）。
    """
    if not probe:
        return ai_client.debug_status()
    return await ai_client.debug_probe()


@app.get("/api/debug/weather")
async def debug_weather(city: str = Query("杭州")) -> dict[str, Any]:
    """V4.3 调试接口：用现有 AMAP_KEY 查询一次高德天气，返回脱敏摘要。

    - 不返回任何 Key；只暴露 city / weather / temperature / humidity / wind / reporttime / forecast。
    - AMAP_KEY 未配置时返回 status=disabled。
    - 高德返回失败时返回 status=error 并附 reason，不抛 500。
    """
    if not weather_client.enabled:
        return {
            "status": "disabled",
            "reason": "AMAP_KEY 未配置，无法查询天气。",
            "amapEnabled": False,
        }
    summary = await weather_client.fetch_summary(city)
    return {**summary, "amapEnabled": True}


@app.post("/api/chat/next-question")
def next_question(payload: NextQuestionRequest) -> ApiEnvelope:
    questions = [
        ("destination", "这次想去哪里？"),
        ("startDate", "什么时候出发？"),
        ("days", "准备玩几天？"),
        ("peopleCount", "同行一共几个人？"),
        ("pace", "你喜欢什么旅行强度？"),
        ("interests", "这趟更想体验什么？"),
        ("dislikes", "有哪些明确不喜欢的内容？"),
        ("budgetLevel", "预算大概是什么水平？"),
        ("hotelArea", "住宿区域定了吗？"),
        ("transportPreference", "当地交通更偏好什么？"),
    ]
    answered = set(payload.answeredKeys)
    for key, title in questions:
        if key not in answered:
            return ApiEnvelope(data={"key": key, "title": title, "finished": False})
    return ApiEnvelope(data={"finished": True})


@app.post("/api/places/recommend")
async def recommend_places(payload: RecommendRequest) -> ApiEnvelope:
    places, meta = await planner.recommend_places(payload.preference, payload.guideText)
    return _envelope([place.model_dump() for place in places], meta)


@app.post("/api/places/extract")
async def extract_places(payload: ExtractRequest) -> ApiEnvelope:
    places, meta = await planner.extract_places(payload.preference, payload.text)
    return _envelope([place.model_dump() for place in places], meta)


@app.post("/api/itinerary/generate")
async def generate_itinerary(payload: ItineraryRequest) -> ApiEnvelope:
    days, meta = await planner.generate_itinerary(payload.preference, payload.places)
    return _envelope([day.model_dump() for day in days], meta)


def infer_end_date(start_date: str, days: int) -> str:
    if not start_date:
        return ""
    try:
        start = datetime.fromisoformat(start_date)
        return (start + timedelta(days=days - 1)).date().isoformat()
    except ValueError:
        return ""
