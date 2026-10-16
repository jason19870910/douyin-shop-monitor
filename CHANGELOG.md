# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 (2026-10-16)


### Features

* system blueprint for version info, optimize version display ([39ecda5](https://github.com/jason19870910/douyin-shop-monitor/commit/39ecda5aca030d1cec787035a0e11ec948c408d4))


### Bug Fixes

* **frontend:** healthcheck use 127.0.0.1, fix TS errors in VersionControl ([2bd0824](https://github.com/jason19870910/douyin-shop-monitor/commit/2bd082446790a2638bd93cfba8703243336d3ba2))

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
