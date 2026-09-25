## 抖音权限能力文档（Douyin Permission Capability Documentation）

> **版本**：2026-08-26  
> **适用范围**：抖音开放平台（Douyin Open Platform）API 与前端授权流程  
> **目标**：帮助开发者快速了解可用权限、使用场景以及授权二维码的最佳实践  

---

### 1. 权限分类

| 类别 | 说明 | 主要权限 |
|------|------|----------|
| **认证与登录** | 用于用户身份验证、登录状态管理 | `授权登录能力`、`user.identification.only`、`JSBridge`、`唤起用户授权界面`、`唤起原生半屏授权界面` |
| **内容分发** | 内容转发、分享至抖音、H5 内容分享 | `aweme.forward`、`aweme.share`、`h5.share`、`im.share`、`native.im.enterChooseContact`、`native.im.enterShare`、`sdk.open.share` |
| **任务与业务** | 任务管理、业务审计、账号关联 | `jump.basic`、`open.business.task_manage`、`open.business.task_verify`、`ma.openapi.task_writeoff` |
| **Web/UX 交互** | 前端页面交互、WebView 手势、音乐收藏 | `JSBridge`、`控制webview全屏手势`、`抖音端内查询音乐收藏状态`、`在抖音端内收藏抖音music clip`、`用原生能力后台播放音乐` |
| **安全与签名** | 请求签名、令牌管理 | `签名ticket`、`获取签名ticket` |
| **其他** | 业务流程、Webhook 管理等 | `aweme.webhook`、`user.identification.only`、`JSBridge` |

---

### 2. 已获得权限列表（截至 2026-08-26）

| 权限代码 | 权限名称 | 状态 | 适用场景 |
|----------|----------|------|----------|
| `user_info` | 授权登录能力 | ✅ 已获得 | 用户登录抖音，获取登录状态 |
| `auth.comment` | 授权页自定义备注说明 | ✅ 已获得 | 在授权页中添加备注说明 |
| `incremental_authorization` | 增量授权 | ✅ 已获得 | 在已有授权基础上增量获取额外权限 |
| `renew_refresh_token` | 授权动态续期 | ✅ 已获得 | 动态续期 refresh_token |
| `aweme.forward` | 转发内容至抖音 | ✅ 已获得 | 将用户生成内容转发至抖音平台 |
| `im.share` | 选择联系人 | ✅ 已获得 | 打开系统原生联系人选择界面进行分享 |
| `native.im.enterChooseContact` | 打开站内分享界面 | ✅ 已获得 | 通过原生 UI 打开分享选择界面 |
| `native.im.enterShare` | 分享 SDK | ✅ 已获得 | 调用抖音 SDK 进行分享 |
| `sdk.open.share` | 获取核心场景跳转链接 | ✅ 已获得 | 获取抖音核心场景的跳转链接 |
| `jump.basic` | 任务活动管理 | ✅ 已获得 | 管理任务、活动、营销活动 |
| `open.business.task_manage` | 经营任务核销 | ✅ 已获得 | 管理经营任务、核销 |
| `open.business.task_verify` | 建立账号BC授权关系 | ✅ 已获得 | 建立抖音账号（BC）与本系统的授权关系 |
| `ma.openapi.task_writeoff` | 获取核心场景跳转链接 | ✅ 已获得 | 获取特定任务的跳转链接 |
| `user.identification.only` | 获取用户唯一标识映射信息 | ✅ 已获得 | 获取用户在不同平台的唯一标识映射 |
| `aweme.webhook` | Webhook OpenAPI 管理 | ✅ 已获得 | 处理抖音 Webhook 回调 |
| `JSBridge` | JSBridge | ✅ 已获得 | 前端与抖音端交互桥梁 |
| `签名ticket` | 获取签名ticket | ✅ 已获得 | 获取请求签名的临时凭证 |
| `唤起用户授权界面` | 唤起用户授权界面 | ✅ 已获得 | 唤起抖音原生授权界面 |
| `唤起原生半屏授权界面` | 唤起原生半屏授权界面 | ✅ 已获得 | 唤起半屏授权界面 |
| `抖音端内查询音乐收藏状态` | 查询音乐收藏状态 | ✅ 已获得 | 查询用户是否收藏了特定音乐 |
| `控制webview全屏手势` | 控制 webview 全屏手势 | ✅ 已获得 | 控制 WebView 的全屏手势交互 |
| `在抖音端内收藏抖音music clip` | 收藏抖音音乐片段 | ✅ 已获得 | 在抖音内收藏音乐片段 |
| `用原生能力后台播放音乐` | 后台播放音乐 | ✅ 已获得 | 使用原生能力在后台播放音乐 |

### 2.1 未获得权限列表

| 权限代码 | 权限名称 | 状态 | 配额 | 备注 |
|----------|----------|------|------|------|
| `aweme.share` | 发布内容至抖音（APP 场景） | ❌ 未开通 | 100000/100000 | 不支持购买 |
| `h5.share` | 发布内容至抖音（H5 场景） | ❌ 审核失败 | 100000/100000 | 开通审核失败 |
| `open.get.ticket` | 获取 openTicket | ❌ 未获得 | 100000/100000 | 不支持购买 |

---

### 2.2 授权二维码生成与使用流程

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | **获取 OAuth URL** | 前端调用 `authApi.getQrCode()`，后端 `/auth/qr-code` 返回真实的 OAuth URL（包含 `client_key`、`response_type`、`redirect_uri`、`scope`、`state` 等） |
| 2 | **生成二维码** | 前端使用 `qrcode.react` 将返回的 `auth_url` 编码为二维码图片 |
| 3 | **展示二维码** | 前端在页面中渲染 QR 码，提示用户使用抖音扫码授权 |
| 4 | **用户扫码** | 用户使用抖音 App 扫描二维码，跳转至抖音授权页面 |
| 5 | **授权完成** | 抖音返回 `code`，后端 `/auth/callback` 完成 token 交换 |
| 6 | **获取 token** | 后端完成 token 交换后返回 `access_token`、`refresh_token` 等，前端本地存储 |

---

### 3. 授权二维码最佳实践

| 项目 | 推荐做法 | 目的 |
|------|----------|------|
| **二维码内容** | 只编码 OAuth URL（完整 URL，含查询参数） | 确保抖音 App 能识别并跳转到授权页面 |
| **URL 参数** | 必须包含 `scope`（所需权限）、`state`（防 CSRF） | 防止授权失败、提升安全性 |
| **URL 编码** | 使用 `encodeURIComponent` 对参数进行正确编码 | 防止参数解析错误 |
| **二维码大小** | 尺寸 200x200px（推荐），保持清晰度 | 保证扫码成功率 |
| **错误容错** | 前端捕获异常并提示"获取二维码失败"，提供"刷新二维码"按钮 | 提升用户体验 |
| **安全** | `state` 参数必须唯一且短暂有效，后端验证后即可删除 | 防止重放攻击 |
| **权限最小化** | 只在 `scope` 中包含实际需要的权限 | 减少审核通过难度、提升安全性 |

---

### 4. 当前项目配置

| 配置项 | 值 |
|--------|-----|
| 后端接口 | `GET /api/v1/auth/qr-code` |
| 返回格式 | `{ success: true, data: { auth_url: string }, message: string }` |
| OAuth URL | `https://open.douyin.com/platform/oauth/connect/` |
| client_key | `aw370towtp6bg82b` |
| redirect_uri | `https://wlkj-tech.cn/api/v1/auth/callback` |
| 当前 scope | `video.list,video.create,creator.info` |
| state 格式 | `douyin_oauth_{timestamp}` |

### 5. 审查频率与负责人

| 项目 | 说明 |
|------|------|
| 审查频率 | 每季度审查一次，或在抖音开放平台更新权限后立即审查 |
| 负责人 | 项目维护者 |
| 最后更新 | 2026-08-26 |
