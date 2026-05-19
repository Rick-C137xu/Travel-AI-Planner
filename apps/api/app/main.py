import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai_client import AIClient
from .mock_data import mock_extract_places, mock_itinerary, mock_places
from .models import (
    ApiEnvelope,
    DayPlan,
    ExtractRequest,
    ItineraryRequest,
    NextQuestionRequest,
    Place,
    RecommendRequest,
)

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")
load_dotenv()

API_VERSION = "v3"
SERVICE_NAME = "travel-ai-planner-api"
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://travel-ai-planner-lake.vercel.app",
]


def get_allowed_origins(raw_value: str | None) -> list[str]:
    if raw_value is None:
        return DEFAULT_ALLOWED_ORIGINS
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    if "*" in origins:
        return ["*"]
    return origins or DEFAULT_ALLOWED_ORIGINS


allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
allowed_origins_env_configured = allowed_origins_env is not None
allowed_origins = get_allowed_origins(allowed_origins_env)
allow_credentials = "*" not in allowed_origins

app = FastAPI(title="Travel AI Planner API", version=API_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_client = AIClient()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Travel AI Planner API", "version": API_VERSION}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME, "version": API_VERSION}


@app.get("/api/health")
def api_health() -> dict[str, str | bool]:
    return {**health(), "aiEnabled": ai_client.enabled}


@app.get("/api/debug/cors")
def debug_cors() -> dict[str, list[str] | bool]:
    return {
        "allowedOrigins": allowed_origins,
        "allowCredentials": allow_credentials,
        "envConfigured": allowed_origins_env_configured,
    }


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
    fallback = mock_places(payload.preference)
    if not ai_client.enabled:
        return ApiEnvelope(data=[place.model_dump() for place in fallback], warning="未配置 AI_API_KEY，已使用 mock 候选地点。")

    result, warning = await ai_client.json_completion(
        system_prompt=(
            "你是旅行规划助手。只能返回 JSON，不要返回 Markdown。"
            "JSON 格式为 {\"places\": Place[]}，Place 字段必须包含："
            "id,name,type,address,lat,lng,reason,suitableFor,estimatedTime,warning,source,userStatus。"
            "type 只能是 景点/餐厅/商圈/博物馆/夜市/自然风景/交通点/其他；source 使用 AI推荐；userStatus 使用 backup。"
        ),
        user_prompt=(
            "根据以下旅行需求推荐 10-20 个候选地点，不要直接生成路线。"
            "推荐要兼顾偏好、雷区、预算和旅行强度。\n"
            f"旅行需求：{payload.preference.model_dump_json(ensure_ascii=False)}\n"
            f"用户粘贴攻略补充：{payload.guideText[:4000]}"
        ),
    )
    try:
        raw_places = result.get("places", result) if isinstance(result, dict) else result
        places = [Place.model_validate(item).model_dump() for item in raw_places]
        return ApiEnvelope(data=places, warning=warning)
    except Exception:
        return ApiEnvelope(data=[place.model_dump() for place in fallback], warning=warning or "AI 地点 JSON 解析失败，已使用 mock 数据。")


@app.post("/api/places/extract")
async def extract_places(payload: ExtractRequest) -> ApiEnvelope:
    fallback = mock_extract_places(payload.preference, payload.text)
    if not ai_client.enabled:
        return ApiEnvelope(data=[place.model_dump() for place in fallback], warning="未配置 AI_API_KEY，已使用 mock 文本提取。")

    result, warning = await ai_client.json_completion(
        system_prompt=(
            "你是攻略文本结构化助手。只能返回 JSON，不要返回 Markdown。"
            "JSON 格式为 {\"places\": Place[]}。从文本中提取地点、推荐理由和避坑信息，source 使用 用户粘贴攻略，userStatus 使用 backup。"
        ),
        user_prompt=f"目的地：{payload.preference.destination}\n攻略文本：{payload.text[:6000]}",
    )
    try:
        raw_places = result.get("places", result) if isinstance(result, dict) else result
        places = [Place.model_validate(item).model_dump() for item in raw_places]
        return ApiEnvelope(data=places, warning=warning)
    except Exception:
        return ApiEnvelope(data=[place.model_dump() for place in fallback], warning=warning or "AI 提取 JSON 解析失败，已使用 mock 数据。")


@app.post("/api/itinerary/generate")
async def generate_itinerary(payload: ItineraryRequest) -> ApiEnvelope:
    fallback = mock_itinerary(payload.preference, payload.places)
    if not ai_client.enabled:
        return ApiEnvelope(data=[day.model_dump() for day in fallback], warning="未配置 AI_API_KEY，已使用 mock 行程。")

    density = {"relaxed": "每天 2-3 个主要地点", "normal": "每天 3-4 个主要地点", "intense": "每天 4-6 个主要地点"}[
        payload.preference.pace
    ]
    result, warning = await ai_client.json_completion(
        system_prompt=(
            "你是旅行行程规划助手。只能返回 JSON，不要返回 Markdown。"
            "JSON 格式为 {\"days\": DayPlan[]}。DayPlan 字段：day,date,title,items。"
            "ItineraryItem 字段：id,timeLabel,placeId,placeName,activity,estimatedDuration,transportSuggestion,note。"
            "行程不要太满，按地理与体力合理安排。"
        ),
        user_prompt=(
            f"旅行需求：{payload.preference.model_dump_json(ensure_ascii=False)}\n"
            f"强度密度要求：{density}\n"
            f"已选地点：{json.dumps([place.model_dump() for place in payload.places], ensure_ascii=False)}"
        ),
    )
    try:
        raw_days = result.get("days", result) if isinstance(result, dict) else result
        days = [DayPlan.model_validate(item).model_dump() for item in raw_days]
        return ApiEnvelope(data=days, warning=warning)
    except Exception:
        return ApiEnvelope(data=[day.model_dump() for day in fallback], warning=warning or "AI 行程 JSON 解析失败，已使用 mock 数据。")


def infer_end_date(start_date: str, days: int) -> str:
    if not start_date:
        return ""
    try:
        start = datetime.fromisoformat(start_date)
        return (start + timedelta(days=days - 1)).date().isoformat()
    except ValueError:
        return ""
