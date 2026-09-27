# 清理清单 2026-09-23

## 已归档重复文档
- docs/1_architecture/FRONTEND_DESIGN.md → docs/archive_cleanup_20260923/
- docs/1_architecture/DESIGN.md → docs/archive_cleanup_20260923/
- docs/1_architecture/ARCHITECTURE.md → docs/archive_cleanup_20260923/

## 已归档根目录调试脚本
- 根目录下 check_*.py 全部移至 docs/archive_cleanup_20260923/root_scripts/

## 前端构建产物处理
- src/frontend/build 已加入 .gitignore，后续构建产物不再入库
- 建议删除历史构建缓存以节省空间

## 下一步建议
- 统一 docs 目录结构，保留唯一版本文档
- 将遗留 test_*.py 归档
- 定期清理 screenshots 无效文件
