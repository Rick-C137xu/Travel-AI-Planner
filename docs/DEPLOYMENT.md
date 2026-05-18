# V3 部署指南

## V2 前端静态部署回顾

V2 / V2.1 的线上前端部署在 Vercel，`apps/web` 可以作为纯静态站点运行。默认环境变量为：

```env
VITE_USE_MOCK=true
VITE_API_BASE_URL=
```

这种模式不会请求 FastAPI 后端，适合继续演示 V2.1 的前端 Mock 流程。Vercel 核心配置：

- Root Directory: `apps/web`
- Framework Preset: `Vite`
- Install Command: `npm install`
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variables: `VITE_USE_MOCK=true`

Cloudflare Pages 仍可按 V2 方式部署：

- Root directory: `apps/web`
- Build command: `npm run build`
- Build output directory: `dist`
- Environment variables: `VITE_USE_MOCK=true`

## V3 后端部署目标

V3 把项目升级为前后端分离部署版：

- 前端仍可用 `VITE_USE_MOCK=true` 保持 V2.1 前端 Mock 演示。
- 前端设置 `VITE_USE_MOCK=false` 后，会请求 `VITE_API_BASE_URL` 指向的 FastAPI 后端。
- FastAPI 后端部署到 Render 或 Railway，当前仍返回 Mock 数据。
- V3 不接真实 AI API、真实地图 API、真实天气 API、数据库或登录系统。

## FastAPI 本地运行

Windows:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

非 Windows:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：

```text
http://127.0.0.1:8000/health
```

应返回：

```json
{
  "status": "ok",
  "service": "travel-ai-planner-api",
  "version": "v3"
}
```

## CORS 配置

后端通过 `ALLOWED_ORIGINS` 配置允许访问的前端来源，支持逗号分隔：

```env
ALLOWED_ORIGINS=http://localhost:5173,https://travel-ai-planner-lake.vercel.app
```

未配置时，默认只允许：

```text
http://localhost:5173
http://127.0.0.1:5173
```

生产环境不要长期使用 `ALLOWED_ORIGINS=*`。如果临时排查跨域问题使用了 `*`，排查完成后应改回明确的 Vercel 前端域名。

V3.0.1 起，后端会在 FastAPI app 创建后立即注册 `CORSMiddleware`：

- `ALLOWED_ORIGINS="*"` 时使用 `allow_origins=["*"]`，并自动设置 `allow_credentials=False`。
- `ALLOWED_ORIGINS` 为逗号分隔域名时，会去掉每一项前后空格并忽略空值。
- `allow_methods=["*"]`、`allow_headers=["*"]`，确保浏览器 `OPTIONS` 预检请求能返回 CORS 头。
- 可访问 `GET /api/debug/cors` 查看当前后端读取到的 `allowedOrigins` 和 `allowCredentials`，该接口不返回 API Key 或其他敏感配置。

## Render 部署步骤

推荐配置：

- Service Type: `Web Service`
- Root Directory: `apps/api`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables:

```env
ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app
```

操作步骤：

1. 登录 Render。
2. New Web Service，导入 GitHub 仓库 `Travel-AI-Planner`。
3. 设置 Root Directory 为 `apps/api`。
4. 设置 Build Command 为 `pip install -r requirements.txt`。
5. 设置 Start Command 为 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
6. 添加 `ALLOWED_ORIGINS`，值为 Vercel 前端地址。
7. 部署完成后打开 `https://your-api-service.onrender.com/health` 验证。

如 Render 需要指定 Python 版本，可在 Render 设置中选择 Python 运行时版本；当前项目暂不强制新增 `runtime.txt`。

## Railway 部署步骤

推荐配置：

- 从 GitHub 导入 `Travel-AI-Planner` 仓库。
- 服务根目录设置为 `apps/api`。
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables:

```env
ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app
```

操作步骤：

1. 登录 Railway。
2. New Project，从 GitHub 导入仓库。
3. 选择或设置服务根目录为 `apps/api`。
4. 如果 Railway 自动识别 Python 项目，仍要检查 Start Command 是否为 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`。
5. 添加 `ALLOWED_ORIGINS`，值为 Vercel 前端地址。
6. 部署完成后打开后端域名的 `/health` 验证。

## Vercel 前端切换到后端模式

在 Vercel 的 `apps/web` 项目中设置：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=https://your-api-service.onrender.com
```

说明：

- `VITE_API_BASE_URL` 不要以 `/api` 结尾，直接填写后端根地址。
- 地址末尾带不带 `/` 都可以，前端会自动去掉末尾斜杠。
- 修改 Vercel 环境变量后必须重新部署前端，新的构建才会生效。
- 如果后端请求失败，页面会显示 warning，并回退到前端 Mock 数据，避免白屏。

## 本地前后端联调

1. 启动后端：

```bash
cd apps/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. 在项目根目录 `.env` 设置：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_AMAP_KEY=
```

3. 启动前端：

```bash
cd apps/web
npm.cmd run dev
```

4. 打开 `http://localhost:5173`，完整测试问答、候选地点、攻略文本提取、行程生成和地图降级地点清单。

## 如何验证部署成功

1. 打开后端 `/health`，确认返回 `status: ok` 和 `version: v3`。
2. 在 Vercel 设置 `VITE_USE_MOCK=false`。
3. 在 Vercel 设置 `VITE_API_BASE_URL=<Render 或 Railway 后端地址>`。
4. 在后端设置 `ALLOWED_ORIGINS=<Vercel 前端地址>`。
5. 重新部署 Vercel 前端。
6. 打开线上前端，完整测试问答、推荐、攻略文本提取、行程生成。
7. 临时关闭或填错后端地址，确认页面会提示后端失败并回退到前端 Mock。

## 常见问题

### CORS 报错

确认后端 `ALLOWED_ORIGINS` 包含完整 Vercel 前端地址，例如：

```env
ALLOWED_ORIGINS=https://travel-ai-planner-lake.vercel.app
```

不要只写域名片段，也不要遗漏 `https://`。

Render 重新部署后，也可以访问：

```text
https://your-api-service.onrender.com/api/debug/cors
```

确认返回的 `allowedOrigins` 包含 Vercel 前端完整域名。如果临时设置为 `ALLOWED_ORIGINS=*`，返回的 `allowCredentials` 应为 `false`。

### 请求 404

确认 `VITE_API_BASE_URL` 是后端根地址，例如：

```env
VITE_API_BASE_URL=https://your-api-service.onrender.com
```

不要写成 `https://your-api-service.onrender.com/api`。

### 502 或后端未启动

检查 Render / Railway 的 Start Command 是否为：

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

同时查看平台日志，确认依赖安装完成且 `apps/api` 是服务根目录。

### Vercel 环境变量修改后没有生效

Vite 会在构建时注入 `VITE_*` 变量。修改 Vercel 环境变量后，需要重新部署前端。

### 后端地址末尾是否带斜杠

可以带也可以不带。前端会把 `VITE_API_BASE_URL` 末尾的 `/` 去掉，再拼接 `/api/...`。

### 本地能跑但线上不能跑

优先检查：

- Render / Railway Root Directory 是否为 `apps/api`。
- Start Command 是否使用 `$PORT`。
- 后端 `/health` 是否能打开。
- Vercel `VITE_API_BASE_URL` 是否指向线上后端。
- 后端 `ALLOWED_ORIGINS` 是否包含 Vercel 前端地址。
- Vercel 修改环境变量后是否重新部署。
