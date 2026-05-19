# Change Record

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
