import { reactive, watch } from 'vue';
import type { ApiEnvelope, AppStep, DayPlan, Place, TravelPreference, WeatherInfo } from '@/types';

const STORAGE_KEY = 'travel-ai-planner:v1';
// V4.3.1：行程缓存 key 升级到 v4.3，避免读取到 V4.2 时期残留的 sourceLabel/文案。
const ITINERARY_CACHE_PREFIX = 'travel-ai-planner:itinerary:v4.3:';
const LEGACY_ITINERARY_CACHE_PREFIXES = ['travel-ai-planner:itinerary:v1:'];

type RuntimeScope = 'places' | 'itinerary' | 'general';

interface ItineraryCacheEntry {
  itinerary: DayPlan[];
  sourceLabel: string;
  warning: string;
  backendConnected: boolean;
  aiEnabled: boolean | null;
  amapEnabled: boolean | null;
  createdAt: string;
  weather?: WeatherInfo | null;
}

export const defaultPreference = (): TravelPreference => ({
  destination: '',
  startDate: '',
  endDate: '',
  days: 3,
  peopleCount: 2,
  pace: 'normal',
  interests: [],
  dislikes: [],
  budgetLevel: 'medium',
  hotelArea: '',
  transportPreference: []
});

export interface PlannerState {
  step: AppStep;
  questionIndex: number;
  preference: TravelPreference;
  places: Place[];
  itinerary: DayPlan[];
  guideText: string;
  warning: string;
  backendConnected: boolean;
  aiEnabled: boolean | null;
  amapEnabled: boolean | null;
  dataSourceLabel: string;
  placeSourceLabel: string;
  itinerarySourceLabel: string;
  placeWarning: string;
  itineraryWarning: string;
  weather: WeatherInfo | null;
}

function normalizeList(values: string[]) {
  return values.map((value) => value.trim()).filter(Boolean).sort();
}

function selectedPlaceSignature(places: Place[]) {
  return places
    .filter((place) => place.userStatus === 'want')
    .map((place) => ({
      id: place.id || '',
      name: place.name || ''
    }))
    .sort((a, b) => `${a.id}|${a.name}`.localeCompare(`${b.id}|${b.name}`));
}

function stableStringify(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify((value as Record<string, unknown>)[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}

function hashString(value: string) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) | 0;
  }
  return Math.abs(hash).toString(36);
}

export function buildItineraryCacheKey(preference: TravelPreference, places: Place[]) {
  const signature = {
    destination: preference.destination.trim(),
    startDate: preference.startDate,
    days: preference.days,
    selectedPlaces: selectedPlaceSignature(places),
    interests: normalizeList(preference.interests),
    budgetLevel: preference.budgetLevel,
    transportPreference: normalizeList(preference.transportPreference),
    pace: preference.pace,
    dislikes: normalizeList(preference.dislikes),
    hotelArea: preference.hotelArea.trim()
  };
  return `${ITINERARY_CACHE_PREFIX}${hashString(stableStringify(signature))}`;
}

function readItineraryCache(cacheKey: string): ItineraryCacheEntry | null {
  try {
    // V4.3.1：清理旧版本前缀的行程缓存。
    for (const legacy of LEGACY_ITINERARY_CACHE_PREFIXES) {
      try {
        for (let i = localStorage.length - 1; i >= 0; i -= 1) {
          const k = localStorage.key(i);
          if (k && k.startsWith(legacy)) localStorage.removeItem(k);
        }
      } catch {
        // ignore
      }
    }
    const raw = localStorage.getItem(cacheKey);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<ItineraryCacheEntry>;
    if (!Array.isArray(parsed.itinerary) || !parsed.itinerary.length) return null;
    // V4.3.1：若缓存里的 sourceLabel 仍含 V4.2 字样，视为脏数据丢弃。
    if (typeof parsed.sourceLabel === 'string' && /v4\.2/i.test(parsed.sourceLabel)) {
      try { localStorage.removeItem(cacheKey); } catch { /* ignore */ }
      return null;
    }
    return {
      itinerary: parsed.itinerary,
      sourceLabel: parsed.sourceLabel || '',
      warning: parsed.warning || '',
      backendConnected: parsed.backendConnected === true,
      aiEnabled: typeof parsed.aiEnabled === 'boolean' ? parsed.aiEnabled : null,
      amapEnabled: typeof parsed.amapEnabled === 'boolean' ? parsed.amapEnabled : null,
      createdAt: parsed.createdAt || '',
      weather: parsed.weather && typeof parsed.weather === 'object' ? parsed.weather : null
    };
  } catch {
    return null;
  }
}

function writeItineraryCache(cacheKey: string, entry: ItineraryCacheEntry) {
  localStorage.setItem(cacheKey, JSON.stringify(entry));
}

function removeItineraryCache(cacheKey: string) {
  localStorage.removeItem(cacheKey);
}

function loadState(): PlannerState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) throw new Error('empty');
    const parsed = JSON.parse(raw) as Partial<PlannerState>;
    return {
      step: parsed.step || 'start',
      questionIndex: parsed.questionIndex || 0,
      preference: { ...defaultPreference(), ...(parsed.preference || {}) },
      places: parsed.places || [],
      itinerary: parsed.itinerary || [],
      guideText: parsed.guideText || '',
      warning: parsed.warning || '',
      backendConnected: parsed.backendConnected || false,
      aiEnabled: typeof parsed.aiEnabled === 'boolean' ? parsed.aiEnabled : null,
      amapEnabled: typeof parsed.amapEnabled === 'boolean' ? parsed.amapEnabled : null,
      dataSourceLabel: parsed.dataSourceLabel || '',
      placeSourceLabel: parsed.placeSourceLabel || parsed.dataSourceLabel || '',
      itinerarySourceLabel: parsed.itinerarySourceLabel || (parsed.step === 'itinerary' ? parsed.dataSourceLabel || '' : ''),
      placeWarning: parsed.placeWarning || '',
      itineraryWarning: parsed.itineraryWarning || '',
      weather: parsed.weather && typeof parsed.weather === 'object' ? parsed.weather : null
    };
  } catch {
    return {
      step: 'start',
      questionIndex: 0,
      preference: defaultPreference(),
      places: [],
      itinerary: [],
      guideText: '',
      warning: '',
      backendConnected: false,
      aiEnabled: null,
      amapEnabled: null,
      dataSourceLabel: '',
      placeSourceLabel: '',
      itinerarySourceLabel: '',
      placeWarning: '',
      itineraryWarning: '',
      weather: null
    };
  }
}

const state = reactive<PlannerState>(loadState());

watch(
  state,
  () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  },
  { deep: true }
);

export function usePlannerStore() {
  function resetPlan() {
    removeItineraryCache(buildItineraryCacheKey(state.preference, state.places));
    Object.assign(state, {
      step: 'start',
      questionIndex: 0,
      preference: defaultPreference(),
      places: [],
      itinerary: [],
      guideText: '',
      warning: '',
      backendConnected: false,
      aiEnabled: null,
      amapEnabled: null,
      dataSourceLabel: '',
      placeSourceLabel: '',
      itinerarySourceLabel: '',
      placeWarning: '',
      itineraryWarning: '',
      weather: null
    });
    localStorage.removeItem(STORAGE_KEY);
  }

  function updateRuntimeStatus<T>(response: ApiEnvelope<T>, scope: RuntimeScope = 'general') {
    const label = response.dataSourceLabel || (response.backendMode ? 'V4.3 后端' : '前端 Mock');
    state.backendConnected = response.backendMode === true;
    state.aiEnabled = typeof response.aiEnabled === 'boolean' ? response.aiEnabled : state.aiEnabled;
    state.amapEnabled = typeof response.amapEnabled === 'boolean' ? response.amapEnabled : state.amapEnabled;
    state.dataSourceLabel = label;
    if (scope === 'places') {
      state.placeSourceLabel = label;
      state.placeWarning = response.warning || '';
    }
    if (scope === 'itinerary') {
      state.itinerarySourceLabel = label;
      state.itineraryWarning = response.warning || '';
      // V4.3：行程响应可能携带天气；失败/空时清空但不影响主流程。
      state.weather = response.weather && response.weather.status === 'ok' ? response.weather : null;
    }
  }

  function getCachedItinerary() {
    return readItineraryCache(buildItineraryCacheKey(state.preference, state.places));
  }

  function saveCurrentItineraryToCache() {
    if (!state.itinerary.length) return;
    writeItineraryCache(buildItineraryCacheKey(state.preference, state.places), {
      itinerary: state.itinerary,
      sourceLabel: state.itinerarySourceLabel || state.dataSourceLabel,
      warning: state.itineraryWarning,
      backendConnected: state.backendConnected,
      aiEnabled: state.aiEnabled,
      amapEnabled: state.amapEnabled,
      createdAt: new Date().toISOString(),
      weather: state.weather
    });
  }

  function clearCurrentItineraryCache() {
    removeItineraryCache(buildItineraryCacheKey(state.preference, state.places));
  }

  return {
    state,
    resetPlan,
    updateRuntimeStatus,
    getCachedItinerary,
    saveCurrentItineraryToCache,
    clearCurrentItineraryCache
  };
}
