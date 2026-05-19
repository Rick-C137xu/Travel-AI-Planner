import { reactive, watch } from 'vue';
import type { ApiEnvelope, AppStep, DayPlan, Place, TravelPreference } from '@/types';

const STORAGE_KEY = 'travel-ai-planner:v1';

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
      dataSourceLabel: parsed.dataSourceLabel || ''
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
      dataSourceLabel: ''
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
      dataSourceLabel: ''
    });
    localStorage.removeItem(STORAGE_KEY);
  }

  function updateRuntimeStatus<T>(response: ApiEnvelope<T>) {
    state.backendConnected = response.backendMode === true;
    state.aiEnabled = typeof response.aiEnabled === 'boolean' ? response.aiEnabled : state.aiEnabled;
    state.amapEnabled = typeof response.amapEnabled === 'boolean' ? response.amapEnabled : state.amapEnabled;
    state.dataSourceLabel = response.dataSourceLabel || (response.backendMode ? 'V4 后端' : '前端 Mock');
  }

  return { state, resetPlan, updateRuntimeStatus };
}
