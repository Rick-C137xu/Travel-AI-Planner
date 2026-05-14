import { reactive, watch } from 'vue';
import type { AppStep, DayPlan, Place, TravelPreference } from '@/types';

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
      warning: parsed.warning || ''
    };
  } catch {
    return {
      step: 'start',
      questionIndex: 0,
      preference: defaultPreference(),
      places: [],
      itinerary: [],
      guideText: '',
      warning: ''
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
      warning: ''
    });
    localStorage.removeItem(STORAGE_KEY);
  }

  return { state, resetPlan };
}
