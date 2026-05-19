import type { ApiEnvelope, DayPlan, Place, TravelPreference } from '@/types';
import { mockExtractPlaces, mockGenerateItinerary, mockRecommendPlaces } from './mockPlanner';

const useMock = import.meta.env.VITE_USE_MOCK !== 'false';
const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');

export const isFrontendMockMode = useMock;

function apiUrl(path: string) {
  if (!apiBaseUrl) {
    throw new Error('未配置 VITE_API_BASE_URL，无法请求后端。');
  }
  return `${apiBaseUrl}${path}`;
}

async function postJson<T>(url: string, body: unknown): Promise<ApiEnvelope<T>> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(`API 请求失败：${response.status}`);
  }
  return response.json() as Promise<ApiEnvelope<T>>;
}

function mockEnvelope<T>(data: T, warning?: string): ApiEnvelope<T> {
  return { data, warning, dataSourceLabel: '前端 Mock', aiEnabled: false, backendMode: false };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function normalizeBackendResponse<T>(response: ApiEnvelope<T>): ApiEnvelope<T> {
  const backendMode = response.backendMode ?? true;
  const aiEnabled = response.aiEnabled;
  const isBackendMock =
    aiEnabled === false || Boolean(response.warning && response.warning.includes('AI_API_KEY'));
  const dataSourceLabel = response.dataSourceLabel || (isBackendMock ? '后端 Mock' : 'V3 后端');

  if (isBackendMock && Array.isArray(response.data)) {
    response.data = response.data.map((item) => {
      if (isRecord(item) && item.source === 'Mock数据') {
        return { ...item, source: '后端 Mock' };
      }
      return item;
    }) as T;
  }

  return { ...response, backendMode, dataSourceLabel };
}

async function withFallback<T>(request: () => Promise<ApiEnvelope<T>>, fallback: () => T): Promise<ApiEnvelope<T>> {
  if (useMock) {
    return mockEnvelope(fallback(), '当前为 V2.1 / 前端 Mock 演示数据，未请求后端。');
  }
  try {
    return normalizeBackendResponse(await request());
  } catch (error) {
    const reason = error instanceof Error ? error.message : '未知错误';
    return mockEnvelope(fallback(), `后端请求失败，已降级为前端 Mock 数据。原因：${reason}`);
  }
}

export function recommendPlaces(preference: TravelPreference, guideText = '') {
  return withFallback(
    () => postJson<Place[]>(apiUrl('/api/places/recommend'), { preference, guideText }),
    () => mockRecommendPlaces(preference, guideText)
  );
}

export function extractPlaces(preference: TravelPreference, text: string) {
  return withFallback(
    () => postJson<Place[]>(apiUrl('/api/places/extract'), { preference, text }),
    () => mockExtractPlaces(preference, text)
  );
}

export function generateItinerary(preference: TravelPreference, places: Place[]) {
  return withFallback(
    () => postJson<DayPlan[]>(apiUrl('/api/itinerary/generate'), { preference, places }),
    () => mockGenerateItinerary(preference, places)
  );
}
