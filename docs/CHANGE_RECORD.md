# Change Record

## 2026-05-20 V4.1.2 AI stability/token hotfix

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
