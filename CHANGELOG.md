# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 (2026-10-22)


### Features

* system blueprint for version info, optimize version display ([39ecda5](https://github.com/jason19870910/douyin-shop-monitor/commit/39ecda5aca030d1cec787035a0e11ec948c408d4))


### Bug Fixes

* **backend:** load initial data lazily on first request ([bddb157](https://github.com/jason19870910/douyin-shop-monitor/commit/bddb157b9ccf8bfcc8ca6ac49b00df4abf077f67))
* **backend:** stop disabled alert toggles from re-enabling on cache expiry ([e0d59ee](https://github.com/jason19870910/douyin-shop-monitor/commit/e0d59ee6546ff9560e1daa766b4a4977d114d965))
* **ci:** inline ssh options in deploy job to avoid \C:\Users\Administrator/~ double-expansion failure ([368677f](https://github.com/jason19870910/douyin-shop-monitor/commit/368677f60ca069d5af0691d03dc85bad3fd7f1c3))
* **ci:** restore entrypoint.sh exec bit when syncing backend source ([d12a647](https://github.com/jason19870910/douyin-shop-monitor/commit/d12a647914bef152e304b1d790fe949c78b95938))
* **ci:** sync frontend source to server so build uses latest code ([273b36e](https://github.com/jason19870910/douyin-shop-monitor/commit/273b36e84260a3d33cad1d91afbfb0a6b42c88f3))
* **ci:** track frontend tsconfig.json (root .gitignore *.json hid it from CI, broke tsc alias/JX), add temporary ssh diagnostics step in deploy job ([d565176](https://github.com/jason19870910/douyin-shop-monitor/commit/d565176c68ce5a2e50d3aa4866a9104cdb7cb148))
* **ci:** use explicit key file instead of ssh-agent, fix archive path and rollback image names ([97e2457](https://github.com/jason19870910/douyin-shop-monitor/commit/97e24571a7181db72a3bd80e6f686799cc6990d6))
* **compliance:** unify compliance storage and rule engine outcome handling ([f47bdcb](https://github.com/jason19870910/douyin-shop-monitor/commit/f47bdcb7286ba2d7f3872651149f27f97ed8d4cd))
* **deploy:** repair version-control chain and alert toggles ([b59e413](https://github.com/jason19870910/douyin-shop-monitor/commit/b59e413a64f3378f909605cc5c87d401db9e2a6e))
* **docker:** rewrite apt mirror for trixie deb822 sources so build stops hitting deb.debian.org ([b98b3b1](https://github.com/jason19870910/douyin-shop-monitor/commit/b98b3b1df18ef472465283cf438af52d4853ae2b))
* **frontend:** align @eslint/js to v9 to unblock npm ci on CI runners ([7406e11](https://github.com/jason19870910/douyin-shop-monitor/commit/7406e113f674094d47343c0a2e1433d469bbb5f4))
* **frontend:** healthcheck use 127.0.0.1, fix TS errors in VersionControl ([2bd0824](https://github.com/jason19870910/douyin-shop-monitor/commit/2bd082446790a2638bd93cfba8703243336d3ba2))
* make DATA_DIR creation non-fatal at import to fix CI collection error ([2d2a4df](https://github.com/jason19870910/douyin-shop-monitor/commit/2d2a4df17ae446111484583e0c0368abf420afd1))
* **orders:** normalize fxg order fields before API output ([6db6d40](https://github.com/jason19870910/douyin-shop-monitor/commit/6db6d40dd4567f5c254f75f58a47d442eb9b3abe))
* **rollback:** roll back backend source with image and verify by image id ([751d2af](https://github.com/jason19870910/douyin-shop-monitor/commit/751d2afdf62ab823d29e358873167deb3d0aba60))

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

### Fixed
- HAOHUO plugin field path mapping (haohuo_detail_info, haohuo_extra)
- Indentation error in rule_engine.py

## [0.1.0] - 2026-10-15

### Added
- Initial commit: Douyin compliance platform with HAOHUO plugins enabled
- Product compliance checking with Haohuo preview data enrichment
- Works compliance checking for creator content
- Git version control with automated deployment
