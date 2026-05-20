# V4.2 部署指南

## V4.2 稳定体验版前端验证

本次修改主要影响 Vercel 前端代码，不修改任何 Key 或环境变量。部署后需要重新部署 Vercel 前端；Render 后端如果仍是 V4.1.2，可不因本轮前端改动单独重部署。

后端健康与 AI 调试验证：
1. 打开 `https://travel-ai-planner-api.onrender.com/api/health`，确认 `aiEnabled=true`、`amapEnabled=true`，并查看 `dataMode` 是否为“高德地图 + AI”。
2. 打开 `https://travel-ai-planner-api.onrender.com/api/debug/ai`，确认只返回非敏感配置状态，`probeEnabled=false`，不会请求真实 DeepSeek。
3. 需要真实连通性探测时，再打开 `https://travel-ai-planner-api.onrender.com/api/debug/ai?probe=1`，确认 `ok=true`、`parsedJsonOk=true`。这个地址会发起一次极小 AI 请求，不要反复刷新。

前端页面验证：
1. 在 Vercel 前端完整走问答流程，进入候选地点页。
2. 如果候选地点 `dataSourceLabel="高德地图 + 后端模板"`，页面应显示“候选地点来自高德 POI，AI 补充文案失败，已使用规则文案。”，Header 应显示 `Travel AI Planner · V4.2 AI Fallback` 或候选阶段对应状态。
3. 选择地点后点击“生成行程”。如果行程接口返回 `dataSourceLabel="高德地图 + AI"`，行程页 Header 应显示 `Travel AI Planner · V4.2 AI + Amap`，不应继续显示候选阶段的 fallback。
4. 行程页应显示“行程来源：V4.2 高德地图 + AI（按经纬度排序后由 AI 生成行程文案）”。
5. 刷新页面、返回候选地点页再点“生成行程”，如果偏好和已选地点未变，前端应读取 localStorage 缓存，不自动重新请求 `/api/itinerary/generate`。
6. 只有点击行程页“重新生成行程”时，Network 中才应再次出现 `POST /api/itinerary/generate`，并在成功后覆盖缓存。
7. 点击“清空当前计划”后，对应行程缓存会同步清理；重新选择并生成时会按新的 key 请求后端。

Network 检查重点：
- `POST /api/places/recommend`：进入候选地点页或点击“重新推荐地点”时请求。
- `POST /api/itinerary/generate`：首次生成或点击“重新生成行程”时请求。
- 刷新页面、切换页面回来、重复进入行程页时，不应自动重复请求 `/api/itinerary/generate`。

## V4.1.2 AI 稳定性与省 token hotfix

本次修改只影响 Render 后端代码；修改后需要重新部署 Render 后端。Vercel 前端环境变量、`AI_MODEL`、DeepSeek Key 与高德 Key 不需要修改。

`/api/debug/ai` 行为已调整：
- 默认访问 `https://travel-ai-planner-api.onrender.com/api/debug/ai` 只返回非敏感配置状态，不发起真实 AI 请求，不消耗 DeepSeek token。
- 需要真实连通性探测时，访问 `https://travel-ai-planner-api.onrender.com/api/debug/ai?probe=1`。
- probe 请求已极小化，`maxTokens=32`，只要求返回 `{"ok": true}`。
- debug 接口不会返回任何 API Key；`rawPreview` 仅保留短预览并脱敏。

行程生成稳定性调整：
- `/api/itinerary/generate` 继续以高德 POI 作为地点来源。
- 发送给 DeepSeek 的地点字段已精简为 `id/name/type/address/reason/estimatedTime/warning`，最多 8 个已选地点。
- AI 返回 Markdown fence、JSON 前后解释文字、JSON object 或 array 时，后端会尽量提取并解析。
- 若仍降级为后端模板，`POST /api/itinerary/generate` 的 envelope 会包含安全诊断字段：`aiErrorType`、`aiErrorMessage`、`aiRawPreview`、`aiChoicesContentFound`、`aiParsedJsonOk`。这些字段用于判断是否成功读取 `choices[0].message.content`、是否 JSON 解析失败、是否 schema 映射失败；不会返回任何 Key 或完整 AI 响应。
- AI 仍失败时保留原有后端模板 fallback，不影响主流程。

## V4.1.1 AI 行程生成 timeout/token hotfix

本次修复只影响 Render 后端代码。前端 Vercel 环境变量、高德 Key、DeepSeek Key 和 `AI_MODEL` 不需要改动。

后端 `/api/itinerary/generate` 已减少传给 DeepSeek 的内容：
- 不再传完整 `Place` 对象。
- 只传已选地点的行程必要字段：`id/name/type/reason/suitableFor/estimatedTime/warning/lat/lng`。
- 地点较多时最多传前 8 个已排序地点。
- 行程生成 AI 请求限制 `max_tokens=1200`，`temperature=0.3`，并要求只输出 JSON。

AI 调用失败时仍保留原降级策略：
- AI 成功：`dataSourceLabel="高德地图 + AI"`。
- AI 超时、返回格式异常或其他失败：`dataSourceLabel="高德地图 + 后端模板"`，地点仍来自高德 POI。
- `/api/debug/ai` 会返回非敏感诊断字段，包括 `timeoutSeconds`、`maxTokens`、`errorType`、`errorMessage`，不会返回任何 API Key。

部署后建议验证：
1. 打开 `https://travel-ai-planner-api.onrender.com/api/health`，确认 `aiEnabled=true`、`amapEnabled=true`、`dataMode="高德地图 + AI"`。
2. 打开 `https://travel-ai-planner-api.onrender.com/api/debug/ai`，确认 `ok=true`、`parsedJsonOk=true`，并查看 `timeoutSeconds` / `maxTokens`。
3. 在 Vercel 前端完整走一遍问答、推荐地点、选择 6-8 个地点、生成行程。
4. 在浏览器 Network 中确认 `POST /api/itinerary/generate` 返回 200，并观察页面 Header 是否从 `V4.1 AI Fallback` 恢复为 `V4.1 AI + Amap`。

## V2 前端静态部署回顾

V2 / V2.1 的线上前端部署在 Vercel，`apps/web` 可以作为纯静态站点运行。默认环境变量为：

```env
VITE_USE_MOCK=true
VITE_API_BASE_URL=
```

这种模式不会请求 FastAPI 后端，适合继续演示 V2.1 的前端 Mock 流程。Vercel 核心配置：

- Root Directory: `apps/web`
- Framework Preset: `Vite`
- Install Command: `npm install`
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variables: `VITE_USE_MOCK=true`

Cloudflare Pages 仍可按 V2 方式部署：

- Root directory: `apps/web`
- Build command: `npm run build`
- Build output directory: `dist`
- Environment variables: `VITE_USE_MOCK=true`

## V3 后端部署目标

V3 把项目升级为前后端分离部署版：

- 前端仍可用 `VITE_USE_MOCK=true` 保持 V2.1 前端 Mock 演示。
- 前端设置 `VITE_USE_MOCK=false` 后，会请求 `VITE_API_BASE_URL` 指向的 FastAPI 后端。
- FastAPI 后端部署到 Render 或 Railway；当前 Render 后端已可被 Vercel 前端请求。
- 如果后端未配置 `AI_API_KEY`，接口会返回后端 Mock 数据，前端会显示“V3 Backend Mock”或“后端 Mock”。
- V3 不接真实 AI API、真实地图 API、真实天气 API、数据库或登录系统。

## FastAPI 本地运行

Windows:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

非 Windows:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：

```text
http://127.0.0.1:8000/health
```

应返回：

```json
{
  "status": "ok",
  "service": "travel-ai-planner-api",
  "version": "v3"
}
```

## CORS 配置

后端通过 `ALLOWED_ORIGINS` 配置允许访问的前端来源，支持逗号分隔：

```env
ALLOWED_ORIGINS=http://localhost:5173,https://travel-ai-planner-lake.vercel.app
```

未配置时，默认允许：

```text
http://localhost:5173
http://127.0.0.1:5173
https://travel-ai-planner-lake.vercel.app
```

生产环境推荐明确配置：

```env
ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app
```

临时排查跨域问题时可以使用：

```env
ALLOWED_ORIGINS=*
```

生产环境不要长期使用 `ALLOWED_ORIGINS=*`。如果临时排查跨域问题使用了 `*`，排查完成后应改回明确的 Vercel 前端域名。

V3.0.2 起，后端会在 FastAPI app 创建后立即注册 `CORSMiddleware`：

- `ALLOWED_ORIGINS="*"` 时使用 `allow_origins=["*"]`，并自动设置 `allow_credentials=False`。
- `ALLOWED_ORIGINS` 为逗号分隔域名时，会去掉每一项前后空格并忽略空值。
- `allow_methods=["*"]`、`allow_headers=["*"]`，确保浏览器 `OPTIONS` 预检请求能返回 CORS 头。
- 可访问 `GET /api/debug/cors` 查看当前后端读取到的 `allowedOrigins`、`allowCredentials` 和 `envConfigured`，该接口不返回 API Key 或其他敏感配置。

## Render 部署步骤

推荐配置：

- Service Type: `Web Service`
- Root Directory: `apps/api`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables（V4 推荐）：

```env
ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app
AI_PROVIDER=openai-compatible
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4.1-mini
AI_API_KEY=不要写入仓库，只在 Render 后台配置
AMAP_KEY=不要写入仓库，只在 Render 后台配置
```

`AI_API_KEY` / `AMAP_KEY` 任意一个未配置，对应能力会自动降级为后端 Mock，并在响应 envelope 的 `warning` 中说明降级原因；前端不会因此白屏。

操作步骤：

1. 登录 Render。
2. New Web Service，导入 GitHub 仓库 `Travel-AI-Planner`。
3. 设置 Root Directory 为 `apps/api`。
4. 设置 Build Command 为 `pip install -r requirements.txt`。
5. 设置 Start Command 为 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
6. 添加 `ALLOWED_ORIGINS`，值为 Vercel 前端地址。
7. 如果要启用真实 AI / 高德，添加 `AI_API_KEY` 和 `AMAP_KEY`（其它 AI_* 变量按需配置）。
8. 部署完成后打开 `https://your-api-service.onrender.com/health` 验证。
9. 访问 `/api/debug/config`，确认 `aiEnabled` / `amapEnabled` / `dataMode` 与预期一致。该接口只暴露非敏感信息，不返回任何 Key。

修改 Render 环境变量后必须重新部署后端，新的 `ALLOWED_ORIGINS` 才会被运行中的 FastAPI 进程读取。

如 Render 需要指定 Python 版本，可在 Render 设置中选择 Python 运行时版本；当前项目暂不强制新增 `runtime.txt`。

## Render 后端 CORS 排查

当前线上前端为：

```text
https://travel-ai-planner-lake.vercel.app
```

当前 Render 后端为：

```text
https://travel-ai-planner-api.onrender.com
```

如果浏览器控制台出现：

```text
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

按以下顺序排查：

1. 打开 `https://travel-ai-planner-api.onrender.com/api/debug/cors`。
2. 确认 `allowedOrigins` 包含 `https://travel-ai-planner-lake.vercel.app`。
3. 确认 `envConfigured` 是否为 `true`。如果为 `false`，说明 Render 当前进程没有读到 `ALLOWED_ORIGINS`，会使用代码内置 fallback。
4. 生产环境推荐在 Render 设置 `ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app`。
5. 临时排查可设置 `ALLOWED_ORIGINS=*`，此时 `allowCredentials` 应返回 `false`。
6. 每次修改 Render 环境变量后，都需要重新部署后端，再重新访问 `/api/debug/cors` 验证。

## Railway 部署步骤

推荐配置：

- 从 GitHub 导入 `Travel-AI-Planner` 仓库。
- 服务根目录设置为 `apps/api`。
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables:

```env
ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app
```

操作步骤：

1. 登录 Railway。
2. New Project，从 GitHub 导入仓库。
3. 选择或设置服务根目录为 `apps/api`。
4. 如果 Railway 自动识别 Python 项目，仍要检查 Start Command 是否为 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
5. 添加 `ALLOWED_ORIGINS`，值为 Vercel 前端地址。
6. 部署完成后打开后端域名的 `/health` 验证。

## Vercel 前端切换到后端模式

在 Vercel 的 `apps/web` 项目中设置：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=https://your-api-service.onrender.com
```

说明：

- `VITE_API_BASE_URL` 不要以 `/api` 结尾，直接填写后端根地址。
- 地址末尾带不带 `/` 都可以，前端会自动去掉末尾斜杠。
- 修改 Vercel 环境变量后必须重新部署前端，新的构建才会生效。
- 如果后端请求成功但未配置 `AI_API_KEY`，页面会显示后端已连接，并使用后端 Mock 数据。
- 只有后端请求失败、CORS 失败、接口返回非 2xx 或网络失败时，页面才会显示失败 warning，并回退到前端 Mock 数据，避免白屏。

## 数据来源显示规则（V4.1）

前端 Header 与各页面按本次请求 envelope 中的 `dataSourceLabel` 为权威，后端能力（`aiEnabled / amapEnabled`）作为兜底：

| 场景 | dataSourceLabel | Header 版本签 |
| --- | --- | --- |
| 前端 Mock | （前端自填） | `V2.1 Frontend Mock` |
| 后端请求失败 | （前端自填） | `Backend Failed → Frontend Mock` |
| AI + 高德 都配置且 AI 成功 | `高德地图 + AI` | `V4.1 AI + Amap` |
| AI + 高德 都配置但 AI 失败 | `高德地图 + 后端模板` | `V4.1 AI Fallback`（页面顶部红条：AI 请求失败，已降级为后端模板，地点仍来自高德 POI） |
| 仅高德 | `高德地图` | `V4 Amap` |
| 仅 AI | `AI 生成` | `V4.1 AI` |
| 都没配置 | `后端 Mock` | `V3 Backend Mock` |

`/api/debug/config` 用来判断当前后端能力（`aiEnabled / amapEnabled / dataMode`）；具体一次请求实际走的路径以 envelope.dataSourceLabel 为准。`/api/debug/config` 不返回任何 `*_KEY` 字段。

### V4.3.1 候选页状态映射

候选页状态完全由 `placeSourceLabel` 决定，行程页由 `itinerarySourceLabel` 决定，互不影响。

| 候选页 dataSourceLabel | 候选页 Header | 候选页提示 |
| --- | --- | --- |
| `高德地图 + AI` | `V4.3 AI + Amap` | 高德 POI + AI 文案 |
| `高德地图 + 规则文案` | `V4.3 Amap + Rule Copy` | 候选地点来自高德 POI 真实数据；AI 文案增强未生效，已用规则文案补充（无红色横条） |
| `高德地图 + 后端模板` | `V4.3 AI Fallback` | 行程级 AI Fallback 语义，候选页一般不再产生 |
| `高德地图` | `V4.3 Amap` | 仅高德，无 AI |
| `AI 生成` | `V4.3 AI` | 仅 AI |
| `后端 Mock` | `V4.3 Backend Mock` | 都没配置 |

部署后建议验证：

1. Render Manual Deploy 后端，等到状态为 Live。
2. 重新打开 Vercel 前端，进入候选页，根据当前 AI 文案是否成功，Header 应显示 `V4.3 AI + Amap` 或 `V4.3 Amap + Rule Copy`，不再出现 `V4.3 AI Fallback`，也不再出现红色「AI 请求失败」横条。
3. 进入行程页：行程 AI 成功仍显示 `V4.3 AI + Amap + Weather`；若行程 AI 真的失败，Header 才会显示 `V4.3 AI Fallback (+ Weather)`。
4. `/api/debug/ai?probe=1`、`/api/debug/weather` 仍可用，无 Key 泄漏。

### /api/debug/weather 调试接口（V4.3）

天气服务复用已有 `AMAP_KEY`，无需新增环境变量。

- `GET https://travel-ai-planner-api.onrender.com/api/debug/weather`（默认 `city=杭州`）。
- 支持 `?city=城市名` 或 `?city=adcode`，例如 `?city=330100`。
- 成功示例 `status="ok"`，包含 `city / weather / temperature / humidity / winddirection / windpower / reporttime / forecast`。
- `AMAP_KEY` 未配置返回 `status="disabled"`。
- 高德调用失败返回 `status="error"` 并附 `reason`，不抛 500。
- 返回内容与服务端日志不会包含 `AMAP_KEY`。

行程生成接口 `/api/itinerary/generate` 现在 envelope 中会带 `weather` 字段；天气获取失败或目的地为空时为 `null`，主流程（地点推荐、行程生成、缓存）不受影响。前端 Header 在行程页且 `state.weather.status==='ok'` 时显示 `V4.3 ... + Weather`。

### /api/debug/ai 调试接口（V4.1）

当 `/api/debug/config` 显示 `aiEnabled=true` 但前端始终显示「AI 请求失败」时，访问 `GET https://travel-ai-planner-api.onrender.com/api/debug/ai`，后端会实际向 AI 端点发一次最小请求并返回脱敏诊断：

```json
{
  "aiConfigured": true,
  "aiProvider": "openai-compatible",
  "aiBaseUrl": "https://api.deepseek.com",
  "aiModel": "deepseek-chat",
  "requestUrl": "https://api.deepseek.com/chat/completions",
  "ok": true,
  "statusCode": 200,
  "errorType": null,
  "errorMessage": null,
  "rawPreview": "{\"ok\": true}",
  "parsedJsonOk": true
}
```

- 该接口不返回任何 `*_KEY`；`rawPreview` 与日志均经过脱敏（`Bearer ***` / `sk-***`）。
- 失败时按 `errorType` 排查：
  - **`http_error` + `statusCode=401`**：`AI_API_KEY` 无效 / 过期 / 没绑账户额度。检查 Render 后台 Key 是否完整、是否选择了正确的 provider。
  - **`http_error` + `statusCode=402`**：DeepSeek 账户余额不足。前往 DeepSeek 控制台充值后即可，无需改代码。
  - **`http_error` + `statusCode=422 / 400`**：通常是模型名或 payload 字段不合法。看 `rawPreview` 是否包含 `model_not_found` / `invalid model`。例如 `deepseek-v4-flash` 不存在，请把 Render 的 `AI_MODEL` 改为 `deepseek-chat` 或 `deepseek-reasoner` 后 Manual Deploy。
  - **`empty_content`**：HTTP 200 但 `choices[0].message.content` 为空。常见原因是 `max_tokens` 太小、`temperature` 异常，或服务端把 `response_format=json_object` 与不合规 prompt 一起拒绝；可先把 `AI_MODEL` 换 `deepseek-chat` 重试。
  - **`request_error` / `timeout`**：网络问题，Render 与 DeepSeek 网络不通或区域被限。可换一个 OpenAI 兼容端点（如 Moonshot / 通义千问 OpenAI 兼容 URL）做对比。
- 该接口可以反复调用以做回归验证；建议修复后访问一次确认 `ok: true, parsedJsonOk: true`，再回到前端验证 Header 是否从 `V4.1 AI Fallback` 变为 `V4.1 AI + Amap`。

## 本地前后端联调

1. 启动后端：

```bash
cd apps/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. 在项目根目录 `.env` 设置：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_AMAP_KEY=
```

3. 启动前端：

```bash
cd apps/web
npm.cmd run dev
```

4. 打开 `http://localhost:5173`，完整测试问答、候选地点、攻略文本提取、行程生成和地图降级地点清单。

## 如何验证部署成功

1. 打开后端 `/health`，确认返回 `status: ok` 和 `version: v3`。
2. 在 Vercel 设置 `VITE_USE_MOCK=false`。
3. 在 Vercel 设置 `VITE_API_BASE_URL=<Render 或 Railway 后端地址>`。
4. 在后端设置 `ALLOWED_ORIGINS=<Vercel 前端地址>`。
5. 重新部署 Vercel 前端。
6. 打开 `https://travel-ai-planner-api.onrender.com/api/debug/cors`，确认 CORS 允许来源包含 `https://travel-ai-planner-lake.vercel.app`。
7. 打开线上前端，完整测试问答、推荐、攻略文本提取、行程生成。
8. 在浏览器 Network 中确认 `POST https://travel-ai-planner-api.onrender.com/api/places/recommend` 返回 `200`。返回 `200` 就表示前端确实请求到了后端。
9. 如果后端未配置 `AI_API_KEY`，页面应显示后端已连接但使用后端 Mock 数据；这不是请求失败。
10. 临时关闭或填错后端地址，确认页面会提示后端失败并回退到前端 Mock。

## 常见问题

### CORS 报错

确认后端 `ALLOWED_ORIGINS` 包含完整 Vercel 前端地址，例如：

```env
ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app
```

不要只写域名片段，也不要遗漏 `https://`。

Render 重新部署后，也可以访问：

```text
https://your-api-service.onrender.com/api/debug/cors
```

确认返回的 `allowedOrigins` 包含 Vercel 前端完整域名。如果临时设置为 `ALLOWED_ORIGINS=*`，返回的 `allowCredentials` 应为 `false`。

### 请求 404

确认 `VITE_API_BASE_URL` 是后端根地址，例如：

```env
VITE_API_BASE_URL=https://your-api-service.onrender.com
```

不要写成 `https://your-api-service.onrender.com/api`。

### 502 或后端未启动

检查 Render / Railway 的 Start Command 是否为：

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

同时查看平台日志，确认依赖安装完成且 `apps/api` 是服务根目录。

### Vercel 环境变量修改后没有生效

Vite 会在构建时注入 `VITE_*` 变量。修改 Vercel 环境变量后，需要重新部署前端。

### 后端地址末尾是否带斜杠

可以带也可以不带。前端会把 `VITE_API_BASE_URL` 末尾的 `/` 去掉，再拼接 `/api/...`。

### 本地能跑但线上不能跑

优先检查：

- Render / Railway Root Directory 是否为 `apps/api`。
- Start Command 是否使用 `$PORT`。
- 后端 `/health` 是否能打开。
- Vercel `VITE_API_BASE_URL` 是否指向线上后端。
- 后端 `ALLOWED_ORIGINS` 是否包含 Vercel 前端地址。
- Vercel 修改环境变量后是否重新部署。
