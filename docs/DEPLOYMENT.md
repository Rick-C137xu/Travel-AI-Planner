# V2 部署指南

## V2 部署目标

V2 的目标是把 `apps/web` 作为纯静态前端部署到 Vercel 或 Cloudflare Pages，让手机浏览器可以直接打开并完整体验 Mock 旅行规划流程。

V2 不部署 FastAPI 后端，不接真实 AI API，不接真实高德地图 API，也不需要数据库或登录系统。生产环境默认使用：

```env
VITE_USE_MOCK=true
```

## Vercel 部署步骤

1. 登录 Vercel。
2. 点击 Import GitHub Repository。
3. 选择 `Travel-AI-Planner` 仓库。
4. 设置 Root Directory 为 `apps/web`。
5. Framework Preset 选择 `Vite`。
6. Build Command 填 `npm run build`。
7. Output Directory 填 `dist`。
8. Install Command 填 `npm install`。
9. 添加环境变量 `VITE_USE_MOCK=true`。
10. 点击 Deploy。
11. 打开生成的网址，测试完整 Mock 流程。

Vercel SPA fallback 已通过 `apps/web/vercel.json` 配置：

```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

## Cloudflare Pages 部署步骤

1. 登录 Cloudflare Dashboard。
2. 在 Workers & Pages / Pages 中创建项目。
3. 连接 GitHub 仓库。
4. 设置 Root directory 为 `apps/web`。
5. Framework preset 选择 `Vite` 或 `None`。
6. Build command 填 `npm run build`。
7. Build output directory 填 `dist`。
8. 添加环境变量 `VITE_USE_MOCK=true`。
9. 点击 Deploy。
10. 打开生成的网址，测试完整 Mock 流程。

Cloudflare Pages SPA fallback 已通过 `apps/web/public/_redirects` 配置：

```text
/* /index.html 200
```

## 环境变量设置

V2 生产部署至少需要：

```env
VITE_USE_MOCK=true
```

可选变量：

```env
VITE_API_BASE_URL=
VITE_AMAP_KEY=
VITE_AMAP_SECURITY_CODE=
```

说明：

- `VITE_USE_MOCK=true` 时，前端不会请求 FastAPI。
- `VITE_API_BASE_URL` 在 V2 静态部署中可以留空。
- `VITE_AMAP_KEY` 留空时，地图区域会显示降级地点清单。
- 不要在 Vercel、Cloudflare 配置文件或仓库中写入真实 Key。

## 如何确认部署成功

部署完成后，用桌面浏览器和手机浏览器分别打开部署地址，确认以下流程可走通：

1. 首页显示“AI 出行旅游计划助手”。
2. 点击“开始规划”。
3. 完成问答式需求收集。
4. 进入候选地点推荐页。
5. 对地点选择“想去 / 备选 / 不想去”。
6. 点击生成行程。
7. 页面展示 Day 1、Day 2 等每日行程。
8. 地图区域在未配置高德 Key 时显示降级地点清单。
9. 刷新页面后，`localStorage` 中的计划仍然保留。

## 常见问题

### 部署后刷新页面 404

确认 Vercel 使用了 `apps/web/vercel.json`，Cloudflare Pages 使用了 `apps/web/public/_redirects`。这两个文件用于 SPA fallback。

### 页面请求后端失败

V2 默认不需要后端。确认生产环境变量设置为：

```env
VITE_USE_MOCK=true
```

### 地图没有显示真实地图

V2 默认不配置真实高德地图 Key。未配置 `VITE_AMAP_KEY` 时，页面会显示降级地点清单，这是预期行为。

### 手机页面按钮换行

这是预期的移动端布局。V2 优先保证手机可用和不横向溢出，按钮在窄屏会自动换行。

## 为什么 V2 不部署 FastAPI 后端

V2 的重点是先把 Mock 版体验放到线上，让用户可以通过手机浏览器完整体验产品流程。这样可以更快验证页面流程、文案、交互和行程结构，不必先处理后端部署、AI Key、地图 Key、跨域和服务稳定性。

## V3 才会部署 FastAPI 后端

V3 可以开始考虑：

- 部署 FastAPI 后端。
- 接入真实 AI API。
- 增加服务端 Prompt 和 JSON 容错监控。
- 接入真实地点地理编码。
- 增加路线规划和交通时间估算。
