# AI 出行旅游计划助手

当前版本：V2 Web Deploy Ready

这是一个网页端旅行规划 MVP。用户通过问答收集旅行需求，系统推荐候选地点，用户选择想去、备选或不想去，再生成每日行程，并在地图区域显示地点清单或地图降级视图。

## 版本说明

- V1：本地 Mock 流程可运行。
- V2：前端可部署到 Vercel / Cloudflare Pages，手机浏览器可直接体验。
- 当前线上部署默认使用 Mock 数据，不需要部署 FastAPI 后端。
- V3 之后再考虑部署 FastAPI 后端、真实 AI、真实地图地理编码和路线规划。

## 技术栈

- 前端：Vue 3 + Vite + TypeScript + 普通 CSS
- 后端：FastAPI + Python，当前仅作为本地 Mock/API 骨架
- 地图：高德地图 JS API 可选；未配置 Key 时自动降级为地点清单
- 存储：浏览器 `localStorage`
- Mock：默认 `VITE_USE_MOCK=true`，前端不依赖后端也能完整运行

## 项目结构

```text
travel-ai-planner
├─ apps
│  ├─ web        # Vue 3 + Vite + TypeScript 前端
│  └─ api        # FastAPI 后端骨架
├─ docs
│  ├─ CHANGE_RECORD.md
│  └─ DEPLOYMENT.md
├─ README.md
├─ AGENTS.md
└─ .env.example
```

## 本地运行

V2 默认可以只跑前端 Mock：

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

复制 `.env.example` 为项目根目录 `.env`，按需填写。V2 默认保持：

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

V2 部署不要求 FastAPI。仅本地测试后端时使用：

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

V2 推荐部署 `apps/web` 为纯静态前端。部署文档见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。

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
- 候选地点推荐
- 手动粘贴攻略文本并提取地点
- 地点标记：想去 / 备选 / 不想去
- 结构化每日行程生成
- 行程项删除和重新生成
- 地图区域降级地点清单
- `localStorage` 本地保存

## 后续计划

- V3：部署 FastAPI 后端
- 接入真实 AI API
- 接入地点地理编码，补全经纬度
- 增加真实路线连线和交通时间估算
- 支持拖拽调整行程顺序
- 增加导出和分享能力
