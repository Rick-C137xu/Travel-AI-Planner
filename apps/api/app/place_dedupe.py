"""V4.3.2 POI 去重与地点聚合（后端）。

只用名称 / 类别规则，不做坐标聚类——真实坐标聚类留到接入真实地图 API 之后。

核心目标：把「云南大学东门 / 云南大学西门 / 云南大学北门 / 云南大学停车场」这种
明显属于同一主地点的附属 POI 合并为「云南大学」，并把入口、停车场、卫生间等低价
值附属 POI 从候选地点列表中过滤掉。

注意：
- 不能把「中华门 / 朝阳门 / 西直门 / 宣武门 / 玄武门 / 凯旋门 / 前门大街 / 东门老街」
  这种本身就是知名主地点的名字误删；这里只剥离明确位于名称末尾的方位门 / 停车场 /
  入口等附属后缀，并且只在剥离后仍有 ≥ 2 个汉字时才认为是「附属」。
- 不依赖任何第三方库，可以被前端、后端、Mock 多处复用。
"""
from __future__ import annotations

from typing import Iterable, TypeVar

# 末尾附属后缀：按长度从长到短匹配，避免「地下停车场」被「停车场」先吃掉。
_AUXILIARY_SUFFIXES: tuple[str, ...] = (
    "出租车上客点",
    "网约车上车点",
    "地上停车场",
    "地下停车场",
    "游客中心",
    "服务中心",
    "服务区",
    "售票处",
    "停车场",
    "公交站",
    "地铁站",
    "卫生间",
    "洗手间",
    "进出口",
    "东门",
    "西门",
    "南门",
    "北门",
    "正门",
    "后门",
    "侧门",
    "入口",
    "出口",
)

# 这些类别词只要出现就视为附属 POI，不论名称是否含特殊后缀。
_AUXILIARY_CATEGORY_HINTS: tuple[str, ...] = (
    "停车场",
    "公交站",
    "地铁站",
    "出入口",
    "卫生间",
    "洗手间",
    "公共厕所",
    "出租车",
    "网约车",
    "加油站",
    "充电站",
)

# 一些「形似附属但其实是主地点」的白名单，归一化时直接放过。
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
        "南门",  # 防止被剥成空
        "东门",
        "西门",
        "北门",
    }
)


def _has_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def normalize_place_name(name: str) -> str:
    """剥离末尾附属后缀，得到主地点名。

    - 仅剥末尾匹配的附属后缀；中间出现的「东门 / 停车场」不会被破坏。
    - 剥离后若剩余长度 < 2 个字符或没有中文字符，认为剥离不安全，回退到原始名。
    - 命中 _KNOWN_MAIN_PLACES 时直接返回原名，避免「中华门 → 中华」这种误伤。
    - 反复剥离，处理「云南大学东门停车场」这种叠加情况。
    """
    if not isinstance(name, str):
        return ""
    current = name.strip()
    if not current:
        return ""
    if current in _KNOWN_MAIN_PLACES:
        return current
    while True:
        stripped = current
        for suffix in _AUXILIARY_SUFFIXES:
            if stripped.endswith(suffix) and len(stripped) > len(suffix):
                candidate = stripped[: -len(suffix)].rstrip(" -·、_/")
                # 剥离后仍需是合理主地点（至少 2 字符且包含中文）。
                if len(candidate) >= 2 and _has_chinese(candidate) and candidate not in {""}:
                    stripped = candidate
                    break
        if stripped == current:
            break
        current = stripped
        if current in _KNOWN_MAIN_PLACES:
            break
    return current


def is_auxiliary_poi(name: str, category: str | None = None) -> bool:
    """判断是否为「不该作为独立景点展示」的附属 POI。

    判定逻辑：
    1. 类别命中 _AUXILIARY_CATEGORY_HINTS（如「停车场」「公交站」）→ True。
    2. 名称命中白名单主地点 → False，避免「中华门 / 朝阳门」误判。
    3. 名称末尾是附属后缀，且剥离后剩余至少 2 个中文字符（说明原名只是某主地点的附属
       入口 / 停车场）→ True。
    4. 否则 False。
    """
    if not isinstance(name, str) or not name.strip():
        return True
    if category and any(hint in category for hint in _AUXILIARY_CATEGORY_HINTS):
        return True
    raw = name.strip()
    if raw in _KNOWN_MAIN_PLACES:
        return False
    for suffix in _AUXILIARY_SUFFIXES:
        if raw.endswith(suffix) and len(raw) > len(suffix):
            remainder = raw[: -len(suffix)].rstrip(" -·、_/")
            if len(remainder) >= 2 and _has_chinese(remainder):
                return True
    return False


def _aux_rank(name: str, category: str | None) -> int:
    """0 = 主地点（优先），1 = 附属。用于排序时挑「更主」的条目。"""
    return 1 if is_auxiliary_poi(name, category) else 0


def _content_score(entry: object) -> int:
    """按 reason / description / address 完整度打分，越大越值得保留。"""
    if isinstance(entry, dict):
        getter = entry.get  # type: ignore[assignment]
    else:
        def getter(key: str, default: str = "") -> object:  # type: ignore[misc]
            return getattr(entry, key, default)
    score = 0
    for key in ("reason", "description", "address", "suitableFor"):
        value = getter(key, "")
        if isinstance(value, str):
            score += min(len(value), 80)
    return score


T = TypeVar("T")


def dedupe_places(places: Iterable[T]) -> list[T]:
    """按归一化后的主地点名去重并合并。

    规则：
    1. 同一归一化名下，优先保留非附属 POI；并列时按 reason/address 完整度排序。
    2. 不破坏 Place 数据结构；只在「整条都是附属」时才把 name 替换成归一化后的主名。
    3. 保持首次出现顺序（按代表条目在输入里第一次出现的位置）。
    4. 永不返回空列表：若所有条目都被判定为附属，把它们按归一化主名当作候选返回。
    """
    items = list(places)
    if not items:
        return []

    groups: dict[str, list[tuple[int, T]]] = {}
    order: list[str] = []
    for index, item in enumerate(items):
        name = _get_attr(item, "name", "")
        if not isinstance(name, str) or not name.strip():
            # 没名字的条目直接跳过去重，单独保留。
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
        # 排序：非附属优先 → 内容完整度高优先 → 出现顺序靠前优先。
        bucket_sorted = sorted(
            bucket,
            key=lambda pair: (
                _aux_rank(_get_attr(pair[1], "name", ""), _get_attr(pair[1], "type", "")),
                -_content_score(pair[1]),
                pair[0],
            ),
        )
        winner_index, winner = bucket_sorted[0]
        winner = _maybe_rename_to_main(winner, key)
        deduped.append(winner)
        _ = winner_index  # 仅用于排序键，不再使用

    # 兜底：若全部被判定为附属导致看起来异常稀疏，回退到去重前列表。
    if not deduped:
        return items
    return deduped


def _get_attr(item: object, key: str, default: object = "") -> object:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _maybe_rename_to_main(item: T, normalized_name: str) -> T:
    """若原条目是附属 POI 而归一化名是合理主名，则把 name 替换为主名，便于前端展示。"""
    if not isinstance(normalized_name, str) or not normalized_name.strip():
        return item
    raw_name = _get_attr(item, "name", "")
    if not isinstance(raw_name, str) or raw_name.strip() == normalized_name:
        return item
    if not is_auxiliary_poi(raw_name, _get_attr(item, "type", "")):  # type: ignore[arg-type]
        return item
    # 主地点白名单不重命名（避免「中华门 / 朝阳门」被误改）。
    if raw_name in _KNOWN_MAIN_PLACES:
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
