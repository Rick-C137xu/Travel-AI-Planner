# Change Record

## 2026-05-21 V4.4 Local User Preferences

### 背景

用户测试不同目的地时，每次都要重复填写稳定偏好，例如不喜欢早起、偏好轻松节奏、默认预算、交通方式、住宿倾向、常用兴趣和避雷标签。本轮新增本地用户偏好保存，让新建计划时可以快速复用这些长期偏好，同时不接入登录、数据库或新 API。

### 修改文件

- `apps/web/src/types.ts`
  - 新增 `WakeUpPreference`、`AccommodationPreference`、`UserPreferenceProfile` 类型。
- `apps/web/src/services/userPreferences.ts`
  - 新增本地偏好服务。
  - localStorage key：`travel_ai_planner_user_preferences_v1`。
  - 提供 `getUserPreferences()`、`saveUserPreferences(profile)`、`clearUserPreferences()`、`hasUserPreferences()`、`mergePreferencesIntoTravelForm(form, profile)`。
  - 读取、解析、写入均做 try/catch，偏好数据损坏或 localStorage 不可用时不会影响主流程。
- `apps/web/src/components/StartPage.vue`
  - 检测到本地偏好时显示“使用默认偏好 / 重新填写 / 管理偏好”。
  - 增加偏好管理摘要与“清除默认偏好”按钮。
  - 明确提示数据仅保存在当前浏览器，不会上传服务器。
- `apps/web/src/components/GuidedChat.vue`
  - 在偏好题阶段提供“保存为我的默认偏好”按钮。
  - 保存前先提交当前题答案，避免当前题未写入偏好。
- `apps/web/src/components/AppHeader.vue`
  - 页面版本标签升级到 V4.4，同时保留 AI / 高德 / Mock / Weather 状态展示。
- `apps/web/src/store/usePlannerStore.ts`
  - 后端默认 fallback 标签升级为 `V4.4 后端`。
- `apps/web/src/styles.css`
  - 新增本地偏好提示、管理区和移动端按钮布局样式。
- `README.md`
  - 当前版本更新为 V4.4，并说明本地偏好保存能力与限制。
- `AGENTS.md`
  - 当前版本说明更新为 V4.4，并记录 localStorage key 与约束。
- `docs/CHANGE_RECORD.md`
  - 记录本轮改动、保存字段、不保存字段、清除方式和检查结果。

### 保存内容

- 行程强度：`pace`
- 起床偏好：`wakeUpPreference`
- 默认预算：`budgetLevel`
- 默认交通方式：`transportPreference`
- 默认住宿偏好：`accommodationPreference`
- 默认兴趣标签：`interestTags`
- 默认避雷偏好：`avoidTags`
- 更新时间：`updatedAt`

### 不保存内容

- 目的地
- 出发日期 / 结束日期
- 游玩天数
- 人数
- 真实 API Key 或任何后端部署配置
- 已生成的候选地点和行程内容

### 使用方式

- 用户在问答偏好阶段点击“保存为我的默认偏好”。
- 下次新建计划时，Start 页会提示检测到默认偏好，可选择“使用默认偏好”或“重新填写”。
- “管理偏好”可查看摘要；“清除默认偏好”会删除 `travel_ai_planner_user_preferences_v1`，恢复无偏好状态。

### 说明

- 本轮只做浏览器本地保存，不接入登录系统、数据库或新第三方 API。
- 换设备不会同步；清理浏览器缓存后会丢失。
- 后续如果加入登录系统，可将本地偏好升级为云端同步。
- 未修改 Render / Vercel 环境变量，未提交任何真实 Key。

### 检查结果

- `python -m compileall app`：通过
- `npm.cmd run typecheck`：通过
- `npm.cmd run build`：通过

## 2026-05-21 V4.3.5 Over-filter Fix

### 背景

V4.3.4 引入全国通用主地点聚合后，`is_auxiliary_poi / isAuxiliaryPoi` 对「东门 / 图书馆 / 学院 / 游客中心」等子 POI 的判断过于靠前。高德 POI 入口 `_collect_amap_pois` 会在 `dedupe_places` 之前调用过滤，导致「云南大学呈贡校区生命科学学院」「云南大学东门」这类本应归并为「云南大学」的结果被直接跳过，最终候选列表里反而不再出现云南大学。

### 修改文件

- `apps/api/app/place_dedupe.py`
  - 版本语义更新为 V4.3.5。
  - `is_auxiliary_poi` 调整顺序：先 `normalize_place_name`，如果能归并成受保护主地点（大学、景区、公园、博物馆、古镇、老街、湖、山、岛、广场等），则不判为辅助 POI。
  - 保留真正低价值 POI 过滤：酒店、民宿、客栈、餐厅、便利店、写字楼、小区等仍直接过滤。
  - 展示名排序增加类别惩罚，避免「云南大学东门」这类出入口条目赢过「云南大学呈贡校区生命科学学院」等更有上下文的高校条目。
- `apps/api/app/services/planner_service.py`
  - 高德 POI 收集入口改为先计算 `normalize_place_name`，用归一化主名做 `seen_names` 去重 key。
  - 可归并子 POI 会被改名为主地点后进入后续流程，例如「云南大学东门」进入候选时已是「云南大学」。
  - 只有无法归并且 `is_auxiliary_poi=True` 的低价值 POI 才会在入口阶段跳过。
- `apps/web/src/services/placeDedupe.ts`
  - 同步后端保护逻辑，保证前端 Mock、后端回包兜底、fallback 去重行为一致。
- `README.md`
  - 当前版本更新为 V4.3.5，说明 Over-filter 修复。
- `AGENTS.md`
  - 当前版本说明更新为 V4.3.5，并强调先归并主地点再过滤。
- `docs/CHANGE_RECORD.md`
  - 记录本次修复、验证样例和检查结果。

### 验证样例

高校类：

```text
云南大学呈贡校区生命科学学院 -> 云南大学，非过滤
云南大学呈贡校区新闻学院 -> 云南大学，非过滤
云南大学图书馆 -> 云南大学，非过滤
云南大学东门 -> 云南大学，非过滤
北京大学东门 -> 北京大学，非过滤
浙江大学紫金港校区 -> 浙江大学，非过滤
武汉大学信息学部 -> 武汉大学，非过滤
广州大学城 -> 广州大学城，非过滤，不误截成广州大学
```

景区类：

```text
昆明翠湖公园-竹林岛 -> 翠湖公园，非过滤
翠湖公园游乐场 -> 翠湖公园，非过滤
西湖风景区-断桥残雪 -> 西湖风景区，非过滤
故宫博物院午门 -> 故宫博物院，非过滤
```

应过滤类：

```text
XX停车场 -> 过滤
XX厕所 -> 过滤
XX售票处 -> 过滤
XX酒店 -> 过滤
XX民宿 -> 过滤
XX客栈 -> 过滤
XX便利店 -> 过滤
```

### 检查结果

- `python -m compileall app`：通过
- `npm.cmd run typecheck`：通过
- `npm.cmd run build`：通过
- 手工验证：高校、景区主地点样例均为 `aux=False` 且可归并；低价值 POI 样例均为 `aux=True`；多条云南大学子 POI 经 `dedupe_places` 后返回单条「云南大学」。

## 2026-05-21 V4.3.4 Generic POI Aggregation

### 背景

V4.3.2 / V4.3.3 已经能处理一部分昆明 POI 去重，但仍存在全国通用问题：高德 POI 可能返回高校内部学院、校区、图书馆、食堂、门岗，或景区内部入口、码头、游客中心、售票处等子地点。用户在旅行地点推荐阶段真正需要的是「云南大学」「北京大学」「西湖风景区」「宽窄巷子」「故宫博物院」这类主地点，而不是细碎设施。

### 修改文件

- `apps/api/app/place_dedupe.py`
  - 将版本语义升级为 V4.3.4 Generic POI Aggregation。
  - 新增通用高校主名提取：命中「大学」时优先取第一个非「大学城」的大学主名，例如「云南大学呈贡校区生命科学学院」归一为「云南大学」。
  - 新增通用景区主地点聚合：支持 `-`、`—`、`·`、`•`、`（`、`(`、`：`、`:` 等子地点分隔符，并按公园、景区、风景区、古镇、老街、步行街、博物馆、寺庙、湖、山、岛、广场、巷、街等主地点词截取。
  - 扩展辅助 POI 过滤：停车场、入口、出口、售票处、游客中心、厕所、公交站、地铁站、酒店、民宿、客栈、餐厅、便利店、写字楼、小区等默认不作为景点候选。
  - 调整 `dedupe_places` 展示名选择：优先更短、更接近归一化主名、且不含辅助词的条目；必要时把子 POI 展示名重命名为主地点。
- `apps/web/src/services/placeDedupe.ts`
  - 同步后端规则和函数语义，保证前端 Mock、后端回包兜底、fallback 路径行为一致。
- `apps/web/src/services/mockPlanner.ts`
  - 前端 mock 行程生成前对传入 selected places 再调用一次 `dedupePlaces`。
- `README.md`
  - 当前版本更新为 V4.3.4，并补充全国通用 POI 主地点聚合说明。
- `AGENTS.md`
  - 当前版本说明更新为 V4.3.4，并补充以后修改 POI 去重时必须前后端同步。
- `docs/CHANGE_RECORD.md`
  - 记录本次小版本修复背景、修改范围、规则和验证样例。

### 验证样例

高校聚合：

```text
云南大学呈贡校区生命科学学院 -> 云南大学
云南大学呈贡校区新闻学院 -> 云南大学
北京大学东门 -> 北京大学
浙江大学紫金港校区 -> 浙江大学
武汉大学信息学部 -> 武汉大学
广州大学城 -> 广州大学城
```

景区聚合：

```text
昆明翠湖公园-竹林岛 -> 翠湖公园
翠湖公园游乐场 -> 翠湖公园
西湖风景区-断桥残雪 -> 西湖风景区
宽窄巷子游客中心 -> 宽窄巷子
故宫博物院午门 -> 故宫博物院
鼓浪屿游客中心 -> 鼓浪屿
```

过滤：

```text
XX停车场 -> 过滤
XX酒店 -> 过滤
XX民宿 -> 过滤
XX游客中心 -> 过滤
XX售票处 -> 过滤
XX厕所 -> 过滤
```

### 不变 / 不做

- 未新增 API，未修改任何真实 API Key、Render / Vercel 环境变量或部署配置。
- 未引入新依赖，未改 UI 大布局。
- 未删除 V4.3.2 / V4.3.3 已有白名单保护，继续保留「中华门 / 朝阳门 / 西直门 / 宣武门 / 玄武门 / 凯旋门 / 前门大街 / 东门老街」等主地点。

### 检查结果

- `python -m compileall app`：通过
- `npm.cmd run typecheck`：通过
- `npm.cmd run build`：通过
- 手工验证：高校聚合、景区聚合、辅助 POI 过滤样例均符合本节记录，特别是「云南大学呈贡校区生命科学学院 -> 云南大学」。

## 2026-05-21 V4.3.3 Enhanced Place Aggregation

### 背景

V4.3.2 已加入基础 POI 去重（门 / 停车场 / 入口过滤），但实际测试昆明时仍出现第二层重复：

1. **景区内部子景点重复**：
   - 翠湖公园、翠湖·阮堤、翠湖公园游乐场、昆明翠湖公园-竹林岛、昆明翠湖公园-说园、昆明翠湖公园-唐堤、翠湖·定西桥、昆明翠湖公园-滇花苑
   - 期望：只保留「翠湖公园」

2. **高校内部学院/校区重复**：
   - 云南大学呈贡校区、云南大学呈贡校区新闻学院、云南大学呈贡校区药学院、云南大学呈贡校区经济学院
   - 期望：只保留「云南大学」

3. **住宿类 POI 误入景点推荐**：
   - 滇池逸境民宿(昆明滇池海埂大坝店)
   - 期望：不作为景点候选返回

V4.3.3 在 V4.3.2 基础上增强主地点聚合逻辑，**不回退**任何 V4.3.2 / V4.3.1 能力，不接新增 API，不改任何 Key / 环境变量。

### 修改文件

- `apps/api/app/place_dedupe.py`：
  - 新增 `_LODGING_KEYWORDS`（酒店/民宿/客栈/宾馆/旅馆/公寓/青旅/住宿/旅社/招待所）。
  - 新增 `_LOW_VALUE_KEYWORDS`（写字楼/商务楼/办公楼/小区/住宅/售楼处/房产/中介）。
  - 新增 `_SCENIC_AGGREGATION_RULES`（翠湖→翠湖公园、滇池→滇池、海埂大坝→滇池海埂大坝、西山→西山风景区、金马坊→金马碧鸡坊、昆明老街→昆明老街、南强街→南强街、斗南花市→斗南花市）。
  - 新增 `_UNIVERSITY_NAMES`（云南大学、昆明理工大学、云南师范大学、云南民族大学、云南财经大学、昆明医科大学）。
  - 新增 `_UNIVERSITY_SUBUNIT_SUFFIXES`（学院/校区/图书馆/教学楼/实验楼/行政楼/食堂/宿舍/体育馆/操场/礼堂）。
  - `normalize_place_name` 增强：景区子景点聚合 + 高校子单位聚合，优先于末尾后缀剥离。
  - `is_auxiliary_poi` 增强：住宿类 POI 过滤 + 低价值 POI 过滤，优先于原有逻辑。

- `apps/web/src/services/placeDedupe.ts`：前端镜像实现，签名与后端一致。

- `docs/CHANGE_RECORD.md`：本条记录。
- `README.md`：版本号升级到 V4.3.3。

### 聚合规则（手工验证样例）

#### 翠湖相关 POI

输入：
```
翠湖公园
翠湖·阮堤
翠湖公园游乐场
昆明翠湖公园-竹林岛
昆明翠湖公园-说园
昆明翠湖公园-唐堤
翠湖·定西桥
昆明翠湖公园-滇花苑
```

期望输出：
- 只保留「翠湖公园」（所有含「翠湖」关键词的条目归一化为「翠湖公园」）

#### 云南大学相关 POI

输入：
```
云南大学呈贡校区
云南大学呈贡校区新闻学院
云南大学呈贡校区药学院
云南大学呈贡校区经济学院
云南大学图书馆
云南大学食堂
```

期望输出：
- 只保留「云南大学」（所有含「云南大学」+ 子单位后缀的条目归一化为「云南大学」）

#### 住宿类 POI

输入：
```
滇池逸境民宿(昆明滇池海埂大坝店)
昆明XX酒店
XX客栈
XX宾馆
XX旅馆
XX公寓
XX青旅
```

期望输出：
- 全部被 `is_auxiliary_poi` 判定为 True，不进入候选地点列表

#### 低价值 POI

输入：
```
XX写字楼
XX商务楼
XX小区
XX住宅
XX售楼处
```

期望输出：
- 全部被 `is_auxiliary_poi` 判定为 True，不进入候选地点列表

### 不变 / 不做

- 未修改 `AI_API_KEY / AI_MODEL / AMAP_KEY / VITE_AMAP_KEY / VITE_API_BASE_URL / VITE_USE_MOCK / securityJsCode`。
- 未改 Render / Vercel 部署配置；未引入新依赖。
- 未做坐标聚类（真实坐标聚合留到接入真实地图能力后再做）。
- 未删除 V4.3.2 已有去重逻辑；V4.3.3 是在 V4.3.2 基础上的增强。
- 未修改 UI（除文档外）。

### 检查结果

- `python -m compileall app`：通过
- `npm.cmd run typecheck`：通过
- `npm.cmd run build`：通过

## 2026-05-21 V4.3.2 POI Dedupe and Place Aggregation

### 背景

用户在测试昆明目的地时反馈：候选地点中出现「云南大学东门 / 西门 / 北门 / 停车场」「翠湖公园南门 / 停车场」「金马坊停车场」等条目，看起来像多个独立景点。这些其实是同一个主地点的附属 POI，会让推荐列表像 POI 数据库导出，不像真实旅行规划结果。

V4.3.2 在 V4.3.1（AI / 高德 / 天气）已有能力之上，统一增加基础 POI 去重与地点聚合，**不回退**任何 V4 能力，不接新增 API，不改任何 Key / 环境变量。

### 新增文件

- `apps/api/app/place_dedupe.py`：后端 POI 去重核心
  - `normalize_place_name(name)`：剥离末尾附属后缀，得到主地点名（叠加后缀也能剥干净）。
  - `is_auxiliary_poi(name, category=None)`：综合名称末尾后缀 + 类别命中（停车场 / 公交站 / 出入口…）判定低价值 POI；命中主地点白名单时一定返回 False。
  - `dedupe_places(places)`：按归一化名分组，非附属优先 + 内容完整度优先 + 首次出现顺序，永不返回空列表。
- `apps/web/src/services/placeDedupe.ts`：前端镜像实现，签名 `normalizePlaceName / isAuxiliaryPoi / dedupePlaces`，与后端语义一致。

### 修改文件

- `apps/api/app/services/planner_service.py`
  - 引入 `dedupe_places / is_auxiliary_poi`。
  - `recommend_places` / `extract_places` 拆分为公共方法 + `_impl` 私有方法，公共方法在返回前统一走一次 `dedupe_places`。
  - `_collect_amap_pois` 在高德 POI 入口处直接 `is_auxiliary_poi` 过滤，节约后续 AI 文案增强 token，避免同一主地点的多 POI 同时进 AI prompt。
  - `generate_itinerary` 在排序前对入参 places 走一次 `dedupe_places`，避免同一主地点被分到同一天多个时段。
- `apps/web/src/services/mockPlanner.ts`
  - 引入 `dedupePlaces`。
  - 新增「昆明」城市 Mock：翠湖公园 / 云南大学 / 金马碧鸡坊 / 云南省博物馆 / 滇池海埂大坝 / 西山风景区 / 斗南花市 / 南强街 / 昆明老街 / 官渡古镇 / 讲武堂旧址 / 大观公园 / 过桥米线老店；不含任何门 / 停车场 / 入口条目。
  - `mockRecommendPlaces / mockExtractPlaces` 返回前走一次 `dedupePlaces`。
- `apps/web/src/services/api.ts`：新增 `applyPlaceDedupe<T>(envelope)`，对后端返回的 `Place[]` 再保险一次去重，兼容旧版本后端 / 前端 Mock fallback 路径。
- `apps/web/src/components/PlaceRecommendation.vue` + `apps/web/src/styles.css`：在候选页 `source-note` 中增加一行 `dedupe-hint`：「V4.3.2 已加入基础 POI 去重，会尽量合并景点入口、停车场等附属地点，优先展示主游玩地点。」样式克制，不打扰主流程。

### 去重规则（手工验证样例）

输入（模拟昆明真实高德 POI 返回 / 用户粘贴）：

```
云南大学东门
云南大学西门
云南大学北门
云南大学停车场
翠湖公园南门
翠湖公园停车场
金马坊停车场
金马碧鸡坊
```

期望经 `dedupePlaces` / `dedupe_places` 处理后：

- 「云南大学东门 / 西门 / 北门 / 停车场」→ 合并为「云南大学」（无主条目时被附属条目重命名）。
- 「翠湖公园南门 / 停车场」→ 合并为「翠湖公园」。
- 「金马坊停车场」→ 合并为「金马坊」。
- 「金马碧鸡坊」与「金马坊」名称不一致（前者多 2 字），按名称归一化属于不同组，保留 `金马碧鸡坊` 作为更常用全称。
- 不影响「中华门 / 朝阳门 / 西直门 / 宣武门 / 玄武门 / 凯旋门 / 前门大街 / 东门老街」这类知名主地点（命中 `_KNOWN_MAIN_PLACES` 白名单或末尾不匹配附属后缀规则）。

### 不变 / 不做

- 未修改 `AI_API_KEY / AI_MODEL / AMAP_KEY / VITE_AMAP_KEY / VITE_API_BASE_URL / VITE_USE_MOCK / securityJsCode`。
- 未改 Render / Vercel 部署配置；未引入新依赖。
- 未做坐标聚类（真实坐标聚合留到接入真实地图能力后再做）。
- 未删除 V2.1 已有城市专属 Mock 数据。

### 检查结果

- `python -m compileall app`：通过
- `npm.cmd run typecheck`：通过
- `npm.cmd run build`：通过

## 2026-05-20 V4.3.1 文案与缓存版本统一修复

### 问题

- Header 已显示 V4.3，但行程页 / 候选页 / 粘贴攻略 / StartPage / store 默认 fallback 文案仍硬编码 `V4.2`。
- 行程缓存前缀仍是 `travel-ai-planner:itinerary:v1:`，部署 V4.3 后用户旧缓存里的 `sourceLabel` 仍是 V4.2 文案，会被回填到行程页。

### 修改

- `apps/web/src/components/StartPage.vue`、`apps/web/src/components/PlaceRecommendation.vue`、`apps/web/src/components/PasteGuidePanel.vue`、`apps/web/src/components/ItineraryView.vue`：所有用户可见 `V4.2` 文案统一替换为 `V4.3`，未触碰 AI / 高德 / 天气逻辑。
- `apps/web/src/services/api.ts`：默认 `dataSourceLabel` fallback 与前端 Mock 提示中的 `V4.2` → `V4.3`。
- `apps/web/src/store/usePlannerStore.ts`：
  - `ITINERARY_CACHE_PREFIX` 升级为 `travel-ai-planner:itinerary:v4.3:`，并保留 `LEGACY_ITINERARY_CACHE_PREFIXES = ['travel-ai-planner:itinerary:v1:']`，读缓存时自动清理旧前缀条目。
  - `readItineraryCache` 检测到 `sourceLabel` 仍含 `V4.2` 字样时直接丢弃该缓存。
  - `updateRuntimeStatus` 默认 fallback `V4.2 后端` → `V4.3 后端`。

### 不变

- 未修改 `AI_API_KEY / AI_MODEL / AMAP_KEY / VITE_AMAP_KEY / securityJsCode`；未改 Render / Vercel 配置；未改后端 AI / 高德 / 天气逻辑。
- 未改 `STORAGE_KEY`，不会清掉用户偏好/草稿，只清行程缓存这一层。

## 2026-05-20 V4.3.1 候选地点 AI 文案 hotfix（candidate AI copy fallback / status）

### 问题

- 候选页 POI 来自高德成功，但 AI 文案增强（`_ai_annotate_pois`）解析失败时，旧逻辑使用与行程 AI Fallback 同名标签 `"高德地图 + 后端模板"`，让前端 Header 误显示成 `V4.3 AI Fallback`，且红色横条提示「AI 请求失败」，让用户误以为整体 AI 失败。

### 修改

- `apps/api/app/services/planner_service.py`
  - `_recommend_ai_amap` 在 POI 成功 + AI 文案失败时改为新标签 `"高德地图 + 规则文案"`，与行程级 `"高德地图 + 后端模板"` 语义解耦。
  - `_ai_annotate_pois` 显式传入 `temperature=0.3 / timeout=20s / max_tokens=min(900, 110×POI 数)`，失败更快且不放大 token 消耗。
  - 新增 `_coerce_place_annotations`：宽容解析 AI 文案返回，支持 `{"places":[...]}`、`{"data"|"items"|"results"|"list"|"annotations":[...]}`、root array、单 dict；不抛异常，失败返回空 dict 由上层走规则文案。
- `apps/web/src/components/AppHeader.vue`：新增 `"高德地图 + 规则文案" → V4.3 Amap + Rule Copy` 映射；行程页天气 `+ Weather` 后缀逻辑保持不变。
- `apps/web/src/components/PlaceRecommendation.vue`：新增 `"高德地图 + 规则文案"` 文案；该标签下不再显示红色 `aiFallbackNotice` / `placeWarning`，只保留 `source-note` 中的温和提示。
- `docs/DEPLOYMENT.md`：补充 V4.3.1 候选页状态映射与验证步骤。

### 不变

- 未修改 `AI_API_KEY / AI_MODEL / AMAP_KEY / VITE_*`；未改 Render / Vercel 配置；未改前端高德 JS Key / securityJsCode。
- 行程页状态独立判断：行程 AI 成功仍显示 `V4.3 AI + Amap + Weather`；行程 AI 失败仍是 `V4.3 AI Fallback (+ Weather)`，与候选页独立。
- AI prompt 长度未增加；`max_tokens` 在候选 annotate 路径上被收紧，token 消耗只减不增。

## 2026-05-20 V4.3 高德天气集成

### 新增 / 修改

- `apps/api/app/services/weather_client.py`：新增高德 `weatherInfo` 封装，复用 `AMAP_KEY`，并行请求 live(`base`) + forecast(`all`)，timeout=6s，失败统一返回 `status=error/disabled` 不抛异常；提供 `build_prompt_line()` 生成单行天气提示。
- `apps/api/app/services/planner_service.py`：`PlannerService` 注入 `WeatherClient`，`generate_itinerary` 中按 `preference.destination` 安全拉一次天气，将单行摘要拼入 AI prompt（不放完整 JSON），meta 中携带 `weather`；AI 失败 / 无 AI 路径均会回写 weather；天气失败不影响主流程。
- `apps/api/app/models.py`：`ApiEnvelope` 增加 `weather: dict | None` 字段。
- `apps/api/app/main.py`：注册 `WeatherClient`，`_envelope` 透传 weather；新增 `GET /api/debug/weather?city=...`，AMAP_KEY 未配置返回 `status=disabled`，调用失败返回 `status=error` 并附 reason，不暴露 Key。
- `apps/api/app/config.py`：`version` 升级 `v4.1` → `v4.3`。
- `apps/web/src/types.ts`：新增 `WeatherInfo / WeatherForecastDay`，`ApiEnvelope.weather`。
- `apps/web/src/store/usePlannerStore.ts`：`PlannerState.weather` + 行程缓存条目 `weather`；`updateRuntimeStatus('itinerary')` 写入；`saveCurrentItineraryToCache` 持久化；`PlaceRecommendation.vue` 命中缓存时恢复 `state.weather`，天气接口失败不破坏缓存。
- `apps/web/src/components/ItineraryView.vue`：行程页新增「天气参考」精简卡片，显示天气/温度/湿度/风向风力/更新时间；无数据展示「暂无天气参考」，不影响主流程。
- `apps/web/src/components/AppHeader.vue`：行程页且 `state.weather.status==='ok'` 时版本签追加 ` + Weather`，例如 `V4.3 AI + Amap + Weather`；候选页保持原标签；版本前缀整体升 V4.3。
- `apps/web/src/styles.css`：新增 `.weather-card / .weather-title / .weather-time / .weather-empty` 极简样式。
- `docs/DEPLOYMENT.md`：补充 V4.3 部署与 `/api/debug/weather` 验证步骤。

### 安全约束

- 未写死 / 未提交任何真实 Key；天气服务复用现有 `AMAP_KEY`；不修改 `AI_API_KEY` / `AI_MODEL` / 前端高德 JS Key / securityJsCode。
- `/api/debug/weather` 与 envelope.weather 都不返回 Key；高德原始 raw 不透传。
- 天气接口超时/失败/无 Key 时安全 fallback，主流程（推荐 / 行程生成）继续运行。



## 2026-05-20 V4.2 稳定体验版

### 背景

V4.1 已经接通 Render 后端、DeepSeek OpenAI-compatible API 与高德 Web 服务，候选地点和行程生成基本可用。本轮重点解决前端把候选地点阶段的 AI fallback 状态误用于行程页的问题，并通过本地行程缓存减少重复请求 `/api/itinerary/generate` 造成的 DeepSeek token 消耗。

### 修改

- `apps/web/src/store/usePlannerStore.ts`
  - 新增 `placeSourceLabel / itinerarySourceLabel` 与 `placeWarning / itineraryWarning`，将候选地点来源和行程来源拆开保存。
  - 新增行程 localStorage 缓存，key 根据 `destination / startDate / days / 已选地点 id 和 name / interests / budgetLevel / transportPreference / pace / dislikes / hotelArea` 生成。
  - 新增读取、写入、清理当前行程缓存的方法；清空当前计划时同步清理对应缓存。
- `apps/web/src/components/AppHeader.vue`
  - Header 根据当前页面实际内容选择候选地点来源或行程来源。
  - 行程页 AI 成功时显示 `Travel AI Planner · V4.2 AI + Amap`；候选地点仅高德时显示 `Travel AI Planner · V4.2 Amap`；最终行程模板降级时才显示 `Travel AI Planner · V4.2 AI Fallback`。
- `apps/web/src/components/PlaceRecommendation.vue`
  - 候选地点页使用候选地点来源文案，不再污染行程来源。
  - AI 补充文案失败但高德 POI 成功时，显示“候选地点来自高德 POI，AI 补充文案失败，已使用规则文案。”
  - 点击“生成行程”时先读取缓存；命中缓存则直接进入行程页，不请求 `/api/itinerary/generate`。
  - 首次生成成功后写入缓存；重新推荐地点时清空当前行程展示状态。
- `apps/web/src/components/ItineraryView.vue`
  - 行程页使用独立的行程来源文案。
  - AI 行程成功时显示“V4.2 高德地图 + AI（按经纬度排序后由 AI 生成行程文案）”。
  - “重新生成行程”会清理当前缓存、重新请求后端并覆盖缓存。
- `apps/web/src/components/PasteGuidePanel.vue` 与 `apps/web/src/components/PlaceCard.vue`
  - 读取候选地点来源标签，避免被行程来源影响。
- `docs/CHANGE_RECORD.md`
  - 新增本次 V4.2 记录。
- `docs/DEPLOYMENT.md`
  - 补充 V4.2 部署后验证方式，包含 `/api/health`、`/api/debug/ai`、`/api/debug/ai?probe=1`、候选地点页、行程页和 Network 请求次数检查。

### 追加修改

- `apps/web/src/components/AppHeader.vue`、`PlaceRecommendation.vue`、`ItineraryView.vue`、`PasteGuidePanel.vue`、`StartPage.vue`、`apps/web/src/services/api.ts`、`apps/web/src/store/usePlannerStore.ts`
  - 将页面可见版本号统一为 V4.2，包含前端 Mock、后端模式、高德模式、AI 模式、AI Fallback 和后端 Mock 等状态。

### 未修改

- 未修改后端业务代码、AI 调用参数、高德 POI 搜索逻辑或 envelope 结构。
- 未修改 `AI_API_KEY`、`AMAP_KEY`、高德 JS API Key、securityJsCode、Render / Vercel 私密环境变量。
- 未新增数据库、登录系统或新的第三方服务。

## 2026-05-20 V4.1.2 AI stability/token hotfix

### 追加修复：行程 JSON 输出与解析诊断

- `apps/api/app/services/ai_client.py`
  - 新增 `json_completion_detailed()`，在业务调用失败时返回结构化诊断：`errorType / errorMessage / rawPreview / choicesContentFound / parsedJsonOk`。
  - 明确区分是否成功读取 `choices[0].message.content`、是否成功解析 JSON。
  - HTTP body 非 JSON、AI content 非 JSON、Markdown fence 或前后解释文字等情况继续只返回脱敏短 `rawPreview`。
- `apps/api/app/services/planner_service.py`
  - `/api/itinerary/generate` 使用 detailed AI 调用；AI 成功但短 schema 无法映射为前端 `DayPlan` 时，返回 `itinerary_schema_error` 而不是笼统格式异常。
  - 兼容 `days / itinerary / plan / data` 等常见顶层字段；若对象本身就是单日计划，也会尝试按单日解析。
  - 行程 prompt 进一步强调只返回严格 `json object`，不返回 Markdown 或解释文字。
- `apps/api/app/models.py` 与 `apps/api/app/main.py`
  - `ApiEnvelope` 增加 AI 安全诊断字段，便于线上从 Network 判断是 content 读取失败、JSON 解析失败，还是 schema 映射失败。

### 背景

DeepSeek 与高德均已在线启用，`/api/debug/ai` 可探测成功，但默认访问 debug 接口会消耗 token；业务接口偶尔因 AI 多输出解释文字、Markdown fence 或 JSON 结构不完全匹配而降级为后端模板。本次只做稳定性与省 token hotfix，不重构、不新增平台、不修改 Key 或模型名。

### 修改

- `apps/api/app/main.py`
  - `/api/debug/ai` 默认只返回当前 AI 配置状态，不再发起真实 DeepSeek 请求。
  - 只有访问 `/api/debug/ai?probe=1` 时才执行一次真实极小探测。
- `apps/api/app/services/ai_client.py`
  - debug probe 的 `maxTokens` 从 64 降为 32。
  - 新增 `debug_status()`，返回 `aiConfigured / aiProvider / aiBaseUrl / aiModel / requestUrl / timeoutSeconds / maxTokens / probeEnabled=false` 等非敏感字段。
  - 增强 JSON 解析：先处理 Markdown fence，再 `json.loads`，失败后提取文本中的第一个完整 JSON object 或 array 再解析。
  - JSON 解析失败时使用 `json_parse_error`，`rawPreview` 继续脱敏并截断，不返回 Key 或完整原始响应。
- `apps/api/app/services/planner_service.py`
  - 行程生成 prompt 进一步精简为短 JSON schema：`days/title/date/items/time/placeName/description/duration/tips`。
  - 行程生成只传最多 8 个已选地点的必要字段：`id/name/type/address/reason/estimatedTime/warning`。
  - 3 天内行程 `max_tokens=900`，更长行程 `max_tokens=1000`，`temperature=0.3`。
  - 兼容 AI 返回的新短 schema，并映射回前端既有 `DayPlan / ItineraryItem` 结构；保留失败时后端模板 fallback。
- `docs/CHANGE_RECORD.md`
  - 新增本次 V4.1.2 记录。
- `docs/DEPLOYMENT.md`
  - 说明 `/api/debug/ai` 默认不消耗 token，真实探测改为 `/api/debug/ai?probe=1`，以及 Render 后端需重新部署。

### 未修改

- 未修改前端 UI 或业务流程。
- 未修改 `AI_MODEL`、`AI_API_KEY`、`AMAP_KEY` 或高德地图逻辑。
- 未新增第三方服务，未删除现有 fallback。

## 2026-05-20 V4.1.1 AI timeout/token hotfix

### 背景

线上 `/api/debug/ai` 已验证 DeepSeek OpenAI-compatible 配置、模型名与网络连通性正常，但 `/api/itinerary/generate` 在生成行程时出现 45s 超时并降级为后端模板。判断主要原因是行程生成 prompt 携带完整地点对象、字段过多且未限制业务 `max_tokens`。

### 修改

- `apps/api/app/services/ai_client.py`
  - 为业务 AI JSON 调用增加默认 `max_tokens=1600`，保留默认 `timeout=45.0s`。
  - `/api/debug/ai` 结果补充 `timeoutSeconds` 与 `maxTokens`，继续不返回任何 API Key。
  - 将超时、JSON/格式异常、其他请求失败的 warning 文案分得更清楚，避免把完整 AI 返回内容暴露给前端。
- `apps/api/app/services/planner_service.py`
  - `/api/itinerary/generate` 生成 AI prompt 时不再传完整 `Place` 对象。
  - 仅传行程需要的精简字段：`id/name/type/reason/suitableFor/estimatedTime/warning/lat/lng`。
  - 仅使用已选地点；若地点较多，最多传前 8 个已排序地点。
  - 行程生成请求使用更短 system/user prompt、`temperature=0.3`、`max_tokens=1200`，并要求只输出 JSON。
  - 保留 AI 失败时后端模板降级；超时、格式异常、其他失败会给出更明确 warning，地点仍来自高德 POI。
- `docs/CHANGE_RECORD.md`
  - 记录本次 V4.1.1 hotfix。
- `docs/DEPLOYMENT.md`
  - 补充 V4.1.1 部署与验证说明。

### 未修改

- 未修改 `AI_MODEL` 默认值或线上模型名，继续兼容 `AI_MODEL=deepseek-v4-flash`。
- 未写入任何真实 `AI_API_KEY`、`AMAP_KEY` 或私密部署配置。
- 未修改高德地图 POI 搜索逻辑。
- 未修改前端业务流程。

## 2026-05-20 V4.1 AI 调试增强（DeepSeek 排查）

### 背景

V4.1 接入 DeepSeek 后，Render 后端 `/api/health` 显示 `dataMode=高德地图 + AI`，`aiEnabled=true`，但前端候选地点与行程页仍提示「AI 请求失败，已降级为后端模板」。Render 业务接口日志只看到 200，看不到 DeepSeek 的真实错误。本轮只做**后端排查增强**：未改前端业务逻辑，未改高德相关代码，未新增真实 Key。

### 修改

- `apps/api/app/services/ai_client.py`
  - 重构为「HTTP 调用层 + 业务封装层」两段：底层 `_raw_chat_completion` 统一捕获并分类异常为 `http_error / request_error / timeout / parse_error / empty_content / unknown`，每种都通过 `logging` 写一条结构化日志：包含 `status_code / model / url / 脱敏 preview`；**不会**打印 `AI_API_KEY` 或 `Authorization` 原文，已用 `_sanitize` 把 `Bearer xxx` 和 `sk-xxx` 替换为 `Bearer ***` / `sk-***`。
  - 新增 `debug_probe()`：发送一个极简 JSON probe（system + user 都包含 `json` 字样、`response_format={"type":"json_object"}`、`max_tokens=64`），返回结构化诊断给 `/api/debug/ai`。
  - 新增 `request_url` 属性，会把 `AI_BASE_URL` 末尾多余的 `/` 去掉后再拼接 `/chat/completions`，避免出现 `https://api.deepseek.com//chat/completions` 这类隐形错误。
- `apps/api/app/main.py`
  - 新增 `GET /api/debug/ai` 路由，转发到 `ai_client.debug_probe()`。
  - 返回 `aiConfigured / aiProvider / aiBaseUrl / aiModel / requestUrl / ok / statusCode / errorType / errorMessage / rawPreview / parsedJsonOk`，**不返回任何 Key**。
- `docs/CHANGE_RECORD.md`：新增本节，说明排查接口的目的与使用方式。
- `docs/DEPLOYMENT.md`：补充 `/api/debug/ai` 的使用说明（见相应章节）。

### 是否修复了 AI 请求失败

代码侧最常见的格式问题已经过排查并确认 OK：

- 请求 URL：`https://api.deepseek.com/chat/completions`（DeepSeek 文档允许，等价于 `/v1/chat/completions`）。
- Header：`Authorization: Bearer ${AI_API_KEY}`、`Content-Type: application/json`。
- Body：`model / messages(system+user) / temperature / response_format={"type":"json_object"}`，prompt 中包含 `json` 字样。

仍未修复的最大可疑点是 **`AI_MODEL=deepseek-v4-flash` 不是 DeepSeek 公开模型名**。DeepSeek OpenAI-compatible 端点公开支持的模型仅为 `deepseek-chat`、`deepseek-reasoner`。若 `/api/debug/ai` 返回 `statusCode=400/422` 且 `rawPreview` 中包含 `model_not_found` / `invalid model` 之类字样，请把 Render 环境变量 `AI_MODEL` 改为 `deepseek-chat` 后重新部署。代码侧未硬编码任何模型别名（避免悄悄替换用户配置）。

### 安全约束

- 任何分支都不打印 `AI_API_KEY` 或完整 `Authorization` header。
- `rawPreview` / 日志 preview 经 `_sanitize` 双重正则脱敏，并强制截断（成功 ≤300 字符，失败 ≤500 字符）。
- 不打印完整用户输入：仅在业务路径走 `planner_service` 时使用 prompt；调试 probe 使用固定无害文本，不携带任何用户隐私输入。
- 没有新增任何环境变量；沿用 `AI_PROVIDER / AI_API_KEY / AI_BASE_URL / AI_MODEL / AMAP_KEY / ALLOWED_ORIGINS`。
- 没有修改前端业务逻辑、没有改高德相关代码、没有改 CORS。

## 2026-05-20 V4.1 AI 接入与降级语义对齐

### 目标

在 V4（高德 POI 已跑通）基础上接入 AI，并把"AI 成功 / AI 失败但高德 OK / 完全无 Key"三种状态在 envelope 与前端文案中显式区分。范围克制，**不重构架构、不删 V4 高德 / 地图 JS API / CORS 任何已跑通能力**。

### 修改

- `apps/api/app/config.py`
  - `Settings.version` 由 `v4` 升级为 `v4.1`，`/health`、`/api/health`、`/api/debug/config` 都会同步显示。
  - `data_mode` 命名按 V4.1 规范统一：`高德地图 + AI` / `高德地图` / `AI 生成` / `后端 Mock`。
  - 仍只通过环境变量读取 `AI_PROVIDER / AI_API_KEY / AI_BASE_URL / AI_MODEL / AMAP_KEY / ALLOWED_ORIGINS`，绝不返回任何 Key。
- `apps/api/app/services/planner_service.py`
  - `_recommend_ai_amap` 与 `_ai_annotate_pois` 改为返回 `(places, warning, ai_succeeded)`，让上层能判断"AI 是否真正成功"。
  - `recommend_places` 新增"高德地图 + 后端模板"降级分支：AI 失败但高德返回了 POI 时，POI 不丢，文案/source 改为后端模板，envelope.warning 明确写 `AI 请求失败，已降级为后端模板，地点仍来自高德 POI。`，`aiEnabled` 仍上报真实配置以区分"AI 未配置"。
  - `extract_places` 同步引入"高德地图 + 后端模板"降级，AI 失败而高德可用时不再退回到无地图标签。
  - `generate_itinerary` 同步引入"高德地图 + 后端模板"降级；AI 成功时标签为 `高德地图 + AI`。
  - `_ai_annotate_pois` 内部 source 选择改为：注释成功且命中 → `AI + 高德`；否则 → `高德地图`，避免在降级时仍宣称是 AI 来源。
  - 不动 `amap_client.py` 与 V4 高德搜索路径。
- `apps/api/app/main.py`：无需改动；版本号、debug/config 字段已经自动跟随 `Settings`。
- `apps/web/src/services/api.ts`：`normalizeBackendResponse` 命名对齐为 `高德地图 + AI / 高德地图 / AI 生成 / 后端 Mock`，并显式让后端的 `dataSourceLabel` 优先（这样"高德地图 + 后端模板"能直接透传给前端）。
- `apps/web/src/store/usePlannerStore.ts`：默认数据来源占位字符串从 `V4 后端` 改为 `V4.1 后端`，行为不变。
- `apps/web/src/components/AppHeader.vue`：按 V4.1 规范展示版本签：
  - `Travel AI Planner · V4.1 AI + Amap`（AI 成功）
  - `Travel AI Planner · V4.1 AI Fallback`（AI 请求失败，POI 仍来自高德）
  - `Travel AI Planner · V4 Amap`（AI 未配置，仅高德）
  - `Travel AI Planner · V4.1 AI`（AI 已配置但未配高德）
  - `Travel AI Planner · V3 Backend Mock`（都没有）
  - `Travel AI Planner · Backend Failed → Frontend Mock`（请求失败）
- `apps/web/src/components/PlaceRecommendation.vue`、`PasteGuidePanel.vue`、`ItineraryView.vue`：文案改成按 `dataSourceLabel` 分支显示；`高德地图 + 后端模板` 状态下额外渲染一行 `AI 请求失败，已降级为后端模板；地点仍来自高德 POI` 的明显提示。
- `apps/web/src/components/PlaceCard.vue`：保持原映射逻辑，仅在"都没 Key"时才把 `Mock数据` 映射为「后端 Mock」，真实 `高德地图 / AI + 高德` 标签直接展示。
- `docs/CHANGE_RECORD.md`：新增本节。
- `docs/DEPLOYMENT.md`、`README.md`、`AGENTS.md`：版本号 V4 → V4.1，记录新的 dataSourceLabel 集合与验证步骤。

### 失败降级行为约束

- AI 请求超时 / HTTP 错误 / JSON 解析失败：返回 `(None, warning)`，绝不抛 500。
- 当 `amap_enabled=True` 且 AI 失败：保留高德 POI，使用模板文案；envelope 中 `dataSourceLabel="高德地图 + 后端模板"`，`aiEnabled=True`（这样前端能识别"AI 配了但失败"），并附 warning。
- 当 `amap_enabled=False` 且 AI 失败：维持 V4 现有降级（`后端 Mock`）。
- 前端 Header 与列表页据此显示 `V4.1 AI Fallback` 版本签 + 一行明显的 warning，**不会**把整个推荐结果替换为前端 Mock。

### 环境变量

- 不新增任何环境变量，沿用 V4：`AI_PROVIDER / AI_API_KEY / AI_BASE_URL / AI_MODEL / AMAP_KEY / ALLOWED_ORIGINS`。
- `.env.example` 与 `apps/api/.env.example` 已在 V4 提供占位，本轮无改动。
- 任何文档、CHANGE_RECORD、代码、日志均未出现真实 Key。

### 检查命令真实结果（见对话末尾）

- `python -m py_compile app/main.py`
- `python -m compileall app`
- `npm.cmd run typecheck`
- `npm.cmd run build`

## 2026-05-19 V4.0 Real AI + Amap Integration Ready

### 新增

- `apps/api/app/config.py`：新增 V4 后端 Settings，集中读取 `AI_PROVIDER / AI_API_KEY / AI_BASE_URL / AI_MODEL / AMAP_KEY / ALLOWED_ORIGINS`，并暴露 `ai_enabled / amap_enabled / data_mode`。
- `apps/api/app/services/__init__.py`：新增 services 包入口。
- `apps/api/app/services/ai_client.py`：V4 AI 调用封装，OpenAI-compatible Chat Completions，所有外部请求带 timeout，所有异常被捕获并降级返回 warning。
- `apps/api/app/services/amap_client.py`：V4 高德 Web 服务封装，POI 关键字搜索 (`/v3/place/text`)，失败时返回空列表由上层降级。
- `apps/api/app/services/planner_service.py`：V4 规划编排层，根据 `aiEnabled / amapEnabled` 选择「AI+高德 / 高德 / AI / 后端 Mock」四种运行模式；包含基于经纬度的最近邻排序、AI 关键词生成、AI 注释 POI、AI 攻略文本提取、AI 行程生成等逻辑，全部带 fallback。

### 修改

- `apps/api/app/main.py`：使用 `Settings + PlannerService`，路由变为薄封装；新增 `GET /api/debug/config`（仅返回非敏感配置：service / version / aiProvider / aiEnabled / amapEnabled / allowedOrigins / dataMode，不返回任何 Key）；`GET /api/health` 增加 `amapEnabled / dataMode`；版本号升级为 `v4`。
- `apps/api/app/ai_client.py`：保留为向后兼容入口，转发到 `app.services.ai_client.AIClient`，避免外部代码因为路径迁移直接报错。
- `apps/api/app/models.py`：`PlaceSource` 由 Literal 放宽为 `str` 以容纳「高德地图」「AI + 高德」「规则 + 高德 提取」等新值；`ApiEnvelope` 新增 `amapEnabled` 字段。
- `apps/web/src/types.ts`：`ApiEnvelope` 新增 `amapEnabled?: boolean`。
- `apps/web/src/store/usePlannerStore.ts`：`PlannerState` 新增 `amapEnabled`；`updateRuntimeStatus` 同步该字段；默认数据来源标签升级为 `V4 后端`。
- `apps/web/src/services/api.ts`：`normalizeBackendResponse` 根据 `aiEnabled / amapEnabled` 推导 `dataSourceLabel`（真实 AI + 高德 / 高德地图 / AI 生成 / 后端 Mock）。
- `apps/web/src/components/AppHeader.vue`：版本签升级为五种状态：`V2.1 Frontend Mock / V4 AI + Amap / V4 Amap / V4 AI / V3 Backend Mock / Backend Failed → Frontend Mock`。
- `apps/web/src/components/PlaceRecommendation.vue`：候选地点页顶部说明按 V4 四种模式展示。
- `apps/web/src/components/PlaceCard.vue`：`source = "Mock数据"` 仅在「都没有 Key」时才映射为「后端 Mock」；其余直接展示后端真实标签（如「高德地图」「AI + 高德」）。
- `apps/web/src/components/PasteGuidePanel.vue`：粘贴攻略面板说明按 V4 模式展示「V4 AI 提取 / V4 AI + 高德 提取 / V4 后端规则 + 高德 提取 / V3 后端 Mock 提取」。
- `apps/web/src/components/ItineraryView.vue`：行程页新增「行程来源」一行，区分 AI / 高德排序 / Mock。
- `.env.example`、`apps/api/.env.example`：新增 V4 推荐变量 `AI_PROVIDER / AI_BASE_URL / AI_MODEL / AI_API_KEY / AMAP_KEY` 占位。
- `README.md`、`docs/DEPLOYMENT.md`、`AGENTS.md`：更新版本号 V4，记录四种运行模式、`/api/debug/config` 验证方式、Render 推荐环境变量、未配置 Key 时的降级行为。

### AI 接入方式

- 协议：OpenAI-compatible `POST {AI_BASE_URL}/chat/completions`，`response_format={"type":"json_object"}`。
- Key 仅从 `AI_API_KEY` 环境变量读取，不写入代码、不打印、不在 `/api/debug/config` 返回。
- 所有 `httpx.AsyncClient` 请求带 timeout（默认 45s），异常时返回 `(None, warning)` 由 `PlannerService` 降级。
- AI 输出严格按 JSON 解析，含 ```json ... ``` 围栏的也能 parse；解析失败时单条丢弃，不会让前端崩。

### 高德地图接入方式

- 仅使用文档化的高德 Web 服务 `https://restapi.amap.com/v3/place/text`，超时 12s。
- Key 仅从 `AMAP_KEY` 环境变量读取，不写入代码。
- 前端不会直接请求高德接口，所有调用都经过后端，避免 Key 暴露。
- 失败 / 非 1 状态码 / JSON 解析失败时返回空列表，由 `PlannerService` 走规则关键词或 Mock 降级。

### 降级策略

- AI 失败：返回 `dataSourceLabel="后端 Mock"`，warning 说明降级原因；不抛堆栈给前端。
- 高德返回空：尝试规则关键词；仍失败则走 `mock_places`。
- AI + 高德都启用但 AI 注释失败：使用模板文案 + 真 POI，`dataSourceLabel="AI + 高德"`。
- AI + 高德都未配置：保留 V3 后端 Mock 行为，返回「后端已连接成功，但未配置 AI_API_KEY 与 AMAP_KEY，当前使用后端 Mock 数据」。

### 测试结果

- `python -m py_compile app/main.py app/config.py app/services/ai_client.py app/services/amap_client.py app/services/planner_service.py app/ai_client.py app/models.py`：通过。
- `python -m compileall app`：通过。
- `npm.cmd run typecheck`：通过。
- `npm.cmd run build`：通过（dist/index 95.41 kB / gzip 42.39 kB）。
- 本地 `uvicorn` 启动验证未执行：当前 `apps/api/.venv` 中缺少 `python-dotenv` 等依赖，且沙箱无法稳定 `pip install`；建议在 Render 重新部署后通过 `/api/health` 与 `/api/debug/config` 验证运行模式。

### 未完成内容

- 高德地理编码 (geocode)、路径规划 (direction) 暂未接入，仅做了 POI 文本搜索；行程顺序基于 POI 经纬度做最近邻排序，未做真实驾车 / 步行路径。
- AI 关键词生成 + AI 注释会发起 2 次 AI 请求，未做缓存，频繁请求会增加成本，后续可考虑短时缓存或合并 prompt。
- `app/ai_client.py` 仅保留为兼容层，下个迭代可视情况删除。

## 2026-05-19 V3.0.3 Backend Mock Source Label Hotfix

### 修改

- `apps/web/src/services/api.ts`：明确区分三种状态：纯前端 Mock、后端请求成功但返回后端 Mock、后端请求失败后降级为前端 Mock。只要后端返回 2xx，就不再提示“后端请求失败”。
- `apps/web/src/store/usePlannerStore.ts`：新增运行状态字段，记录后端是否连接成功、AI 是否启用、当前数据来源标签。
- `apps/web/src/components/AppHeader.vue`：根据运行模式显示 `V2.1 Mock`、`V3 Backend` 或 `V3 Backend Mock`。
- `apps/web/src/components/PlaceRecommendation.vue`：候选地点页顶部来源说明改为按模式显示，避免 V3 后端已连接时仍显示“V2.1 演示数据”。
- `apps/web/src/components/PlaceCard.vue`：地点卡片来源标签可区分“前端 Mock”和“后端 Mock”。
- `apps/web/src/components/PasteGuidePanel.vue`、`apps/web/src/components/StartPage.vue`、`apps/web/src/data/questions.ts`、`apps/web/src/components/ItineraryView.vue`：调整 V2.1 固定文案或同步运行状态，避免后端模式下误导用户。
- `apps/web/src/types.ts`：为 API envelope 增加可选的 `dataSourceLabel`、`aiEnabled`、`backendMode` 元数据，并允许地点来源显示后端 Mock。
- `apps/api/app/models.py`、`apps/api/app/main.py`：后端 Mock 响应增加 `dataSourceLabel="后端 Mock"`、`aiEnabled=false`、`backendMode=true`，并将未配置 `AI_API_KEY` 的 warning 改为“后端已连接成功，但未配置 AI_API_KEY，当前使用后端 Mock 数据”。
- `README.md`、`docs/DEPLOYMENT.md`、`AGENTS.md`：补充 V3 已实现 Vercel 前端请求 Render 后端、CORS 验证方式、Network 里 `/api/places/recommend` 返回 200 的判断方式，以及真实 AI / 地图 API 留到 V4。

### 修复原因

- CORS 已修复且 Vercel 前端可以成功请求 Render 后端，但页面仍显示“V2.1 演示数据”“地点推荐来自内置 Mock 数据”“未配置 AI_API_KEY，已使用 mock 候选地点”和“Mock数据”标签，容易让用户误以为前端没有请求后端。
- 本次只修复状态判断、数据来源标签和文案，不接入真实 AI API，不接入高德地图 API，不新增真实 Key，不改变部署架构。

### 验证方式

- 在 `apps/api` 运行 `python -m py_compile app/main.py`。
- 在 `apps/api` 运行 `python -m compileall app`。
- 在 `apps/web` 运行 `npm.cmd run typecheck`。
- 在 `apps/web` 运行 `npm.cmd run build`。

## 2026-05-19 V3.0.2 CORS fallback hotfix

### 修改

- `apps/api/app/main.py`：保留 `ALLOWED_ORIGINS` 环境变量读取逻辑，并将未配置时的默认允许来源扩展为本地 Vite 地址和线上 Vercel 前端 `https://travel-ai-planner-lake.vercel.app`，避免 Render 环境变量未生效时线上前端仍无法跨域访问后端。
- `apps/api/app/main.py`：继续支持 `ALLOWED_ORIGINS="*"` 时使用 `allow_origins=["*"]` 且 `allow_credentials=False`；逗号分隔域名会自动去掉空格、忽略空值，并保持 `allow_credentials=True`。
- `apps/api/app/main.py`：增强 `GET /api/debug/cors`，新增返回 `envConfigured`，用于判断后端是否实际读取到了 `ALLOWED_ORIGINS`，不输出真实 API Key 或其他敏感配置。
- `docs/DEPLOYMENT.md`：补充 Render 后端 CORS 排查说明、生产环境推荐配置、临时 `ALLOWED_ORIGINS=*` 排查方式，以及修改 Render 环境变量后必须重新部署后端的提醒。

### 修复原因

- 线上 Vercel 前端 `https://travel-ai-planner-lake.vercel.app` 已请求到 Render 后端 `https://travel-ai-planner-api.onrender.com/api/places/recommend`，但浏览器报错 `No 'Access-Control-Allow-Origin' header is present on the requested resource`。
- 当前 `/api/debug/cors` 仍只返回 localhost，说明 Render 的 `ALLOWED_ORIGINS` 可能未配置、未重新部署或未被进程读取；本次增加安全 fallback，保证未设置环境变量时也包含线上 Vercel 前端来源。

### 验证方式

- 在 `apps/api` 运行 `python -m py_compile app/main.py`。
- 在 `apps/api` 运行 `python -m compileall app`。
- 在 `apps/web` 运行 `npm.cmd run typecheck`。
- 在 `apps/web` 运行 `npm.cmd run build`。

## 2026-05-18 V3.0.1 CORS Hotfix

### 修改

- `apps/api/app/main.py`：调整 `ALLOWED_ORIGINS` 解析逻辑，支持逗号分隔域名、自动去掉前后空格并忽略空值；当配置包含 `*` 时固定使用 `allow_origins=["*"]` 且 `allow_credentials=False`；FastAPI app 创建后立即注册 `CORSMiddleware`，保留 `allow_methods=["*"]` 和 `allow_headers=["*"]`，确保线上 Vercel 到 Render 的 `OPTIONS` 预检请求能返回 CORS 头。
- `apps/api/app/main.py`：新增 `GET /api/debug/cors`，仅返回当前 `allowedOrigins` 和 `allowCredentials`，方便排查 Render 环境变量是否生效，不返回 API Key 或敏感配置。
- `docs/DEPLOYMENT.md`：补充 V3.0.1 CORS 配置规则、`ALLOWED_ORIGINS=*` 的临时排查行为，以及 `/api/debug/cors` 验证方式。

### 修复原因

- Render 后端被 Vercel 前端调用时，浏览器报错 `No 'Access-Control-Allow-Origin' header is present on the requested resource`，说明预检请求未拿到正确 CORS 响应头。
- 本次只做 V3 后端跨域 hotfix，不新增前端业务功能，不提交真实 API Key。

### 验证方式

- 在 `apps/api` 运行 `python -m py_compile app/main.py`。
- 在 `apps/api` 运行 `python -m compileall app`。
- 如本地前端依赖可用，在 `apps/web` 运行 `npm.cmd run typecheck` 和 `npm.cmd run build`，确认本次后端修复未影响前端构建。
- Render 重新部署后访问 `/api/debug/cors`，确认 `allowedOrigins` 包含 `https://travel-ai-planner-lake.vercel.app`，再从 Vercel 前端完整测试推荐、攻略提取和行程生成接口。

## 2026-05-14 V1 MVP

从空目录创建“AI 出行旅游计划助手”V1 MVP。

### 新增

- `.gitignore`：忽略 `node_modules`、`dist`、`.env`、虚拟环境、缓存等本地生成文件。
- `.env.example`：列出 AI、高德地图和前端代理相关环境变量，不包含真实 Key。
- `apps/web`：创建 Vue 3 + Vite + TypeScript 前端。
- `apps/api`：创建 FastAPI 后端骨架。
- `docs/CHANGE_RECORD.md`、`README.md`、`AGENTS.md`：建立项目文档和协作规则。

### 检查

- 已运行 `python -m compileall apps/api/app`，后端源码编译通过。

## 2026-05-14 V1 收尾修复

### 修改

- `apps/web/vite.config.ts`：增加 `resolve.alias`，将 `@` 指向 `apps/web/src`；增加 `envDir`，从项目根目录读取 `.env`。
- `apps/web/src/services/api.ts`：增加 `VITE_USE_MOCK` 判断；开启 Mock 时不请求后端，请求后端失败时自动降级为前端 Mock。
- `apps/web/src/services/mockPlanner.ts`：新增前端 Mock 推荐地点、攻略文本提取和行程生成方法。
- `apps/web/src/vite-env.d.ts`：增加 `VITE_USE_MOCK` 类型声明。
- `.env.example`：增加 `VITE_USE_MOCK=true`。
- `README.md`：说明 V1 默认可只跑前端 Mock、测试 FastAPI 的配置方式，以及 Windows 下建议使用 `npm.cmd`。
- `apps/api/app/__pycache__`：清理 Python 缓存目录。

### 检查

- 已确认 `apps/api/app/__pycache__` 不存在。

## 2026-05-14 V2 Web Deploy Ready

### 修改

- `apps/web/vercel.json`：新增 Vercel SPA fallback，支持刷新或后续路由扩展。
- `apps/web/public/_redirects`：新增 Cloudflare Pages SPA fallback。
- `apps/web/.env.production.example`：新增生产环境示例，默认 `VITE_USE_MOCK=true`。
- `apps/web/vite.config.ts`：明确 `build.outDir` 为 `dist`；保留 `@` alias、根目录 `envDir` 和根路径部署默认 `base`；使用 `dirname + resolve` 修复 Windows 下 Vite build 的 HTML 路径问题。
- `apps/web/src/styles.css`：轻量优化移动端布局，避免窄屏横向溢出、按钮过挤和卡片过宽。
- `.env.example`：整理环境变量说明，确认 `VITE_USE_MOCK=true`、`VITE_API_BASE_URL=`、`VITE_AMAP_KEY=`。
- `README.md`：更新为 V2 Web Deploy Ready，增加 Vercel / Cloudflare Pages 部署入口和本地运行说明。
- `docs/DEPLOYMENT.md`：新增 V2 部署文档。
- `AGENTS.md`：补充部署配置不要写死密钥、V2 不引入真实后端依赖、部署修改必须更新文档的规则。

### 检查

- 已运行 `npm.cmd run typecheck`，通过。
- 已运行 `npm.cmd run build`，通过。

## 2026-05-15 V2.1 Feedback Improvement

### 修改

- `docs/USER_FEEDBACK.md`：整理 V2 用户试用反馈，保留原始反馈含义，并记录 V2.1 处理范围与后续版本方向。
- `apps/web/src/services/mockPlanner.ts`：优化前端 Mock 推荐数据，增加城市专属 Mock 数据；优化攻略文本演示提取逻辑。
- `apps/web/src/services/api.ts`：整理 Mock fallback 提示，明确当前为 V2.1 前端 Mock 演示数据。
- `apps/web/src/types.ts`：整理 Place、TravelPreference、Itinerary 等类型中的中文枚举文案。
- `apps/web/src/data/questions.ts`：修复问答文案，给预算低 / 中 / 高增加解释。
- `apps/web/src/components/PlaceRecommendation.vue`：在候选地点区域上方增加数据来源说明。
- `apps/web/src/components/PlaceCard.vue`：将类型、来源、停留时间、适合场景压缩为标签；地址和避坑提醒改为“详情 / 收起”。
- `apps/web/src/components/PasteGuidePanel.vue`：优化攻略文本粘贴说明、示例 placeholder 和短文本提示。
- `apps/web/src/components/GuidedChat.vue`：展示预算选项解释，修复页面中文文案。
- `apps/web/src/components/AppHeader.vue`、`StartPage.vue`、`PreferenceSummary.vue`、`ItineraryView.vue`、`MapView.vue`：修复页面中文文案，保持 V1/V2 功能不变。
- `apps/web/src/styles.css`：新增数据来源说明样式、紧凑地点卡片样式、标签样式和手机端按钮/卡片优化。
- `README.md`：更新为 V2.1 Feedback Improvement，记录本轮优化和天气、预算量化后续计划。
- `AGENTS.md`：补充用户反馈修改、Mock 数据来源和密钥相关规则。

### 新增或优化的城市专属 Mock 数据

- 张家界
- 重庆
- 长沙
- 上海
- 北京
- 杭州
- 南京
- 成都
- 西安
- 广州
- 厦门

每个城市提供 8-12 个适合旅行规划演示的地点，覆盖景点、餐厅、商圈、博物馆、夜市、自然风景、交通点或其他类型。其他城市继续使用通用 Mock fallback。

### 为什么修改

- 回应用户对推荐真实感、数据来源、攻略文本提取、手机端浏览长度、天气和预算表达的反馈。
- 在不接入真实 AI、真实地图、真实天气 API 的前提下，提高 Mock 演示版的可理解性和手机端体验。

- 已验证

- 已运行 `npm.cmd run typecheck`，通过。
- 已运行 `npm.cmd run build`，通过。
- 已清理构建产物 `apps/web/dist`。
- 已确认没有 `__pycache__`。
- 已检查未提交真实 API Key；仅存在 `.env.example` / 文档中的空变量名示例。
- 线上或本地保持 `VITE_USE_MOCK=true`，完整测试首页、问答、候选地点、攻略文本提取、生成行程、地图降级清单和刷新保存。

### 是否影响 V1/V2 原有功能

- 不影响 V1 本地 Mock 流程。
- 不破坏 V2 Vercel / Cloudflare Pages 静态部署配置。
- 不改变 FastAPI 后端骨架。
- 不接入真实 AI、真实高德地图、真实天气、登录、数据库、PWA、Capacitor 或 PDF 导出。

## 2026-05-16 V3 Backend Deploy Ready

### 修改

- `apps/api/app/main.py`：将 FastAPI 版本标记更新为 `v3`；新增 `GET /` 根路径接口；新增标准健康检查 `GET /health`；保留并更新 `GET /api/health`；增加 `ALLOWED_ORIGINS` 环境变量解析，默认允许本地 Vite 前端来源。
- `apps/web/src/services/api.ts`：新增 `VITE_API_BASE_URL` 后端根地址拼接逻辑；`VITE_USE_MOCK=true` 时继续使用前端 Mock；`VITE_USE_MOCK=false` 时请求后端 Mock API；后端地址缺失或请求失败时回退到前端 Mock 并返回页面 warning。
- `apps/web/vite.config.ts`：明确 Vite root 为 `apps/web`，修复 Windows 下生产构建时 `index.html` 被识别为绝对输出路径的问题。
- `.env.example`：补充 V3 前后端联调变量、`ALLOWED_ORIGINS` 示例和 V3 仍不提交真实 Key 的说明。
- `apps/web/.env.production.example`：调整为 V3 线上后端模式示例，使用 `VITE_USE_MOCK=false` 和占位后端地址。
- `apps/api/.env.example`：新增后端 CORS 环境变量示例。
- `docs/DEPLOYMENT.md`：重写为 V3 部署指南，包含 V2 前端静态部署回顾、FastAPI 本地运行、CORS、Render、Railway、Vercel 后端模式切换、验证步骤和常见问题。
- `README.md`：更新为 `V3 Backend Deploy Ready`，补充 V1/V2/V2.1/V3 版本说明、本地前后端联调、线上前后端部署方式和后续 V4/V5 计划。
- `AGENTS.md`：补充 V3 后端部署文档同步、环境变量示例与真实密钥禁止提交、Mock 来源说明规则。

### 新增或确认的后端接口

- `GET /`：返回 `{ "message": "Travel AI Planner API", "version": "v3" }`。
- `GET /health`：返回 `{ "status": "ok", "service": "travel-ai-planner-api", "version": "v3" }`。
- `GET /api/health`：返回健康检查结果，并附带 `aiEnabled`。
- `POST /api/places/recommend`：继续返回 Mock 候选地点或 AI 降级 Mock 数据。
- `POST /api/places/extract`：继续返回用户粘贴文本的 Mock 提取结果。
- `POST /api/itinerary/generate`：继续返回 Mock 行程。

### 部署说明

- Render 推荐 Root Directory 为 `apps/api`，Build Command 为 `pip install -r requirements.txt`，Start Command 为 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
- Railway 推荐同样使用 `apps/api` 作为服务根目录，并检查 Start Command 是否使用 `$PORT`。
- Vercel 前端切换到后端模式时设置 `VITE_USE_MOCK=false` 和 `VITE_API_BASE_URL=<Render 或 Railway 后端地址>`，修改环境变量后需要重新部署前端。
- 后端 `ALLOWED_ORIGINS` 需要加入线上 Vercel 前端地址，例如 `https://travel-ai-planner-lake.vercel.app`。

### 检查结果

- 已运行 `python -m py_compile app/main.py`，通过。
- 已运行 `python -m compileall app`，通过。
- 已运行 `npm.cmd run typecheck`，通过。
- 已运行 `npm.cmd run build`，通过；同时修复 `apps/web/vite.config.ts` 中 Windows 下 Vite build 会把 `index.html` 识别为绝对输出路径的问题。
- 已尝试在 `apps/api/.venv` 安装 `requirements.txt` 以启动后端运行验证；当前沙箱网络阻止 pip 访问包索引，自动提权审批超时，因此未能完成真实 `uvicorn` 启动验证。
