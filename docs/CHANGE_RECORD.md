# Change Record

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
