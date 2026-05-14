import type { DayPlan, ItineraryItem, Place, TravelPreference } from '@/types';

const typeByInterest: Record<string, Place['type']> = {
  美食: '餐厅',
  自然风景: '自然风景',
  拍照: '景点',
  博物馆: '博物馆',
  夜市: '夜市',
  购物: '商圈',
  Citywalk: '景点',
  亲子: '景点',
  情侣: '景点'
};

export function mockRecommendPlaces(preference: TravelPreference, guideText = ''): Place[] {
  const destination = preference.destination || '目的地';
  const interests = preference.interests.length ? preference.interests : ['美食', 'Citywalk', '博物馆', '自然风景', '夜市'];
  const templates = [
    ['老城 Citywalk 街区', '适合第一天熟悉城市节奏，沿路可穿插咖啡和小店。', '步行闲逛、拍照、轻体验'],
    ['城市代表博物馆', '了解目的地历史文化，雨天也很稳。', '文化爱好者、亲子、慢节奏旅行'],
    ['本地口碑小吃街', '一次覆盖多种本地小吃，适合把晚餐安排得灵活一点。', '美食探索、朋友出游'],
    ['核心商圈', '交通方便，吃饭购物选择多，适合作为行程缓冲点。', '购物、餐饮、晚间活动'],
    ['城市公园或湖畔', '给行程留出放松空间，适合拍照和散步。', '自然风景、情侣、亲子'],
    ['夜市或夜生活街区', '晚上氛围更好，适合不想太早回酒店的人。', '夜游、美食、拍照'],
    ['特色咖啡馆片区', '适合下午休息，也能作为不赶路的备选。', '轻松旅行、拍照'],
    ['地标观景点', '第一次到访值得打卡，建议避开正午和高峰。', '拍照、城市初访'],
    ['本地菜餐厅', '更适合正式吃一顿本地风味，预算可控。', '美食、情侣、家庭'],
    ['周边自然半日游', '适合想看风景的人，强度会比市区略高。', '自然风景、轻徒步'],
    ['独立书店与文创街', '适合慢逛和买伴手礼，不会占用太多体力。', 'Citywalk、购物'],
    ['交通枢纽附近补给点', '适合抵达或离开当天安排，减少绕路。', '中转、轻量行程']
  ] as const;

  const guideHint = guideText.trim() ? '已参考你粘贴的攻略文本。' : '';

  return templates.map(([name, reason, suitableFor], index) => {
    const interest = interests[index % interests.length] || 'Citywalk';
    const type = inferType(name, typeByInterest[interest] || '其他');
    return {
      id: `front-mock-${index + 1}`,
      name: `${destination}${name}`,
      type,
      address: `${destination}市中心区域`,
      lat: index < 8 ? 31.2304 + (index + 1) * 0.01 : null,
      lng: index < 8 ? 121.4737 + (index + 1) * 0.012 : null,
      reason: `${reason}${guideHint}`,
      suitableFor,
      estimatedTime: type === '餐厅' ? '1-1.5 小时' : '1.5-2.5 小时',
      warning: warningFor(preference, type),
      source: 'Mock数据',
      userStatus: 'backup'
    };
  });
}

export function mockExtractPlaces(preference: TravelPreference, text: string): Place[] {
  const destination = preference.destination || '目的地';
  const names = text
    .split(/\r?\n/)
    .map((line) => line.trim().replace(/^[-*、\d.\s]+/, ''))
    .filter(Boolean)
    .slice(0, 6);
  const fallbackNames = names.length ? names : ['攻略提到的咖啡馆', '攻略提到的观景点', '攻略提到的小吃店'];

  return fallbackNames.map((name, index) => ({
    id: `front-guide-${Date.now()}-${index + 1}`,
    name: name.includes(destination) ? name.slice(0, 28) : `${destination}${name.slice(0, 18)}`,
    type: '其他',
    address: '',
    lat: null,
    lng: null,
    reason: '从用户粘贴攻略文本中提取，建议后续人工确认营业时间和位置。',
    suitableFor: '攻略补充地点',
    estimatedTime: '1-2 小时',
    warning: '来源为粘贴文本，可能需要二次核对。',
    source: '用户粘贴攻略',
    userStatus: 'backup'
  }));
}

export function mockGenerateItinerary(preference: TravelPreference, places: Place[]): DayPlan[] {
  const selected = places.length ? places : mockRecommendPlaces(preference).slice(0, 6);
  const perDay = preference.pace === 'relaxed' ? 3 : preference.pace === 'intense' ? 5 : 4;
  const slots = ['上午', '中午', '下午', '晚上', '夜间'];
  const startDate = parseDate(preference.startDate);

  return Array.from({ length: preference.days }, (_, dayIndex) => {
    const chunk = selected.slice(dayIndex * perDay, dayIndex * perDay + perDay);
    const dayPlaces = chunk.length ? chunk : selected.slice(0, Math.min(perDay, selected.length));
    const items: ItineraryItem[] = dayPlaces.map((place, itemIndex) => ({
      id: `front-day-${dayIndex + 1}-item-${itemIndex + 1}`,
      timeLabel: slots[itemIndex] || `第 ${itemIndex + 1} 段`,
      placeId: place.id,
      placeName: place.name,
      activity: `体验${place.type}，重点关注：${place.reason}`,
      estimatedDuration: place.estimatedTime,
      transportSuggestion: transportText(preference),
      note: place.warning || '留出机动时间，现场按体力调整。'
    }));

    return {
      day: dayIndex + 1,
      date: startDate ? addDays(startDate, dayIndex).toISOString().slice(0, 10) : '',
      title: `${preference.destination || '目的地'}第 ${dayIndex + 1} 天`,
      items
    };
  });
}

function inferType(name: string, fallback: Place['type']): Place['type'] {
  if (name.includes('餐厅') || name.includes('小吃')) return '餐厅';
  if (name.includes('夜市')) return '夜市';
  if (name.includes('商圈')) return '商圈';
  if (name.includes('博物馆')) return '博物馆';
  if (name.includes('自然') || name.includes('湖畔')) return '自然风景';
  return fallback;
}

function warningFor(preference: TravelPreference, type: Place['type']) {
  if (preference.dislikes.includes('排队')) return '热门时段可能排队，建议错峰或保留备选。';
  if (preference.dislikes.includes('太赶路')) return '建议与相邻区域组合，避免跨城折返。';
  if (type === '自然风景' && preference.dislikes.includes('爬山')) return '如涉及爬坡，可替换为市区公园。';
  return '提前核对开放时间，周末适当错峰。';
}

function transportText(preference: TravelPreference) {
  const first = preference.transportPreference[0];
  return first ? `优先${first}，跨区时保留打车选项。` : '优先选择少换乘路线。';
}

function parseDate(value: string) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}
