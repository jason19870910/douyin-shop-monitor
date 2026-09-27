# 系统架构文档

> **注意**：此文档已移至 [`../ARCHITECTURE.md`](../ARCHITECTURE.md)。请参考该文档获取最新的系统架构信息。

本文档原文档已迁移到项目文档根目录以保持文档组织的一致性。

## 系统架构概览

抖音电商数据监控平台采用微服务架构，主要包括以下组件：

1. **前端应用**（React + Vite）
   - 负责用户界面和交互
   - 使用Ant Design UI库
   - 使用Recharts进行数据可视化

2. **后端服务**（Flask + Celery）
   - 提供RESTful API
   - 使用Celery处理异步任务
   - 使用Redis作为代理和结果后端

3. **数据存储**
   - 使用关系型数据库存储业务数据
   - 使用Redis进行缓存

4. **部署基础设施**
   - 使用Docker容器化部署
   - 使用Nginx作为反向代理
   - 使用docker-compose进行服务编排

详细信息请参考 [`../ARCHITECTURE.md`](../ARCHITECTURE.md)。