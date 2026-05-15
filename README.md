# AI 出行旅游计划助手

当前版本：V2.1 Feedback Improvement

这是一个网页端旅行规划 MVP。用户通过问答收集旅行需求，系统推荐候选地点，用户选择想去、备选或不想去，再生成每日行程，并在地图区域显示地点清单或地图降级视图。

## 版本说明

- V1：本地 Mock 流程可运行。
- V2：前端可部署到 Vercel / Cloudflare Pages，手机浏览器可直接体验。
- V2.1：根据用户反馈优化 Mock 推荐、数据来源说明、攻略文本演示提取和手机端候选地点卡片。
- 当前线上部署默认使用 Mock 数据，不需要部署 FastAPI 后端。
- 真实 AI、真实地图、真实天气、预算量化仍在后续版本。

## 技术栈

- 前端：Vue 3 + Vite + TypeScript + 普通 CSS
- 后端：FastAPI + Python，当前仅作为本地 Mock/API 骨架
- 地图：高德地图 JS API 可选；未配置 Key 时自动降级为地点清单
- 存储：浏览器 `localStorage`
- Mock：默认 `VITE_USE_MOCK=true`，前端不依赖后端也能完整运行

## V2.1 做了什么

- 增加城市专属 Mock 数据：张家界、重庆、长沙、上海、北京、杭州、南京、成都、西安、广州、厦门。
- 候选地点上方增加数据来源说明，明确当前不是来自真实平台。
- 攻略文本提取优化为更友好的演示能力，支持按换行、标点和序号拆分。
- 候选地点卡片更紧凑，类型、来源、停留时间和适合场景改成标签。
- 地址和避坑提醒收进“详情 / 收起”，减少手机端滑动负担。
- 预算问题增加低 / 中 / 高的解释。
- 文档记录天气预报和预算量化需求，留到后续版本。

## 项目结构

```text
travel-ai-planner
├─ apps
│  ├─ web        # Vue 3 + Vite + TypeScript 前端
│  └─ api        # FastAPI 后端骨架
├─ docs
│  ├─ CHANGE_RECORD.md
│  ├─ DEPLOYMENT.md
│  └─ USER_FEEDBACK.md
├─ README.md
├─ AGENTS.md
└─ .env.example
```

## 本地运行

V2.1 默认可以只跑前端 Mock：

```bash
cd apps/web
npm.cmd install
npm.cmd run dev
```

打开：

```text
http://localhost:5173
```

非 Windows 环境可使用：

```bash
cd apps/web
npm install
npm run dev
```

## 本地构建检查

Windows：

```bash
cd apps/web
npm.cmd run typecheck
npm.cmd run build
```

非 Windows：

```bash
cd apps/web
npm run typecheck
npm run build
```

## 环境变量

复制 `.env.example` 为项目根目录 `.env`，按需填写。V2.1 默认保持：

```env
VITE_USE_MOCK=true
VITE_API_BASE_URL=
VITE_AMAP_KEY=
```

说明：

- `VITE_USE_MOCK=true`：前端完全使用本地 Mock，不请求 FastAPI。
- `VITE_USE_MOCK=false`：前端请求 FastAPI；如果请求失败，会自动降级到前端 Mock。
- `VITE_AMAP_KEY` 留空时，前端显示降级地图区域和地点清单。
- 不要把真实 Key 提交到仓库。

## 测试 FastAPI 后端

V2.1 部署不要求 FastAPI。仅本地测试后端时使用：

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

然后在项目根目录 `.env` 设置：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 部署

V2.1 继续推荐部署 `apps/web` 为纯静态前端。Vercel 部署方式仍然有效，详见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。

Vercel 核心设置：

- Root Directory: `apps/web`
- Framework Preset: `Vite`
- Install Command: `npm install`
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variables: `VITE_USE_MOCK=true`

Cloudflare Pages 核心设置：

- Framework preset: `Vite` 或 `None`
- Root directory: `apps/web`
- Build command: `npm run build`
- Build output directory: `dist`
- Environment variables: `VITE_USE_MOCK=true`

部署完成后，建议直接用手机浏览器打开部署地址，完整测试首页、问答、选地点、生成行程和地图降级地点清单。

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

## 后续计划

- V3：部署 FastAPI 后端。
- V4：接入真实 AI API、地图地点搜索、地理编码和路线规划。
- V4：强化攻略文本解析，但不做违反平台规则的自动爬取。
- V5：接入天气预报，增加雨天备选和户外风险提醒。
- V5：增加人均预算、每日预算、餐饮/交通/门票预算等量化输入。
- 后续：拖拽调整行程顺序、导出和分享能力。
