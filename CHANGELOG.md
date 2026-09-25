# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 初始化项目结构
- 实现前端仪表盘布局优化（3列核心指标网格）
- 修复动态趋势着色（CreatorDataCard组件）
- 统一页面布局使用PageContainer、PageHeader、TableCard组件
- 创建后端服务文档（src/backend/README.md）
- 创建后端变更日志（src/backend/CHANGELOG.md）
- 更新项目文档以反映实际结构
- 修复所有损坏的文档链接
- 清理重复和过时的文档

### Changed
- 调整Dashboard布局：核心指标网格从6列改为3列
- 增加各网格间距和图表最小高度以提升可读性
- 更新环境变量文档和设置说明
- 修复本地开发路径说明

### Fixed
- 修复500 API错误：将FXG_SHOP_ID设置为正确的整数值
- 修复环境变量加载问题：确保使用正确的.env文件路径
- 修复后端服务认证配置
- 修复文档索引中的损坏链接
- 修复重复的环境变量条目在docker-compose.yml中
- 2026-09-21 修复 Nginx 502 Bad Gateway：修正 /etc/nginx/conf.d/cci-monitor.conf proxy_set_header 语法错误，恢复反向代理到 127.0.0.1:3000/5000
- 2026-09-21 修复 API 401 Unauthorized：统一后端 API_KEY 与前端 VITE_API_KEY 为 wlkj_douyin_api_20260921_abc123，移除 SKIP_AUTH，frontend/.env 配置 VITE_API_KEY 并重新 vite build 部署
- 2026-09-21 修复前端构建后部署流程，避免 nested build 目录与缓存导致页面无更新

## [v1.0.0] - 2026-09-05
### Added
- 首次正式版本发布