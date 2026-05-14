# Change Record

## 2026-05-14 V1 MVP

从空目录创建“AI 出行旅游计划助手”V1 MVP。

### 新增

- `.gitignore`：忽略 `node_modules`、`dist`、`.env`、虚拟环境、缓存等本地生成文件。
- `.env.example`：列出 AI、高德地图和前端代理相关环境变量，不包含真实 Key。
- `README.md`：补充项目功能、技术栈、安装运行方式、环境变量、API、当前版本功能和后续计划。
- `AGENTS.md`：定义后续 AI agent 修改项目的协作规则。
- `apps/web`：创建 Vue 3 + Vite + TypeScript 前端。
- `apps/web/src/components/*`：创建首页、问答、需求摘要、候选地点、行程、地图和攻略粘贴相关组件。
- `apps/web/src/services/api.ts`：前端 API 请求封装。
- `apps/web/src/services/amapService.ts`：高德地图加载、创建地图、marker 管理和视野适配。
- `apps/web/src/store/usePlannerStore.ts`：响应式状态和 `localStorage` 持久化。
- `apps/web/src/types.ts`：前端核心数据结构。
- `apps/web/src/data/questions.ts`：问答问题配置。
- `apps/web/src/styles.css`：全局样式和响应式布局。
- `apps/api`：创建 FastAPI 后端骨架。
- `apps/api/app/models.py`：后端核心数据模型。
- `apps/api/app/mock_data.py`：Mock 候选地点、攻略提取和行程生成。
- `apps/api/app/ai_client.py`：可选 AI 调用和 JSON 容错解析。
- `apps/api/app/main.py`：健康检查、问答、候选地点、攻略提取、行程生成 API。

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
- `docs/DEPLOYMENT.md`：新增 V2 部署文档，包含 Vercel、Cloudflare Pages、环境变量、常见问题、成功验证和 V3 后端说明。
- `docs/CHANGE_RECORD.md`：记录本轮 V2 修改、原因和验证。
- `AGENTS.md`：补充部署配置不要写死密钥、V2 不引入真实后端依赖、部署修改必须更新文档的规则。

### 为什么修改

- 让 `apps/web` 可以作为纯静态前端部署到 Vercel / Cloudflare Pages。
- 确保生产环境默认使用前端 Mock，手机浏览器无需后端即可完整体验 V1 流程。
- 为后续加入路由预留 SPA fallback。

### 如何验证

- 已在 `apps/web` 下运行 `npm.cmd run typecheck`，通过。
- 已在 `apps/web` 下运行 `npm.cmd run build`，通过。
- 部署后打开生成的网址，完整测试首页、问答、地点选择、行程生成、地图降级清单和刷新后的本地保存。

### 是否影响 V1 原有功能

- 不影响 V1 本地 Mock 流程。
- 不改变 FastAPI 后端骨架。
- 不接入真实 AI、真实高德地图、登录、数据库或 PWA。
