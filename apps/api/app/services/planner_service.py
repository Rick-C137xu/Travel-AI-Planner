"""V4 规划服务：根据当前是否配置了 AI / 高德 Key 选择不同的实现路径。

四种运行模式：
1. AI + Amap：AI 生成关键词 → 高德搜索真实 POI → AI 补充推荐文案。
2. Amap only：根据 preference 规则生成关键词 → 高德搜索 → 模板文案。
3. AI only：AI 直接生成候选地点；无地图校验，warning 中说明。
4. 都没有：保持现有后端 Mock。

对所有外部失败都做 try/except，绝不向前端抛堆栈。
"""

from __future__ import annotations

import json
import math
import uuid
from typing import Any

from ..config import Settings
from ..mock_data import mock_extract_places, mock_itinerary, mock_places
from ..models import DayPlan, ItineraryItem, Place, TravelPreference
from .ai_client import AIClient
from .amap_client import AmapClient


ITINERARY_AI_PLACE_LIMIT = 8

PLACE_TYPE_BY_AMAP = [
    ("餐饮", "餐厅"),
    ("美食", "餐厅"),
    ("购物", "商圈"),
    ("商务", "商圈"),
    ("博物馆", "博物馆"),
    ("展览馆", "博物馆"),
    ("科教", "博物馆"),
    ("夜市", "夜市"),
    ("酒吧", "夜市"),
    ("风景", "景点"),
    ("公园", "自然风景"),
    ("自然", "自然风景"),
    ("山", "自然风景"),
    ("湖", "自然风景"),
    ("海", "自然风景"),
    ("火车站", "交通点"),
    ("机场", "交通点"),
    ("地铁", "交通点"),
    ("汽车站", "交通点"),
]


def _map_place_type(amap_type_label: str) -> str:
    label = amap_type_label or ""
    for keyword, mapped in PLACE_TYPE_BY_AMAP:
        if keyword in label:
            return mapped
    return "景点"


def _short_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lng1 = a
    lat2, lng2 = b
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


class PlannerService:
    def __init__(
        self,
        settings: Settings,
        ai: AIClient | None = None,
        amap: AmapClient | None = None,
    ) -> None:
        self.settings = settings
        self.ai = ai or AIClient(settings)
        self.amap = amap or AmapClient(settings)

    # ---- 推荐地点 ----
    async def recommend_places(
        self, preference: TravelPreference, guide_text: str
    ) -> tuple[list[Place], dict[str, Any]]:
        ai_on = self.ai.enabled
        amap_on = self.amap.enabled

        if ai_on and amap_on:
            places, warning, ai_succeeded = await self._recommend_ai_amap(preference, guide_text)
            if places and ai_succeeded:
                return places, _meta(
                    label="高德地图 + AI",
                    ai=True,
                    amap=True,
                    warning=warning,
                )
            if places and not ai_succeeded:
                # POI 仍来自高德，文案降级为模板；明确告知用户 AI 失败
                return places, _meta(
                    label="高德地图 + 后端模板",
                    ai=True,
                    amap=True,
                    warning=_ai_fallback_warning(warning, keep_amap_places=True),
                )
            # AI + Amap 全失败（连 POI 都拿不到），向下降级
        if amap_on:
            places, warning = await self._recommend_amap_only(preference)
            if places:
                return places, _meta(
                    label="高德地图",
                    ai=False,
                    amap=True,
                    warning=warning,
                )
        if ai_on:
            places, warning = await self._recommend_ai_only(preference, guide_text)
            if places:
                return places, _meta(
                    label="AI 生成",
                    ai=True,
                    amap=False,
                    warning=warning or "未配置 AMAP_KEY，AI 推荐结果未经过地图校验。",
                )
        return self._recommend_mock(preference, reason="未配置 AI_API_KEY / AMAP_KEY")

    async def _recommend_ai_amap(
        self, preference: TravelPreference, guide_text: str
    ) -> tuple[list[Place], str | None, bool]:
        """返回 (places, warning, ai_succeeded)。

        ai_succeeded 为 True 表示 AI 注释成功补全了至少部分 POI 的推荐文案。
        若 ai_succeeded 为 False 但 places 非空，说明 POI 来自高德、文案为模板。
        """
        keywords = await self._ai_keywords(preference, guide_text)
        keyword_ai_ok = bool(keywords)
        if not keywords:
            keywords = _rule_keywords(preference)

        pois = await self._collect_amap_pois(keywords, preference.destination, limit=20)
        if not pois:
            return [], "高德 POI 搜索结果为空，已尝试降级。", False

        annotated, ai_warning, annotate_ok = await self._ai_annotate_pois(preference, pois)
        ai_succeeded = keyword_ai_ok and annotate_ok
        return annotated, ai_warning, ai_succeeded

    async def _recommend_amap_only(
        self, preference: TravelPreference
    ) -> tuple[list[Place], str | None]:
        keywords = _rule_keywords(preference)
        pois = await self._collect_amap_pois(keywords, preference.destination, limit=18)
        if not pois:
            return [], "高德 POI 搜索结果为空。"
        places = [_poi_to_place(poi, preference, source="高德地图") for poi in pois]
        return places, None

    async def _recommend_ai_only(
        self, preference: TravelPreference, guide_text: str
    ) -> tuple[list[Place], str | None]:
        result, warning = await self.ai.json_completion(
            system_prompt=(
                "你是旅行规划助手。只能返回 JSON，不要返回 Markdown。"
                "JSON 格式为 {\"places\": Place[]}，Place 字段必须包含："
                "id,name,type,address,lat,lng,reason,suitableFor,estimatedTime,warning,source,userStatus。"
                "type 只能是 景点/餐厅/商圈/博物馆/夜市/自然风景/交通点/其他；"
                "source 使用 \"AI推荐\"；userStatus 使用 \"backup\"。"
                "如果不确定经纬度，用 null。"
            ),
            user_prompt=(
                "根据以下旅行需求推荐 10-15 个候选地点，不要直接生成路线。\n"
                f"旅行需求：{preference.model_dump_json()}\n"
                f"用户粘贴攻略补充（可选）：{guide_text[:4000]}"
            ),
        )
        places = _safe_parse_places(result)
        return places, warning

    def _recommend_mock(
        self, preference: TravelPreference, reason: str
    ) -> tuple[list[Place], dict[str, Any]]:
        fallback = mock_places(preference, source="后端 Mock")
        return fallback, _meta(
            label="后端 Mock",
            ai=False,
            amap=False,
            warning=f"后端已连接成功，但{reason}，当前使用后端 Mock 候选地点。",
        )

    async def _ai_keywords(
        self, preference: TravelPreference, guide_text: str
    ) -> list[str]:
        result, _ = await self.ai.json_completion(
            system_prompt=(
                "你是旅行关键词助手。只返回 JSON，格式为 {\"keywords\": string[]}。"
                "根据旅行需求，列出 4-6 个用于地图 POI 搜索的中文关键词，"
                "比如「外滩」「南京路步行街」「老字号餐厅」等。不要解释，不要返回 Markdown。"
            ),
            user_prompt=(
                f"旅行需求：{preference.model_dump_json()}\n"
                f"用户粘贴攻略（可选）：{guide_text[:2000]}"
            ),
            temperature=0.3,
        )
        if isinstance(result, dict):
            keywords = result.get("keywords") or []
        elif isinstance(result, list):
            keywords = result
        else:
            keywords = []
        cleaned: list[str] = []
        for item in keywords:
            if isinstance(item, str) and item.strip():
                cleaned.append(item.strip())
        return cleaned[:6]

    async def _collect_amap_pois(
        self, keywords: list[str], city: str, *, limit: int
    ) -> list[dict[str, Any]]:
        seen_names: set[str] = set()
        collected: list[dict[str, Any]] = []
        for keyword in keywords:
            pois = await self.amap.search_pois(keyword, city=city, offset=8)
            for poi in pois:
                name = poi.get("name") or ""
                if not name or name in seen_names:
                    continue
                seen_names.add(name)
                poi["search_keyword"] = keyword
                collected.append(poi)
                if len(collected) >= limit:
                    return collected
        return collected

    async def _ai_annotate_pois(
        self, preference: TravelPreference, pois: list[dict[str, Any]]
    ) -> tuple[list[Place], str | None, bool]:
        compact = [
            {
                "name": poi.get("name", ""),
                "address": poi.get("address", ""),
                "type_label": poi.get("type_label", ""),
            }
            for poi in pois
        ]
        result, warning = await self.ai.json_completion(
            system_prompt=(
                "你是旅行规划助手。给定一组真实 POI 数据，请补充每个地点的推荐理由、适合人群、"
                "建议停留时间和避坑提醒。只返回 JSON，格式为 {\"places\": "
                "[{\"name\": str, \"reason\": str, \"suitableFor\": str, \"estimatedTime\": str, \"warning\": str}]}。"
                "name 必须与输入完全一致；不要返回 Markdown，不要新增地点。"
            ),
            user_prompt=(
                f"旅行需求：{preference.model_dump_json()}\n"
                f"待补充的 POI 列表：{json.dumps(compact, ensure_ascii=False)}"
            ),
        )
        annotations: dict[str, dict[str, str]] = {}
        if isinstance(result, dict):
            raw_list = result.get("places") or []
            for item in raw_list:
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    annotations[item["name"]] = {
                        "reason": str(item.get("reason") or ""),
                        "suitableFor": str(item.get("suitableFor") or ""),
                        "estimatedTime": str(item.get("estimatedTime") or ""),
                        "warning": str(item.get("warning") or ""),
                    }

        annotate_ok = bool(annotations)
        places: list[Place] = []
        for poi in pois:
            extra = annotations.get(poi.get("name", ""), {})
            source = "AI + 高德" if (annotate_ok and extra) else "高德地图"
            places.append(_poi_to_place(poi, preference, source=source, extra=extra))
        return places, warning, annotate_ok

    # ---- 攻略提取 ----
    async def extract_places(
        self, preference: TravelPreference, text: str
    ) -> tuple[list[Place], dict[str, Any]]:
        ai_on = self.ai.enabled
        amap_on = self.amap.enabled

        if ai_on:
            result, warning = await self.ai.json_completion(
                system_prompt=(
                    "你是攻略文本结构化助手。只返回 JSON，格式为 "
                    "{\"places\": [{\"name\": str, \"reason\": str, \"suitableFor\": str, "
                    "\"estimatedTime\": str, \"warning\": str}]}。"
                    "从文本里识别真实存在的地点，忽略明显主观情绪和无关内容。"
                ),
                user_prompt=(
                    f"目的地：{preference.destination}\n"
                    f"攻略文本：{text[:6000]}"
                ),
            )
            ai_places: list[dict[str, str]] = []
            if isinstance(result, dict):
                raw = result.get("places") or []
                for item in raw:
                    if isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"].strip():
                        ai_places.append(
                            {
                                "name": item["name"].strip(),
                                "reason": str(item.get("reason") or "用户粘贴攻略中提到的地点。"),
                                "suitableFor": str(item.get("suitableFor") or "攻略补充地点"),
                                "estimatedTime": str(item.get("estimatedTime") or "1-2 小时"),
                                "warning": str(item.get("warning") or "来源为粘贴文本，建议二次核对。"),
                            }
                        )
            if ai_places:
                if amap_on:
                    enriched = await self._enrich_extracted_with_amap(ai_places, preference.destination)
                    return enriched, _meta(
                        label="高德地图 + AI",
                        ai=True,
                        amap=True,
                        warning=warning,
                    )
                places = [
                    Place(
                        id=_short_id("guide"),
                        name=item["name"],
                        type="其他",
                        address="",
                        lat=None,
                        lng=None,
                        reason=item["reason"],
                        suitableFor=item["suitableFor"],
                        estimatedTime=item["estimatedTime"],
                        warning=item["warning"],
                        source="用户粘贴攻略",
                        userStatus="backup",
                    )
                    for item in ai_places
                ]
                return places, _meta(
                    label="AI 提取",
                    ai=True,
                    amap=False,
                    warning=warning,
                )
            # AI 抽取失败，向下降级
        # 规则降级（不依赖 AI）
        rule_places = mock_extract_places(preference, text)
        if amap_on and rule_places:
            enriched = await self._enrich_extracted_with_amap(
                [
                    {
                        "name": p.name,
                        "reason": p.reason,
                        "suitableFor": p.suitableFor,
                        "estimatedTime": p.estimatedTime,
                        "warning": p.warning,
                    }
                    for p in rule_places
                ],
                preference.destination,
            )
            if ai_on:
                warning_msg = "AI 请求失败，已降级为后端模板，地点仍来自高德 POI。"
            else:
                warning_msg = "未配置 AI_API_KEY，使用规则提取并通过高德校验。"
            return enriched, _meta(
                label="高德地图 + 后端模板",
                # 后端能力侧仍上报真实配置，便于前端区分"AI 配了但失败" vs "AI 未配置"
                ai=ai_on,
                amap=True,
                warning=warning_msg,
            )
        if ai_on:
            warning_msg = "AI 请求失败，已使用规则提取。"
        else:
            warning_msg = "未配置 AI_API_KEY，已使用后端规则提取。"
        return rule_places, _meta(
            label="后端 Mock",
            ai=ai_on,
            amap=False,
            warning=warning_msg,
        )

    async def _enrich_extracted_with_amap(
        self, items: list[dict[str, str]], city: str
    ) -> list[Place]:
        enriched: list[Place] = []
        for item in items:
            pois = await self.amap.search_pois(item["name"], city=city, offset=1)
            poi = pois[0] if pois else None
            enriched.append(
                Place(
                    id=_short_id("guide"),
                    name=poi["name"] if poi else item["name"],
                    type=_map_place_type(poi["type_label"]) if poi else "其他",
                    address=poi["address"] if poi else "",
                    lat=poi["lat"] if poi else None,
                    lng=poi["lng"] if poi else None,
                    reason=item["reason"],
                    suitableFor=item["suitableFor"],
                    estimatedTime=item["estimatedTime"],
                    warning=item["warning"] if poi else (item["warning"] or "高德未匹配到该地点，请人工确认。"),
                    source="用户粘贴攻略",
                    userStatus="backup",
                )
            )
        return enriched

    # ---- 行程生成 ----
    async def generate_itinerary(
        self, preference: TravelPreference, places: list[Place]
    ) -> tuple[list[DayPlan], dict[str, Any]]:
        ai_on = self.ai.enabled
        amap_on = self.amap.enabled

        if not places:
            mock = mock_itinerary(preference, places)
            return mock, _meta(
                label="后端 Mock",
                ai=False,
                amap=False,
                warning="未选择任何想去的地点，已使用后端 Mock 行程。",
            )

        ordered = _sort_places_by_geo(places) if amap_on else list(places)

        if ai_on:
            density = {
                "relaxed": "每天 2-3 个主要地点",
                "normal": "每天 3-4 个主要地点",
                "intense": "每天 4-6 个主要地点",
            }[preference.pace]
            compact_places = _compact_places_for_itinerary(ordered)
            compact_preference = _compact_preference_for_ai(preference)
            itinerary_max_tokens = 900 if preference.days <= 3 else 1000
            result, warning, ai_diagnostic = await self.ai.json_completion_detailed(
                system_prompt=(
                    "你是旅行行程规划助手。只返回严格 json object，不要 markdown，不要解释。"
                    "只能输出这个 JSON 结构：{\"days\":[{\"title\":\"\",\"date\":\"\",\"items\":["
                    "{\"time\":\"09:00-11:00\",\"placeName\":\"\",\"description\":\"短句\","
                    "\"duration\":\"\",\"tips\":\"短句\"}]}]}。"
                    "只能使用输入地点 name。description/tips 每项不超过 30 个中文字符。"
                ),
                user_prompt=(
                    "生成行程 json，只输出 JSON 对象。\n"
                    f"需求：{json.dumps(compact_preference, ensure_ascii=False)}\n"
                    f"密度：{density}\n"
                    f"地点（最多 {ITINERARY_AI_PLACE_LIMIT} 个，已排序）："
                    f"{json.dumps(compact_places, ensure_ascii=False)}"
                ),
                temperature=0.3,
                max_tokens=itinerary_max_tokens,
            )
            days = _safe_parse_days(result)
            if days:
                label = "高德地图 + AI" if amap_on else "AI 生成"
                return days, _meta(
                    label=label,
                    ai=True,
                    amap=amap_on,
                    warning=warning,
                )
            if result is not None and not warning:
                warning = "AI itinerary schema parse failed"
                ai_diagnostic = {
                    **ai_diagnostic,
                    "errorType": "itinerary_schema_error",
                    "errorMessage": "AI JSON 已解析，但未能映射为 DayPlan/ItineraryItem",
                    "rawPreview": _preview_json(result),
                    "parsedJsonOk": True,
                }
            # AI 失败：若有高德，POI 仍来自高德，文案/行程模板降级
            mock = mock_itinerary(preference, ordered)
            fallback_label = "高德地图 + 后端模板" if amap_on else "后端 Mock"
            fallback_warning = (
                _ai_fallback_warning(warning, keep_amap_places=True)
                if amap_on
                else (warning or "AI 返回格式异常，已使用后端 Mock 行程。")
            )
            return mock, _meta(
                label=fallback_label,
                ai=True,
                amap=amap_on,
                warning=fallback_warning,
                ai_diagnostic=ai_diagnostic,
            )

        # 没有 AI 时直接走 mock
        mock = mock_itinerary(preference, ordered)
        label = "高德地图" if amap_on else "后端 Mock"
        warning = (
            "未配置 AI_API_KEY，已基于高德经纬度排序后使用后端模板生成行程。"
            if amap_on
            else "后端已连接成功，但未配置 AI_API_KEY，当前使用后端 Mock 行程。"
        )
        return mock, _meta(
            label=label,
            ai=False,
            amap=amap_on,
            warning=warning,
        )


def _meta(
    *,
    label: str,
    ai: bool,
    amap: bool,
    warning: str | None,
    ai_diagnostic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = {
        "dataSourceLabel": label,
        "aiEnabled": ai,
        "amapEnabled": amap,
        "backendMode": True,
        "warning": warning,
    }
    if ai_diagnostic:
        meta.update(
            {
                "aiErrorType": ai_diagnostic.get("errorType"),
                "aiErrorMessage": ai_diagnostic.get("errorMessage"),
                "aiRawPreview": ai_diagnostic.get("rawPreview"),
                "aiChoicesContentFound": ai_diagnostic.get("choicesContentFound"),
                "aiParsedJsonOk": ai_diagnostic.get("parsedJsonOk"),
            }
        )
    return meta


def _ai_fallback_warning(warning: str | None, *, keep_amap_places: bool) -> str:
    if warning and "超时" in warning:
        base = "AI 请求超时，已使用后端模板。"
    elif warning and ("格式" in warning or "JSON" in warning or "json" in warning):
        base = "AI 返回格式异常，已使用后端模板。"
    else:
        base = "AI 请求失败，已使用后端模板。"
    if keep_amap_places:
        base += " 地点仍来自高德 POI。"
    if warning:
        base += f" 详情：{warning}"
    return base


def _rule_keywords(preference: TravelPreference) -> list[str]:
    destination = preference.destination or ""
    interests = preference.interests or ["景点", "美食"]
    keyword_map = {
        "美食": "美食",
        "自然风景": "公园",
        "拍照": "网红打卡",
        "博物馆": "博物馆",
        "夜市": "夜市",
        "购物": "商圈",
        "Citywalk": "步行街",
        "亲子": "亲子乐园",
        "情侣": "观景台",
    }
    keywords: list[str] = []
    seen: set[str] = set()
    if destination:
        for label in [f"{destination}景点", f"{destination}地标"]:
            if label not in seen:
                seen.add(label)
                keywords.append(label)
    for interest in interests:
        mapped = keyword_map.get(interest, interest)
        target = f"{destination}{mapped}" if destination else mapped
        if target and target not in seen:
            seen.add(target)
            keywords.append(target)
        if len(keywords) >= 6:
            break
    if not keywords:
        keywords = ["景点", "美食"]
    return keywords[:6]


def _poi_to_place(
    poi: dict[str, Any],
    preference: TravelPreference,
    *,
    source: str,
    extra: dict[str, str] | None = None,
) -> Place:
    extra = extra or {}
    place_type = _map_place_type(poi.get("type_label") or "")
    interests_text = "、".join(preference.interests) or "本地体验"
    default_reason = f"{poi.get('name', '')}由高德 POI 搜索返回，{interests_text}方向值得一去。"
    return Place(
        id=poi.get("id") or _short_id("amap"),
        name=poi.get("name", ""),
        type=place_type,  # type: ignore[arg-type]
        address=poi.get("address") or "",
        lat=poi.get("lat"),
        lng=poi.get("lng"),
        reason=extra.get("reason") or default_reason,
        suitableFor=extra.get("suitableFor") or interests_text,
        estimatedTime=extra.get("estimatedTime")
        or ("1-1.5 小时" if place_type == "餐厅" else "1.5-2.5 小时"),
        warning=extra.get("warning") or "请提前核对营业时间，节假日注意人流。",
        source=source,
        userStatus="backup",
    )


def _compact_preference_for_ai(preference: TravelPreference) -> dict[str, Any]:
    return {
        "destination": preference.destination,
        "startDate": preference.startDate,
        "days": preference.days,
        "peopleCount": preference.peopleCount,
        "pace": preference.pace,
        "interests": preference.interests[:6],
        "dislikes": preference.dislikes[:6],
        "budgetLevel": preference.budgetLevel,
        "hotelArea": preference.hotelArea,
        "transportPreference": preference.transportPreference[:4],
    }


def _compact_places_for_itinerary(places: list[Place]) -> list[dict[str, Any]]:
    selected = [place for place in places if place.userStatus == "want"] or list(places)
    compact: list[dict[str, Any]] = []
    for place in selected[:ITINERARY_AI_PLACE_LIMIT]:
        item: dict[str, Any] = {
            "id": place.id,
            "name": place.name,
            "type": place.type,
            "address": place.address,
            "reason": place.reason,
            "estimatedTime": place.estimatedTime,
            "warning": place.warning,
        }
        compact.append(item)
    return compact


def _preview_json(value: Any, *, limit: int = 300) -> str:
    try:
        preview = json.dumps(value, ensure_ascii=False)
    except TypeError:
        preview = str(value)
    return preview[:limit] + ("...<truncated>" if len(preview) > limit else "")


def _safe_parse_places(result: Any) -> list[Place]:
    if isinstance(result, dict):
        raw = result.get("places") or result.get("data") or []
    elif isinstance(result, list):
        raw = result
    else:
        return []
    places: list[Place] = []
    for item in raw:
        try:
            place = Place.model_validate(item)
        except Exception:  # noqa: BLE001 - 单条失败不影响整体
            continue
        if not place.id:
            place.id = _short_id("ai")
        places.append(place)
    return places


def _safe_parse_days(result: Any) -> list[DayPlan]:
    if isinstance(result, dict):
        raw = result.get("days") or result.get("itinerary") or result.get("plan") or result.get("data") or []
        if not raw and "items" in result:
            raw = [result]
    elif isinstance(result, list):
        raw = result
    else:
        return []
    days: list[DayPlan] = []
    for day_index, item in enumerate(raw, start=1):
        try:
            day = DayPlan.model_validate(_normalize_day_payload(item, day_index))
        except Exception:  # noqa: BLE001
            continue
        # 补 id 兜底，避免前端 :key 冲突
        for it in day.items:
            if not it.id:
                it.id = _short_id("item")
        days.append(day)
    return days


def _normalize_day_payload(item: Any, day_index: int) -> Any:
    if not isinstance(item, dict):
        return item
    normalized = dict(item)
    normalized.setdefault("day", day_index)
    normalized.setdefault("title", f"Day {day_index}")
    normalized.setdefault("date", "")
    normalized_items: list[Any] = []
    for item_index, raw_item in enumerate(normalized.get("items") or [], start=1):
        if not isinstance(raw_item, dict):
            normalized_items.append(raw_item)
            continue
        place_name = str(raw_item.get("placeName") or raw_item.get("name") or "")
        normalized_items.append(
            {
                "id": str(raw_item.get("id") or _short_id("item")),
                "timeLabel": str(raw_item.get("timeLabel") or raw_item.get("time") or ""),
                "placeId": str(raw_item.get("placeId") or place_name or f"place-{day_index}-{item_index}"),
                "placeName": place_name,
                "activity": str(raw_item.get("activity") or raw_item.get("description") or ""),
                "estimatedDuration": str(raw_item.get("estimatedDuration") or raw_item.get("duration") or ""),
                "transportSuggestion": str(raw_item.get("transportSuggestion") or ""),
                "note": str(raw_item.get("note") or raw_item.get("tips") or ""),
            }
        )
    normalized["items"] = normalized_items
    return normalized


def _sort_places_by_geo(places: list[Place]) -> list[Place]:
    """简单的最近邻排序，没有经纬度的地点放后面。"""
    geo: list[Place] = [p for p in places if p.lat is not None and p.lng is not None]
    no_geo: list[Place] = [p for p in places if p.lat is None or p.lng is None]
    if len(geo) <= 1:
        return geo + no_geo
    ordered: list[Place] = [geo[0]]
    remaining = geo[1:]
    while remaining:
        last = ordered[-1]
        last_pt = (float(last.lat or 0.0), float(last.lng or 0.0))
        nearest_idx = 0
        nearest_dist = float("inf")
        for idx, candidate in enumerate(remaining):
            pt = (float(candidate.lat or 0.0), float(candidate.lng or 0.0))
            d = _haversine(last_pt, pt)
            if d < nearest_dist:
                nearest_dist = d
                nearest_idx = idx
        ordered.append(remaining.pop(nearest_idx))
    return ordered + no_geo


# 防止未使用 import 警告
_ = ItineraryItem
