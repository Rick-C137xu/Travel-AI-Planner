import type { ApiEnvelope, DayPlan, Place, TravelPreference } from '@/types';
import { mockExtractPlaces, mockGenerateItinerary, mockRecommendPlaces } from './mockPlanner';

const useMock = import.meta.env.VITE_USE_MOCK !== 'false';

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
  return { data, warning };
}

async function withFallback<T>(request: () => Promise<ApiEnvelope<T>>, fallback: () => T): Promise<ApiEnvelope<T>> {
  if (useMock) {
    return mockEnvelope(fallback(), '当前为 V2.1 前端 Mock 演示数据，未请求真实后端。');
  }
  try {
    return await request();
  } catch (error) {
    const reason = error instanceof Error ? error.message : '未知错误';
    return mockEnvelope(fallback(), `后端请求失败，已降级为前端 Mock 数据。原因：${reason}`);
  }
}

export function recommendPlaces(preference: TravelPreference, guideText = '') {
  return withFallback(
    () => postJson<Place[]>('/api/places/recommend', { preference, guideText }),
    () => mockRecommendPlaces(preference, guideText)
  );
}

export function extractPlaces(preference: TravelPreference, text: string) {
  return withFallback(
    () => postJson<Place[]>('/api/places/extract', { preference, text }),
    () => mockExtractPlaces(preference, text)
  );
}

export function generateItinerary(preference: TravelPreference, places: Place[]) {
  return withFallback(
    () => postJson<DayPlan[]>('/api/itinerary/generate', { preference, places }),
    () => mockGenerateItinerary(preference, places)
  );
}
