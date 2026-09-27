---
title: {服务名} API 规范
version: 1.0
status: Draft
last_updated: YYYY-MM-DD
owner: Backend Lead
reviewers: [Frontend Lead, Tech Lead]
approvers: [Backend Lead, Frontend Lead]
classification: Internal
doc_id: DOC-API-XXX
tags: [API, 接口规范, {服务名}]
related_docs: [DOC-API-001]
changelog: |
  v1.0 (YYYY-MM-DD): 初版创建 - 作者
---

# {服务名} API 规范

## 1. 概述
### 1.1 版本信息
### 1.2 基础 URL
### 1.3 认证方式
### 1.4 通用响应格式
### 1.5 错误码定义

## 2. 接口列表
### 2.1 {模块名}
#### GET /api/v1/{resource}
**描述**: {接口描述}
**权限**: {所需权限}
**参数**:
| 参数名 | 类型 | 必填 | 位置 | 说明 |
|--------|------|------|------|------|
| page | integer | 否 | query | 页码，默认 1 |
| size | integer | 否 | query | 每页大小，默认 20 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [],
    "total": 0,
    "page": 1,
    "size": 20
  }
}
```

## 3. 数据模型
### 3.1 {ModelName}
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 唯一标识 |
| name | string | 是 | 名称 |

## 4. 版本兼容性策略
## 5. 变更历史
EOF