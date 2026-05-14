# AI Agent 协作规则

本项目是“AI 出行旅游计划助手”。当前版本为 V2 Web Deploy Ready，前端可作为纯静态站点部署到 Vercel / Cloudflare Pages。

后续 agent 修改项目时请遵守以下规则：

1. 先读现有文件，再动手改代码。至少查看 `README.md`、`docs/CHANGE_RECORD.md`、`docs/DEPLOYMENT.md` 和相关源码文件。
2. 不要删除用户已有文件或大段重写无关代码；确实要删改时，在 `docs/CHANGE_RECORD.md` 写清原因。
3. 不要提交、打印或写死真实 API Key。环境变量只写在本地 `.env`，示例写到 `.env.example` 或 `.env.*.example`。
4. 每轮改动都要更新 `docs/CHANGE_RECORD.md`，记录新增、修改、删除的文件和目的。
5. 部署相关修改必须同步更新 `docs/DEPLOYMENT.md` 和 `docs/CHANGE_RECORD.md`。
6. V2 不应引入真实后端依赖，不应要求线上部署 FastAPI，不应新增数据库或登录系统。
7. 前端保持 Vue 3 + Vite + TypeScript，避免引入重 UI 库；优先使用普通 CSS 和现有组件结构。
8. 后端保持 FastAPI 骨架，AI 调用必须有 Mock 降级；AI 输出必须按 JSON 解析并容错。
9. 高德地图 Key 缺失或加载失败时必须降级展示地点清单，不能影响主流程。
10. 不要实现自动爬取小红书等违反平台规则的爬虫；只允许用户手动粘贴攻略文本后进行提取。
11. 提交前尽量运行前端 `npm.cmd run typecheck` 和 `npm.cmd run build`；如果无法运行，说明原因和风险。
