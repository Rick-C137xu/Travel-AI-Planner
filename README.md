# AI 出行旅游计划助手

当前版本：V4.1 AI 接入 + 失败降级语义对齐

这是一个网页端旅行规划 MVP。用户通过问答收集旅行需求，系统推荐候选地点，用户选择想去、备选或不想去，再生成每日行程，并在地图区域显示地点清单或地图降级视图。

## 版本说明

- V1：本地 Mock 流程可运行。
- V2：前端可部署到 Vercel / Cloudflare Pages，手机浏览器可直接体验。
- V2.1：根据用户反馈优化 Mock 推荐、数据来源说明、攻略文本演示提取和手机端候选地点卡片。
- V3：FastAPI 后端已完成 Render 部署联通验证，前端可通过 `VITE_USE_MOCK=false` 请求线上后端 API。
- V4：后端新增 AI 调用封装（OpenAI-compatible）与高德 Web 服务封装。配置了 `AI_API_KEY` 和 `AMAP_KEY` 后，推荐接口会返回真实 POI + AI 推荐文案；未配置时仍返回后端 Mock 数据。
- V4.1：AI 接入后的失败降级语义统一。AI 请求超时 / 出错 / JSON 解析失败时，POI 仍来自高德，文案/行程退回为后端模板，envelope 中 `dataSourceLabel="高德地图 + 后端模板"`，前端显示 `V4.1 AI Fallback` 并提示「AI 请求失败，已降级为后端模板，地点仍来自高德 POI」。

V4.1 运行模式以后端环境变量为准：

- `AI_API_KEY` + `AMAP_KEY` 都有 → `dataMode = "高德地图 + AI"`，高德返回真 POI，AI 补推荐文案/行程。
- 仅 `AMAP_KEY` → `dataMode = "高德地图"`，使用高德 POI，推荐文案为后端模板。
- 仅 `AI_API_KEY` → `dataMode = "AI 生成"`，AI 生成候选地点，warning 会说明未经过高德校验。
- 都没有 → `dataMode = "后端 Mock"`，返回后端 Mock 数据（与 V3 一致）。

具体某次请求的 `dataSourceLabel` 可能为：`高德地图 + AI` / `高德地图 + 后端模板` / `高德地图` / `AI 生成` / `后端 Mock`。`高德地图 + 后端模板` 表示 AI 请求失败而高德可用的降级状态。

可访问 `GET /api/debug/config` 查看当前 `aiEnabled / amapEnabled / dataMode`，该接口不返回任何 Key。

## 技术栈

- 前端：Vue 3 + Vite + TypeScript + 普通 CSS
- 后端：FastAPI + Python
- 地图：高德地图 JS API 可选；未配置 Key 时自动降级为地点清单
- 存储：浏览器 `localStorage`
- Mock：默认 `VITE_USE_MOCK=true`，前端不依赖后端也能完整运行

## 项目结构

```text
travel-ai-planner
├── apps
│   ├── web        # Vue 3 + Vite + TypeScript 前端
│   └── api        # FastAPI 后端
├── docs
│   ├── CHANGE_RECORD.md
│   ├── DEPLOYMENT.md
│   └── USER_FEEDBACK.md
├── README.md
├── AGENTS.md
└── .env.example
```

## 本地只跑前端 Mock

Windows:

```bash
cd apps/web
npm.cmd install
npm.cmd run dev
```

非 Windows:

```bash
cd apps/web
npm install
npm run dev
```

打开：

```text
http://localhost:5173
```

默认环境变量：

```env
VITE_USE_MOCK=true
VITE_API_BASE_URL=
VITE_AMAP_KEY=
```

## 本地前后端联调

启动后端：

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问健康检查：

```text
http://127.0.0.1:8000/health
```

在项目根目录 `.env` 设置：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_AMAP_KEY=
```

再启动前端：

```bash
cd apps/web
npm.cmd run dev
```

当 `VITE_USE_MOCK=false` 且后端请求失败时，页面会显示失败提示，并回退到前端 Mock 数据，避免白屏。

如果 `VITE_USE_MOCK=false` 且后端请求成功，但后端未配置 `AI_API_KEY`，页面会提示“后端已连接成功，但未配置 AI_API_KEY，当前使用后端 Mock 数据”。这不是请求失败，也不是前端 Mock。

## 后端接口

V4 后端接口：

- `GET /`：返回 API 名称和版本。
- `GET /health`：返回服务健康状态。
- `GET /api/health`：返回 `aiEnabled / amapEnabled / dataMode`。
- `GET /api/debug/cors`：返回当前 CORS 配置（不含 Key）。
- `GET /api/debug/config`：返回非敏感运行时配置（`service / version / aiProvider / aiEnabled / amapEnabled / allowedOrigins / dataMode`），不返回任何 Key。
- `POST /api/places/recommend`：根据运行模式返回 高德+AI / 高德 / AI / 后端 Mock 候选地点。
- `POST /api/places/extract`：AI 提取粘贴文本里的地点，有 `AMAP_KEY` 时补齐地址与经纬度；无 AI 时走后端规则提取。
- `POST /api/itinerary/generate`：有 AI 时生成自然语言行程；有高德时优先按经纬度顺序排序地点。

## 线上部署

前端仍部署在 Vercel，Root Directory 为 `apps/web`。

V2.1 前端 Mock 模式：

```env
VITE_USE_MOCK=true
VITE_API_BASE_URL=
```

V3 前后端联通模式：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=https://your-api-service.onrender.com
```

FastAPI 后端推荐部署到 Render（或 Railway）。V4 后端推荐环境变量：

```env
ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app
AI_PROVIDER=openai-compatible
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4.1-mini
AI_API_KEY=不要写入仓库，只在 Render 后台配置
AMAP_KEY=不要写入仓库，只在 Render 后台配置
```

验证是否真的启用了 AI / 高德：

1. 访问 `https://travel-ai-planner-api.onrender.com/api/debug/config`，查看 `aiEnabled` 与 `amapEnabled` 是否为 `true`，`dataMode` 是否为 “真实 AI + 高德”。
2. 在前端 Network 中查看 `POST /api/places/recommend` 返回体里的 `dataSourceLabel`，以及顶部版本签（例如 `V4 AI + Amap`）。

当前线上联通验证方式：

- 访问 `https://travel-ai-planner-api.onrender.com/api/debug/cors`，确认 `allowedOrigins` 包含 Vercel 前端地址。
- 在浏览器 Network 中查看 `POST /api/places/recommend` 是否返回 `200`。如果返回 `200`，说明前端确实请求到了后端。
- 如果响应内容提示未配置 `AI_API_KEY`，当前会显示为“后端 Mock”，真实 AI 推荐留到 V4 接入。

完整步骤见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。

## 本地构建检查

后端：

```bash
cd apps/api
python -m compileall app
```

前端 Windows：

```bash
cd apps/web
npm.cmd run typecheck
npm.cmd run build
```

前端非 Windows：

```bash
cd apps/web
npm run typecheck
npm run build
```

## 当前功能

- 首页和开始规划入口
- 问答式旅行需求收集
- 旅行需求摘要
- 城市专属 Mock 候选地点推荐
- 手动粘贴攻略文本并演示提取地点
- 地点标记：想去 / 备选 / 不想去
- 结构化每日行程生成
- 行程项删除和重新生成
- 地图区域降级地点清单
- `localStorage` 本地保存
- 前端 Mock 与后端 Mock API 环境变量切换

## 后续计划

- V4 (current)：接入真实 AI API、高德 POI 搜索；保留后端 Mock 降级。
- V5：接入天气预报，增加雨天备选和户外风险提醒；增加人均预算、每日预算、餐饮、交通、门票等量化输入。
- 后续：高德路线规划、拖拽调整行程顺序、导出和分享能力。
