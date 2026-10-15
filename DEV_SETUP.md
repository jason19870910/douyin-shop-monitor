# 开发环境与运行说明

推荐在本地与 CI 中使用 Python 3.11（兼容性最好，能避免在 Windows 上构建 pydantic-core 时出现本机编译问题）。

## 快速上手（Windows / macOS / Linux）

1. 安装 Python 3.11（建议从 https://www.python.org/downloads/ 下载安装程序）。
2. 在仓库根目录创建并激活虚拟环境：

   - Windows (PowerShell):

     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

   - macOS / Linux:

     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

3. 安装依赖：

   ```bash
   python -m pip install --upgrade pip
   pip install -r src/backend/requirements-dev.txt
   ```

4. 运行测试：

   ```bash
   pytest -c pytest.ini
   ```

### 前端开发

```bash
cd src/frontend
npm ci
npm run dev
```

> 开发模式会代理至后端 `http://localhost:5000`，使用 Vite 原生代理配置（`vite.config.ts` 中 `proxy: { '/api': { target: 'http://localhost:5000', changeOrigin: true } }`）。

### 全栈（Docker）

```bash
# 1. 环境准备
cp config/.env.example config/.env   # 如有
# 按 secrets_template 准备 secrets/*.txt

# 2. 启动服务
docker compose up -d

# 3. 前端部署（已构建推送）
# 详细部署流程见：[README.md - 部署流程（前端）](./README.md#部署流程前端)
# 修改前端代码后：
cd src/frontend && npm run build
# 然后按 README.md 中的步骤执行 docker cp + nginx reload
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| **前端 403 Forbidden（静态资源）** | 容器内文件属主为 root，Nginx 以 nginx 用户运行。执行：`docker exec <容器> chown -R nginx:nginx /usr/share/nginx/html && chmod -R 755 /usr/share/nginx/html && docker exec <容器> nginx -s reload` |
| **前端页面显示旧内容** | 已部署缓存或镜像未重新构建。执行完上述 docker cp + nginx reload 后，浏览器强制刷新 (Ctrl+Shift+R)。 |
| **401 Unauthorized** | 前后端 API_KEY 不一致。确保 `config/.env` 中 `VITE_API_KEY` 与后端 `Config.API_KEY` 完全一致。 |
| **404 Not Found** | API 路径拼接错误。确认前端使用相对路径（`/creators/overview` 而非 `/api/v1/janus/...`），且 `apiClient.baseURL` 为 `/api/v1`。 |
| **405 Method Not Allowed** | 创作者概览使用 POST 改为 GET。前端 `creatorApi.getCreatorOverview` 已改为 `apiClient.get`。 |

## CI 建议

仓库已包含一个 GitHub Actions 工作流示例（`.github/workflows/ci.yml`），用于在 Python 3.11 下运行 lint 与测试。你可以根据团队需要调整。

如需我为你生成其它 CI 平台或更严格的 lint 规则配置，告诉我即可。

## 新增 API 端点

后端现已提供以下额外接口：

| 路径 | 说明 |
|------|------|
| /api/v1/version | 获取当前应用版本、git commit、构建时间和 API Key 内联状态 |
| /api/v1/changes | 获取最近 10 条 git commit 变更记录 |
| /api/v1/status | 检查 3 容器 (app/redis/frontend) 的健康状态 |
| /api/v1/env | 获取 Vite 环境变量配置 (VITE_API_KEY, VITE_DEV_MODE 等) |

使用示例：

`ash
# 查看版本信息
curl -H 'X-API-Key: wlkj_douyin_api_20260921_abc123' http://122.51.208.138:3000/api/v1/version

# 查看容器状态
curl -H 'X-API-Key: wlkj_douyin_api_20260921_abc123' http://122.51.208.138:3000/api/v1/status
`

前端页面：
- 访问 /dian/version 可查看版本控制管理页面（需在 Layout.tsx 中注册路由）

> 注：上述端点均需要有效的 X-API-Key 认证头。
