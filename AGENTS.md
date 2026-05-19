# AI Agent 协作规则

本项目是“AI 出行旅游计划助手”。当前版本为 V4.1：在 V4 高德 POI 已跑通的基础上接入 AI（OpenAI-compatible），并把 AI 成功 / AI 失败但高德 OK / 完全无 Key 三种状态在 envelope 与前端文案中显式区分。AI 请求失败时会保留高德 POI，文案降级为后端模板，envelope 中 `dataSourceLabel="高德地图 + 后端模板"`，前端 Header 显示 `V4.1 AI Fallback` 并附明显提示。Vercel 前端继续请求 Render 后端。

后续 agent 修改项目时请遵守以下规则：

1. 先读现有文件，再动手改代码。至少查看 `README.md`、`docs/CHANGE_RECORD.md`、`docs/DEPLOYMENT.md`、`docs/USER_FEEDBACK.md` 和相关源码文件。
2. 不要删除用户已有文件或大段重写无关代码；确实要删改时，在 `docs/CHANGE_RECORD.md` 写清原因。
3. 不要提交、打印或写死真实 API Key。环境变量只写在本地 `.env`，示例写到 `.env.example` 或 `.env.*.example`。
4. 每轮改动都要更新 `docs/CHANGE_RECORD.md`，记录新增、修改、删除的文件和目的。
5. 用户反馈相关修改必须同步更新 `docs/USER_FEEDBACK.md` 或 `docs/CHANGE_RECORD.md`。
6. 部署相关修改必须同步更新 `docs/DEPLOYMENT.md` 和 `docs/CHANGE_RECORD.md`。
7. Mock 数据不能声称来自小红书、高德地图、携程、马蜂窝、Tripadvisor 或其他真实平台。
8. V2/V2.1 不应引入真实后端依赖，不应要求线上部署 FastAPI，不应新增数据库或登录系统。
9. 前端保持 Vue 3 + Vite + TypeScript，避免引入重 UI 库；优先使用普通 CSS 和现有组件结构。
10. 后端保持 FastAPI 骨架，AI 调用必须有 Mock 降级；AI 输出必须按 JSON 解析并容错。
11. 高德地图 Key 缺失或加载失败时必须降级展示地点清单，不能影响主流程。
12. 不要实现自动爬取小红书等违反平台规则的爬虫；只允许用户手动粘贴攻略文本后进行提取。
13. 提交前尽量运行前端 `npm.cmd run typecheck` 和 `npm.cmd run build`；如果无法运行，说明原因和风险。
14. V3 起允许部署 FastAPI 后端，但后端仍必须保留 Mock 降级；后端部署相关修改必须同步更新 `docs/DEPLOYMENT.md` 和 `docs/CHANGE_RECORD.md`。
15. 环境变量示例文件可以提交，真实 `.env`、真实 API Key、Render / Railway / Vercel 私密配置不得提交，也不得写死到代码中。
16. Mock 数据不得声称来自真实平台；如果展示来源，必须明确是 Mock 数据、用户粘贴文本或后续真实 API 能力。
17. V3 前端文案必须区分“前端 Mock”“后端 Mock”和“后端请求失败后的前端 Mock 降级”。`VITE_USE_MOCK=false` 且后端接口返回 2xx 时，不要把后端 Mock 说成前端 Mock 或请求失败。
18. V4 之前不要宣称已接入真实 AI 或真实地图数据；未配置 `AI_API_KEY` 时，后端返回的是后端 Mock 数据。
