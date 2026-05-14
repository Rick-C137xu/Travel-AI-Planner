# Change Record

## 2026-05-14

本轮从空目录创建“AI 出行旅游计划助手”V1 MVP。

### 新增

- `.gitignore`：忽略 `node_modules`、`dist`、`.env`、虚拟环境、缓存等本地生成文件。
- `.env.example`：列出 AI、高德地图和前端代理相关环境变量，不包含真实 Key。
- `README.md`：补充项目功能、技术栈、安装运行方式、环境变量、API、当前版本功能和后续计划。
- `AGENTS.md`：定义后续 AI agent 修改项目的协作规则。
- `apps/web`：创建 Vue 3 + Vite + TypeScript 前端。
- `apps/web/src/components/AppHeader.vue`：应用头部、阶段显示和清空计划入口。
- `apps/web/src/components/StartPage.vue`：首页和开始规划入口。
- `apps/web/src/components/GuidedChat.vue`：问答式需求收集流程，支持返回上一步。
- `apps/web/src/components/PreferenceSummary.vue`：旅行需求摘要。
- `apps/web/src/components/PlaceRecommendation.vue`：候选地点推荐、地点选择和生成行程入口。
- `apps/web/src/components/PlaceCard.vue`：候选地点卡片。
- `apps/web/src/components/PasteGuidePanel.vue`：手动粘贴攻略文本并提取地点。
- `apps/web/src/components/ItineraryView.vue`：每日行程展示、删除行程项、重新生成。
- `apps/web/src/components/MapView.vue`：高德地图展示和降级地点清单。
- `apps/web/src/services/api.ts`：前端 API 请求封装。
- `apps/web/src/services/amapService.ts`：高德地图加载、创建地图、marker 管理和视野适配。
- `apps/web/src/store/usePlannerStore.ts`：响应式状态和 `localStorage` 持久化。
- `apps/web/src/types.ts`：前端核心数据结构。
- `apps/web/src/data/questions.ts`：问答问题配置。
- `apps/web/src/styles.css`：全局样式和响应式布局。
- `apps/api`：创建 FastAPI 后端。
- `apps/api/app/models.py`：后端核心数据模型。
- `apps/api/app/mock_data.py`：mock 候选地点、攻略提取和行程生成。
- `apps/api/app/ai_client.py`：可选 AI 调用和 JSON 容错解析。
- `apps/api/app/main.py`：健康检查、问答、候选地点、攻略提取、行程生成 API。
- `apps/web/vite.config.ts`、`apps/api/app/main.py`：支持从项目根目录 `.env` 读取环境变量。

### 说明

- 当前版本不实现登录、自动爬虫、复杂路线优化、真实预订、PDF 导出和多人协作。
- AI 和地图均可选配置，未配置时项目仍可完整本地走通。

### 检查记录

- 已运行 `python -m compileall apps/api/app`，后端源码编译通过。
- 当前环境未安装 FastAPI 和前端 npm 依赖；安装依赖时网络权限受限，已保留 README 中的本地安装运行命令。
- Python 编译检查生成了 `apps/api/app/__pycache__`，该目录已加入 `.gitignore`，不会作为源码提交。

## 2026-05-14 收尾修复

### 修改

- `apps/web/vite.config.ts`：增加 `resolve.alias`，将 `@` 指向 `apps/web/src`；增加 `envDir`，从项目根目录读取 `.env`。
- `apps/web/src/services/api.ts`：增加 `VITE_USE_MOCK` 判断；开启 mock 时不请求后端，请求后端失败时自动降级为前端 mock。
- `apps/web/src/services/mockPlanner.ts`：新增前端 mock 推荐地点、攻略文本提取和行程生成方法。
- `apps/web/src/vite-env.d.ts`：增加 `VITE_USE_MOCK` 类型声明。
- `.env.example`：增加 `VITE_USE_MOCK=true`。
- `README.md`：说明 V1 默认可只跑前端 mock、测试 FastAPI 的配置方式，以及 Windows 下建议使用 `npm.cmd`。
- `apps/api/app/__pycache__`：清理 Python 缓存目录。

### 检查记录

- 已确认 `apps/api/app/__pycache__` 不存在。
- 已运行 `npm.cmd run typecheck`，当前环境因未安装前端依赖失败：`vue-tsc` not recognized。
- 已运行 `npm.cmd run build`，当前环境因未安装前端依赖失败：`vue-tsc` not recognized。
- 已尝试 `npm.cmd install`，但依赖下载超时；随后请求联网安装审批，审批未返回。
