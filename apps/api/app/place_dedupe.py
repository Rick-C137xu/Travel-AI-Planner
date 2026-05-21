"""V4.3.4 POI 去重与全国通用主地点聚合（后端）。"""
from __future__ import annotations

import re
from typing import Iterable, TypeVar


_AUXILIARY_SUFFIXES: tuple[str, ...] = (
    "出租车上客点",
    "网约车上车点",
    "地下停车场",
    "地上停车场",
    "停车点",
    "停车场",
    "游客服务中心",
    "游客中心",
    "服务中心",
    "咨询处",
    "售票大厅",
    "售票厅",
    "售票处",
    "检票口",
    "候船厅",
    "码头候船厅",
    "公共厕所",
    "卫生间",
    "洗手间",
    "厕所",
    "公交站",
    "地铁站",
    "火车站",
    "汽车站",
    "机场",
    "进出口",
    "出入口",
    "入口",
    "出口",
    "东门",
    "西门",
    "南门",
    "北门",
    "正门",
    "后门",
    "侧门",
)

_AUXILIARY_CATEGORY_HINTS: tuple[str, ...] = (
    "停车场",
    "停车点",
    "公交站",
    "地铁站",
    "火车站",
    "汽车站",
    "机场",
    "出入口",
    "卫生间",
    "洗手间",
    "公共厕所",
    "厕所",
    "出租车",
    "网约车",
    "加油站",
    "充电站",
    "售票处",
    "游客中心",
)

_LODGING_KEYWORDS: tuple[str, ...] = (
    "酒店",
    "宾馆",
    "旅馆",
    "客栈",
    "民宿",
    "公寓",
    "青旅",
    "青年旅舍",
    "住宿",
    "旅社",
    "招待所",
)

_FOOD_SHOP_KEYWORDS: tuple[str, ...] = (
    "餐厅",
    "饭店",
    "小吃店",
    "便利店",
    "超市",
    "商铺",
)

_LOW_VALUE_KEYWORDS: tuple[str, ...] = (
    "写字楼",
    "商务楼",
    "办公楼",
    "小区",
    "住宅",
    "售楼处",
    "房产",
    "中介",
)

_UNIVERSITY_SUBUNIT_KEYWORDS: tuple[str, ...] = (
    "校区",
    "学院",
    "学部",
    "系",
    "图书馆",
    "食堂",
    "教学楼",
    "实验楼",
    "宿舍",
    "体育馆",
    "行政楼",
    "研究院",
    "东门",
    "西门",
    "南门",
    "北门",
    "正门",
    "停车场",
    "生活区",
    "学生公寓",
    "校医院",
    "南校园",
    "北校园",
    "东校园",
    "西校园",
)

_SCENIC_MAIN_TERMS: tuple[str, ...] = (
    "风景区",
    "博物院",
    "博物馆",
    "纪念馆",
    "步行街",
    "旅游区",
    "公园",
    "景区",
    "古镇",
    "古城",
    "老街",
    "街区",
    "广场",
    "码头",
    "寺",
    "庙",
    "宫",
    "塔",
    "湖",
    "山",
    "岛",
    "湾",
    "滩",
    "坊",
    "巷",
    "街",
    "园",
    "城",
    "村",
    "寨",
)

_SCENIC_CHILD_KEYWORDS: tuple[str, ...] = (
    "游客中心",
    "服务中心",
    "东广场",
    "西广场",
    "南广场",
    "北广场",
    "游乐场",
    "游船码头",
    "码头",
    "午门",
    "神武门",
    "东门",
    "西门",
    "南门",
    "北门",
    "入口",
    "出口",
    "售票处",
    "停车场",
    "音乐喷泉",
    "步行街",
    "秦淮风光带",
)

_SCENIC_AGGREGATION_RULES: tuple[tuple[str, str], ...] = (
    ("翠湖", "翠湖公园"),
    ("西湖风景区", "西湖风景区"),
    ("西湖", "西湖"),
    ("宽窄巷子", "宽窄巷子"),
    ("故宫博物院", "故宫博物院"),
    ("故宫", "故宫博物院"),
    ("夫子庙", "夫子庙"),
    ("鼓浪屿", "鼓浪屿"),
    ("滇池", "滇池"),
    ("海埂大坝", "滇池海埂大坝"),
    ("西山", "西山风景区"),
    ("金马坊", "金马碧鸡坊"),
    ("金马碧鸡坊", "金马碧鸡坊"),
    ("昆明老街", "昆明老街"),
    ("南强街", "南强街"),
    ("斗南花卉市场", "斗南花市"),
    ("斗南花市", "斗南花市"),
)

_KNOWN_MAIN_PLACES: frozenset[str] = frozenset(
    {
        "中华门",
        "凯旋门",
        "朝阳门",
        "西直门",
        "东直门",
        "宣武门",
        "玄武门",
        "和平门",
        "复兴门",
        "建国门",
        "永定门",
        "崇文门",
        "前门",
        "天安门",
        "东门老街",
        "前门大街",
        "南门口",
        "南门",
        "东门",
        "西门",
        "北门",
    }
)

_SEPARATOR_RE = re.compile(r"[-—·•（(：:]")


def _has_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _strip_trailing_separators(text: str) -> str:
    return text.rstrip(" -—·•、_/:：(").strip()


def _extract_university_main(name: str) -> str | None:
    """聚合「某某大学 + 子单位」，但不把「大学城」截成「大学」。"""
    for match in re.finditer("大学", name):
        end = match.end()
        if end < len(name) and name[end] == "城":
            continue
        main = name[:end].strip()
        if len(main) < 3 or not _has_chinese(main):
            continue
        remainder = name[end:]
        if not remainder:
            return main
        if any(keyword in remainder for keyword in _UNIVERSITY_SUBUNIT_KEYWORDS):
            return main
        if len(remainder) >= 1:
            return main
    return None


def _split_by_child_separator(name: str) -> str | None:
    match = _SEPARATOR_RE.search(name)
    if not match:
        return None
    main = _strip_trailing_separators(name[: match.start()])
    if len(main) >= 2 and _has_chinese(main):
        return main
    return None


def _extract_scenic_main(name: str) -> str | None:
    separated = _split_by_child_separator(name)
    if separated:
        return normalize_place_name(separated)

    if any(name == main_name for _, main_name in _SCENIC_AGGREGATION_RULES):
        return name

    for keyword, main_name in _SCENIC_AGGREGATION_RULES:
        if keyword in name and name != main_name:
            return main_name

    for term in sorted(_SCENIC_MAIN_TERMS, key=len, reverse=True):
        index = name.find(term)
        if index <= 0:
            continue
        end = index + len(term)
        main = name[:end]
        remainder = name[end:]
        if remainder and any(keyword in remainder for keyword in _SCENIC_CHILD_KEYWORDS):
            return main
    return None


def normalize_place_name(name: str) -> str:
    """得到用于分组的主地点名。"""
    if not isinstance(name, str):
        return ""
    current = name.strip()
    if not current:
        return ""
    if current in _KNOWN_MAIN_PLACES:
        return current

    university_main = _extract_university_main(current)
    if university_main:
        return university_main

    scenic_main = _extract_scenic_main(current)
    if scenic_main and scenic_main != current:
        return scenic_main

    while True:
        stripped = current
        for suffix in _AUXILIARY_SUFFIXES:
            if stripped.endswith(suffix) and len(stripped) > len(suffix):
                candidate = _strip_trailing_separators(stripped[: -len(suffix)])
                if len(candidate) >= 2 and _has_chinese(candidate):
                    stripped = normalize_place_name(candidate)
                    break
        if stripped == current:
            break
        current = stripped
        if current in _KNOWN_MAIN_PLACES:
            break
    return current


def is_auxiliary_poi(name: str, category: str | None = None) -> bool:
    """判断是否为不应进入旅行景点推荐的辅助 POI。"""
    if not isinstance(name, str) or not name.strip():
        return True
    raw = name.strip()
    cat = category or ""

    if raw in _KNOWN_MAIN_PLACES:
        return False
    for keyword in _LODGING_KEYWORDS + _FOOD_SHOP_KEYWORDS + _LOW_VALUE_KEYWORDS:
        if keyword in raw or keyword in cat:
            return True
    if any(hint in cat for hint in _AUXILIARY_CATEGORY_HINTS):
        return True
    for suffix in _AUXILIARY_SUFFIXES:
        if raw.endswith(suffix) and len(raw) > len(suffix):
            remainder = _strip_trailing_separators(raw[: -len(suffix)])
            if len(remainder) >= 2:
                return True
    normalized = normalize_place_name(raw)
    return bool(normalized and normalized != raw and _looks_like_child_place(raw, normalized))


def _looks_like_child_place(raw: str, normalized: str) -> bool:
    if normalized in _KNOWN_MAIN_PLACES:
        return False
    remainder = raw.replace(normalized, "", 1)
    return any(
        keyword in remainder
        for keyword in _UNIVERSITY_SUBUNIT_KEYWORDS + _SCENIC_CHILD_KEYWORDS + _AUXILIARY_SUFFIXES
    )


def _bad_display_score(name: str, category: str | None) -> int:
    score = 0
    if is_auxiliary_poi(name, category):
        score += 100
    for keyword in _UNIVERSITY_SUBUNIT_KEYWORDS + _AUXILIARY_SUFFIXES + _LODGING_KEYWORDS:
        if keyword in name:
            score += 12
    for keyword in _FOOD_SHOP_KEYWORDS + _LOW_VALUE_KEYWORDS:
        if keyword in name:
            score += 20
    return score


def _content_score(entry: object) -> int:
    if isinstance(entry, dict):
        getter = entry.get  # type: ignore[assignment]
    else:
        def getter(key: str, default: str = "") -> object:  # type: ignore[misc]
            return getattr(entry, key, default)
    score = 0
    for key in ("rating", "score", "weight"):
        value = getter(key, 0)
        if isinstance(value, (int, float)):
            score += int(value * 10)
    for key in ("reason", "description", "address", "suitableFor"):
        value = getter(key, "")
        if isinstance(value, str):
            score += min(len(value), 80)
    return score


T = TypeVar("T")


def dedupe_places(places: Iterable[T]) -> list[T]:
    """按主地点去重，并优先展示更像主地点的名称。"""
    items = list(places)
    if not items:
        return []

    groups: dict[str, list[tuple[int, T]]] = {}
    order: list[str] = []
    for index, item in enumerate(items):
        name = _get_attr(item, "name", "")
        if not isinstance(name, str) or not name.strip():
            key = f"__unnamed__::{index}"
        else:
            key = normalize_place_name(name) or name.strip()
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append((index, item))

    deduped: list[T] = []
    for key in order:
        bucket = groups[key]
        bucket_sorted = sorted(
            bucket,
            key=lambda pair: (
                _bad_display_score(
                    str(_get_attr(pair[1], "name", "")),
                    str(_get_attr(pair[1], "type", "")),
                ),
                abs(len(str(_get_attr(pair[1], "name", ""))) - len(key)),
                -_content_score(pair[1]),
                pair[0],
            ),
        )
        _, winner = bucket_sorted[0]
        deduped.append(_maybe_rename_to_main(winner, key))
    return deduped or items


def _get_attr(item: object, key: str, default: object = "") -> object:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _maybe_rename_to_main(item: T, normalized_name: str) -> T:
    if not isinstance(normalized_name, str) or not normalized_name.strip():
        return item
    raw_name = _get_attr(item, "name", "")
    if not isinstance(raw_name, str) or raw_name.strip() == normalized_name:
        return item
    if raw_name in _KNOWN_MAIN_PLACES:
        return item
    if not (
        is_auxiliary_poi(raw_name, str(_get_attr(item, "type", "")))
        or normalize_place_name(raw_name) == normalized_name
    ):
        return item
    if isinstance(item, dict):
        new_item = dict(item)
        new_item["name"] = normalized_name
        return new_item  # type: ignore[return-value]
    try:
        if hasattr(item, "model_copy"):
            return item.model_copy(update={"name": normalized_name})  # type: ignore[attr-defined]
    except Exception:
        return item
    try:
        setattr(item, "name", normalized_name)
    except Exception:
        return item
    return item


__all__ = [
    "normalize_place_name",
    "is_auxiliary_poi",
    "dedupe_places",
]
