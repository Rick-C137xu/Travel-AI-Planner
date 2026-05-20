export type Pace = 'relaxed' | 'normal' | 'intense';
export type BudgetLevel = 'low' | 'medium' | 'high';
export type PlaceStatus = 'want' | 'reject' | 'backup';

export interface TravelPreference {
  destination: string;
  startDate: string;
  endDate: string;
  days: number;
  peopleCount: number;
  pace: Pace;
  interests: string[];
  dislikes: string[];
  budgetLevel: BudgetLevel;
  hotelArea: string;
  transportPreference: string[];
}

export interface Place {
  id: string;
  name: string;
  type: '景点' | '餐厅' | '商圈' | '博物馆' | '夜市' | '自然风景' | '交通点' | '其他';
  address: string;
  lat?: number | null;
  lng?: number | null;
  reason: string;
  suitableFor: string;
  estimatedTime: string;
  warning: string;
  source: 'AI推荐' | '用户粘贴攻略' | 'Mock数据' | '前端 Mock' | '后端 Mock' | string;
  userStatus?: PlaceStatus;
}

export interface ItineraryItem {
  id: string;
  timeLabel: string;
  placeId: string;
  placeName: string;
  activity: string;
  estimatedDuration: string;
  transportSuggestion: string;
  note: string;
}

export interface DayPlan {
  day: number;
  date: string;
  title: string;
  items: ItineraryItem[];
}

export interface WeatherForecastDay {
  date: string;
  week?: string;
  dayweather?: string;
  nightweather?: string;
  daytemp?: string;
  nighttemp?: string;
  daywind?: string;
  daypower?: string;
}

export interface WeatherInfo {
  status: 'ok' | 'error' | 'disabled' | string;
  source?: string;
  city?: string;
  weather?: string;
  temperature?: string;
  winddirection?: string;
  windpower?: string;
  humidity?: string;
  reporttime?: string;
  forecast?: WeatherForecastDay[];
  reason?: string;
}

export interface ApiEnvelope<T> {
  data: T;
  warning?: string;
  dataSourceLabel?: string;
  aiEnabled?: boolean;
  amapEnabled?: boolean;
  backendMode?: boolean;
  weather?: WeatherInfo | null;
}

export type AppStep = 'start' | 'chat' | 'places' | 'itinerary';
