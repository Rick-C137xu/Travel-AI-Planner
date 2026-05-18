# AI 出行旅游计划助手

当前版本：V3 Backend Deploy Ready

这是一个网页端旅行规划 MVP。用户通过问答收集旅行需求，系统推荐候选地点，用户选择想去、备选或不想去，再生成每日行程，并在地图区域显示地点清单或地图降级视图。

## 版本说明

- V1：本地 Mock 流程可运行。
- V2：前端可部署到 Vercel / Cloudflare Pages，手机浏览器可直接体验。
- V2.1：根据用户反馈优化 Mock 推荐、数据来源说明、攻略文本演示提取和手机端候选地点卡片。
- V3：FastAPI 后端部署就绪，前端可通过 `VITE_USE_MOCK=false` 请求线上后端 Mock API。

V3 的重点是完成前后端分离部署链路。后端仍然返回 Mock 数据，不接真实 AI、真实高德地图、真实天气、数据库或登录系统。真实 AI 和地图能力留到 V4，天气和预算量化等能力留到 V5。

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

## 后端接口

V3 后端新增或确认以下接口：

- `GET /`：返回 API 名称和版本。
- `GET /health`：返回服务健康状态。
- `GET /api/health`：返回服务健康状态和 AI 是否启用。
- `POST /api/places/recommend`：返回 Mock 候选地点。
- `POST /api/places/extract`：根据用户粘贴文本返回 Mock 提取地点。
- `POST /api/itinerary/generate`：返回 Mock 行程。

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

FastAPI 后端推荐部署到 Render 或 Railway。后端需要设置：

```env
ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app
```

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

- V4：接入真实 AI API，优化地点推荐和攻略文本解析。
- V4：接入真实地图地点搜索、地理编码和路线规划。
- V5：接入天气预报，增加雨天备选和户外风险提醒。
- V5：增加人均预算、每日预算、餐饮、交通、门票等量化输入。
- 后续：拖拽调整行程顺序、导出和分享能力。
