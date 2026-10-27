# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline with automated build and deploy
- release-please for automated semantic versioning
- Version info generation from git history
- Compliance detection with HAOHUO_* plugins
- Product and works compliance checking endpoints

### Changed
- Docker build now uses pre-generated version files
- Compliance rules now support `applicable_to` field (product/work)
- Rule engine plugins registered for HAOHUO_IMAGE, HAOHUO_SPEC, HAOHUO_PRICE, HAOHUO_FATAL
- 配置双写审计：移除 auth 旁路写 (cache.set CACHE_KEYS['auth'])，统一通过 set_config (Redis ttl=None + JSON 文件) 双写
- alert_history 写入改为 ttl=None，避免 1 小时后告警历史随缓存过期而清空
- media/accounts/videos CRUD 改为双写 (Redis ttl=None + JSON 文件)，避免缓存过期后数据丢失
- save_json_file 临时文件名改为带 pid+uuid，避免多 worker 并发写入互相覆盖

### Fixed
- HAOHUO plugin field path mapping (haohuo_detail_info, haohuo_extra)
- Indentation error in rule_engine.py
- 新建合规规则丢失 applicable_to 字段（新增规则适用范围回退为全部目标）
- /data/alert_config.json 为非法 JSON，重启后告警配置回退默认值 enabled=true，现已修正为合法 JSON 并双写 enabled=false
- 清理 Redis 残留键 douyin:monitor:auth，防止 save_all_data 用带 TTL 的默认值覆盖授权配置
- **订单页面无数据**：`FXG_COOKIES` 会话 Cookie 过期导致 FXG API 返回 `code=10008` 登录信息已失效；已将完整 Cookie 替换并重建 `app` 容器，`/api/v1/orders?page=1` 返回 `data_source="real"` 且 `items` 非空
- **`page=0` 订单列表为空**：`orders.py` 分页逻辑 `page = int(...)` 改为 `page = max(1, int(...))`，前端若误传 `page=0` 会被纠正为第 1 页返回数据
- **`TOKEN` 签名参数非必需**：清空 `TOKEN=` 后 `/api/v1/orders` 仍正常返回真实订单数据，订单数据主要依赖 `FXG_COOKIES` 会话 Cookie

## [0.1.0] - 2026-10-15

### Added
- Initial commit: Douyin compliance platform with HAOHUO plugins enabled
- Product compliance checking with Haohuo preview data enrichment
- Works compliance checking for creator content
- Git version control with automated deployment
