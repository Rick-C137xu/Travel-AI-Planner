/**
 * V4.3.2 前端 POI 去重与地点聚合工具。
 *
 * 与 apps/api/app/place_dedupe.py 保持同名 / 同语义实现，覆盖：
 * - 前端 Mock 模式（VITE_USE_MOCK=true）下 mockPlanner.ts 的返回。
 * - 后端模式下 services/api.ts 拿到后端返回后的兜底去重。
 *
 * 不依赖任何运行时库，仅按名称 / 类别规则去重；真实坐标聚类留到接入真实地图 API 后处理。
 */
import type { Place } from '@/types';

// 末尾附属后缀：按长度从长到短匹配，避免「地下停车场」被「停车场」先吃掉。
const AUXILIARY_SUFFIXES: readonly string[] = [
  '出租车上客点',
  '网约车上车点',
  '地上停车场',
  '地下停车场',
  '游客中心',
  '服务中心',
  '服务区',
  '售票处',
  '停车场',
  '公交站',
  '地铁站',
  '卫生间',
  '洗手间',
  '进出口',
  '东门',
  '西门',
  '南门',
  '北门',
  '正门',
  '后门',
  '侧门',
  '入口',
  '出口'
];

const AUXILIARY_CATEGORY_HINTS: readonly string[] = [
  '停车场',
  '公交站',
  '地铁站',
  '出入口',
  '卫生间',
  '洗手间',
  '公共厕所',
  '出租车',
  '网约车',
  '加油站',
  '充电站'
];

// 形似附属但实际是知名主地点，归一化时直接放过，避免「中华门 → 中华」误伤。
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

function hasChinese(text: string): boolean {
  return CHINESE_RE.test(text);
}

function stripTrailingSeparators(text: string): string {
  return text.replace(/[\s\-·、_/]+$/u, '');
}

/**
 * 剥离末尾附属后缀，得到主地点名。
 *
 * 示例：
 * - 云南大学东门 → 云南大学
 * - 翠湖公园南门 → 翠湖公园
 * - 云南大学东门停车场 → 云南大学（叠加后缀也能剥干净）
 * - 中华门 / 朝阳门 / 前门大街 / 东门老街 → 原样返回（白名单 + 末尾不匹配规则保护）
 */
export function normalizePlaceName(name: string): string {
  if (typeof name !== 'string') return '';
  let current = name.trim();
  if (!current) return '';
  if (KNOWN_MAIN_PLACES.has(current)) return current;
  while (true) {
    let stripped = current;
    for (const suffix of AUXILIARY_SUFFIXES) {
      if (stripped.endsWith(suffix) && stripped.length > suffix.length) {
        const candidate = stripTrailingSeparators(stripped.slice(0, -suffix.length));
        if (candidate.length >= 2 && hasChinese(candidate)) {
          stripped = candidate;
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

/**
 * 是否为不该独立展示的附属 POI：
 * 1. 类别命中 AUXILIARY_CATEGORY_HINTS（停车场 / 公交站 / 出入口...）。
 * 2. 名称末尾是附属后缀，且剥离后剩余 ≥ 2 个中文字符（说明原名只是某主地点的附属）。
 * 3. 名称是主地点白名单则一定返回 false，避免误判。
 */
export function isAuxiliaryPoi(name: string, category?: string | null): boolean {
  if (typeof name !== 'string' || !name.trim()) return true;
  if (category && AUXILIARY_CATEGORY_HINTS.some((hint) => category.includes(hint))) return true;
  const raw = name.trim();
  if (KNOWN_MAIN_PLACES.has(raw)) return false;
  for (const suffix of AUXILIARY_SUFFIXES) {
    if (raw.endsWith(suffix) && raw.length > suffix.length) {
      const remainder = stripTrailingSeparators(raw.slice(0, -suffix.length));
      if (remainder.length >= 2 && hasChinese(remainder)) return true;
    }
  }
  return false;
}

interface DedupeLike {
  name?: string;
  type?: string;
  reason?: string;
  description?: string;
  address?: string;
  suitableFor?: string;
}

function contentScore(entry: DedupeLike): number {
  let score = 0;
  for (const key of ['reason', 'description', 'address', 'suitableFor'] as const) {
    const value = entry[key];
    if (typeof value === 'string') score += Math.min(value.length, 80);
  }
  return score;
}

/**
 * 按归一化后的主地点名去重并合并。
 *
 * 规则：
 * 1. 同一归一化名下，非附属 POI 优先；并列时按 reason/address 完整度优先。
 * 2. 不破坏 Place 数据结构，仅在「整条都是附属」时把 name 替换为归一化后的主名。
 * 3. 保持首次出现顺序（按代表条目在输入里的首次出现位置）。
 * 4. 永不返回空列表：极端情况下回退到原输入。
 */
export function dedupePlaces<T extends Place>(places: readonly T[]): T[] {
  if (!Array.isArray(places) || places.length === 0) return [];
  const groups = new Map<string, Array<{ index: number; item: T }>>();
  const order: string[] = [];
  places.forEach((item, index) => {
    const rawName = typeof item?.name === 'string' ? item.name : '';
    let key: string;
    if (!rawName.trim()) {
      key = `__unnamed__::${index}`;
    } else {
      const normalized = normalizePlaceName(rawName);
      key = normalized || rawName.trim();
    }
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
      const auxA = isAuxiliaryPoi(a.item.name, a.item.type) ? 1 : 0;
      const auxB = isAuxiliaryPoi(b.item.name, b.item.type) ? 1 : 0;
      if (auxA !== auxB) return auxA - auxB;
      const scoreDiff = contentScore(b.item) - contentScore(a.item);
      if (scoreDiff !== 0) return scoreDiff;
      return a.index - b.index;
    });
    const winner = bucket[0].item;
    deduped.push(maybeRenameToMain(winner, key));
  }
  return deduped.length ? deduped : [...places];
}

function maybeRenameToMain<T extends Place>(item: T, normalizedName: string): T {
  if (!normalizedName || typeof item?.name !== 'string') return item;
  if (item.name.trim() === normalizedName) return item;
  if (!isAuxiliaryPoi(item.name, item.type)) return item;
  if (KNOWN_MAIN_PLACES.has(item.name.trim())) return item;
  return { ...item, name: normalizedName };
}
