---
title: 术语表
version: 1.1.0
status: Published
last_updated: 2026-10-16
owner: PM
reviewers: [Tech Lead, 业务分析师, 架构师]
approvers: [PM]
classification: Public
doc_id: DOC-REF-001
tags: [参考, 术语表, 词汇表, 定义, 缩略语]
related_docs: [DOC-REQ-001, DOC-TECH-001, DOC-OPS-001]
changelog: |
  v1.1.0 (2026-10-16): 同步架构变更 - 移除 Celery/MySQL/JWT 术语，改为内置调度器/Redis/API Key - PM
  v1.0.0 (2026-09-26): 初版创建 - PM
---

# 术语表

## 1. 业务术语

| 术语 | 英文 | 定义 | 相关模块 |
|------|------|------|----------|
| 抖店 | FXG (Fenxiao) | 字节跳动旗下电商商家后台系统，提供商品、订单、合规等 API | 同步、商品、订单、合规 |
| 抖音创作者中心 | Creator Center | 字节跳动旗下创作者数据平台，提供视频、粉丝、互动数据 API | 同步、创作者 |
| 店铺 | Shop | 抖店/抖音平台上的商家实体，拥有独立授权凭证 | 全模块 |
| 授权 | Authorization | 商家通过 OAuth2 授权平台访问其店铺/创作者数据 | 授权、同步 |
| 同步 | Sync | 定时/手动从外部 API 拉取数据并写入 Redis/文件缓存的过程 | 同步任务 |
| 全量同步 | Full Sync | 拉取指定时间范围内的所有数据，覆盖式更新 | 同步任务 |
| 增量同步 | Incremental Sync | 仅拉取上次同步后新增/变更的数据 | 同步任务 |
| 回传 | Callback | 外部平台主动推送数据变更通知到平台回调接口 | 同步、Webhook |
| 订单 | Order | 用户在店铺下单购买商品形成的交易记录 | 订单、同步 |
| 商品 | Product | 店铺在售的 SKU/SPU 实体 | 商品、同步 |
| SKU | Stock Keeping Unit | 库存量单位，商品的最小销售单位（含规格、价格、库存） | 商品、订单 |
| SPU | Standard Product Unit | 标准化产品单位，聚合多个 SKU 的商品抽象 | 商品 |
| 合规 | Compliance | 平台对商品/订单/内容进行规则检测，识别违规风险 | 合规管理 |
| 违规 | Violation | 商品/内容/行为触发平台规则判定为不合规 | 合规管理 |
| 告警 | Alert | 关键指标异常时自动触发的通知机制 | 告警设置 |
| 通知渠道 | Notification Channel | 告警/通知的发送途径（企业微信/邮件/短信/钉钉） | 告警设置 |
| 授权凭证 | Credentials | 包含 Cookie、Token、签名参数等访问外部 API 所需的认证信息 | 授权、同步 |
| 同步任务 | Sync Task | 内置调度器 (schedule + threading) 中执行具体同步逻辑的周期任务单元 | 同步、调度器 |

---

## 2. 技术术语

| 术语 | 英文 | 定义 | 相关模块 |
|------|------|------|----------|
| API | Application Programming Interface | 应用程序编程接口，前后端/服务间通信契约 | 全模块 |
| RESTful | Representational State Transfer | 基于 HTTP 方法的资源导向架构风格 | API 设计 |
| GraphQL | Graph Query Language | 查询语言，客户端按需获取数据 | API 设计 (可选) |
| API Key | API Key | 访问平台内部 API 的密钥凭证，通过 Authorization: Bearer / X-API-Key 双 Header 传递 | 认证授权 |
| OAuth2 | Open Authorization 2.0 | 行业标准授权框架，支持授权码/刷新令牌流程 | 授权 |
| RBAC | Role-Based Access Control | 基于角色的访问控制模型 | 权限管理 |
| ABAC | Attribute-Based Access Control | 基于属性的访问控制（更细粒度） | 权限管理 (规划) |
| 内置调度器 | Built-in Scheduler | 基于 schedule 库 + threading 后台线程的定时任务机制，运行于 app 容器内 | 同步、定时任务 |
| Redis | Remote Dictionary Server | 内存键值存储，用于缓存、分布式锁、限流 | 缓存、锁、限流 |
| ORM | Object-Relational Mapping | 对象关系映射，代码操作数据库 (SQLAlchemy) | 后端开发 |
| Nginx | Web Server / Reverse Proxy | 高性能 Web 服务器/反向代理/负载均衡 | 部署、网关 |
| Docker | Container Platform | 容器化平台，镜像构建/运行/编排 | 部署、CI/CD |
| Docker Compose | Multi-container Orchestration | 单机多容器编排工具 | 本地/单机部署 |
| Kubernetes (K8s) | Container Orchestration | 容器编排平台 (生产规划) | 部署 (规划) |
| Prometheus | Monitoring & Alerting | 时序数据库 + 查询语言 + 告警引擎 | 监控告警 |
| Grafana | Visualization | 可视化仪表盘平台 | 监控大盘 |
| Loki | Log Aggregation | 日志聚合系统 (Grafana Labs) | 日志查询 |
| OpenTelemetry | Observability Framework | 可观测性标准 (追踪/指标/日志) | 链路追踪 |
| CI/CD | Continuous Integration / Continuous Deployment | 持续集成/持续部署自动化流水线 | DevOps |
| GitOps | Git Operations | 以 Git 为单一事实来源的声明式部署 | 部署 (规划) |
| Feature Flag | 功能开关 | 运行时动态控制功能发布/灰度 | 发布策略 |
| Blue-Green Deployment | 蓝绿部署 | 双环境切换，零停机发布 | 发布策略 |
| Canary Release | 金丝雀发布 | 少量流量验证后全量推进 | 发布策略 |

---

## 3. 架构与设计术语

| 术语 | 英文 | 定义 | 相关文档 |
|------|------|------|----------|
| 领域驱动设计 | DDD | 以业务领域为核心的软件设计方法论 | 架构设计 |
| 微服务 | Microservices | 将应用拆分为小型自治服务 | 架构设计 (规划) |
| 单体架构 | Monolithic Architecture | 单一代码库、单一进程部署 | 当前架构 |
| 领域模型 | Domain Model | 核心业务逻辑的对象化表达 | 后端设计 |
| 聚合根 | Aggregate Root | DDD 中保证一致性的实体入口 | 后端设计 |
| 值对象 | Value Object | 无标识、不可变、按值比较的对象 | 后端设计 |
| 领域事件 | Domain Event | 领域内发生的业务事实记录 | 后端设计 |
| 仓储模式 | Repository Pattern | 封装数据访问逻辑，隔离领域与基础设施 | 后端设计 |
| 单元工作 | Unit of Work | 管理事务边界、跟踪变更、批量持久化 | 后端设计 |
| CQRS | Command Query Responsibility Segregation | 读写分离模式，命令与查询分离 | 架构模式 (规划) |
| 事件溯源 | Event Sourcing | 以事件序列重建状态，而非存储当前状态 | 架构模式 (规划) |
| 幂等性 | Idempotency | 同一操作重复执行结果一致 | 接口设计 |
| 熔断器 | Circuit Breaker | 防止级联故障，快速失败、自动恢复 | 微服务/外部调用 |
| 限流 | Rate Limiting | 控制请求频率，保护系统稳定性 | 网关、服务 |
| 熔断降级 | Circuit Breaker + Fallback | 熔断后提供降级响应 | 微服务/外部调用 |
| 背压 | Backpressure | 消费者告知生产者降低发送速率 | 响应式编程 |
| 幂等键 | Idempotency Key | 客户端生成的唯一标识，保证重复请求幂等 | 接口设计 |
| 分布式锁 | Distributed Lock | 多实例环境下的互斥访问控制 | 同步任务、缓存 |
| 乐观锁 | Optimistic Lock | 基于版本号/时间戳的无锁并发控制 | 数据库更新 |
| 悲观锁 | Pessimistic Lock | 数据库行锁/表锁，强互斥 | 数据库更新 |

---

## 4. 运维与监控术语

| 术语 | 英文 | 定义 | 相关文档 |
|------|------|------|----------|
| SLA | Service Level Agreement | 服务等级协议，定义可用性/性能指标承诺 | 运维 SLA |
| SLO | Service Level Objective | 服务等级目标，内部衡量指标目标值 | 运维 SLA |
| SLI | Service Level Indicator | 服务等级指标，实际测量的量化指标 | 监控指标 |
| 可用性 | Availability | 系统正常服务时间比例 (如 99.9%) | SLA |
| 延迟 | Latency | 请求处理耗时 (P50/P95/P99) | 性能指标 |
| 吞吐量 | Throughput | 单位时间处理请求数 (QPS/TPS) | 性能指标 |
| 错误率 | Error Rate | 失败请求占比 (5xx/业务错误) | 性能指标 |
| 饱和度 | Saturation | 资源利用率 (CPU/内存/磁盘/网络/连接池) | 资源指标 |
| P50/P95/P99 | Percentile | 延迟分布的百分位数 (中位数/95分位/99分位) | 性能指标 |
| APDEX | Application Performance Index | 应用性能指数，综合满意度评分 | 性能指标 |
| RTO | Recovery Time Objective | 故障恢复时间目标 | 灾难恢复 |
| RPO | Recovery Point Objective | 数据恢复点目标 (最大数据丢失量) | 灾难恢复 |
| MTTD | Mean Time To Detect | 平均故障发现时间 | 事件管理 |
| MTTR | Mean Time To Recover | 平均故障恢复时间 | 事件管理 |
| MTBF | Mean Time Between Failures | 平均故障间隔时间 | 可靠性指标 |
| 链路追踪 | Distributed Tracing | 跨服务请求链路可视化 (TraceID/SpanID) | 可观测性 |
| TraceID | Trace Identifier | 全局唯一标识，串联完整调用链 | 链路追踪 |
| SpanID | Span Identifier | 单次操作的唯一标识 | 链路追踪 |
| 采样率 | Sampling Rate | 链路追踪数据采集比例 | 链路追踪 |
| 日志级别 | Log Level | DEBUG/INFO/WARN/ERROR/CRITICAL | 日志规范 |
| 结构化日志 | Structured Logging | JSON 格式、字段标准化、便于查询分析 | 日志规范 |
| 关联日志 | Correlated Logs | 通过 TraceID 关联同一请求的所有日志 | 日志规范 |

---

## 5. 数据与安全术语

| 术语 | 英文 | 定义 | 相关文档 |
|------|------|------|----------|
| PII | Personally Identifiable Information | 个人身份信息 (姓名/手机/邮箱/身份证等) | 数据安全 |
| 敏感数据 | Sensitive Data | 需加密保护的数据 (凭证/PII/财务/生物特征) | 数据安全 |
| 数据分级 | Data Classification | 公开/内部/机密/绝密/受限 五级分类 | 数据安全 |
| 脱敏 | Data Masking | 生产数据在非生产环境/展示时隐藏敏感字段 | 数据安全 |
| 匿名化 | Anonymization | 移除个人身份标识，不可逆恢复 | 数据安全 |
| 加密 | Encryption | 明文转密文 (AES-256-GCM/RSA/ECC) | 数据安全 |
| 密钥管理 | Key Management | 密钥生成/存储/轮换/撤销/审计 (KMS/Vault) | 数据安全 |
| TDE | Transparent Data Encryption | 数据库透明加密 (存储层加密) | 数据安全 |
| TLS/mTLS | Transport Layer Security / mutual TLS | 传输层加密/双向认证 | 网络安全 |
| 零信任 | Zero Trust | 永不信任、持续验证、最小权限 | 安全架构 |
| 最小权限 | Least Privilege | 仅授予完成任务所需的最小权限 | 权限模型 |
| RBAC | Role-Based Access Control | 基于角色的访问控制 | 权限模型 |
| ABAC | Attribute-Based Access Control | 基于属性的动态访问控制 | 权限模型 (规划) |
| 零信任网络 | ZTN | 网络层面的零信任实现 (Service Mesh) | 安全架构 (规划) |
| SBOM | Software Bill of Materials | 软件物料清单，组件/版本/许可证/漏洞清单 | 供应链安全 |
| SLSA | Supply Chain Levels for Software Artifacts | 软件供应链安全等级框架 | 供应链安全 |
| CVE | Common Vulnerabilities and Exposures | 公共漏洞披露编号 | 漏洞管理 |
| CVSS | Common Vulnerability Scoring System | 漏洞评分系统 (0-10 分) | 漏洞管理 |
| SAST | Static Application Security Testing | 静态代码安全分析 (源码/字节码) | 安全测试 |
| DAST | Dynamic Application Security Testing | 动态应用安全测试 (运行时黑盒) | 安全测试 |
| SCA | Software Composition Analysis | 软件成分分析 (依赖漏洞/许可证) | 供应链安全 |
| RASP | Runtime Application Self-Protection | 运行时应用自我保护 | 运行时防护 (规划) |

---

## 6. 项目管理术语

| 术语 | 英文 | 定义 | 相关文档 |
|------|------|------|----------|
| PRD | Product Requirements Document | 产品需求文档 | 需求管理 |
| BRD | Business Requirements Document | 业务需求文档 | 需求管理 |
| 用户故事 | User Story | 敏捷需求描述格式：作为<角色>，我希望<功能>，以便<价值> | 需求管理 |
| 验收标准 | Acceptance Criteria | 用户故事完成的可验证条件 | 需求管理 |
| Epic | 史诗 | 大型跨迭代功能，拆解为多个 Story | 敏捷管理 |
| Story | 故事/用户故事 | 单个迭代可完成的最小价值单元 | 敏捷管理 |
| Task | 任务 | Story 分解的具体执行单元 | 敏捷管理 |
| Sprint | 迭代/冲刺 | 固定周期 (通常 2 周) 的开发周期 | 敏捷管理 |
| Backlog | 待办列表 | 待优先级排序的需求/缺陷/技术债集合 | 敏捷管理 |
| Definition of Ready | DoR | Story 进入 Sprint 前的就绪标准 | 敏捷管理 |
| Definition of Done | DoD | Story 完成的验收标准 (代码/测试/文档/部署) | 敏捷管理 |
| Story Points | 故事点 | 相对工作量估算 (斐波那契: 1/2/3/5/8/13) | 估算 |
| Velocity | 速率 | 团队每 Sprint 完成的 Story Points 总和 | 规划指标 |
| Burndown Chart | 燃尽图 | Sprint 内剩余工作量随时间变化图 | 进度跟踪 |
| Retrospective | 复盘/回顾会议 | Sprint 结束后团队反思改进会议 | 敏捷管理 |
| Daily Standup | 每日站会 | 15 分钟同步进度/阻碍/计划 | 敏捷管理 |
| P0/P1/P2/P3 | Priority | 优先级分级 (阻塞/严重/一般/建议) | 缺陷/需求管理 |
| RCA | Root Cause Analysis | 根因分析 (5Why/鱼骨图) | 事件管理 |
| PIR | Post-Incident Review | 事后复盘/事后分析报告 | 事件管理 |
| ADR | Architecture Decision Record | 架构决策记录 | 架构治理 |
| RACI | Responsible/Accountable/Consulted/Informed | 职责分配矩阵 | 项目管理 |
| OKR | Objectives and Key Results | 目标与关键结果管理框架 | 目标管理 |
| KPI | Key Performance Indicator | 关键绩效指标 | 绩效管理 |

---

## 7. 缩略语对照表

| 缩略语 | 全称 | 中文 | 类别 |
|--------|------|------|------|
| FXG | Fenxiao | 抖店 | 业务 |
| SKU | Stock Keeping Unit | 库存量单位 | 业务 |
| SPU | Standard Product Unit | 标准产品单位 | 业务 |
| API | Application Programming Interface | 应用程序编程接口 | 技术 |
| REST | Representational State Transfer | 表述性状态转移 | 技术 |
| API Key | API Key | API 访问密钥 | 技术 |
| OAuth | Open Authorization | 开放授权 | 技术 |
| RBAC | Role-Based Access Control | 基于角色的访问控制 | 技术 |
| ABAC | Attribute-Based Access Control | 基于属性的访问控制 | 技术 |
| ORM | Object-Relational Mapping | 对象关系映射 | 技术 |
| CI/CD | Continuous Integration/Continuous Deployment | 持续集成/持续部署 | 运维 |
| SLA | Service Level Agreement | 服务等级协议 | 运维 |
| SLO | Service Level Objective | 服务等级目标 | 运维 |
| SLI | Service Level Indicator | 服务等级指标 | 运维 |
| RTO | Recovery Time Objective | 恢复时间目标 | 运维 |
| RPO | Recovery Point Objective | 恢复点目标 | 运维 |
| MTTR | Mean Time To Recover | 平均恢复时间 | 运维 |
| MTBF | Mean Time Between Failures | 平均故障间隔 | 运维 |
| MTTD | Mean Time To Detect | 平均发现时间 | 运维 |
| PII | Personally Identifiable Information | 个人身份信息 | 安全 |
| TDE | Transparent Data Encryption | 透明数据加密 | 安全 |
| TLS | Transport Layer Security | 传输层安全 | 安全 |
| mTLS | mutual TLS | 双向 TLS | 安全 |
| PII | Personally Identifiable Information | 个人身份信息 | 安全 |
| SBOM | Software Bill of Materials | 软件物料清单 | 供应链 |
| SAST | Static Application Security Testing | 静态应用安全测试 | 安全 |
| DAST | Dynamic Application Security Testing | 动态应用安全测试 | 安全 |
| SCA | Software Composition Analysis | 软件成分分析 | 供应链 |
| SLA | Service Level Agreement | 服务等级协议 | 运维 |
| SLO | Service Level Objective | 服务等级目标 | 运维 |
| SLI | Service Level Indicator | 服务等级指标 | 运维 |
| RTO | Recovery Time Objective | 恢复时间目标 | 运维 |
| RPO | Recovery Point Objective | 恢复点目标 | 运维 |
| MTTR | Mean Time To Recover | 平均恢复时间 | 运维 |
| MTBF | Mean Time Between Failures | 平均故障间隔 | 运维 |
| MTTD | Mean Time To Detect | 平均发现时间 | 运维 |
| CI/CD | Continuous Integration/Continuous Deployment | 持续集成/持续部署 | 运维 |
| PR | Pull Request | 拉取请求 | 开发流程 |
| MR | Merge Request | 合并请求 | 开发流程 |
| LGTM | Looks Good To Me | 代码审查通过 | 代码审查 |
| WIP | Work In Progress | 进行中 | 开发流程 |
| RFC | Request For Comments | 征求意见稿 | 架构治理 |
| ADR | Architecture Decision Record | 架构决策记录 | 架构治理 |
| RFC | Request For Comments | 征求意见稿 | 架构治理 |
| DoD | Definition of Done | 完成的定义 | 敏捷 |
| DoR | Definition of Ready | 就绪的定义 | 敏捷 |
| PO | Product Owner | 产品负责人 | 敏捷 |
| SM | Scrum Master | 敏捷教练 | 敏捷 |

---

## 8. 版本管理

| 版本 | 日期 | 变更内容 | 编制人 | 审核人 |
|------|------|----------|--------|--------|
| v1.0.0 | 2026-09-26 | 初版创建，涵盖业务/技术/运维/安全/管理全维度术语 | PM | Tech Lead |

---

*文档密级: Public | 维护责任: PM | 更新周期: 随项目演进持续补充*
EOF