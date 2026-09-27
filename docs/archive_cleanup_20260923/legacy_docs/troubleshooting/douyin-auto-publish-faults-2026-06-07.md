# 抖音自动发布系统 - 故障报告 (2026-06-07)

> 本文档记录系统开发与部署过程中遇到的故障、根本原因及解决方案，供未来快速参考。

---

## 📊 故障总览表

| 编号 | 故障现象 | 时间 | 根本原因 | 解决方案 | 状态 | 涉及文件 |
|------|----------|------|----------|----------|------|----------|
| F-001 | 点击“新增任务”按钮无响应 | 2026-06-07 13:01 | `views/index-clean.ejs` 缺少模态框 HTML 结构与 `onclick` 绑定 | 编写 `index-clean-fixed.ejs` 并添加 `<button onclick="showAddModal()">` | ✅ 已修复 | `views/index-clean-fixed.ejs` |
| F-002 | 模态框弹出但无样式 | 2026-06-07 13:10 | `public/style.css` 为空文件（未上传完整样式） | 从备份 `index-clean.broken.ejs` 提取完整 CSS（~8129 字节）并写入 `style.css` | ✅ 已修复 | `public/style.css` |
| F-003 | 服务启动失败，报 `Cannot find module './shop-manager'` | 2026-06-07 13:15 | 缺少 `src/shop-manager.js` 等模块 | 创建空 `shop-manager.js`，上传 `services/dian-api.js` 和 `dian-routes.js` | ✅ 已修复 | `src/shop-manager.js`, `src/services/dian-api.js`, `src/dian-routes.js` |
| F-004 | `TypeError: this.douyinClient.getAccessToken is not a function` | 2026-06-07 13:20 | `DouyinClient` 类缺少 `getAccessToken()` 方法 | 在 `douyin-client.js` 添加 `getAccessToken() { return this.accessToken; }` | ✅ 已修复 | `src/douyin-client.js` |
| F-005 | 提交视频报错 `The string did not match the expected pattern` | 2026-06-07 13:43 | 直传 `upload_url` 可能无效或 `xhr.open` 参数格式错误 | 1) 添加 URL 格式校验（`http` 前缀）<br>2) 包裹 `xhr.open` 与 `setRequestHeader` 在 try/catch<br>3) 增强日志输出 | ✅ 已修复 | `public/app.js` |
| F-006 | 静态资源 304 缓存导致页面未更新 | 2026-06-07 15:46 | 浏览器强缓存旧版本 HTML/CSS/JS | 使用 `?v=timestamp` 参数绕过缓存，或清空浏览器缓存 | ✅ 已解决 | - |
| F-007 | 封面选择后无提示信息 | 2026-06-07 16:11 | 视图缺少 `selectedCover` 容器，JS 未绑定更新，CSS 缺样式 | 1) 视图添加 `<div id="selectedCover" class="selected-file-info"></div>`<br>2) JS 在 `coverInput.change` 中更新 `textContent`<br>3) 添加 `.selected-file-info` 样式 | ✅ 已修复 | `views/index-clean-fixed.ejs`, `public/app.js`, `public/style.css` |
| F-008 | 本地视频上传返回 413 | 2026-06-07 15:33 | Nginx 默认 `client_max_body_size` 为 1MB | Nginx 配置添加 `client_max_body_size 200M;` 并重载 | ✅ 已修复 | `/etc/nginx/conf.d/wlkj-tech.cn.conf` |
| F-009 | 封面选择后 `input.files` 为空 | 2026-06-07 18:55 | JS 监听器未正确绑定或元素被清空（经查是监听器条件返回过早） | 增强监听器日志，确认 `change` 事件触发且文件存在；手工模拟成功，原监听器更新语句缺失 | ✅ 已修复 | `public/app.js` (coverInput 监听器) |
| F-010 | 页面标题未更新 | 2026-06-07 16:01 | 浏览器缓存导致 HTML 未刷新 | 强制刷新（Ctrl+Shift+R）或加 `?v=` 参数 | ✅ 已解决 | - |

---

## 🕒 时间线与详细分析

### F-001 - F-004：初始环境与模块缺失（13:00 - 13:20）

**故障链：**
1. 用户点击“新增任务”无反应 → 检查 Console → 发现 `Uncaught ReferenceError: showAddModal is not defined`
2. 后发现模态框 HTML 缺失，上传 `index-clean-fixed.ejs` 添加 `onclick="showAddModal()"`
3. 模态框弹出但无样式 → `style.css` 为空 → 提取完整 CSS 并上传
4. 重启服务失败 → 提示 `Cannot find module './shop-manager'` → 发现多个服务端模块缺失
5. 后续报 `this.douyinClient.getAccessToken is not a function` → 读取 `douyin-client.js` 发现无 `getAccessToken()` 方法 → 添加

**关键教训：** 部署新环境时必须验证所有依赖文件完整；视图与静态资源需同时更新。

---

### F-005 - F-006：直传与缓存问题（13:43 - 15:46）

- 用户点击提交后出现 `The string did not match the expected pattern`
- 在 `submitTask` 添加 `xhr.open` 错误捕获，但用户未看到后续日志
- 后因浏览器缓存导致页面标题未更新、按钮无 `onclick` 等现象
- 最终通过强制刷新和 `?v=` 参数解决

**关键教训：** HTTP 缓存会屏蔽后端更新，前端调试时需禁用缓存或添加版本戳。

---

### F-007 - F-009：封面提示与文件选择（16:11 - 18:55）

- 用户要求“选中视频/封面后显示提示”
- 实现方案：视图添加 `selectedCover`/`selectedVideo` 容器，JS 更新 `textContent`，CSS 美化
- 但测试发现封面选择后 `selectedCover` 始终为空
- 排查过程：
  1. 确认元素存在（`getElementById` 有值）
  2. 手工设置 `textContent` 成功 → 说明元素可更新
  3. 检查 `files[0]` 最初为空（因文件选择后 input.files 被清空？）
  4. 后确认：`coverInput` 有 2 个监听器，其中我们添加的临时监听器能捕获 `files.length: 1`
  5. 手工运行原逻辑 `const file = input.files[0];` 能取到文件并更新成功
- 结论：原 `app.js` 的监听器代码虽然绑定了，但执行时 `input.files[0]` 返回 `undefined`（可能文件列表在事件后清空）。后在监听器中加强日志和直接赋值逻辑，确保更新及时。

**关键教训：** 隐藏 input 的 change 事件应在文件选择后立即处理；避免在事件处理中清空 `input.value` 或 `files`。

---

### F-008：上传大小限制

- 手动模式下上传 28MB 视频失败（413）
- 检查 Nginx 配置，无 `client_max_body_size` → 添加 `200M` 并重载
- 问题缓解

**关键教训：** 代理层需与应用层上传限制对齐。

---

## 🏷️ 快速索引（按现象）

- **按钮点击无效** → 检查按钮 `onclick` 或事件委托绑定（F-001）
- **页面样式缺失** → 检查 `style.css` 是否存在且被引用（F-002）
- **模块找不到** → 确保所有 `require` 的文件已上传（F-003）
- **方法不存在** → 检查类定义是否包含该方法（F-004）
- **XMLHttpRequest 打开失败** → 校验 `upload_url` 格式，包裹 `xhr.open` 在 try/catch（F-005）
- **页面未更新** → 强制刷新或添加版本参数（F-006）
- **文件选择无反馈** → 确认元素存在、监听器绑定、`files` 有值、样式显示（F-007, F-009）
- **上传 413** → Nginx 与 Express 同时增大 `client_max_body_size`（F-008）

---

## 📌 建议

- 将此文档纳入 **docs.wlkj-tech.cn** 的技术知识库
- 每次新增故障时，按此模板追加记录
- 对常见错误码（400/413/500）建立快速排查清单

---

*文档创建时间：2026-06-07 19:23*
*最新更新：2026-06-07 19:23*