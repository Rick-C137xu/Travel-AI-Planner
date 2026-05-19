from typing import Any, Literal

from pydantic import BaseModel, Field


Pace = Literal["relaxed", "normal", "intense"]
BudgetLevel = Literal["low", "medium", "high"]
PlaceType = Literal["景点", "餐厅", "商圈", "博物馆", "夜市", "自然风景", "交通点", "其他"]
# V4 起允许真实数据源标签，例如「高德地图」「AI + 高德」，仍兼容旧值。
PlaceSource = str
PlaceStatus = Literal["want", "reject", "backup"]


class TravelPreference(BaseModel):
    destination: str = ""
    startDate: str = ""
    endDate: str = ""
    days: int = Field(default=3, ge=1, le=30)
    peopleCount: int = Field(default=2, ge=1, le=50)
    pace: Pace = "normal"
    interests: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    budgetLevel: BudgetLevel = "medium"
    hotelArea: str = ""
    transportPreference: list[str] = Field(default_factory=list)


class Place(BaseModel):
    id: str
    name: str
    type: PlaceType = "其他"
    address: str = ""
    lat: float | None = None
    lng: float | None = None
    reason: str
    suitableFor: str
    estimatedTime: str
    warning: str = ""
    source: PlaceSource = "Mock数据"
    userStatus: PlaceStatus | None = None


class ItineraryItem(BaseModel):
    id: str
    timeLabel: str
    placeId: str
    placeName: str
    activity: str
    estimatedDuration: str
    transportSuggestion: str
    note: str = ""


class DayPlan(BaseModel):
    day: int
    date: str = ""
    title: str
    items: list[ItineraryItem] = Field(default_factory=list)


class ApiEnvelope(BaseModel):
    data: Any
    warning: str | None = None
    dataSourceLabel: str | None = None
    aiEnabled: bool | None = None
    amapEnabled: bool | None = None
    backendMode: bool | None = None


class PreferenceRequest(BaseModel):
    preference: TravelPreference


class RecommendRequest(PreferenceRequest):
    guideText: str = ""


class ExtractRequest(PreferenceRequest):
    text: str


class ItineraryRequest(PreferenceRequest):
    places: list[Place]


class NextQuestionRequest(BaseModel):
    preference: TravelPreference
    answeredKeys: list[str] = Field(default_factory=list)
