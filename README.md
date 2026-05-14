# AI 出行旅游计划助手

一个网页端 V1 MVP：通过问答收集旅行需求，推荐候选地点，让用户选择想去/不想去/备选，再生成每日行程，并在地图区域展示已选地点。

## 技术栈

- 前端：Vue 3 + Vite + TypeScript + 普通 CSS
- 后端：FastAPI + Python + Pydantic
- 地图：高德地图 JS API，可选配置
- 存储：浏览器 `localStorage`
- AI：兼容 OpenAI Chat Completions 风格接口；未配置 Key 时自动使用 mock 数据

## 项目结构

```text
travel-ai-planner
├─ apps
│  ├─ web        # Vue 3 + Vite + TypeScript 前端
│  └─ api        # FastAPI 后端
├─ docs
│  └─ CHANGE_RECORD.md
├─ README.md
├─ AGENTS.md
└─ .env.example
```

## 本地运行

V1 默认可以只跑前端 mock：保持 `VITE_USE_MOCK=true`，前端不会请求 FastAPI，推荐地点、攻略提取和行程生成都会使用浏览器端 mock 数据。

### 1. 后端

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

### 2. 前端

```bash
cd apps/web
npm install
npm run dev
```

Windows PowerShell 如果遇到 `npm.ps1` 执行策略限制，建议使用：

```bash
cd apps/web
npm.cmd install
npm.cmd run dev
npm.cmd run build
```

浏览器打开：

```text
http://localhost:5173
```

如果要测试 FastAPI 后端，请先启动后端服务，并在项目根目录 `.env` 中设置：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 环境变量

复制 `.env.example` 为本地 `.env`，按需填写。

```env
AI_API_KEY=
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
AMAP_KEY=
AMAP_SECURITY_CODE=
VITE_AMAP_KEY=
VITE_AMAP_SECURITY_CODE=
VITE_USE_MOCK=true
VITE_API_BASE_URL=http://127.0.0.1:8000
```

说明：

- `AI_API_KEY` 留空时，后端返回 mock 候选地点、mock 文本提取和 mock 行程。
- `VITE_AMAP_KEY` 留空时，前端显示降级地图区域和地点清单。
- `VITE_USE_MOCK=true` 时，前端完全使用本地 mock，不依赖后端。
- `VITE_USE_MOCK=false` 时，前端请求 FastAPI；如果请求失败，会自动降级到前端 mock。
- 不要把真实 Key 提交到仓库。

## 当前版本功能

- 首页展示项目名称、功能说明和“开始规划”按钮。
- 聊天式问答收集目的地、日期/天数、人数、旅行强度、兴趣、雷区、预算、住宿区域和交通偏好。
- 右侧或下方实时显示“旅行需求摘要”，支持返回上一步修改。
- 候选地点推荐：有 AI Key 时调用 AI；无 Key 时使用 mock 数据。
- 支持粘贴攻略文本并提取地点，不做任何自动爬虫。
- 用户可对地点标记“想去 / 备选 / 不想去”。
- 根据已选地点生成按天排列的结构化 JSON 行程并渲染。
- 行程项支持从某一天删除，也支持重新生成。
- 高德地图可选加载；没有 Key 或加载失败时显示降级地点清单和待定位地点列表。
- 使用 `localStorage` 保存当前计划，刷新后保留。
- 提供“清空当前计划”按钮。

## 后端 API

- `GET /api/health`
- `POST /api/chat/next-question`
- `POST /api/places/recommend`
- `POST /api/places/extract`
- `POST /api/itinerary/generate`

## 后续计划

- 接入真实地点地理编码，自动补全经纬度。
- 增加路线连线和真实交通时间估算。
- 支持拖拽调整行程顺序。
- 增加更多城市画像和地点去重策略。
- 增加导出、分享和多人协作能力。
