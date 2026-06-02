# f19-campaigns 需求文档

> 来源：ReceptivIQ Dev Brief v2 §Pillar 4 — Omnichannel Media Buying
> 状态：MVP — Priority 4, API connectivity only

## 功能概述

在 ReceptivIQ 中统一管理跨广告平台（Meta Ads、DV360、StackAdapt）的投放活动，提供统一视图、预算节奏告警。全自动预算重分配（OmniFlux）为 Phase 2。

## MVP 功能需求

### FR-1: 统一 Campaign 视图

- 单一界面展示所有平台的 campaign 状态、花费、绩效
- 替代当前逐个登录各平台后台的手动流程
- 支持按平台、时间范围、客户筛选

### FR-2: Budget Pacing Alerts

- 基于规则的告警：campaign 花费节奏偏离目标时触发
- MVP 为 human-in-the-loop 通知，Phase 2 为自动重分配
- 可配置告警阈值（默认偏差 15%）

### FR-3: 跨平台聚合摘要

- 总花费、总转化、平台分布、趋势图数据
- Staff View（全详情）和 Client View（简化标签）两套视图

## 非功能需求

- Dashboard 加载时间 < 3 秒
- ETL 数据延迟 ≤ 30 分钟
- 租户隔离：agency_id 级别数据隔离

## 技术约束

- 数据架构：仓库聚合模式（Snowflake/DuckDB 查询，PG 仅存配置）
- 依赖：DV360 + StackAdapt ETL adapter（f20-etl-adapters）
- 复用：warehouse_client.py、notifications 模块

## Out of MVP Scope

- Campaign 创建/修改/暂停（写操作）
- OmniFlux 自动预算重分配
- Persona-to-Audience Export（独立模块）
