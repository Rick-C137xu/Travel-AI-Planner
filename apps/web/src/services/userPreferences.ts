import type {
  AccommodationPreference,
  BudgetLevel,
  Pace,
  TravelPreference,
  UserPreferenceProfile,
  WakeUpPreference
} from '@/types';

export const USER_PREFERENCES_STORAGE_KEY = 'travel_ai_planner_user_preferences_v1';

const DEFAULT_PROFILE: UserPreferenceProfile = {
  pace: 'normal',
  wakeUpPreference: 'flexible',
  budgetLevel: 'medium',
  transportPreference: [],
  accommodationPreference: 'undecided',
  interestTags: [],
  avoidTags: [],
  updatedAt: ''
};

const validPace = new Set<Pace>(['relaxed', 'normal', 'intense']);
const validBudget = new Set<BudgetLevel>(['low', 'medium', 'high']);
const validWake = new Set<WakeUpPreference>(['no_early_start', 'flexible', 'early_ok']);
const validAccommodation = new Set<AccommodationPreference>([
  'city_center',
  'near_scenic_area',
  'near_transport',
  'undecided'
]);

function cleanList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return Array.from(new Set(value.filter((item): item is string => typeof item === 'string').map((item) => item.trim()).filter(Boolean)));
}

function normalizeProfile(value: unknown): UserPreferenceProfile | null {
  if (!value || typeof value !== 'object') return null;
  const raw = value as Partial<UserPreferenceProfile>;
  return {
    pace: validPace.has(raw.pace as Pace) ? (raw.pace as Pace) : DEFAULT_PROFILE.pace,
    wakeUpPreference: validWake.has(raw.wakeUpPreference as WakeUpPreference)
      ? (raw.wakeUpPreference as WakeUpPreference)
      : DEFAULT_PROFILE.wakeUpPreference,
    budgetLevel: validBudget.has(raw.budgetLevel as BudgetLevel)
      ? (raw.budgetLevel as BudgetLevel)
      : DEFAULT_PROFILE.budgetLevel,
    transportPreference: cleanList(raw.transportPreference),
    accommodationPreference: validAccommodation.has(raw.accommodationPreference as AccommodationPreference)
      ? (raw.accommodationPreference as AccommodationPreference)
      : DEFAULT_PROFILE.accommodationPreference,
    interestTags: cleanList(raw.interestTags),
    avoidTags: cleanList(raw.avoidTags),
    updatedAt: typeof raw.updatedAt === 'string' ? raw.updatedAt : ''
  };
}

export function getUserPreferences(): UserPreferenceProfile | null {
  try {
    const raw = localStorage.getItem(USER_PREFERENCES_STORAGE_KEY);
    if (!raw) return null;
    return normalizeProfile(JSON.parse(raw));
  } catch {
    return null;
  }
}

export function saveUserPreferences(profile: UserPreferenceProfile): boolean {
  try {
    const normalized = normalizeProfile({ ...profile, updatedAt: new Date().toISOString() });
    if (!normalized) return false;
    localStorage.setItem(USER_PREFERENCES_STORAGE_KEY, JSON.stringify(normalized));
    return true;
  } catch {
    // localStorage may be unavailable; preference save should never break planning.
    return false;
  }
}

export function clearUserPreferences() {
  try {
    localStorage.removeItem(USER_PREFERENCES_STORAGE_KEY);
  } catch {
    // ignore
  }
}

export function hasUserPreferences() {
  return getUserPreferences() !== null;
}

export function mergePreferencesIntoTravelForm(
  form: TravelPreference,
  profile: UserPreferenceProfile
): TravelPreference {
  const avoidTags = Array.from(new Set([
    ...profile.avoidTags,
    ...(profile.wakeUpPreference === 'no_early_start' ? ['早起'] : [])
  ]));
  return {
    ...form,
    pace: profile.pace,
    interests: [...profile.interestTags],
    dislikes: avoidTags,
    budgetLevel: profile.budgetLevel,
    hotelArea: accommodationToHotelArea(profile.accommodationPreference),
    transportPreference: [...profile.transportPreference]
  };
}

export function buildUserPreferencesFromTravelForm(form: TravelPreference): UserPreferenceProfile {
  const avoidTags = cleanList(form.dislikes);
  return {
    pace: form.pace,
    wakeUpPreference: avoidTags.includes('早起') ? 'no_early_start' : 'flexible',
    budgetLevel: form.budgetLevel,
    transportPreference: cleanList(form.transportPreference),
    accommodationPreference: inferAccommodationPreference(form.hotelArea),
    interestTags: cleanList(form.interests),
    avoidTags,
    updatedAt: new Date().toISOString()
  };
}

export function accommodationToHotelArea(value: AccommodationPreference) {
  const map: Record<AccommodationPreference, string> = {
    city_center: '市中心或商圈附近',
    near_scenic_area: '主要景区附近',
    near_transport: '地铁站或交通枢纽附近',
    undecided: ''
  };
  return map[value];
}

export function inferAccommodationPreference(hotelArea: string): AccommodationPreference {
  const value = hotelArea.trim();
  if (!value || value.includes('不确定') || value.includes('还没')) return 'undecided';
  if (value.includes('景区') || value.includes('景点')) return 'near_scenic_area';
  if (value.includes('地铁') || value.includes('车站') || value.includes('交通')) return 'near_transport';
  if (value.includes('市中心') || value.includes('中心') || value.includes('商圈')) return 'city_center';
  return 'undecided';
}

export function summarizeUserPreferences(profile: UserPreferenceProfile) {
  const paceMap: Record<Pace, string> = { relaxed: '轻松', normal: '正常', intense: '特种兵' };
  const budgetMap: Record<BudgetLevel, string> = { low: '低预算', medium: '中预算', high: '高预算' };
  const wakeMap: Record<WakeUpPreference, string> = {
    no_early_start: '不早起',
    flexible: '时间灵活',
    early_ok: '可以早起'
  };
  const accommodationMap: Record<AccommodationPreference, string> = {
    city_center: '住市中心',
    near_scenic_area: '住景区附近',
    near_transport: '住交通便利处',
    undecided: '住宿未定'
  };
  return [
    paceMap[profile.pace],
    wakeMap[profile.wakeUpPreference],
    budgetMap[profile.budgetLevel],
    accommodationMap[profile.accommodationPreference],
    profile.interestTags.length ? `兴趣：${profile.interestTags.join('、')}` : '',
    profile.avoidTags.length ? `避雷：${profile.avoidTags.join('、')}` : '',
    profile.transportPreference.length ? `交通：${profile.transportPreference.join('、')}` : ''
  ].filter(Boolean);
}
