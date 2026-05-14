from datetime import date, datetime, timedelta
from itertools import cycle

from .models import DayPlan, ItineraryItem, Place, TravelPreference


TYPE_BY_INTEREST = {
    "美食": "餐厅",
    "自然风景": "自然风景",
    "拍照": "景点",
    "博物馆": "博物馆",
    "夜市": "夜市",
    "购物": "商圈",
    "Citywalk": "景点",
    "亲子": "景点",
    "情侣": "景点",
}


def mock_places(preference: TravelPreference, source: str = "Mock数据") -> list[Place]:
    destination = preference.destination or "目的地"
    interests = preference.interests or ["美食", "Citywalk", "博物馆", "自然风景", "夜市"]
    templates = [
        ("老城 Citywalk 街区", "适合第一天熟悉城市节奏，沿路可穿插咖啡和小店。", "步行闲逛、拍照、轻体验"),
        ("城市代表博物馆", "了解目的地历史文化，雨天也很稳。", "文化爱好者、亲子、慢节奏旅行"),
        ("本地口碑小吃街", "一次覆盖多种本地小吃，适合把晚餐安排得灵活一点。", "美食探索、朋友出游"),
        ("核心商圈", "交通方便，吃饭购物选择多，适合作为行程缓冲点。", "购物、餐饮、晚间活动"),
        ("城市公园或湖畔", "给行程留出放松空间，适合拍照和散步。", "自然风景、情侣、亲子"),
        ("夜市或夜生活街区", "晚上氛围更好，适合不想太早回酒店的人。", "夜游、美食、拍照"),
        ("特色咖啡馆片区", "适合下午休息，也能作为不赶路的备选。", "轻松旅行、拍照"),
        ("地标观景点", "第一次到访值得打卡，建议避开正午和高峰。", "拍照、城市初访"),
        ("本地菜餐厅", "更适合正式吃一顿本地风味，预算可控。", "美食、情侣、家庭"),
        ("周边自然半日游", "适合想看风景的人，强度会比市区略高。", "自然风景、轻徒步"),
        ("独立书店与文创街", "适合慢逛和买伴手礼，不会占用太多体力。", "Citywalk、购物"),
        ("交通枢纽附近补给点", "适合抵达或离开当天安排，减少绕路。", "中转、轻量行程"),
    ]
    places: list[Place] = []
    interest_cycle = cycle(interests)
    base_lat = 31.2304
    base_lng = 121.4737
    for index, (name, reason, suitable) in enumerate(templates, start=1):
        interest = next(interest_cycle)
        place_type = TYPE_BY_INTEREST.get(interest, "其他")
        if "餐厅" in name:
            place_type = "餐厅"
        if "夜市" in name:
            place_type = "夜市"
        if "商圈" in name:
            place_type = "商圈"
        places.append(
            Place(
                id=f"mock-{index}",
                name=f"{destination}{name}",
                type=place_type,  # type: ignore[arg-type]
                address=f"{destination}市中心区域",
                lat=base_lat + index * 0.01 if index <= 8 else None,
                lng=base_lng + index * 0.012 if index <= 8 else None,
                reason=reason,
                suitableFor=suitable,
                estimatedTime="1.5-2.5 小时" if place_type != "餐厅" else "1-1.5 小时",
                warning=_warning_for(preference, place_type),
                source=source,  # type: ignore[arg-type]
                userStatus="backup",
            )
        )
    return places


def mock_extract_places(preference: TravelPreference, text: str) -> list[Place]:
    words = [line.strip(" -，。,.;；") for line in text.splitlines() if line.strip()]
    names = words[:6] or ["攻略提到的咖啡馆", "攻略提到的观景点", "攻略提到的小吃店"]
    destination = preference.destination or "目的地"
    return [
        Place(
            id=f"guide-{index}",
            name=name if destination in name else f"{destination}{name[:18]}",
            type="其他",
            address="",
            reason="从用户粘贴攻略文本中提取，建议后续人工确认营业时间和位置。",
            suitableFor="攻略补充地点",
            estimatedTime="1-2 小时",
            warning="来源为粘贴文本，可能需要二次核对。",
            source="用户粘贴攻略",
            userStatus="backup",
        )
        for index, name in enumerate(names, start=1)
    ]


def mock_itinerary(preference: TravelPreference, places: list[Place]) -> list[DayPlan]:
    selected = places or mock_places(preference)[:6]
    per_day = {"relaxed": 3, "normal": 4, "intense": 5}[preference.pace]
    slots = ["上午", "中午", "下午", "晚上", "夜间"]
    start = _parse_date(preference.startDate)
    plans: list[DayPlan] = []
    cursor = 0
    for day in range(1, preference.days + 1):
        day_places = selected[cursor : cursor + per_day]
        if not day_places:
            day_places = selected[: min(per_day, len(selected))]
        cursor += per_day
        items = [
            ItineraryItem(
                id=f"day-{day}-item-{index}",
                timeLabel=slots[index - 1] if index <= len(slots) else f"第 {index} 段",
                placeId=place.id,
                placeName=place.name,
                activity=f"体验{place.type}，重点关注：{place.reason}",
                estimatedDuration=place.estimatedTime,
                transportSuggestion=_transport_text(preference),
                note=place.warning or "留出机动时间，现场按体力调整。",
            )
            for index, place in enumerate(day_places, start=1)
        ]
        plans.append(
            DayPlan(
                day=day,
                date=(start + timedelta(days=day - 1)).isoformat() if start else "",
                title=f"{preference.destination or '目的地'}第 {day} 天",
                items=items,
            )
        )
    return plans


def _warning_for(preference: TravelPreference, place_type: str) -> str:
    dislikes = set(preference.dislikes)
    if "排队" in dislikes:
        return "热门时段可能排队，建议错峰或保留备选。"
    if "太赶路" in dislikes:
        return "建议与相邻区域组合，避免跨城折返。"
    if place_type == "自然风景" and "爬山" in dislikes:
        return "如涉及爬坡，可替换为市区公园。"
    return "提前核对开放时间，周末适当错峰。"


def _transport_text(preference: TravelPreference) -> str:
    if not preference.transportPreference:
        return "优先选择少换乘路线。"
    return f"优先{preference.transportPreference[0]}，跨区时保留打车选项。"


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None
