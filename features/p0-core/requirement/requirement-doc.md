# p0-core 需求文档

> 来源：ReceptivIQ 底层框架开发计划 Phase 0
> 状态：F-00 ~ F-05 核心基础层聚合模块

## 功能概述

所有 Pillar 功能的前置依赖层，包含合规、多租户、认证、凭证保险库、审计日志、平台集成管理 6 大模块。P0 是整个项目的地基。

## 功能需求

### FR-1: 多租户基础设施（F-01）

- Agency（顶层）→ Client（下级）二级租户体系
- 所有表均有 `agency_id` FK（NOT NULL，indexed）
- 每个请求通过 `user.agency_id` 强制过滤
- 白标子路径路由（`/agency-slug/client-slug`）

### FR-2: 认证与授权（F-02）

- JWT Bearer Token（access 30min + refresh 7d）
- 三角色 RBAC：agency_admin / agency_ops / client_viewer
- Google OAuth 登录
- 登录 IP 限流（5次/5分钟 → 15分钟锁定）
- Token 撤销（jti + Redis 黑名单）

### FR-3: 凭证保险库（F-03）

- OAuth token / API key 使用 Fernet 加密存储
- 解密仅在 ETL/API 调用时进行
- 脱敏输出（日志、API 响应）
- OAuth token 自动刷新

### FR-4: 审计日志（F-04）

- INSERT-only 触发器防止修改
- 记录 user_id / agency_id / action / resource_type / extra_data
- 6 年保留（HIPAA 要求）
- 所有 API 端点必须调用 `audit_simple()`

### FR-5: 平台集成管理（F-05）

- 12 平台注册表（GA4/Meta/HubSpot/TikTok/DV360/StackAdapt/LeadRX/LiveRamp/Quorum/Canva/Firefly/ICON）
- connect / disconnect / sync 统一接口
- 平台状态追踪（connected / expired / error）

## 非功能需求

- 启动时校验 SECRET_KEY 强度（生产环境 32+ 字符）
- CORS 限制来源 + 方法白名单
- 安全头（HSTS / X-Frame-Options / X-Content-Type-Options）

## 合规要求

见 compliance 模块顶层策略，P0 是合规落地的承载层。
