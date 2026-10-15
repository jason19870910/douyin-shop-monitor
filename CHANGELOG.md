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

### Fixed
- HAOHUO plugin field path mapping (haohuo_detail_info, haohuo_extra)
- Indentation error in rule_engine.py

## [0.1.0] - 2026-10-15

### Added
- Initial commit: Douyin compliance platform with HAOHUO plugins enabled
- Product compliance checking with Haohuo preview data enrichment
- Works compliance checking for creator content
- Git version control with automated deployment