/**
 * V4.3.4 前端 POI 去重与全国通用主地点聚合工具。
 *
 * 与 apps/api/app/place_dedupe.py 保持同名 / 同语义实现。
 */
import type { Place } from '@/types';

const AUXILIARY_SUFFIXES: readonly string[] = [
  '出租车上客点',
  '网约车上车点',
  '地下停车场',
  '地上停车场',
  '停车点',
  '停车场',
  '游客服务中心',
  '游客中心',
  '服务中心',
  '咨询处',
  '售票大厅',
  '售票厅',
  '售票处',
  '检票口',
  '码头候船厅',
  '候船厅',
  '公共厕所',
  '卫生间',
  '洗手间',
  '厕所',
  '公交站',
  '地铁站',
  '火车站',
  '汽车站',
  '机场',
  '进出口',
  '出入口',
  '入口',
  '出口',
  '东门',
  '西门',
  '南门',
  '北门',
  '正门',
  '后门',
  '侧门'
];

const AUXILIARY_CATEGORY_HINTS: readonly string[] = [
  '停车场',
  '停车点',
  '公交站',
  '地铁站',
  '火车站',
  '汽车站',
  '机场',
  '出入口',
  '卫生间',
  '洗手间',
  '公共厕所',
  '厕所',
  '出租车',
  '网约车',
  '加油站',
  '充电站',
  '售票处',
  '游客中心'
];

const LODGING_KEYWORDS: readonly string[] = [
  '酒店',
  '宾馆',
  '旅馆',
  '客栈',
  '民宿',
  '公寓',
  '青旅',
  '青年旅舍',
  '住宿',
  '旅社',
  '招待所'
];

const FOOD_SHOP_KEYWORDS: readonly string[] = ['餐厅', '饭店', '小吃店', '便利店', '超市', '商铺'];

const LOW_VALUE_KEYWORDS: readonly string[] = [
  '写字楼',
  '商务楼',
  '办公楼',
  '小区',
  '住宅',
  '售楼处',
  '房产',
  '中介'
];

const UNIVERSITY_SUBUNIT_KEYWORDS: readonly string[] = [
  '校区',
  '学院',
  '学部',
  '系',
  '图书馆',
  '食堂',
  '教学楼',
  '实验楼',
  '宿舍',
  '体育馆',
  '行政楼',
  '研究院',
  '东门',
  '西门',
  '南门',
  '北门',
  '正门',
  '停车场',
  '生活区',
  '学生公寓',
  '校医院',
  '南校园',
  '北校园',
  '东校园',
  '西校园'
];

const SCENIC_MAIN_TERMS: readonly string[] = [
  '风景区',
  '博物院',
  '博物馆',
  '纪念馆',
  '步行街',
  '旅游区',
  '公园',
  '景区',
  '古镇',
  '古城',
  '老街',
  '街区',
  '广场',
  '码头',
  '寺',
  '庙',
  '宫',
  '塔',
  '湖',
  '山',
  '岛',
  '湾',
  '滩',
  '坊',
  '巷',
  '街',
  '园',
  '城',
  '村',
  '寨'
];

const SCENIC_CHILD_KEYWORDS: readonly string[] = [
  '游客中心',
  '服务中心',
  '东广场',
  '西广场',
  '南广场',
  '北广场',
  '游乐场',
  '游船码头',
  '码头',
  '午门',
  '神武门',
  '东门',
  '西门',
  '南门',
  '北门',
  '入口',
  '出口',
  '售票处',
  '停车场',
  '音乐喷泉',
  '步行街',
  '秦淮风光带'
];

const SCENIC_AGGREGATION_RULES: ReadonlyArray<readonly [string, string]> = [
  ['翠湖', '翠湖公园'],
  ['西湖风景区', '西湖风景区'],
  ['西湖', '西湖'],
  ['宽窄巷子', '宽窄巷子'],
  ['故宫博物院', '故宫博物院'],
  ['故宫', '故宫博物院'],
  ['夫子庙', '夫子庙'],
  ['鼓浪屿', '鼓浪屿'],
  ['滇池', '滇池'],
  ['海埂大坝', '滇池海埂大坝'],
  ['西山', '西山风景区'],
  ['金马坊', '金马碧鸡坊'],
  ['金马碧鸡坊', '金马碧鸡坊'],
  ['昆明老街', '昆明老街'],
  ['南强街', '南强街'],
  ['斗南花卉市场', '斗南花市'],
  ['斗南花市', '斗南花市']
];

const KNOWN_MAIN_PLACES: ReadonlySet<string> = new Set([
  '中华门',
  '凯旋门',
  '朝阳门',
  '西直门',
  '东直门',
  '宣武门',
  '玄武门',
  '和平门',
  '复兴门',
  '建国门',
  '永定门',
  '崇文门',
  '前门',
  '天安门',
  '东门老街',
  '前门大街',
  '南门口',
  '南门',
  '东门',
  '西门',
  '北门'
]);

const CHINESE_RE = /[\u4e00-\u9fff]/;
const CHILD_SEPARATOR_RE = /[-—·•（(：:]/u;

function hasChinese(text: string): boolean {
  return CHINESE_RE.test(text);
}

function stripTrailingSeparators(text: string): string {
  return text.replace(/[\s\-—·•、_/:：(]+$/u, '').trim();
}

function extractUniversityMain(name: string): string | null {
  const matches = name.matchAll(/大学/g);
  for (const match of matches) {
    const index = match.index ?? -1;
    const end = index + '大学'.length;
    if (name[end] === '城') continue;
    const main = name.slice(0, end).trim();
    if (main.length < 3 || !hasChinese(main)) continue;
    const remainder = name.slice(end);
    if (!remainder) return main;
    if (UNIVERSITY_SUBUNIT_KEYWORDS.some((keyword) => remainder.includes(keyword))) return main;
    if (remainder.length >= 1) return main;
  }
  return null;
}

function splitByChildSeparator(name: string): string | null {
  const match = CHILD_SEPARATOR_RE.exec(name);
  if (!match || match.index <= 0) return null;
  const main = stripTrailingSeparators(name.slice(0, match.index));
  return main.length >= 2 && hasChinese(main) ? main : null;
}

function extractScenicMain(name: string): string | null {
  const separated = splitByChildSeparator(name);
  if (separated) return normalizePlaceName(separated);

  if (SCENIC_AGGREGATION_RULES.some(([, mainName]) => name === mainName)) return name;

  for (const [keyword, mainName] of SCENIC_AGGREGATION_RULES) {
    if (name.includes(keyword) && name !== mainName) return mainName;
  }

  const terms = [...SCENIC_MAIN_TERMS].sort((a, b) => b.length - a.length);
  for (const term of terms) {
    const index = name.indexOf(term);
    if (index <= 0) continue;
    const end = index + term.length;
    const main = name.slice(0, end);
    const remainder = name.slice(end);
    if (remainder && SCENIC_CHILD_KEYWORDS.some((keyword) => remainder.includes(keyword))) {
      return main;
    }
  }
  return null;
}

export function normalizePlaceName(name: string): string {
  if (typeof name !== 'string') return '';
  let current = name.trim();
  if (!current) return '';
  if (KNOWN_MAIN_PLACES.has(current)) return current;

  const universityMain = extractUniversityMain(current);
  if (universityMain) return universityMain;

  const scenicMain = extractScenicMain(current);
  if (scenicMain && scenicMain !== current) return scenicMain;

  while (true) {
    let stripped = current;
    for (const suffix of AUXILIARY_SUFFIXES) {
      if (stripped.endsWith(suffix) && stripped.length > suffix.length) {
        const candidate = stripTrailingSeparators(stripped.slice(0, -suffix.length));
        if (candidate.length >= 2 && hasChinese(candidate)) {
          stripped = normalizePlaceName(candidate);
          break;
        }
      }
    }
    if (stripped === current) break;
    current = stripped;
    if (KNOWN_MAIN_PLACES.has(current)) break;
  }
  return current;
}

function looksLikeChildPlace(raw: string, normalized: string): boolean {
  if (KNOWN_MAIN_PLACES.has(normalized)) return false;
  const remainder = raw.replace(normalized, '');
  return [...UNIVERSITY_SUBUNIT_KEYWORDS, ...SCENIC_CHILD_KEYWORDS, ...AUXILIARY_SUFFIXES].some((keyword) =>
    remainder.includes(keyword)
  );
}

export function isAuxiliaryPoi(name: string, category?: string | null): boolean {
  if (typeof name !== 'string' || !name.trim()) return true;
  const raw = name.trim();
  const cat = category || '';

  if (KNOWN_MAIN_PLACES.has(raw)) return false;
  for (const keyword of [...LODGING_KEYWORDS, ...FOOD_SHOP_KEYWORDS, ...LOW_VALUE_KEYWORDS]) {
    if (raw.includes(keyword) || cat.includes(keyword)) return true;
  }
  if (AUXILIARY_CATEGORY_HINTS.some((hint) => cat.includes(hint))) return true;
  for (const suffix of AUXILIARY_SUFFIXES) {
    if (raw.endsWith(suffix) && raw.length > suffix.length) {
      const remainder = stripTrailingSeparators(raw.slice(0, -suffix.length));
      if (remainder.length >= 2) return true;
    }
  }
  const normalized = normalizePlaceName(raw);
  return Boolean(normalized && normalized !== raw && looksLikeChildPlace(raw, normalized));
}

interface DedupeLike {
  name?: string;
  type?: string;
  reason?: string;
  description?: string;
  address?: string;
  suitableFor?: string;
  rating?: number;
  score?: number;
  weight?: number;
}

function badDisplayScore(name: string, category?: string | null): number {
  let score = isAuxiliaryPoi(name, category) ? 100 : 0;
  for (const keyword of [...UNIVERSITY_SUBUNIT_KEYWORDS, ...AUXILIARY_SUFFIXES, ...LODGING_KEYWORDS]) {
    if (name.includes(keyword)) score += 12;
  }
  for (const keyword of [...FOOD_SHOP_KEYWORDS, ...LOW_VALUE_KEYWORDS]) {
    if (name.includes(keyword)) score += 20;
  }
  return score;
}

function contentScore(entry: DedupeLike): number {
  let score = 0;
  for (const key of ['rating', 'score', 'weight'] as const) {
    const value = entry[key];
    if (typeof value === 'number') score += Math.round(value * 10);
  }
  for (const key of ['reason', 'description', 'address', 'suitableFor'] as const) {
    const value = entry[key];
    if (typeof value === 'string') score += Math.min(value.length, 80);
  }
  return score;
}

export function dedupePlaces<T extends Place>(places: readonly T[]): T[] {
  if (!Array.isArray(places) || places.length === 0) return [];
  const groups = new Map<string, Array<{ index: number; item: T }>>();
  const order: string[] = [];

  places.forEach((item, index) => {
    const rawName = typeof item?.name === 'string' ? item.name : '';
    const key = rawName.trim() ? normalizePlaceName(rawName) || rawName.trim() : `__unnamed__::${index}`;
    if (!groups.has(key)) {
      groups.set(key, []);
      order.push(key);
    }
    groups.get(key)!.push({ index, item });
  });

  const deduped: T[] = [];
  for (const key of order) {
    const bucket = groups.get(key)!;
    bucket.sort((a, b) => {
      const badDiff = badDisplayScore(a.item.name, a.item.type) - badDisplayScore(b.item.name, b.item.type);
      if (badDiff !== 0) return badDiff;
      const lengthDiff = Math.abs(a.item.name.length - key.length) - Math.abs(b.item.name.length - key.length);
      if (lengthDiff !== 0) return lengthDiff;
      const scoreDiff = contentScore(b.item) - contentScore(a.item);
      if (scoreDiff !== 0) return scoreDiff;
      return a.index - b.index;
    });
    deduped.push(maybeRenameToMain(bucket[0].item, key));
  }
  return deduped.length ? deduped : [...places];
}

function maybeRenameToMain<T extends Place>(item: T, normalizedName: string): T {
  if (!normalizedName || typeof item?.name !== 'string') return item;
  if (item.name.trim() === normalizedName) return item;
  if (KNOWN_MAIN_PLACES.has(item.name.trim())) return item;
  if (!isAuxiliaryPoi(item.name, item.type) && normalizePlaceName(item.name) !== normalizedName) return item;
  return { ...item, name: normalizedName };
}
